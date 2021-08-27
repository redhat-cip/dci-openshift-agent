# DCI OpenShift Agent

`dci-openshift-agent` provides Red Hat OpenShift Container Platform (RHOCP) in Red Hat Distributed CI service.

## Table of Contents

- [Requirements](#requirements)
  - [Systems requirements](#systems-requirements)
    - [Jumpbox requirements](#jumpbox-requirements)
    - [Systems under test](#systems-under-test)
    - [Optional](#optional)
- [Installation of DCI Jumpbox](#installation-of-dci-jumpbox)
- [Configuration](#configuration)
  - [Overloading settings and hooks directories](#overloading-settings-and-hooks-directories)
- [Copying the ssh key to your provisionhost](#copying-the-ssh-key-to-your-provisionhost)
- [Starting the DCI OCP Agent](#starting-the-dci-ocp-agent)
- [Keep the DCI OCP Agent Updated](#keep-the-dci-ocp-agent-updated)
- [dci-openshift-agent workflow](#dci-openshift-agent-workflow)
- [Getting Involved](#getting-involved)
  - [Testing a change](#testing-a-change)
  - [Local dev environment](#local-dev-environment)
- [Create your DCI account on distributed-ci.io](#create-your-dci-account-on-distributed-ciio)
- [License](#license)
- [Contact](#contact)

## Requirements

### Systems requirements

`DCI OpenShift Agent` needs a dedicated system to act as a `controller node`. It is identified as the `DCI Jumpbox` in this document. This system will be added to a standard OCP topology by being connected to the OCP `baremetal network`. The `DCI OpenShift Agent` will drive the RHOCP installation workflow from there.

Therefore, the simplest working setup must be composed of at least **5** systems (1 system for DCI and 4 systems to match OCP minimum requirements).

Please follow the [OpenShift Baremetal Deploy Guide (a.k.a. `openshift-kni`)](https://openshift-kni.github.io/baremetal-deploy/) for how to properly configure the OCP networks, systems and DNS.

Choose the OCP version you want to install and follow steps 1 to 3 to configure the networks and install RHEL 8 on the **OpenShift Provisioning node**. Steps after 4 will be handled by the `dci-openshift-agent`.

1. [Installation of DCI Jumpbox](#installation-of-dci-jumpbox)
2. [Configuration](#configuration)
3. [Copying the ssh key to your provisionhost](#copying-the-ssh-key-to-your-provisionhost)
4. [Starting the DCI OCP Agent](#starting-the-dci-ocp-agent)

As mentioned before, the **DCI Jumpbox** is NOT part of the RHOCP cluster. It is only dedicated to download `RHOCP` artifacts from `DCI` public infrastructure and to schedule the RHOCP cluster deployment across all systems under test (1x OpenShift Provisioning node and several OCP nodes).

The **OpenShift Provisioning node** is used by the OpenShift installer to provision the OpenShift cluster nodes.

The 3 remaining systems will run the freshly installed OCP Cluster. “3” is the minimum required number of nodes to run RHOCP but it can be more if you need to.

#### Prerequisites

- Each server needs 2 NICs pre-configured. NIC1 for the private network and NIC2 for the baremetal network. NIC interface names must be identical across all nodes
- Each server must have IPMI configured
- Each server must have DHCP setup for the baremetal NICs
- Each server must have DNS setup for the API, wildcard applications. Please follow the [Openshift Baremetal DNS server configuration](https://openshift-kni.github.io/baremetal-deploy/latest/Deployment#DNS)
- Optional - Include DNS entries for the hostnames for each of the servers

![Proposed network diagram](https://lucid.app/publicSegments/view/bedb0b3c-0cca-43ef-9dc6-7ed40ac35506/image.png "Proposed network diagram")

#### Jumpbox requirements

The `Jumpbox` can be a physical server or a virtual machine.
In any case, it must:

- Be running the latest stable RHEL release (**8.4 or higher**) and registered via RHSM.
- Have at least 160GB of free space available in `/var`
- Have access to Internet
- Be able to connect the following Web urls:
  - DCI API, https://api.distributed-ci.io
  - DCI Packages, https://packages.distributed-ci.io
  - DCI Repository, https://repo.distributed-ci.io
  - EPEL, https://dl.fedoraproject.org/pub/epel/
  - QUAY.IO, https://quay.io
  - RED HAT REGISTRY, https://registry.redhat.io
  - RED HAT SSO, https://access.redhat.com
  - RED HAT CATALOG, https://catalog.redhat.com
- Have a static internal (network lab) IP
- Be able to reach all systems under test (SUT) using (mandatory, but not limited to):
  - SSH
  - IPMI
  - Serial-Over-LAN or other remote consoles (details & software to be provided by the partner)
- Be reachable by the Systems Under Test by using:
  - DHCP
  - PXE
  - HTTP/HTTPS

NOTE: Make sure rhel-8-for-x86_64-appstream-rpms repo provides access to libvirt => 6.0.0 packages

#### Systems under test

`Systems under test` will be **installed** through DCI workflow with each job and form the new “fresh” RHOCP cluster.

All files on these systems are NOT persistent between each `dci-openshift-agent` job as the RHOCP cluster is reinstalled at each time. Therefore, every expected customization and tests have to be automated from the DCI Jumpbox (by using hooks) and will therefore be applied after each deployment (More info at [Configuration](#configuration)).

#### Optional

- We strongly advise the partners to provide the Red Hat DCI team with access to their jumpbox. This way, Red Hat engineers can help with initial setup and troubleshooting.

- We suggest to run the `full virtualized` provided example first to understand how the `dci-openshift-agent` works before going to production with a real lab.

## Installation of DCI Jumpbox

Before proceeding you should have set up your networks and systems according to the baremetal-deploy doc that was referenced above.

Provision the Jumphost with RHEL8.

The `dci-openshift-agent` is packaged and available as a RPM file.
However,`dci-release` and `epel-release` must be installed first:

```bash
# dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
# dnf -y install https://packages.distributed-ci.io/dci-release.el8.noarch.rpm
# subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
# subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
# dnf -y install dci-openshift-agent
```

## Configuration

There are three configuration files for `dci-openshift-agent`: `/etc/dci-openshift-agent/dcirc.sh`, `/etc/dci-openshift-agent/hosts` and `/etc/dci-openshift-agent/settings.yml`.

- `/etc/dci-openshift-agent/dcirc.sh`

Note: The initial copy of `dcirc.sh` is shipped as `/etc/dci-openshift-agent/dcirc.sh.dist`.

Copy this to `/etc/dci-openshift-agent/dcirc.sh` to get started, then replace inline some values with your own credentials.

From the web the [DCI web dashboard](https://www.distributed-ci.io), the partner team administrator has to create a `Remote CI` in the DCI web dashboard.

Copy the relative credential and paste it locally on the Jumpbox to `/etc/dci-openshift-agent/dcirc.sh`.

This file should be edited once:

```bash
#!/usr/bin/env bash
DCI_CS_URL="https://api.distributed-ci.io/"
DCI_CLIENT_ID=remoteci/<remoteci_id>
DCI_API_SECRET=<remoteci_api_secret>
export DCI_CLIENT_ID
export DCI_API_SECRET
export DCI_CS_URL
```

- `/etc/dci-openshift-agent/settings.yml`

This is the dci openshift agent settings (format is YAML). Use this to specify which version of OCP to install.

| Variable                           | Required | Type    | Default                                          | Description                                                    |
| ---------------------------------- | -------- | ------- | ------------------------------------------------ | -------------------------------------------------------------- |
| dci\_topic                         | True     | String  |                                                  | Name of the topic. `OCP-4.5` and up.                           |
| dci\_tags                          | False    | List    | ["debug"]                                        | List of tags to set on the job                                 |
| dci\_name                          | False    | String  |                                                  | Name of the job                                                |
| dci\_configuration                 | False    | String  |                                                  | String representing the configuration of the job               |
| dci\_comment                       | False    | String  |                                                  | Comment to associate with the job                              |
| dci\_url                           | False    | URL     |                                                  | URL to associate with the job                                  |
| dci\_components\_by\_query         | False    | List    | []                                               | Component by query. ['name:4.5.9']                             |
| dci\_component                     | False    | List    | []                                               | Component by UUID. ['acaf3f29-22bb-4b9f-b5ac-268958a9a67f']    |
| dci\_must\_gather\_images          | False    | List    |["registry.redhat.io/openshift4/ose-must-gather"] | List of the must-gather images to use when retrieving logs.\*  |
| dci\_teardown\_on\_failure         | False    | Boolean | False                                            | Whether or not execute the teardown hook on a failure          |
| dci\_teardown\_on\_success         | False    | Boolean | True                                             | Whether or not execute the teardown hook on success            |
| dci\_openshift\_agent\_conformance | False    | String  |                                                  | If defined it will run that category of conformance test       |
| baremetal\_deploy\_version         | False    | String  | HEAD                                             | Allows you to lock upstream baremetal repo to specific version |
| http\_proxy                        | False    | String  |                                                  | http proxy to use                                              |
| https\_proxy                       | False    | String  |                                                  | https proxy to use                                             |
| no\_proxy\_list                    | False    | String  |                                                  | Comma separated list of hosts not going through the proxies    |

\* [Here](https://docs.openshift.com/container-platform/4.7/support/gathering-cluster-data.html) you can find information on the available must-gather images. Also, bear in mind that authentication is required to retrieve the images.

Example:

```YAML
---
dci_topic: "OCP-4.8"
dci_name: "ocp-4.8-job"
dci_configuration: "baremetal"
dci_url: "https://softwarefactory-project.io/r/c/dci-openshift-agent/+/22195"
dci_comment: "test-runner: use the new url metadata for jobs"
dci_tags: ["debug", "gerrit:22195"]
...
```

- `/etc/dci-openshift-agent/hosts`

This file is an Ansible inventory file (format is `.ini`). It includes the configuration for the `dci-openshift-agent` job and the inventory for the masters, workers (if any) and the provisionhost.

Example:

```console
[all:vars]
prov_nic=eno1 # The provisioning NIC (NIC1) used on all baremetal nodes
pub_nic=eno2 # The public NIC (NIC2) used on all baremetal nodes
domain=example.com # Base domain
cluster=dciokd # Name of the cluster
masters_prov_nic=eno1 # The provisioning NIC (NIC1) used on the master nodes
prov_ip=172.22.0.3 # Provisioning IP address
dir="{{ ansible_user_dir }}/clusterconfigs" # The directory used to store the cluster configuration files (install-config.yaml, pull-secret.txt, metal3-config.yaml)
ipv6_enabled=false # Enable IPv6 addressing instead of IPv4 addressing
disable_bmc_certificate_verification=True # Disable TLS verification of BMC certificates

# Master nodes
[masters]
master-0 name=master-0 role=master ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-master-0.dciokd.example.com provision_mac=ac:1f:6b:7d:dd:44 hardware_profile=default labels='{"node-role.kubernetes.io.foo":"", "node-role.kubernetes.io.bar":""}'
master-1 name=master-1 role=master ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-master-1.dciokd.example.com provision_mac=ac:1f:6b:6c:ff:ee hardware_profile=default labels='{"node-role.kubernetes.io.bar":""}'
master-2 name=master-2 role=master ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-master-2.dciokd.example.com provision_mac=ac:1f:6b:29:33:3c hardware_profile=default

# Worker nodes
[workers]

# Provision Host
[provisioner]
provisionhost ansible_user=kni prov_nic=eno1 pub_nic=ens3 ansible_ssh_common_args="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
```
NOTE: If the jumpbox server is in a different network than the baremetal network, then include extcirdnet=<baremetal-network/mask> in the all:vars section of the inventory

### Overloading settings and hooks directories

To allow storing the settings and the hooks in a different directory,
you can set `/etc/dci-openshift-agent/config` like this:

```Shell
CONFIG_DIR=/var/lib/dci-openshift-agent/config
```

This will allow you to use a version control system for all your settings.

If you want to also store the hooks in the same directory, you have to
specify `dci_config_dirs` in your `settings.yml`. Example:

```YAML
---
dci_topic: OCP-4.8
dci_config_dirs: [/var/lib/dci-openshift-agent/config]
```

## Copying the ssh key to your provisionhost

```console
# su - dci-openshift-agent
% ssh-keygen
% ssh-copy-id kni@provisionhost
```

## Starting the DCI OCP Agent

Now that you have configured the `DCI OpenShift Agent`, you can start the service.

Please note that the service is a systemd `Type=oneshot`. This means that if you need to run a DCI job periodically, you have to configure a `systemd timer` or a `crontab`.

```
$ systemctl start dci-openshift-agent
```

If you need to run the `dci-openshift-agent` manually in foreground,
you can use this command line:

```
# su - dci-openshift-agent
% dci-openshift-agent-ctl -s -- -v
```

### Launching the agent without doing DCI calls

The `dci` tag can be used to skip all DCI calls. You will need to
provide fake `job_id` and `job_info` variables in a `myvars.yml` file
like this:

```YAML
job_id: fake-id
job_info:
  job:
    components:
    - name: 1.0.0
      type: my-component
```

and then call the agent like this:

```ShellSession
# su - dci-openshift-agent
$ dci-openshift-agent-ctl -s -- --skip-tags dci -e @myvars.yml
```

## Keep the DCI OCP Agent Updated

It is recommended to keep the jumphost server updated, enable dnf-automatic updates to make sure system is using latest dci-openshift-agent

Install dnf-automatic

```ShellSession
# dnf install -y dnf-automatic
```

Modify the default configuration to enable automatic downloads and apply updates

```ShellSession
# vi /etc/dnf/automatic.conf
...
download_updates = yes
apply_updates = yes
...
```

Enable the dnf-automatic.timer

```ShellSession
# systemctl enable --now dnf-automatic.timer
```

## dci-openshift-agent workflow

_Step 0 :_ “New DCI job”

- Create a DCI job

_tags: job_
_runs on localhost_

_Step 1 :_ “Pre-run”

- Prepare the `Jumpbox`: `/plays/pre-run.yml`
- Deploy infrastructure if needed: `/hooks/pre-run.yml`

_tags: pre-run_
_runs on localhost_

_Step 2 :_ “Configure”

- Prepare provisioner: `/plays/configure-provisioner.yml` and `/hooks/configure.yml`

_tags: running, configure_
_runs on provisioner_

_Step 3a :_ “Installing”

- Start OpenShift install: `/plays/install.yml` and `/hooks/install.yml`. This is launched the variable `dci_main` is undefined or equal to `install`.
This step is split into three part: 3a-1 is the installation of OCP itself (tag `installing`), 3a-2 is the deployment of operators (tag `operator-deployment`), and the last part 3a-3 is the installation of partner hooks (tag `hook-installing`).
  Each part can be called separately using the associated tag.

_tags: running, installing, hook-installing_
_runs on provisioner_

_Step 3b :_ “Upgrading”

- Start OpenShift upgrade: `/plays/upgrade.yml` and `/hooks/upgrade.yml`. This is launched when the variable `dci_main` is set to `upgrade`.

_tags: running, upgrading, hook-upgrading_
_runs on provisioner_

_Step 4 :_ “Deploy operators”

- start Deploy operators: `/plays/deploy-operators.yml`

_tags: running, operator-deployment_
_runs on provisioner_

_Step 5 :_ “Red Hat tests”

- start Red Hat tests: `/plays/tests.yml`

_tags: running, testing, redhat-testing_
_runs on localhost_

_Step 6 :_ “Partner tests”

- start partner tests: `/hooks/tests.yml`

_tags: running, testing, partner-testing_
_runs on localhost_

_Step 7 :_ “Post-run”

- Start post-run to collect results: `/plays/post-run.yml` and `/hooks/post-run.yml`
- Note: All results files (logs, tests, ...) must be stored within the {{ dci_cluster_configs_dir }}/ directory in order to be properly uploaded
  to the DCI server. Test result files must follow the Junit format and the file name must follow the pattern "junit\_\*.xml".

_tags: post-run_
_runs on localhost_

_Step 8 :_ “Success”

- Launch additional tasks when the job is successful: `/hooks/success.yml`

_tags: success_
_runs on localhost_

_Exit playbooks:_
The following playbooks are executed sequentially at any step that fail:

- Teardown: `/hooks/teardown.yml`
- Failure: `/plays/failure.yml` during the `running` steps and `/plays/error.yml` during the other steps.

_All the task files located in directory `/etc/dci-openshift-agent/hooks/` are empty by default and should be customized by the user._

All the tasks prefixed with `test_` will get exported in Junit using
the [Ansible Junit
callback](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/junit_callback.html)
and submitted automatically to the DCI control server.

## Getting Involved

### Testing a change

If you want to test a change from a Gerrit review or from a Github PR,
use the `dci-check-change` command. Example:

```ShellSession
$ dci-check-change 21136
```

to check https://softwarefactory-project.io/r/#/c/21136/ or from a Github:

```ShellSession
$ dci-check-change https://github.com/myorg/config/pull/42
```

Regarding Github, you will need a token to access private repositories
stored in `~/.github_token`.

By convention, the `settings.yml` and `hosts` files are searched in
directories ending in `config`.

You can use `dci-queue` from the `dci-pipeline` package to manage a
queue of changes. To enable it, add the name of the queue into
`/etc/dci-openshift-agent/config`:

```Shell
DCI_QUEUE=<queue name>
```

If you have multiple prefixes, you can also enable it in
`/etc/dci-openshift-agent/config`:

```Shell
USE_PREFIX=1
```

### Local dev environment

For dev purposes, it is important to be able to run and test the code directly on your dev environment so without using the package manager.

In order to run the agent without using the RPM package, you need to move the three configuration files (`settings.yml`, `dcirc.sh` and `hosts`) in the directory of the git repo.

Then, you need to modify dev-ansible.cfg two variables: `inventory` and `roles_path` (baremetal_deploy_repo).

Also, in order to install package with the ansible playbook, you need to add rights to `dci-openshift-agent` user:

```
# cp dci-openshift-agent.sudo /etc/sudoers.d/dci-openshift-agent
```

Finally, you can run the script:

```
# Option -d for dev mode
# Overrides variables with group_vars/dev
% ./dci-openshift-agent-ctl -s -c settings.yml -d -- -e @group_vars/dev
```

## Create your DCI account on distributed-ci.io

Every user needs to create his personal account by connecting to `https://www.distributed-ci.io` by using a Red Hat SSO account.

The account will be created in the DCI database at the first connection with the SSO account. For now, there is no reliable way to know your team automatically. Please contact the DCI team when this step has been reached, to be assigned in the correct organisation.

## License

Apache License, Version 2.0 (see [LICENSE](LICENSE) file)

## Contact

Email: Distributed-CI Team <distributed-ci@redhat.com>
IRC: #distributed-ci on Freenode

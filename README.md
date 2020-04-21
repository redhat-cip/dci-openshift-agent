# DCI Openshift Agent

`dci-openshift-agent` provides Red Hat OpenShift Container Platform (RHOCP) in Red Hat Distributed CI service.

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How to run your own set of tests](#how-to-run-your-own-set-of-tests)
- [Create your DCI account on distributed-ci.io](#create-your-dci-account-on-distributed-ciio)
- [License](#license)
- [Contact](#contact)


## Requirements
### Systems requirements

The simplest working setup must be composed of at least **5** systems. The `DCI Openshift Agent` does NOT require all systems to be dedicated physical hardware. Therefore, by using virtualization technology (such as Libvirt), the number of physical systems can be reduced.

You will find in the `/sample` folder some configuration examples to run the `DCI Openshift Agent` in a full or in a partial virtualized environment.

- The first mandatory system is the **DCI Jumpbox**. It acts as a `controller node`. This system is NOT part of the RHOCP cluster. It is dedicated to download `RHOCP` artifacts from `DCI` public infrastructure and to schedule the RHOCP cluster deployment across all Systems Under Test (SUT).

The **DCI Jumpbox** has 2 network interfaces (NICs). The first one is connected to the outbound Internet (default gateway) and the second one to the lab (RHOCP cluster).

- The second system is the **Provisioning node**. This system is silently used by the Openshift installer to provision the OpenShift cluster.

- The 3 remaining systems will run the freshly installed OCP Cluster. “3” is the minimum required number of nodes to run RHOCP but it can be more if you need to.

Please note that you can have only one **DCI Jumpbox** per lab, but it makes sense to have multiple group of **Systems Under Test** (for instance: systems with different hardware profiles).



#### Jumpbox requirements

The `Jumpbox` can be a physical server or a virtual machine.
In any case, it must:

* Be running the latest stable RHEL release (**7.6 or higher**) and registered via RHSM.
* Have at least 160GB of free space available in `/var`
* Have access to Internet
* Be able to connect the following Web urls:
  * DCI API, https://api.distributed-ci.io
  * DCI Packages, https://packages.distributed-ci.io
  * DCI Repository, https://repo.distributed-ci.io
  * EPEL, https://dl.fedoraproject.org/pub/epel/
  * QUAY.IO, https://quay.io
* Have a static internal (network lab) IP
* Be able to reach all systems under test (SUT) using (mandatory, but not limited to):
  * SSH
  * IPMI
  * Serial-Over-LAN or other remote consoles (details & software to be provided by the partner)
* Be reachable by the Systems Under Test by using:
  * DHCP
  * PXE
  * HTTP/HTTPS

#### Provisioning node requirements

The `Provisioning node` can be a physical server or a virtual machine. This system is used only once by the OCP installer to provision the OpenShift cluster (which is formed by all Systems Under Test). The `Provisioning node` is re-imaged at each DCI job.

The `Provisioning node` must match the official [OCP guidelines](#https://github.com/openshift-kni/baremetal-deploy/blob/master/install-steps.md) (cf: Prerequisites).

It is possible for the `DCI Openshift Agent` to create this system automatically for you. In this case, it will be a Libvirt virtual machine deployed on top of the DCI `Jumpbox`.

Please note that the `Provisioning node` might be a [nested virtual machine](#https://www.linux-kvm.org/page/Nested_Guests) if the DCI Jumpbox is already a virtual machine.

#### Systems under test

`Systems under test` can be physical servers or virtual machines. They will be **installed** through DCI workflow with each job and form the new “fresh” RHOCP cluster.

All files on these systems are NOT persistent between each `dci-openshift-agent` job as the RHOCP cluster is reinstalled at each time. Therefore, every expected customization and tests have to be automated from the DCI Jumpbox (by using hooks) and will therefore be applied after each deployment (More info at #Configuration and #Usage).

Each nodes of the OCP cluster (all Systems Under Tests) should match the official [OCP requirements](#https://github.com/openshift-kni/baremetal-deploy/blob/master/install-steps.md).

### Lab generic network requirements
* The lab network must allow network booting protocols such as DHCP/PXE.
* The lab network should be fully isolated, to prevent conflicts with other networks (we suggest to use VLAN).
* The lab network bandwidth can be impacted since the `dci-openshift-agent` will download OCP artifacts once in a while.

#### Optional

* We strongly advise the partners to provide the Red Hat DCI team with access to their jumpbox. This way, Red Hat engineers can help with initial setup and troubleshooting.

* We suggest to run the `full virtualized` provided example first to understand how the `dci-openshift-agent` works before going to production with a real lab.

## Installation

The `dci-openshift-agent` is packaged and available as a RPM file.
However,`dci-release` and `epel-release` must be installed first:

```bash
# yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
# yum -y install https://packages.distributed-ci.io/dci-release.el7.noarch.rpm
# subscription-manager repos --enable=rhel-7-server-extras-rpms
# subscription-manager repos --enable=rhel-7-server-optional-rpms
# yum -y install dci-openshift-agent
```

## Configuration

There are two configuration files for `dci-openshift-agent`: `/etc/dci-openshift-agent/dcirc.sh` and `/etc/dci-openshift-agent/settings.yml`.

  * `/etc/dci-openshift-agent/dcirc.sh`

Note: The initial copy of `dcirc.sh` is shipped as `/etc/dci-rhel-agent/dcirc.sh.dist`. Copy this to `/etc/dci-openshift-agent/dcirc.sh` to get started, then replace inline some values with your own credentials.

From the web the [DCI web dashboard](https://www.distributed-ci.io), the partner team administrator has to create a `Remote CI` in the DCI web dashboard. Copy the relative credential and paste it locally on the Jumpbox to `/etc/dci-openshift-agent/dcirc.sh`.

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

* `/etc/dci-openshift-agent/settings.yml`

This YAML file includes the configuration for the `dci-openshift-agent` job.
The possible values are:

| Variable | Required | Type | Description |
|----------|----------|------|-------------|
| topic | True | String | Name of the topic. It can be `OCP-4.3` or `OCP-4.4`.|
| cluster_name | True | String | RHCP cluster name.|
| base_domain | True | String | tbd |
| ironic_nodes | True | String (JSON) | tbd|

Example:

```console
dci_topic: OCP-4.3
cluster_name: dciokd
base_domain: metalkube.org
ironic_nodes: {"openshift-master-2": {"ipmi_user": "root", "ipmi_pass": "password", "ipmi_address": "192.168.123.1:6232", "mac_address": "52:54:00:89:58:20"}, "openshift-master-0": {"ipmi_user": "root", "ipmi_pass": "password", "ipmi_address": "192.168.123.1:6230", "mac_address": "52:54:00:8a:3c:df"}, "openshift-master-1": {"ipmi_user": "root", "ipmi_pass": "password", "ipmi_address": "192.168.123.1:6231", "mac_address": "52:54:00:73:26:fb"}}
cluster_domain: "dciokd.metalkube.org"
cluster_pro_if: ens3
pro_if: eth0
int_if: eth1
dns_vip: 192.168.123.6
openshift_release_image: ''
provisionhost_name: worker-0
provisionhost_ip: 192.168.123.142
provisionhost_user: dci
provisionhost_password: redhat
```

## Starting the DCI OCP Agent

Now that you have configured the DCI OCP Agent, you can start the service.

Please note that the service is a systemd `Type=oneshot`. This means that if you need to run a DCI job periodically, you have to configure a `systemd timer` or a `crontab`.

```
$ systemctl start dci-rhel-agent
```

If you need to run the `dci-openshift-agent` manually in foreground, you can use this command line:

```
# su - dci-openshift-agent 
$ cd /usr/share/dci-openshift-agent && source /etc/dci-openshift-agent/dcirc.sh && /usr/bin/ansible-playbook -vv /usr/share/dci-openshift-agent/dci-openshift-agent.yml -e @/etc/dci-openshift-agent/settings.yml -e dci_topic=OCP-4.3
``` 

### dci-openshift-agent workflow

*Step 1 :* State “New job”
- Prepare the `Jumpbox`: `/plays/configure.yml`
- Download Openshift from DCI: `/plays/fetch_bits.yml`

*Step 2 :* State “Pre-run”
- Deploy infrastructure: `/hooks/pre-run.yml`

*Step 3 :* State “Running”
- Configure Openshift nodes: `/hooks/configure.yml`
- Start Openshift installer: `/hooks/running.yml`

*Step 4 :* State “Post-run”
- Start DCI tests (This is empty for now): `/plays/dci-tests.yml`
- Start user specific tests: `/hooks/user-tests.yml`

*Step 5 :* State “Success”
- Launch additional tasks when the job is successful: /hooks/success.yml

*Exit playbooks:*

The 2 following playbooks are executed sequentially at any step that fail: 

- Teardown: /hooks/teardown.yml
- Failure: /plays/failure.yml

*All playbooks located in directory `/etc/dci-openshift-agent/hooks/` are empty by default and should be customized by the user.*

### How to run the full virtualized example

This example will help you to run the `dci-openshift-agent` within one single hardware system by running `libvirt` virtual machines. This example is a good path to understand the `dci-openshift-agent` (all different steps, hooks, settings) and to be used as a development environment.

At this point, the `Jumpbox` is installed with all above prerequisites except the `/etc/dci-openshift-agent/settings.yml` file.

The following commands will guide you to generate and use an appropriate settings file for this scenario.

First, you need to work directly as the `dci-openshift-agent` user:

```
# su - dci-openshift-agent
$ id
uid=990(dci-openshift-agent) gid=987(dci-openshift-agent) groups=987(dci-openshift-agent),107(qemu),985(libvirt) ...
```

Copy all sample files from `dci-openshift-agent` documentation directory to the home directory:

```
$ cp -rp /usr/share/doc/dci-openshift-agent-*/samples/setup_bootstrap ~
```

Run `libvirt_up` playbook to configure libvirt nodes.
This playbook will:

* Create 3 local virtual machines to be used as `System Under Test`
* Create 1 local virtual machine to be used as a `Provisioning node`
* Generate the relative `hosts` file (ready to be used as an inventory for the `dci-openshift-agent`).
* Provide a `pre-run.yml` to be used in your virtual environment.

```
$ cd ~/setup_bootstrap/full_virt
$ ansible-playbook -v libvirt_up.yml
```

Copy the newly created file `hosts` to the `/etc/dci-openshift-agent` directory:

```
$ pwd
/var/lib/dci-openshift-agent/setup_bootstrap/full_virt
$ sudo cp hosts /etc/dci-openshift-agent/
```

At this step, you need to configure the `dci-openshift-agent pre-run playbook` to startup your virtual machines before it schedules any deployment on it.

Copy the libvirt `pre-run.yml` hook:

```
$ pwd
/var/lib/dci-openshift-agent/setup_bootstrap/full_virt
$ sudo cp ../pre-run.yml /etc/dci-openshift-agent/hooks/
```

*The `dci-openshift-agent` is now ready to run the “all in one” virtualized workflow.*

You can check the virtual machines status by using `virsh` command:

```
$ sudo virsh list --all
 Id    Name                           State
----------------------------------------------------
 60    provisionhost                  running
 64    master-0                       running
 65    master-2                       running
 66    master-1                       running
```

You can now interact with the RHOCP cluster:

```
$ export KUBECONFIG=/home/admin/clusterconfigs/auth/kubeconfig
$ oc get pods --all-namespaces

``` 

In case you need to delete the full virtualized environment, you can run the playbook `libvirt_destroy.yml` located in `setup_bootstrap/full_virt`:

```
$ cd ~/setup_bootstrap/full_virt
$ ansible-playbook -v libvirt_destroy.yml
```

## Create your DCI account on distributed-ci.io
Every user needs to create his personal account by connecting to `https://www.distributed-ci.io` by using a Red Hat SSO account.

The account will be created in the DCI database at the first connection with the SSO account. For now, there is no reliable way to know your team automatically. Please contact the DCI team when this step has been reached, to be assigned in the correct organisation.

## License
Apache License, Version 2.0 (see [LICENSE](LICENSE) file)

## Contact
Email: Distributed-CI Team  <distributed-ci@redhat.com>
IRC: #distributed-ci on Freenode

# DCI OpenShift Agent

`dci-openshift-agent` provides Red Hat OpenShift Container Platform (RHOCP) in
Red Hat Distributed CI service.

There are some benefits of running the DCI OCP Agent:

1. Automation of nightly/candidate OCP component testing
2. CI runs on your own hardware
3. Red Hat doesn't have access to your hardware, the agent reports metrics/logs
   back to distributed-ci.io
4. The agent leverages the OpenShift IPI Installer which in turn is based on
   proven ansible tech
5. You have access to all your jobs logs and metrics through distributed-ci.io
   where you can also set notifications for errors/exceptions

## Table of Contents

- [Requirements](#requirements)
  - [Network requirements](#network-requirements)
  - [Systems requirements](#systems-requirements)
    - [Jumpbox requirements](#jumpbox-requirements)
    - [Systems under test](#systems-under-test)
  - [Optional](#optional)
- [Setting up access to DCI](#setting-up-access-to-dci)
- [Installation of DCI Jumpbox](#installation-of-dci-jumpbox)
  - [Installation of OCP Provision Host](#installation-of-ocp-provision-host)
  - [Copying the ssh key to your provisioner](#copying-the-ssh-key-to-your-provisioner)
  - [Jumpbox Configuration](#jumpbox-configuration)
  - [Overloading settings and hooks directories](#overloading-settings-and-hooks-directories)
- [Starting the DCI OCP Agent](#starting-the-dci-ocp-agent)
- [Interacting with your RHOCP Cluster](#interacting-with-your-rhocp-cluster)
- [Troubleshooting common issues](#troubleshooting-common-issues)
- [Keep the DCI OCP Agent Updated](#keep-the-dci-ocp-agent-updated)
- [dci-openshift-agent workflow](#dci-openshift-agent-workflow)
- [Getting Involved](#getting-involved)
- [Create your DCI account on distributed-ci.io](#create-your-dci-account-on-distributed-ci.io)
- [License](#license)
- [Contact](#contact)

## Requirements

### Network requirements

This is a summary taken from the upstream [Network requirements guide from OpenShift](https://openshift-kni.github.io/baremetal-deploy/latest/Deployment#network-requirements_ipi-install-prerequisites):

- Each server needs 2 NICs pre-configured. NIC1 for the private/provisioning
  network and NIC2 for the baremetal network. NIC interface names must be
  identical across all nodes
- Each server's NIC1 (provisioning) must be configured for PXE booting in
  BIOS/UEFI
- Each server must have IPMI configured and functional
- Each server must have static IP addresses for their baremetal NICs *plus* a
  dynamic pool of 5 or more IP addresses with a short TTL (2h) for the
  bootstrap VM
- Must have 2 reserved virtual IPs for API (`api.<cluster>.<domain>`) and
  wildcard ingress (`*.apps.<cluster>.<domain>`) and DNS setup for both. Please
  follow the [Openshift Baremetal DNS server
  configuration](https://openshift-kni.github.io/baremetal-deploy/latest/Deployment#DNS)
  as a reference guide
- Optional - Include DNS entries for the hostnames for each of the servers

![Proposed network diagram](https://lucid.app/publicSegments/view/bedb0b3c-0cca-43ef-9dc6-7ed40ac35506/image.png "Proposed network diagram")

### Systems requirements

`DCI OpenShift Agent` needs a dedicated system to act as a `controller node`.
It is identified as the `DCI Jumpbox` in this document. This system will be
added to a standard OCP topology by being connected to the OCP `baremetal
network`. The `DCI OpenShift Agent` will drive the RHOCP installation workflow
from there.

Therefore, the simplest working setup must be composed of at least **5**
systems (1 system for DCI and 4 systems to match OCP minimum requirements).

Please use the [OpenShift Baremetal Deploy Guide (a.k.a.
`openshift-kni`)](https://openshift-kni.github.io/baremetal-deploy/) as a
reference for how to properly configure the OCP networks, systems and DNS.

Choose the OCP version you want to install and follow steps 1 to 3 to configure
the networks and install RHEL 8 on the **OpenShift Provisioning node**. Steps
after 4 will be handled by the `dci-openshift-agent`.

1. [Setting up access to DCI](#setting-up-access-to-dci)
2. [Installation of DCI Jumpbox](#installation-of-dci-jumpbox)
3. [Jumpbox Configuration](#jumpbox-configuration)
4. [Copying the ssh key to your provisioner](#copying-the-ssh-key-to-your-provisioner)
5. [Starting the DCI OCP Agent](#starting-the-dci-ocp-agent)

As mentioned before, the **DCI Jumpbox** is NOT part of the RHOCP cluster. It
is only dedicated to download `RHOCP` artifacts from `DCI` public
infrastructure and to schedule the RHOCP cluster deployment across all systems
under test (1x OpenShift Provisioning node and several OCP nodes).

The **OpenShift Provisioning node** is used by the OpenShift installer to
provision the OpenShift cluster nodes.

The 3 remaining systems will run the freshly installed OCP Cluster. “3” is the
minimum required number of nodes to run RHOCP but it can be more if you need
to.

#### Jumpbox requirements

The `Jumpbox` can be a physical server or a virtual machine.
In any case, it must:

- Be running the latest stable RHEL release (**8.4 or higher**) and registered
  via RHSM.
- Have at least 160GB of free space available in `/var`
- Have access to Internet
- Be able to connect the following Web urls:
  - DCI API, https://api.distributed-ci.io
  - DCI Packages, https://packages.distributed-ci.io
  - DCI Repository, https://repo.distributed-ci.io
  - EPEL, https://dl.fedoraproject.org/pub/epel/
  - QUAY, https://quay.io
  - RED HAT REGISTRY, https://registry.redhat.io
  - RED HAT SSO, https://access.redhat.com
  - RED HAT CATALOG, https://catalog.redhat.com
- Have a static internal (network lab) IP
- Be able to reach all systems under test (SUT) using (mandatory, but not
  limited to):
  - SSH
  - IPMI
  - Serial-Over-LAN or other remote consoles (details & software to be provided by the partner)
- Be reachable by the Systems Under Test by using:
  - DHCP
  - PXE
  - HTTP/HTTPS

NOTE: Make sure rhel-8-for-x86_64-appstream-rpms repo provides access to
libvirt => 6.0.0 packages

#### Systems under test

`Systems under test` will be **installed** through DCI workflow with each job
and form the new “fresh” RHOCP cluster.

All files on these systems are NOT persistent between each
`dci-openshift-agent` job as the RHOCP cluster is reinstalled at each time.
Therefore, every expected customization and tests have to be automated from the
DCI Jumpbox (by using hooks) and will therefore be applied after each
deployment (More info at [Jumpbox Configuration](#jumpbox-configuration)).

### Optional

- We strongly advise the partners to provide the Red Hat DCI team with access
  to their jumpbox. This way, Red Hat engineers can help with initial setup and
  troubleshooting.
- We suggest to run the `full virtualized` provided example first to understand
  how the `dci-openshift-agent` works before going to production with a real
  lab.

## Setting up access to DCI
The DCI dashboard gives you a view into what jobs you have run in your distributed agent. In order to gain access to it you have to:

1. Go to distributed-ci.io and click login. You will be redirected to
   ssh.redhat.com so you'll use your RH account credentials
2. If you are not part of any teams you can contact an admin to get yourself
   added
3. You will have to create a Remote CI for use later, go on the left navigation bar on the `Remotecis` option and click on "Create a new remoteci"
4. Fill out the description and which team it belongs to then click Create
5. You should see your newly created remoteci in the list, you can get the
   credentials by click the button in the Authentication column. You will need
   these to [configure your jumpbox](#jumpbox-configuration) further down

## Installation of DCI Jumpbox

Before proceeding you should have set up your networks and systems according to
the baremetal-deploy doc that was referenced above.

Provision the Jumphost with RHEL8. This includes subscribing the host to RHSM
and ensuring it's receiving updates.

The `dci-openshift-agent` is packaged and available as a RPM file.
However,`dci-release` and `epel-release` must be installed first:

```console
# dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
# dnf -y install https://packages.distributed-ci.io/dci-release.el8.noarch.rpm
# subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
# subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
# dnf -y install dci-openshift-agent
```

### Installation of OCP Provision Host

The provision host is part of the OCP requirements, as such you should follow
the guide linked before. The main things you need to know about the provision
host are:

- Provision with RHEL8
- Subscribe to RHSM and make sure it is receiving updates
- Must have 2 NICs: one for the baremetal public/routed network and another for
  the provisioning private network
- Create a `kni` user

### Copying the ssh key to your provisioner

```console
# su - dci-openshift-agent
% ssh-keygen
% ssh-copy-id kni@provisionhost
```

### Jumpbox Configuration

There are three configuration files for `dci-openshift-agent`:
`/etc/dci-openshift-agent/dcirc.sh`, `/etc/dci-openshift-agent/hosts` and
`/etc/dci-openshift-agent/settings.yml`.

#### `/etc/dci-openshift-agent/dcirc.sh`

!!! NOTE
    The default `dcirc.sh` is shipped as
    `/etc/dci-openshift-agent/dcirc.sh.dist`.

Copy the [recently obtained API credentials](#setting-up-access-to-dci) and
paste it on the Jumpbox to `/etc/dci-openshift-agent/dcirc.sh`.

This file should be edited once and looks similar to this:

```bash
#!/usr/bin/env bash
DCI_CS_URL="https://api.distributed-ci.io/"
DCI_CLIENT_ID=remoteci/<remoteci_id>
DCI_API_SECRET=<remoteci_api_secret>
export DCI_CLIENT_ID
export DCI_API_SECRET
export DCI_CS_URL
```

#### `/etc/dci-openshift-agent/settings.yml`

This is the dci openshift agent settings (format is YAML). Use this to specify
which version of OCP to install.

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
| dci\_previous\_job\_id             | False    | String  | ""                                               | Previous job UUID
| dci\_must\_gather\_images          | False    | List    |["registry.redhat.io/openshift4/ose-must-gather"] | List of the must-gather images to use when retrieving logs.\*  |
| dci\_teardown\_on\_failure         | False    | Boolean | False                                            | Whether or not execute the teardown hook on a failure          |
| dci\_teardown\_on\_success         | False    | Boolean | True                                             | Whether or not execute the teardown hook on success            |
| dci\_openshift\_agent\_conformance | False    | String  |                                                  | If defined it will run that category of conformance test       |
| dci\_disconnected                  | False    | Boolean | False                                            | Signals that the OCP agent will run in disconnected            |
| dci\_openshift\_csi_test\_manifest | False    | String  | ""                                               | Manifest file that contains the tests for CSI validation. <br>Please review [test-parameters](https://redhat-connect.gitbook.io/openshift-badges/badges/container-storage-interface-csi-1/workflow/setup-test-parameters) and [csi-e2e](https://github.com/kubernetes/kubernetes/tree/v1.16.0/test/e2e/storage/external) <br> for details about drivers capabilities |
| baremetal\_deploy\_version         | False    | String  | HEAD                                             | Allows you to lock upstream baremetal repo to specific version |
| http\_proxy                        | False    | String  |                                                  | http proxy to use                                              |
| https\_proxy                       | False    | String  |                                                  | https proxy to use                                             |
| no\_proxy\_list                    | False    | String  |                                                  | Comma separated list of hosts not going through the proxies    |
| openshift\_secret                  | False    | Dict    | auths:                                           | Additional auths will be combined                              |
|                                    |          |         |   quay.io/rhceph-dev:                            | You can also override the default auths provided by DCI        |
|                                    |          |         |     auth: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx    | Any dict entry with the same name will override default values |

[Here](https://docs.openshift.com/container-platform/4.7/support/gathering-cluster-data.html)
you can find information on the available must-gather images. Also, bear in
mind that authentication is required to retrieve the images so you will need a
valid RH subscription

Example:

```YAML
---
dci_topic: "OCP-4.9"
dci_name: "ocp-4.9-job"
dci_configuration: "baremetal"
dci_url: "https://softwarefactory-project.io/r/c/dci-openshift-agent/+/22195"
dci_comment: "test-runner: use the new url metadata for jobs"
dci_tags: ["debug", "gerrit:22195"]
...
```

#### `/etc/dci-openshift-agent/hosts`

This file is an Ansible inventory file (format is `.ini`) and includes the
configuration for the `dci-openshift-agent` job and the inventory for the
masters, workers (if any) and the provisioner.

Example:

```ini
[all:vars]
# The NIC used for provisioning network on all nodes
prov_nic=eno1
# The NIC used for baremetal network on all nodes
pub_nic=eno2
# Base domain
domain=example.com
# Name of the cluster
cluster=dciokd
# The directory used to store the cluster configuration files (install-config.yaml, pull-secret.txt, metal3-config.yaml)
dir="{{ ansible_user_dir }}/clusterconfigs"
# Virtual IP for the cluster ingress
dnsvip=1.2.3.4
# Override which NIC masters use for the private/provisioning network
;masters_prov_nic=eno1
# Disable TLS verification of BMC certificates
;disable_bmc_certificate_verification=true
# Enable some light caching on the provision host
;cache_enabled=false

# Activate disconnected mode in DCI OCP agent, requires you to set the next variables as well
;dci_disconnected=true
# Must be reachable from the cluster
;webserver_url="http://<jumpbox IP/DNS>:8080"
# Path on the jumpbox
;disconnected_registry_auths_file=/path/to/auths.json
# Path on the jumpbox
;disconnected_registry_mirrors_file=/path/to/trust-bundle.yml
# Path on the jumpbox, must have enough space to hold your qcow images
;provision_cache_store="/path/to/qcow/cache"
# Registry host that will mirror all container images
;local_registry_host=local-registry
# Registry port
;local_registry_port=5000
# Registry namespace
;local_repo=ocp4/openshift4

# Master nodes
[masters]
master-0 name=master-0 ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-master-0.dciokd.example.com provision_mac=aa:bb:cc:dd:ee:ff
master-1 name=master-1 ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-master-1.dciokd.example.com provision_mac=aa:bb:cc:dd:ee:ff
master-2 name=master-2 ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-master-2.dciokd.example.com provision_mac=aa:bb:cc:dd:ee:ff

[masters:vars]
role=master
hardware_profile=default
# If needed, you can set node labels too
;labels='{"node-role.kubernetes.io.foo":"", "node-role.kubernetes.io.bar":""}' # example

# Worker nodes
[workers]
worker-0 name=worker-0 ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-worker-0.dciokd.example.com provision_mac=aa:bb:cc:dd:ee:ff

[workers:vars]
role=worker
hardware_profile=default
# If needed, you can set node labels too
;labels='{"node-role.kubernetes.io.foo":"", "node-role.kubernetes.io.bar":""}' # example

# Provision Host
[provisioner]
provisionhost ansible_user=kni prov_nic=eno1 pub_nic=ens3 ansible_ssh_common_args="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
```

NOTE: If the jumpbox server is in a different network than the baremetal
network, then include extcirdnet=<baremetal-network/mask> in the all:vars
section of the inventory

### Overloading settings and hooks directories

To allow storing the settings and the hooks in a different directory,
you can set `/etc/dci-openshift-agent/config` like this:

```console
CONFIG_DIR=/var/lib/dci-openshift-agent/config
```

This will allow you to use a version control system for all your settings.

If you want to also store the hooks in the same directory, you have to
specify `dci_config_dirs` in your `settings.yml`. Example:

```YAML
---
dci_topic: OCP-4.9
dci_config_dirs: [/var/lib/dci-openshift-agent/config]
```

## Starting the DCI OCP Agent

Now that you have configured the `DCI OpenShift Agent`, you can start the
service.

Please note that the service is a systemd `Type=oneshot`. This means that if
you need to run a DCI job periodically, you have to configure a `systemd timer`
or a `crontab`.

```console
$ systemctl start dci-openshift-agent
```

If you need to run the `dci-openshift-agent` manually in foreground,
you can use this command line:

```console
# su - dci-openshift-agent
% dci-openshift-agent-ctl -s -- -v
```

## Interacting with your RHOCP Cluster

After you run a DCI job you will be able to interact with the RHOCP cluster using the OC client, the API, or the GUI.

1. Using the OC client
  ```bash
  $ export KUBECONFIG=/home/<user>/<clusterconfigs-path>/kubeconfig
  $ oc get nodes
  ```
2. Using the GUI/API

Obtain the credentials generated during the installation from /home/`<user>`/`<clusterconfigs-path>`/ocp_creds.txt in the jumphost.

Get the the URL of the cluster GUI:
```bash
$ oc whoami --show-console
https://console-openshift-console.apps.<cluster>.<domain>
```

Note: The dci-openshift-agent is part of a [Continuous integration](https://en.wikipedia.org/wiki/Continuous_integration) tool aimed to perform OCP deployments, should not be considered for production workloads. Use the above connection methods if some troubleshooting is required.

## Troubleshooting common issues

- [Basic configuration](#troubleshooting-basic-configuration)
- [Network connectivity](#troubleshooting-network-connectivity)
- [OpenShift bootstrap](#troubleshooting-ocp-bootstrapping)
- [OpenShift install](#troubleshooting-ocp-install)

### Troubleshooting basic configuration

Review the following checklist to make sure you've got all the basic pieces in
place:

- Is the DCI repo configured?
- Is the dci-openshift-agent package the latest version?
- Does my `/etc/dci-openshift-agent/dcirc.sh` file contain my remote CI
  credentials as per the distributed-ci.io dashboard?
- Does my `/etc/dci-openshift-agent/hosts` reflect my cluster's expected
  configuration? Check the following variables:
  - `cluster`
  - `domain`
  - `prov_nic`
  - `pub_nic`
  - IPMI configuration for all nodes in OCP cluster: `ipmi_user`,
    `ipmi_password`, `ipmi_address`
  - MAC addresses for all nodes in OCP cluster
- Does my `/etc/dci-openshift-agent/settings.yml` file reflect the right
  topic/component for my needs?
- Is my `dci-openshift-agent` SSH key transferred to the provision host? e.g.
  can I SSH without a password from Jumpbox -> provisioner?

### Troubleshooting network connectivity

First, take another look at the [network requirements](#network-requirements)
section and make sure your setup looks similar to the proposed basic diagram.
Your particular lab may differ in how things are laid out, but the basic points
to look for are:

- Your `provisioning` network should be treated as an exclusive "out of band"
  network only intended to PXE boot the initial cluster OS
- Your `baremetal` network should be capable of routing to:
  - Your jumpbox
  - Your cluster nodes' BMCs (e.g. your management network)
- You should have outbound internet access from your Jumpbox (and OCP cluster
  unless in [disconnected mode](docs/disconnected_en.md))
- Your `baremetal` network should be DHCP enabled and have addresses for all of
  your cluster nodes *plus* the bootstrap VM (usually not an issue but make
  sure there are enough IP addresses to lease)
- Your Jumpbox, provisioner, and cluster nodes all should be able to resolve
  your API and your wildcard DNS entries e.g. `api.<cluster>.<domain>` and
  `*.apps.<cluster>.<domain>`
- The provision host should have 2 bridges setup: one for the `provisioning`
  network and another for the `baremetal` network, are both setup? Are the
  functional?

Here are a few things you can check to make sure the above assertions are true:

- Can I query the power status of the cluster nodes from the provisioner and
  control-plane nodes via e.g. `ipmitool`?
- Can I curl one of the mirror.openshift.com resources from the provisioner and
  cluster nodes?
- Is the lab's DNS resolvable from all places via e.g. `dig
  api.<cluster>.<domain>` and `dig foo.apps.<cluster>.<domain>`?


### Troubleshooting OCP bootstrapping

You can monitor the bootstrap/install process by logging into the provision
host and tailing the file `~/clusterconfigs/.openshift_install.log`.

If you're having issues once the agent gets to the point where
`baremetal-install` is called, you can check a few things:

- Check the `~/clusterconfigs/install-config.yaml.bkup` file in your provision
  host (this is a copy of the install manifest fed to `baremetal-install`) and
  make sure the manifest looks correct
- Is the bootstrap VM coming up? e.g. `sudo virsh list --all` should list a VM
  named `*-bootstrap` about 5-10 minutes after you started the run
- Is the bootstrap VM getting IP address from the `baremetal` network? Run
  `virsh console <bootstrap VM>` and a linux login prompt should be visible,
  hit `<Enter>` and it should show 2 IP addresses: a DHCP one as per your
  configuration, and a static `172.22.0.22` on the `provisioning` network
- Is your bootstrap VM up coming up correctly? You can `ssh core@172.22.0.2`
  and check the status of the pods running on the system by `sudo podman ps`.
  You should see (after a few minutes) some pods named
  `ironic-{api,conductor,inspector}`
- Check the logs of the `ironic-*` pods with `sudo podman logs <pod>` and look
  for errors/exceptions
- Is your `ironic-inspector` able to interact with the BMCs? Try logging
  yourself to the pod (`sudo podman exec -it ironic-inspector /bin/sh`) and
  make sure there is connectivity to the BMC e.g. `ipmi -I lanplus -H <BMC
  host> -U <BMC user> -P <BMC password> power status`

### Troubleshooting OCP install

During the deployment, ironic services are started temporally in the bootstrap
VM, to help bootstrapping the master nodes.
Then after the master nodes are ready to take the role, bootstrap VM is deleted
and ironic services are started in the cluster.
At both stages you can interact with ironic to see details of the nodes

If you want to interact with ironic services during the bootstrap, get the
baremetal network IP of ironic service from the bootstrap VM

```console
[core@localhost ~]$ sudo ss -ntpl | grep 6385
[core@localhost ~]$ ip a s ens3
```

Get the bootstrap VM ironic credentials from the terraform variables back in
the provision host

```console
[dci@provisionhost ~]$ grep ironic_ clusterconfigs/terraform.baremetal.auto.tfvars.json
  "ironic_username": "bootstrap-user",
  "ironic_password": "foo",
```

If you want to interact with ironic services in the cluster, get the IP of
ironic service from the metal3 resources

```console
[dci@provisionhost ~]$ export KUBECONFIG=/home/dci/clusterconfigs/auth/kubeconfig
[dci@provisionhost ~]$ oc -n openshift-machine-api get pods # find the metal3 pod
[dci@provisionhost ~]$ oc -n openshift-machine-api describe pod <pod> | egrep ^IP:
IP:                   192.168.123.148
[dci@provisionhost ~]$ oc -n openshift-machine-api get secrets metal3-ironic-password \
  -o jsonpath='{.data.username}' | base64 -d
ironic-user
[dci@provisionhost ~]$ oc -n openshift-machine-api get secrets metal3-ironic-password \
  -o jsonpath='{.data.password}' | base64 -d
bar
```

Then prepare a clouds.yaml with the following information, and replace the IP
addresses and password accordingly

!!! NOTE
    Starting with OCP 4.7 `metal3-boostrap` service uses `auth_type:
    http_basic`, but in in older versions it uses `auth_type: none` so there's
    no need to set auth section with the credentials

```YAML
clouds:
  metal3-bootstrap:
    auth_type: http_basic
    auth:
      username: bootstrap-user
      password: $BOOTSTRAP_PASSWORD
    baremetal_endpoint_override: http://IP-Provisioining-bootstrapVM-IP:6385
    baremetal_introspection_endpoint_override: http://IP-Provisioining-bootstrapVM-IP:5050
  metal3:
    auth_type: http_basic
    auth:
      username: ironic-user
      password: $IRONIC_PASSWORD
    baremetal_endpoint_override: http://IP-Provisioining-Master-IP:6385
    baremetal_introspection_endpoint_override: http://IP-Provisioining-Master-IP:5050
```

Back in the provisioning host, install podman and start a container, set
`OS_CLOUD` with metal3 if you want to use the ironic services on the cluster,
or metal3-bootstrap if you want to use the services on the bootstrap VM (if
still running)

```console
[dci@provisionhost ~]$ sudo dnf install -y podman
[dci@provisionhost ~]$ podman run -ti --rm \
  --entrypoint /bin/bash \
  -v /home/dci/clouds.yaml:/clouds.yaml:z \
  -e OS_CLOUD=metal3
  quay.io/metal3-io/ironic-client
```

Finally from the pod you started, you can run ironic baremetal commands

```console
[root@8ce291ff4f4a /]# baremetal node list
+--------------------------------------+----------+--------------------------------------+-------------+--------------------+-------------+
| UUID                                 | Name     | Instance UUID                        | Power State | Provisioning State | Maintenance |
+--------------------------------------+----------+--------------------------------------+-------------+--------------------+-------------+
| ba3d1990-e860-4685-9929-3c3356e6e29e | master-1 | 7a116082-1b8a-4f65-9991-242dd56ed44b | power on    | active             | False       |
| 3ab260c7-9a1e-48bf-841a-473a3cec2cbd | master-2 | a9658128-570c-45ad-9ef6-d4721aeaeb81 | power on    | active             | False       |
| d67ade66-d9e1-4825-b53e-381870ff5c81 | master-0 | 728106a3-1994-4e86-9a8c-838becf22aa5 | power on    | active             | False       |
+--------------------------------------+----------+--------------------------------------+-------------+--------------------+-------------+
```

## Keep the DCI OCP Agent Updated

It is recommended to keep the Jumpbox server updated, enable dnf-automatic
updates to make sure system is using latest dci-openshift-agent

Install dnf-automatic

```console
# dnf install -y dnf-automatic
```

Modify the default configuration to enable automatic downloads and apply
updates

```console
# vi /etc/dnf/automatic.conf
...
download_updates = yes
apply_updates = yes
...
```

Enable the dnf-automatic.timer

```console
# systemctl enable --now dnf-automatic.timer
```

## dci-openshift-agent workflow

0. "New DCI job"
    - Create a DCI job
    - _tags: job_
    - _runs on: localhost_

1. "Pre-run"
    - Prepare the `Jumpbox`: `/plays/pre-run.yml`
    - Trigger partner Jumpbox preparation if needed: `/hooks/pre-run.yml`
    - _tags: pre-run_
    - _runs on: localhost_

2. "Configure"
    - Prepare provisioner: `/plays/configure-provisioner.yml`
    - Trigger partner Provisioner preparation if needed: `/hooks/configure.yml`
    - _tags: running, configure_
    - _runs on: provisioner_

3. "DCI Main"
    1. "Install" (`dci_main` is "install" or undefined)
        - Start OpenShift install: `/plays/install.yml` 
        - Trigger partner install hook if needed: `/hooks/install.yml`.
        - _tags: running, installing, hook-installing_
        - _runs on: provisioner_

    2. "Upgrading" (`dci_main` is "upgrade")
        - Start OpenShift upgrade: `/plays/upgrade.yml`
        - Trigger partner upgrade hook if needed `/hooks/upgrade.yml`
        - _tags: running, upgrading, hook-upgrading_
        - _runs on: provisioner_

    3. "Deploy operators"
        - start operator deployment: `/plays/deploy-operators.yml`
        - _tags: running, operator-deployment_
        - _runs on: provisioner_

4. "Red Hat tests"
    - start Red Hat tests: `/plays/tests.yml`
    - _tags: running, testing, redhat-testing_
    - _runs on: localhost_

5. "Partner tests"
    - start partner tests: `/hooks/tests.yml`
    - _tags: running, testing, partner-testing_
    - _runs on: localhost_

6. "Post-run"
    - Start post-run to collect results: `/plays/post-run.yml` and
      `/hooks/post-run.yml`
    - Note: All results files (logs, tests, ...) must be stored within the `{{
      dci_cluster_configs_dir }}/` directory in order to be properly uploaded to
      the DCI server. Test result files must follow the Junit format and the
      file name must follow the pattern `junit_*.xml`
    - _tags: post-run_
    - _runs on: localhost_

7. "Success"
    - Launch additional tasks when the job is successful: `/hooks/success.yml`
    - _tags: success_
    - _runs on: localhost_

_Exit playbooks:_
The following playbooks are executed sequentially at any step that fail:

- Teardown: `/hooks/teardown.yml` which is executed only when the boolean `dci_teardown_on_success` is set to `true` (set to `true` by default)
- Failure: `/plays/failure.yml` and `/hooks/failure.yml` during the `running` steps and `/plays/error.yml` during the other steps. `/hooks/failure.yml` was added to allow custom debug command to gather more meaningful logs.

**NOTE**: All the task files located in directory
`/etc/dci-openshift-agent/hooks/` are empty by default and should be customized
by the user.

All the tasks prefixed with `test_` will get exported in Junit using the
[Ansible Junit
callback](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/junit_callback.html)
and submitted automatically to the DCI control server.

## Getting involved
Refer to [the development guide](docs/development.md)

## Create your DCI account on distributed-ci.io

Every user needs to create his personal account by connecting to
https://www.distributed-ci.io by using a Red Hat SSO account.

The account will be created in the DCI database at the first connection with
the SSO account. For now, there is no reliable way to know your team
automatically. Please contact the DCI team when this step has been reached, to
be assigned in the correct organisation.

## License

Apache License, Version 2.0 (see [LICENSE](LICENSE) file)

## Contact

Email: Distributed-CI Team <distributed-ci@redhat.com>

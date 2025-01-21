# Agent Based Installation

The Agent Based Installer (ABI) is yet another method DCI OCP
agent can use to install OpenShift clusters. If you're curious about the
[ABI](https://docs.redhat.com/en/documentation/openshift_container_platform/4.12/html-single/installing_an_on-premise_cluster_with_the_agent-based_installer/indexr) you can also
read [meet the new agent based openshift installer](https://cloud.redhat.com/blog/meet-the-new-agent-based-openshift-installer-1).
This document will focus on explaining how the ABI can be used to install an
OpenShift cluster through the DCI agent.


## Table of contents

* [Requirements](#requirements)
* [An explanation of the process](#an-explanation-of-the-process)
* [Configuration](#configuration)
  * [Vendors](#vendors)
  * [Disconnected Environment](#disconnected-environment)
* [Virtual Lab Quick Start](#virtual-lab-quick-start)
  * [Single Node Openshift](#single-node-openshift)

## Requirements

* 3 nodes *minimum* with:
  * 8 CPU cores
  * 16G RAM
  * 100GB Storage

AI does not use a dedicated *bootstrap* node, instead it re-purposes the
bootstrap node into a control plane node when it completes the installation.

!!! note
    ABI installer in available starting OCP 4.12.

For the DCI Jumpbox you will need:

* A RHEL 8 server with:
  * 100G of available disk in the location where you configure the service to
    store the ISO files. Keep in mind that you will require more disk space if
    you plan on using a disconnected environment for the local cache
  * 8G of RAM


## An explanation of the process

1.  Process starts, the agent creates a new job in the [DCI
    dashboard](https://www.distributed-ci.io/login)
1.  Some checks are performed to make sure the installation can proceed
1.  NTP server is installed/configured
1.  HTTP server is created/configured
1.  If this is a disconnected / restricted network environment:
    1. The OCP release artifacts are downloaded
    1. A container registry is created
    1. Container/operator images are mirrored to the local registry
    1. Configuration is put in place so ABI uses the locally
       cached resources
1.  If VMs are defined in the inventory file, those must exist
1.  DNS server is installed/configured
1.  Sushy tools service is configured (if using local VMs)
1.  A Discovery ISO file is created and mounted on all nodes in the cluster via
    redfish API / virtual media over HTTP
1.  The ABI installation is triggered
1.  Installation process is monitored until completion
1.  The `KUBECONFIG` file is fetched and used to perform some connectivity
    checks on the OCP cluster
1.  Process ends, the job status is set to complete in the DCI dashboard

## Configuration

Before anything else you will need to set `install_type: abi` in your
inventory or pipeline ansible extra variables. We do this because AI is not the
default install method in the DCI OCP Agent.

The first change you will notice right away is that the inventory file has a
completely different format: instead of the INI-style format default
configuration shows, it is a YAML file. The YAML file offers more capabilities
to represent more comples variables (e.g. dicts, lists) then INI files, so
familiarize yourself with it.

The following variables control where **in the jumpbox** the different pieces
will store their data, make sure you have enough space (at least 200G) to hold
your cached files, and routinely monitor for disk consumption:

  * `downloads_path` where the OCP files (ISO files, RAW images, client tools,
    etc) will be downloaded
  * `registry_dir` where the locally configured container registry layers will
    be stored
  * `sushy_dir` (for a virtual environment only) stores the files needed by the
    [sushy service](https://docs.openstack.org/sushy/latest/), this directory
    may grow indiscriminately if left unchecked
  * `http_dir` will store the files served over HTTP e.g. the discovery ISO
  * `vm_create_scripts_dir` (for a virtual environment only): holds the shell
    scripts that tell libvirt how to create the VMs.
  * `images_dir` (for a virtual environment only): where the generated
    libvirt OS images will be stored


### Vendors

Under the nodes section where each member of the control/compute planes is
defined you will see a vendor variable.  If it's not specified at the node
level it's probably specified at the parent and inherited.

Types of vendors:

* KVM
* PXE
* DELL
* HPE
* LENOVO
* SUPERMICRO
* ZT

KVM will generate virtual hosts in libvirt and PXE will setup dhcp and tftpboot
so that your systems can netboot.  All the other types are vendor specific and
use redfish to attach virtual media for discovery.

### Disconnected environment

This setup is a little bit different from the regular disconnected environment
from the IPI method mainly because of the changes in the underlying mechanism
that performs the installation and the inventory format change.

If you need to setup a disconnected environment, there's a couple more things
you'll have to adjust:

* Set `dci_disconnected` to true, this can be done in the inventory file or the
  `settings.yml` file
* Turn on the following variables:
  * `setup_registry_service`: Creates a container registry in the jumpbox
  * `use_local_registry`: Tells the Installer to use the previously
    configured container registry
  * `setup_ntp_service` (if needed): Configures an NTP server so the cluster
    can synchronize with. This is turned on by default in the libvirt template
  * `setup_dns_service` (if needed): Configures a DNS server so the cluster can
    resolve names. This is turned on by default in the libvirt template

## Virtual Lab Quick Start

If you want to get started quickly with the OCP Agent to test ABI the path is fairly easy,
assuming you have a jumpbox that meets the
requirements. Here's a quick step by step list of what you need to do:

1.  Create (if there is none) an SSH key for the `dci-openshift-agent` user and
    add it to its own `~/.ssh/authorized_keys`
1.  Generate the libvirt test inventory file from the sample template, there
    are 3 templates to choose from: `sno` (single node openshift),
    `controlplane` (only 3 control plane nodes), and `split` (3+3 control and
    compute plane nodes). To generate the inventory file, login to your jumpbox
    and execute the following as the dci-openshift-agent user:

    ```bash
    CONFIG=sno  # or 'controlplane' or 'split'
    cd ~/samples/abi_on_libvirt
    ansible-playbook -i $PWD/dev/$CONFIG parse-template.yml
    ```

1.  Inspect the generated `~dci-openshift-agent/hosts` file and adjust as needed
1.  Copy the generated file from `~dci-openshift-agent/hosts` to
    `/etc/dci-openshift-agent/hosts`
1.  Start the agent

That's it, after the process is complete, you should be left with a
`~dci-openshift-agent/clusterconfigs-dciokd/kubeconfig` file which you can use
to interact with your OCP cluster.

!!! note
    The name of the cluster is prepended to the clusterconfigs directory, if
    you change the cluster name then the path to the `kubeconfig` file will
    need to be adjusted


### Single Node Openshift

If you followed the libvirt quickstart above, you can see right away there's a few notable differences between SNO and the other cluster configurations:

1.  There are no nodes defined in the compute plane section
1.  There is a single node defined in the control plane section
1.  *Both* the `api_vip` and `ingress_vip` values are pointed to the **same IP
    address you gave the single node**
1.  Because SNO requires a minimum of 8 cores, make sure your `vm_spec` in your
    `vm_nodes` section for your control plane has `cpu_cores: 8` (it is
    possible to adjust the memory and disk size in this section too)

That should be all that is required to install in SNO mode, the playbooks will
install a SNO cluster and leave you with a kubeconfig/access to the cluster
once finished.

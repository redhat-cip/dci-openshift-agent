# Assisted Installer Based Installation

The Assisted Installer (AI for short in this doc) is yet another method DCI OCP
agent can use to install OpenShift clusters. If you're curious about the
[Assisted Installer](https://github.com/openshift/assisted-installer) you can
read
[several](https://cloud.redhat.com/blog/openshift-assisted-installer-is-now-generally-available)
[resources](https://cloud.redhat.com/blog/assisted-installer-on-premise-deep-dive)
[already out
there](https://docs.openshift.com/container-platform/4.10/installing/installing_on_prem_assisted/assisted-installer-preparing-to-install.html).
This document will focus on explaining how the AI can be used to install an
OpenShift cluster through the DCI agent.


## Table of contents

* [Requirements](#requirements)
* [An explanation of the process](#an-explanation-of-the-process)
* [Configuration](#configuration)
  * [Disconnected Environment](#disconnected-environment)
* [Virtual Lab Quick Start](#virtual-lab-quick-start)
  * [Single Node Openshift](#single-node-openshift)


## Requirements

You can consult the [upstream
documentation](https://docs.openshift.com/container-platform/4.10/installing/installing_on_prem_assisted/assisted-installer-preparing-to-install.html)
on the prerequisites needed for a cluster, but they are basically the same as
with any other OCP cluster you intend to run, to summarize, for a baremetal
cluster you will need:

* 3 nodes *minimum* with:
  * 8 CPU cores
  * 16G RAM
  * 100GB Storage

AI does not use a dedicated *bootstrap* node, instead it re-purposes the
bootstrap node into a control plane node when it completes the installation.

For the DCI Jumpbox you will need:

* A RHEL 8 provisioned server with:
  * 8G of RAM just to run the AI service
  * 100G of disk space in the location where you configure the service to store
    the ISO files


## An explanation of the process

The installation is a little different from the default IPI install. First of
all, we leverage the [crucible
project](https://github.com/redhat-partner-solutions/crucible) to perform the
installation. Crucible is entirely based on ansible, so that's why we're able
to integrate it so seamlessly with the OCP agent.

Most of the heavy lifting is done by crucible, we "decorate" the process around
by having the DCI specific bits trigger in the proper places. Here's more or
less a breakdown of the whole process

1.  Process starts, the agent creates a new job in the [DCI
    dashboard](https://www.distributed-ci.io/login)
1.  Some checks are performed to make sure the installation can proceed
1.  NTP server is installed/configured
1.  If this is a disconnected / restricted network environment:
    1. The OCP release artifacts are downloaded
    1. A container registry is created
    1. Container/operator images are mirrored to the local registry
    1. An HTTP server is created
    1. Configuration is put in place so the Assisted Installer uses the locally
       cached resources
1.  VM are created if defined in the inventory file
1.  DNS server is installed/configured
1.  The Assisted Installer service is setup and started
1.  Sushy tools service is configured
1.  A Discovery ISO file is created and mounted on all nodes in the cluster via
    sushy tools / virtual media over HTTP
1.  A new cluster is created in the Assisted Installer service
1.  Nodes are rebooted, they will use the discovery ISO previously mounted to
    talk to the Assisted Installer service and fetch their installation /
    configuration
1.  Installation process is monitored until completion
1.  The `KUBECONFIG` file is fetched and used to perform some connectivity
    checks on the OCP cluster
1.  Process ends, the job is completed in the DCI dashboard

## Configuration

The first change you will notice right away is that the inventory file has a
completely different format: instead of the INI-style format default
configuration shows, it is a YAML file. Take a look at the contents of
[`samples/assisted/hosts.in`](https://github.com/redhat-cip/dci-openshift-agent/blob/master/samples/assisted/hosts.in)
file in the source repo and adjust as needed. This file comes ready to work in
a connected environment, if this fits your use case you only need to adjust
your node details e.g. your cluster node details.

### Vendor

Under the nodes section where each master and worker is defined you will see a vendor variable.  If it's not specified at the node level it's probably specified at the parent and inherited.

Types of vendors:

* KVM
* PXE
* DELL
* HPE
* LENOVO
* SUPERMICRO
* ZT

KVM will generate virtual hosts in libvirt and PXE will setup dhcp and tftpboot so that your systems can netboot.  All the other types are vendor specific and use redfish to attach virtual media for discovery.

### Disconnected environment

This setup is a little bit different from the regular disconnected environment from the IPI method mainly because of the changes in the underlying mechanism that performs the installation and the inventory format change.

If you need to setup a disconnected environment, there's a couple more things
you'll have to adjust:

* Set `dci_disconnected` to true, this can be done in the inventory file or the
  `settings.yml` file
* Adjust the section called **Restricted Network configuration** as shown in
  `samples/assisted/hosts.in` file. Here's a brief explanation of each var:
  * `setup_registry_service`: Creates a container registry in the jumpbox
  * `setup_http_store_service`: Creates an HTTP cache in the jumpbox
  * `use_local_registry`: Tells the Assisted Installer to use the previously
    configured container registry
  * The *Local Cache configuration* sub section serves to tell the agent where
    in the jumpbox we're going to store the cached files. Make sure wherever
    you put them there's enough space (at least 200G) to hold your cached
    files, and routinely monitor for disk consumption:
    * `downloads_path` where the OCP files (ISO files, RAW images, client
      tools, etc) will be downloaded
    * `assisted_installer_dir` where the data needed by the Assisted Installer
      service(s) will be stored such as database files, etc
    * `registry_dir` where the locally configured container registry layers
      will be stored
    * `sushy_dir` stores the files needed by the [sushy
      service](https://docs.openstack.org/sushy/latest/), this directory may
      grow indiscriminately if left unchecked, as it creates boot ISO files for
      every node install
    * `http_dir` will store the files served over HTTP e.g. the discovery ISO
    * `vm_create_scripts_dir` **for a virtual environment only**: holds the
      shell scripts that tell libvirt how to create the VMs
    * `images_dir` **for a virtual environment only**: where the generated
      libvirt OS images will be stored


## Virtual Lab Quick Start

If you want to get started quickly with the OCP Agent to test the Assisted
Installer the path is fairly easy, assuming you have a jumpbox that meets the
requirements. Here's a quick step by step list of what you need to do:

1.  Create an SSH key for the `dci-openshift-agent` user and add it to its own
    `~/.ssh/authorized_keys` **and** to root's authorized keys, in such a
    manner that you can `ssh dci-openshift-agent@localhost` and `ssh
    root@localhost`
1.  Generate the libvirt test inventory file from the sample template, there
    are 3 templates to choose from: `sno` (single node openshift),
    `controlplane` (only 3 control plane nodes), and `split` (3+3 control and
    data plane nodes). To generate the inventory file, login to your jumpbox
    and execute the following as the dci-openshift-agent user:

    ```bash
    INSTALL_TYPE=sno  # or 'controlplane' or 'split'
    cd ~/samples/assisted_on_libvirt
    ansible-playbook -i $PWD/dev/$INSTALL_TYPE parse-template.yml
    ```

1.  Copy the generated file from `~dci-openshift-agent/hosts` to
    `/etc/dci-openshift-agent/hosts`
1.  Start the agent with `dci-openshift-agent-ctl -s`

That's it, after the process is complete, you should be left with a
`~dci-openshift-agent/clusterconfigs-dciokd/kubeconfig` file which you can use
to interact with your OCP cluster.

!!! note
    The name of the cluster is prepended to the clusterconfigs directory, if
    you change the cluster name then the path to the `kubeconfig` file will
    need to be adjusted


### Single Node Openshift

If you want to test SNO with Assisted Installer in your local/development
environment, there's a few changes you need to make to your inventory:

1.  Remove all workers from the inventory file and leave a single master in the
    inventory file
1.  Point *both* the `api_vip` and `ingress_vip` values to the **same IP
    address you gave the single master**
1.  Because SNO requires a minimum of 8 cores on the single master, make sure
    your `vm_spec` in your `vm_nodes` section for your master has `cpu_cores:
    8` (it is possible to adjust the memory and disk size in this section too)

That should be all that is required to install in SNO mode, the playbooks will
install a SNO cluster and leave you with a kubeconfig/access to the cluster
once finished.

!!! note
    One of the inventory files in the samples directory creates a single node
    openshift cluster, take a look at it for reference

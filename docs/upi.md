# UPI Install

UPI (User provisioned Infrastructure) is another install method for deploying
OpenShift in your environment. Where IPI (Installer provisioned Infrastructure)
is opinionated and has stricter requirements, UPI leaves a lot of the install
process up to the user.

UPI doesn't require a separate provisioning network like IPI does.  But this
means it's up to the user to configure Netboot for their network.  You are
responsible for configuring dhcp so that it answers PXE/Netboot requests.
You are responsible for setting up the tftpboot directory and serving ignition
files from your web server.

There are example configs for the various services needed for UPI installs in the
samples/upi directory.

This document will go over the different pieces and how to set them up.

You can also do UPI in a disconnected environment, please see the
[disconnected mode](disconnected_en.md) for additional details on how to setup.

## Table of Contents

- [Requirements](#requirements)
- [Configurations](#configurations)
- [Hooks upi-install.yml](#hooks-upi-install.yml)
- [Running dci-openshift-agent](#running-dci-openshift-agent)

## Requirements

- 1 Bootstrap host which is used to bootstrap the cluster, can be powered off
  after install.
- 3 Master hosts are required to make a working cluster.
- 2 Worker hosts are recommended at a minimum.
- Only one network is required for UPI installs, no provisioning network needed.
- Network services
  - DHCP
  - DNS
  - HAPROXY
  - TFTPBOOT

## Configurations

First you have to set the 'install_type' option to 'upi' in the settings
file `/etc/dci-openshift-agent/settings.yaml.

There are certain variables and host entries that need to be defined in
the hosts file `/etc/dci-openshift-agent/hosts`.

Following is an example of the configuration file highlighting the hosts
needed for a upi install:

```INI
[all:vars]
bootstrap_interface=<IP ADDRESS OF PROVISIONER>

[...]
[bootstrap]
boostrap name=boostrap

[masters]
master-0 name=master-0
master-1 name=master-1
master-2 name=master-2

[...]
[workers]
worker-0 name=worker-0
worker-1 name=worker-1

[...]
[provisioner]
provisioner ansible_user=dci
```

The host names for masters and workers need to match your dns/dhcp
configuration.  If the names don't match then the agent won't be able
to verify that the cluster has been provisioned correctly and will fail
the DCI job.

The variables needed by the disconnected environment:

Group                   | Variable | Required      | Type   | Description
----------------------- | -------- | ------------- | ------ |----------------------------------------------------
[settings] | install_type | True | String | Setting this to upi for a upi install
[all:vars] | bootstrap_interface | False | String | If you are using the upi_bootstrap module in your hook this needs to be the provisioning hosts ip address

## Hooks upi-install.yml

When running the openshift agent in UPI mode the majority of the install
happens in `/etc/dci-openshift-agent/hooks/upi-install.yml`.  It is up to
the user to copy the kernel, ramdisk and root images to the appropriate
place.  Please see the `samples/upi/hooks/upi-install.yml` for examples.

The following variables are made available to allow you to pull the kernel,
ramdisk and root images easily:
  - rhcos_pxe_kernel_path
  - rhcos_pxe_kernel_sha256
  - rhcos_pxe_initramfs_path
  - rhcos_pxe_initramfs_sha256
  - rhcos_pxe_rootfs_path
  - rhcos_pxe_rootfs_sha256
  - rhcos_live_iso_path
  - rhcos_live_iso_sha256

The basic layout for the hook can be described by these steps:
  - Download/Copy kernel, ramdisk and images to appropriate location
  - Generate install-config.yaml
  - Create OpenShift Manifests
  - Generate Ignition configs
  - Copy Ignition files to appropriate locations
  - Power off bootstrap, masters and workers
  - Set boot to network for bootstrap, masters and workers
  - Power on bootstrap, masters and workers
  - Wait for nodes to provision
  - Wait for bootstrap to complete
  - Power off bootstrap
  - Get CR's to approve (allow workers to join cluster)
  - Wait for install to complete

## Running dci-openshift-agent

After the configuration is setup, we can deploy openshift
using the dci-openshift-agent:

```Shell
dci-openshift-agent-ctl -s -- -v
```

anything after the -- are arguments passed to ansible-playbook.  In this
example we are increasing the verbosity.

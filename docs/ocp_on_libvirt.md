# DCI OpenShift Agent on libvirt

## Table of contents

- [How to run the fully virtualized example](#how-to-run-the-fully-virtualized-example)
  - [Demo screencast](#demo-screencast)
  - [Additional resources](#additional-resources)
- [Troubleshooting](#troubleshooting)
  - [Installer timeout](#installer-timeout)
  - [Monitor install log](#monitor-install-log)
  - [Troubleshooting ironic issues](#troubleshooting-ironic-issues)

If you are interested in getting an OCP deployment running as quickly as
possible you will find in the `/samples/ocp_on_libvirt` folder some
configuration examples to run the `DCI Openshift Agent` in a “all-in-one” full
virtualized environment.

In this case, the agent will use `libvirt` virtual machines deployed on top of
the DCI `Jumpbox`.

Please note that systems are [nested virtual
machines](#https://www.linux-kvm.org/page/Nested_Guests) at least in the case
of the provision host: provisioner will spawn a bootstrap VM inside itself, in
our case that would be a VM inside a VM. Please remember to enable `nested_kvm`
in your Jumpbox. 

The full virtualized environment scenario requires the DCI Jumpbox to have at
least 64 Gi of memory and 200 Gi of storage to host a virtual provision machine
and all virtual masters.

The provided example will create 4 systems (1 provisionner and 3 OCP masters)
on top of the DCI Jumpbox. The number of nodes can be adapted by modifying the
`samples/ocp_on_libvirt/inventory/libvirt_resources.yml` file.

## How to run the fully virtualized example

This example will help you to run the `dci-openshift-agent` within one single
system by running `libvirt` virtual machines. This example is a good path to
understand the `dci-openshift-agent` (all different steps, hooks, settings) and
to be used as a development environment.

At this point, the `DCI Jumpbox` is installed with all above prerequisites
([learn how to install the DCI
Jumpbox](../README.md#installation-of-dci-jumpbox)).

The following documentation covers how to configure deploy virtual systems,
virtual networks and the according `/etc/dci-openshift-agent/hooks/`
configuration.

It will also guide you to generate and use an appropriate settings file for
this scenario.

Please note, that in the fully virtualized environment, the `DCI Openshift
Agent` will create the `Openshift Provisioning node` system automatically.

First, you need to work directly as the `dci-openshift-agent` user:

```
# su - dci-openshift-agent
$ id
uid=990(dci-openshift-agent) gid=987(dci-openshift-agent) groups=987(dci-openshift-agent),107(qemu),985(libvirt) ...
```

Run `libvirt_up` playbook to configure libvirt nodes.
This playbook will:

- Create 3 local virtual machines to be used as `System Under Test`
- Create 1 local virtual machine to be used as a `Provisioning node`
- Generate the relative `hosts` file (ready to be used as an inventory for the
  `dci-openshift-agent`).
- Provide a `pre-run.yml` hook file to be used by the agent.

```
cd ~/samples/ocp_on_libvirt/
$ ansible-playbook -v libvirt_up.yml
```

Copy the newly created file `hosts` to the `/etc/dci-openshift-agent`
directory:

```
$ pwd
~/samples/ocp_on_libvirt
$ sudo cp hosts /etc/dci-openshift-agent/
```

_The `dci-openshift-agent` is now ready to run the “all-in-one” virtualized
workflow._

You can check the virtual machines status by using `virsh` command:

```
$ sudo virsh list --all
 Id    Name                           State
----------------------------------------------------
 60    provisionhost                  running
 64    master-0                       off
 65    master-2                       off
 66    master-1                       off
```

From here on out you can run your agent normally as you would with baremetal
hardware, please refer to the main `README.md` file section "Starting the DCI
OCP Agent" for how to start the agent. The agent will see the virtualized
resources as regular resources thanks to SSH and VBMC emulation.

After you run a DCI job (see the main `README.md`) you will be able to interact
with the RHOCP cluster:

```
$ export KUBECONFIG=/home/admin/clusterconfigs/auth/kubeconfig
$ oc get pods --all-namespaces

```

In case you need to delete the fully virtualized environment, you can run the
playbook `libvirt_destroy.yml`:

```
$ cd samples/ocp_on_libvirt/
$ ansible-playbook -v libvirt_destroy.yml
```

### Demo screencast
[![demo](https://asciinema.org/a/Rv35FeMi5CADVsaBUhdu3f6d0.svg)](https://asciinema.org/a/Rv35FeMi5CADVsaBUhdu3f6d0?autoplay=1)

### Additional resources
We have provided dnsmasq config templates in the samples directory to serve
dhcp/dns from the dci jumpbox if you don’t already have a dns/dhcp server on
your bare metal network.

## Troubleshooting

The
[kni](https://openshift-kni.github.io/baremetal-deploy/latest/Troubleshooting.html)
page offers a good start to understand and debug your libvirt environments.

Furthermore, some issues (see below) are specific to a libvirt(or small)
environment.

### Installer Timeout

Due to the lack of hardware (cpu, memory) and the fact that all resources are
virtualized, the installation may take longer to complete. A recurring timeout
is reached during the bootstrap.

Two parameters are available to increase this timeout,
*increase_bootstrap_timeout* and *increase_install_timeout*.

```YAML
- name: "installer : Run IPI installer"
  import_role:
    name: installer
  vars:
    increase_bootstrap_timeout: 2
    increase_install_timeout: 2
```

If you need to troubleshoot this environment for bootstrap/install issues
please follow the "Troubleshooting" section(s) in the main README

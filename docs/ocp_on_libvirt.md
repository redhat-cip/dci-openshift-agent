# OpenShift using virtual machines emulating baremetal (a.k.a. Full virtualized environment)

## Introduction

If you are interested in getting an OCP deployment running as quickly as possible you will find in the `/sample` folder some configuration examples to run the `DCI Openshift Agent` in a “all-in-one” full virtualized environment.

In this case, the agent will use `libvirt` virtual machines deployed on top of the DCI `Jumpbox`.

Please note that systems might be [nested virtual machines](#https://www.linux-kvm.org/page/Nested_Guests) if the DCI Jumpbox is already a virtual machine.

The full virtualized environment scenario requires the DCI Jumpbox to have at least 64 Gi of memory and 200 Gi of storage to host a virtual provision machine and all virtual masters.

The provided example will create 4 systems (1 provisionner and 3 OCP masters) on top of the DCI Jumpbox. The number of nodes can be adapted by modifying the `libvirt_resources.yml` file.

## How to run the full virtualized example ?

This example will help you to run the `dci-openshift-agent` within one single system by running `libvirt` virtual machines. This example is a good path to understand the `dci-openshift-agent` (all different steps, hooks, settings) and to be used as a development environment.

At this point, the `DCI Jumpbox` is installed with all above prerequisites ([learn how to install the DCI Jumpbox](../README.md#installation-of-dci-jumpbox)).

The following documentation covers how to configure deploy virtual systems, virtual networks and the according `/etc/dci-openshift-agent/hooks/` configuration.

It will also guide you to generate and use an appropriate settings file for this scenario.

Please note, that in the fully virtualized environment, the `DCI Openshift Agent` will create the `Openshift Provisioning node` system automatically.

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
- Generate the relative `hosts` file (ready to be used as an inventory for the `dci-openshift-agent`).
- Provide a `pre-run.yml` hook file to be used by the agent.

```
cd ~/samples/ocp_on_libvirt/
$ ansible-playbook -v libvirt_up.yml
```

Copy the newly created file `hosts` to the `/etc/dci-openshift-agent` directory:

```
$ pwd
~/samples/ocp_on_libvirt
$ sudo cp hosts /etc/dci-openshift-agent/
```

_The `dci-openshift-agent` is now ready to run the “all-in-one” virtualized workflow._

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

After you run a DCI job (see the main `README.md`) you will be able to interact with the RHOCP cluster:

```
$ export KUBECONFIG=/home/admin/clusterconfigs/auth/kubeconfig
$ oc get pods --all-namespaces

```

In case you need to delete the full virtualized environment, you can run the playbook `libvirt_destroy.yml` located in `setup_bootstrap/full_virt`:

```
$ cd ~/samples/ocp_on_libvirt/
$ ansible-playbook -v libvirt_destroy.yml
```

### Demo
[![demo](https://asciinema.org/a/Rv35FeMi5CADVsaBUhdu3f6d0.svg)](https://asciinema.org/a/Rv35FeMi5CADVsaBUhdu3f6d0?autoplay=1)

### Additional resources

We have provided dnsmasq config templates in the samples directory to serve dhcp/dns from the dci jumpbox if you don’t already have a dns/dhcp server on your bare metal network.

## Troubleshooting

The [kni](https://openshift-kni.github.io/baremetal-deploy/latest/Troubleshooting.html) page offers a good start to understand and debug your libvirt environments.

Furthermore, some issues (see below) are specific to a libvirt(or small) environment.

### Timeout

Due to the lack of hardware (cpu, memory), the installation may take longer to complete. A recurring timeout is reached during the bootstrap.
Two parameters are available to increase this timeout, *increase_bootstrap_timeout* and *increase_install_timeout*.


```
- name: "installer : Run IPI installer"
  import_role:
    name: installer
  vars:
    increase_bootstrap_timeout: 2
    increase_install_timeout: 2
```

## License

Apache License, Version 2.0 (see [LICENSE](LICENSE) file)

## Contact

Email: Distributed-CI Team <distributed-ci@redhat.com>
IRC: #distributed-ci on Freenode

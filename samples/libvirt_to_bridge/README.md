# Playbook to convert OCP on libvirt to bridged networking

## Table of contents

- [How to run the convert bridge playbook](#how-to-run-the-convert-bridge-playbook)
  - [Updating DHCP, DNS and dci-openshift-agent](#updating-dhcp,-dns-and-dci-openshift-agent)
  - [Demo screencast](#demo-screencast)
- [Troubleshooting](#troubleshooting)

If you are interested in combining virtualized masters with physical workers
then this playbook will help you.

If you haven't already setup your virtualized masters then please ([learn how
 to install the virtual environment](../../docs/ocp_on_libvirt.md))

For this playbook to work you will need two additional network interfaces
on your jumpbox for a total of 3 networks.  We will call the exisiting
network on your jumpbox the jumpbox network.  For the additional two
networks, one network will be used for the baremetal network and the second
one will be used for the provisioning network.  Each interface will need to
be plugged into its own switch or if using one switch it will need to be
divided with port based vlan tagging.

Your physical workers will be plugged into these switches, one switch for
each network interface.

Your baseboard management controller (BMC) will need to be plugged into
either the jumpbox or the baremetal network.

## How to run the convert bridge playbook

First, you need to work directly as the `dci-openshift-agent` user:

```
# su - dci-openshift-agent
$ id
uid=990(dci-openshift-agent) gid=987(dci-openshift-agent) groups=987(dci-openshift-agent),107(qemu),985(libvirt) ...
```

Run `libvirt_to_bridge` playbook to configure your jumpbox networks.
This playbook will:

- Shutdown the virtual hosts
- Check for libvirt dnsmasq settings and convert to system dnsmasq settings
- Shutdown and undefine the libvirt networks baremetal and provisioning
- Create new baremetal and provisioning networks using the 2 new nics
- Define and start the libvirt networks baremetal and provisioning
- Setup the Jumpbox network to do NAT
- Restart dnsmasq on the jumphost
- boot the provisionhost back up.

```
cd ~/samples/libvirt_to_bridge/
$ ansible-playbook -e provisioning_nic=eno2 -e baremetal_nic=eno3 libvirt_to_bridge.yml
```

## Updating DHCP, DNS and dci-openshift-agent

Update the following files to add DNS and DHCP entries for your physical workers:

/etc/NetworkManager/dnsmasq.d/openshift.conf
```
address=/worker-0/192.168.100.105
address=/worker-1/192.168.100.106
```

/var/lib/dnsmasq/baremetal.hostsfile
```
ac:1f:6b:19:53:3d,192.168.100.105,worker-0.dciokd.metalkube.org
ac:1f:6b:17:33:2f,192.168.100.106,worker-1.dciokd.metalkube.org
```

/etc/dci-openshift-agent/hosts
```
[workers]
worker-0 name=worker-0 role=worker ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=192.168.1.52 provision_mac=ac:1f:6b:19:53:3c hardware_profile=default
worker-1 name=worker-1 role=worker ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=192.168.1.53 provision_mac=ac:1f:6b:17:33:2e hardware_profile=default
```

After making the above changes you will need to reload NetworkManager and dnsmasq

```
$ sudo systemctl restart NetworkManager
$ sudo systemctl restart dnsmasq
```

_The `dci-openshift-agent` is now ready to run the “hybrid” virtualized
workflow._

From here on out you can run your agent normally as you would with just baremetal
hardware, please refer to the main `README.md` file section "Starting the DCI
OCP Agent" for how to start the agent. The agent will see the virtualized
resources as regular resources thanks to SSH and VBMC emulation.

### Demo screencast
[![demo](https://asciinema.org/a/Rv35FeMi5CADVsaBUhdu3f6d0.svg)](https://asciinema.org/a/Rv35FeMi5CADVsaBUhdu3f6d0?autoplay=1)

## Troubleshooting

The
[kni](https://openshift-kni.github.io/baremetal-deploy/latest/Troubleshooting.html)
page offers a good start to understand and debug your libvirt environments.

Furthermore, some issues (see below) are specific to a libvirt(or small)
environment.

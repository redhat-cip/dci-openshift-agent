# How to troubleshoot a libvirt Cluster?

This document refers to a virtual cluster using libvirt.
Examples show user dci-openshift-agent on jumphost pctt-hv5, but it could be any host with libvirt

- [Introduction](#introduction)
- [Monitor the cluster install log](#monitor-the-cluster-install-log)
- [Debug the initial cluster bootstraping](#debug-the-initial-cluster-bootstraping)
- [Troubleshoot ironic issues](#troubleshoot-ironic-issues)
- [References](#references)

## Introduction

This documents provides some advices to troubleshoot issues on an OCP cluster deployed using libvirt


## Monitor the cluster install log
From the jumpbox (the hypervisor server)

Get the VMs names
```
[dci-openshift-agent@pctt-hv5 ~]$ sudo virsh list --all
 Id   Name            State
-------------------------------
 9    provisionhost   running
 13   master-2        running
 14   master-1        running
 15   master-0        running
```

Connect to the corresponding provisionhost and monitor the openshift_install.log file.
```
[dci-openshift-agent@pctt-hv5 ~]$ ssh dci@provisionhost
[dci@provisionhost ~]$ tail -f /home/dci/clusterconfigs/.openshift_install.log
```

## Debug the initial cluster bootstraping
During the cluster install phase, the installer boots and setup a Bootstrap VM into the provision host that performs the cluster bootstrapping.

List the VMs running on the provisionhost VM (nested virtualization magic!), and get the first IP address of vnet0
```
[dci@provisionhost ~]$ sudo virsh list --all
 Id   Name                     State
----------------------------------------
 1    dciokd-btzxz-bootstrap   running

[dci@provisionhost ~]$ sudo virsh domifaddr --source arp dciokd-btzxz-bootstrap
 Name       MAC address          Protocol     Address
-------------------------------------------------------------------------------
 vnet0      52:54:00:ba:12:96    ipv4         192.168.123.5/0
 vnet0      52:54:00:ba:12:96    ipv4         192.168.123.111/0
 vnet1      52:54:00:c2:ad:c4    ipv4         172.22.0.2/0
```

Connect via SSH to it usign the default private key available in the provisioner and check the logs from journalclt.
```
[dci@provisionhost ~]$ ssh core@192.168.123.5
[core@localhost ~]$ journalctl -b -f -u release-image.service -u bootkube.service
```

You can also log in from the provisionhost to the master nodes
```
[dci@provisionhost ~]$ ssh core@master-0
[core@master-0 ~]$
```

In the bootstrap VM, it is also possible to list the ironic services during the bootstrap
```
[core@localhost ~]$ sudo crictl ps
```


## Troubleshoot ironic issues

During the deployment, ironic services are started temporally in the bootstrap VM, to help bootstrapping the master nodes.
Then after the master nodes are ready to take the role, bootstrap VM is deleted and ironic services are started in the cluster.
At both stages you can interact with ironic to see details of the nodes


If you want to interact with ironic services during the bootstrap, get the baremetal network IP of ironic service from the bootstrap VM
```
[core@localhost ~]$ sudo ss -ntpl | grep 6385
[core@localhost ~]$ ip a s ens3
```

Get the bootstrap VM ironic credentials from the terraform variables
```
[dci@provisionhost ~]$ grep ironic_ clusterconfigs/terraform.baremetal.auto.tfvars.json
  "ironic_username": "bootstrap-user",
  "ironic_password": "fUEE9CZy5vz6lXnJ",
```

If you want to interact with ironic services in the cluster, get the IP of ironic service from the metal3 resources
```
[dci@provisionhost ~]$ export KUBECONFIG=/home/dci/clusterconfigs/auth/kubeconfig
[dci@provisionhost ~]$ oc describe pod metal3-896d759f4-lwk5n -n openshift-machine-api | egrep ^IP:
IP:                   192.168.123.148
[dci@provisionhost ~]$ oc get secrets metal3-ironic-password -n openshift-machine-api -o jsonpath='{.data.username}' | base64 -d
ironic-user
[dci@provisionhost ~]$ oc get secrets metal3-ironic-password -n openshift-machine-api -o jsonpath='{.data.password}' | base64 -d
auZkWXfV77wC2XzJ
```

Then prepare a clouds.yaml with the following information, and replace the IP addresses and password accordingly
```
[dci@provisionhost ~]$ vi clouds.yaml

clouds:
  metal3-bootstrap:
    auth_type: http_basic
    auth:
      username: bootstrap-user
      password: fUEE9CZy5vz6lXnJ
    baremetal_endpoint_override: http://IP-Provisioining-bootstrapVM-IP:6385
    baremetal_introspection_endpoint_override: http://IP-Provisioining-bootstrapVM-IP:5050
  metal3:
    auth_type: http_basic
    auth:
      username: ironic-user
      password: auZkWXfV77wC2XzJ
    baremetal_endpoint_override: http://IP-Provisioining-Master-IP:6385
    baremetal_introspection_endpoint_override: http://IP-Provisioining-Master-IP:5050
```

Back in the provisioning host, install podman and start a container, set OS_CLOUD with metal3 if you want to use the ironic services on the cluster, or metal3-bootstrap if you want to use the services on the bootstrap VM (if still running)
```
[dci@provisionhost ~]$ sudo dnf install -y podman
[dci@provisionhost ~]$ podman run -ti --rm --entrypoint /bin/bash -v /home/dci/clouds.yaml:/clouds.yaml:z -e OS_CLOUD=metal3 quay.io/metal3-io/ironic-client
```

Finally from the pod you started, you can run ironic baremetal commands
```
[root@8ce291ff4f4a /]# baremetal node list
+--------------------------------------+----------+--------------------------------------+-------------+--------------------+-------------+
| UUID                                 | Name     | Instance UUID                        | Power State | Provisioning State | Maintenance |
+--------------------------------------+----------+--------------------------------------+-------------+--------------------+-------------+
| ba3d1990-e860-4685-9929-3c3356e6e29e | master-1 | 7a116082-1b8a-4f65-9991-242dd56ed44b | power on    | active             | False       |
| 3ab260c7-9a1e-48bf-841a-473a3cec2cbd | master-2 | a9658128-570c-45ad-9ef6-d4721aeaeb81 | power on    | active             | False       |
| d67ade66-d9e1-4825-b53e-381870ff5c81 | master-0 | 728106a3-1994-4e86-9a8c-838becf22aa5 | power on    | active             | False       |
+--------------------------------------+----------+--------------------------------------+-------------+--------------------+-------------+
```


## References

A good to place to start is https://openshift-kni.github.io/baremetal-deploy/4.7/Troubleshooting.html



# Playbooks to deploy Single Node Openshift on a libvirt VM

This directory includes playbooks, inventories and configuration files to faciliate the deployment of OCP SNO on virtual machines

Virtual SNO can be deployed either with DCI on standalone mode (without DCI)

## Pre-requisites

A provisioner node with the following:
- A RHEL >= 8.4 server
- Ansible >= 2.9
- A valid Red Hat subscription
  - Access to `rhel-8-for-x86_64-baseos-rpms` and `rhel-8-for-x86_64-appstream-rpms` repositories is required
  - If the vars activation_key and org_id are provided, the system registration to the proper subscriptions is done during the deployme

This is where the OCP/SNO installation will be launched, and where the VM will be running OpenShift.

Virtual SNO implementation can be deployed in a VM with the following resources:
- vCPU: 6
- RAM: 16 GB
- Storage: 20 GB
NOTE: More are required to be able to install operators and apps.

The playbook `deploy-sno-standalone.yml` has been also tested in Fedora 34. It means no need to RHEL OS or Red Hat subscriptions

Choose one deployment method:

## A) Deploy with DCI from the SNO provisioner node

Note: You can run steps 1, 2, and 3 manually if you prefer to do so. The steps are just to help you configure the provisioner host quickly. See these [hosts files](https://github.com/redhat-cip/dci-openshift-agent/blob/master/samples/sno_on_libvirt/examples) as examples of the variables you need, depending on your case (libvirt or baremetal deployment).

### 1. Configuration

Create your `~/sno-node-settings.yml` file to declare your variables.

NOTE: You can provide your RHN password in plaintext but is not recommended.

```yaml
dci_client_id: remoteci/XXXXXXXXX
dci_api_secret: API-SECRET-GOES-HERE
rhn_user: your-rhn-user
rhn_pass: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          VAULTED_RHN_PASSWORD
```

* Please engage the DCI team if you do not have the proper access keys and you want to use the Red Hat Distributed CI service during your deployments.

### 2. Prepare the inventory

The playbook "sno-on-libvirt.yml" setup the pre-requisites in the SNO Host, it explicitly looks for the group name `[sno_host]` and will fail if it does not find it.
This is also predicated on actually being run on a workstation or server different than the soon-to-be SNO provisioner node.

```bash
your-user@your-workstation ~$ echo "[sno_host]" | sudo tee -a /etc/ansible/hosts
your-user@your-workstation ~$ echo "mysnoserver ansible_user=user-with-sudo-priv ansible_host=some-server" | sudo tee -a /etc/ansible/hosts
```

### 3. Run playbook

This will subscribe the SNO host to Red Hat CDN, install external repos, DCI agents, and setup the dci-openshift-agent user to be able to launch an OCP/SNO deployment on next step.

```bash
your-user@your-workstation ~$ cd samples/sno_on_libvirt/
your-user@your-workstation ~$ ansible-playbook sno-on-libvirt.yml -e "@~/sno-node-settings.yml" -i /etc/ansible/hosts --vault-password-file ~/.vault_secret
```

NOTE: The playbook sno-on-libvirt.yml, by default, it copies the default inventory `samples/sno_on_libvirt/examples/hosts-libvirt` to `/etc/dci-openshift-agent/hosts` which contains required variables, including a very important one: `install_type=sno` this will allow DCI agent to define which install to perform. In case you want to copy `samples/sno_on_libvirt/examples/hosts-baremetal` instead, because you want to use a baremetal deployment, you need to setup the variable `sno_mode: baremetal` in `~/sno-node-settings.yml` file.

### 4. Source the credentials and run the main d-o-a playbook.

SNO only works on OCP 4.8 and above. Please ensure your `/etc/dci-openshift-agent/settings.yml` has only 4.8 references.

```bash
sudo su - dci-openshift-agent
source /etc/dci-openshift-agent/dcirc.sh
cd /usr/share/dci-openshift-agent
ansible-playbook dci-openshift-agent.yml -i /etc/dci-openshift-agent/hosts  -e "@/etc/dci-openshift-agent/settings.yml"
```

or

```bash
sudo su - dci-openshift-agent
source /etc/dci-openshift-agent/dcirc.sh
dci-openshift-agent-ctl -s -- -v
```

## B) Deploy without DCI from the SNO provisioner node

### 1. Inventory Notes

If you run the playbook sno-on-libvirt.yml, by default it copies the default inventory `samples/sno_on_libvirt/examples/hosts-libvirt` to `/etc/dci-openshift-agent/hosts` (unless you are in a baremetal deployment, in whose case you will have to follow the instructions commented above).
This inventory contains defaults values for the SNO/OCP cluster setup, and SNO plays will validate if they are provided:

- pull secret
- domain
- cluster name
- dir to store deployment files
- extcidrnet

Additionally the following groups are defined:

- provisioner group and host entry
- master group and host entry
- worker group (no need to add hosts to this group

If you did not run sno-on-libvirt.yml playbook, you can use `deploy-sno-standalone.yml` playbook to deploy the SNO VM to be used in subsequent deployments. They are under the `samples/sno_on_libvirt/inventory` folder (for the case of libvirt environments).

If you want to use an inventory file for a baremetal deployment, you can use as base the file placed in `samples/sno_on_libvirt/examples/hosts-baremetal`, in whose case you will have to 1) remove the files under the `samples/sno_on_libvirt/inventory` folder, then 2) move `samples/sno_on_libvirt/examples/hosts-baremetal` to that folder, and 3) rename it to `hosts`.

If you use the default inventory files, then you only need to provide the pullsecret variable. A basic pull secret can be obtained from the [Red Hat Console](https://console.redhat.com/openshift/downloads) under Token > pullsecret section. Note that you will need to append authentication data for other registries such as Quay.io to that basic pullsecret file.

```bash
$ sudo vi ./inventory/hosts
...
pullsecret="{{ lookup('file', '<PATH_TO_PULLSECRET>')|string }}"
...
```
### 2. Set OCP/SNO version
If you want to deploy a specific version of SNO >= 4.8 then update the version variable or build variable with (ga or dev)

```bash
$ sudo su - dci-openshift-agent
cd /usr/share/dci-openshift-agent
vi ~/samples/sno_on_libvirt/deploy-sno-standalone.yml
...
version="4.8.X"
build="ga"
...
```

### 3. Deploy

```bash
sudo su - dci-openshift-agent
cd /usr/share/dci-openshift-agent
ansible-playbook ~/samples/sno_on_libvirt/deploy-sno-standalone.yml
```

##  Access the GUI

If SNO is deployed using DCI, the dci-openshift-agent will create 2 users for the API/GUI. Please review /home/`<user>`/`<clusterconfigs-path>`/ocp_creds.txt file in the jumphost for details and change the passwords if needed.

In case SNO is deployed using the standalone mode, please follow the process below to create a local user for the GUI/API.

* Adding the admin user to the httpassd Identity provider and assign to to the cluster-admin role.

```bash
touch htpasswd
htpasswd -Bb htpasswd admin <your_password>
oc --user=admin create secret generic htpasswd --from-file=htpasswd -n openshift-config
oc replace -f - <<API
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: Local Password
    mappingMethod: claim
    type: HTPasswd
    htpasswd:
      fileData:
        name: htpasswd
API

oc adm policy add-cluster-role-to-group cluster-admin admin
```

* Add the following entries to you local host file:
```bash
192.168.126.10 api.dcisno.example.com console-openshift-console.apps.dcisno.example.com oauth-openshift.apps.dcisno.example.com
```

* The OCP GUI should be ready at: https://console-openshift-console.apps.dcisno.example.com

## Destroy the SNO VM and perform some cleanup

NOTE: The sno_node_prep and sno_installer roles by default clean up before a deployment

```bash
sudo su - dci-openshift-agent
cd ~/samples/sno_on_libvirt/
ansible-playbook deploy-sno-standalone.yml -t cleanup
```

## Generate a host file based on a template

If you only want to generate the hosts file to be used in `dci-openshift-agent`, you can do the following. The hosts file will be saved in this folder.

```bash
sudo su - dci-openshift-agent
cd ~/samples/sno_on_libvirt/
ansible-playbook generate-hosts-file.yml
```

In particular, with the inventory files placed in inventory folder, you will obtain a hosts file like the one placed in `samples/sno_on_libvirt/examples/hosts-libvirt`.

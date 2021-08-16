# Playbooks to deploy Single Node Openshift on a libvirt VM

## Pre-requisites

- A RHEL 8.4 server with direct internet access
  - Access to `rhel-8-for-x86_64-baseos-rpms` and `rhel-8-for-x86_64-appstream-rpms` repos required
  - If the vars activation_key and org_id are provided registration is done during the deployment
- Tested in Fedora 34 using play `deploy-sno-standalone.yml`

## Prepare SNO node

This is where the OCP/SNO installation will be launched, and where the VM will be running.

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
github_user: your-github-user
```

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

NOTE: The playbook sno-on-libvirt.yml, it copies the default inventory `samples/sno_on_libvirt/hosts` to `/etc/dci-openshift-agent/hosts` which contains required variables, including a very important one: `install_type=sno` this will allow DCI agent to define which install to perform.

## Deploy with DCI from the SNO provisioner node

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

## Deploy without DCI from the SNO provisioner node

### 1. Inventory Notes

If you run the playbook sno-on-libvirt.yml, it copies the default inventory `samples/sno_on_libvirt/hosts` to `/etc/dci-openshift-agent/hosts`.
This inventory contains defaults values for the SNO/OCP cluster setup, and SNO plays will validate if they are not provided:

- pull secret
- domain
- cluster name
- dir to store deployment files
- extcidrnet

Additionally the following groups are defined:

- provisioner group and host entry
- master group and host entry
- worker group (no need to add hosts to this group

If you did not run sno-on-libvirt.yml playbook, you can copy the default inventory and adapt it to your setup, make sure you include the variables above. 

```bash
cp samples/sno_on_libvirt/hosts /etc/dci-openshift-agent/hosts
```

If you use the default inventory, then you only need to provide the pullsecret variable.

```bash
$ sudo vi /etc/dci-openshift-agent/hosts
...
pullsecret="Add-pull-secret-in-json"
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
cluster="dcisno"
...
```

### 3. Deploy

```bash
sudo su - dci-openshift-agent
cd /usr/share/dci-openshift-agent
ansible-playbook ~/samples/sno_on_libvirt/deploy-sno-standalone.yml -i /etc/dci-openshift-agent/hosts
```

## Destroy the SNO VM and perform some cleanup

NOTE: The sno-installer role by default cleans up before a deployment

```bash
sudo su - dci-openshift-agent
cd ~/samples/sno_on_libvirt/
ansible-playbook deploy-sno-standalone.yml -t cleanup
```

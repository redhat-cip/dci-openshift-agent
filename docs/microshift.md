# Microshift installation

In this section of the documentation we will see how to run the DCI OpenShift Agent to install Microshift on a system. At the end of this documentation you should have at least one system under test (SUT) running Microshift.

Before starting, check that you have followed the [get started](get_started). Normally you should have created a remoteci on [the user interface](https://www.distributed-ci.io/remotecis). The `dcictl --version` command should return the client version.

The rest of the documentation is performed as root user.

## Installing the DCI OpenShift agent and DCI pipeline

The `dci-openshift-agent` and `dci-pipeline` are packaged and available as RPM files. However `epel-release` along with additional support repos must be installed first:

```console
subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
subscription-manager repos --enable=ansible-2.9-for-rhel-8-x86_64-rpms
dnf config-manager --add-repo=https://releases.ansible.com/ansible-runner/ansible-runner.el8.repo
dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
```

Then we can install `dci-openshift-agent` and `dci-pipeline`

```console
dnf -y install dci-openshift-agent dci-pipeline
```

## Create a repository to save your settings

In the following doc, we use `~/microshift-config` as a folder for our hooks and pipelines files. Change it with a better name (example: `<YOUR_COMPANY>-<LAB>-config`). A good pratice is to save this folder in git.

```
mkdir ~/microshift-config
cd ~/microshift-config
touch install-microshift-pipeline.yml
touch ansible.cfg
touch secrets/credentials.yml
```

## Edit install-microshift-pipeline.yml

Modify your pipeline file `install-microshift-pipeline.yml`:

```yaml
- name: Microshift
  stage: install
  ansible_playbook: /usr/share/dci-openshift-agent/plays/microshift/main.yml
  ansible_cfg: ./ansible.cfg
  dci_credentials: ~/microshift-config/secrets/credentials.yml
  topic: OCP-4.16
  components:
    - repo?name:Microshift 4.16*
  ansible_extravars:
    hooks_dir: ~/microshift-config/hooks
    rhsm_offline_token: "REPLACE_ME"
    rhsm_org_id: "REPLACE_ME"
    rhsm_activation_key: "REPLACE_ME"
    suts:
      - name: "sut1"
        memory: 4096
        vcpu: 2
        disk_size: 20
    # Default settings
    # http_proxy: "{{ lookup('env','http_proxy') }}"
    # https_proxy: "{{ lookup('env','https_proxy') }}"
    # no_proxy_list: "{{ lookup('env','no_proxy') }}"
    # dci_tags: []
    # http_store: "/opt/http_store"
    # dci_cluster_configs_dir: "~/clusterconfigs"
    # libvirt_pool_dir: "/var/lib/libvirt/images"
    # ssh_public_key: "{{ lookup('env', 'HOME') + '/.ssh/id_rsa.pub' }}"
    # ssh_private_key: "{{ lookup('env', 'HOME') + '/.ssh/id_rsa' }}"
```

- `topic` and `components`: Choose the right version of Microshift you want to test.

Ansible configuration with extra vars:

- `hooks_dir`: Location of your hooks files (`error.yml, failure.yml, install.yml, post-run.yml, pre-run.yml, success.yml, test-jumpbox.yml, test-sut.yml`). If your hooks are not found, no worries, `include_tasks` is skipped. Use hooks to customize your pipeline. See [Customizing a DCI job with hooks](general_concepts/#customizing-a-dci-job-with-hooks).
- `rhsm_offline_token`: RHSM offline token. Get it [here](https://access.redhat.com/management/api)
- `rhsm_org_id` and `rhsm_activation_key`: RHSM organization ID and activation key. Information available on [console.redhat.com](https://console.redhat.com/insights/connector/activation-keys)
- `suts`: Describe the system under tests the agent will create. We are using Redfish to install Microshift OStree ISO on the SUTs. Sushy tools is used to control virtual systems with Redfish protocol.

Here a description of the default settings you can modify:

- `http_proxy`, `https_proxy` and `no_proxy_list`: Change this if you are using proxy to access internet.
- `dci_tags`: add tags to your DCI job.
- `http_store`: Location of the data folder served by a HTTP server on port 80. During the process, a `http://localhost:80/microshift.iso` will be created and used by the agent to provision the SUTs.
- `dci_cluster_configs_dir`: Where the kubeconfig files are saved. You will have for example a `~/clusterconfigs/kubeconfig-sut1` file for `sut1`. You can source this file and use `oc` client to query Microshift.
- `libvirt_pool_dir`: where the VM images are stored.
- `ssh_public_key` and `ssh_private_key`: SSH key used to authenticate on the SUTs.

## Edit ansible.cfg

Modify your pipeline file `ansible.cfg`:

```ini
[defaults]
library             = /usr/share/dci/modules/
module_utils        = /usr/share/dci/module_utils/
action_plugins      = /usr/share/dci/action_plugins/
filter_plugins      = /usr/share/dci/filter_plugins/
callback_plugins    = /usr/share/dci/callback/
callback_whitelist  = dci,junit
retry_files_enabled = False
host_key_checking   = False
roles_path          = /usr/share/dci/roles/
log_path            = ansible.log

[privilege_escalation]
become_method       = sudo
```

## Get credentials.yml for your remoteci

Connect to https://www.distributed-ci.io/remotecis and get the credentials.yml for your remoteci (`Remotecis > Column authentication > button credentials.yml > Copy to clipboard`)

Fill your `secrets/credentials.yml` file.

## Run the installation

```console
dci-pipeline @pipeline:name="install microshift" install-microshift-pipeline.yml
```

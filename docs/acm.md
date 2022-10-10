# Advanced Cluster Management based installation

Advanced Cluster Management (ACM) is yet another method DCI OCP agent can use to install OpenShift clusters. If you are curious about it please read [Red Hat Advanced Cluster Management for Kubernetes](https://www.redhat.com/en/technologies/management/advanced-cluster-management).

This document will focus on explaining how the ACM can be used to install an OpenShift cluster through the DCI Agent.

## Table of contents

* [Requirements](#requirements)
* [Configuration](#configuration)
* [Explanation of the process](#explanation-of-the-process)
  * [Disconnected Environment](#disconnected-environment)
* [Pipelines examples](#pipelines-examples)
* [Inventory example](#inventory-example)

At this time only SNO deployments are supported. Support for multi-node deployments will be added in the future.

## Requirements

* An OCP cluster already installed and configured with the ACM operator and its dependencies. A default storage class is mandatory in order to save information about the clusters managed by ACM. This will act as the Hub Cluster.
* A kubeconfig file to be used to interact with the Hub Cluster.
* A node that will be the target for the SNO deployment with support for Virtual Media at its Baseboard Management Controller (BMC).
  - CPU: 6
  - RAM: 16 GB
  - At least 20GB of storage

ACM does not require a dedicated jumphost or provisioning node, being able to interact with the Cluster hub using a kubeconfig file is enough.

The ACM integration with DCI uses the [acm-setup](../roles/acm-setup/README.md) and [acm-sno](../roles/acm-sno/README.md) to complete the deployment of SNO instances.

Please read the role's documentation in order to get more information.

# Configuration
1. Create a directory for the SNO instance on the path defined by `dci_cluster_configs_dir`. Set the directory name as the name of the target instance to host the SNO deployment.
    ```ShellSession
    $ mkdir ${dci_cluster_configs_dir}/clusterX
    ```
1. A Hub cluster is deployed with support for ACM. It can be achieved by setting `enable_acm=true` during an OCP deployment. Please see the [Pipelines examples](#pipelines-examples) section for a snippet of a pipeline prepared for ACM.
1. The kubeconfig file of the Cluster Hub is exported as HUB_KUBECONFIG
`export HUB_KUBECONFIG=/<kubeconfig_path>`
1. Define the inventory file with the information of the instance to be used to deploy SNO. See [Inventory example](#inventory-example) a snippet of an inventory file for acm-sno deployment.
1. Define the deployment settings for the new SNO instance. See [pipelines examples](#pipelines-examples) a snippet of a pipeline to deploy SNO.

1. Use `dci_pipeline` or the DCI Agent to initiate the deployment using the values defined in the `acm-sno-pipeline`.

* Operators can be deployed on top of the SNO instance by defining the proper `enable_<operator>` flag. DCI will perform the proper operator mirroring and complete its deployment. Please take into consideration that not all operators may be suitable for SNO instances.

## Explanation of the process

1. Process starts, the agent creates a new job in the [DCI Web UI](https://www.distributed-ci.io/login).
1. Some checks are performed to make sure the installation can proceed.
1. If this is a disconnected/restricted network environment:
   1. The OCP release artifacts are downloaded
   1. Container/operator images are mirrored to the local registry
   1. Cluster hub is inspected to get setting that will be inherited to the SNO instance, like pull secrets, registry host, web server, etc
1. The ACM installation is set up and started. The required ACM resources are created.
   1. BMC secret.
   1. The Agent Service Config is patched with information for the new requested cluster.
   1. InfraEnv.
   1. Cluster deployment.
   1. Bare Metal Controller.
1. The target node's BMC is provisioned by ACM. A base RHCOS image will be used to boot the server, start the ACM agents and complete the initial bootstrap.
1. The node is discovered by ACM and auto-approved.
1. Network settings and NTP are validated.
1. A new cluster installation starts. Deployment should complete in around 60 minutes.
1. If DNS is properly configured, the new instance is registered as a managed cluster in the ACM console.
1. The `KUBECONFIG` and admin credentials are fetched and uploaded to DCI. Those files are also stored in the `dci_cluster_configs_dir` directory.
1. The `KUBECONFIG` is used to interact with the new cluster and perform the deployment of the desired operators.
1. Process ends and the job is completed in the DCI Web UI.

### Disconnected environment

* Set `dci_disconnected` to true, this can be done in the inventory file or the
  `settings.yml` file.

### Pipelines examples

* ACM Hub pipeline with Trident as storage backend

```yaml
---
- name: openshift-acm-hub
  stage: ocp
  ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
  ansible_cfg: /var/lib/dci/pipelines/ansible.cfg
  ansible_inventory: /var/lib/dci/inventories/<lab>/8nodes/@RESOURCE
  dci_credentials: /etc/dci-openshift-agent/<dci_credentials.yml>
  pipeline_user: /etc/dci-openshift-agent/pipeline_user.yml
  ansible_extravars:
    dci_config_dirs:
      - /var/lib/dci/<lab>-config/dci-openshift-agent
      - /var/lib/dci/trident-config
    dci_local_log_dir: /var/lib/dci-pipeline/upload-errors
    dci_gits_to_components:
      - /var/lib/dci/<lab>-config/dci-openshift-agent
      - /var/lib/dci/inventories
      - /var/lib/dci/pipelines
    dci_tags: []
    dci_cache_dir: /var/lib/dci-pipeline
    dci_base_ip: "{{ ansible_default_ipv4.address }}"
    dci_baseurl: "http://{{ dci_base_ip }}"
    cnf_test_suites: []
    cnf_tests_mode: offline
    enable_acm: true
    dci_teardown_on_success: false
  topic: OCP-4.10
  components:
    - ocp
    - netapp-trident=22.10.0
  outputs:
    kubeconfig: "kubeconfig"
  success_tag: ocp-acm-hub-4.10-ok
```

* ACM SNO pipeline
```yaml
---
- name: openshift-acm-sno
  type: ocp
  ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
  ansible_cfg: /var/lib/dci/pipelines/ansible.cfg
  dci_credentials: /etc/dci-openshift-agent/<dci_credentials.yml>
  pipeline_user: /etc/dci-openshift-agent/pipeline_user.yml
  ansible_inventory: /home/dciteam/inventories/<lab>/sno/<inventory_file.yml>
  ansible_extravars:
    install_type: acm
    acm_cluster_type: sno
    dci_local_log_dir: /var/lib/dci-pipeline/upload-errors
    dci_gits_to_components:
      - /var/lib/dci/<lab>-config/dci-openshift-agent
      - /var/lib/dci/inventories
      - /var/lib/dci/pipelines
    dci_tags: []
    dci_cache_dir: /var/lib/dci-pipeline
    dci_base_ip: "{{ ansible_default_ipv4.address }}"
    dci_baseurl: "http://{{ dci_base_ip }}"
    dci_teardown_on_success: false
    enable_perf_addon: true
  topic: OCP-4.10
  components:
    - ocp
  success_tag: ocp-acm-sno-4.10-ok
```

### Inventory example

* SNO Inventory file

```yaml
all:
  hosts:
    jumphost:
      ansible_connection: local
    # All task for ACM run from localhost, so making provisioner equal to localhost
    provisioner:
      ansible_connection: local
      ansible_user: dciteam
  vars:
    cluster: clusterX-sno
    dci_disconnected: true
    acm_force_deploy: true
    acm_cluster_name: sno1
    acm_base_domain: sno.<mydomain>
    acm_bmc_address: 192.168.10.48
    acm_boot_mac_address: 3c:fd:fe:c2:0f:fx
    acm_machine_cidr: 192.168.82.0/24
    acm_bmc_user: REDACTED
    acm_bmc_pass: REDACTED
    provision_cache_store: "/opt/cache"
```

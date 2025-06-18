# Advanced Cluster Management based installation

Advanced Cluster Management (ACM) is yet another method the dci-openshift-agent can use to install OpenShift clusters. If you are curious about it please read [Red Hat Advanced Cluster Management for Kubernetes](https://www.redhat.com/en/technologies/management/advanced-cluster-management).

This document will focus on explaining how the ACM can be used to install an OpenShift cluster through the DCI Agent.

## Table of contents

* [Supported deployments](#supported-deployments)
* [Requirements](#requirements)
* [Roles](#roles)
* [SNO Configuration](#sno-configuration)
* [SNO Deployment Process](#sno-deployment-process)
* [HCP Configuration](#hcp-configuration)
* [Pipelines Examples](#pipeline-examples)
* [Inventory Examples](#inventory-examples)

## Supported deployments

We are constantly adding new ways to deploy OCP, currently, the agent supports

- HCP (Hosted Control Planes)
- SNO
- ZTP
  - ClusterInstance (SNO)

## Requirements

* An installed OCP cluster configured with the ACM operator and its dependencies. A default storage class is mandatory to save information about the clusters managed by ACM. This will act as the Hub Cluster.
* A `kubeconfig` file to interact with the Hub Cluster. There's no need for a provisioning node or a dedicated jumphost when using ACM.

### SNO requirements

* The target node with support for Virtual Media at its Baseboard Management Controller (BMC).
  * CPU: 6
  * RAM: 16 GB
  * At least 20GB of storage

## Roles

The ACM integration with DCI uses the [acm_setup](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/acm_setup) role to deploy a cluster hub.
And the following roles are used to deploy different types of clusters through ACM

* [acm_sno](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/acm_sno) to deploy SNO instances.
* [acm_hypershift](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/acm_hypershift) to deploy HCP (Hosted Control Planes) instances.

Please read the role's documentation for more information.

## SNO configuration

1. Create a directory for the SNO instance on the path defined by `dci_cluster_configs_dir`. Set the directory name as the name of the target instance to host the SNO deployment.

    ```ShellSession
    mkdir ${dci_cluster_configs_dir}/clusterX
    ```

1. A Hub cluster is deployed with support for ACM. It can be achieved by setting `enable_acm=true` during an OCP deployment. Please see the example of an [ACM Hub pipeline](#acm-hub-pipeline).
1. The kubeconfig file of the Cluster Hub is exported as HUB_KUBECONFIG: `export HUB_KUBECONFIG=/<kubeconfig_path>`
1. Define the inventory file with the information of the instance to be used to deploy SNO. See an example of an [SNO inventory file](#sno-inventory-file)
    * To deploy in a disconnected environment, set `dci_disconnected` to true
1. Define the deployment settings for the new SNO instance. See the example of an [ACM SNO Pipeline](#acm-sno-pipeline).
1. Use `dci_pipeline` or the DCI Agent to initiate the deployment using the values defined in the [`acm-sno-pipeline`](#acm-sno-pipeline).

> NOTE: Operators can be deployed on top of the SNO instance as it is described in [Deploying operators](../README.md#deploying-operators).
> DCI will perform the proper operator mirroring and complete its deployment.
> Please take into consideration that not all operators may be suitable for SNO instances.

## SNO deployment process

1. The process starts, and the agent creates a new job in the [DCI Web UI](https://www.distributed-ci.io/login).
1. Some checks are performed to make sure the installation can proceed.
1. If this is a disconnected/restricted network environment:
   1. The OCP release artifacts are downloaded.
   1. Container/operator images are mirrored to the local registry. The `acm_local_repo` variable can be used to set a local registry repository. Defaults to ocp-<major-version>/<version>
   1. The cluster hub is inspected to extract settings used in the SNO instance, e.g. pull secrets, registry host, web server, among others.
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
1. The process ends and the job is completed in the DCI Web UI.

## HCP configuration

> ⚠️ Currently, HCP only supports the "kvirt" hosted cluster type.

1. A Hub cluster is deployed with support for ACM. It can be achieved by setting `enable_acm=true` during an OCP deployment. Please see the example of an [ACM Hub pipeline](#acm-hub-pipeline).
1. The Hub cluster must have the CNV and metallb operators installed.
1. The OCP release images for the HCP cluster will be mirrored to the same registry path as the Hub cluster images.
1. The kubeconfig file of the Cluster Hub is exported as HUB_KUBECONFIG: `export HUB_KUBECONFIG=/<kubeconfig_path>`
1. Define the deployment settings for the new Hosted Cluster instance. See the example of an [ACM HCP Pipeline](#acm-hcp-pipeline).
  1. As part of the installation, the agent will deploy a MetalLB instance in L2 mode. The variable `metallb_ipaddr_pool_l2` with the range of IPs for the LoadBalancer is required and can be defined at the pipeline or inventory.
  1. The metallb setup can be skipped if there is one already running but it will validated during the HCP installation.
1. Use `dci_pipeline` or the DCI Agent to initiate the deployment using the values defined in the [`acm-hcp-pipeline`](#acm-hcp-pipeline).

## ZTP

### ClusterInstance

> ⚠️ Currently, in disconnected environments, it is only supported the same version of spoke cluster as the Hub

1. A Hub cluster is deployed with support for ACM. It can be achieved by setting `enable_acm=true` during an OCP deployment. Please see the example of an [ACM Hub pipeline](#acm-hub-pipeline).
1. The Hub cluster must have the SiteConfig Operator enabled.
1. The kubeconfig file of the Cluster Hub is exported as HUB_KUBECONFIG: `export HUB_KUBECONFIG=/<kubeconfig_path>`
1. A directory with the templates to apply the ClusterInstance is required `dci_clusterinstance_template_dir`.
1. Use `dci_pipeline` or the DCI Agent to initiate the deployment using the values defined in the [`acm-clusterinstance-pipeline`](#acm-clusterinstance-pipeline).

#### Variables for ACM-based deployments

| Name                             | Required | Default | Description
| -------------------------------- | -------- | ------- | -----------
| acm_cluster_type                 | Yes      | None    | The type of cluster to deploy through ACM. Must use: `ztp-spoke-clusterinstance`
| dci_clusterinstance_template_dir | Yes      | None    | Directory that holds the [ClusterInstance templates](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single/multicluster_engine_operator_with_red_hat_advanced_cluster_management/index?ref=cloud-cult-devops#install-clusters-preq)
| dci_force_deploy_spoke           | No       | False   | Whether or not force an installation of a and Spoke cluster
| dci_spoke_manifest_files         | No       | []      | A list of rendered manifest that must be applied to the Hub cluster before a Gitops managed spoke installation. ie: pull_secrets, BMC credentials, etc.

#### ClusterInstance Templates

Installing a cluster using ClusterInstance with the SiteConfig Operator requires some preparation as described above.
The dci-openshift-agent can be used to satisfy these requirements.

The ClusterInstance, for SNO requires 4 manifests documented in the 
[Installing single-node OpenShift clusters with the SiteConfig operator.](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single/multicluster_engine_operator_with_red_hat_advanced_cluster_management/index?ref=cloud-cult-devops#install-clusters)
But the dci-openshift-agent only requires 3, as Namespace is created automatically. The other manifests are provided as templates to use the dci-openshift-agent capabilities to extract information from different sources like the Hub itself, DCI control server, the inventory and the pipeline file.

The manifests are expected to be located in `dci_clusterinstance_template_dir` with a prefix of the cluster name, e.g. `my-sno-cluster-`.

Here the links to the documention for each of the manifests required:

- [PullSecret](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single/multicluster_engine_operator_with_red_hat_advanced_cluster_management/index?ref=cloud-cult-devops#install-create-pull-secret)
- [BMH-Secret](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single/multicluster_engine_operator_with_red_hat_advanced_cluster_management/index?ref=cloud-cult-devops#install-create-bmc-secret)
- [ClusterInstance](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single/multicluster_engine_operator_with_red_hat_advanced_cluster_management/index?ref=cloud-cult-devops#install-render-manifests)


## Pipeline Examples

### ACM Hub pipeline

This pipeline includes NFS storage

```yaml
---
- name: openshift-acm-hub
  stage: ocp
  ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
  ansible_cfg: /var/lib/dci/pipelines/ansible.cfg
  ansible_inventory: /var/lib/dci/inventories/<lab>/<pool>/@RESOURCE
  dci_credentials: /etc/dci-openshift-agent/<dci_credentials.yml>
  pipeline_user: /etc/dci-openshift-agent/pipeline_user.yml
  ansible_extravars:
    dci_config_dirs:
      - /var/lib/dci/<lab>-config/dci-openshift-agent
    dci_local_log_dir: /var/lib/dci-pipeline/upload-errors
    dci_gits_to_components:
      - /var/lib/dci/<lab>-config/dci-openshift-agent
      - /var/lib/dci/inventories
      - /var/lib/dci/pipelines
    dci_tags: []
    dci_cache_dir: /var/lib/dci-pipeline
    dci_base_ip: "{{ ansible_default_ipv4.address }}"
    dci_baseurl: "http://{{ dci_base_ip }}"
    cnf_tests_mode: offline
    enable_acm: true
    enable_nfs_storage: true
    nfs_server: nfs.example.com
    nfs_path: /path/to/exports
    dci_teardown_on_success: false
  topic: OCP-4.14
  components:
    - ocp
  outputs:
    kubeconfig: "kubeconfig"
  success_tag: ocp-acm-hub-4.14-ok
```

### ACM SNO pipeline

```yaml
---
- name: openshift-acm-sno
  stage: acm-sno
  prev_stages: [acm-hub]
  ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
  ansible_cfg: /var/lib/dci/pipelines/ansible.cfg
  dci_credentials: ~/.config/dci-pipeline/<dci_credentials>.yml
  pipeline_user: ~/.config/dci-pipeline/<pipeline_user>.yml
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
    enable_sriov: true
  topic: OCP-4.15
  components:
    - ocp
  success_tag: ocp-acm-sno-4.15-ok
```

### ACM HCP pipeline

```yaml
---
- name: openshift-acm-hcp
  stage: acm-hcp
  prev_stages: [acm-hub]
  ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
  ansible_cfg: /var/lib/dci/pipelines/ansible.cfg
  dci_credentials: ~/.config/dci-pipeline/<dci_credentials>.yml
  pipeline_user: ~/.config/dci-pipeline/<pipeline_user>.yml
  ansible_extravars:
    install_type: acm
    acm_cluster_type: hcp
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
  topic: OCP-4.14
  components:
    - ocp
  success_tag: ocp-acm-hcp-4.14-ok
```

### ACM ClusterInstance pipeline

```yaml
---
- name: openshift-ztp-clusterinstance
  stage: ztp-spoke
  prev_stages: [acm-hub]
  ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
  ansible_cfg: /var/lib/dci/pipelines/ansible.cfg
  dci_credentials: ~/.config/dci-pipeline/<dci_credentials>.yml
  configuration: "@QUEUE"
  pipeline_user: ~/.config/dci-pipeline/<pipeline_user>.yml
  ansible_inventory: /var/lib/dci/inventories/@QUEUE/ztp/spoke/@RESOURCE-clusterinstance
  ansible_extravars:
    install_type: acm
    acm_cluster_type: ztp-spoke-clusterinstance
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
    # ClusterInstance
    dci_clusterinstance_template_dir: /var/lib/dci/inventories/@QUEUE/ztp/spoke/templates
  topic: OCP-4.18
  components:
    - ocp
  inputs:
    kubeconfig: hub_kubeconfig_path
  outputs:
    kubeconfig: "kubeconfig"
  success_tag: ocp-ztp-clusterinstance-4.18-ok
```

## Inventory Examples

### ACM HCP kvirt Inventory file

```yaml
all:
  hosts:
    jumphost:
      ansible_connection: local
    # All task for ACM run from localhost, so making provisioner equals to localhost
    provisioner:
      ansible_connection: local
      ansible_python_interpreter: "{{ansible_playbook_python}}"
      ansible_user: <ansible_user>
  vars:
    cluster: cluster<X>-hcp
    webserver_url: "http://webcache.<domain>.lab:8080"
    provision_cache_store: "/opt/cache"
    # MetalLB in L2 mode
    metallb_ipaddr_pool_l2:
      - <ipv4-start>-<ipv4-end>
      - <<ipv6-start>-<ipv6-end>
```

### SNO Inventory file

```yaml
all:
  hosts:
    jumphost:
      ansible_connection: local
    # All task for ACM run from localhost, so making provisioner equal to localhost
    provisioner:
      ansible_connection: local
      ansible_user: <ansible_user>
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

### ACM ClusterInstance Inventory

```yaml
all:
  hosts:
    localhost:
      ansible_connection: local
    jumphost:
      ansible_connection: local
      ansible_python_interpreter: "{{ ansible_playbook_python }}"
      ansible_user: <user>
  vars:
    dci_disconnected: true
    cluster: sno1
    cluster_name: "{{ cluster }}"
    base_dns_domain: sno.<mydomain>
    # Uses AI templates to deploy the cluster
    cluster_template_ref: ai-cluster-templates-v1
    node_template_ref:  ai-node-templates-v1
    webserver_url: http://webcache.<mydomain>.lab:8080
    provision_cache_store: /opt/cache
    bmh_password: REDACTED
    bmh_user: REDACTED
```
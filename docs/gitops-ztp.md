# GitOps ZTP based installation

GitOps ZTP is an OpenShift cluster deployment method based on the principle of managing the installation settings from a source code repository.

## Table of contents

* [Process description](#process-description)
* [ZTP ACM Hub Cluster](#ztp-acm-hb-cluster)
* [ZTP Spoke Cluster](#ztp-spoke-cluster)

## Process description

The DCI process of deploying a cluster using the GitOps ZTP method comprises two stages.

In the first stage, an OpenShift Hub Cluster, running the Advanced Cluster Management (ACM), GitOps and Topology-Aware Lifecycle Manager operators are deployed. This must be a multinode cluster since ACM relies on a redundant PostgreSQL database.

After this, the GitOps operator is connected to a Git repository containing the site configuration (deployment) and policy generator templates (settings and workloads) manifests for the OpenShift Spoke Clusters. On reading and processing these manifests the deployment of any defined spoke clusters is triggered.

These two stages are run through separate DCI jobs that may be pipeline stages.

## ZTP ACM Hub Cluster

To support ZTP GitOps based deployments, the ACM Hub Cluster must be provisioned with some operators on top of the Advanced Cluster Management. In particular, the OpenShift GitOps Operator and the Topology Aware Lifecycle Manager is required.

Also, for disconnected environments you may need to have a Git repository served from the restricted network. To help with this, the DCI OpenShift Agent allows you to install a Gitea instance on the hub cluster, so it can be reached both, from the jumpbox and the spoke cluster.

### Requirements for the ZTP ACM Hub Cluster

* A multi-node or compact cluster (minimum 3 control plane nodes).
* For disconnected environments, a container image registry running from the DMZ may be used to mirror the Gitea image.

### Configuration for the ZTP ACM Hub Cluster

| Variable                | Description |
|-------------------------|-------------|
| dci_operators      | List of the operators, along with their specific settings, to be installed in the Hub Cluster. This list must included, at minimum, the advanced-cluster-management, the openshift-gitops-operator and the topology-aware-lifecycle manager. |
| enable_acm         | The variable must be set to "true" for the dci-openshift-agent to run the ACM hub cluster configuration tasks. |
| enable_gitea       | For disconnected environments, set it to "true" to enable the deployment of a Gitea server in the hub cluster so you may push your gitops manifests. |
| dci_pullsecret_file    | In disconnected environments, paths to the pull-secret file to authenticate on the Gitea image registry. |
| dci_local_registry  | In disconnected environments, base URL to the local registry hosting the Gitea mirrored images. |
| sg_username        | The internal Git server user name. |
| sg_password        | The internal Git server user password. |
| sg_email           | The internal Git server user e-mail address. |
| sg_repository      | The name to be given to the internal Git repository. |
| sg_repo_mirror_url | URL to an external reference repository containing the manifests to push (mirror) into the internal Git repository. |


### Pipeline data for the ZTP ACM Hub Cluster

Make sure the ACM Hub Clusters as described in the [ACM documentation](/docs/acm.md) includes the following data:

```
dci_operators:
  - name: advanced-cluster-management
    catalog_source: "redhat-operators"
    namespace: "open-cluster-management"
    operator_group_spec:
      targetNamespaces:
        - "open-cluster-management"
  - name: kubevirt-hyperconverged
    catalog_source: "redhat-operators"
    namespace: openshift-cnv
    starting_csv: kubevirt-hyperconverged-operator.v4.14.3
  - name: openshift-gitops-operator
    catalog_source: redhat-operators
    namespace: openshift-gitops-operator
  - name: topology-aware-lifecycle-manager
    catalog_source: redhat-operators
    namespace: openshift-operators
    operator_group_name: "global-operators"
# Operators to configure
enable_acm: true
# For disconnected environments
#enable_gitea: true
#sg_gitea_image: registry.local:5000/gitea/gitea:latest-rootless
#sg_username: gituser
#sg_password: Git_Ops_1234
#sg_email: gituser@example.com
#sg_repository: gitops
#sg_repo_mirror_url: git@github.com:gituser/gitops.git
```

### Inventory data for the ZTP ACM Hub Cluster

No extra variables are needed in the ACM Hub Cluster inventory.

## ZTP spoke cluster

### Requirements for the ZTP Spoke Cluster

* The Spoke Cluster is located in a connected environment.

* An installed OCP cluster configured with the ACM, GitOps and TALM operators and their dependencies. A default storage class is mandatory to save information about the clusters managed by ACM. This will act as the Hub Cluster.

* A kubeconfig file to interact with the Hub Cluster.

* A Git repository accessible from the Hub Cluster, so it can pull the site configuration and policies.

* The Git repository must have a SSH public key enabled.

* The private key to the SSH private key enabled in the Git repository.

* The Git repository must provide credentials to log into the spoke cluster node BMC consoles.

* Also provide a pull secret file for the Spoke cluster. You can use the pull secret extracted from the Hub cluster for this purpose.

### Configuration for the ZTP Spoke Cluster

The following settings must be provided to the SNO Spoke Cluster deployment job.

| Variable | Required | Value | Description |
|----------|----------|-------|-------------|
| install_type | yes | acm | Enables the dci-openshift-agent flow that installs a spoke cluster. |
| acm_cluster_type | yes | ztp-spoke | Enables the gitops-ztp installation method from all the available ACM based methods. |
| dci_gitops_sites_repo | yes | | Parameters to the site-config manifest repository.
| dci_gitops_policies_repo | yes | | Parameters to the policy generator template manifest repository. |
| dci_gitops_*_repo.url | yes | | URL to the repository. |
| dci_gitops_*_repo.path | yes | | Path to the directory containing the manifests. |
| dci_gitops_*_repo.branch | yes | | Branch containing your target version of the manifests. |
| dci_gitops_*_repo.key_path | yes | | Local path to the SSH private key file authorized to access the repository. |
| dci_gitops_*_repo.known_hosts | no | | (If required) List of the repository SSH fingerprints. |

### Pipeline example for the ZTP Spoke Cluster

```
- name: openshift-ztp-spoke
  stage: ztp-spoke
  prev_stages: [acm-hub]
  ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
  ansible_cfg: /usr/share/dci-openshift-agent/ansible.cfg
  dci_credentials: /etc/dci-openshift-agent/dci_credentials.yml
  configuration: "@QUEUE"
  ansible_inventory: ~/inventories/sno_baremetal-sno1-ztp-spoke-hosts
  ansible_extravars:
    install_type: acm
    acm_cluster_type: ztp-spoke
    dci_tags: [debug, sno, ztp, spoke, baremetal]
    dci_must_gather_images:
      - registry.redhat.io/openshift4/ose-must-gather
    dci_teardown_on_success: false
    acm_vm_external_network: False # False when running on ACM Hubs deployed by Assisted
  topic: OCP-4.15
  components:
    - ocp
  inputs:
    kubeconfig: hub_kubeconfig_path
  outputs:
    kubeconfig: "kubeconfig"
```

### Inventory example for the ZTP Spoke Cluster inventory - SNO

```
all:
  hosts:
    localhost:
      ansible_connection: local
  vars:
    cluster: sno1
    domain: spoke.example.lab
    dci_gitops_sites_repo:
      url: git@githost.com:org/spoke-ci-config.git
      path: files/ztp-spoke/sites
      branch: ztp_spoke
      key_path: "/path/to/ssh/private/key"
      known_hosts: "{{ gitops_repo_known_hosts }}"
    dci_gitops_policies_repo:
      url: git@githost.com:org/spoke-ci-config.git
      path: files/ztp-spoke/policies
      branch: ztp_spoke
      key_path: "/path/to/ssh/private/key"
      known_hosts: "{{ gitops_repo_known_hosts }}"
    gitops_repo_known_hosts: |
      github.com ecdsa-sha2-nistp256 ### REDACTED ###
      github.com ssh-ed25519 ### REDACTED ###
      github.com ssh-rsa ### REDACTED ###
```

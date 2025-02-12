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

| Variable              | Description
|---------              |------------
| dci_operators         | List of the operators, along with their specific settings, to be installed in the Hub Cluster. This list must included, at minimum, the advanced-cluster-management, the openshift-gitops-operator and the topology-aware-lifecycle manager.
| enable_acm            | The variable must be set to "true" for the dci-openshift-agent to run the ACM hub cluster configuration tasks.
| enable_gitea          | For disconnected environments, set it to "true" to enable the deployment of a Gitea server in the hub cluster so you may push your gitops manifests.
| dci_gitea_repo_sshkey | The sshkey to clone the initial repository when the repo requires ssh authentication.
| dci_pullsecret_file   | In disconnected environments, paths to the pull-secret file to authenticate on the Gitea image registry.
| dci_local_registry    | In disconnected environments, base URL to the local registry hosting the Gitea mirrored images.


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
# For private repositories
#dci_gitea_repo_sshkey: /path/to/ssh_private_key
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

| Variable                      | Required | Value | Description |
|-------------------------------|----------|-------|-------------|
| install_type                  | yes      | acm | Enables the dci-openshift-agent flow that installs a spoke cluster. |
| acm_cluster_type              | yes      | ztp-spoke | Enables the gitops-ztp installation method from all the available ACM based methods. |
| dci_gitops_sites_repo         | yes      | | Parameters to the site-config manifest repository.
| dci_gitops_policies_repo      | yes      | | Parameters to the policy generator template manifest repository. |
| dci_gitops_*_repo.url         | yes      | | URL to the repository in SSH or HTTP format. |
| dci_gitops_*_repo.path        | yes      | | Path to the directory containing the manifests. |
| dci_gitops_*_repo.branch      | yes      | | Branch containing your target version of the manifests. |
| dci_gitops_*_repo.key_path    | yes      | | If using SSH protocol, local path to the private key file authorized to access the repository. |
| dci_gitops_*_repo.username    | yes      | | If using HTTP protocol, user name of an authorized account. |
| dci_gitops_*_repo.password    | yes      | | If using HTTP protocol, password for the authorized user name. |
| dci_gitops_*_repo.known_hosts | no       | | (If required) List of the repository SSH fingerprints. |

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
    acm_vm_external_network: False # False when running on ACM Hubs deployed by ABI
  topic: OCP-4.15
  components:
    - ocp
  inputs:
    kubeconfig: hub_kubeconfig_path
  outputs:
    kubeconfig: "kubeconfig"
```

### Inventory example for the ZTP Spoke Cluster inventory - SNO running Git over SSH

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
      github.com ecdsa-sha2-nistp256 ### KEY ###
      github.com ssh-ed25519 ### KEY ###
      github.com ssh-rsa ### KEY ###
```

### Inventory example for the ZTP Spoke Cluster inventory - SNO running Git over HTTP

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
      username: ### USERNAME ###
      password: ### PASSWORD ###
    dci_gitops_policies_repo:
      url: git@githost.com:org/spoke-ci-config.git
      path: files/ztp-spoke/policies
      branch: ztp_spoke
      username: ### USERNAME ###
      password: ### PASSWORD ###
```

## Disconnected environments

When working in restricted networks the DCI Agents must run a set of preliminary actions that otherwise would be run by the network administrators in order to set up the conditions to run Disconnected environment deployments.

For the ZTP use cases, this involves mirroring the release images to a local registry where they can be accessed by both the hub and the spoke clusters.

Furthermore, for the deployment to work, a Cluster Image Set must exist in the hub cluster with a name that matches the one specified in the ClusterImageSetNameRef variable from the Site Config manifests.

Bear in mind that, although the ClusterImageSet name value usually identifies the OCP release version number to be installed, in the context of DCI automated deployments the release version number is taken from the OCP DCI Job component, so the DCI agent will read whatever value is set in the site config manifest's ClusterImageSetNameRef field and create a ClusterImageSet of that name resolving to the OCP release image for the release number specified in the DCI component, so the original ClusterImageSetNameRef parameter has no relevance beyond acting as the place holder to link the spoke cluster configuration with the required OCP release number.

The logic for these two operations is part of the dci-openshift-agent and is triggered by the presence of the dci_disconnected variable set to "true" in combination with the acm_cluster_type variable set to "ztp-spoke".

Besides the dci_disconnected and acm_cluster_type variables, the following variables must be defined in the inventory to control the mirroring services:

Variable              | Description
----------------------|-------------
pullsecret_file       | Path to a local copy of the pull-secret including the credentials needed to pull images from the public registries and push them to the local registry. 
registry_certificate  | Path to a local copy of the local registry certificate to allow for its authentication.
webserver_url         | Base URL to the local cache web server serving every other resource different than a container image.
provision_cache_store | Local path to the directory containing the resources served by the cache web server.
local_registry_host   | FQDN to the local registry mirroring container images like the release image.
local_registry_port   | (Optional) Network port the local registry is bound to.
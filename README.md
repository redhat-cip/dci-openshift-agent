# DCI OpenShift Agent

`dci-openshift-agent` provides Red Hat OpenShift Container Platform (RHOCP) in
Red Hat Distributed CI service.

There are some benefits of running the DCI OCP Agent:

1. Automation of nightly/dev preview/candidate/ga OCP component testing
2. CI runs on your own hardware
3. Red Hat doesn't have access to your hardware, the agent reports metrics/logs
   back to distributed-ci.io
4. The agent leverages the OpenShift IPI/UPI/AI/ACM/ZTP installers
5. You have access to all your jobs logs and metrics through distributed-ci.io
   where you can also set notifications for errors/exceptions

## Requirements

### Network requirements

This is a summary taken from the
upstream [Network requirements guide from OpenShift](https://openshift-kni.github.io/baremetal-deploy/latest/Deployment#network-requirements_ipi-install-prerequisites):

- Each server needs 2 NICs pre-configured. NIC1 for the private/provisioning
  network and NIC2 for the baremetal network. NIC interface names must be
  identical across all nodes
- Each server's NIC1 (provisioning) must be configured for PXE booting in
  BIOS/UEFI
- Each server must have IPMI configured and functional
- Each server must have static IP addresses for their baremetal NICs *plus* a
  dynamic pool of 5 or more IP addresses with a short TTL (2h) for the
  bootstrap VM
- Must have 2 reserved virtual IPs for API (`api.<cluster>.<domain>`) and
  wildcard ingress (`*.apps.<cluster>.<domain>`) and DNS setup for both. Please
  follow the [Openshift Baremetal DNS server
  configuration](https://openshift-kni.github.io/baremetal-deploy/latest/Deployment#DNS)
  as a reference guide
- Optional - Include DNS entries for the hostnames for each of the servers
- Nightly builds require that the provisionhost (SNO or IPI installs) is able
  to communicate directly to the controller server.

![Proposed network diagram](https://lucid.app/publicSegments/view/bedb0b3c-0cca-43ef-9dc6-7ed40ac35506/image.png "Proposed network diagram")

### Systems requirements

`DCI OpenShift Agent` needs a dedicated system to act as a `controller node`.
It is identified as the `DCI Jumpbox` in this document. This system will be
added to a standard OCP topology by being connected to the OCP `baremetal
network`. The `DCI OpenShift Agent` will drive the RHOCP installation workflow
from there.

Therefore, the simplest working setup must be composed of at least **5**
systems (1 system for DCI and 4 systems to match OCP minimum requirements).

Please use the [OpenShift Baremetal Deploy Guide (a.k.a.
`openshift-kni`)](https://openshift-kni.github.io/baremetal-deploy/) as a
reference for how to properly configure the OCP networks, systems and DNS.

Choose the OCP version you want to install and follow these steps to configure
the networks and install RHEL 8 on the **OpenShift Provisioning node**.

1. [Setting up access to DCI](#setting-up-access-to-dci)
2. [Installation of DCI Jumpbox](#installation-of-dci-jumpbox)
3. [Installation of Provision Host](#installation-of-ocp-provision-host)

As mentioned before, the **DCI Jumpbox** is NOT part of the RHOCP cluster. It
is only dedicated to download `RHOCP` artifacts from `DCI` public
infrastructure and to schedule the RHOCP cluster deployment across all systems
under test (1x OpenShift Provisioning node and several OCP nodes).

The **OpenShift Provisioning node** is used by the OpenShift installer to
provision the OpenShift cluster nodes.

The 3 remaining systems will run the freshly installed OCP Cluster. “3” is the
minimum required number of nodes to run RHOCP but it can be more if you need
to.

### Jumpbox requirements

The `Jumpbox` can be a physical server or a virtual machine.
In any case, it must:

- Be running the latest stable RHEL release (**8.4 or higher**) and registered
  via RHSM.
- Have at least 160GB of free space available in `/var`
- Having full access to Internet is highly recommended
- Be able to connect the following Web urls:
    - DCI API: <https://api.distributed-ci.io>
    - DCI Packages: <https://packages.distributed-ci.io>
    - DCI Repository: <https://repo.distributed-ci.io>
    - EPEL: <https://dl.fedoraproject.org/pub/epel/>
    - Ansible Runner Repository: <https://releases.ansible.com/ansible-runner/>
    - QUAY: <https://quay.io>
    - Nightly releases: <https://registry.ci.openshift.org>
    - RED HAT REGISTRY: <https://registry.redhat.io>
    - RED HAT SSO: <https://access.redhat.com>
    - RED HAT CATALOG: <https://catalog.redhat.com>
    - OpenShift Mirrors: <https://rhcos.mirror.openshift.com> and <https://mirror.openshift.com>
    - GitHub: <https://github.com>
    - Software Factory (gerrit): <https://softwarefactory-project.io>
    - Access to cloudfront CDN
- Have a static internal (network lab) IP
- Be able to reach all systems under test (SUT) using (mandatory, but not
  limited to):
    - SSH
    - IPMI
    - Serial-Over-LAN or other remote consoles (details & software to be provided by the partner)
- Be reachable by the Systems Under Test by using:
    - DHCP
    - PXE
    - HTTP/HTTPS

> NOTES:
 - Make sure rhel-8-for-x86_64-appstream-rpms repo provides access to libvirt => 6.0.0 packages
 - The installer may require access to other endpoint (CDNs). The list above is for well know URLs that be subject to change.

## Systems under test

`Systems under test` will be **installed** through DCI workflow with each job
and form the new “fresh” RHOCP cluster.

All files on these systems are NOT persistent between each
`dci-openshift-agent` job as the RHOCP cluster is reinstalled at each time.
Therefore, every expected customization and tests have to be automated from the
DCI Jumpbox (by using hooks) and will therefore be applied after each
deployment (More info at [Jumpbox Configuration](#jumpbox-configuration)).

## Optional DCI Access

- We strongly advise the partners to provide the Red Hat DCI team with access
  to their jumpbox. This way, Red Hat engineers can help with initial setup and
  troubleshooting.
- We suggest to run the `full virtualized` provided example first to understand
  how the `dci-openshift-agent` works before going to production with a real
  lab.

## Setting up access to DCI

The DCI dashboard gives you a view into what jobs you have run in your distributed agent. In order to gain access to it
you have to:

1. Go to https://www.distributed-ci.io/ and click login. You will be redirected to
   sso.redhat.com so you'll use your RH account credentials
2. If you are not part of any teams you can contact an admin to get yourself
   added
3. You will have to create a Remote CI for use later, go on the left navigation bar on the `Remotecis` option and click
   on "Create a new remoteci"
4. Fill out the description and which team it belongs to then click Create
5. You should see your newly created remoteci in the list, you can get
   the credentials in YAML format by click the button in the
   Authentication column. This should be saved under
   `~/.config/dci-pipeline/dci_credentials.yml`.

## Installation of DCI Jumpbox

Before proceeding you should have set up your networks and systems according to
the baremetal-deploy doc that was referenced above.

Provision the Jumphost with RHEL8. This includes subscribing the host to RHSM
and ensuring it's receiving updates.

The `dci-openshift-agent` is packaged and available as a RPM file.
However,`dci-release` and `epel-release` along with additional support
repos must be installed first:

For RHEL-8

```console
subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
subscription-manager repos --enable=ansible-2-for-rhel-8-x86_64-rpms
```

For CentOS Stream 8

```console
dnf install centos-release-ansible-29.noarch
```

For Both

```console
dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
dnf -y install https://packages.distributed-ci.io/dci-release.el8.noarch.rpm
dnf config-manager --add-repo=https://releases.ansible.com/ansible-runner/ansible-runner.el8.repo
dnf -y install dci-openshift-agent
```

### Folders and files location

Once `dci-openshift-agent` package is installed, the files and resources you can find in this repository will be placed in the following locations:

- `/etc/dci-openshift-agent` contains these folders and files: `dcirc.sh.dist` file, `hooks` folder, `settings.yml` file.
- `/usr/share/dci-openshift-agent/` gathers the following folders and files: `action_plugins` folder, `ansible.cfg` file, `dci-openshift-agent.yml` file, `group_vars` folder, `plays` folder, `test-runner` script and `utils` folder.
- `/var/lib/dci-openshift-agent` folder holds the `samples` folder.
- `/usr/bin` folder holds scripts such as `dci-openshift-agent-ctl` or `dci-check-change`.

> Note: scripts provided in this agent are deprecated. You should use `dci-pipeline` instead.

Also, have in mind that:

- `dci-openshift-agent` user (with sudo permissions) and group are created
- Files under `systemd` folder in this repo will be used to create the corresponding system service for `dci-openshift-agent`.

## Installation of OCP Provision Host

The provision host is part of the OCP requirements, as such you should follow
the guide linked before. The main things you need to know about the provision
host are:

- Provision with RHEL8
- Subscribe to RHSM and make sure it is receiving updates
- Install the EPEL RPM package
- Must have 2 NICs: one for the baremetal public/routed network and another for
  the provisioning private network
- Create a `kni` user
- Create a ssh key for the `kni` user

### Copying the ssh key to your provisioner

```console
# su - dci-openshift-agent
% ssh-keygen
% ssh-copy-id kni@provisionhost
```

## Collections

The `dci-openshift-agent` relies on [redhatci.ocp](https://github.com/redhatci/ansible-collection-redhatci-ocp) ansible collections that provide a set of roles and plugins that bring the functionality to the agent. The ansible collections are installed as a dependency of the agent and the project is hosted in https://github.com/redhatci/ansible-collection-redhatci-ocp

## Pipelines

To configure your DCI job pipelines, you need to install `dci-pipeline`. Instructions at [dci-pipeline documentation](../dci-pipeline/).

Here is an example of a pipeline job definition for `dci-openshift-agent`:

```YAML
- name: ocp-install
  stage: ocp
  ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
  ansible_cfg: ~/my-lab-config/pipelines/ansible.cfg
  ansible_inventory: ~/my-lab-config/inventories/inventory
  dci_credentials: ~/.config/dci-pipeline/dci_credentials.yml
  ansible_extravars:
    dci_cache_dir: ~/dci-cache-dir
    dci_config_dirs:
      - ~/my-lab-config/ocp-install
    dci_gits_to_components:
      - ~/config
    dci_local_log_dir: ~/upload-errors
    dci_tags: []
  topic: OCP-4.11
  components:
    - ocp
  outputs:
    kubeconfig: kubeconfig
```

## Ansible variables

This is the dci-openshift-agent variables that can be set in the
`ansible_extravars` section of your pipeline job definition:

| Variable                        | Required | Type    | Default                                                        | Description
|---------------------------------| -------- | ------- | -------------------------------------------------------------- | ------------
| dci_must_gather_images          | False    | List    |["registry.redhat.io/openshift4/ose-must-gather"]               | List of the must-gather images to use when retrieving "logs.\*".
| dci_teardown_on_failure         | False    | Boolean | False                                                          | Whether or not execute the teardown hook on a failure.
| dci_teardown_on_success         | False    | Boolean | True                                                           | Whether or not execute the teardown hook on success.
| dci_openshift_agent_conformance | False    | String  |                                                                | If defined it will run that category of conformance test.
| dci_ocp_channel                 | False    | String  | fast                                                           | [Update channel](https://docs.openshift.com/container-platform/4.14/updating/understanding_updates/understanding-update-channels-release.html#understanding-update-channels_understanding-update-channels-releases) to use in the cluster, see `upgrade_eus` variable for EUS channel.
| dci_custom_component            | False    | Boolean | False                                                          | Used to enable the use of custom OCP builds.
| dci_custom_component_file       | False    | String  | Undefined                                                      | A file that contains the custom OCP information in json. See [custom builds](#custom-builds) for details.
| dci_disconnected                | False    | Boolean | False                                                          | Signals that the OCP agent will run in disconnected.
| dci_force_mirroring             | False    | Boolean | False                                                          | Force the copy of the OCP release images to the local_registry_host.
| dci_openshift_csi_test_manifest | False    | String  | ""                                                             | Manifest file that contains the tests for CSI validation. Please review [test-parameters](https://redhat-connect.gitbook.io/openshift-badges/badges/container-storage-interface-csi-1/workflow/setup-test-parameters) and [csi-e2e](https://github.com/kubernetes/kubernetes/tree/v1.16.0/test/e2e/storage/external) for details about drivers capabilities.
| dci_sno_sideload_kernel_uri     | False    | String  | Undefined                                                      | URI to a kernel RPM to sideload on an SNO cluster.
| dci_do_cni_tests                | False    | Boolean | False                                                          | Executes the CNI tests as described in the [Openshift Badges documentation](https://redhat-connect.gitbook.io/openshift-badges/badges/container-network-interface-cni).
| dci_do_virt_tests               | False    | Boolean | False                                                          | Execute the Kubevirt Conformance tests as described in the [Openshift Badges documentation](https://redhat-connect.gitbook.io/openshift-badges/badges/container-network-interface-cnii). Hyperconverged operator must be installed on the cluster. For airgapped environments this is only supported on OCP 4.9 and newer versions.
| dci_sos_report_nodes            | False    | List    | Undefined                                                      | A list of nodes to generate SOS report from. Uses [redhatci.ocp.sos_report](https://github.com/redhatci/ocp/tree/main/roles/sos_report) module.
| baremetal_deploy_version        | False    | String  | origin/master                                                  | Allows you to lock upstream baremetal repo to specific version.
| force_upgrade                   | False    | Boolean | False                                                          | Force upgrade even if no version is available. This is set to true in a nightly build.
| allow_explicit_upgrade          | False    | Boolean | False                                                          | Allow an explicit upgrade even if it is not available. This is set to true in a nightly build and when force_upgrade is set to true.
| allow_upgrade_warnings          | False    | Boolean | False                                                          | Allow an upgrade even if there are warnings. This is set to true in a nightly build and when force_upgrade is set to true.
| upgrade_eus                     | False    | Boolean | False                                                          | Enable the EUS upgrade. Please see the [EUS upgrade](#eus-upgrade) section for more details.
| upgrade_operators               | False    | Boolean | True                                                           | In upgrade mode, enable the upgrade of installed operators after the cluster upgrade.
| update_catalog_channel          | False    | Boolean | True                                                           | When performing operators upgrade, in disconnected mode, update disconnected catalogSources for mirroring.
| storage_upgrade_tester          | False    | Boolean | False                                                          | only for upgrade; set it to true to launch CronJobs that are testing the storage service by deploying volumes (mounting and writing) during an upgrade.
| tester_storage_class            | False    | String  | False                                                          | only for upgrade; define which storage class to use for Storage upgrade tests. If is not defined, it will use the default storage class.
| dci_workarounds                 | False    | List    | []                                                             | List of workarounds to be considered in the execution. Each element of the list must be a String with the following format: bz\<id> or gh-org-repo-\<id>.
| openshift_secret                | False    | Dict    | auths:                                                         | Additional auths will be combined
| operators_index                 | False    | String  | registry.redhat.io/redhat/redhat-operator-index:v<ocp_version> | Catalog index that contains the bundles for the operators that will be mirrored in disconnected environments. In connected environments, if defined it will update the operators catalog index.
| opm_expire                      | False    | Boolean | True                                                           | Enable or disable expiration label in the operator-mirror catalog.
| opm_expire_time                 | False    | String  | 24h                                                            | Set the time used for the expiration label in the operator-mirror catalog.
| opm_mirror_list                 | False    | List    | []                                                             | List additional operators to be mirrored in disconnected environments. The package names of operators deployed using `dci_operators` must be included in this list.
| dci_operators                   | False    | List    | []                                                             | List of additional operators or custom operators deployments. Please see the [Customizing the Operators installation](#customizing-the-operators-installation) section for more details.
| apply_sriov_upgrade_settings    | False    | Boolean | True                                                           | Whether to apply SR-IOV recommended settings before operator upgrade.
| enable_cnv                      | False    | Boolean | False                                                          | Configures the CNV and the HCO operator.
| dci_cnv_test                    | False    | Boolean | False                                                          | Test the deploy of a VM using CNV and HCO operator.
| cnv_api_version                 | False    | String  | v1beta1                                                        | API version to use when deploying HCO operator: hco.kubevirt.io/cnv_api_version
| enable_logs_stack               | False    | Boolean | False                                                          | Configures the OCP cluster logging subsystem using the Loki and ClusterLogging Operators. Please see the [Logging Stack settings](#logging-stack) section for more details.
| enable_sriov                    | False    | Boolean | False                                                          | Configures the SRIOV Operator.
| enable_acm                      | False    | Boolean | False                                                          | Configures the [ACM](https://www.redhat.com/en/technologies/management/advanced-cluster-management) Operator. It converts the cluster into an ACM Hub.
| enable_nfd                      | False    | Boolean | False                                                          | Configures the [NFD](https://docs.openshift.com/container-platform/4.10/hardware_enablement/psap-node-feature-discovery-operator.html) Operator.
| enable_mlb                      | False    | Boolean | False                                                          | Configures MetalLB operator.
| enable_nmstate                  | False    | Boolean | False                                                          | Configures the k8s NMstate operator and creates initial instance.
| enable_odf                      | False    | Boolean | False                                                          | Configures the ODF Operator and its dependencies(ocs, lso, mcg, odf-csi-addons). Staring OCP 4.10, ODF replaces OCS. See: [Openshift Data Foundation](https://access.redhat.com/documentation/. Creates a storage cluster using Red Hat OpenShift Data Foundation operators.
| enable_nro                      | False    | Boolean | False                                                          | Configures NUMA Resources Operator CRDs (NUMA-Aware). GA from 4.12.24, it is Technology preview before.
| nro_topo_img_tag                | False    | String  |                                                                | Tag of the NUMA Topology scheduler image, by default it matches the OCP release name, but non-GA releases will require this variable to specify a tag from a previous OCP release.
| enable_nfs_storage              | False    | Boolean | False                                                          | Enable an NFS as external storage provisioner. Values for `nfs_server` and `nfs_path` are required if for this. See [nfs_external_storage](https://github/redhatci/ansible-collections-redhatci-ocp/roles/nfs_external_storage) for details.
| nfs_server                      | False    | String  |                                                                | NFS server's FQDN or IP Address. eg. my-nfs.mylab.local
| nfs_path                        | False    | String  |                                                                | NFS export path. e.g. /exports/nfs-provisioner
| performance_definition          | False    | String  |                                                                | Path of a Performance Profile YAML to apply after the OCP install.
| tuned_definition                | False    | String  |                                                                | Path of Tuned YAML to apply after the application of the Performance Profile.
| cnf_test_suites                 | False    | List    |                                                                | List of CNF Tests to perform: ['sctp','ptp','performance','sriov','dpdk'].
| operator_skip_upgrade           | False    | List    | []                                                             | List of operators to skip during the upgrade.
| custom_catalogs                 | False    | List    | []                                                             | List of custom catalogs to install alongside default catalog sources.
| operator_catalog_dir            | False    | String  | ""                                                             | Absolute path to a directory that contains archive files created using the oc mirror plugin. See [Mirroring from directory](#mirroring-from-directory) section for more information.
| operator_catalog_dir_name       | False    | String  | catalog-from-file                                              | Name for the operator's catalog created using the images from `operator_catalog_dir` path.
| operator_catalog_registry_path  | False    | String  | prega                                                          | Path/Org in the local registry where the images will be mirrored into when loading operators from an `oc_mirror` archive.
| install_all_from_catalog        | False    | String  | ''                                                             | Name of a catalog from which all its operators need to be installed.
| install_all_from_catalog_source | False    | String  | openshift-marketplace                                          | Namespace where the catalog defined in `install_all_from_catalog` was created.
| dci_erase_bootloader_on_disk    | False    | Boolean | False                                                          | Boolean to define if node disks should be deleted before powering off during the pre-run
| increase_unavailable_workers    | False    | Boolean | True                                                           | Boolean to define if the default maxUnavailable setting of the MCP worker should be increased from 1 to 2 (Only applied with 4 or more worker nodes are available.
| dci_console_pass                | False    | String  |                                                                | Password for the core user. This is supported in IPI installer and requires `customize_extramanifests_path` defined.

> NOTE: There are certain particularities about versioning that you can read more in depth
> in [the versioning document](docs/ocp_versioning.md)

## Inventory

The Ansible inventory file specified in the pipeline job definition includes the
configuration for the `dci-openshift-agent` job and the inventory for the
masters, workers (if any) and the provisioner.

Example:

```ini
[all:vars]
# The NIC used for provisioning network on all nodes
prov_nic=eno1
# The NIC used for baremetal network on all nodes
pub_nic=eno2
# Base domain
domain=example.com
# Name of the cluster
cluster=dciokd
# Disable the provisioning within the cluster (after installation)
#dci_disable_provisioning=false
# The directory used to store the cluster configuration files (install-config.yaml, pull-secret.txt, metal3-config.yaml)
dir="{{ ansible_user_dir }}/clusterconfigs"
# Virtual IP for the cluster ingress
dnsvip=1.2.3.4
# Override which NIC masters use for the private/provisioning network
#masters_prov_nic=eno1
# Disable TLS verification of BMC certificates
#disable_bmc_certificate_verification=true
# Enable some light caching on the provision host
#cache_enabled=false

# Activate disconnected mode in DCI OCP agent, requires you to set the next variables as well
#dci_disconnected=true
# Must be reachable from the cluster
#webserver_url="http://<jumpbox IP/DNS>:8080"
# Path of the file with the pull secret and registry auths in json format.
#pullsecret_file=/path/to/clusterX-pull-secret.txt
# Content of the pull secret as downloaded from from https://cloud.redhat.com/openshift/install/metal/user-provisioned
# *only* used when running a deployment without DCI.
#pullsecret='content-in-json-format'
# Path on the jumpbox
#disconnected_registry_auths_file=/path/to/auths.json
# Path on the jumpbox
#disconnected_registry_mirrors_file=/path/to/trust-bundle.yml
# Path on the jumpbox, must have enough space to hold your qcow images
# Please set setype to container_file_t if you create this folder manually
# sudo /usr/bin/chcon -t container_file_t /path/to/qcow/cache
#provision_cache_store="/path/to/qcow/cache"
# Registry host that will mirror all container images
#local_registry_host=local-registry
# Registry port
#local_registry_port=4443
# Registry namespace. In disconnected environments, the default value is set by the mirror-ocp-role
#local_repo=ocp4/openshift4
# NFS external storage variables
#enable_nfs_storage: false
#nfs_server=""
#nfs_path=""

# Master nodes
[masters]
master-0 name=master-0 ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-master-0.dciokd.example.com provision_mac=aa:bb:cc:dd:ee:ff
master-1 name=master-1 ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-master-1.dciokd.example.com provision_mac=aa:bb:cc:dd:ee:ff
master-2 name=master-2 ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-master-2.dciokd.example.com provision_mac=aa:bb:cc:dd:ee:ff

[masters:vars]
role=master
hardware_profile=default
# If needed, you can set node labels too
#labels='{"node-role.kubernetes.io.foo":"", "node-role.kubernetes.io.bar":""}' # example

# Worker nodes
[workers]
worker-0 name=worker-0 ipmi_user=ADMIN ipmi_password=ADMIN ipmi_address=ipmi-worker-0.dciokd.example.com provision_mac=aa:bb:cc:dd:ee:ff

[workers:vars]
role=worker
hardware_profile=default
# If needed, you can set node labels too
#labels='{"node-role.kubernetes.io.foo":"", "node-role.kubernetes.io.bar":""}' # example

# Provision Host
[provisioner]
provisionhost ansible_user=kni prov_nic=eno1 pub_nic=ens3 ansible_ssh_common_args="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
```

> NOTE: If the jumpbox server is in a different network than the baremetal network, then
> include `extcirdnet=<baremetal-network/mask>` in the `all:vars` section of the inventory

> NOTE: If you choose to create the `provision_cache_store` folder manually, make sure to set the `container_file_t` setype for it. This will help ensure a smooth installation of OCP nightly builds.

```
# sudo /usr/bin/chcon -t container_file_t /path/to/qcow/cache
# ls -lZd /path/to/qcow/cache
drwxr-xr-x. 19 dci dci system_u:object_r:container_file_t:s0 4096 may 02 18:28 /path/to/qcow/cache
```

## Disconnected mode in DCI OCP agent

When using the agent in a disconnected environment, special variables should be used. See
the [disconnected doc](docs/disconnected_en.md) for more details.

## Pull secrets

Pull secrets are credentials used against container registries that require authentication.

DCI provide pull secrets used to deploy OCP on every job.

- `cloud.openshift.com` - Insights monitoring
- `quay.io` - Openshift releases
- `registry.ci.openshift.org` - Nightly builds
- `registry.connect.redhat.com` - Red Hat images
- `registry.redhat.io` - Red Hat images

These pull secrets are used by default, but the agent allows using other pull secrets if needed through some variables.

- `openshift_secret`: String with secrets that are appended to the job's provided pull secrets. Used to include additional credentials. This is an agent variable.
- `disconnected_registry_auths_file`: A file with a string that contains the auths for private registries.
- `pullsecret_file`: File with secrets in JSON format that will be used along with the ones provided by DCI job and the `openshift_secret`.

The content all these variables is merged by DCI, those secrets are combined in a single podman authentication file used to interact with the required registries during the mirroring, image inspections, pruning tasks performed byt the DCI Openshift agent.

Important:

- Secrets are processed in the following order: Job secrets --> openshift_secret --> disconnected_auths --> pull_secret_file
- If a registry entry exists in multiple sources, the last one processed takes priority
- It is recommended that the additional secrets are set in the form of registryA/<namespace> to use an specific auth entry against a registry as recommended in the [podman documentation](https://github.com/containers/image/blob/main/docs/containers-auth.json.5.md)

### Disconnected environment

Another related variable is `disconnected_registry_auths_files` used in IPI or SNO installs.

This is an inventory variable used in disconnected environments.
The content of this file is appended to the list of DCI provided pull secrets. This file is used for two main purposes.

- To allow the cluster to communicate to a local registry
- To use to mirror images to the local registry

## Storing secrets

You can store secrets in an encrypted manner in your pipelines and YAML inventories by using `dci-vault` to
generate your encrypted secrets. Details in the [python-dciclient documentation](../python-dciclient/).

## Deploying operators

The Agent manages the mirroring and deployment of most of the day-2 operators. For others, it can configure them by setting up the corresponding operands.

The workflow for the deployment is:

- Operator mirroring for disconnected environments

- Operator installation

- Operator configuration

### Operators mirroring for disconnected environments

The opm_mirror_list variable, controls the operators that are mirrored when dci_disconnected is true. The Agent takes care of mirroring the required operator's images and creates a pruned catalog source for the OCP cluster. Some examples are below:

- Explicit definition (This is recommended)

Example 1:

Definition of three operators. Two operators specify the channels, while the last compliance-operator includes all the channels.

```yaml
opm_mirror_list:
  file-integrity-operator:
    channel: stable
  cluster-logging:
    channel: stable-5.8
  compliance-operator:
```

Example 2:

Same three operators, this time all the channels are included.
```yaml
opm_mirror_list:
  file-integrity-operator:
  cluster-logging:
  compliance-operator:
```

- Implicit definition, always includes all the channels (Prefer to use Example 2 above)

Example 3:

A pruned catalog with all operator's channels.

```yaml
opm_mirror_list:
  - compliance-operator
  - file-integrity-operator
  - cluster-logging
```

> NOTE: By default the catalog source name that can be used to create operator subscription is named mirrored-redhat-operators.

> NOTE: Some operators may have other operators dependencies, for such cases the dependencies must be added to the list.

### Operators installation

Operator subscriptions and installation monitoring are controlled by the `dci_operators` variable, which allows basic or custom installations. An example of how to define the `dci_operators` variable is shown below.

```yaml
dci_operators:
  - name: compliance-operator
    catalog_source: mirrored-redhat-operators
    namespace: openshift-compliance
  - name: cluster-logging
    catalog_source: mirrored-redhat-operators
    namespace: openshift-logging
  - name: local-storage-operator
    catalog_source: mirrored-redhat-operators
    namespace: openshift-local-storage
    channel: stable
    starting_csv: 4.14.0-202307190803
    operator_group_name: local-storage
    operator_group_spec:
      targetNamespaces:
        - openshift-local-storage
  - name: ocs-operator
    catalog_source: mirrored-redhat-operators
    namespace: openshift-storage
    operator_group_spec:
      targetNamespaces:
        - openshift-storage
    ns_labels:
      openshift.io/cluster-monitoring: "true"
```

> Important: For a successful operator installation, ensure that the settings defined in dci_operators align with the packages available in the specified catalog_source. The following examples highlight potential misconfigurations that can cause the operator installation to fail:

* Selecting an installation channel that is unavailable.
* Configuring an operator group with settings not supported by the operator.
* Specifying a starting CSV that is not available in the selected channel.

### Operator configuration

For some operators, the agent support the operand creation by setting to `true` specific flags. See `enable_<operator>` variables above. Also, the operator configuration can be executed as part of a run during the `/hooks/install.yml` phase.

## Install all operators from a catalog

All the operators available in a catalog can be installed on the cluster by setting `install_all_from_catalog`. This is mainly to test if the operators are deployable by OLM. There is no additional testing, or configuration executed after a running CSV is detected.

The catalog source namespace defaults to `openshift-marketplace` but that can be set using the `install_all_from_catalog_source` variable in case the catalog was created on a different namespace.

```yaml
install_all_from_catalog: <my-ocp-catalog>
install_all_from_catalog_source: <my-ocp-catalog-namespace>
```

## Additional Catalogs

Additional catalogs can be configured for the cluster to provide another source to install operators. Set the `custom_catalogs` variable with the references to the catalog images. For example:

```yaml
custom_catalogs:
  - quay.io/telcoci/sriov-operator-catalog:latest
  - quay.io/telcoci/simple-demo-operator:v0.0.3
  - quay.io/telcoci/nfv-example-cnf-catalog:v0.2.9
  - icr.io/cpopen/ibm-operator-catalog:latest
```

All the images available in the defined catalogs will be mirrored when `dci_disconnected` is `true` and a `local_image_registry` is defined.

Please see the [settings table](#ansible-variables) for the variables names to control the Operators deployment.

#### Mirroring from directory

In fully disconnected environments, mirroring can be performed by loading operators previously stored in a local file. The `oc mirror` plugin, allows the creation of catalogs that can be stored on a USB stick that will be used later to load operators on a local image registry.

The dci-openshift-agent can consume files generated by the `oc mirror` plugin. The agent uploads these files to the local registry, creates the catalog source, and applies the corresponding  ImageContentSourcePolicies (ICSPs). The catalog source is then used to deploy the operators enabled for testing.

The `operator_catalog_dir` variable should be set to a valid directory that contains one or multiple archive files generated using the [oc mirror plugin](https://docs.openshift.com/container-platform/4.13/installing/disconnected_install/installing-mirroring-disconnected.html). In the provided example, `operator_catalog_dir: /data/` is used as the path to the archive tar files.

Subscriptions for the mirrored operators can be defined using the `dci_operators` variable as explained above.

## Minio deployment

Some workloads like Migration Toolkit for Containers or Loki may require an object Object Storage provider. For such cases, a [Minio](https://min.io/) instance can be deployed on the OCP cluster by setting `true` to the `enable_minio` flag.

In the DCI Openshift Agent integration, an initial bucket named `loki` is deployed and is used for the [logging](#logging-stack) if no information about an external Object provider are provided.

The following variables allow customizing the Minio deployment. Please see the [minio_setup](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/setup_minio) role for additional details.

| Variable                               | Default                       | Required   | Description                                   |
| -------------------------------------- | ----------------------------- | ---------- | ----------------------------------------------|
| minio_claim_size                       | 10Gi                          | No         | Requested storage for Minio                   |
| minio_storage_class                    | undefined                     | Yes        | A storage Class with Support for RWX volumes  |
| minio_namespace                        | minio                         | No         | Deployment Namespace                          |
| minio_access_key_id                    | minioadmin                    | No         | Minio's Initial Username                      |
| minio_access_key_secret                | minioadmin                    | No         | Minio's Initial Password                      |
| monio_bucket_name                      | minio                         | No         | Initial Bucket name                           |

The workloads that require Object Storage, can use the `http://minio-service.minio:9000` endpoint and the default credentials set in the [minio_setup](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/setup_minio) role to start shipping data to Minio.

## Logging stack

The `enable_logs_stack` variable allows configuring OCP to send log files and metrics produced by the infrastructure and workloads to a logging stack. This stack is integrated by the ClusterLogging, Loki and an Object storage system.

The following variables allow customizing the logs stack deployment. Please see the [ocp_logging](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/ocp_logging) role for additional details.

| Variable                        | Required | Type    | Default                                                        | Description
| ------------------------------- | -------- | ------- | -------------------------------------------------------------- | ------------
| logs_access_key_id              | False    | String  | undefined                                                      | Key ID for the Object storage system.
| logs_access_key_secret          | False    | String  | undefined                                                      | Key Secret for the Object Storage system.
| logs_bucket                     | False    | String  | undefined                                                      | Object Storage bucket name.
| logs_endpoint                   | False    | String  | undefined                                                      | Object Storage endpoint.
| logs_region                     | False    | String  | undefined                                                      | Object Storage region.
| logs_loki_size                  | False    | String  | undefined                                                      | Loki Deployment Size. See [Sizing](https://docs.openshift.com/container-platform/4.13/logging/cluster-logging-loki.html#deployment-sizing_cluster-logging-loki) for more details.
| logs_storage_class              | False    | String  | undefined                                                      | Cluster Storage class for Loki components.
| logs_event_router_image         | False    | String  | registry.redhat.io/openshift-logging/eventrouter-rhel8:v5.2.1-1| Event Router image.
| logs_settings                   | False    | String  | ""                                                             | An optional yaml file with the variables listed above. The variables defined there take precedence over the ones defined at role level

Enabling the openshift `cluster-logging` components requires high amounts of storage available for data persistency, please take this in consideration during the sizing of the Object Storage provider.

## Network Observability stack

The `enable_netobserv` variable allows configuring the Network Observability operator to collect information about OCP network flows and traffic. This stack is integrated by the Network Observability Operator, Loki, an Object storage system and the Flow Collector.

The following variables allow customizing the Network Observability stack deployment. Please see the [ocp_netobserv](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/ocp_netobserv) role for additional details.

 Variable                                         | Default                         | Required    | Description
------------------------------------------------- | ------------------------------- | ----------- | ----------------------------------------------
setup_netobserv_stackaction                       | 'install'                       | No          | Role's default action
setup_netobserv_stacksampling                     | 50                              | No          | Data sampling
setup_netobserv_stackagent_privileged             | true                            | No          | Privileged mode allows collecting data from SRIOV functions
setup_netobserv_stackagent_memory                 | 50Mi                            | No          | Memory assigned to the agent
setup_netobserv_stackagent_cpu                    | 100m                            | No          | CPU assigned to the agent
setup_netobserv_stackagent_limits_memory          | 800Mi                           | No          | Memory limit for the agent
setup_netobserv_stackprocessor_memory             | 100Mi                           | No          | Memory assigned to the processor
setup_netobserv_stackprocessor_cpu                | 100m                            | No          | CPU assigned to the processor
setup_netobserv_stackprocessor_limits_memory      | 800Mi                           | No          | CPU limit for the processor
setup_netobserv_stackconsole_avg_utilization      | 50                              | No          | Average utilization for the console
setup_netobserv_stackconsole_max_replicas         | 3                               | No          | Console replicas
setup_netobserv_stackloki_tls_insecure_skip_verify| true                            | No          | Skip TLS verification
setup_netobserv_stackaccess_key_id                | minioadmin                      | No          | Access Key ID for the object storage backend
setup_netobserv_stackaccess_key_secret            | minioadmin                      | No          | Secret Key for the object storage backend
setup_netobserv_stackbucket                       | network                         | No          | Bucket for the Network Observability
setup_netobserv_stackendpoint                     | http://minio-service.minio:9000 | No          | Object Storage Endpoint. It must exist and be reachable
setup_netobserv_stackregion                       | us-east-1                       | No          | Object Storage region
setup_netobserv_stackloki_size                    | 1x.extra-small                  | No          | Loki Stack size. See: [Sizing](https://docs.openshift.com/container-platform/4.13/logging/cluster-logging-loki.html#deployment-sizing_cluster-logging-loki) for details
setup_netobserv_stackstorage_class                | managed-nfs-storage             | No          | Storage class for the Loki Stack

The configuration setting can be passed using the `dci_netobserv_conf_file` containing the variables listed above.

Enabling the Openshift `Network observability Operator` requires high amounts of storage available for data persistency, please take this in consideration during the sizing of the Object Storage provider. By default, the stack is configured to use the internal [Minio deployment](#minio-deployment) as backend.

## Interacting with your RHOCP Cluster

After you run a DCI job you will be able to interact with the RHOCP cluster using the OC client, the API, or the GUI.

1. Using the OC client

    ```bash
    export KUBECONFIG=/home/<user>/<clusterconfigs-path>/kubeconfig
    oc get nodes
    ```

   A copy of the generated kubeconfig file will be attached to the job files section in DCI.

1. Using the GUI/API

   Obtain the credentials generated during the installation from /home/`<user>`/`<clusterconfigs-path>`/ocp_creds.txt in
   the jumphost.

   Get the the URL of the cluster GUI:

    ```bash
    $ oc whoami --show-console
    https://console-openshift-console.apps.<cluster>.<domain>
    ```

> NOTE: The dci-openshift-agent is part of
> a [Continuous integration](https://en.wikipedia.org/wiki/Continuous_integration) tool aimed to perform OCP deployments,
> should not be considered for production workloads. Use the above connection methods if some troubleshooting is required.

## Non-GA versions of API

Some of the APIs used by the `dci-openshift-agent` are still in the beta or alpha version. See the following table for details regarding its status.

| API                     | Why it is used   |
| ----------------------- | ---------------- |
| hco.kubevirt.io/v1beta1                    | As of Jan 2023, [v1beta1 is the latest version for HyperConverged Cluster Operator](https://github.com/kubevirt/hyperconverged-cluster-operator/blob/main/docs/cluster-configuration.md#storage-resource-configurations-example). |
| kubevirt.io/v1alpha3                       | We only keep v1alpha3 for VirtualMachine on OCP-4.7 (k8s 1.20) because v1 does not exist yet for this version. For OCP versions >= 4.8, we use v1. |
| metal3.io/v1alpha1                         | As of Jan 2023, [v1alpha1 is the latest version for the Provisioning API](https://docs.openshift.com/container-platform/4.11/rest_api/provisioning_apis/baremetalhost-metal3-io-v1alpha1.html).      |
| operators.coreos.com/v1alpha1              | As of Jan 2023, v1alpha1 is the latest version for [OperatorHub APIs](https://docs.openshift.com/container-platform/4.11/rest_api/operatorhub_apis/operatorhub-apis-index.html) such as CatalogSource, Subscription, CSV, and InstallPlan.                                 |
| extensions.hive.openshift.io/v1beta1       | As of Jan 2023, AgentClusterInstall API uses [v1beta1](https://github.com/openshift/assisted-service/tree/master/api/hiveextension) as the latest version.                                     |
| agent-install.openshift.io/v1beta1         | As of Jan 2023, both InfraEnv and AgentServiceConfig API use [v1beta1](https://github.com/openshift/assisted-service/tree/master/api) as the latest version.                                     |

## Job outputs

A DCI job produces a set of relevant configuration files, logs, reports, and test results that are collected during the last execution stages. The following table depicts the most relevant.

| File                                            | Section | Description                                                                               |
| ----------------------------------------------- | ------- | ----------------------------------------------------------------------------------------- |
| install-config-yaml.txt                         | Files   | Configuration file used for the cluster deployment                                        |
| all-nodes.yaml                                  | Files   | The output `oc get get nodes -o yaml` command                                             |
| *.log                                           | Files   | Log files generated during the job execution and stored in the `dci_log` directory        |
| *.trace                                         | Files   | Tracing files generated during the job execution and stored in the `dci_log` directory    |
| \<cluster-name\>-\<master\|worker\>-console.log | Files   | Console log from the specific master or worker node                                       |
| \<journal\>-\<master\|worker\>.log              | Files   | A dump of the node systemd logs for the cluster nodes                                     |
| clusternetwork.yaml                             | Files   | File describing the network configuration of the cluster                                  |
| clusteroperator.txt                             | Files   | Report of the status of the cluster operators                                             |
| dci-openshift-agent-\<timestamp\>               | Files   | `dci-openshift-agent` tests report as JUnit format                                        |
| clusterversion.txt                              | Files   | Report of the OCP version applied to the cluster                                          |
| events.txt                                      | Files   | Output of the `oc get events -A` command                                                  |
| kubeadmin-password                              | Files   | Password assigned to the `kubeadmin` user                                                 |
| kubeconfig                                      | Files   | Kubeconfig file to interact with the deployed OCP cluster                                 |
| nodes.txt                                       | Files   | Output of the `oc get nodes` command                                                      |
| pods.txt                                        | Files   | Output of the `oc get pods -A` command                                                    |
| must_gather.tar.gz                              | Files   | Cluster state information. Useful for support cases or troubleshooting with [O Must Gather tool](https://github.com/kxr/o-must-gather) |
| ocp_creds.txt                                   | Files   | A set of admin and non-admin credentials attached to an httpasswd identity provider       |
| openshift_install.log                           | Files   | Openshift installation log file                                                           |
| version.txt                                     | Files   | Report of the OCP client and server version using during the deployment                   |
| diff-jobs.txt                                   | Files   | A report that compares the `current` and `previous` job's components of the same type     |
| *.junit                                         | Tests   | Processed JUnit files generated by the Job or partner tests                               |
| machine-configs.txt                             | Tests   | Debugging information regarding the machine configs status                                |
| image-sources.yaml                              | Files   | ImageDigestMirrorSetis or ImageContentSourcePolicies applied to the cluster               |
| openshift_install_state.json                    | Files   | The installation state of the cluster, contains paramaters used, progress, etc.           |
| operators.json                                  | Files   | A JSON file with details about the operators installed in the cluster                     |
| worker-kernel-params.json                       | Files   | A JSON file with details about the kernel argsuments used by the workers                  |

You may find extra files for the case of Assisted jobs:

| File                                           | Section | Description                                                                               |
| ---------------------------------------------- | ------- | ----------------------------------------------------------------------------------------- |
| agent-config.yaml                              | Files   | agent-config file from the Assisted deployment                                            |
| install-config.yaml                            | Files   | install-config file from the Assisted deployment                                          |
| \<pod_name\>_ai_pod.log                        | Files   | Log files from pods (`assisted-db`, `assisted-installer`, `cluster-bootstrap` and `service`) deployed during Assisted bootstrap stage |
| \<service_name\>.log                           | Files   | Log files from services (`bootkube` and `release-image`) running during Assisted bootstrap stage |
| log-bundle-\<date\>                            | Files   | If present, it represents the output of `openshift-install gather bootstrap` command      |

## Troubleshooting common issues

- [Basic configuration](#troubleshooting-basic-configuration)
- [Network connectivity](#troubleshooting-network-connectivity)
- [OpenShift bootstrap](#troubleshooting-ocp-bootstrapping)
- [OpenShift install](#troubleshooting-ocp-install)

### Troubleshooting basic configuration

Review the following checklist to make sure you've got all the basic pieces in
place:

- Is the DCI repo configured?
- Is the dci-openshift-agent package the latest version?
- Does my credentials file contain my remote CI
  credentials as per the distributed-ci.io dashboard?
- Does my inventory reflect my cluster's expected
  configuration? Check the following variables:
    - `cluster`
    - `domain`
    - `prov_nic`
    - `pub_nic`
    - IPMI configuration for all nodes in OCP cluster: `ipmi_user`,
      `ipmi_password`, `ipmi_address`
    - MAC addresses for all nodes in OCP cluster
- Does my pipeline file reflect the right
  topic/component for my needs?
- Is my `dci-openshift-agent` SSH key transferred to the provision host? e.g.
  can I SSH without a password from Jumpbox -> provisioner?

### Troubleshooting network connectivity

First, take another look at the [network requirements](#network-requirements)
section and make sure your setup looks similar to the proposed basic diagram.
Your particular lab may differ in how things are laid out, but the basic points
to look for are:

- Your `provisioning` network should be treated as an exclusive "out of band"
  network only intended to PXE boot the initial cluster OS
- Your `baremetal` network should be capable of routing to:
    - Your jumpbox
    - Your cluster nodes' BMCs (e.g. your management network)
- You should have outbound internet access from your Jumpbox (and OCP cluster
  unless in [disconnected mode](docs/disconnected_en.md))
- Your `baremetal` network should be DHCP enabled and have addresses for all of
  your cluster nodes *plus* the bootstrap VM (usually not an issue but make
  sure there are enough IP addresses to lease)
- Your Jumpbox, provisioner, and cluster nodes all should be able to resolve
  your API and your wildcard DNS entries e.g. `api.<cluster>.<domain>` and
  `*.apps.<cluster>.<domain>`
- The provision host should have 2 bridges setup: one for the `provisioning`
  network and another for the `baremetal` network, are both setup? Are the
  functional?

Here are a few things you can check to make sure the above assertions are true:

- Can I query the power status of the cluster nodes from the provisioner and
  control-plane nodes via e.g. `ipmitool`?
- Can I curl one of the mirror.openshift.com resources from the provisioner and
  cluster nodes?
- Is the lab's DNS resolvable from all places via e.g. `dig
  api.<cluster>.<domain>` and `dig foo.apps.<cluster>.<domain>`?

### Troubleshooting OCP bootstrapping

You can monitor the bootstrap/install process by logging into the provision
host and tailing the file `~/clusterconfigs/.openshift_install.log`.

If you're having issues once the agent gets to the point where
`baremetal-install` is called, you can check a few things:

- Check the `~/clusterconfigs/install-config.yaml.bkup` file in your provision
  host (this is a copy of the install manifest fed to `baremetal-install`) and
  make sure the manifest looks correct
- Is the bootstrap VM coming up? e.g. `sudo virsh list --all` should list a VM
  named `*-bootstrap` about 5-10 minutes after you started the run
- Is the bootstrap VM getting IP address from the `baremetal` network? Run
  `virsh console <bootstrap VM>` and a linux login prompt should be visible,
  hit `<Enter>` and it should show 2 IP addresses: a DHCP one as per your
  configuration, and a static `172.22.0.22` on the `provisioning` network
- Is your bootstrap VM up coming up correctly? You can `ssh core@172.22.0.2`
  and check the status of the pods running on the system by `sudo podman ps`.
  You should see (after a few minutes) some pods named
  `ironic-{api,conductor,inspector}`
- Check the logs of the `ironic-*` pods with `sudo podman logs <pod>` and look
  for errors/exceptions
- Is your `ironic-conductor` able to interact with the BMCs? Try logging
  yourself to the pod (`sudo podman exec -it ironic-conductor /bin/sh`) and
  make sure there is connectivity to the BMC e.g. `ipmi -I lanplus -H <BMC
  host> -U <BMC user> -P <BMC password> power status`

### Troubleshooting OCP install

During the deployment, ironic services are started temporally in the bootstrap
VM, to help bootstrapping the master nodes.
Then after the master nodes are ready to take the role, bootstrap VM is deleted
and ironic services are started in the cluster.
At both stages you can interact with ironic to see details of the nodes

If you want to interact with ironic services during the bootstrap, get the
baremetal network IP of ironic service from the bootstrap VM

```console
[core@localhost ~]$ sudo ss -ntpl | grep 6385
[core@localhost ~]$ ip a s ens3
```

Get the bootstrap VM ironic credentials from the terraform variables back in
the provision host

```console
[dci@provisionhost ~]$ grep ironic_ clusterconfigs/terraform.baremetal.auto.tfvars.json
  "ironic_username": "bootstrap-user",
  "ironic_password": "foo",
```

If you want to interact with ironic services in the cluster, get the IP of
ironic service from the metal3 resources

```console
[dci@provisionhost ~]$ export KUBECONFIG=/home/dci/clusterconfigs/auth/kubeconfig
[dci@provisionhost ~]$ oc -n openshift-machine-api get pods # find the metal3 pod
[dci@provisionhost ~]$ oc -n openshift-machine-api describe pod <pod> | egrep ^IP:
IP:                   192.168.123.148
[dci@provisionhost ~]$ oc -n openshift-machine-api get secrets metal3-ironic-password \
  -o jsonpath='{.data.username}' | base64 -d
ironic-user
[dci@provisionhost ~]$ oc -n openshift-machine-api get secrets metal3-ironic-password \
  -o jsonpath='{.data.password}' | base64 -d
bar
```

Then prepare a clouds.yaml with the following information, and replace the IP
addresses and password accordingly

> NOTE: Starting with OCP 4.7 `metal3-boostrap` service uses `auth_type: http_basic`, but in in older versions it
> uses `auth_type: none` so there's no need to set auth section with the credentials

```YAML
clouds:
  metal3-bootstrap:
    auth_type: http_basic
    auth:
      username: bootstrap-user
      password: $BOOTSTRAP_PASSWORD
    baremetal_endpoint_override: http://IP-Provisioining-bootstrapVM-IP:6385
    baremetal_introspection_endpoint_override: http://IP-Provisioining-bootstrapVM-IP:5050
  metal3:
    auth_type: http_basic
    auth:
      username: ironic-user
      password: $IRONIC_PASSWORD
    baremetal_endpoint_override: http://IP-Provisioining-Master-IP:6385
    baremetal_introspection_endpoint_override: http://IP-Provisioining-Master-IP:5050
```

Back in the provisioning host, install podman and start a container, set
`OS_CLOUD` with metal3 if you want to use the ironic services on the cluster,
or metal3-bootstrap if you want to use the services on the bootstrap VM (if
still running)

```console
[dci@provisionhost ~]$ sudo dnf install -y podman
[dci@provisionhost ~]$ podman run -ti --rm \
  --entrypoint /bin/bash \
  -v /home/dci/clouds.yaml:/clouds.yaml:z \
  -e OS_CLOUD=metal3
  quay.io/metal3-io/ironic-client
```

Finally from the pod you started, you can run ironic baremetal commands

```console
[root@8ce291ff4f4a /]# baremetal node list
+--------------------------------------+----------+--------------------------------------+-------------+--------------------+-------------+
| UUID                                 | Name     | Instance UUID                        | Power State | Provisioning State | Maintenance |
+--------------------------------------+----------+--------------------------------------+-------------+--------------------+-------------+
| ba3d1990-e860-4685-9929-3c3356e6e29e | master-1 | 7a116082-1b8a-4f65-9991-242dd56ed44b | power on    | active             | False       |
| 3ab260c7-9a1e-48bf-841a-473a3cec2cbd | master-2 | a9658128-570c-45ad-9ef6-d4721aeaeb81 | power on    | active             | False       |
| d67ade66-d9e1-4825-b53e-381870ff5c81 | master-0 | 728106a3-1994-4e86-9a8c-838becf22aa5 | power on    | active             | False       |
+--------------------------------------+----------+--------------------------------------+-------------+--------------------+-------------+
```

## dci-openshift-agent workflow

0. "New DCI job"
    - Create a DCI job
    - *tags: job*
    - *runs on: localhost*

1. "Pre-run"
    - Prepare the `Jumpbox`: `/plays/pre-run.yml`
    - Trigger partner Jumpbox preparation if needed: `/hooks/pre-run.yml`
    - *tags: pre-run, hook-pre-run*
    - *runs on: localhost*

2. "Configure"
    - Prepare provisioner: `/plays/configure-provisioner.yml`
    - Trigger partner Provisioner preparation if needed: `/hooks/configure.yml`
    - *tags: running, configure*
    - *runs on: provisioner*

3. "DCI Main"
    1. "Install" (`dci_main` is "install" or undefined)
        - Start OpenShift install: `/plays/install.yml`
        - Trigger partner install hook if needed: `/hooks/install.yml`.
        - *tags: running, installing, hook-installing, post-installing*
        - Runs the post installation: `/plays/post-install.yml`
        - *runs on: provisioner*

    2. "Upgrading" (`dci_main` is "upgrade")
        - Start OpenShift upgrade: `/plays/upgrade.yml`
        - Trigger partner upgrade hook if needed `/hooks/upgrade.yml`
        - *tags: running, upgrading, hook-upgrading*
        - *runs on: provisioner*

    3. "Deploy operators"
        - start operator deployment: `/plays/deploy-operators.yml`
        - *tags: running, operator-deployment*
        - *runs on: provisioner*

4. "Red Hat tests"
    - start Red Hat tests: `/plays/tests.yml`
    - *tags: running, testing, redhat-testing*
    - *runs on: localhost*

5. "Partner tests"
    - start partner tests: `/hooks/tests.yml`
    - *tags: running, testing, partner-testing*
    - *runs on: localhost*

6. "Post-run"
    - Start post-run to collect results: `/plays/post-run.yml` and
      `/hooks/post-run.yml`
    - *tags: post-run*
    - *runs on: localhost*
   > NOTE: All results files (logs, tests, ...) must be stored within the `{{ dci_cluster_configs_dir }}/` directory in
   order to be properly uploaded to the DCI server. Test result files must follow the Junit format, must be stored within 
   the `{{ job_logs.path }}` directory and the file name must follow the pattern `*.xml`.

7. "Success"
    - Launch additional tasks when the job is successful: `/hooks/success.yml`
    - *tags: success*
    - *runs on: localhost*

*Exit playbooks:*
The following playbooks are executed sequentially at any step that fail:

- Teardown: `/hooks/teardown.yml` which is executed only when the boolean `dci_teardown_on_success` is set to `true` (
  set to `true` by default)
- Failure: `/plays/failure.yml` and `/hooks/failure.yml` during the `running` steps and `/plays/error.yml` during the
  other steps. `/hooks/failure.yml` was added to allow custom debug command to gather more meaningful logs.

> NOTE: All the task files located in directory `/etc/dci-openshift-agent/hooks/` are empty by default and should be
> customized by the user.

All the tasks prefixed with `test_` will get exported in Junit using the
[Ansible Junit
callback](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/junit_callback.html)
and submitted automatically to the DCI control server.

## OCP upgrades using dci-openshift-agent

### Test OCP upgrades using the dci-openshift agent

The `dci-openshift-agent` supports testing cluster upgrades by executing an `upgrade pipeline`.

See below and an example of a pipeline job definition:

```yaml
- name: openshift-vanilla-upgrade-4.10
  stage: ocp-upgrade
  prev_stages: [ocp-upgrade, ocp]
  ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
  ansible_cfg: /var/lib/dci/pipelines/ansible.cfg
  ansible_inventory: /var/lib/dci/inventories/inventory
  dci_credentials: /etc/dci-openshift-agent/dci_credentials.yml
  configuration: "@QUEUE"
  ansible_extravars:
    dci_config_dirs: [/var/lib/dci/dallas-config/dci-openshift-agent]
    dci_local_log_dir: /var/lib/dci-pipeline/upload-errors
    dci_tags: []
    dci_cache_dir: /var/lib/dci-pipeline
    dci_base_ip: "{{ ansible_default_ipv4.address }}"
    dci_baseurl: "http://{{ dci_base_ip }}"
    dci_main: upgrade
    cnf_test_suites: []
    performance_definition: /<path>/performance-profile.yml
    tuned_definition: /<path>/tuned-definition.yml
    # Operators to mirror
    opm_mirror_list:
      loki-operator:
      cluster-logging:
  topic: OCP-4.10
  components:
    - ocp
  outputs:
    kubeconfig: "kubeconfig"
  success_tag: ocp-upgrade-4.10-ok
```

Please note the following settings:

1. `prev_stages`: Indicates that this pipeline can only be executed after an OCP install or another OCP upgrade, as those will provide the `kubeconfig` used to interact with the cluster during the upgrade.
1. `dci_main`: Instructs the agent to execute only the tasks related to a cluster upgrade. Accepted values are `install` and `upgrade`.
1. `opm_mirror_list`: During the upgrade the operators already installed will be upgraded, those operators must be listed in this variable to perform the operators mirroring according to the target OCP version.

See: [dci-pipeline](https://docs.distributed-ci.io/dci-pipeline/) documentation for more details about the configuration settings.

The agent supports 2 types of upgrades:

1. Upgrades to the next support <major>.<minor>-<patch> release version according the [OCP update graph](https://access.redhat.com/labsinfo/ocpupgradegraph).
1. Extended Update Support (EUS) upgrades, if the current cluster version is EUS supported version. See [preparing EUS-EUS upgrade](https://docs.openshift.com/container-platform/4.10/updating/preparing-eus-eus-upgrade.html).

#### The upgrade process

Some of the relevant tasks executed during a cluster upgrade are listed below:

1. A DCI job is created to track the upgrade process.
1. The specific target version is calculated based on the [OCP upgrade graph](https://access.redhat.com/labs/ocpupgradegraph/update_path).
1. The target OCP release is mirrored to the same images <registry>/<path> that was used for the cluster deployment. For EUS upgrades, the intermediate release images are also mirrored <sup>1</sup>.
1. The ISO, rootfs, and other artifacts are mirrored to the same `webserver_url` used for the initial cluster deployment <sup>1</sup>.
1. The Image Content Source Policies and OCP signature for the new version are applied <sup>1</sup>.
1. The "cluster version" is patched for the new target version based on the calculated target version.
1. The upgrade is executed and monitored for completion.
1. The Red Hat operators catalog for the new OCP version is pruned and mirrored according to the `opm_mirror_list` or `dci_operators` variables defined in the pipeline file <sup>1</sup>.
1. The current Red Hat operators catalog is replaced with the new one for the target OCP version.
1. Information about installed operators is collected based on the current subscriptions.
1. The operator upgrade is executed for operators not listed in the `operator_skip_upgrade` list.
1. An operator upgrade will be triggered if:
   * There is a new CSV version available for the currently installed operator in the current channel.
   * There is a new default channel available for the currently installed operator. That will usually imply the availability of a new CSV.
1. Operators' upgrade starts and is monitored until it reaches the target CSV.
1. Cluster resources, machine config pools, cluster operators, etc. are validated to declare a cluster as successfully upgraded.
1. The relevant logs and cluster information are uploaded to the "Files" section of the DCI-UI.

<sup>1</sup> Only in disconnected environments.

#### The EUS upgrade

OpenShift offers a way to facilitate the upgrade between two EUS versions. This allows upgrading between even versions, for example from ocp-4.8 to ocp-4.10. Detailed documentation is available in [preparing EUS-EUS upgrade](https://docs.openshift.com/container-platform/4.10/updating/preparing-eus-eus-upgrade.html)

To perform this type of upgrade with DCI, the following conditions must be met:

- Activate the boolean `upgrade_eus` to true.
- The cluster has to be installed in an EUS version.
- The topic or target version must be an EUS release.

Transitioning between two OCP releases requires an intermediate version. It's possible to specify the intermediate version through `version_inter`, this ignores the upgrade path.

For example, to upgrade to a version where there's no path to it. Specify the intermediate version. `version_inter:4.11.5` or to use candidate versions use `version_inter:4.11.0-*`.

Note the `-*`, this will help to include candidate versions in the search.

Upgrade notes:

* The upgrade process is only supported when the installation was performed with the dci-openshift-agent.

* For disconnected environments, it's required to mirror the same operators originally installed in the cluster in order to allow the upgrade to the version used for the upgrade.

* Please see the [ansible-variables](#ansible-variables) section for more settings related to the upgrade process.

## Custom Builds

This is a way to test with custom builds. The requirements are:

- Pipeline
  - Must NOT contain `ocp` component
  - Must define:

  ```yaml
    dci_custom_component: true
    dci_custom_component_file: /path/to/custom_component.json
  ```
- Inventory
  - Must define a pullsecret with access to the custom build image

  ```yaml
    pullsecret_file: /path/to/custom_pullsecret.json
  ```

Example of a custom component file:

```json
{
  "data": {
    "pull_url": "registry.<sub-domain>.ci.openshift.org/<build-id>/release@sha256:abcdef...",
    "version": "4.15.0-0.ci.test-<timestamp>-<id>"
  },
  "tags": [
    "sha256:abcdef...",
    "build:nightly"
  ],
  "id": "",
  "type": "ocp",
  "url": "https://registry.<sub-domain>.ci.openshift.org/<build-id>/release:latest"
}
```

## Keep the DCI OCP Agent Updated

It is recommended to keep the Jumpbox server updated, enable dnf-automatic
updates to make sure system is using latest dci-openshift-agent

Install dnf-automatic

```console
# dnf install -y dnf-automatic
```

Modify the default configuration to enable automatic downloads and apply
updates

```console
# vi /etc/dnf/automatic.conf
...
download_updates = yes
apply_updates = yes
...
```

Enable the dnf-automatic.timer

```console
# systemctl enable --now dnf-automatic.timer
```

## Getting involved

Refer to [the development guide](docs/development.md)

## Create your DCI account on distributed-ci.io

Every user needs to create his personal account by connecting to
<https://www.distributed-ci.io> by using a Red Hat SSO account.

The account will be created in the DCI database at the first connection with
the SSO account. For now, there is no reliable way to know your team
automatically. Please contact the DCI team when this step has been reached, to
be assigned in the correct organisation.

## License

Apache License, Version 2.0 (see [LICENSE](LICENSE) file)

## Contact

Email: Distributed-CI Team <distributed-ci@redhat.com>

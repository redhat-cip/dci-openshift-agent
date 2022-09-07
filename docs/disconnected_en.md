# Disconnected environment

Frequently, portions of a data center might not have access to the Internet,
even via proxy servers. You can still install OpenShift Container Platform in
these environments, but you must download required software and images and make
them available to the disconnected environment.

## Table of Contents

- [Requirements](#requirements)
- [Configurations](#configurations)
- [Deploying the Registry (Optional)](#deploying-the-registry-optional)
  - [Registry demo](#registry-demo)
- [Running dci-openshift-agent](#running-dci-openshift-agent)
  - [Agent demo](#agent-demo)

## Requirements

- The registry host needs to have access to the Internet and at least 110 GB of
  disk space. You will download the required software repositories and
  container images to this computer. The registry host will usually be the
  jumpbox but it can be another server.

## Configurations

First you have to set the 'dci_disconnected' option to 'True' in the settings
file `/etc/dci-openshift-agent/settings.yml`.

All the configuration needs to be done in the ansible hosts file
`/etc/dci-openshift-agent/hosts`.

Following an example of the configuration file highlighting the variables
needed by the disconnected environment:

```INI
[all:vars]

# Local registry
local_registry_host=registry.example.com
local_registry_port=4443
local_registry_user=MY_REGISTRY_USER
local_registry_password=MY_REGISTRY_PASSWORD
provision_cache_store="/opt/cache"

[...]
webserver_url=http://pctt-hv1:8080

[...]
# Registry Host
#   Define a host here to create or use a local copy of the installation registry
#   Used for disconnected installation
[registry_host]
pctt-hv1 ansible_user=dci-openshift-agent

[registry_host:vars]
# The following cert_* variables are needed to create the certificates
#   when creating a disconnected registry. They are not needed to use
#   an existing disconnected registry.
disconnected_registry_auths_file=/opt/cache/pctt-hv1-auths.json
disconnected_registry_mirrors_file=/opt/cache/pctt-hv1-trust-bundle.yml
local_repo=ocp4/openshift4
# The following mirror entries are the default ones. If you want to add more mirror
#   you can uncomment this parameter and add it here.
#registry_source_mirrors=["quay.io/openshift-release-dev/ocp-v4.0-art-dev", "registry.svc.ci.openshift.org/ocp/release", "quay.io/openshift-release-dev/ocp-release"]
```

The variables needed by the disconnected environment:

Group                   | Variable | Required      | Type   | Description
----------------------- | -------- | ------------- | ------ |----------------------------------------------------
[all:vars] | dci_disconnected | True | Boolean | Main variable to specify this is a disconnected environment
[all:vars] | webserver_url | True | String | URL of the webserver hosting the qcow images
[all:vars] | local_registry_host | True | String | FQDN or IP for the registry server acting as a mirror
[all:vars] | local_registry_port | True | String | Listening Port for the registry server
[all:vars] | local_registry_user | True | String | Username for the registry server
[all:vars] | local_registry_password | True | String | Password of the registry user for the registry server
[all:vars] | provision_cache_store | True | String | Folder using for the caching
[all:vars] | pullsecret_file | Optional | String | Path of the file in the jumpbox with the pull secret and registry auths in json format. If not provided the content of disconnected_registry_auths_file and pullsecret variable (pulled from DCI components) will be combined to be used by all disconnected tasks.
[all:vars] | opm_local_registry_path | True | String | Path on the local registry host where the pruned catalog images will be stored
[registry_host]         |          | True          | String | Define a host here to create or use a local registry
[registry_host:vars] | disconnected_registry_auths_file | Optional | String | File that contains extra auth tokens to include in the pull-secret. This file will be generated if it doesn't exist. And only required if pullsecret_file var not provided)
[registry_host:vars] | disconnected_registry_mirrors_file | True | String | File that contains the addition trust bundle and image content sources for the local registry. The contents of this file will be appended to the install-config.yml file
[registry_host:vars] | registry_dir | True | String | Folder where to store the openshift container images
[registry_host:vars] | local_repo | True | String | Specify the name of the repository to create in your registry
[registry_host:vars] | registry_source_mirrors | False | String | List of the mirror entries pointing to the registry_host

## Deploying the registry (Optional)

A playbook exist to deploy the registry and the webserver storing the QCOW
images

On the jumpbox:

```Shell
su - dci-openshift-agent
cd samples
ansible-playbook infrastructure.yml
```

### Registry demo

[![demo](https://asciinema.org/a/vUVI3w23OBqQaM0Ux7IDOlaiq.svg)](https://asciinema.org/a/vUVI3w23OBqQaM0Ux7IDOlaiq?autoplay=1)

## Running dci-openshift-agent

After the configuration and the registry are setup, we can deploy openshift
using the dci-openshift-agent:

```Shell
systemctl start dci-openshift-agent
```

### Agent demo

[![demo](https://asciinema.org/a/zbrwiulDWgtV2ABzJ6pK4Uez3.svg)](https://asciinema.org/a/zbrwiulDWgtV2ABzJ6pK4Uez3?autoplay=1)

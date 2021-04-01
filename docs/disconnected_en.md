# Disconnected environment

Frequently, portions of a data center might not have access to the Internet, even via proxy servers. You can still install OpenShift Container Platform in these environments, but you must download required software and images and make them available to the disconnected environment.

## Table of Contents

- [Requirements](#requirements)
- [Configurations](#configurations)
- [Deploying the Registry (optional)](#deploying-the-registry-(optional))
- [Running dci-openshift-agent](#running-dci-openshift-agent)
- [License](#license)
- [Contact](#contact)

## Requirements:
* The registry host needs to have access to the Internet and at least 110 GB of disk space. You will download the required software repositories and container images to this computer. The registry host will usually be the Jumphost but it can be another server.

## Configurations:
All the configuration needs to be done in the ansible hosts file `/etc/dci-openshift-agent/hosts`.

Following an example of the configuration file highlighting the variables needed by the disconnected environment:
```
[all:vars]
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
provision_cache_store="/opt/cache"
local_repo=ocp4/openshift4
```
The variables needed by the disconnected environment:

| Group                   | Variable | Required      | Type   | Description                                   |
| ----------------------- | -------- | ------------- | ------ |---------------------------------------------------- |
| [registry_host]         |          | True          | String | Define a host here to create or use a local registry |
| [all:vars] | webserver_url | True | String | URL of the webserver hosting the qcow images |
| [registry_host:vars] | disconnected_registry_auths_file | True | String | File that contains extra auth tokens to include in the pull-secret. This file will be generated if it doesn't exist. |
| [registry_host:vars] | disconnected_registry_mirrors_file | True | String | File that contains the addition trust bundle and image content sources for the local registry. The contents of this file will be appended to the install-config.yml file. This file will be generated if it doesn't exist. |
| [registry_host:vars] | provision_cache_store | True | String | Folder using for the caching |
| [registry_host:vars] | registry_dir | True | String | Folder where to store the openshift container images |
| [registry_host:vars] | local_registry | True | String | URL of the local registry hosting the openshift container images |
| [registry_host:vars] | local_repo | True | String | Specify the name of the repository to create in your registry, |

## Deploying the registry (Optional)

A playbook exist to deploy the registry and the webserver storing the QCOW images

On the Jumphost:
```
su - dci-openshift-agent
cd samples
ansible-playbook infrastructure.yml
```

### Demo
[![demo](https://asciinema.org/a/vUVI3w23OBqQaM0Ux7IDOlaiq.svg)](https://asciinema.org/a/vUVI3w23OBqQaM0Ux7IDOlaiq?autoplay=1)

## Running dci-openshift-agent
After the configuration and the registry are setup, we can deploy openshift using the dci-openshift-agent:
```
systemctl start dci-openshift-agent
```

### Demo
[![demo](https://asciinema.org/a/qH2Peb2cc9AlJda9DokupUI9Z.svg)](https://asciinema.org/a/qH2Peb2cc9AlJda9DokupUI9Z?autoplay=1)

## License

Apache License, Version 2.0 (see [LICENSE](LICENSE) file)

## Contact

Email: Distributed-CI Team <distributed-ci@redhat.com>
IRC: #distributed-ci on Freenode

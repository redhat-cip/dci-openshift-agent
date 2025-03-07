# Assisted on-prem deprecation

The Assisted Installer's on-premises deployment feature in the DCI Agent has been removed. This feature previously allowed deploying Assisted Installer components within a pod on a local server. Users can continue using the Assisted Installer SaaS through the [Red Hat Hybrid Cloud Console](http://console.redhat.com/). This document outlines the changes, their impact, and steps to adapt your deployments.

This removal represents a breaking change that may significantly impact DCI users. The ABI is the recommended method to continue the deployments and the inventory files are almost compatible.

## What changed

1. Setting `assisted` as the `install_type` is deprecated.
1. The `use_agent_based_installer: true` configuration is deprecated.
1. `boot_iso_url` must now be specified in the inventory.
1. Support for provisioning infrastructure (VMs, networking) in KVM-libvirt environments has been removed.
1. The assisted pod on the bastion host is no longer required.

## Identifying Affected Deployments

Your deployments may be affected if:
1. Jobs fail early with the error: "Assisted on-prem is deprecated."
1. Your cluster inventory includes the following:
    ```yaml
    install_type: assisted
    use_agent_based_installer: false
    ```

# Fixing the Jobs
1. Update the inventory files:
  - Set `install_type: abi` in the inventory files.
  - Remove `use_agent_based_installer: true` from the inventory files
1. Clean up unused pods and containers:
    ```Shell
    $ sudo podman rm http_store -f
    $ sudo podman pod rm http_store_pod -f
    $ sudo podman rm -f assisted-db service next-step-runner assisted-installer
    $ sudo podman pod rm assisted-installer
    ```
1. Add the following variable to the inventory:
    ```yaml
    boot_iso_url: "{{ discovery_iso_server }}:{{ hostvars['http_store']['http_port'] }}/{{ discovery_iso_name }}"`
    ```
1. For KVM-libvirt deployments, provision infrastructure manually or via a playbook like [the one in samples directory](../samples/infrastructure.yml). You can use the `inventory_playbook` variable to customize the target infrastructure using existing settings.

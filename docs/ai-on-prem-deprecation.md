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
1. For KVM-libvirt deployments, provision infrastructure manually or via a playbook like shown below. You can use the `inventory_playbook` variable to customize the target infrastructure using existing settings.

    provision-abi-vms.yml
    ```yaml
    ---
    - name: Process KVM nodes
      hosts: bastion
      tasks:
        - name: Process KVM nodes
          block:
            - name: Process kvm nodes
              ansible.builtin.include_role:
                name: redhatci.ocp.process_kvm_nodes
              when: (setup_vms | default(true))

    - name: Provision VMS
      hosts: vm_hosts
      vars:
        SETUP_VMS: "{{ setup_vms | default((kvm_nodes | default([])) | length | int >= 1) }}"
      tasks:
        - name: Provision VMS
          block:
            - name: Destroy vms
              ansible.builtin.include_role:
                name: redhatci.ocp.destroy_vms
              when: SETUP_VMS | bool
              tags:
                - destroy_vms

            - name: Setup vm host network
              ansible.builtin.include_role:
                name: redhatci.ocp.setup_vm_host_network
              when: (SETUP_VM_BRIDGE | default(SETUP_VMS)) | bool

            - name: Configure firewall for vm_bridge_zone
              when:
                - (SETUP_VM_BRIDGE | default(SETUP_VMS)) | bool
                - vm_bridge_zone is defined
              become: true
              block:
                - name: Move bridge to designated firewall zone
                  community.general.nmcli:
                    conn_name: "{{ vm_bridge_name }}"
                    state: present
                    zone: "{{ vm_bridge_zone }}"

                - name: Create Iptables NAT chain
                  ansible.builtin.iptables:
                    table: nat
                    chain: POSTROUTING
                    source: '{{ machine_network_cidr }}'
                    destination: '! {{ machine_network_cidr }}'
                    jump: MASQUERADE
                    protocol: all
                    comment: Ansible NAT Masquerade

                - name: Manage IPv4 forwarding
                  ansible.posix.sysctl:
                    name: net.ipv4.ip_forward
                    value: '1'
                    state: present
                    reload: true

            - name: Create vms
              vars:
                create_vms_disable_secure_boot: "{{ disable_secure_boot | default(false) | bool }}"
              ansible.builtin.include_role:
                name: redhatci.ocp.create_vms
              when: SETUP_VMS | bool
              tags:
                - setup_vms

    - name: Setup DNS Records
      hosts: dns_host
      gather_facts: "{{ (setup_dns_service | default(true)) | bool }}"
      vars:
        SETUP_DNS_SERVICE: "{{ setup_dns_service | default(true) }}"
        domain: "{{ cluster_name + '.' + base_dns_domain }}"
      tasks:
        - name: Setup DNS Records
          block:
            - name: Insert DNS records
              ansible.builtin.include_role:
                name: redhatci.ocp.insert_dns_records
              when: SETUP_DNS_SERVICE | bool

            - name: Use /etc/hosts
              ansible.builtin.copy:
                content: |
                  # /etc/NetworkManager/dnsmasq.d/02-add-hosts.conf
                  # By default, the plugin does not read from /etc/hosts.
                  # This forces the plugin to slurp in the file.
                  #
                  # If you didn't want to write to the /etc/hosts file.  This could
                  # be pointed to another file.
                  #
                  addn-hosts=/etc/hosts
                dest: /etc/NetworkManager/dnsmasq.d/02-add-hosts.conf
                mode: '0644'
              become: true

            - name: Remove expand-hosts entry
              ansible.builtin.lineinfile:
                path: /etc/NetworkManager/dnsmasq.d/dnsmasq.{{ cluster_name }}.conf
                state: absent
                regexp: ^expand-hosts
              become: true

            - name: "Restart NetworkManager"
              ansible.builtin.service:
                name: NetworkManager
                state: restarted
              become: true

            - name: Validate dns records
              ansible.builtin.include_role:
                name: redhatci.ocp.validate_dns_records

    - name: Setup NTP
      hosts: ntp_host
      gather_facts: "{{ (setup_ntp_service | default(true)) | bool }}"
      vars:
        SETUP_NTP_SERVICE: "{{ setup_ntp_service | default(true)}}"
      tasks:
        - name: Setup NTP
          block:
            - name: Setup NTP
              ansible.builtin.include_role:
                name: redhatci.ocp.setup_ntp
              when: SETUP_NTP_SERVICE | bool

    - name: Deploy sushy tools
      hosts: vm_hosts
      vars:
        SETUP_SUSHY_TOOLS: "{{ setup_sushy_tools | default(setup_vms | default(true)) }}"
      tasks:
        - name: Setup sushy tools
          block:
            - name: Setup sushy tools
              vars:
                fetched_dest: "{{ '~/clusterconfigs' | expanduser }}-{{ cluster_name }}"
              ansible.builtin.include_role:
                name: redhatci.ocp.setup_sushy_tools
              when: SETUP_SUSHY_TOOLS | bool

    - name: Clean-up nodes - Mainly Baremetal use cases
      hosts: bastion
      tasks:
        - name: Clean-up nodes
          block:
            - name: Erase bootloader to prevent old OS to boot
              delegate_to: "{{ item }}"
              ansible.builtin.shell: |
                if grep 'Red Hat Enterprise Linux CoreOS' /etc/os-release; then
                  for disk in /dev/sd?; do
                    dd if=/dev/zero of=$disk bs=512 count=1
                  done
                fi
              when:
                - dci_erase_bootloader_on_disk|default(False)|bool
                - dci_main is not defined or dci_main == 'install'
              with_items: "{{ groups['masters'] + groups['workers'] | default([]) }}"
              ignore_unreachable: true
              ignore_errors: true

            - name: Empty Console log files if present
              ansible.builtin.command: dd if=/dev/null of="{{ item }}"
              with_fileglob:
                - "/var/consoles/{{ cluster }}/{{ cluster }}*"
              when:
                - cluster is defined
              ignore_errors: true
          become: true
    ...
    ```

#!/usr/bin/sh

linchpin --template-data @libvirt_settings.yml -v up libvirt-network libvirt-hosts

ansible-playbook -i inventories/ocp-edge.inventory \
                 -e @libvirt_settings.yml \
                 hooks/ansible/ocp-edge-setup/dev-scripts-vm.yml

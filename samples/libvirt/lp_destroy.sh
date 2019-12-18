#!/usr/bin/sh
virsh_cmd="sudo virsh"

# Remove Snapshots from VM's or linchpin can't undefine the host
# Limit to only VM's starting with the name master- or worker-
for vm in $($virsh_cmd list --all --name| awk '/worker-|master/ {print $1}'); do
    for vm_snap in $($virsh_cmd snapshot-list --name $vm); do
        $virsh_cmd snapshot-delete $vm $vm_snap
    done
done

linchpin --template-data @libvirt_settings.yml -v destroy libvirt-network libvirt-hosts

# OpenShift using virtual machines emulating baremetal

Please refer to Google Doc (dci-openshift-agent-linchpin)

## steps ##

Step 1 : Enable EPEL
- yum install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

Step 2: Upgrade to latest packages
- yum upgrade

Step 3 : Enable passwordless sudo and libvirt group to your login
- echo "admin ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/admin
- usermod --append --groups libvirt admin
- usermod --append --groups qemu admin

Step 4 : Install Linchpin
- install_linchpin.sh

Step 5 : Enable nested virt
- see https://www.linuxtechi.com/enable-nested-virtualization-kvm-centos-7-rhel-7/

Step 6 : Launch linchpin and openshift install
- ./lp_up.sh

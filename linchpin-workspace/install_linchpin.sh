#!/bin/sh

yum install python-netaddr libvirt-python libvirt-daemon-kvm python-lxml python-pip ansible
systemctl start libvirtd
systemctl enable libvirtd
pip install linchpin

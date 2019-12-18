#!/usr/bin/sh

linchpin --template-data @libvirt_settings.yml -v destroy libvirt-network libvirt-hosts

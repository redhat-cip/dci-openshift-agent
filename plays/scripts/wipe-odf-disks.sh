#!/bin/bash
#
# Copyright (C) 2025 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Description: A shell script wipe listed SCSI devices on a node labeled as part of
# and ODF cluster

# It requires connections details for the cluster servers
# The script only works on disks larger than 100GB

#!/bin/bash

set -euo pipefail

oc_path=$(which oc)

SCSI_IDS=("$@")
NODE_LABEL="cluster.ocs.openshift.io/openshift-storage"

if [ ${#SCSI_IDS[@]} -eq 0 ]; then
  echo "Usage: $0 <scsi-id1> <scsi-id2> ..."
  exit 1
fi

echo "Get nodes labeled for OCS"
NODES=$(${oc_path} get nodes -l $NODE_LABEL= -o name | sed 's|node/||')

echo "${NODES}"

if [ -z "$NODES" ]; then
  echo "[!] No OCS nodes found."
  exit 2
fi

for NODE in $NODES; do
  echo ">>> Processing node: $NODE"
  for SCSI_ID in "${SCSI_IDS[@]}"; do
    ${oc_path} debug node/$NODE -- chroot /host bash -c '
      DEVICE_LINK="/dev/disk/by-id/'"$SCSI_ID"'"
      if [[ -L "$DEVICE_LINK" ]]; then
        DEVICE=$(readlink -f "$DEVICE_LINK")
        sgdisk --zap-all $DEVICE
        dd if=/dev/zero of=$DEVICE bs=1 count=204800 seek=0
        dd if=/dev/zero of=$DEVICE bs=1 count=204800 seek=$((1 * 1024**3))
        dd if=/dev/zero of=$DEVICE bs=1 count=204800 seek=$((10 * 1024**3))
        dd if=/dev/zero of=$DEVICE bs=1 count=204800 seek=$((100 * 1024**3))
        blkdiscard $DEVICE
        blockdev --rereadpt $DEVICE
        echo "Wiped $DEVICE ($DEVICE_LINK)"
      fi
    '
  done
done

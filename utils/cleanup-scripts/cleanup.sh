#!/bin/bash
#
# Copyright (C) 2023 Red Hat, Inc.
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

DAYS=3

TOPDIR="$(cd "$(dirname "$0")"/.. || exit 1; pwd)"

exec >> "$HOME"/cleanup.log 2>&1

echo "================================================================================"
date

set -x

find /var/lib/dci-pipeline/*/ -maxdepth 1 -type d -regex '.*/[0-9a-f\-]+[a-f0-9]+' -mtime +$DAYS -print0|xargs -0 rm -rvf
find "$HOME"/.dci-queue/log/*/ -type f -mtime +"$DAYS" -print0|xargs -0 rm -vf

echo ">>> Removing dangling container images from local storage ======================"

buildah rm --prune
buildah rmi --prune

echo ">>> Removing temporary ansible directories ====================================="

find "$HOME"/.ansible/tmp/*/ -type f -mtime +"$DAYS" -print0|xargs -0 rm -vf

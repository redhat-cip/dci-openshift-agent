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

# A shell script to remove dangling containers for the artifacts web server
# Lingering images named with job IDs are also removed
# The Remore CI is used to confirm the Job status
# Params: The path to a valid remote CI

exec >> "$HOME"/containers-cleanup.log 2>&1

function help(){
    echo "$(basename "$0") <remote_ci_path>"
    echo "Absolute path to remote CI is missing"
}

if [[ $# != 1 ]]; then
    echo "Error: Missing remote CI" >&2
    help
    exit 1
fi

echo "================================================================================"
date

# Source the remote CI file
remote_ci="${1}"
if [[ ! -f $remote_ci ]]; then
    echo "Remote CI: ${remote_ci} does not exist, skipping" >&2
    exit 1
fi
source "${remote_ci}"

###
# Cleaning web-artifacts containers
###

# Get the web-container names
containers=$(podman ps -a --sort created --filter 'name=^\w{8}(-\w{4}){3}-\w{12}$' --format "{{.Names}}");

# Loop over the containers and check their job status
while IFS=, read -r name
do
  # Check if the job is in a failure state
  fail_states=( failure error killed )
  job_status=$(dcictl --format json job-show "${name}" | jq -er .job.status)
  if [[ -n "$job_status" && " ${fail_states[*]} " =~ ${job_status} ]]; then
    port=$(podman inspect "${name}" | jq -r '.[].NetworkSettings.Ports."8080/tcp"[0].HostPort')
    sudo firewall-cmd --remove-port="${port}"/tcp
    podman rm -f "${name}"
    echo "Removed container ${name}"
  fi
done <<< "${containers}"

####
# Remove lingering images
####

### Collect information about lingering images
# Get the certsuite images
podman images --sort created --filter 'reference=*/certsuite:*' --format "{{.Repository}}:{{.Tag}}" | grep -E '\w{8}(-\w{4}){3}-\w{12}' > /tmp/clean-images

# Preflight images
podman images --sort created --filter 'reference=*/preflight:*' --format "{{.Repository}}:{{.Tag}}" | grep -E '\w{8}(-\w{4}){3}-\w{12}' >> /tmp/clean-images

# operator-sdk images
podman images --sort created --filter 'reference=*/operator-sdk:*' --format "{{.Repository}}:{{.Tag}}" | grep -E '\w{8}(-\w{4}){3}-\w{12}' >> /tmp/clean-images

# Loop over the images and check their job status
# Remove the image if job is already in failure, error, or killed state
while read -r name
do
  job_id=$(echo "${name##*:}" |  cut -d'-' -f2-)
  # Check if the job is in a failure state
  fail_states=( failure error killed )
  job_status=$(dcictl --format json job-show "${job_id}" | jq -er .job.status)
  if [[ " ${fail_states[*]} " =~ ${job_status} ]]; then
    podman rmi -f "${name}"
    echo "Removed image ${name}"
  fi
done < /tmp/clean-images

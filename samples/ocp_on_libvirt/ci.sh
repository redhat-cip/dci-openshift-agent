#!/bin/bash
#
# Copyright (C) 2021 Red Hat, Inc.
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

set -e

cleanup() {
    ssh-agent -k
}

. /etc/dci-openshift-agent/config

if [ -n "$GERRIT_SSH_ID" ]; then
    eval $(ssh-agent)
    ssh-add ~/.ssh/"$GERRIT_SSH_ID"
    trap cleanup 0
fi

if [ -n "$GERRIT_USER" ]; then
    while :; do
        ssh -p 29418 $GERRIT_USER gerrit stream-events|while read -r data; do
            type=$(jq -r .type <<< $data)
            if [ "$type" = "patchset-created" ]; then
                project=$(jq -r .change.project <<< $data)
                number=$(jq -r .change.number <<< $data)
                subject="$(jq -r .change.subject <<< $data)"
                url="$(jq -r .change.url <<< $data | tr -d '\r' | sed 's/[;|&$]//g')"
                echo "$type $project $number \"$subject\" $url =============================="
                case $project in
                    dci-openshift-agent|dci-ansible|ansible-role-dci-*)
                        dci-check-change $number
                        ;;
                esac
            elif [ "$type" = "comment-added" ]; then
                project=$(jq -r .change.project <<< $data)
                number=$(jq -r .change.number <<< $data)
                comment="$(jq -r .comment <<< $data)"
                url="$(jq -r .change.url <<< $data | tr -d '\r' | sed 's/[;|&$]//g')"
                echo "$type $project $number \"$comment\" $url =============================="
                case $project in
                    dci-openshift-agent|dci-ansible|ansible-role-dci-*)
                        if egrep -qi '^\s*recheck\s*$' <<< "$comment"; then
                            dci-check-change $number                            
                        fi
                        ;;
                esac
            fi
        done
   done
fi

# ci.sh ends here

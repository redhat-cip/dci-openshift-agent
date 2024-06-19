#!/bin/bash
# Get diff between operators available in 2 indexes
# Comparison is based on its defaults channels and the latest bundle version
# Access to index images may require a valid pull secret
# Usage example:
#   DOCKER_CONFIG=/path/to/docker/ ./compare_indexes.sh registry.redhat.io/redhat/redhat-operator-index:v4.15 quay.io/prega/prega-operator-index:v4.16.0

process_index_render() {
  local index_render="${1}"
  local -n package_default_channels_ref=${2}
  local -n channel_entries_ref=${3}

  # Extract package names and default channels
  while IFS="|" read -r package_name default_channel; do
    package_default_channels_ref["${package_name}"]=${default_channel}
  done < <(echo "${index_render}" | jq -r '. | select(.schema == "olm.package") | "\(.name)|\(.defaultChannel)"')

  # Extract latest CSV version for default channel
  while IFS="|" read -r package_name channel_name entries; do
    if [[ "${package_default_channels_ref[${package_name}]}" == "${channel_name}" ]]; then
      latest_version=$(echo "${entries}" | jq -r '.[] | .name' | sort --version-sort | tail -1)
      # shellcheck disable=SC2034
      channel_entries_ref["${package_name}"]=${latest_version}
    fi
  done < <(echo "${index_render}" | jq -r '. | select(.schema == "olm.channel") | "\(.package)|\(.name)|\(.entries)"')
}

### Main

# Check requirements
if [ "$#" -ne 2 ] || [ -z "${DOCKER_CONFIG}" ]; then
    if [ "$#" -ne 2 ]; then
        echo "Error: Two references to operators indexes are required"
    fi
    if [ -z "${DOCKER_CONFIG}" ]; then
        echo "Please set DOCKER_CONFIG to the path of your docker config.json" >&2
    fi
    echo "Usage: DOCKER_CONFIG=/path/to/docker/ $0 index1 index2"
    exit 1
fi

# Render index1 and index2
index1_render=$(opm render "${1}")
index2_render=$(opm render "${2}")

# Initialize arrays for indexes
declare -A package_default_channels_index1
declare -A package_default_channels_index2
declare -A channel_entries_index1
declare -A channel_entries_index2
declare -A index1_versions
declare -A index2_versions

# Process index1 and index2
process_index_render "${index1_render}" package_default_channels_index1 channel_entries_index1
process_index_render "${index2_render}" package_default_channels_index2 channel_entries_index2

# Get versions from index1
for package_name in "${!package_default_channels_index1[@]}"; do
  latest_entry=${channel_entries_index1[$package_name]}
  latest_entry_version=$(echo "${latest_entry}" | cut -d'.' -f2-)
  index1_versions["$package_name"]=${latest_entry_version}
done

# Get versions from index2
for package_name in "${!package_default_channels_index2[@]}"; do
  latest_entry=${channel_entries_index2[${package_name}]}
  latest_entry_version=$(echo "${latest_entry}" | cut -d'.' -f2-)
  index2_versions["${package_name}"]=${latest_entry_version}
done

# Combine the packages/versions
keys=$(echo "${!index1_versions[@]}" "${!index2_versions[@]}" | tr ' ' '\n' | sort | uniq)

# Print report
echo "Compared indexes:"
echo "  Index 1: ${1}"
echo "  Index 2: ${2}"

# Header
h1=$(echo "${1}" | sed -E 's|.*/([^@:]+(:[^@:]+)?)|\1|')
h2=$(echo "${2}" | sed -E 's|.*/([^@:]+(:[^@:]+)?)|\1|')
printf "%-50s %-30s %-30s\n" "NAME" "${h1}" "${h2}"

for package in $keys; do
  version1=${index1_versions[$package]:-N/A}
  version2=${index2_versions[$package]:-N/A}
  printf "%-50s %-30s %-30s\n" "${package}" "${version1}" "${version2}"
done

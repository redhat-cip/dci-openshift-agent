# DCI empty agent

The `dci-empty-agent` is designed for partners who manage the entire OpenShift installation process on their own infrastructure. It provides a lightweight integration point, allowing them to seamlessly connect their existing automation pipelines with Distributed CI by implementing the appropriate hooks.

# Requirements

- podman
- dci-pipeline container
- pipeline file
- hooks folder
- credentials.yml file

The `dci-empty-agent` allows you to execute hook files directly from within the `dci-pipeline` container. To run the empty agent, you need a pipeline description file, a set of Ansible hook files, and a credentials.yml file to authenticate the agent with the DCI system.

You will mount these files inside the container at runtime.

```
hooks/
|- pre-run.yml
|- install.yml
|- post-run.yml
secrets/
|- credentials.yml
pipelines/
|- ocp-4.20-pipeline.yml
```

All hook files are called with the following variables during a pipeline run:

- `job`: The job variable that contains information about the DCI job created when dci-pipeline is launched
- `temporary_job_dir`: A temporary directory that can be used to create files during the execution of your job
- `ocp_component`: The OCP component retrieved from the DCI API

# Pipeline file

Example of `pipelines/ocp-4.20-download.yml` pipeline file:

```yaml
- name: Simple OCP download pipeline
  stage: download
  ansible_playbook: /usr/share/dci-openshift-agent/plays/empty-agent/main.yml
  ansible_cfg: /usr/share/dci-openshift-agent/ansible.cfg
  dci_credentials: /dci-config/secrets/credentials.yml
  topic: OCP-4.20
  components:
    - ocp
```

# Get your credential file

See [create-your-first-remoteci](https://docs.distributed-ci.io/get_started/#create-your-first-remoteci).

Save your authentication file in `~/dci-config/secrets/credentials.yml` file.

# Run dci-pipeline container

Mount the current folder into `/dci-config`

```
podman run --rm --privileged -e LC_ALL=C.UTF-8 \
          -v ${PWD}:/dci-config --workdir /dci-config \
          quay.io/distributedci/dci-pipeline \
          dci-pipeline pipelines/ocp-4.20-download.yml
```

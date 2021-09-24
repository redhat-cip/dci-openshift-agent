# Getting Involved

## Table of Contents

- [Development](#development)
  - [Local dev environment](#local-dev-environment)
  - [Libvirt environment](#libvirt-environment)
- [Continuous Integration](#continuous-integration)
  - [Testing a change](#testing-a-change)
- [Agent troubleshooting](#agent-troubleshooting)
  - [Launching the agent without DCI calls](#launching-the-agent-without-dci-calls)

# Development

## Local dev environment

For dev purposes, it is important to be able to run and test the code directly
on your dev environment without using the package manager.

In order to run the agent without using the RPM package, you need to move the
three configuration files (`settings.yml`, `dcirc.sh` and `hosts`) in the
directory of the git repo.

Then, you need to modify dev-ansible.cfg two variables: `inventory` and
`roles_path` (baremetal_deploy_repo).

Also, in order to install package with the ansible playbook, you need to add
rights to `dci-openshift-agent` user:

```
# cp dci-openshift-agent.sudo /etc/sudoers.d/dci-openshift-agent
```

Finally, you can run the script:

```
# Option -d for dev mode
# Overrides variables with group_vars/dev
% ./dci-openshift-agent-ctl -s -c settings.yml -d -- -e @group_vars/dev
```
## Libvirt environment

Please refer to the [full libvirt documentation](ocp_on_libvirt.md) to setup
your own local libvirt environment

# Continuous integration

## Testing a change

If you want to test a change from a Gerrit review or from a Github PR,
use the `dci-check-change` command. Example:

```console
$ dci-check-change 21136
```

to check https://softwarefactory-project.io/r/#/c/21136/ or from a Github:

```console
$ dci-check-change https://github.com/myorg/config/pull/42
```

Regarding Github, you will need a token to access private repositories
stored in `~/.github_token`.

By convention, the `settings.yml` and `hosts` files are searched in
directories ending in `config`.

You can use `dci-queue` from the `dci-pipeline` package to manage a
queue of changes. To enable it, add the name of the queue into
`/etc/dci-openshift-agent/config`:

```console
DCI_QUEUE=<queue name>
```

If you have multiple prefixes, you can also enable it in
`/etc/dci-openshift-agent/config`:

```console
USE_PREFIX=1
```

# Agent troubleshooting

## Launching the agent without DCI calls

The `dci` tag can be used to skip all DCI calls. You will need to
provide fake `job_id` and `job_info` variables in a `myvars.yml` file
like this:

```YAML
job_id: fake-id
job_info:
  job:
    components:
    - name: 1.0.0
      type: my-component
```

and then call the agent like this:

```console
# su - dci-openshift-agent
$ dci-openshift-agent-ctl -s -- --skip-tags dci -e @myvars.yml
```


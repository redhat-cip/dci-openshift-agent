# Development

## Table of Contents

- [Local dev environment](#local-dev-environment)
- [Libvirt environment](#libvirt-environment)
- [Testing a change](#testing-a-change)
  - [Advanced](#advanced)
    - [Dependencies](#dependencies)
    - [Prefix](#prefix)
    - [Hints](#hints)
- [Continuous integration](#continuous-integration)
- [Launching the agent without DCI calls](#launching-the-agent-without-dci-calls)

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

```console
# cp dci-openshift-agent.sudo /etc/sudoers.d/dci-openshift-agent
```

Finally, you can run the script:

```console
## Option -c to take the settings.yml file placed in the directory of the git repo
## Option -d for dev mode
## Overrides variables with group_vars/dev
$ ./dci-openshift-agent-ctl -s -c settings.yml -d -- -e @group_vars/dev
```

## Libvirt environment

Please refer to the [full libvirt documentation](ocp_on_libvirt.md) to setup
your own local libvirt environment

## Testing a change

If you want to test a change from a Gerrit review or from a GitHub PR,
use the `dci-check-change` command. Example:

```console
dci-check-change 21136
```

to check https://softwarefactory-project.io/r/#/c/21136/ or from a
GitHub PR:

```console
dci-check-change https://github.com/myorg/lab-config/pull/42
```

Regarding Github, you will need a token to access private
repositories. To be configured in `/etc/dci-openshift-agent/config`
like this:

```shell
GITHUB_LOGIN=<login name>
GITHUB_TOKEN=<token>
```

If you want to use `ssh` as the transport method for `git`, you can
also configure which ssh key to use from `~/.ssh/` like this:

```shell
GITHUB_SSH_ID=<ssh key name>
```

The ssh key needs to be without password.

`dci-check-change` will launch a DCI job to perform an OCP
installation using `dci-openshift-agent-ctl` and then launch another
DCI job to run an OCP workload using `dci-openshift-app-agent-ctl` if
`dci-openshift-app-agent-ctl` is present on the system.

You can use `dci-queue` from the `dci-pipeline` package to manage a
queue of changes. To enable it, add the name of the queue into
`/etc/dci-openshift-agent/config`:

```shell
DCI_QUEUE=<queue name>
```

If you have multiple prefixes, you can also enable it in
`/etc/dci-openshift-agent/config`:

```shell
USE_PREFIX=1
```

This way, the resource from `dci-queue` is passed as the prefix for
`dci-openshift-app-agent-ctl`.

### Advanced

#### Dependencies

If the change you want to test has a `Depends-On:` or `Build-Depends:`
field, `dci-check-change` will install the corresponding change and
make sure all the changes are tested together.

#### Prefix

If you want to pass a prefix to the `dci-openshift-agent` use the `-p`
option and if you want to pass a prefix to the
`dci-openshift-app-agent` use the `-p2` option.

Remember that you need to set up `CONFIG_DIR`variable in `/etc/dci-openshift-agent/config`
(and in `/etc/dci-openshift-app-agent/config`, in case you want to use
this feature to run jobs on top of already deployed OCP clusters) to instruct
`dci-check-change` to look for the settings file in the correct path. You should
use different values for `CONFIG_DIR` variables on the config files for each agent
to avoid potential issues with the files used; for example, hosts file in `dci-openshift-agent`
is not the same than the hosts file used in `dci-openshift-app-agent`, and the same for
settings file, so if you use the same `CONFIG_DIR` for both agents, you may find conflicts.

Example of execution using prefixes:

```console
dci-check-change https://github.com/myorg/lab-config/pull/42 -p prefix -p2 app-prefix
```

#### Hints

You can also specify a `Test-Hints:` field in the description of your
change. This will direct `dci-check-change` to test in a specific way:

- `Test-Hints: sno` validate the change in SNO mode.
- `Test-Hints: abi` validate the change in ABI using the agent based installer.
- `Test-Hints: abi-sno` validate the change in ABI-SNO with agent based installer.
- `Test-Hints: libvirt` validate in libvirt mode (3 masters).
- `Test-Hints: no-check` do not run a check (useful in CI mode).
- `Test-Hints: force-check` run a check even if there is no code change (useful in CI mode).

`Test-Upgrade-Hints: yes` can also be used to force an upgrade job after
the installation.

`Test-App-Hints:` can also be used to change the default app to be
used (`control_plane_example`). If `none` is specified in `Test-App-Hints:`,
the configuration is taken from the system.

In case you want to provide extra parameters to the jobs deployed by
`dci-check-change` (OCP installation, OCP upgrade or CNF), you can
rely on different `Args-Hints` arguments, depending on your case:

- `Test-Args-Hints:` can be used to specify extra parameters to
pass to `dci-check-change` when running an OCP installation.

```
Test-Args-Hints: -e dci_topic=OCP-4.10 -e dci_teardown_on_success=false -e {"dci_workarounds":["bug42"]}
```

- `Test-Upgrade-Args-Hints:` can also be used to specify extra
parameters to pass to `dci-check-change` for the OCP upgrade command
line. You can also specify the topics by using
`Test-Upgrade-From-Topic-Hints` and `Test-Upgrade-To-Topic-Hints`.

- `Test-App-Args-Hints:` can also be used to provide extra arguments to
pass to `dci-check-change` for CNFs deployed on top of the OCP cluster.

- `Test-PipelineName: <name>` allows to specify the pipeline name. Else the pipeline name is created from the URL of the change.

Hints need to be activated in the `SUPPORTED_HINTS` variable in
`/etc/dci-openshift-agent/config` like this:

```console
SUPPORTED_HINTS="sno|abi|abi-sno|libvirt|no-check|args|app|app-args|upgrade|upgrade-args|upgrade-from-topic|upgrade-to-topic|pipelinename"
```

#### Testing changes in an already up-and-running cluster

If you want to test a change in an up-and-running cluster, you can
pass the path to the kubeconfig file to `dci-check-change`, so that
it will directly execute `dci-openshift-app-agent` on top of that
cluster, using the change you want to test. Note that the change to be
tested should be related to `dci-openshift-app-agent`.

```console
dci-check-change <change> <path/to/kubeconfig>
```

In this way, the default settings file placed in
`/etc/dci-openshift-app-agent/settings.yml` file would be used.
If you want to customize the execution, make use of the App-Hints explained
in the previous section.

Also, if you want to make use of prefixes to launch specific settings file,
you can do it in the following way (remember that `-p2` is the argument that
allows to select settings files for `dci-openshift-app-agent`).

```console
dci-check-change <change> <path/to/kubeconfig> -p2 prefix
```

## Continuous integration

You can use
`/var/lib/dci-openshift-agent/samples/ocp_on_libvirt/ci.sh` to setup
your own CI system to validate changes.

To do so, you need to set the `GERRIT_SSH_ID` variable to set the ssh
key file to use to read the stream of Gerrit events from
`softwarefactory-project.io`. And `GERRIT_USER` to the Gerrit user to
use.

The `ci.sh` script will then monitor the Gerrit events for new changes
to test with `dci-check-change` and to report results to Gerrit.

For the CI to vote in Gerrit and comment in GitHub, you need to set
the `DO_VOTE` variable in `/etc/dci-openshift-agent/config` like this:

```console
DO_VOTE=1
```

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

## Concerning Ansible extra variables

The dci-check-change command is known to fail if provided with composite (list, dictionary) Ansible extra variables containing blank spaces in their definition. For instance:

```console
# dci-check-change 21136 -e "composite=['foo', 'bar']"
```

Note the blank space after the comma in the list definition.

Instead, the proper way to specify the variable avoids the use of blank spaces:

```console
# dci-check-change 21136 -e "composite=['foo','bar']"
```

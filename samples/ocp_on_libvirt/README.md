# CI

The CI script (ci.sh) gets gerrit events, it tests the change for a new patch or if the keyword *recheck* is used in a comment.

## CI service

### Installation

A systemd service handles the execution of the CI script.

You can install it by the creation of a symbolic link.

```bash
# In this case the repository in cloned in the /var/lib directory
sudo ln -s /var/lib/dci-openshift-agent/samples/ocp_on_libvirt/ci.service /etc/systemd/system/ci.service
```

Note: The symbolic link above creates a service named *ci*, of course you can choose any name you want..

If you are using selinux, don't forget to change the context of the script used by the service.

```bash
semanage fcontext -a -t bin_t /var/lib/dci-openshift-agent/samples/ocp_on_libvirt/ci.sh
restorecon /var/lib/dci-openshift-agent/samples/ocp_on_libvirt/ci.sh
```

### Usage

To obtain the status of the CI:

```bash
sudo systemctl status ci
```

To get the logs, use the journalctl command:

```bash
sudo journalctl -u ci -f
```

### Input/Output

ci service get events from gerrit via SSH, everytime you add a comment in a change request from gerrit
it would evaluate how to handle it. It does this by looking for specific strings, then it uses all this
to produce a command that will continue with the flow to deploy an environment, for instance the command
is `dci-check-change` with some parameters:

- a `recheck` command will produce `dci-check-change $CR-number`
- a `check` command will produce the same, as the recheck
- but if the string `check libvirt` is passed then extra parameters can be used, for instance
  - `check libvirt --sno` will produce `dci-check-change --sno $CR-number` (specially designed to SNO)
  - `check libvirt -e var=value` will produce `dci-check-change $CR-number -e var=value` (intended to pass parameters to ansible)

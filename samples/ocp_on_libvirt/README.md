# CI

The CI script (ci.sh) gets gerrit events, it tests the change for a new patch or if the keyword *recheck* is used in a comment.

## CI service

### Installation

A systemd service handles the execution of the CI script.

You can install it by the creation of a symbolic link.

```
# In this case the repository in cloned in the /var/lib directory
sudo ln -s /var/lib/dci-openshift-agent/samples/ocp_on_libvirt/ci.service /etc/systemd/system/ci.service
```

Note: The symbolic link above creates a service named *ci*, of course you can choose any name you want..

If you are using selinux, don't forget to change the context of the script used by the service.

```
semanage fcontext -a -t bin_t /var/lib/dci-openshift-agent/samples/ocp_on_libvirt/ci.sh
restorecon /var/lib/dci-openshift-agent/samples/ocp_on_libvirt/ci.sh
```

### Usage

To obtain the status of the CI:

```
sudo systemctl status ci
```

To get the logs, use the journalctl command:

```
sudo journalctl -u ci -f
```

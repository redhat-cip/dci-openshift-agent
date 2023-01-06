# Old way to use the dci-openshift-agent

## Jumpbox Configuration

There are three configuration files for `dci-openshift-agent`:
`/etc/dci-openshift-agent/dcirc.sh`, `/etc/dci-openshift-agent/hosts` and
`/etc/dci-openshift-agent/settings.yml`.

#### `/etc/dci-openshift-agent/dcirc.sh`

> NOTE: The default `dcirc.sh` is shipped as `/etc/dci-openshift-agent/dcirc.sh.dist`.

Copy the [recently obtained API credentials](#setting-up-access-to-dci) and
paste it on the Jumpbox to `/etc/dci-openshift-agent/dcirc.sh`.

This file should be edited once and looks similar to this:

```bash
DCI_CS_URL="https://api.distributed-ci.io/"
DCI_CLIENT_ID=remoteci/<remoteci_id>
DCI_API_SECRET=<remoteci_api_secret>
export DCI_CLIENT_ID
export DCI_API_SECRET
export DCI_CS_URL
```

If you need any proxy settings, you can also add them to your `dcirc.sh`:

```bash
http_proxy="<your http proxy>"
https_proxy="<your https proxy>"
no_proxy="<your proxy exception list comma separated>"
export http_proxy
export https_proxy
export no_proxy
```

## Starting the DCI OCP Agent

Now that you have configured the `DCI OpenShift Agent`, you can start the
service.

Please note that the service is a systemd `Type=oneshot`. This means that if
you need to run a DCI job periodically, you have to configure a `systemd timer`
or a `crontab`.

```console
systemctl start dci-openshift-agent
```

If you need to run the `dci-openshift-agent` manually in foreground,
you can use this command line:

```console
# su - dci-openshift-agent
% dci-openshift-agent-ctl -s -- -v
```

### Overloading settings and hooks directories

To allow storing the settings and the hooks in a different directory,
you can set `/etc/dci-openshift-agent/config` like this:

```console
CONFIG_DIR=/var/lib/dci-openshift-agent/config
```

This will allow you to use a version control system for all your settings.

If you want to also store the hooks in the same directory, you have to specify `dci_config_dirs` in your `settings.yml`.
Example:

```YAML
---
dci_topic: OCP-4.11
dci_config_dirs: [ /var/lib/dci-openshift-agent/config ]
```

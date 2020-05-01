# Openshift install on already deployed Openstack

## steps ##

* Edit and Configure the example hosts file for your environment
* Copy hosts file to /etc/dci-openshift-agent
* Configure clouds.yaml ??
* Run the openshift installer Manually first

```bash
# su - dci-openshift-agent
% . /etc/dci-openshift-agent/dcirc.sh
% cd /usr/share/dci-openshift-agent
% ansible-playbook -v dci-openshift-agent.yml
```

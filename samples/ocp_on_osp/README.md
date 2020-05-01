# Openshift install on already deployed Openstack

## steps ##

* Edit and Configure the example hosts file for your environment
* Copy hosts file to /etc/dci-openshift-agent
* Copy pre-run.yml to /etc/dci-openshift-agent/hooks
* Copy ansible.cfg to /usr/share/dci-openshift-agent
* Configure clouds.yaml in /usr/share/dci-openshift-agent
* Run the openshift installer Manually first

```bash
# su - dci-openshift-agent
% . /etc/dci-openshift-agent/dcirc.sh
% cd /usr/share/dci-openshift-agent
% ansible-playbook -v dci-openshift-agent.yml
```

* Assuming this works you can enable the systemd timer to run this job daily or trigger it from your CI system

# DCI Openshift Agent

This is the README of the DCI Openshift agent.

It will schedule a job, run the appropriate installation steps, run tests then
returns results back to DCI API.


# Openshift is installed via openshift-ansible
$ ansible-playbook -i hosts ./openshift-ansible/playbooks/prerequisites.yml
$ ansible-playbook -i hosts ./openshift-ansible/playbooks/deploy_cluster.yml


# DCI cleanup scripts

DCI jobs execution may lead to generate some lingering resources that need to be cleaned up to avoid resources starvation on the servers used to execute the jobs. Those resources could be:

- Dangling images, volumes, containers.
- OCP releases that are not in use.
- Ports.

The following scripts will allow to perform the removal of those resources. It is recommended to schedule its execution in crontab.

Please review the scripts before running them on your environment, this to detect tasks that may not be suitable for your environment.

`cleanup.sh`: The following is a list of actions performed by this script:
1. Removes DCI temporary files and directories.
1. Removes dangling container resources.

`clean-webartifact.sh` The following is a list of actions performed by this script:
1. Remove lingering web server containers used to temporary host nightly releases.
1. Remove the ports opened to allow traffic to the web server containers.

This script requires as parameter the dci-credentials in order to verify the status of the job that generated the containers.

```ShellSession
./clean-webartifact.sh /etc/dci-openshift-agent/<your>_dci_credentials.sh
```

`cleanup.py`: A Python script that will garbage-collect old OCP nightly release artifacts from the `provision_cache_store` path. This one is useful and will run fine only if dci-pipeline or dci-queue are installed.

```ShellSession
./cleanup.py -r <provision_cache_store>
```

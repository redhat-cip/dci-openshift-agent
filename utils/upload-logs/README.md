# Upload logs to a DCI job

Sometimes, it may happen that a DCI job is not able to retrieve a file to be saved in the DCI job's Files section.

Currently, there's a [rescue](https://github.com/redhat-cip/dci-openshift-agent/blob/master/plays/upload-log.yml#L15-L26) section when uploading the logs that saves the file locally in case it's not possible to submit it by the time the DCI job is running. Same applies to [dci-openshift-app-agent](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/plays/upload_logs.yml#L15-L24).

This utility allows users to upload any file to a DCI job that may have not been submitted previously in the job.

For this to work, you need to:

1. Have the following environment variables in your terminal:

- Variables related to your remoteci credentials, i.e. `DCI_CLIENT_ID`, `DCI_API_SECRET` and `DCI_CS_URL`, which can be obtained from your remoteci credentials file in DCI.
- Variables related to the DCI job, identified by `DCI_JOB_ID` variable.
- Variables related to the files to submit, which have to be placed in a directory pointed by a variable called `DCI_LOGS_FOLDER`

2. Run properly the playbook.

Here's an example of execution. Imagine you want to upload the following files:

```
$ pwd
/tmp/upload-logs

# in our case, we've created a file with the env vars we need
$ ls
ansible.cfg env_vars.sh  files  upload-logs.yml

$ ls files/
example-upload-2.yml  example-upload.txt

$ cat files/example-upload.txt
hello from custom playbook

$ cat files/example-upload-2.yml
---
msg: "hello from custom playbook"
...
```

To this [DCI job](https://www.distributed-ci.io/jobs/99317fd3-526a-4fe2-b293-f8697c4c37d2/jobStates?sort=date), whose job ID is 99317fd3-526a-4fe2-b293-f8697c4c37d2.

The variables you need to export are:

```
$ cat env_vars.sh

DCI_CLIENT_ID='remoteci/xxx'
DCI_API_SECRET='yyy'
DCI_CS_URL='https://api.distributed-ci.io/'
export DCI_CLIENT_ID
export DCI_API_SECRET
export DCI_CS_URL

DCI_JOB_ID='99317fd3-526a-4fe2-b293-f8697c4c37d2'
DCI_LOGS_FOLDER='/tmp/upload-logs/files'
export DCI_JOB_ID
export DCI_LOGS_FOLDER

$ source env_vars.sh
```

Then, you're ready to launch the playbook, for example: `$ ansible-playbook -v upload-logs.yml`

In the DCI job commented before, you have these files uploaded: [example-upload-2.yml]https://www.distributed-ci.io/files/cebc4ddc-3f55-4d0a-b67f-c889a4a95939) and [example-upload.txt](https://www.distributed-ci.io/files/1cd50067-3496-4f81-ad6d-896c31a346f7)

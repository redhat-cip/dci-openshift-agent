# DCI Openshift Agent

Please refer to :
https://docs.google.com/document/d/11oWu0BZD-4GVdka3VE_NnmSRvXNT1qND_ZcgYrNG2C8/edit?usp=sharing

## Agent steps ##

Step 1 : State “New job”
- Prepare host: /plays/configure.yml
- Download Openshift: /plays/fetch_bits.yml

Step 2 : State “Pre-run”
- Deploy infrastructure: /hooks/pre-run.yml
- Download installer: /hooks/pre-run-installer.yml

Step 3 : Step “running”
- Launch Openshift installer: /hooks/install-openshift.yml

Step 4 : Step “post-run”
- DCI tests: /plays/openshift-dci-tests.yml
- User specific tests (local tests): /hooks/openshift-user-tests.yml


Exit playbooks:

Teardown: /hooks/teardown.yml
Failure: /plays/failure.yml


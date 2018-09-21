# DCI Openshift Agent

Please refer to Google Doc (dci-openshift-agent)

## Agent steps ##

Step 1 : State “New job”
- Prepare host: /plays/configure.yml
- Download Openshift: /plays/fetch_bits.yml

Step 2 : State “Pre-run”
- Deploy infrastructure: /hooks/pre-run.yml

Step 3 : State “running”
- Download and launch Openshift installer: /hooks/running.yml

Step 4 : State “post-run”
- DCI tests: /plays/dci-tests.yml
- User specific tests (local tests): /hooks/user-tests.yml

Step 5 : State “success”
- Launch success: /hooks/success.yml

Exit playbooks:

Teardown: /hooks/teardown.yml
Failure: /plays/failure.yml


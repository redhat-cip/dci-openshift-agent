#!/usr/bin/sh

PATH=$1:$PATH
NUM_WORKERS=$2

CSRS=$(oc get csr -o go-template='{{range .items}}{{if not .status}}{{.metadata.name}}{{"\n"}}{{end}}{{end}}' | wc -l)
while [ $CSRS -lt $NUM_WORKERS ]; do
	sleep 5
        CSRS=$(oc get csr -o go-template='{{range .items}}{{if not .status}}{{.metadata.name}}{{"\n"}}{{end}}{{end}}' | wc -l)
done

oc get csr -o go-template='{{range .items}}{{if not .status}}{{.metadata.name}}{{"\n"}}{{end}}{{end}}' | xargs oc adm certificate approve

CSRS=$(oc get csr -o go-template='{{range .items}}{{if not .status}}{{.metadata.name}}{{"\n"}}{{end}}{{end}}' | wc -l)
while [ $CSRS -lt $NUM_WORKERS ]; do
	sleep 5
        CSRS=$(oc get csr -o go-template='{{range .items}}{{if not .status}}{{.metadata.name}}{{"\n"}}{{end}}{{end}}' | wc -l)
done

oc get csr -o go-template='{{range .items}}{{if not .status}}{{.metadata.name}}{{"\n"}}{{end}}{{end}}' | xargs oc adm certificate approve

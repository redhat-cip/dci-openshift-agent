# A note on OCP Versions and Artifacts

The OpenShift team cuts 3 different types of releases, all of them available from the download mirrors. However they differ on naming and location:

1. Stable: meant for public consumption and supported by RH
2. Release Candidate: this is for tech preview purposes only
3. Nightly: only for development / QA

Some differences:

* Stable builds are stored in the [main download
  location](https://mirror.openshift.com/pub/openshift-v4/clients/ocp)
* RC and Development/nightly builds are stored in a [different
  location](https://mirror.openshift.com/pub/openshift-v4/clients/ocp-dev-preview)
* Stable and RC builds publish their container images to [this quay
  namespace](https://quay.io/openshift-release-dev/ocp-release)
* Development/nightly builds publish to [this quay
  namespace](https://quay.io/openshift-release-dev/ocp-release-nightly), but it
  is protected and you need your cloud.redhat.com pull secret

Furthermore, the Version field listed in the release.txt fetched from the
mirrors has changed gradually throughout OCP versions, example: for nightly
builds it used to show the version for the goal version (e.g. "4.7.14") even if
the nightly build had the timestamp (e.g. "4.7.14-20220322"). This is not true
anymore and the release.txt Version field shows the full matching version
indicating RC or nightly status.

DCI uses component tags (in this case, an OCP build maps to a component in the
DCI control server) to identify tags, DCI uses `build:ga` (or "general
availability") for stable builds, `build:candidate` for RC builds and
`build:dev` for nightlies.

Here's a table to summarize the changes in URLs across all versions we have
identified:

| Build type    | DCI Tag           | OCP Mirror Base URL                                           | Quay.io Namespace                                 |
|---------------|-------------------|---------------------------------------------------------------|---------------------------------------------------|
| Stable        | `build:ga`        | mirror.openshift.com/pub/openshift-v4/clients/ocp             | quay.io/openshift-release-dev/ocp-release         |
| Candidate     | `build:candidate` | mirror.openshift.com/pub/openshift-v4/clients/ocp-dev-preview | quay.io/openshift-release-dev/ocp-release         |
| Nightly/Dev   | `build:dev`       | mirror.openshift.com/pub/openshift-v4/clients/ocp-dev-preview | quay.io/openshift-release-dev/ocp-release-nightly |

The DCI OCP agent fetches the `release.txt` file from the OCP mirror and then
parses it to figure out the SHA256 for the image to pull from Quay. This way
there is no ambiguity on what image to download.

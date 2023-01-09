# A note on OCP Versions and Artifacts

The OpenShift team cuts 4 different types of releases, all of them available from the download mirrors. However they differ on naming and location:

1. Stable: highest quality release and intended for customer use.
2. Release Candidate: early customer access for staging environments and integration testing.
3. Dev preview: very early customer access for feature assessment and dev environments.
3. Nightly: for inter-op and continuous testing.

Some differences:

* Stable builds are stored in the [main download
  location](https://mirror.openshift.com/pub/openshift-v4/clients/ocp)
* RC and Development/nightly builds are stored in a [different
  location](https://mirror.openshift.com/pub/openshift-v4/clients/ocp-dev-preview)
* Stable and RC builds publish their container images to [this quay
  namespace](https://quay.io/openshift-release-dev/ocp-release)
* Development builds publish to [this quay
  namespace](https://quay.io/openshift-release-dev/ocp-release-nightly), but it
  is protected and you will need to authenticate using your [cloud.redhat.com
  pull
  secret](https://console.redhat.com/openshift/install/metal/user-provisioned).
* Nightly builds published to openshiftapps.com. Accessible only through DCI.

For more information about the available builds, please reference the
[OpenShift Release Types
documentation](https://mirror.openshift.com/pub/openshift-v4/OpenShift_Release_Types.pdf).

DCI uses component tags (in this case, an OCP build maps to a component in the
DCI control server) to identify tags, DCI uses `build:ga` (or "general
availability") for stable builds, `build:candidate` for RC builds and
`build:dev` for dev preview and `build:nightly` for nightlies.

Here's a table to summarize the changes in URLs across all versions we have
identified:

| Build type    | DCI Tag           | OCP Mirror Base URL                                           | Quay.io Namespace                                 |
|---------------|-------------------|---------------------------------------------------------------|---------------------------------------------------|
| Stable        | `build:ga`        | mirror.openshift.com/pub/openshift-v4/clients/ocp             | quay.io/openshift-release-dev/ocp-release         |
| Candidate     | `build:candidate` | mirror.openshift.com/pub/openshift-v4/clients/ocp-dev-preview | quay.io/openshift-release-dev/ocp-release         |
| Dev           | `build:dev`       | mirror.openshift.com/pub/openshift-v4/clients/ocp-dev-preview | quay.io/openshift-release-dev/ocp-release-nightly |
| Nightly       | `build:nightly`   | openshiftapps.com                                             | registry.ci.openshift.org                         |

The DCI OCP agent fetches the `release.txt` file from the OCP mirror and then
parses it to figure out the SHA256 for the image to pull from Quay. This way
there is no ambiguity on what image to download.

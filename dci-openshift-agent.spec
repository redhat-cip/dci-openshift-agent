Name:          dci-openshift-agent
Version:       0.21.0
Release:       1.VERS%{?dist}
Summary:       DCI Openshift Agent
License:       ASL 2.0
URL:           https://github.com/redhat-cip/dci-openshift-agent
BuildArch:     noarch
Source0:       dci-openshift-agent-%{version}.tar.gz

BuildRequires: systemd
BuildRequires:  /usr/bin/pathfix.py
Requires: /usr/bin/sudo
Requires: dci-ansible >= 0.3.1
%if 0%{?rhel} && 0%{?rhel} < 8
Requires: python2-dciclient >= 3.1.0
%else
Requires: python3-dciclient >= 3.1.0
%endif
Requires: dci-pipeline >= 0.7.0
Requires: ansible-role-dci-podman
Requires: ansible-collection-redhatci-ocp >= 0.15.0

%{?systemd_requires}
Requires(pre): shadow-utils

%description
DCI Openshift Agent

%prep
%setup -qc

%build

%install

make install BUILDROOT=%{buildroot} DATADIR=%{_datadir} NAME=%{name} SYSCONFDIR=%{_sysconfdir} BINDIR=%{_bindir} SHAREDSTATEDIR=%{_sharedstatedir} UNITDIR=%{_unitdir}

%pre
getent group dci-openshift-agent >/dev/null || groupadd -r dci-openshift-agent
getent passwd dci-openshift-agent >/dev/null || \
    useradd -m -g dci-openshift-agent -d %{_sharedstatedir}/dci-openshift-agent -s /bin/bash \
            -c "DCI OpenShift Agent service" dci-openshift-agent
exit 0

%post
%systemd_post %{name}.service
%systemd_preun %{name}.timer

%preun
%systemd_preun %{name}.service
%systemd_preun %{name}.timer

%postun
%systemd_postun %{name}.service
%systemd_postun %{name}.timer

%files
%license LICENSE
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/hooks/*.yml
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/settings.yml
%config(noreplace) %{_datadir}/dci-openshift-agent/ansible.cfg
%{_bindir}/dci-openshift-agent-ctl

%{_bindir}/dci-check-change
%{_datadir}/dci-openshift-agent/test-runner

%{_datadir}/dci-openshift-agent/dci-openshift-agent.yml
%{_sysconfdir}/dci-openshift-agent/dcirc.sh.dist

%{_datadir}/dci-openshift-agent/plays/*.yml
%{_datadir}/dci-openshift-agent/plays/scripts/*
%{_datadir}/dci-openshift-agent/action_plugins/*
%{_datadir}/dci-openshift-agent/utils/*
%{_datadir}/dci-openshift-agent/plays/crucible/*
%{_datadir}/dci-openshift-agent/plays/microshift/*
%{_datadir}/dci-openshift-agent/plays/templates/*

%{_datadir}/dci-openshift-agent/group_vars/all

%{_unitdir}/*

%dir %{_sharedstatedir}/dci-openshift-agent
%attr(0755, dci-openshift-agent, dci-openshift-agent) %{_sharedstatedir}/dci-openshift-agent
%{_sysconfdir}/sudoers.d/%{name}

%changelog
* Wed Aug 14 2024 Guillaume Vincent <gvincent@redhat.com> 0.21.0-1
- Add Microshift support

* Wed Aug  7 2024 Tony Garcia <tonyg@redhat.com> 0.20.0-1
- Remove opm-auth util script

* Wed Jul 31 2024 Tony Garcia <tonyg@redhat.com> 0.19.0-1
- Requires redhatci.ocp >= 0.15.0 for mirror_images role changes

* Fri Jul 26 2024 Tony Garcia <tonyg@redhat.com> 0.18.0-1
- Requires redhatci.ocp >= 0.14.0 for efi_boot_mgr

* Fri Jul 26 2024 Ramon Perez <raperez@redhat.com> 0.17.0-1
- Requires redhatci.ocp >= 0.13.0 for k8s_best_practices_certsuite

* Wed Jul 10 2024 Ramon Perez <raperez@redhat.com> 0.16.0-1
- Requires redhatci.ocp >= 0.12.0 for create_vms and setup_sushy_tools roles

* Fri Jun 14 2024 Tony Garcia <tonyg@redhat.com> 0.15.0-1
- Requires redhatci.ocp >= 0.11.0 for mirror_ocp_release

* Wed Jun  5 2024 Tony Garcia <tonyg@redhat.com> 0.14.0-1
- Remove unrequired/unused package ansible-role-dci-sync-registry

* Wed May  1 2024 Beto Rdz <josearod@redhat.com> 0.13.0-1
- Requires ansible-collection-redhatci-ocp >= 0.9.0 for ACM

* Sun Feb 18 2024 Beto Rdz <josearod@redhat.com> 0.12.0-1
- Add templates directory

* Mon Feb 12 2024 Tony Garcia <tonyg@redhat.com> 0.11.0-1
- Move out dependencies to the redhatci.ocp collection

* Wed Jan 17 2024 Frederic Lepied <flepied@redhat.com> 0.10.0-1
- requires dci-pipeline >= 0.7.0 for send_status and send_comment

* Tue Jan  2 2024 Frederic Lepied <flepied@redhat.com> 0.9.0-1
- remove extract-dependencies and send-feedback to use the versions
  from dci-pipeline

* Mon Dec 04 2023 Jorge A Gallegos <jgallego@redhat.com> - 0.8.0-1
- FQCN crucible roles to be pulled from redhatci.ocp collection
- Don't clone the crucible repo anymore

* Mon Oct 16 2023 Jorge A Gallegos <jgallego@redhat.com> - 0.7.0-2
- Depend on a version of collection with the right role names

* Mon Oct 16 2023 Tony Garcia <tonyg@redhat.com> 0.7.0-1
- Remove roles, use collections instead

* Tue Oct 10 2023 Tony Garcia <tonyg@redhat.com> - 0.6.1-1
- Moving baremetal-deploy to use collections

* Mon Oct 09 2023 Jorge A Gallegos <jgallego@redhat.com> - 0.6.0-1
- Adding Red Hat CI OCP collection as a dependency

* Thu Oct  5 2023 Tony Garcia <tonyg@redhat.com> 0.5.12-1
- Renaming of common-roles

* Tue Sep 12 2023 Tony Garcia <tonyg@redhat.com> 0.5.11-1
- Bump version for dependencies used in dci-openshift-app-agent

* Thu Aug 31 2023 Tony Garcia <tonyg@redhat.com> 0.5.10-1
- Bump for changes in utils

* Mon Jul 31 2023 Beto Rdz <josearod@redhat.com> 0.5.9-1
- Add jmespath dependency

* Mon Jul 31 2023 Beto Rdz <josearod@redhat.com> 0.5.8-1
- Bump for changes in common-roles

* Mon May 15 2023 Bill Peck <bpeck@redhat.com> 0.5.7-1
- Move crucible playbooks into crucible directory in the agent

* Fri Apr 28 2023 Frederic Lepied <flepied@redhat.com> 0.5.6-1
- Requires dci-ansible >= 3.1.0 for the new component fields

* Thu Mar 30 2023 Beto Rdz <josearod@redhat.com> 0.5.5-1
- Add utils scripts

* Wed Mar  1 2023 Bill Peck <bpeck@redhat.com> 0.5.4-1
- added requires on ansible-collection-ansible-utils

* Mon Dec  5 2022 Frederic Lepied <flepied@redhat.com> 0.5.3-1
- change internal logic for rpm and git components

* Thu Nov 10 2022 Frederic Lepied <flepied@redhat.com> 0.5.2-1
- bump the requires for python-dciclient to >= 2.6.0 to get dci-diff-jobs

* Wed Sep 28 2022 Frederic Lepied <flepied@redhat.com> 0.5.1-2
- use make install
- removed ansible-role-dci-ocp-imagesideload requires

* Wed Sep 28 2022 Frederic Lepied <flepied@redhat.com> 0.5.1-1
- removed ansible-role-dci-cvp requires

* Thu Mar 24 2022 Frederic Lepied <flepied@redhat.com> 0.5.0-1
- use dci-vault-client

* Wed Mar  9 2022 Frederic Lepied <flepied@redhat.com> 0.4.0-1
- store shared roles in /usr/share/dci/roles

* Fri Jan 28 2022 Tony Garcia <tonyg@redhat.com> 0.3.2-1
- Add LICENSE file

* Wed Apr  7 2021 Frederic Lepied <flepied@redhat.com> 0.3.1-1
- fix packaging of roles (label-nodes was missing)

* Tue Apr  6 2021 Frederic Lepied <flepied@redhat.com> 0.3.0-1
- add ci.sh

* Thu Apr 01 2021 Jorge A Gallegos <jgallego@redhat.com> - 0.2.0-3
- Set ansible.cfg as a config file

* Tue Mar 02 2021 Tony Garcia <tonyg@redhat.com> - 0.2.0-2
- Remove unused template

* Tue Feb 23 2021 Frederic Lepied <flepied@redhat.com> 0.2.0-1
- Add the dci-check-change command

* Thu Jan 21 2021 Bill Peck <bpeck@redhat.com> - 0.1.5-1
- Add dynamic operator mirroring

* Mon Dec 21 2020 Jorge A Gallegos <jgallego@redhat.com> - 0.1.4-1
- Move infrastructure playbook to the samples directory

* Thu Dec 03 2020 Jorge A Gallegos <jgallego@redhat.com> - 0.1.3-1
- Add ansible roles to replace podman setup and image sideload

* Wed Nov 25 2020 Frederic Lepied <flepied@redhat.com> 0.1.2-1
- add a scripts subdir

* Tue Nov 24 2020 Thomas Vassilian <tvassili@redhat.com> - 0.1.1-2
- Add a role to prepare CNF testings
- Add a role to enable performance-profile operator
- Add a role to enable sriov operator

* Sat Oct 31 2020 Jorge A Gallegos <jgallego@redhat.com> - 0.1.1-1
- Add an upgrader playbook

* Mon Oct 26 2020 Thomas Vassilian <tvassili@redhat.com> - 0.1.0-1
- Fail if OCP nodes do not match installer inventory
- Add an optional task to erase bootloader

* Fri Oct 23 2020 Jorge A Gallegos <jgallego@redhat.com> - 0.0.1-8
- Add an infrastructure playbook to setup a local registry
- Add a local-registry-setup role

* Thu Oct 15 2020 Jorge A Gallegos <jgallego@redhat.com> - 0.0.1-7
- Split and rename redhat-tests role

* Wed Oct 14 2020 Jorge A Gallegos <jgallego@redhat.com> - 0.0.1-6
- split image-side-load into a role

* Tue Oct 13 2020 Jorge A Gallegos <jgallego@redhat.com> - 0.0.1-5
- podman-setup is now a role

* Tue Oct 13 2020 Jorge A Gallegos <jgallego@redhat.com> - 0.0.1-4
- oc-setup is now a role

* Wed Aug 26 2020 Jorge A Gallegos <jgallego@redhat.com> - 0.0.1-3
- Unbundled the oc setup from the dci-tests play
- Images are now side-loaded onto the openshift cluster nodes
- Podman is setup on its own playbook

* Tue Jun  2 2020 Haïkel Guémar <hguemar@fedoraproject.org> - 0.0.1-2
- Add RHEL8 support

* Mon Oct 15 2018 Thomas Vassilian <tvassili@redhat.com> - 0.0.1
- Initial release.

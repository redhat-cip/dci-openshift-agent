Name:          dci-openshift-agent
Version:       0.5.10
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
Requires: ansible-role-dci-sync-registry
Requires: ansible-role-dci-podman
Requires: ansible-collection-community-kubernetes
Requires: ansible-collection-containers-podman
Requires: ansible-collection-community-general
Requires: ansible-collection-community-libvirt
Requires: ansible-collection-ansible-posix
Requires: ansible-collection-ansible-utils
Requires: python3-pyyaml python3-openshift
Requires: jq
Requires: git
Requires: python3-netaddr
Requires: python3-jmespath
Requires: skopeo
Requires: podman

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
%{_datadir}/dci-openshift-agent/extract-dependencies
%{_datadir}/dci-openshift-agent/send-feedback
%{_datadir}/dci-openshift-agent/test-runner

%{_datadir}/dci-openshift-agent/dci-openshift-agent.yml
%{_sysconfdir}/dci-openshift-agent/dcirc.sh.dist

%{_datadir}/dci-openshift-agent/plays/*.yml
%{_datadir}/dci-openshift-agent/plays/scripts/*
%{_datadir}/dci-openshift-agent/roles/*
%{_datadir}/dci-openshift-agent/action_plugins/*
%{_datadir}/dci-openshift-agent/utils/*
%{_datadir}/dci-openshift-agent/plays/crucible/*

%{_datadir}/dci-openshift-agent/group_vars/all

%{_datadir}/dci/roles/*

%{_unitdir}/*

%dir %{_sharedstatedir}/dci-openshift-agent
%attr(0755, dci-openshift-agent, dci-openshift-agent) %{_sharedstatedir}/dci-openshift-agent
%{_sysconfdir}/sudoers.d/%{name}

%changelog
* Thu Aug 31 2023 Tony Garcia <tonyg@redhat.com> 0.5.10-1
- Bump for changes in utils

* Thu Jul 31 2023 Beto Rdz <josearod@redhat.com> 0.5.9-1
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

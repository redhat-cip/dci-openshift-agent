Name:          dci-openshift-agent
Version:       0.0.VERS
Release:       3%{?dist}
Summary:       DCI Openshift Agent
License:       ASL 2.0
URL:           https://github.com/redhat-cip/dci-openshift-agent
BuildArch:     noarch
Source0:       dci-openshift-agent-%{version}.tar.gz

BuildRequires: systemd
BuildRequires:  /usr/bin/pathfix.py
Requires: /usr/bin/sudo
Requires: dci-ansible
Requires: ansible-role-dci-import-keys
Requires: ansible-role-dci-retrieve-component
Requires: ansible-role-dci-sync-registry

%{?systemd_requires}
Requires(pre): shadow-utils

%description
DCI Openshift Agent

%prep
%setup -qc

%build

%install
install -p -D -m 644 ansible.cfg %{buildroot}%{_datadir}/dci-openshift-agent/ansible.cfg
install -p -D -m 644 dci-openshift-agent.yml  %{buildroot}%{_datadir}/dci-openshift-agent/dci-openshift-agent.yml
install -p -D -m 644 dcirc.sh.dist %{buildroot}%{_sysconfdir}/dci-openshift-agent/dcirc.sh.dist
install -p -D -m 644 hooks/pre-run.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/pre-run.yml
install -p -D -m 644 hooks/configure.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/configure.yml
install -p -D -m 644 hooks/running.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/running.yml
install -p -D -m 644 hooks/success.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/success.yml
install -p -D -m 644 hooks/user-tests.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/user-tests.yml
install -p -D -m 644 hooks/teardown.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/teardown.yml
install -p -D -m 644 hooks/templates/install-config.yaml.j2 %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/templates/install-config.yaml.j2
install -p -D -m 644 hooks/templates/metal3-config.yaml.j2 %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/templates/metal3-config.yaml.j2
install -p -D -m 644 settings.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/settings.yml

install -p -D -m 644 plays/configure.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/configure.yml
install -p -D -m 644 plays/oc-setup.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/oc-setup.yml
install -p -D -m 644 plays/image-side-load.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/image-side-load.yml
install -p -D -m 644 plays/podman-setup.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/podman-setup.yml
install -p -D -m 644 plays/dci-tests.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/dci-tests.yml
install -p -D -m 644 plays/failure.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/failure.yml
install -p -D -m 644 plays/fetch_bits.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/fetch_bits.yml
install -p -D -m 644 plays/upload_logs.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/upload_logs.yml
install -p -D -m 644 group_vars/all %{buildroot}%{_datadir}/dci-openshift-agent/group_vars/all

install -p -D -m 644 systemd/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
install -p -D -m 644 systemd/%{name}.timer %{buildroot}%{_unitdir}/%{name}.timer

install -p -D -m 440 dci-openshift-agent.sudo %{buildroot}%{_sysconfdir}/sudoers.d/%{name}
install -p -d -m 755 %{buildroot}/%{_sharedstatedir}/%{name}
find samples -type f -exec install -Dm 644 "{}" "%{buildroot}%{_sharedstatedir}/dci-openshift-agent/{}" \;
install -p -D -m 755 dci-openshift-agent-ctl %{buildroot}%{_bindir}/dci-openshift-agent-ctl

%if 0%{?rhel} && 0%{?rhel} < 8
pathfix.py -pni "%{__python2}" %{buildroot}%{_sharedstatedir}/dci-openshift-agent/samples/ocp_on_libvirt/roles/bridge-setup/library/nmcli.py
%else
pathfix.py -pni "%{__python3}" %{buildroot}%{_sharedstatedir}/dci-openshift-agent/samples/ocp_on_libvirt/roles/bridge-setup/library/nmcli.py
%endif

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
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/hooks/pre-run.yml
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/hooks/configure.yml
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/hooks/running.yml
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/hooks/success.yml
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/hooks/teardown.yml
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/hooks/user-tests.yml
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/hooks/templates/install-config.yaml.j2
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/hooks/templates/metal3-config.yaml.j2
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/settings.yml
%{_bindir}/dci-openshift-agent-ctl

%{_datadir}/dci-openshift-agent/ansible.cfg
%{_datadir}/dci-openshift-agent/dci-openshift-agent.yml
%{_sysconfdir}/dci-openshift-agent/dcirc.sh.dist

%{_datadir}/dci-openshift-agent/plays/failure.yml
%{_datadir}/dci-openshift-agent/plays/configure.yml
%{_datadir}/dci-openshift-agent/plays/oc-setup.yml
%{_datadir}/dci-openshift-agent/plays/image-side-load.yml
%{_datadir}/dci-openshift-agent/plays/podman-setup.yml
%{_datadir}/dci-openshift-agent/plays/dci-tests.yml
%{_datadir}/dci-openshift-agent/plays/fetch_bits.yml
%{_datadir}/dci-openshift-agent/plays/upload_logs.yml
%{_datadir}/dci-openshift-agent/group_vars/all

%{_unitdir}/*

%exclude /%{_datadir}/dci-openshift-agent/*.pyc
%exclude /%{_datadir}/dci-openshift-agent/*.pyo

%dir %{_sharedstatedir}/dci-openshift-agent
%attr(0755, dci-openshift-agent, dci-openshift-agent) %{_sharedstatedir}/dci-openshift-agent
%{_sysconfdir}/sudoers.d/%{name}

%changelog
* Wed Aug 26 2020 Jorge A Gallegos <kad@blegh.net> - 0.0.1-3
- Unbundled the oc setup from the dci-tests play
- Images are now side-loaded onto the openshift cluster nodes
- Podman is setup on its own playbook

* Tue Jun  2 2020 Haïkel Guémar <hguemar@fedoraproject.org> - 0.0.1-2
- Add RHEL8 support

* Mon Oct 15 2018 Thomas Vassilian <tvassili@redhat.com> - 0.0.1
- Initial release.

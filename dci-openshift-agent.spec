Name:          dci-openshift-agent
Version:       0.0.VERS
Release:       1%{?dist}
Summary:       DCI Openshift Agent
License:       ASL 2.0
URL:           https://github.com/redhat-cip/dci-openshift-agent
BuildArch:     noarch
Source0:       dci-openshift-agent-%{version}.tar.gz

BuildRequires: systemd
BuildRequires: systemd-units
Requires: sudo
Requires: dci-ansible
Requires: ansible-role-dci-sync-registry
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
DCI Openshift Agent

%prep
%setup -qc

%build

%clean

%install
install -p -D -m 644 ansible.cfg %{buildroot}%{_datadir}/dci-openshift-agent/ansible.cfg
install -p -D -m 644 dci-openshift-agent.yml  %{buildroot}%{_datadir}/dci-openshift-agent/dci-openshift-agent.yml
install -p -D -m 644 hooks/pre-run.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/pre-run.yml
install -p -D -m 644 hooks/running.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/running.yml
install -p -D -m 644 hooks/success.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/success.yml
install -p -D -m 644 hooks/user-tests.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/user-tests.yml
install -p -D -m 644 hooks/teardown.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/hooks/teardown.yml

install -p -D -m 644 plays/configure.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/configure.yml
install -p -D -m 644 plays/dci-tests.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/dci-tests.yml
install -p -D -m 644 plays/failure.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/failure.yml
install -p -D -m 644 plays/fetch_bits.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/fetch_bits.yml
install -p -D -m 644 plays/upload_logs.yml %{buildroot}%{_datadir}/dci-openshift-agent/plays/upload_logs.yml

install -p -D -m 644 settings.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/settings.yml
install -p -D -m 644 systemd/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
install -p -D -m 644 systemd/dci-update.service %{buildroot}%{_unitdir}/dci-update.service


%post
%systemd_post %{name}.service
%systemd_post dci-update.service

%preun
%systemd_preun %{name}.service
%systemd_preun dci-update.service

%postun
%systemd_postun

%files
%{_sysconfdir}/dci-openshift-agent/settings.yml
%{_sysconfdir}/dci-openshift-agent/hooks/pre-run.yml
%{_sysconfdir}/dci-openshift-agent/hooks/running.yml
%{_sysconfdir}/dci-openshift-agent/hooks/success.yml
%{_sysconfdir}/dci-openshift-agent/hooks/teardown.yml
%{_sysconfdir}/dci-openshift-agent/hooks/user-tests.yml

%{_datadir}/dci-openshift-agent/ansible.cfg
%{_datadir}/dci-openshift-agent/dci-openshift-agent.yml

%{_datadir}/dci-openshift-agent/plays/failure.yml
%{_datadir}/dci-openshift-agent/plays/configure.yml
%{_datadir}/dci-openshift-agent/plays/dci-tests.yml
%{_datadir}/dci-openshift-agent/plays/fetch_bits.yml
%{_datadir}/dci-openshift-agent/plays/upload_logs.yml

%{_unitdir}/*

%exclude /%{_datadir}/dci-openshift-agent/*.pyc
%exclude /%{_datadir}/dci-openshift-agent/*.pyo

%changelog
* Mon Oct 15 2018 Thomas Vassilian <tvassili@redhat.com> - 0.0.1
- Initial release.

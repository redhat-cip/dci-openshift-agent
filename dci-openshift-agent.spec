Name:          dci-openshift-agent
Version:       0.0.1
Release:       0.VER%{?dist}
Summary:       DCI Openshift Agent
License:       ASL 2.0
URL:           https://github.com/redhat-cip/dci-openshift-agent
BuildArch:     noarch
Source0:       https://github.com/redhat-cip/dci-openshift-agent/archive/%{version}.tar.gz

BuildRequires: systemd
BuildRequires: systemd-units
Requires: sudo
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
DCI Openshift Agent

%prep

%build

%clean

%install

%post
%systemd_post %{name}.service
%systemd_post dci-update.service
%systemd_post %{name}.timer
%systemd_post dci-update.timer

%preun
%systemd_preun %{name}.service
%systemd_preun dci-update.service
%systemd_preun %{name}.timer
%systemd_preun dci-update.timer

%postun
%systemd_postun

%files

%changelog
* Tue Oct 15 2018 Thomas Vassilian <tvassili@redhat.com> - 0.0.1
- Initial release.

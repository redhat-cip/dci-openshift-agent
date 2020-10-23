Name:          dci-openshift-agent
Version:       0.1.0
Release:       1.VERS%{?dist}
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
Requires: python3-pyyaml python3-openshift

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
install -p -D -m 644 infrastructure.yml %{buildroot}%{_datadir}/dci-openshift-agent/infrastructure.yml
install -p -D -m 644 dcirc.sh.dist %{buildroot}%{_sysconfdir}/dci-openshift-agent/dcirc.sh.dist

for hook in hooks/*.yml; do
    install -p -D -m 644 $hook  %{buildroot}%{_sysconfdir}/dci-openshift-agent/$hook
done

install -p -D -m 644 settings.yml %{buildroot}%{_sysconfdir}/dci-openshift-agent/settings.yml

for play in plays/*.yml; do
    install -p -D -m 644 $play %{buildroot}%{_datadir}/dci-openshift-agent/$play
done

find roles/oc-setup -type f -exec install -v -p -D -m 644 "{}" "%{buildroot}%{_datadir}/dci-openshift-agent/{}" \;
find roles/podman-setup -type f -exec install -v -p -D -m 644 "{}" "%{buildroot}%{_datadir}/dci-openshift-agent/{}" \;
find roles/image-side-load -type f -exec install -v -p -D -m 644 "{}" "%{buildroot}%{_datadir}/dci-openshift-agent/{}" \;
find roles/redhat-tests -type f -exec install -v -p -D -m 644 "{}" "%{buildroot}%{_datadir}/dci-openshift-agent/{}" \;
find roles/local-registry-setup -type f -exec install -v -p -D -m 644 "{}" "%{buildroot}%{_datadir}/dci-openshift-agent/{}" \;

install -p -D -m 644 group_vars/all %{buildroot}%{_datadir}/dci-openshift-agent/group_vars/all
install -p -D -m 644 templates/ssh_config.j2 %{buildroot}%{_datadir}/dci-openshift-agent/templates/ssh_config.j2

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
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/hooks/*.yml
%config(noreplace) %{_sysconfdir}/dci-openshift-agent/settings.yml
%{_bindir}/dci-openshift-agent-ctl

%{_datadir}/dci-openshift-agent/ansible.cfg
%{_datadir}/dci-openshift-agent/dci-openshift-agent.yml
%{_datadir}/dci-openshift-agent/infrastructure.yml
%{_sysconfdir}/dci-openshift-agent/dcirc.sh.dist

%{_datadir}/dci-openshift-agent/plays/*.yml
%{_datadir}/dci-openshift-agent/roles/oc-setup/*
%{_datadir}/dci-openshift-agent/roles/podman-setup/*
%{_datadir}/dci-openshift-agent/roles/image-side-load/*
%{_datadir}/dci-openshift-agent/roles/redhat-tests/*
%{_datadir}/dci-openshift-agent/roles/local-registry-setup/*

%{_datadir}/dci-openshift-agent/group_vars/all
%{_datadir}/dci-openshift-agent/templates/ssh_config.j2

%{_unitdir}/*

%exclude /%{_datadir}/dci-openshift-agent/*.pyc
%exclude /%{_datadir}/dci-openshift-agent/*.pyo

%dir %{_sharedstatedir}/dci-openshift-agent
%attr(0755, dci-openshift-agent, dci-openshift-agent) %{_sharedstatedir}/dci-openshift-agent
%{_sysconfdir}/sudoers.d/%{name}

%changelog
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

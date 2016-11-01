Name:       openshift-fedora-installer
Version:    0.0.1
Release:    1%{?dist}
Summary:    OpenShift Fedora installer with libvirt and vagrant
Group:      Applications/Productivity
License:    GPLv3
URL:        https://github.com/phracek/openshift-fedora-installation
Requires:   vagrant
Requires:   vagrant-libvirt
Requires:   vagrant-libvirt-doc
Requires:   vagrant-libvirt-registration
Requires:   rubygem-ruby-libvirt
Requires:   wget
Requires:   @Virtualization
Requires:   git
Requires:   origin

%description
OpenShift Fedora installer is used for faster deploying and creating Docker images.
Users does not care about installing them OpenShift and vagrant itself.
Origin is automatically deploy and user should only deploy their Docker images.

%prep
%setup -q

%install
mkdir -p %{buildroot}%{_bindir}/%{name}

cp %{_datadir}/vagrant/gems/doc/vagrant-libvirt-0.0.30/polkit/10-vagrant-libvirt-rules \
    /etc/polkit-1/rules.d

%files
%defattr(-,root,root)
%doc README.md
%license LICENSE
%attr(755,root,root) %{_bindir}/openshift_installer


%changelog
* Mon Oct 24 2016 Petr Hracek <phracek@redhat.com> - 0.0.1-1
- initial release

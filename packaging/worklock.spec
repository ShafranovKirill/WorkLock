Name:           worklock
Version:        0.1.1
Release:        1%{?dist}
Summary:        Fullscreen photo curtain for GNOME
License:        MIT
URL:            https://github.com/ShafranovKirill/WorkLock
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python3-devel
Requires:       python3 >= 3.14
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita

%description
A non-security fullscreen photo curtain with a temporary password.

%prep
%autosetup

%build

%install
install -d %{buildroot}%{python3_sitelib}/worklock
install -m 644 worklock/*.py %{buildroot}%{python3_sitelib}/worklock/
install -D -m 755 bin/worklock %{buildroot}%{_bindir}/worklock
install -D -m 644 data/com.github.shafranovkirill.WorkLock.desktop %{buildroot}%{_datadir}/applications/com.github.shafranovkirill.WorkLock.desktop
install -D -m 644 data/com.github.shafranovkirill.WorkLock.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/com.github.shafranovkirill.WorkLock.svg

%files
%license LICENSE
%doc README.md
%{python3_sitelib}/worklock/
%{_bindir}/worklock
%{_datadir}/applications/com.github.shafranovkirill.WorkLock.desktop
%{_datadir}/icons/hicolor/scalable/apps/com.github.shafranovkirill.WorkLock.svg

%changelog
* Tue Nov 24 2026 ShafranovKirill - 0.1.1-1
- Add padding inside password panel

* Tue Nov 24 2026 ShafranovKirill - 0.1.0-1
- Initial Fedora package

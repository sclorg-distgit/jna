%global pkg_name jna
%{?scl:%scl_package %{pkg_name}}
%{?maven_find_provides_and_requires}

Name:           %{?scl_prefix}%{pkg_name}
Version:        3.5.2
Release:        8.15%{?dist}
Summary:        Pure Java access to native libraries
# src/com/sun/jna/WeakIdentityHashMap.java is from apache-cxf project
License:        LGPLv2+ and ASL 2.0
URL:            https://jna.dev.java.net/
Source0:        %{pkg_name}-%{version}.tar.xz
Source1:        package-list
# script used to generate clean tarball without bundled things
Source2:        generate-tarball.sh
# needed for all apache licensed code
Source3:        http://www.apache.org/licenses/LICENSE-2.0
Patch0:         jna-3.5.0-build.patch
# This patch is Fedora-specific for now until we get the huge
# JNI library location mess sorted upstream
Patch1:         jna-3.5.2-loadlibrary.patch
# The X11 tests currently segfault; overall I think the X11 JNA stuff is just a
# Really Bad Idea, for relying on AWT internals, using the X11 API at all,
# and using a complex API like X11 through JNA just increases the potential
# for problems.
Patch2:         jna-3.4.0-tests-headless.patch
# Build using GCJ javadoc
Patch3:         jna-3.5.2-gcj-javadoc.patch
# junit comes from rpm
Patch4:         jna-3.5.2-junit.patch

# We manually require libffi because find-requires doesn't work
# inside jars.
Requires:       %{?scl_prefix_java_common}javapackages-tools
Requires:       libffi
BuildRequires:  %{?scl_prefix_java_common}javapackages-tools
BuildRequires:  libffi-devel
BuildRequires:  %{?scl_prefix_java_common}ant
BuildRequires:  %{?scl_prefix_java_common}ant-junit
BuildRequires:  %{?scl_prefix_java_common}junit
BuildRequires:  libX11-devel
BuildRequires:  libXt-devel

%description
JNA provides Java programs easy access to native shared libraries
(DLLs on Windows) without writing anything but Java code. JNA's
design aims to provide native access in a natural way with a
minimum of effort. No boilerplate or generated code is required.
While some attention is paid to performance, correctness and ease
of use take priority.

%package        javadoc
Summary:        Javadocs for %{pkg_name}
BuildArch:      noarch

%description    javadoc
This package contains the javadocs for %{pkg_name}.

%package        contrib
Summary:        Contrib for %{pkg_name}
Requires:       %{name} = %{version}-%{release}
# contrib/platform/src/com/sun/jna/platform/mac/Carbon.java is LGPLv3
# contrib/x11/src/jnacontrib/x11/api/X11KeySymDef.java is MIT
License:        LGPLv2+ and LGPLv3+ and MIT
BuildArch:      noarch

%description    contrib
This package contains the contributed examples for %{pkg_name}.

%prep
%setup -q -n %{pkg_name}-%{version}
%{?scl:scl enable %{scl} - <<"EOF"}
set -e -x
cp %{SOURCE1} %{SOURCE3} .
%patch0 -p1 -b .build
sed -e 's|@JNIPATH@|%{_libdir}/%{pkg_name}|' %{PATCH1} | patch -p1
%patch2 -p1 -b .tests-headless
chmod -Rf a+rX,u+w,g-w,o-w .
%patch3 -p0 -b .gcj-javadoc
%patch4 -p1 -b .junit

# UnloadTest fail during build since we modify class loading
rm test/com/sun/jna/JNAUnloadTest.java
# current bug: https://jna.dev.java.net/issues/show_bug.cgi?id=155
#rm test/com/sun/jna/DirectTest.java

# all java binaries must be removed from the sources
find . -name '*.class' -delete

# native directory contains empty *jar files so ant doesn't fail
find . -name '*.jar' -not -path '*lib/native/*' -print -delete

# clean LICENSE.txt
sed -i 's/\r//' LICENSE

chmod -c 0644 LICENSE OTHERS CHANGES.md
%{?scl:EOF}


%build
%{?scl:scl enable %{scl} - <<"EOF"}
set -e -x
# We pass -Ddynlink.native which comes from our patch because
# upstream doesn't want to default to dynamic linking.
ant -Dcflags_extra.native="%{optflags}" -Ddynlink.native=true -Dnomixedjar.native=true compile native javadoc jar contrib-jars
#ant -Dcflags_extra.native="%{optflags}" -Ddynlink.native=true -Dnomixedjar.native=true clean dist
# remove compiled contribs
find contrib -name build -exec rm -rf {} \; || :
%{?scl:EOF}

%install
%{?scl:scl enable %{scl} - <<"EOF"}
set -e -x
# jars
install -D -m 644 build*/%{pkg_name}.jar %{buildroot}%{_javadir}/%{pkg_name}.jar
install -d -m 755 %{buildroot}%{_javadir}/%{pkg_name}
find contrib -name '*.jar' -exec cp {} %{buildroot}%{_javadir}/%{pkg_name}/ \;
# NOTE: JNA has highly custom code to look for native jars in this
# directory.  Since this roughly matches the jpackage guidelines,
# we'll leave it unchanged.
install -d -m 755 %{buildroot}%{_libdir}/%{pkg_name}
install -m 755 build*/native/libjnidispatch*.so %{buildroot}%{_libdir}/%{pkg_name}/

# install maven pom file
install -Dm 644 pom-%{pkg_name}.xml %{buildroot}%{_mavenpomdir}/JPP-%{pkg_name}.pom
install -Dm 644 pom-platform.xml %{buildroot}%{_mavenpomdir}/JPP.%{pkg_name}-platform.pom

# ... and maven depmap
%add_maven_depmap JPP-%{pkg_name}.pom %{pkg_name}.jar
%add_maven_depmap JPP.%{pkg_name}-platform.pom -f platform %{pkg_name}/platform.jar

# javadocs
install -p -d -m 755 %{buildroot}%{_javadocdir}/%{name}
cp -a doc/javadoc/* %{buildroot}%{_javadocdir}/%{name}
%{?scl:EOF}


%files -f .mfiles
%doc LICENSE LICENSE-2.0 OTHERS README.md CHANGES.md TODO
%{_libdir}/%{pkg_name}

%files javadoc
%doc LICENSE LICENSE-2.0
%{_javadocdir}/%{name}

%files contrib -f .mfiles-platform
%{_javadir}/%{pkg_name}


%changelog
* Mon Feb 08 2016 Michal Srb <msrb@redhat.com> - 3.5.2-8.15
- Fix BR on maven-local & co.

* Mon Jan 11 2016 Michal Srb <msrb@redhat.com> - 3.5.2-8.14
- maven33 rebuild #2

* Sat Jan 09 2016 Michal Srb <msrb@redhat.com> - 3.5.2-8.13
- maven33 rebuild

* Wed Jun 10 2015 Michal Srb <msrb@redhat.com> - 3.5.2-8.12
- Build for ppc64

* Tue Jan 13 2015 Michael Simacek <msimacek@redhat.com> - 3.5.2-8.11
- Mass rebuild 2015-01-13

* Mon Jan 12 2015 Michael Simacek <msimacek@redhat.com> - 3.5.2-8.10
- BR/R on packages from rh-java-common

* Wed Jan 07 2015 Michal Srb <msrb@redhat.com> - 3.5.2-8.9
- Migrate to .mfiles

* Tue Jan 06 2015 Michael Simacek <msimacek@redhat.com> - 3.5.2-8.8
- Mass rebuild 2015-01-06

* Mon May 26 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.5.2-8.7
- Mass rebuild 2014-05-26

* Wed Feb 19 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.5.2-8.6
- Mass rebuild 2014-02-19

* Tue Feb 18 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.5.2-8.5
- Mass rebuild 2014-02-18

* Tue Feb 18 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.5.2-8.4
- Remove requires on java

* Mon Feb 17 2014 Michal Srb <msrb@redhat.com> - 3.5.2-8.3
- Enable maven30 SCL in prep/build/install scriptlets

* Fri Feb 14 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.5.2-8.2
- SCL-ize package

* Thu Feb 06 2014 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.5.2-8.1
- Rebuild for el6

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 3.5.2-8
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 3.5.2-7
- Mass rebuild 2013-12-27

* Tue Aug 06 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.5.2-6
- Add LGPLv3+ and MIT licenses to contrib subpackage

* Mon Aug 05 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.5.2-5
- Add ASL 2.0 license text

* Fri Aug 02 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.5.2-4
- Clean bundled jars from tarball

* Fri Jul 12 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.5.2-3
- Update to current packaging guidelines

* Fri Jun 28 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.5.2-2
- Fix ant-trax and ant-nodeps BR

* Fri Jun 28 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.5.2-2
- Rebuild to regenerate API documentation
- Resolves: CVE-2013-1571

* Thu Apr 25 2013 Levente Farkas <lfarkas@lfarkas.org> - 3.5.2-1
- Update to 3.5.2

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.5.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.4.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Jun 20 2012 Levente Farkas <lfarkas@lfarkas.org> - 3.4.0-4
- fix #833786 by Mary Ellen Foster

* Wed Mar 14 2012 Juan Hernandez <juan.hernandez@redhat.com> - 3.4.0-3
- Generate correctly the maven dependencies map (#)

* Sun Mar 11 2012 Ville Skyttä <ville.skytta@iki.fi> - 3.4.0-2
- Don't strip binaries too early, build with $RPM_LD_FLAGS (#802020).

* Wed Mar  7 2012 Levente Farkas <lfarkas@lfarkas.org> - 3.4.0-1
- Update to 3.4.0

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.7-13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.7-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Thu Dec  9 2010 Ville Skyttä <ville.skytta@iki.fi> - 3.2.7-11
- Drop dependency on main package from -javadoc.
- Add license to -javadoc, and OTHERS and TODO to main package docs.
- Install javadocs and jars unversioned.
- Fix release-notes.html permissions.
- Make -javadoc and -contrib noarch where available.

* Fri Dec  3 2010 Levente Farkas <lfarkas@lfarkas.org> - 3.2.7-10
- fix pom file name #655810
- disable check everywhere since it seems to always fail in mock

* Fri Nov  5 2010 Dan Horák <dan[at]danny.cz> - 3.2.7-9
- exclude checks on s390(x)

* Tue Oct 12 2010 Levente Farkas <lfarkas@lfarkas.org> - 3.2.7-8
- exclude check on ppc

* Fri Oct  8 2010 Levente Farkas <lfarkas@lfarkas.org> - 3.2.7-7
- fix excludearch condition

* Wed Oct  6 2010 Levente Farkas <lfarkas@lfarkas.org> - 3.2.7-6
- readd excludearch for old release fix #548099

* Fri Oct 01 2010 Dennis Gilmore <dennis@ausil.us> - 3.2.7-5.1
- remove the ExcludeArch it makes no sense

* Sun Aug  1 2010 Levente Farkas <lfarkas@lfarkas.org> - 3.2.7-5
- reenable test and clean up contrib files

* Tue Jul 27 2010 Levente Farkas <lfarkas@lfarkas.org> - 3.2.7-4
- add Obsoletes for jna-examples

* Sat Jul 24 2010 Levente Farkas <lfarkas@lfarkas.org> - 3.2.7-3
- upstream 64bit fixes

* Fri Jul 23 2010 Levente Farkas <lfarkas@lfarkas.org> - 3.2.7-2
- Temporary hack for 64bit build

* Thu Jul 22 2010 Levente Farkas <lfarkas@lfarkas.org> - 3.2.7-1
- Rebase on upstream 3.2.7

* Wed Jul 21 2010 Stanislav Ochotnicky <sochotnicky@redhat.com> - 3.2.4-6
- Add maven depmap

* Thu Apr 22 2010 Colin Walters <walters@verbum.org> - 3.2.4-5
- Add patches to make the build happen with gcj

* Wed Apr 21 2010 Colin Walters <walters@verbum.org> - 3.2.4-4
- Fix the build by removing upstream's hardcoded md5

* Thu Dec 17 2009 Levente Farkas <lfarkas@lfarkas.org> - 3.2.4-3
- add proper ExclusiveArch

* Thu Dec 17 2009 Alexander Kurtakov <akurtako@redhat.com> 3.2.4-2
- Comment rhel ExclusiveArchs - not correct applies on Fedora.

* Sat Nov 14 2009 Levente Farkas <lfarkas@lfarkas.org> - 3.2.4-1
- Rebase on upstream 3.2.4

* Thu Oct 29 2009 Lubomir Rintel <lkundrak@v3.sk> - 3.0.9-6
- Add examples subpackage

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.9-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.9-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Dec 30 2008 Colin Walters <walters@redhat.com> - 3.0.9-3
- Add patch to allow opening current process

* Sun Nov 30 2008 Colin Walters <walters@redhat.com> - 3.0.9-2
- Fix library mapping, remove upstreamed patches

* Fri Oct 31 2008 Colin Walters <walters@redhat.com> - 3.0.9-1
- Rebase on upstream 3.0.9

* Tue Oct 14 2008 Colin Walters <walters@redhat.com> - 3.0.4-10.svn729
- Add patch to support String[] returns

* Wed Oct 01 2008 Colin Walters <walters@redhat.com> - 3.0.4-9.svn729
- Add new patch to support NativeMapped[] which I want

* Wed Oct 01 2008 Colin Walters <walters@redhat.com> - 3.0.4-8.svn729
- Update to svn r729
- drop upstreamed typemapper patch

* Thu Sep 18 2008 Colin Walters <walters@redhat.com> - 3.0.4-7.svn700
- Add patch to make typemapper always accessible
- Add patch to skip cracktastic X11 test bits which currently fail

* Tue Sep 09 2008 Colin Walters <walters@redhat.com> - 3.0.4-5.svn700
- Update to upstream SVN r700; drop all now upstreamed patches

* Sat Sep 06 2008 Colin Walters <walters@redhat.com> - 3.0.4-3.svn630
- A few more patches for JGIR

* Thu Sep 04 2008 Colin Walters <walters@redhat.com> - 3.0.4-2.svn630
- Add two (sent upstream) patches that I need for JGIR

* Thu Jul 31 2008 Colin Walters <walters@redhat.com> - 3.0.4-1.svn630
- New upstream version, drop upstreamed patch parts
- New patch jna-3.0.4-nomixedjar.patch which ensures that we don't
  include the .so in the .jar

* Fri Apr 04 2008 Colin Walters <walters@redhat.com> - 3.0.2-7
- Add patch to use JPackage-compatible JNI library path
- Do build debuginfo package
- Refactor build patch greatly so it's hopefully upstreamable
- Install .so directly to JNI directory, rather than inside jar
- Clean up Requires/BuildRequires (thanks Mamoru Tasaka)

* Sun Mar 30 2008 Conrad Meyer <konrad@tylerc.org> - 3.0.2-6
- -javadocs should be -javadoc.
- %%files section cleaned a bit.

* Mon Mar 17 2008 Conrad Meyer <konrad@tylerc.org> - 3.0.2-5
- -javadocs package should be in group "Documentation".

* Mon Mar 17 2008 Conrad Meyer <konrad@tylerc.org> - 3.0.2-4
- License should be LGPLv2+, not GPLv2+.
- Several minor fixes.
- Fix Requires in javadoc package.

* Sun Mar 16 2008 Conrad Meyer <konrad@tylerc.org> - 3.0.2-3
- Don't use internal libffi.

* Thu Mar 6 2008 Conrad Meyer <konrad@tylerc.org> - 3.0.2-2
- Don't pull in jars from the web.

* Mon Mar 3 2008 Conrad Meyer <konrad@tylerc.org> - 3.0.2-1
- Initial package.

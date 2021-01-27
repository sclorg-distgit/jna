#!/bin/bash
set -e

version=`grep Version: *spec | sed -e 's/Version:\s*\(.*\)/\1/'`


wget https://github.com/java-native-access/jna/archive/${version}.tar.gz -O jna-${version}.tar.gz
rm -rf jna-${version}
tar xf jna-${version}.tar.gz
#mv twall-jna-* jna-${version}
# remove bundled things with unknown licensing
rm -rvf jna-${version}/{dist/*,www,native/libffi}
# jars in lib/native subdir need to be present in tarball so
# that final jar can be built. They can be empty and then have no
# effect on resulting jar. One jar (depending on architecture) will
# be replaced with full content (containing libjnidispatch.so)
for njar in jna-${version}/lib/native/*.jar; do
    rm -v $njar
    touch empty
    jar cf $njar empty
    rm -f empty
done

find jna-${version} -iname '*jar' -size +1b -delete
find jna-${version} -name '*.class' -delete

tar cf jna-${version}-clean.tar jna-${version}
xz -9 jna-${version}-clean.tar

#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version=0.1.1
mkdir -p "$project_root/dist" "$project_root/dist/rpmbuild"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
tar -C "$project_root" --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner \
  --transform "s,^,worklock-$version/," \
  --exclude=.git --exclude=dist --exclude=__pycache__ \
  -cf - LICENSE README.md bin data packaging scripts worklock tests \
  | gzip -n > "$project_root/dist/rpmbuild/SOURCES/worklock-$version.tar.gz"
rpmbuild -ba "$project_root/packaging/worklock.spec" \
  --define "_topdir $project_root/dist/rpmbuild" \
  --define "_sourcedir $project_root/dist/rpmbuild/SOURCES" \
  --define "_rpmdir $project_root/dist/rpmbuild/RPMS" \
  --define "_srcrpmdir $project_root/dist/rpmbuild/SRPMS"
cp "$project_root/dist/rpmbuild/SOURCES/worklock-$version.tar.gz" "$project_root/dist/"
find "$project_root/dist/rpmbuild/RPMS" "$project_root/dist/rpmbuild/SRPMS" -type f -name '*.rpm' -exec cp {} "$project_root/dist/" \;

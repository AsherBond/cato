#!/usr/bin/env bash
set -x

## this script is to be run in a local git repo only

version=$1

if [ "$version" = "" ] ; then
    echo "usage: $0 <version>"
    exit 1
fi

REPO_HOME=`git rev-parse --show-toplevel`

# 'latest' version
git tag -d latest
git push origin :refs/tags/latest

# supplied version
git tag -d $version
git push origin :refs/tags/$version
git pull
echo $version > $REPO_HOME/VERSION

git add $REPO_HOME/VERSION
git commit -m "Bumped Version to [$version]."
git push
git tag -a latest -m "Version $version"
git tag -a $version -m "Version $version"
git push --tags --force

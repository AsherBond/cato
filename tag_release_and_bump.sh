#!/usr/bin/env bash

## this script is to be run in a local git repo only

version=$1

if [ "$version" = "" ] ; then
    echo "usage: $0 <version>"
    exit 1
fi

# 'latest' version
git tag -d latest
git push origin :refs/tags/latest

# supplied version
git tag -d $version
git push origin :refs/tags/$version
git pull
echo $version > VERSION

git add VERSION
git commit -m "Bumped Version to [$version]."
git push
git tag -a latest -m "Version $version"
git tag -a $version -m "Version $version"
git push --tags

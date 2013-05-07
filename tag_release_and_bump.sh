#!/usr/bin/env bash

version=$1

if [ "$version" = "" ] ; then
    echo "usage: $0 <release>"
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
git commit -m "Bumped Version to [$release]."
git push
git tag -a latest -m "Version $version"
git tag -a $version -m "Version $version"
git push --tags

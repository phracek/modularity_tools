#!/usr/bin/env bash

if [[ x"$1" == "x" ]]; then
    echo "Specify project name where you would like to add anyuid"
    exit 1
fi

PROJECT=$1
echo "Checking whether OpenShift is running."
sudo oc status
if [[ $? -ne 0 ]]; then
    echo "OpenShift instance is not running. To run it call `sudo oc cluster up`"
    exit 1
fi

echo "Switching to system:admin"
sudo oc login -u system:admin
if [[ $? -ne 0 ]]; then
    echo "Switching to system account failed."
    exit 1
fi

echo "Adding anyuid into project $1.."
sudo oadm policy add-scc-to-user anyuid system:serviceaccount:$PROJECT:default
if [[ $? -ne 0 ]]; then
    echo "Adding anyuid failed."
    exit 1
fi

echo "Switching back to developer account"
sudo oc login -u developer

exit 0

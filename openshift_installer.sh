#!/usr/bin/env bash

RHEL_CDK_NAME="cdk-2.2.0.zip"
RHEL_CDK_URL="https://access.cdn.redhat.com//content/origin/files/sha256/9c/9cfc3f161a7e801a500699ef5d7b46b33b9183aa093f87033b3ce0dcc22ed8f9/$RHEL_CDK_NAME?_auth_=1477042139_4b1bf5f6a47741ff642fbd1d93920a66"
RHEL_VAGRANT_LIBVIRT_NAME="rhel-cdk-kubernetes-7.2-29.x86_64.vagrant-libvirt.box"
RHEL_VAGRANT_LIBVIRT_BOX="https://access.cdn.redhat.com//content/origin/files/sha256/35/350f2bd505777d9b324e276b9cd95a4e1fffbcad5af2c4ebb0aeccfe3ccee345/$RHEL_VAGRANT_LIBVIRT_NAME?_auth_=1477042139_8da66fd8758eeed650843c986ff00a25"
DOWNLOAD_DIR="$HOME/Downloads"
PWD=$(pwd)
VAGRANT_NAMES="vagrant-registration vagrant-service-manager vagrant-sshfs"
VAGRANT_GEMS="vagrant-registration-1.2.1.gem vagrant-service-manager-1.0.1.gem vagrant-sshfs-1.1.0.gem"


if [[ ! -d "$DOWNLOAD_DIR" ]]; then
    mkdir -p "$DOWNLOAD_DIR"
fi

function check_vagrant_group {
    local USER_NAME=$1
    # check if your username is in group vagrant
    echo "Checking if your username $USER_NAME is in group 'vagrant'"
    VAGRANT_USER=$(grep vagrant /etc/group)
    if [[ $VAGRANT_USER == *"$USER_NAME"* ]]; then
        echo "$USER_NAME is specified in vagrant group"
    else
        echo "$USER_NAME is not specified in vagrant group. Add them via sudo command"
        sudo usermod -a -G vagrant $USER_NAME
    fi
}

function download_RHEL_stuff {
    NAME=$1
    shift
    URL=$2
    if [[ -f "$NAME" ]]; then
        echo "File $NAME already exists"
        return 0
    fi
    wget "$URL" -O "$NAME"
    if [[ $? -ne 0 ]]; then
        return 1
    fi
    return 0
}

function install_vagrant_stuff {
    cd ~/cdk/plugins/
    echo "Installing $VAGRANT_GEMS."
    plugin=""

    for gem in $VAGRANT_NAMES; do
        vagrant plugin list | grep gem
        if [[ $? -ne 0 ]]; then
            echo "$gem does not exist."
            plugin="$plugin $gem"
        fi
    done
    if [[ x"$plugin" != "x$plugin" ]]; then
        vagrant plugin install "$VAGRANT_GEMS"
        echo "List all vagrant plugins."
        vagrant plugin list
    fi
}

function add_vagrant_box {
    echo "Check if Vagrant box already exists."
    vagrant box list | grep cdkv2
    if [[ $? -eq 0 ]]; then
        echo "The Red Hat Enterprise Linux Server box already exists."
        return 0
    fi
    echo "Add the Red Hat Enterprise Linux Server box to Vagrant."
    vagrant box add --name cdkv2 "$DOWNLOAD_DIR/$RHEL_VAGRANT_LIBVIRT_NAME"
    if [[ $? -ne 0 ]]; then
        echo "Adding Red Hat Enterprise Linux Server box to Vagrant failed."
        return 1
    fi
    echo "List all Vagrant boxes."
    vagrant box list
}

function running_openshift {
    echo "Swith to directory RHEL-OSE."
    cd ~/cdk/components/rhel/rhel-ose/
    echo "Starting Vagrant."
    vagrant up
    if [[ $? -ne 0 ]]; then
        echo "Starting vagrant failed."
        return 1
    fi
    vagrant provision

}


function check_running_vagrant {
    local output=$1
    grep -rn 'rhel-ose' $output
    if [[ $? -eq 0 ]]; then
        echo "OpenShift Enterprise is running."
        return 0
    fi
    return 1
}

check_vagrant_group $USER

# check Vagrant environments
echo "Check Vagrant environments"
output=$(vagrant global-status)

if [[ $(check_running_vagrant) -eq 0 ]]; then
    exit 0
fi

download_RHEL_stuff "$RHEL_VAGRANT_LIBVIRT_NAME" "$DOWNLOAD_DIR/$RHEL_VAGRANT_LIBVIRT_BOX" || {
    echo "Downloading $RHEL_VAGRANT_LIBVIRT_NAME failed for unknown reason."
    exit 1
}

cd $HOME
if [[ ! -d "$HOME/cdk" ]]; then
    unzip "$DOWNLOAD_DIR/$RHEL_CDK_URL"
fi
# download RHEL_CDK
echo "Downloading RHEL_CDK"
if [[ ! -d "$HOME/cdk" ]]; then
    download_RHEL_stuff "$RHEL_CDK_NAME" "$DOWNLOAD_DIR/$RHEL_CDK_URL" || {
        echo "Downloading $RHEL_CDK_NAME failed for unknown reason."
        exit 1
    }
fi

install_vagrant_stuff || {
    echo "Installing $VAGRANT_GEMS failed."
    exit 1
}

add_vagrant_box || {
    echo "Adding Vagrant box $RHEL_VAGRANT_LIBVIRT_NAME failed."
    exit 1
}

running_openshift || {
    echo "Running OpenShift failed."
    exit 1
}

cd $PWD
exit 0
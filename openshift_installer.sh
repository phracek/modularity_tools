#!/usr/bin/env bash

DOWNLOAD_DIR="$HOME/Downloads"


if [[ ! -d "$DOWNLOAD_DIR" ]]; then
    mkdir -p "$DOWNLOAD_DIR"
fi


function install_RHEL_docker_pkgs {
    grep 'Fedora' /etc/redhat-release
    if [[ $? -eq 0 ]]; then
        echo "The script is used for setting OpenShift and Docker on Red Hat Enterprise Linux systems."
        exit 1
    fi
    PKGS_TO_INSTALL="docker-distribution docker-client docker-common docker-registry docker"
    for pkg in $PKGS_TO_INSTALL; do
        rpm -q $pkg
        if [[ $? -ne 0 ]]; then
            echo "Package $pkg is not installed. Installing..."
            yum install -y $pkg --nogpgcheck
            if [[ $? -ne 0 ]]; then
                echo "Package installation failed."
                return 1
            fi
        fi
    done
}

function get_openshift {
    server_name="openshift-origin-server-v1.3.3-bc17c1527938fa03b719e1a117d584442e3727b8-linux-64bit"
    server_tarball="$server_name.tar.gz"
    name="openshift-server.tar.gz"
    if [[ -f "$name" ]]; then
        echo "OpenShift tarball already exists. Skipping."
    else
        echo "Donwloading tarball $server_tarball."
        wget https://github.com/openshift/origin/releases/download/v1.3.3/$server_tarball -O $name
        if [[ $? -ne 0 ]]; then
            echo "Downloading failed."
        fi
    fi
    if [[ -d "./$server_name" ]]; then
        echo "OpenShift dir already exists. Skipping with extraction."
    else
        echo "Extracting $name."
        tar -xzvf "$name"
        if [[ $? -ne 0 ]]; then
            echo "Extracting failed."
            exit 1
        fi
    fi
}

function starting_docker_service {
    echo "Reloading daemon."
    systemctl daemon-reload
    echo "Enabling docker."
    systemctl enable docker
    echo "Restarting docker."
    systemctl restart docker
}

function running_openshift {
    echo 'Running OpenShift via `oc cluster up`'
    sudo oc cluster up
    if [[ $? -ne 0 ]]; then
        echo "Starting OpenShift with oc cluster up failed. See an output."
        echo "In most cases it seems like OpenShift can not communicate with docker."
        echo "Try to set /etc/sysconfig/docker properly. Especially INSECURE_REGISTRY value."
        return 1
    fi
}

PWD=$(pwd)
cd $HOME

install_RHEL_docker_pkgs || {
    echo "Installing docker pkgs failed."
    echo "Check whether you have enabled proper repositories and try again."
    exit 1
}

get_openshift || {
    echo "Downloading OpenShift released version failed."
    exit 1
}

starting_docker_service

running_openshift || {
    echo "Running OpenShift failed."
    exit 1
}

cd $PWD
echo "System is prepared for starting OpenShift and Docker."
exit 0
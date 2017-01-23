# openshift-fedora-installation
The repo provides a set of scripts for faster installation OpenShift on Fedora / RHEL systems

* build_oc_template.py ... script which generates openshift template for ease usage.
    * Dockerfile in your directory has to exist
    * openshift-template.yml ... can be taken from https://github.com/container-images/container-image-template/blob/master/openshift-template.yml
    * required parameter is your built docker image. See `docker images`
* get_oc_registry ... script takes a internal OpenShift docker registry IP address and store it to ~/.config/openshift_ip.ini
* openshift_rhel_installer.sh ... script downloads an OpenShift tarball (1.3.3) and copy binaries to /usr/bin folder.
* add_anyuid_to_project.sh ... script add anyuid policy to your project
    * OpenShift command is: ''oadm policy add-scc-to-user anyuid system:serviceaccount:$PROJECT:default'''

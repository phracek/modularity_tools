#!/bin/python

from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import ast
import yaml
import argparse

from dockerfile_parse import DockerfileParser

# Dockerfile path
DOCKERFILE = "Dockerfile"

# OpenShift template
OPENSHIFT_TEMPLATE = "openshift-template.yml"


class OpenShiftTemplateGenerator(object):
    """
    Class generates an OpenShift template
    It requires openshift-template.yml file.
    """

    docker_file = None
    oc_template = None

    def __init__(self, args=None):
        self.dir = os.getcwd()
        self.docker_image = args.image

    def _get_files(self):
        for f in os.listdir(self.dir):
            if os.path.isdir(os.path.join(self.dir, f)):
                continue
            file_name = os.path.join(self.dir, f)
            if f == DOCKERFILE:
                self.docker_file = file_name
            if f == OPENSHIFT_TEMPLATE:
                self.oc_template = file_name

    def _get_expose_and_volumes(self):
        dfp = DockerfileParser(path=self.dir)
        ports = []
        volumes = []
        env = []
        INST = "instruction"
        VALUE = "value"
        for struct in dfp.structure:
            if struct[INST] == "ENV":
                env.append(struct[VALUE])
            elif struct[INST] == "EXPOSE":
                ports.extend(struct[VALUE].split())
            elif struct[INST] == "VOLUME":
                volumes.extend(ast.literal_eval(struct[VALUE]))
        return ports, volumes, env

    def _load_oc_template(self, ports, volumes, env):
        templ = {}
        import pprint
        with open(self.oc_template, 'r') as f:
            try:
                templ = yaml.load(f)
            except yaml.YAMLError as exc:
                print(exc)
        pprint.pprint(templ)
        templ['metadata']['name'] = self.docker_image
        for obj in templ['objects']:
            obj['spec']['dockerImageRepository'] = self.docker_image
            obj['metadata']['name'] = self.docker_image
            ports_list = []
            for p in ports:
                ports_list.append({'containerPort': int(p)})
            volume_list = []
            volume_names = []
            if volumes:
                for p in volumes:
                    volume_list.append({'mountPath': p,
                                        'name': 'name_' + os.path.basename(p)})
                    volume_names.append({'name': 'name_' + os.path.basename(p),
                                         'emptyDir': {}
                                         })
            if 'template' in obj['spec']:
                obj['spec']['template']['metadata']['labels']['name'] = self.docker_image
                containers = obj['spec']['template']['spec']['containers'][0]
                if ports_list:
                    containers['ports'] = ports_list
                if volume_list:
                    containers['volumeMounts'] = volume_list
                    obj['spec']['template']['spec']['volumes'] = volume_names
                containers['name'] = self.docker_image
                containers['image'] = self.docker_image


            if 'triggers' in obj['spec']:
                for trig in obj['spec']['triggers']:
                    trig['imageChangeParams']['containerNames'] = [self.docker_image]
                    trig['imageChangeParams']['from']['name'] = self.docker_image


        #pprint.pprint(templ)
        with open(self.oc_template + "_tmp", 'w') as f:
            try:
                yaml.dump(templ, f, default_flow_style=False)
            except yaml.YAMLError as exc:
                print(exc)

    def run(self):
        self._get_files()
        ports, volumes, env = self._get_expose_and_volumes()
        self._load_oc_template(ports, volumes, env)


def main():
    parser = argparse.ArgumentParser(description="Creates an openshift template YAML file.")
    parser.add_argument(
        "image",
        metavar='IMAGE',
        help="docker image name",
    )
    args = parser.parse_args()
    otg = OpenShiftTemplateGenerator(args)
    otg.run()


if __name__ == "__main__":
    sys.exit(main())

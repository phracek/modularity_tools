#!/bin/python

from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import ast
import yaml
import argparse
import tempfile
import shutil
import re

from dockerfile_parse import DockerfileParser

# Dockerfile path
DOCKERFILE = "Dockerfile"

EXPOSE = "EXPOSE"
VOLUME = "VOLUME"
LABEL = "LABEL"
ENV = "ENV"

# OpenShift template
OPENSHIFT_TEMPLATE = "openshift-template.yml"


def get_string(value):
    return ast.literal_eval(value)


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
        if args.dockerfile is None:
            self.dockerfile = 'Dockerfile'
        else:
            self.dockerfile = os.path.join(self.dir, args.dockerfile)

    def _get_files(self):
        if not os.path.exists(self.dockerfile):
            print("Dockerfile %s does not exists." % self.dockerfile)
            return
        for f in os.listdir(self.dir):
            if os.path.isdir(os.path.join(self.dir, f)):
                continue
            file_name = os.path.join(self.dir, f)
            if f == OPENSHIFT_TEMPLATE:
                self.oc_template = file_name

    def _get_expose(self, value):
        return value.split()

    def _get_env(self, value):
        return value.split(" ")

    def _get_volume(self, value):
        return get_string(value)

    def _get_labels(self, value):
        labels = re.sub('\s\s+', ';', value).split(';')
        label_dict = {l.split('=')[0]: l.split('=')[1] for l in labels}
        return label_dict

    def _get_docker_tags(self):
        tmp_dir = tempfile.mkdtemp()
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir)
        shutil.copyfile(self.dockerfile, os.path.join(tmp_dir, "Dockerfile"))
        dfp = DockerfileParser(path=tmp_dir)
        docker_dict = {}
        inst = "instruction"
        allowed_tags = [ENV, EXPOSE, VOLUME, LABEL]
        functions = {ENV: self._get_env,
                     EXPOSE: self._get_expose,
                     VOLUME: self._get_volume,
                     LABEL: self._get_labels}

        for struct in dfp.structure:
            key = struct[inst]
            val = struct["value"]
            if key in allowed_tags:
                if key == LABEL:
                    if key not in docker_dict:
                        docker_dict[key] = {}
                    docker_dict[key].update(functions[key](val))
                else:
                    if key not in docker_dict:
                        docker_dict[key] = []
                    docker_dict[key].extend(functions[key](val))

        shutil.rmtree(tmp_dir)
        return docker_dict

    def _load_oc_template(self, docker_dict):
        templ = {}
        with open(self.oc_template, 'r') as f:
            try:
                templ = yaml.load(f)
            except yaml.YAMLError as exc:
                print(exc)
                return
        labels = templ['metadata']['annotation']
        try:
            labels['description'] = docker_dict[LABEL]['description']
            labels['tags'] = docker_dict[LABEL]['io.openshift.tags']
        except KeyError:
            labels['description'] = "EMPTY_DESCRIPTION"
            labels['tags'] = 'EMPTY_TAGS'
        labels['template'] = self.docker_image
        templ['metadata']['name'] = self.docker_image
        for obj in templ['objects']:
            obj['spec']['dockerImageRepository'] = self.docker_image
            obj['metadata']['name'] = self.docker_image
            ports_list = []
            for p in docker_dict[EXPOSE]:
                ports_list.append({'containerPort': int(p)})
            volume_list = []
            volume_names = []
            env_list = []
            if docker_dict[VOLUME]:
                for p in docker_dict[VOLUME]:
                    volume_list.append({'mountPath': p,
                                        'name': 'name-' + os.path.basename(p)})
                    volume_names.append({'name': 'name-' + os.path.basename(p),
                                         'emptyDir': {}
                                         })
            if docker_dict[ENV]:
                for e in docker_dict[ENV]:
                    key, val = e.split('=')
                    env_list.append({'name': key,
                                     'value': val})
            if 'template' in obj['spec']:
                obj['spec']['template']['metadata']['labels']['name'] = self.docker_image
                containers = obj['spec']['template']['spec']['containers'][0]
                if env_list:
                    containers['env'] = env_list
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
                    trig['imageChangeParams']['from']['name'] = self.docker_image + ":latest"

        tmp_dir = tempfile.mkdtemp()
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir)
        tmp_file = os.path.join(tmp_dir, os.path.basename(self.oc_template))
        with open(tmp_file, 'w') as f:
            try:
                yaml.safe_dump(templ, f, default_flow_style=False)
                print("OpenShift template is generated here: %s" % (tmp_file))
            except yaml.YAMLError as exc:
                print(exc)

    def run(self):
        self._get_files()
        docker_dict = self._get_docker_tags()
        self._load_oc_template(docker_dict)


def main():
    parser = argparse.ArgumentParser(description="Creates an OpenShift template YAML file.")
    parser.add_argument(
        "image",
        metavar='IMAGE',
        help="docker image name",
    )
    parser.add_argument(
        "--dockerfile",
        help="Specify Dockerfile name. Default is Dockerfile."
    )
    args = parser.parse_args()
    otg = OpenShiftTemplateGenerator(args)
    otg.run()


if __name__ == "__main__":
    sys.exit(main())

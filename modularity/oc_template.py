from __future__ import absolute_import
from __future__ import print_function

import os
import ast
import yaml
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
    docker_dict = {}

    def __init__(self, args=None, dir_name=None):
        if dir_name is None:
            self.dir = os.getcwd()
        else:
            self.dir = dir_name
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

    def _get_label(self, value):
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
        inst = "instruction"
        allowed_tags = [ENV, EXPOSE, VOLUME, LABEL]
        functions = {ENV: self._get_env,
                     EXPOSE: self._get_expose,
                     VOLUME: self._get_volume,
                     LABEL: self._get_label}

        for struct in dfp.structure:
            key = struct[inst]
            val = struct["value"]
            if key in allowed_tags:
                if key == LABEL:
                    if key not in self.docker_dict:
                        self.docker_dict[key] = {}
                    self.docker_dict[key].update(functions[key](val))
                else:
                    if key not in self.docker_dict:
                        self.docker_dict[key] = []
                    ret_val = functions[key](val)
                    for v in ret_val:
                        if v not in self.docker_dict[key]:
                            self.docker_dict[key].append(v)

        shutil.rmtree(tmp_dir)

    def _load_oc_template(self):
        with open(self.oc_template, 'r') as f:
            try:
                templ = yaml.load(f)
            except yaml.YAMLError as exc:
                print(exc)
                return
        return templ

    def _get_labels(self, templ):
        try:
            labels = templ['metadata']['annotation']
        except KeyError:
            labels = {}
        try:
            labels['description'] = self.docker_dict[LABEL]['description']
            labels['tags'] = self.docker_dict[LABEL]['io.openshift.tags']
        except KeyError:
            labels['description'] = "EMPTY_DESCRIPTION"
            labels['tags'] = 'EMPTY_TAGS'
        labels['template'] = self.docker_image
        return labels

    def _get_docker_volumes(self):
        volume_list = []
        volume_names = []
        if 'VOLUME' in self.docker_dict and self.docker_dict[VOLUME]:
            for p in self.docker_dict[VOLUME]:
                volume_list.append({'mountPath': p,
                                    'name': 'name' + p.replace('/', '-')})
                volume_names.append({'name': 'name' + p.replace('/', '-'),
                                     'emptyDir': {}
                                     })
        return volume_list, volume_names

    def _get_docker_env(self):
        env_list = []
        if 'ENV' in self.docker_dict and self.docker_dict[ENV]:
            for e in self.docker_dict[ENV]:
                key, val = e.split('=')
                env_list.append({'name': key,
                                 'value': val})
        return env_list

    def _get_docker_expose(self):
        ports_list = []

        for p in self.docker_dict[EXPOSE]:
            ports_list.append({'containerPort': int(p)})
        return ports_list

    def write_oc_template(self, templ):
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

    def generate_oc_template(self):
        templ = self._load_oc_template()

        if self.docker_dict:
            labels = self._get_labels(templ)
            volume_list, volume_names = self._get_docker_volumes()
            env_list = self._get_docker_env()
            ports_list = self._get_docker_expose()
        templ['metadata']['name'] = self.docker_image
        templ['metadata']['annotation'] = labels
        for obj in templ['objects']:
            obj['spec']['dockerImageRepository'] = self.docker_image
            obj['metadata']['name'] = self.docker_image
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

        return templ

    def run(self):
        self._get_files()
        self._get_docker_tags()
        tmpl = self._load_oc_template(self.docker_dict)
        self.write_oc_template(tmpl)



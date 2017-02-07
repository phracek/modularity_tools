# - *- coding: utf-8 -*-


import pytest
import tempfile
import shutil
import os
import six

from modularity.cli import CLI
from modularity.oc_template import OpenShiftTemplateGenerator
from modularity.oc_template import VOLUME, ENV, EXPOSE, LABEL


class TestOCTemplate(object):
    ostg = None
    WORKING_DIR = ''
    TESTS_DIR = os.path.dirname(__file__)
    docker_tags = {}

    def setup(self):
        self.WORKING_DIR = tempfile.mkdtemp(prefix="ostg-")
        arguments = ['--dockerfile', 'Dockerfile', 'docker_image']
        cli = CLI(arguments)
        self.ostg = OpenShiftTemplateGenerator(cli, self.WORKING_DIR)
        for f in ['Dockerfile', 'openshift-template.yml']:
            shutil.copy(os.path.join(os.path.dirname(__file__),
                                     'files',
                                     f),
                        self.WORKING_DIR)
        os.chdir(self.WORKING_DIR)
        self.ostg._get_files()
        self.docker_tags = self.ostg._get_docker_tags()

    def teardown(self):
        os.chdir(self.TESTS_DIR)
        shutil.rmtree(self.WORKING_DIR)

    def test_oc_check_docker_tags(self):
        expected_tags = {VOLUME: ['/var/log', '/var/spool/log', '/var/spool/mail'],
                         EXPOSE: ['1234', '2345', '6789'],
                         LABEL: {u'io.k8s.description': '"IO_K8S_DESCRIPTION."',
                                 'version': '"1.0"',
                                 'description': '"DESCRIPTION."',
                                 'io.openshift.expose-services': '"1234:EXPOSE_SERVICES"',
                                 'io.k8s.display-name': '"IO_K8S_DISPLAY_NAME."',
                                 'io.openshift.tags': '"TAGS"',
                                 'summary': '"Testing Summary."'}}
        for key, value in six.iteritems(self.ostg.docker_dict):
            if key in expected_tags:
                assert value == expected_tags[key]

    def test_oc_template_generation(self):
        tmpl = self.ostg._load_oc_template()
        assert True

    def test_docker_volumes(self):
        expected_volume_list = [{'mountPath': '/var/log', 'name': 'name-var-log'},
                                {'mountPath': '/var/spool/log', 'name': 'name-var-spool-log'},
                                {'mountPath': '/var/spool/mail', 'name': 'name-var-spool-mail'}]
        expected_volume_names = [{'emptyDir': {}, 'name': 'name-var-log'},
                                 {'emptyDir': {}, 'name': 'name-var-spool-log'},
                                 {'emptyDir': {}, 'name': 'name-var-spool-mail'}]
        volume_list, volume_names = self.ostg._get_docker_volumes()
        assert volume_list == expected_volume_list
        assert volume_names == expected_volume_names

    def test_docker_env(self):
        expected_env_list = [{'name': 'POSTFIX_SMTP_PORT', 'value': '10025'}]
        env_list = self.ostg._get_docker_env()
        assert env_list == expected_env_list

    def test_docker_expose(self):
        expected_expose_list = [{'containerPort': 1234},
                                {'containerPort': 2345},
                                {'containerPort': 6789}]
        expose_list = self.ostg._get_docker_expose()
        assert expose_list == expected_expose_list

    def test_generate_oc(self):
        expected_tmpl = {'apiVersion': 'v1',
                         'kind': 'Template',
                         'labels': {'description': None, 'tags': None, 'template': None},
                         'metadata': {'annotation': {'description': u'"DESCRIPTION."',
                                      'tags': u'"TAGS"',
                                      'template': 'docker_image'},
                                      'name': 'docker_image'},
                         'objects': [{'apiVersion': 'v1',
                                      'kind': 'ImageStream',
                                      'metadata': {'name': 'docker_image'},
                                      'spec': {'dockerImageRepository': 'docker_image'},
                                      'tags': [{'name': 'latest'}]},
                                     {'apiVersion': 'v1',
                                      'kind': 'DeploymentConfig',
                                      'metadata': {'name': 'docker_image'},
                                      'spec': {'dockerImageRepository': 'docker_image',
                                               'replicas': 1,
                                               'strategy': {'type': 'Rolling'},
                                               'template': {'metadata': {'labels': {'name': 'docker_image'}},
                                                            'spec': {'containers': [{'env': [{'name': u'POSTFIX_SMTP_PORT',
                                                                                              'value': u'10025'}],
                                                                                     'image': 'docker_image',
                                                                                     'imagePullPolicy': 'Never',
                                                                                     'name': 'docker_image',
                                                                                     'ports': [{'containerPort': 1234},
                                                                                               {'containerPort': 2345},
                                                                                               {'containerPort': 6789}],
                                                                                     'volumeMounts': [{'mountPath': '/var/log',
                                                                                                       'name': 'name-var-log'},
                                                                                                      {'mountPath': '/var/spool/log',
                                                                                                       'name': 'name-var-spool-log'},
                                                                                                      {'mountPath': '/var/spool/mail',
                                                                                                       'name': 'name-var-spool-mail'}]}],
                                                                     'volumes': [{'emptyDir': {},
                                                                                  'name': 'name-var-log'},
                                                                                 {'emptyDir': {},
                                                                                  'name': 'name-var-spool-log'},
                                                                                 {'emptyDir': {},
                                                                                  'name': 'name-var-spool-mail'}]}},
                                               'triggers': [{'imageChangeParams': {'automatic': True,
                                                                                   'containerNames': ['docker_image'],
                                                                                   'from': {'kind': 'ImageStreamTag',
                                                                                            'name': 'docker_image:latest'}},
                                                             'type': 'ImageChange'}]
                                               }
                                      }]
                         }
        templ = self.ostg._load_oc_template()
        (args) = self.ostg.get_docker_directives(templ)
        tmpl = self.ostg.generate_oc_template(templ, *args)
        assert tmpl == expected_tmpl

    def test_missing_annotation(self):
        expected_tmpl = {'apiVersion': 'v1',
                         'kind': 'Template',
                         'labels': {'description': None, 'tags': None, 'template': None},
                         'metadata': {'annotation': {'tags': u'"TAGS"',
                                      'template': 'docker_image'},
                                      'name': 'docker_image'},
                         'objects': [{'apiVersion': 'v1',
                                      'kind': 'ImageStream',
                                      'metadata': {'name': 'docker_image'},
                                      'spec': {'dockerImageRepository': 'docker_image'},
                                      'tags': [{'name': 'latest'}]},
                                     {'apiVersion': 'v1',
                                      'kind': 'DeploymentConfig',
                                      'metadata': {'name': 'docker_image'},
                                      'spec': {'dockerImageRepository': 'docker_image',
                                               'replicas': 1,
                                               'strategy': {'type': 'Rolling'},
                                               'template': {'metadata': {'labels': {'name': 'docker_image'}},
                                                            'spec': {'containers': [{'env': [{'name': u'POSTFIX_SMTP_PORT',
                                                                                              'value': u'10025'}],
                                                                                     'image': 'docker_image',
                                                                                     'imagePullPolicy': 'Never',
                                                                                     'name': 'docker_image',
                                                                                     'ports': [{'containerPort': 1234},
                                                                                               {'containerPort': 2345},
                                                                                               {'containerPort': 6789}],
                                                                                     'volumeMounts': [{'mountPath': '/var/log',
                                                                                                       'name': 'name-var-log'},
                                                                                                      {'mountPath': '/var/spool/log',
                                                                                                       'name': 'name-var-spool-log'},
                                                                                                      {'mountPath': '/var/spool/mail',
                                                                                                       'name': 'name-var-spool-mail'}]}],
                                                                     'volumes': [{'emptyDir': {},
                                                                                  'name': 'name-var-log'},
                                                                                 {'emptyDir': {},
                                                                                  'name': 'name-var-spool-log'},
                                                                                 {'emptyDir': {},
                                                                                  'name': 'name-var-spool-mail'}]}},
                                               'triggers': [{'imageChangeParams': {'automatic': True,
                                                                                   'containerNames': ['docker_image'],
                                                                                   'from': {'kind': 'ImageStreamTag',
                                                                                            'name': 'docker_image:latest'}},
                                                             'type': 'ImageChange'}]
                                               }
                                      }]
                         }
        templ = self.ostg._load_oc_template()
        labels, volume_list, volume_names, env_list, ports_list = self.ostg.get_docker_directives(templ)
        del labels['description']
        tmpl = self.ostg.generate_oc_template(templ,
                                              labels,
                                              volume_list,
                                              volume_names,
                                              env_list,
                                              ports_list)
        assert tmpl == expected_tmpl


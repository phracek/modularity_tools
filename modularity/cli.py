# -*- coding: utf-8 -*-
#

import sys
import argparse

from modularity.oc_template import OpenShiftTemplateGenerator


class CLI(object):
    """ Class for processing data from commandline """

    @staticmethod
    def build_parser():
        parser = argparse.ArgumentParser(description="Creates an OpenShift template YAML file.")
        parser.add_argument(
            "image",
            metavar='IMAGE',
            help="docker image name (like NAME or docker.io/USER/NAME)",
        )
        parser.add_argument(
            "--dockerfile",
            help="Specify Dockerfile name. Default is Dockerfile."
        )
        return parser

    def __init__(self, args=None):
        self.parser = CLI.build_parser()
        self.args = self.parser.parse_args(args)

    def __getattr__(self, name):
        try:
            return getattr(self.args, name)
        except AttributeError:
            return object.__getattribute__(self, name)


class CliHelper(object):

    @staticmethod
    def run():
        try:
            cli = CLI(sys.argv[1:])
            otg = OpenShiftTemplateGenerator(cli)
            otg.run()
        except KeyboardInterrupt:
            print('\nInterrupted by user')
        except Exception as e:
            print('\n%s', e)
            sys.exit(1)

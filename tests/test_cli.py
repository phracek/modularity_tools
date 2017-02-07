# -*- coding: utf-8 -*-
#

from modularity.cli import CLI


class TestCLI(object):
    """
    The test suite is used for testing CLI class
    """
    def test_cli_unit(self):
        """Function tests cli class with all arguments"""
        conf = {'dockerfile': 'Dockerfile.testing',
                'image': 'Testing_image'}
        arguments = ['--dockerfile', 'Dockerfile.testing',
                     'Testing_image']
        cli = CLI(arguments)
        for key, value in cli.args.__dict__.items():
            assert cli.args.__dict__[key] == conf[key]

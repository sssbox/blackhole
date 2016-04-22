import os
import tempfile
import unittest
from unittest import mock

import pytest

from blackhole.config import Config, Singleton
from blackhole.smtp import Smtp


@pytest.fixture()
def cleandir():
    newpath = tempfile.mkdtemp()
    os.chdir(newpath)


@pytest.fixture()
def reset_conf():
    Singleton._instances = {}


@pytest.mark.usefixtures('reset_conf')
def create_config(data):
    cwd = os.getcwd()
    path = os.path.join(cwd, 'test.conf')
    with open(path, 'w') as cfile:
        cfile.write('\n'.join(data))
    return path


@pytest.mark.usefixtures('reset_conf', 'cleandir')
class TestProcessHeaders(unittest.TestCase):

    def test_valid_mode_header(self):
        smtp = Smtp()
        assert smtp.mode == 'accept'
        smtp.process_header('x-blackhole-mode: bounce')
        assert smtp.mode == 'bounce'

    def test_invalid_mode_header(self):
        smtp = Smtp()
        assert smtp.mode == 'accept'
        smtp.process_header('x-blackhole-mode: help')
        assert smtp.mode == 'accept'

    def test_invalid_mode_header2(self):
        smtp = Smtp()
        assert smtp.mode == 'accept'
        smtp.process_header('x-some-mode: bounce')
        assert smtp.mode == 'accept'

    def test_valid_single_delay(self):
        smtp = Smtp()
        assert smtp.delay is None
        smtp.process_header('x-blackhole-delay: 30')
        assert smtp.delay is 30

    def test_invalid_single_delay(self):
        smtp = Smtp()
        assert smtp.delay is None
        smtp.process_header('x-blackhole-delay: abc')
        assert smtp.delay is None

    def test_valid_range_delay(self):
        smtp = Smtp()
        assert smtp.delay is None
        smtp.process_header('x-blackhole-delay: 5, 10')
        assert smtp.delay in [5, 6, 7, 8, 9, 10]

    def test_invalid_range_delay(self):
        smtp = Smtp()
        assert smtp.delay is None
        smtp.process_header('x-blackhole-delay: abc, def')
        assert smtp.delay is None


@pytest.mark.usefixtures('reset_conf', 'cleandir')
class TestModeSwitch(unittest.TestCase):

    def test_mode_default(self):
        cfile = create_config(('', ))
        Config(cfile).load()
        smtp = Smtp()
        assert smtp.mode == 'accept'

    def test_mode_invalid(self):
        cfile = create_config(('', ))
        Config(cfile).load()
        smtp = Smtp()
        smtp.mode = 'kura'
        assert smtp.mode == 'accept'

    def test_mode_valid(self):
        cfile = create_config(('', ))
        Config(cfile).load()
        smtp = Smtp()
        smtp.mode = 'bounce'
        assert smtp.mode == 'bounce'

    def test_mode_valid_overrides_config(self):
        cfile = create_config(('mode=bounce', ))
        Config(cfile).load()
        smtp = Smtp()
        assert smtp.mode == 'bounce'
        smtp.mode = 'accept'
        assert smtp.mode == 'accept'


@pytest.mark.usefixtures('reset_conf', 'cleandir')
class TestDelaySwitch(unittest.TestCase):

    def test_delay_not_enabled_or_set(self):
        cfile = create_config(('', ))
        Config(cfile).load()
        smtp = Smtp()
        assert smtp.delay is None

    def test_delay_from_config(self):
        cfile = create_config(('delay=30',))
        Config(cfile).load()
        smtp = Smtp()
        assert smtp.delay is 30

    def test_delay_switch_overrides_config_single(self):
        cfile = create_config(('delay=30',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '60'
        assert smtp.delay is 60
        assert smtp.config.delay is 30

    def test_delay_switch_range_overrides_config(self):
        cfile = create_config(('delay=30',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '40, 45'
        assert smtp.delay in [x for x in range(40, 46)]
        assert smtp.config.delay is 30

    def test_delay_switch_invalid_single_value_no_config(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = 'fifteen'
        assert smtp.delay is None

    def test_delay_switch_invalid_single_value_config_60(self):
        cfile = create_config(('delay=30',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = 'fifteen'
        assert smtp.delay is 30

    def test_delay_switch_invalid_single_negative_value(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '-10'
        assert smtp.delay is None

    def test_delay_switch_not_above_max(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '90'
        assert smtp.delay is 60

    def test_delay_switch_invalid_range_value_no_config(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = 'fifteen, eighteen'
        assert smtp.delay is None

    def test_delay_switch_invalid_min_range_value_no_config(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = 'fifteen, 18'
        assert smtp.delay is None

    def test_delay_switch_invalid_max_range_value_no_config(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '15, eighteen'
        assert smtp.delay is None

    def test_delay_switch_invalid_range_negative_min_value(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '-10, 10'
        assert smtp.delay is None

    def test_delay_switch_invalid_range_negative_max_value(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '1, -10'
        assert smtp.delay is None

    def test_delay_switch_invalid_range_negatives(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '-10, -1'
        assert smtp.delay is None

    def test_delay_switch_range_min_higher_than_max(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '20, 10'
        assert smtp.delay is None

    def test_delay_switch_range_max_higher_than_60(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '59, 70'
        assert smtp.delay in [59, 60]

    def test_delay_switch_more_than_2(self):
        cfile = create_config(('',))
        Config(cfile).load()
        smtp = Smtp()
        smtp.delay = '1, 2, 3'
        assert smtp.delay is None
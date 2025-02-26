# -*- coding: utf-8 -*-

from importlib import util
import os

env = os.environ.get('APP_ENV', 'dev')

try:
    spec = util.spec_from_file_location('', 'config/{}.py'.format(env))
    cfg_mod = util.module_from_spec(spec)
    spec.loader.exec_module(cfg_mod)
except FileNotFoundError as e:
    spec = util.spec_from_file_location('', '../../config/{}.py'.format(env))
    cfg_mod = util.module_from_spec(spec)
    spec.loader.exec_module(cfg_mod)

cf = getattr(cfg_mod,'Config')()



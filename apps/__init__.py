# -*- coding: utf-8 -*-
import pkgutil,importlib
import logging.config
from sanic import Sanic
from config.settings import Config
from sanic import Blueprint


def configure_blueprints(sanic_app):
    app_dict = {}
    for _, modname, ispkg in pkgutil.walk_packages(["apps/modules"]):
        try:
            module = importlib.import_module(f"apps.modules.{modname}.views")
            attr = getattr(module, modname)
            if isinstance(attr, Blueprint):
                if app_dict.get(modname) is None:
                    app_dict[modname] = attr
                    sanic_app.blueprint(attr)
                    # print(" * 注入 %s 模块 %s 成功" % (Blueprint.__name__, attr.__str__()))
        except AttributeError:
            logging.error("failed to load module %s", modname)

def create_app(name=None):
    name = name if name else __name__
    app = Sanic(name)
    # 配置日志
    logging.config.dictConfig(Config.BASE_LOGGING)
    # 加载sanic的配置内容
    app.config.update_config(Config)
    # 配置蓝图
    configure_blueprints(app)
    return app


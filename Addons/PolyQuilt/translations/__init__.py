import bpy
import json
import os
import importlib


class TranslationHelper():
    def __init__(self, name: str, data: dict, lang='zh_CN'):
        self.name = name
        self.translations_dict = dict()

        for src, src_trans in data.items():
            key = ("Operator", src)
            self.translations_dict.setdefault(lang, {})[key] = src_trans
            key = ("*", src)
            self.translations_dict.setdefault(lang, {})[key] = src_trans

    def register(self):
        try:
            bpy.app.translations.register(self.name, self.translations_dict)
        except(ValueError):
            pass

    def unregister(self):
        bpy.app.translations.unregister(self.name)


# Set
############
from . import zh_CN, ja_JP

PolyQuilt_zh_CN = TranslationHelper('PolyQuilt_zh_CN', zh_CN.data)
PolyQuilt_zh_HANS = TranslationHelper('PolyQuilt_zh_HANS', zh_CN.data, lang='zh_HANS')
PolyQuilt_ja_JP = TranslationHelper('PolyQuilt_ja_JP', ja_JP.data, lang='ja_JP')


def register():
    PolyQuilt_ja_JP.register()

    if bpy.app.version < (4, 0, 0):
        PolyQuilt_zh_CN.register()
    else:
        PolyQuilt_zh_CN.register()
        PolyQuilt_zh_HANS.register()


def unregister():
    PolyQuilt_ja_JP.unregister()

    if bpy.app.version < (4, 0, 0):
        PolyQuilt_zh_CN.unregister()
    else:
        PolyQuilt_zh_CN.unregister()
        PolyQuilt_zh_HANS.unregister()

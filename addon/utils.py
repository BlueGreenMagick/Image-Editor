from aqt.qt import *
from aqt import mw

addon = mw.addonManager


def get_config(key, hidden=False, notexist=""):
    config = addon.getConfig(__name__)
    if hidden:
        return config["_hidden"].get(key, notexist)
    else:
        return config[key]

def set_config(key, val, hidden=False):
    config = addon.getConfig(__name__)
    if hidden:
        config["_hidden"][key] = val
    else:
        config[key] = val
    addon.writeConfig(__name__, config)

def checked(ch: bool) -> Qt.CheckState:
    if ch:
        return Qt.CheckState.Checked
    else:
        return Qt.CheckState.Unchecked
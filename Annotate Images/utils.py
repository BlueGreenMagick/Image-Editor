from aqt.qt import *
from aqt import mw

addon = mw.addonManager


def save_geom(widget, key):
    geom: QByteArray = widget.saveGeometry()
    geom_str = geom.toBase64().data().decode("ascii")
    config = addon.getConfig(__name__)
    config["_hidden"]["geom"][key] = geom_str
    addon.writeConfig(__name__, config)


def load_geom(key):
    config = addon.getConfig(__name__)
    if not isinstance(config["_hidden"], dict):
        config["_hidden"] = {}
    if "geom" not in config["_hidden"]:
        config["_hidden"]["geom"] = {}
    if key in config["_hidden"]["geom"]:
        geom = QByteArray.fromBase64(QByteArray.fromRawData(config["_hidden"]["geom"][key].encode("ascii")))
        return geom
    else:
        return None

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
        return Qt.Checked
    else:
        return Qt.Unchecked
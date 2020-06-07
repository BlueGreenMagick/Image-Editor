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
    if key in config["_hidden"]["geom"]:
        geom = QByteArray.fromBase64(QByteArray.fromRawData(config["_hidden"]["geom"][key].encode("ascii")))
        return geom
    else:
        return None
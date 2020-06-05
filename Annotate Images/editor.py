import os
from pathlib import Path

from anki.hooks import addHook
from aqt.editor import EditorWebView, Editor
from aqt import mw
from aqt.utils import tooltip
from aqt.qt import QMenu
from aqt import gui_hooks

from .annotation import AnnotateDialog

ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)

def add_context_menu_action(wv: EditorWebView, m: QMenu):
    context_data = wv.page().contextMenuData()
    url = context_data.mediaUrl()
    image_name = url.fileName()
    # Using url.path() doesn't return the absolute path
    image_path = Path(mw.col.media.dir()) / image_name
    if url.isValid():
        a = m.addAction("Annotate Image")
        a.triggered.connect(lambda _: open_annotate_window(wv, image_path))


def open_annotate_window(wv, img_path):
    mw.anodial = AnnotateDialog(img_path, wv)

def insert_js(web_content, context):
    if not isinstance(context, Editor):
        return
    web_content.js.append(f"/_addons/{ADDON_PACKAGE}/web/editor.js")

mw.addonManager.setWebExports(__name__, r"web/editor.js")
addHook("EditorWebView.contextMenuEvent", add_context_menu_action)
gui_hooks.webview_will_set_content.append(insert_js)
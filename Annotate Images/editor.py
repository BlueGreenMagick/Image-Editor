import os
from pathlib import Path

from anki import version as ANKIVER
from anki.hooks import addHook
from aqt import mw
from aqt.editor import EditorWebView, Editor
from aqt.utils import tooltip
from aqt.qt import QMenu
from aqt import gui_hooks
from aqt.utils import showText

from .annotation import AnnotateDialog

ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)
ICONS_PATH = os.path.join(os.path.dirname(__file__), "icons")


def open_annotate_window(editor, name = "", path = "", src = "", new_image = False):
    mw.annodial = AnnotateDialog(editor, name = name, path = path, src = src, new_image = new_image)

def add_context_menu_action(wv: EditorWebView, m: QMenu):
    context_data = wv.page().contextMenuData()
    url = context_data.mediaUrl()
    image_name = url.fileName()
    # Using url.path() doesn't return the absolute path
    image_path = Path(mw.col.media.dir()) / image_name
    if url.isValid() and image_path.is_file():
        a = m.addAction("Edit Image")
        a.triggered.connect(lambda _, path=image_path, nm=image_name: open_annotate_window(wv.editor, name = nm, path=path, src=url.toString()))


def insert_js(web_content, context):
    if not isinstance(context, Editor):
        return
    web_content.js.append(f"/_addons/{ADDON_PACKAGE}/web/editor.js")

def setup_editor_buttons(btns, editor):
    hotkey = "Ctrl + Shift + I"
    icon = os.path.join(ICONS_PATH, "draw.svg")
    b = editor.addButton(icon, "Draw Image",
                         lambda o=editor: open_annotate_window(o, new_image = True),
                         tip=f"({hotkey})",
                         keys=hotkey, disables=True)

    btns.append(b)
    return btns

mw.addonManager.setWebExports(__name__, r"web/editor.js")
addHook("EditorWebView.contextMenuEvent", add_context_menu_action)
addHook('setupEditorButtons', setup_editor_buttons)
gui_hooks.webview_will_set_content.append(insert_js)
import os

from anki.hooks import addHook
from aqt.editor import EditorWebView
from aqt import mw
from aqt.utils import tooltip
from aqt.qt import QMenu

def add_context_menu_action(wv: EditorWebView, m: QMenu):
    context_data = wv.page().contextMenuData()
    url = context_data.mediaUrl()
    image_name = url.fileName()
    # Using url.path() doesn't return the absolute path
    image_path = os.path.jfefeoin(mw.col.media.dir(), image_name)
    if url.isValid():
        a = m.addAction("Annotate Image")
        a.triggered.connect(lambda _: open_annotate_window(wv, image_path))



addHook("EditorWebView.contextMenuEvent", add_context_menu_action)

import os
import sys
import base64
from pathlib import Path

from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView, AnkiWebPage
from aqt.utils import tooltip, showText

method_draw_path = os.path.join(
    os.path.dirname(__file__), "web", "Method-Draw", "editor", "index.html"
)


MIME_TYPE = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "ico": "image/vnd.microsoft.icon",
    "svg": "image/svg+xml"
}

class myPage(AnkiWebPage):
    def acceptNavigationRequest(self, url, navType, isMainFrame):
        "Needed so the link don't get opened in external browser"
        return True


class AnnotateDialog(QDialog):
    def __init__(self, image_path, editor_wv):
        QDialog.__init__(self)
        mw.setupDialogGC(self)
        self.editor_wv = editor_wv
        self.editor = editor_wv.editor
        self.image_path = image_path
        self.close_queued = False
        self.setupUI()
        

    def setupUI(self):
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        self.web = AnkiWebView(parent=self, title="Annotate Image")
        url = QUrl.fromLocalFile(method_draw_path)
        self.web._page = myPage(self.web._onBridgeCmd)
        self.web.setPage(self.web._page)
        self.web.setUrl(url)
        self.web.set_bridge_command(self.on_bridge_cmd, self)
        mainLayout.addWidget(self.web, stretch=1)

        self.move(
            QDesktopWidget().availableGeometry().center()
            - self.frameGeometry().center()
        )

        self.setWindowTitle("Annotate Image")
        self.setMinimumWidth(640)
        self.show()
    
    def on_bridge_cmd(self, cmd):
        if cmd == "img_src":
            img_path = self.image_path
            img_path_str = self.image_path.resolve().as_posix()
            img_format = img_path_str.split('.')[-1].lower()
            if img_format not in MIME_TYPE:
                tooltip("Image Not Supported")
                return
            
            if img_format == "svg":
                img_data = base64.b64encode(img_path.read_text().encode("utf-8")).decode("ascii")
            else:
                mime_str = MIME_TYPE[img_format]
                encoded_img_data = base64.b64encode(img_path.read_bytes()).decode()
                img_data = "data:{};base64,{}".format(mime_str, encoded_img_data)
            self.web.eval("ankiAddonSetImg('{}', '{}')".format(img_data, img_format))

        elif cmd.startswith("svg_save:"):
            svg_str = cmd[len("svg_save:"):]
            self.save_svg(svg_str)
    
    def save_svg(self, svg_str):
        image_path = self.image_path.resolve().as_posix()
        img_name = image_path.split('/collection.media/')[-1]
        desired_name = '.'.join(img_name.split('.')[:-1]) + '.svg'
        new_name = mw.col.media.write_data(desired_name, svg_str.encode('utf-8'))
        self.replace_img_src(new_name)

        if self.close_queued:
            self.close()

    def replace_img_src(self, path):
        pathstr = base64.b64encode(str(path).encode("utf-8")).decode("ascii")
        self.editor_wv.eval("addonAnnoChangeSrc('{}')".format(pathstr))

    def closeEvent(self, evt):
        if self.close_queued:
            del mw.anodial
            evt.accept()
        else:
            self.web.eval("ankiAddonSaveImg()")
            self.close_queued = True
            evt.ignore()

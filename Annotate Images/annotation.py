import os
import sys
import base64
from pathlib import Path
from threading import Timer

from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView, AnkiWebPage
from aqt.utils import tooltip, showText, askUserDialog

from .utils import load_geom, save_geom

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
        
    def closeEvent(self, evt):
        if self.close_queued:
            del mw.anodial
            save_geom(self, "anno_dial")
            evt.accept()
        else:
            self.ask_on_close(evt)
            
                

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

        okButton = QPushButton("Save")
        okButton.clicked.connect(self.save)
        okButton.setDefault(True)
        cancelButton = QPushButton("Discard")
        cancelButton.clicked.connect(self.discard)
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.reset)

        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(okButton)
        btnLayout.addWidget(cancelButton)
        btnLayout.addWidget(resetButton)
        mainLayout.addLayout(btnLayout)

        self.setWindowTitle("Annotate Image")

        self.setMinimumWidth(400)
        self.setMinimumHeight(400)
        self.setGeometry(0, 0, 640, 640)
        self.move(
            QDesktopWidget().availableGeometry().center()
            - self.frameGeometry().center()
        )
        geom = load_geom("anno_dial")
        if geom:
            self.restoreGeometry(geom)
        self.show()


    def discard(self):
        self.close_queued = True
        self.close()
    
    def save(self):
        self.close_queued = True
        self.web.eval("ankiAddonSaveImg()")
    
    def reset(self):
        self.load_img()



    def on_bridge_cmd(self, cmd):
        if cmd == "img_src":
            self.load_img()

        elif cmd.startswith("svg_save:"):
            svg_str = cmd[len("svg_save:"):]
            self.save_svg(svg_str)

    def load_img(self):
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

    def ask_on_close(self, evt):
        opts = [
            "Cancel",
            "Discard",
            "Save"
        ]
        diag = askUserDialog("Discard Changes?", opts, parent=self)
        diag.setDefault(0)
        ret = diag.run()
        if ret == opts[0]:
            evt.ignore()
        elif ret == opts[1]:
            evt.accept()
        elif ret == opts[2]:
            self.save()
            evt.ignore()
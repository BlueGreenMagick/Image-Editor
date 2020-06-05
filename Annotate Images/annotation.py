import os
import sys
import base64
from pathlib import Path

from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView, AnkiWebPage
from aqt.utils import tooltip

method_draw_path = os.path.join(
    os.path.dirname(__file__), "web", "Method-Draw", "editor", "index.html"
)


class myPage(AnkiWebPage):
    def acceptNavigationRequest(self, url, navType, isMainFrame):
        "Needed so the link don't get opened in external browser"
        return True


class AnnotateDialog(QDialog):
    def __init__(self, image_path):
        QDialog.__init__(self)
        mw.setupDialogGC(self)
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
            encoded_img_path = base64.b64encode(str(self.image_path).encode("utf-8")).decode("ascii")
            self.web.eval("ankiAddonSetImg('%s', 'png')"%encoded_img_path)
            #TODO: as data uri not relative link
        elif cmd.startswith("svg_save:"):
            svg_str = cmd[len("svg_save:"):]
            self.save_svg(svg_str)
    
    def save_svg(self, svg_str):
        #TODO: replace image reference to new image path in anki card field
        image_path = str(self.image_path)
        if image_path[-3:] != "svg":
            image_path = ".".join(image_path.split('.')[:-1]) + ".svg"
        Path(image_path).write_text(svg_str)
        if self.close_queued:
            self.close()

    def closeEvent(self, evt):
        if self.close_queued:
            del mw.anodial
            evt.accept()
        else:
            self.web.eval("ankiAddonSaveImg()")
            self.close_queued = True
            evt.ignore()

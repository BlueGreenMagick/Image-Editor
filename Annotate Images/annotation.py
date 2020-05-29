import os
import sys

from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView, AnkiWebPage

method_draw_path = os.path.join(
    os.path.dirname(__file__), "web", "Method-Draw", "editor", "index.html"
)


class myPage(AnkiWebPage):
    def acceptNavigationRequest(self, url, navType, isMainFrame):
        "Needed so the link don't get opened in external browser"
        return True


class AnnotateDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        mw.setupDialogGC(self)
        self.setupUI()

    def setupUI(self):
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        self.web = AnkiWebView(parent=self, title="Annotate Image")
        url = QUrl.fromLocalFile(method_draw_path)
        self.web._page = myPage(self.web._onBridgeCmd)
        self.web.setPage(self.web._page)
        self.web.setUrl(url)
        mainLayout.addWidget(self.web, stretch=1)

        self.move(
            QDesktopWidget().availableGeometry().center()
            - self.frameGeometry().center()
        )

        self.setWindowTitle("Annotate Image")
        self.setMinimumWidth(640)
        self.show()

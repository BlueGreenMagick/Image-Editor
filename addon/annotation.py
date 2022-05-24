import os
import sys
import base64
import re
import json
from pathlib import Path
from threading import Timer

import anki.find
import aqt
from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView, AnkiWebPage
from aqt.utils import tooltip, showText, askUserDialog, restoreGeom, saveGeom

from . import COMPAT
from .utils import get_config, set_config, checked

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
    "svg": "image/svg+xml",
}


class myPage(AnkiWebPage):
    def acceptNavigationRequest(self, url, navType, isMainFrame):
        "Needed so the link don't get opened in external browser"
        return True


class AnnotateDialog(QDialog):
    def __init__(self, editor, name, path="", src="", create_new=False):
        QDialog.__init__(self, editor.widget, Qt.WindowType.Window)
        # Compatibility: 2.1.0+
        mw.setupDialogGC(self)
        self.editor_wv = editor.web
        self.editor = editor
        self.image_name = name
        self.image_path = path
        self.image_src = src
        self.create_new = create_new
        self.close_queued = False
        if not create_new:
            self.check_editor_image_selected()
        self.setupUI()

    def closeEvent(self, evt):
        if self.close_queued:
            saveGeom(self, "addon_image_editor")
            del mw.annodial
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

        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)

        replaceAll = QCheckBox("Replace All")
        self.replaceAll = replaceAll
        ch = get_config("replace_all", hidden=True, notexist=False)
        replaceAll.setCheckState(checked(ch))
        replaceAll.stateChanged.connect(self.check_changed)
        btnLayout.addWidget(replaceAll)

        okButton = QPushButton("Save")
        okButton.clicked.connect(self.save)
        btnLayout.addWidget(okButton)
        cancelButton = QPushButton("Discard")
        cancelButton.clicked.connect(self.discard)
        btnLayout.addWidget(cancelButton)
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.reset)
        btnLayout.addWidget(resetButton)

        okButton.setDefault(False)
        okButton.setAutoDefault(False)
        cancelButton.setDefault(False)
        cancelButton.setAutoDefault(False)
        resetButton.setDefault(False)
        resetButton.setAutoDefault(False)

        mainLayout.addLayout(btnLayout)

        self.setWindowTitle("Annotate Image")
        self.setMinimumWidth(100)
        self.setMinimumHeight(100)
        self.setGeometry(0, 0, 640, 640)
        restoreGeom(self, "addon_image_editor")
        if not self.close_queued:
            # When image isn't selected js side
            self.show()

    def check_changed(self, state: int):
        set_config("replace_all", bool(state), hidden=True)

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
            if not self.create_new:
                self.load_img()

        elif cmd.startswith("svg_save:"):
            if self.create_new:
                svg_str = cmd[len("svg_save:"):]
                self.create_svg(svg_str)
            else:
                svg_str = cmd[len("svg_save:"):]
                self.save_svg(svg_str)

    def check_editor_image_selected(self):
        def check_image_selected(selected):
            if selected == False:
                self.close_queued = True
                self.close()
                tooltip("Image wasn't selected properly.\nPlease try again.")
        # Compatibility: 2.1.0+
        self.editor_wv.evalWithCallback(
            "addonAnno.imageIsSelected()", check_image_selected)

    def load_img(self):
        img_path = self.image_path
        img_path_str = self.image_path.resolve().as_posix()
        img_format = img_path_str.split(".")[-1].lower()
        if img_format not in MIME_TYPE:
            tooltip("Image Not Supported", parent=self.editor.widget)
            return

        if img_format == "svg":
            img_data = json.dumps(img_path.read_text(encoding="utf-8"))
        else:
            mime_str = MIME_TYPE[img_format]
            encoded_img_data = base64.b64encode(img_path.read_bytes()).decode()
            img_data = "'data:{};base64,{}'".format(mime_str, encoded_img_data)
        self.web.eval("ankiAddonSetImg({}, '{}')".format(
            img_data, img_format))

    def create_svg(self, svg_str):
        "When creating an image from nothing"
        # Compatibility: 2.1.0+
        if COMPAT["write_data"]:
            new_name = mw.col.media.write_data(
                "svg_drawing.svg", svg_str.encode("utf-8"))
        else:
            new_name = mw.col.media.writeData(
                "svg_drawing.svg", svg_str.encode("utf-8"))
        img_el = '"<img src=\\"{}\\">"'.format(new_name)
        # Compatilibility: 2.1.0+
        write_image_script = "document.execCommand('inserthtml', false, {});".format(img_el)
        self.editor_wv.evalWithCallback(
            write_image_script, 
            lambda res: not res and self.editor_wv.eval("focusField(0); setTimeout(() => {" + write_image_script + "},25)"))
        print(self.editor.currentField)
        self.create_new = False
        self.image_path = Path(mw.col.media.dir()) / new_name
        tooltip("Image Created", parent=self.editor.widget)
        if self.close_queued:
            self.close()

    def save_svg(self, svg_str):
        "When editing existing image"

        image_path = self.image_path.resolve().as_posix()
        img_name = self.image_name
        desired_name = ".".join(img_name.split(".")[:-1])
        desired_name = desired_name[:15] if len(
            desired_name) > 15 else desired_name
        desired_name += ".svg"
        # remove whitespace and double quote as it messes with replace_all_img_src
        desired_name = desired_name.replace(
            " ", "").replace('"', "").replace("$", "")
        if not desired_name:
            desired_name = "blank"
        # Compatibility: 2.1.0+
        if COMPAT["write_data"]:
            new_name = mw.col.media.write_data(
                desired_name, svg_str.encode("utf-8"))
        else:
            new_name = mw.col.media.writeData(
                desired_name, svg_str.encode("utf-8"))

        if self.replaceAll.checkState() == Qt.CheckState.Checked:
            if self.editor.addMode:
                self.replace_img_src_webview(new_name, replace_all=True)
                self.replace_all_img_src(img_name, new_name)
            else:
                self.editor.saveNow(lambda s=self, i=img_name,
                                n=new_name: s.replace_all_img_src(i, n))
        else:
            self.replace_img_src_webview(new_name)
            tooltip("Image Saved", parent=self.editor.widget)

        if self.close_queued:
            self.close()

    def replace_img_src_webview(self, name: str, replace_all=False):
        namestr = base64.b64encode(str(name).encode("utf-8")).decode("ascii")
        # Compatibility: 2.1.0+
        if replace_all:
            self.editor_wv.eval("addonAnno.changeAllSrc('{}')".format(namestr))
        else:
            self.editor_wv.eval("addonAnno.changeSrc('{}')".format(namestr))

    def ask_on_close(self, evt):
        # Compatibility: 2.1.0+
        opts = ["Cancel", "Discard", "Save"]
        diag = askUserDialog("Discard Changes?", opts, parent=self)
        diag.setDefault(0)
        ret = diag.run()
        if ret == opts[0]:
            evt.ignore()
        elif ret == opts[1]:
            saveGeom(self, "addon_image_editor")
            evt.accept()
        elif ret == opts[2]:
            self.save()
            saveGeom(self, "addon_image_editor")
            evt.ignore()

    def replace_all_img_src(self, orig_name: str, new_name: str):
        browser = aqt.dialogs._dialogs["Browser"][1]
        if browser:
            browser.model.beginReset()
        cnt = self._replace_all_img_src(orig_name, new_name)
        if not self.editor.addMode:
            mw.requireReset()
        if browser:
            browser.model.endReset()
        tooltip(f"Images across {cnt} note(s) modified",
                parent=self.editor.widget)

    def _replace_all_img_src(self, orig_name: str, new_name: str):
        "new_name doesn't have whitespace, dollar sign, nor double quote"

        orig_name = re.escape(orig_name)
        new_name = new_name

        # Compatibility: 2.1.0+
        n = mw.col.findNotes("<img")

        # src element quoted case
        reg1 = r"""(?P<first><img[^>]* src=)(?:"{name}")|(?:'{name}')(?P<second>[^>]*>)""".format(
            name=orig_name
        )
        # unquoted case
        reg2 = r"""(?P<first><img[^>]* src=){name}(?P<second>(?: [^>]*>)|>)""".format(
            name=orig_name
        )
        img_regs = [reg1]
        if " " not in orig_name:
            img_regs.append(reg2)

        if COMPAT["find_replace"]:
            repl = """${first}"%s"${second}""" % new_name
        else:
            repl = """\\g<first>"%s"\\g<second>""" % new_name

        replaced_cnt = 0
        for reg in img_regs:
            if COMPAT["find_replace"]:
                res = mw.col.find_and_replace(
                    note_ids=n,
                    search=reg,
                    replacement=repl,
                    regex=True,
                    match_case=False,
                    field_name=None,
                )
            else:
                res = anki.find.findReplace(
                    col=mw.col, nids=n, src=reg, dst=repl, regex=True, fold=False)
            if COMPAT["find_replace_cnt"]:
                replaced_cnt += res.count
            else:
                replaced_cnt += res
        return replaced_cnt

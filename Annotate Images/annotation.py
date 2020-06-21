import os
import sys
import base64
from pathlib import Path
from threading import Timer

from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView, AnkiWebPage
from aqt.utils import tooltip, showText, askUserDialog

from .utils import load_geom, save_geom, get_config, set_config, checked

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


class myWebView(AnkiWebView):
    def contextMenuEvent(self, evt: QContextMenuEvent) -> None:
        return


class AnnotateDialog(QDialog):
    def __init__(self, editor, image_path="", image_src="", new_image=False):
        QDialog.__init__(self, editor.widget, Qt.Window)
        mw.setupDialogGC(self)
        self.editor_wv = editor.web
        self.editor = editor
        self.image_path = image_path
        self.image_src = image_src
        self.create_new = new_image
        self.close_queued = False
        self.check_editor_image_selected()
        self.setupUI()

    def closeEvent(self, evt):
        if self.close_queued:
            save_geom(self, "anno_dial")
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

        replaceAll = QCheckBox("Replace All")
        ch = get_config("replace_all", hidden=True, notexist=False)
        replaceAll.setCheckState(checked(ch))
        replaceAll.stateChanged.connect(self.check_changed)
        okButton = QPushButton("Save")
        okButton.clicked.connect(self.save)
        cancelButton = QPushButton("Discard")
        cancelButton.clicked.connect(self.discard)
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.reset)

        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(replaceAll)
        btnLayout.addWidget(okButton)
        btnLayout.addWidget(cancelButton)
        btnLayout.addWidget(resetButton)
        mainLayout.addLayout(btnLayout)

        self.setWindowTitle("Annotate Image")

        self.setMinimumWidth(100)
        self.setMinimumHeight(100)
        self.setGeometry(0, 0, 640, 640)
        geom = load_geom("anno_dial")
        if geom:
            self.restoreGeometry(geom)
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
                svg_str = cmd[len("svg_save:") :]
                self.create_svg(svg_str)
            else:
                svg_str = cmd[len("svg_save:") :]
                self.save_svg(svg_str)
            tooltip("Image Saved", parent=self.editor.widget)

    def check_editor_image_selected(self):
        def check_same_image_selected(src):
            if src != self.image_src:
                fld_txt = self.editor.note.fields[self.editor.currentField]
                err_msg = """Image Editor Error: Unmatching image src\n
Please report the issue in this addon's github https:github.com/bluegreenmagick/image-editor

Src1: {name1}
Src2: {name2}
Note field content: {fld}
""".format(
                    name1=src, name2=self.image_src, fld=fld_txt
                )
                showText(err_msg, parent=self.editor.widget)

                self.close_queued = True
                self.close()

        self.editor_wv.evalWithCallback("addonAnno_getSrc()", check_same_image_selected)

    def load_img(self):
        img_path = self.image_path
        img_path_str = self.image_path.resolve().as_posix()
        img_format = img_path_str.split(".")[-1].lower()
        if img_format not in MIME_TYPE:
            tooltip("Image Not Supported", parent=self.editor.widget)
            return

        if img_format == "svg":
            img_data = base64.b64encode(img_path.read_text().encode("utf-8")).decode(
                "ascii"
            )
        else:
            mime_str = MIME_TYPE[img_format]
            encoded_img_data = base64.b64encode(img_path.read_bytes()).decode()
            img_data = "data:{};base64,{}".format(mime_str, encoded_img_data)
        self.web.eval("ankiAddonSetImg('{}', '{}')".format(img_data, img_format))

    def create_svg(self, svg_str):
        new_name = mw.col.media.write_data("svg_drawing.svg", svg_str.encode("utf-8"))
        img_el = '"<img src=\\"{}\\">"'.format(new_name)
        self.editor_wv.eval("insertHtmlRemovingInitialBR({})".format(img_el))
        self.new_image = False
        self.image_path = Path(mw.col.media.dir()) / new_name

        if self.close_queued:
            self.close()

    def save_svg(self, svg_str):
        image_path = self.image_path.resolve().as_posix()
        img_name = image_path.split("/collection.media/")[-1]
        desired_name = ".".join(img_name.split(".")[:-1]) + ".svg"
        # remove whitespace and double quote as it messes with replace_all_img_src
        desired_name = desired_name.replace(" ", "").replace('"',"")
        if not desired_name:
            desired_name = "blank"
        new_name = mw.col.media.write_data(desired_name, svg_str.encode("utf-8"))
        self.replace_img_src(new_name)

        if self.close_queued:
            self.close()

    def replace_img_src(self, name: str):
        namestr = base64.b64encode(str(name).encode("utf-8")).decode("ascii")
        self.editor_wv.eval("addonAnno_changeSrc('{}')".format(namestr))

    def ask_on_close(self, evt):
        opts = ["Cancel", "Discard", "Save"]
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

    def replace_all_img_src(self, orig_name: str, new_name: str):

        orig_name = re.escape(orig_name)
        new_name = re.escape(new_name)

        n = mw.col.db.list("select id from notes")

        # src element quoted case
        reg1 = r"""(?P<first><img[^>]* src=)(?:"{name}")|(?:'{name}')(?P<second>[^>]*>)""".format(
            name=orig_name
        )
        # unquoted case
        reg2 = r"""(?P<first><img[^>]* src=){name}(?P<second>(?: [^>]*>)|>)""".format(
            name=orig_name
        )
        img_regs = [reg1]
        # new_name cannot have whitespace so skip check
        if " " not in orig_name:
            img_regs.append(reg2)
        # new_name cannot have double quote either
        repl = """${first}"%s"${second}""" % new_name

        for reg in img_regs:
            replaced_cnt = mw.col.backend.find_and_replace(
                nids=n,
                search=reg,
                replacement=repl,
                regex=True,
                match_case=False,
                field_name=None,
            )
        return replaced_cnt


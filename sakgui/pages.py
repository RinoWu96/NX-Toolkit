"""One page per feature. Each page builds Task lists and hands them to the main window.
每个功能一个页面；页面生成任务列表并交给主窗口执行。"""
import re
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QPushButton, QRadioButton, QScrollArea, QSpinBox,
                               QVBoxLayout, QWidget)

from . import forwarder, ops
from .config import TOOLS, Config, open_folder
from .i18n import tr
from .tasks import Task
from .widgets import Card, FileList, PathPicker, labeled


class Page(QWidget):
    title_key = ""
    desc_key = ""
    has_output = True
    # Show the temp-folder picker (pages whose tasks write intermediate files).
    # 是否显示临时文件夹选择框（任务会产生中间文件的页面）。
    uses_temp = False

    def __init__(self, cfg: Config, submit):
        super().__init__()
        self.cfg = cfg
        self.submit = submit  # callable(List[Task]) -> bool，提交任务的回调
        self.setObjectName("page")

        inner = QWidget()
        inner.setObjectName("page")
        self.content = QVBoxLayout(inner)
        self.content.setContentsMargins(28, 24, 28, 16)
        self.content.setSpacing(14)
        if self.title_key:
            t = QLabel(tr(self.title_key))
            t.setObjectName("pageTitle")
            self.content.addWidget(t)
        if self.desc_key:
            d = QLabel(tr(self.desc_key))
            d.setObjectName("pageDesc")
            d.setWordWrap(True)
            self.content.addWidget(d)

        self.build()

        if self.has_output:
            self.out = PathPicker(cfg["output_dir"], "dir")
            card = Card(tr("output_dir"))
            card.add(self.out)
            if self.uses_temp:
                self.temp = PathPicker(cfg["temp_dir"], "dir")
                card.add(labeled(tr("temp_hint"), self.temp))
            self.content.addWidget(card)
            row = QHBoxLayout()
            openb = QPushButton(tr("open_output"))
            openb.clicked.connect(self._open_output)
            self.start_btn = QPushButton(tr("start"))
            self.start_btn.setObjectName("primary")
            self.start_btn.clicked.connect(self._start)
            row.addWidget(openb)
            row.addStretch(1)
            row.addWidget(self.start_btn)
            self.content.addLayout(row)
        self.content.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll)

    def build(self):
        pass

    def tasks(self, outdir: Path) -> List[Task]:
        return []

    def showEvent(self, e):
        # Output and temp folders are shared by all pages and Settings; show their current values.
        # 输出目录和临时目录由所有页面和设置页共用，显示时同步为当前值。
        if self.has_output:
            self.out.set_value(self.cfg["output_dir"])
        if self.uses_temp:
            self.temp.set_value(self.cfg["temp_dir"])
        super().showEvent(e)

    def _remember_paths(self):
        changed = False
        for key, picker in (("output_dir", getattr(self, "out", None)), ("temp_dir", getattr(self, "temp", None))):
            if picker is not None and picker.value() and picker.value() != self.cfg[key]:
                self.cfg[key] = picker.value()
                changed = True
        if changed:
            self.cfg.save()

    def _open_output(self):
        self._remember_paths()
        open_folder(self.cfg.output(self.out.value()))

    def _start(self):
        self._remember_paths()
        try:
            outdir = self.cfg.output(self.out.value())
            tasks = self.tasks(outdir)
        except ops.OpError as e:
            QMessageBox.warning(self, tr("error"), str(e))
            return
        except OSError as e:
            QMessageBox.warning(self, tr("error"), str(e))
            return
        if tasks:
            self.submit(tasks)

    def _require(self, files: FileList) -> List[str]:
        paths = files.paths()
        if not paths:
            raise ops.OpError(tr("no_files"))
        return paths


# ------------------------------------------------------------------ convert / 格式互转
class ConvertPage(Page):
    title_key, desc_key = "convert_title", "convert_desc"
    uses_temp = True

    TARGETS = [".nsp", ".xci", ".nsz", ".xcz"]

    def build(self):
        self.files = FileList([".xci", ".nsp", ".nsz", ".xcz"])
        c = Card(tr("card_input"))
        c.add(self.files)
        self.content.addWidget(c)

        t = Card(tr("convert_target"))
        self.target = QComboBox()
        for ext in self.TARGETS:
            self.target.addItem(tr("target" + ext), ext)
        t.add(self.target)
        self.route = QLabel("")
        self.route.setObjectName("status")
        self.route.setWordWrap(True)
        t.add(self.route)
        self.content.addWidget(t)

        self.nxci_card = Card("4NXCI")
        self.keep = self.nxci_card.add(QCheckBox(tr("keep_ncaid")))
        self.rename = self.nxci_card.add(QCheckBox(tr("rename_out")))
        self.content.addWidget(self.nxci_card)

        self.nsz_card = Card(tr("nsz_options"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        self.level = QSpinBox()
        self.level.setRange(1, 22)
        self.level.setValue(int(self.cfg["nsz_level"]))
        self.threads = QSpinBox()
        self.threads.setRange(0, 64)
        self.mode = QComboBox()
        for key in ("auto", "block", "solid"):
            self.mode.addItem(tr(f"mode_{key}"), key)
        grid.addLayout(labeled(tr("level"), self.level), 0, 0)
        grid.addLayout(labeled(tr("threads"), self.threads), 0, 1)
        grid.addLayout(labeled(tr("mode"), self.mode), 0, 2)
        self.nsz_card.add(grid)
        self.long = self.nsz_card.add(QCheckBox(tr("long_mode")))
        self.verify = self.nsz_card.add(QCheckBox(tr("quick_verify")))
        self.verify.setChecked(True)
        self.overwrite = self.nsz_card.add(QCheckBox(tr("overwrite")))
        self.content.addWidget(self.nsz_card)

        self.target.currentIndexChanged.connect(self._update_route)
        self.files.changed.connect(self._update_route)
        self._update_route()

    def _target(self) -> str:
        return self.target.currentData()

    def _update_route(self, *_):
        """Show which tools each input type goes through, and only the option cards that apply.
        显示每种输入会经过哪些工具，并只显示用得到的选项卡片。"""
        target = self._target()
        exts = sorted({Path(p).suffix.lower() for p in self.files.paths()}) or [".xci", ".nsp", ".nsz", ".xcz"]
        routes = {e: ops.ROUTES[(e, target)] for e in exts if e != target}
        tools = " ".join(routes.values())
        self.nxci_card.setVisible("4NXCI" in tools)
        self.nsz_card.setVisible("nsz -C" in tools)
        self.route.setText("\n".join(f"{e[1:].upper()} → {target[1:].upper()}:   {r}" for e, r in routes.items()))

    def tasks(self, outdir):
        self.cfg["nsz_level"] = self.level.value()
        nsz = ops.NszOpts(self.level.value(), self.long.isChecked(), self.mode.currentData(),
                          self.threads.value(), self.verify.isChecked(), self.overwrite.isChecked())
        opts = ops.ConvertOpts(self.keep.isChecked(), self.rename.isChecked(), nsz)
        return ops.convert(self.cfg, self._require(self.files), outdir, self._target(), opts)


# ------------------------------------------------------------------ merge / 合并
class MergePage(Page):
    title_key, desc_key = "merge_title", "merge_desc"
    uses_temp = True

    def build(self):
        self.files = FileList([".xci", ".nsp", ".nsz", ".xcz"])
        c = Card(tr("card_merge"))
        c.add(self.files)
        self.content.addWidget(c)
        o = Card(tr("merge_format"))
        row = QHBoxLayout()
        self.fmt = QButtonGroup(self)
        for i, (key, label) in enumerate([("xci", "XCI"), ("nsp", "NSP")]):
            rb = QRadioButton(label)
            rb.setProperty("fmt", key)
            rb.setChecked(i == 0)
            self.fmt.addButton(rb)
            row.addWidget(rb)
        row.addStretch(1)
        o.add(row)
        self.content.addWidget(o)

    def tasks(self, outdir):
        return ops.merge(self.cfg, self._require(self.files), outdir, self.fmt.checkedButton().property("fmt"))


# ------------------------------------------------------------------ split / 拆分
class SplitPage(Page):
    title_key, desc_key = "split_title", "split_desc"

    def build(self):
        o = Card(tr("split_mode"))
        row = QHBoxLayout()
        self.rb_split = QRadioButton(tr("do_split"))
        self.rb_join = QRadioButton(tr("do_join"))
        self.rb_split.setChecked(True)
        row.addWidget(self.rb_split)
        row.addWidget(self.rb_join)
        row.addStretch(1)
        o.add(row)
        self.content.addWidget(o)
        self.files = FileList([".nsp", ".xci", ".xc0"], allow_dirs=True)
        c = Card(tr("card_input"))
        c.add(self.files)
        self.content.addWidget(c)

    def tasks(self, outdir):
        return ops.split_join(self.cfg, self._require(self.files), outdir, self.rb_split.isChecked())


# ------------------------------------------------------------------ firmware / 固件
class FirmwarePage(Page):
    title_key, desc_key = "fw_title", "fw_desc"

    def build(self):
        self.files = FileList([".xci"])
        c = Card("XCI")
        c.add(self.files)
        self.content.addWidget(c)

    def tasks(self, outdir):
        return ops.firmware(self.cfg, self._require(self.files), outdir)


# ------------------------------------------------------------------ savegames / 存档
class SavePage(Page):
    title_key, desc_key = "save_title", "save_desc"

    def build(self):
        # NAND save files have no extension (e.g. 8000000000000010); accept any file.
        # NAND 存档文件没有扩展名（如 8000000000000010），所以接受任意文件。
        self.files = FileList([])
        c = Card(tr("card_saves"))
        c.add(self.files)
        self.content.addWidget(c)

    def tasks(self, outdir):
        return ops.savegames(self.cfg, self._require(self.files), outdir)


# ------------------------------------------------------------------ forwarder / 转发器
class ForwarderPage(Page):
    title_key, desc_key = "fwd_title", "fwd_desc"

    def build(self):
        self._nro_icon = None

        src = Card("NRO")
        self.nro = PathPicker("", "file", "NRO (*.nro)")
        self.nro.changed.connect(self._nro_changed)
        src.add(labeled(tr("fwd_nro_local"), self.nro))
        self.sd_path = QLineEdit("sdmc:/switch/")
        src.add(labeled(tr("fwd_nro_path"), self.sd_path))
        self.nro_info = QLabel("")
        self.nro_info.setObjectName("ok")
        self.nro_info.hide()
        src.add(self.nro_info)
        self.content.addWidget(src)

        meta = Card(tr("card_meta"))
        top = QHBoxLayout()
        top.setSpacing(18)
        fields = QGridLayout()
        fields.setHorizontalSpacing(14)
        self.name = QLineEdit()
        self.publisher = QLineEdit("Homebrew")
        self.version = QLineEdit("1.0.0")
        self.tid = QLineEdit(forwarder.random_title_id())
        self.tid.setMaxLength(16)
        rnd = QPushButton(tr("fwd_random"))
        rnd.clicked.connect(lambda: self.tid.setText(forwarder.random_title_id()))
        tid_row = QHBoxLayout()
        tid_row.addWidget(self.tid, 1)
        tid_row.addWidget(rnd)
        tid_w = QWidget()
        tid_w.setLayout(tid_row)
        tid_row.setContentsMargins(0, 0, 0, 0)
        fields.addLayout(labeled(tr("fwd_name"), self.name), 0, 0, 1, 2)
        fields.addLayout(labeled(tr("fwd_publisher"), self.publisher), 1, 0)
        fields.addLayout(labeled(tr("fwd_version"), self.version), 1, 1)
        fields.addLayout(labeled(tr("fwd_titleid"), tid_w), 2, 0, 1, 2)
        top.addLayout(fields, 1)

        self.preview = QLabel(tr("fwd_preview"))
        self.preview.setFixedSize(128, 128)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("border: 1px dashed #2e333f; border-radius: 10px; color: #8b92a3;")
        top.addWidget(self.preview, 0, Qt.AlignTop)
        meta.add(top)

        self.icon = PathPicker("", "file", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        self.icon.changed.connect(self._refresh_preview)
        meta.add(labeled(tr("fwd_icon"), self.icon))
        flags = QHBoxLayout()
        self.ss = QCheckBox(tr("fwd_screenshot"))
        self.ss.setChecked(True)
        self.video = QCheckBox(tr("fwd_video"))
        self.video.setChecked(True)
        self.user = QCheckBox(tr("fwd_user"))
        for w in (self.ss, self.video, self.user):
            flags.addWidget(w)
        flags.addStretch(1)
        meta.add(flags)
        self.content.addWidget(meta)

    def _nro_changed(self, path):
        p = Path(path)
        if not (p.is_file() and p.suffix.lower() == ".nro"):
            return
        self.nro_info.show()
        try:
            info = forwarder.read_nro(p)
        except (OSError, ValueError) as e:
            self.nro_info.setText(str(e))
            return
        self.sd_path.setText(f"sdmc:/switch/{p.name}")
        if info.name:
            self.name.setText(info.name)
        if info.publisher:
            self.publisher.setText(info.publisher)
        if info.version:
            self.version.setText(info.version)
        self._nro_icon = info.icon
        self.nro_info.setText(tr("fwd_read_nro", info.name or p.name))
        self._refresh_preview()

    def _icon_bytes(self):
        if self.icon.value() and Path(self.icon.value()).is_file():
            return forwarder.icon_jpeg(self.icon.value())
        if self._nro_icon:
            return forwarder.icon_jpeg(self._nro_icon)
        return None

    def _refresh_preview(self, *_):
        try:
            data = self._icon_bytes()
        except Exception:
            data = None
        if data:
            pm = QPixmap()
            pm.loadFromData(data)
            self.preview.setPixmap(pm.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.preview.setText(tr("fwd_preview"))

    def tasks(self, outdir):
        name = self.name.text().strip()
        tid = self.tid.text().strip().upper()
        sd = self.sd_path.text().strip()
        if not name:
            raise ops.OpError(tr("fwd_need_name"))
        if not re.fullmatch(r"[0-9A-F]{16}", tid):
            raise ops.OpError(tr("fwd_bad_tid"))
        if not (sd.lower().startswith("sdmc:/") and sd.lower().endswith(".nro")):
            raise ops.OpError(tr("fwd_bad_path"))
        icon = self._icon_bytes()
        if not icon:
            raise ops.OpError(tr("fwd_no_icon"))
        return ops.nro_forwarder(self.cfg, outdir, name=name, publisher=self.publisher.text().strip(),
                                 version=self.version.text().strip(), title_id=tid, sd_path=sd, icon=icon,
                                 screenshot=self.ss.isChecked(), video=self.video.isChecked(),
                                 startup_user=self.user.isChecked())


# ------------------------------------------------------------------ settings / 设置
class SettingsPage(Page):
    title_key = "settings_title"
    has_output = False

    def __init__(self, cfg, submit, on_lang_change):
        self.on_lang_change = on_lang_change
        super().__init__(cfg, submit)

    def build(self):
        c = Card(tr("language"))
        self.lang = QComboBox()
        self.lang.addItem("简体中文", "zh")
        self.lang.addItem("English", "en")
        self.lang.setCurrentIndex(0 if self.cfg["lang"] == "zh" else 1)
        c.add(self.lang)
        self.content.addWidget(c)

        p = Card(tr("card_paths"))
        self.tools = PathPicker(self.cfg["tools_dir"], "dir")
        self.keys = PathPicker(self.cfg["keys"], "file", "Keys (*.keys *.txt *.dat);;* (*)")
        self.output = PathPicker(self.cfg["output_dir"], "dir")
        self.temp = PathPicker(self.cfg["temp_dir"], "dir")
        p.add(labeled(tr("tools_dir"), self.tools))
        p.add(labeled(tr("keys_file"), self.keys))
        p.add(labeled(tr("default_output"), self.output))
        p.add(labeled(tr("temp_dir"), self.temp))
        self.content.addWidget(p)
        self.tools.changed.connect(self._check)
        self.keys.changed.connect(self._check)

        s = Card(tr("tool_status"))
        self.status_grid = QGridLayout()
        s.add(self.status_grid)
        self.content.addWidget(s)
        self._check()

        row = QHBoxLayout()
        row.addStretch(1)
        save = QPushButton(tr("save_settings"))
        save.setObjectName("primary")
        save.clicked.connect(self._save)
        row.addWidget(save)
        self.content.addLayout(row)

    def showEvent(self, e):
        self.output.set_value(self.cfg["output_dir"])
        self.temp.set_value(self.cfg["temp_dir"])
        super().showEvent(e)

    def _check(self, *_):
        while self.status_grid.count():
            self.status_grid.takeAt(0).widget().deleteLater()
        tools = Path(self.tools.value())
        items = [(n, tools / f) for n, f in TOOLS.items()]
        items += [("nro forwarder", tools / "nro_fw_main"), ("fw_nca_mapping.csv", tools / "fw_nca_mapping.csv"),
                  ("prod.keys", Path(self.keys.value()))]
        try:
            import nsz  # noqa: F401
            items.append(("nsz (python)", None))
        except ImportError:
            items.append(("nsz (python)", Path("<missing>")))
        for i, (name, path) in enumerate(items):
            ok = path is None or path.is_file()
            a = QLabel(name)
            b = QLabel(("● " + tr("found")) if ok else ("○ " + tr("not_found")))
            b.setObjectName("ok" if ok else "bad")
            self.status_grid.addWidget(a, i // 2, (i % 2) * 2)
            self.status_grid.addWidget(b, i // 2, (i % 2) * 2 + 1)

    def _save(self):
        old_lang = self.cfg["lang"]
        self.cfg["tools_dir"] = self.tools.value()
        self.cfg["keys"] = self.keys.value()
        self.cfg["output_dir"] = self.output.value()
        self.cfg["temp_dir"] = self.temp.value()
        self.cfg["lang"] = self.lang.currentData()
        self.cfg.save()
        if self.cfg["lang"] != old_lang:
            self.on_lang_change()
        else:
            QMessageBox.information(self, "", tr("saved"))


# ------------------------------------------------------------------ about / 关于
CREDITS = [
    ("Switch Army Knife (SAK)", "kempa / dezem", "https://github.com/dezem/SAK",
     {"zh": "原版工具。NX Toolkit 的功能划分与流程参考了 SAK，界面代码为重新编写，未使用 SAK 的程序代码。",
      "en": "The original tool. NX Toolkit's feature set and workflow follow SAK; the GUI code is rewritten and uses none of SAK's code."}),
    ("4NXCI", "The-4n, SciresM", "https://github.com/The-4n/4NXCI", {"zh": "XCI → NSP", "en": "XCI → NSP"}),
    ("hacBrewPack / hptnacp", "The-4n", "https://github.com/The-4n/hacBrewPack", {"zh": "NRO 转发器 NSP 打包", "en": "Forwarder NSP packing"}),
    ("nx-hbloader (forwarder forks)", "switchbrew, R-YaTian, HookedBehemoth, dezem",
     "https://github.com/switchbrew/nx-hbloader", {"zh": "转发器程序本体", "en": "Forwarder executable"}),
    ("NSC_BUILDER (squirrel)", "julesontheroad", "https://github.com/julesontheroad/NSC_BUILDER",
     {"zh": "NSP → XCI、多内容合并", "en": "NSP → XCI, multi-content merge"}),
    ("LibHac (hactoolnet)", "Thealexbarney", "https://github.com/Thealexbarney/LibHac", {"zh": "固件、存档提取", "en": "Firmware & save extraction"}),
    ("hactool", "SciresM", "https://github.com/SciresM/hactool", {"zh": "NCA 工具", "en": "NCA tooling"}),
    ("nsz", "nicoboss, blawar", "https://github.com/nicoboss/nsz", {"zh": "NSZ / XCZ 压缩解压", "en": "NSZ / XCZ compression"}),
    ("PySide6 (Qt for Python)", "The Qt Company", "https://doc.qt.io/qtforpython/", {"zh": "界面框架（LGPL）", "en": "GUI framework (LGPL)"}),
]


class AboutPage(Page):
    title_key = "about_title"
    has_output = False

    def build(self):
        from .i18n import lang
        intro = Card()
        msg = QLabel({
            "zh": "仅供个人使用。请只处理你合法拥有的游戏，并使用从你自己的主机导出的密钥。\n"
                  "本程序只是外部命令行工具的图形前端；各工具的版权与许可证归其作者所有。",
            "en": "For personal use only. Only process games you legally own, with keys dumped from your own console.\n"
                  "This program is a graphical front-end for external CLI tools; each tool belongs to its authors under its own license.",
        }[lang()])
        msg.setWordWrap(True)
        intro.add(msg)
        self.content.addWidget(intro)
        for name, authors, url, note in CREDITS:
            c = Card()
            t = QLabel(f"<b>{name}</b> &nbsp;<span style='color:#8b92a3'>— {authors}</span>")
            n = QLabel(note[lang()])
            n.setWordWrap(True)
            link = QLabel(f"<a style='color:#19b6ff' href='{url}'>{url}</a>")
            link.setOpenExternalLinks(True)
            for w in (t, n, link):
                c.add(w)
            self.content.addWidget(c)

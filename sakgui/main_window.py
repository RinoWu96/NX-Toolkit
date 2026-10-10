from datetime import datetime

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow,
                               QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QSplitter,
                               QStackedWidget, QVBoxLayout, QWidget)

from . import __version__, pages, theme
from .config import APP_DIR, Config

LOG_DIR = APP_DIR / "logs"
from .i18n import set_lang, tr
from .tasks import TaskRunner

# Glyphs from Segoe Fluent Icons / Segoe MDL2 Assets (ship with Windows 10/11).
# 图标取自 Windows 10/11 自带的 Segoe Fluent Icons / Segoe MDL2 Assets 字体。
NAV = [
    ("", "nav_convert", pages.ConvertPage),
    ("", "nav_merge", pages.MergePage),
    ("", "nav_split", pages.SplitPage),
    ("", "nav_firmware", pages.FirmwarePage),
    ("", "nav_save", pages.SavePage),
    ("", "nav_forwarder", pages.ForwarderPage),
    ("", "nav_settings", pages.SettingsPage),
    ("", "nav_about", pages.AboutPage),
]
_ICON_FONTS = ("Segoe Fluent Icons", "Segoe MDL2 Assets")


def _glyph_icon(ch: str, color: str) -> QIcon:
    pm = QPixmap(40, 40)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    f = QFont()
    f.setFamilies(list(_ICON_FONTS))
    f.setPixelSize(26)
    p.setFont(f)
    p.setPen(QColor(color))
    p.drawText(pm.rect(), Qt.AlignCenter, ch)
    p.end()
    icon = QIcon()
    icon.addPixmap(pm, QIcon.Normal)
    sel = QPixmap(pm.size())
    sel.fill(Qt.transparent)
    p = QPainter(sel)
    p.setFont(f)
    p.setPen(QColor(theme.BLUE))
    p.drawText(sel.rect(), Qt.AlignCenter, ch)
    p.end()
    icon.addPixmap(sel, QIcon.Selected)
    return icon


class MainWindow(QMainWindow):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.runner = TaskRunner(self)
        self.runner.log.connect(self._append_log)
        self.runner.status.connect(lambda s: self.status.setText(s[-160:]))
        self.runner.progress.connect(self._on_progress)
        self.runner.task_started.connect(lambda t: self.status.setText(tr("running", t)))
        self.runner.queue_changed.connect(self._on_queue)
        self.runner.all_done.connect(self._on_done)
        self._pending_rebuild = False
        # Every log line is also kept in logs/nx-toolkit.log so failures can be inspected afterwards.
        # 每行日志也写入 logs/nx-toolkit.log，便于事后排查失败原因。
        LOG_DIR.mkdir(exist_ok=True)
        self._logf = open(LOG_DIR / "nx-toolkit.log", "a", encoding="utf-8")
        self._logf.write(f"\n===== session {datetime.now():%Y-%m-%d %H:%M:%S} =====\n")
        self.resize(1180, 800)
        self.setMinimumSize(960, 640)
        if cfg["geometry"]:
            self.restoreGeometry(QByteArray.fromHex(cfg["geometry"].encode()))
        self._build()
        purged = cfg.purge_stale_temp()
        if purged:
            self._append_log(tr("temp_purged", purged))

    # ---------------------------------------------------------------- layout / 布局
    def _build(self, page_index: int = 0):
        set_lang(self.cfg["lang"])
        self.setWindowTitle(tr("app_title"))
        log_text = self.log.toPlainText() if hasattr(self, "log") else ""

        root = QWidget()
        root.setObjectName("root")
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(220)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(0, 0, 0, 12)
        brand = QLabel("<span style='color:#19b6ff'>●</span> NX Toolkit <span style='color:#ff4f5e'>●</span>")
        brand.setObjectName("brand")
        sub = QLabel(tr("app_subtitle"))
        sub.setObjectName("brandSub")
        sub.setWordWrap(True)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setIconSize(QSize(20, 20))
        for glyph, key, _ in NAV:
            self.nav.addItem(QListWidgetItem(_glyph_icon(glyph, theme.MUTED), "  " + tr(key)))
        sv.addWidget(brand)
        sv.addWidget(sub)
        sv.addWidget(self.nav, 1)
        ver = QLabel(f"v{__version__}")
        ver.setObjectName("brandSub")
        sv.addWidget(ver)

        self.stack = QStackedWidget()
        for _, _, cls in NAV:
            if cls is pages.SettingsPage:
                page = cls(self.cfg, self.submit, self._lang_changed)
            else:
                page = cls(self.cfg, self.submit)
            self.stack.addWidget(page)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)

        # bottom: progress + log / 底部：进度条 + 日志
        bottom = QFrame()
        bottom.setObjectName("card")
        bv = QVBoxLayout(bottom)
        bv.setContentsMargins(14, 10, 14, 12)
        top = QHBoxLayout()
        self.status = QLabel(tr("ready"))
        self.status.setObjectName("status")
        self.queue_lbl = QLabel("")
        self.queue_lbl.setObjectName("status")
        self.cancel_btn = QPushButton(tr("cancel"))
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setEnabled(self.runner.busy())
        self.cancel_btn.clicked.connect(self.runner.cancel)
        clear = QPushButton(tr("clear_log"))
        clear.clicked.connect(lambda: self.log.clear())
        top.addWidget(self.status, 1)
        top.addWidget(self.queue_lbl)
        top.addWidget(clear)
        top.addWidget(self.cancel_btn)
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.log = QPlainTextEdit()
        self.log.setObjectName("log")
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(5000)
        self.log.setPlainText(log_text)
        bv.addLayout(top)
        bv.addWidget(self.bar)
        bv.addWidget(self.log, 1)

        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(12, 0, 12, 12)
        split = QSplitter(Qt.Vertical)
        split.addWidget(self.stack)
        split.addWidget(bottom)
        split.setStretchFactor(0, 4)
        split.setStretchFactor(1, 1)
        split.setSizes([620, 160])
        split.setCollapsible(0, False)
        wl.addWidget(split)

        h.addWidget(side)
        h.addWidget(wrap, 1)
        old = self.centralWidget()
        self.setCentralWidget(root)
        if old is not None:
            old.deleteLater()
        self.nav.setCurrentRow(page_index)

    # ---------------------------------------------------------------- tasks / 任务
    def submit(self, tasks) -> bool:
        self.runner.submit(tasks)
        self.cancel_btn.setEnabled(True)
        return True

    def _append_log(self, text: str):
        try:
            self._logf.write(text + "\n")
            self._logf.flush()
        except (OSError, ValueError):
            pass
        self.log.appendPlainText(text)
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_progress(self, v: int):
        if v < 0:
            self.bar.setRange(0, 0)  # busy animation / 忙碌动画
        else:
            self.bar.setRange(0, 1000)
            self.bar.setValue(v)

    def _on_queue(self, n: int):
        self.queue_lbl.setText(tr("queue_info", n) if n else "")

    def _on_done(self, ok: bool, cancelled: bool):
        self.cancel_btn.setEnabled(False)
        self.bar.setRange(0, 1000)
        self.bar.setValue(1000 if ok else 0)
        msg = tr("cancelled") if cancelled else (tr("done_ok") if ok else tr("done_fail"))
        self.status.setText(msg)
        self._append_log(f"── {msg} ──")
        if self._pending_rebuild:
            self._pending_rebuild = False
            self._build(self.nav.currentRow())

    def _lang_changed(self):
        if self.runner.busy():
            self._pending_rebuild = True
            QMessageBox.information(self, "", tr("lang_busy"))
            return
        self._build(self.nav.currentRow())

    def closeEvent(self, e):
        if self.runner.busy():
            if QMessageBox.question(self, "", tr("quit_busy")) != QMessageBox.Yes:
                e.ignore()
                return
            self.runner.cancel()
        self.cfg["geometry"] = bytes(self.saveGeometry().toHex()).decode()
        self.cfg.save()
        super().closeEvent(e)

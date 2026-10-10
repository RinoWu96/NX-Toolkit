"""Reusable widgets: card container, drag-and-drop file list, path picker.
可复用控件：卡片容器、可拖放的文件列表、路径选择框。"""
from pathlib import Path
from typing import Iterable, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QPushButton, QVBoxLayout, QWidget)

from .i18n import tr


class Card(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(16, 14, 16, 16)
        self.body.setSpacing(10)
        if title:
            t = QLabel(title.upper() if title.isascii() else title)
            t.setObjectName("cardTitle")
            self.body.addWidget(t)

    def add(self, w):
        if isinstance(w, QWidget):
            self.body.addWidget(w)
        else:
            self.body.addLayout(w)
        return w


def _size(p: Path) -> str:
    try:
        if p.is_dir():
            n = sum(f.stat().st_size for f in p.iterdir() if f.is_file())
        else:
            n = p.stat().st_size
    except OSError:
        return ""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return ""


class FileList(QWidget):
    """List of input paths with add/remove/clear and drag-and-drop.
    输入文件列表，支持添加、移除、清空和拖放。"""
    changed = Signal()

    def __init__(self, extensions: Iterable[str], allow_dirs: bool = False, parent=None):
        super().__init__(parent)
        self.exts = tuple(e.lower() for e in extensions)
        self.allow_dirs = allow_dirs
        self.setAcceptDrops(True)

        self.list = QListWidget()
        self.list.setObjectName("files")
        self.list.setSelectionMode(QListWidget.ExtendedSelection)
        self.list.setMinimumHeight(150)
        self.hint = QLabel(tr("drop_hint") + (f"   ({' '.join(self.exts)})" if self.exts else ""))
        self.hint.setObjectName("status")
        self.hint.setAlignment(Qt.AlignCenter)

        add = QPushButton(tr("add_files"))
        add.clicked.connect(self._pick_files)
        rem = QPushButton(tr("remove"))
        rem.clicked.connect(self._remove)
        clr = QPushButton(tr("clear"))
        clr.clicked.connect(self.clear)
        row = QHBoxLayout()
        row.addWidget(add)
        if allow_dirs:
            addd = QPushButton(tr("add_folder"))
            addd.clicked.connect(self._pick_dir)
            row.addWidget(addd)
        row.addStretch(1)
        row.addWidget(rem)
        row.addWidget(clr)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.list)
        lay.addWidget(self.hint)
        lay.addLayout(row)

    # ---- data / 数据
    def paths(self) -> List[str]:
        return [self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]

    def add_paths(self, paths: Iterable[str]):
        have = set(self.paths())
        for s in paths:
            p = Path(s)
            ok = (p.is_file() and (not self.exts or p.suffix.lower() in self.exts)) or (self.allow_dirs and p.is_dir())
            if not ok or str(p) in have:
                continue
            item = QListWidgetItem(f"{p.name}    ·  {_size(p)}")
            item.setData(Qt.UserRole, str(p))
            item.setToolTip(str(p))
            self.list.addItem(item)
            have.add(str(p))
        self._update()

    def clear(self):
        self.list.clear()
        self._update()

    def _remove(self):
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))
        self._update()

    def _update(self):
        self.hint.setVisible(self.list.count() == 0)
        self.changed.emit()

    # ---- dialogs / 对话框
    def _pick_files(self):
        filt = f"Switch ({' '.join(f'*{e}' for e in self.exts)});;* (*)" if self.exts else "* (*)"
        files, _ = QFileDialog.getOpenFileNames(self, tr("add_files"), "", filt)
        self.add_paths(files)

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, tr("add_folder"))
        if d:
            self.add_paths([d])

    # ---- drag and drop / 拖放
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.add_paths(u.toLocalFile() for u in e.mimeData().urls())


class PathPicker(QWidget):
    """Line edit + browse button. mode: 'dir' or 'file'.
    输入框 + 浏览按钮。mode：'dir'（文件夹）或 'file'（文件）。"""
    changed = Signal(str)

    def __init__(self, value: str = "", mode: str = "dir", filt: str = "", parent=None):
        super().__init__(parent)
        self.mode, self.filt = mode, filt
        self.edit = QLineEdit(value)
        self.edit.textChanged.connect(self.changed)
        btn = QPushButton(tr("browse"))
        btn.clicked.connect(self._browse)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.edit, 1)
        lay.addWidget(btn)

    def value(self) -> str:
        return self.edit.text().strip()

    def set_value(self, v: str):
        self.edit.setText(v)

    def _browse(self):
        if self.mode == "dir":
            v = QFileDialog.getExistingDirectory(self, "", self.value())
        else:
            v, _ = QFileDialog.getOpenFileName(self, "", self.value(), self.filt)
        if v:
            self.edit.setText(str(Path(v)))


def labeled(text: str, w: QWidget) -> QVBoxLayout:
    lay = QVBoxLayout()
    lay.setSpacing(4)
    lbl = QLabel(text)
    lbl.setObjectName("status")
    lay.addWidget(lbl)
    lay.addWidget(w)
    return lay

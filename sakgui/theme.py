"""Dark theme. Accent colours borrowed from the neon Joy-Con pair.
深色主题，强调色取自电光蓝 / 电光红 Joy-Con。"""
from PySide6.QtGui import QColor, QPalette

BG = "#14161b"
PANEL = "#1c1f26"
PANEL_2 = "#242832"
BORDER = "#2e333f"
TEXT = "#e6e8ee"
MUTED = "#8b92a3"
BLUE = "#19b6ff"
RED = "#ff4f5e"
GREEN = "#3ddc97"

QSS = f"""
* {{ font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif; font-size: 10pt; color: {TEXT}; }}
QMainWindow, QWidget#root {{ background: {BG}; }}
QWidget#page {{ background: {BG}; }}

/* sidebar */
QFrame#sidebar {{ background: {PANEL}; border-right: 1px solid {BORDER}; }}
QLabel#brand {{ font-size: 15pt; font-weight: 700; padding: 18px 18px 0 18px; }}
QLabel#brandSub {{ color: {MUTED}; font-size: 8.5pt; padding: 2px 18px 14px 18px; }}
QListWidget#nav {{ background: transparent; border: none; outline: none; padding: 4px 8px; }}
QListWidget#nav::item {{ padding: 10px 12px; margin: 2px 0; border-radius: 8px; color: {MUTED}; }}
QListWidget#nav::item:hover {{ background: {PANEL_2}; color: {TEXT}; }}
QListWidget#nav::item:selected {{ background: {PANEL_2}; color: {TEXT};
    border-left: 3px solid {BLUE}; padding-left: 9px; }}

/* page header */
QLabel#pageTitle {{ font-size: 16pt; font-weight: 700; }}
QLabel#pageDesc {{ color: {MUTED}; }}

/* cards */
QFrame#card {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px; }}
QLabel#cardTitle {{ color: {MUTED}; font-size: 9pt; font-weight: 600; letter-spacing: 1px; }}

/* inputs */
QLineEdit, QSpinBox, QComboBox, QPlainTextEdit, QListWidget#files {{
    background: {BG}; border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 8px;
    selection-background-color: {BLUE}; selection-color: #000; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {BLUE}; }}
QListWidget#files {{ padding: 4px; }}
QListWidget#files::item {{ padding: 5px 6px; border-radius: 6px; }}
QListWidget#files::item:selected {{ background: {PANEL_2}; color: {TEXT}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {PANEL}; border: 1px solid {BORDER}; selection-background-color: {PANEL_2}; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 16px; border: none; }}
QPlainTextEdit#log {{ font-family: "Cascadia Mono", "Consolas", monospace; font-size: 9pt; color: #c8ccd6; }}

/* buttons */
QPushButton {{ background: {PANEL_2}; border: 1px solid {BORDER}; border-radius: 8px; padding: 7px 14px; }}
QPushButton:hover {{ border-color: {BLUE}; }}
QPushButton:pressed {{ background: {BORDER}; }}
QPushButton:disabled {{ color: #5a6070; border-color: {PANEL_2}; }}
QPushButton#primary {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {BLUE}, stop:1 #4f7dff);
    color: #04121c; font-weight: 700; border: none; padding: 9px 26px; }}
QPushButton#primary:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4cc7ff, stop:1 #6b92ff); }}
QPushButton#primary:disabled {{ background: {PANEL_2}; color: #5a6070; }}
QPushButton#danger {{ background: transparent; border: 1px solid {RED}; color: {RED}; }}
QPushButton#danger:hover {{ background: {RED}; color: #1a0003; }}
QPushButton#danger:disabled {{ border-color: {PANEL_2}; color: #5a6070; }}

QCheckBox, QRadioButton {{ spacing: 8px; }}
QCheckBox::indicator, QRadioButton::indicator {{ width: 16px; height: 16px; }}
QCheckBox::indicator {{ border: 1px solid {BORDER}; border-radius: 4px; background: {BG}; }}
QCheckBox::indicator:checked {{ background: {BLUE}; border-color: {BLUE}; }}
QRadioButton::indicator {{ border: 1px solid {BORDER}; border-radius: 8px; background: {BG}; }}
QRadioButton::indicator:checked {{ background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
    stop:0 {BLUE}, stop:0.45 {BLUE}, stop:0.55 {BG}, stop:1 {BG}); border-color: {BLUE}; }}

QProgressBar {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 6px; height: 10px; text-align: center; font-size: 8pt; }}
QProgressBar::chunk {{ border-radius: 5px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {BLUE}, stop:1 {RED}); }}

QSplitter::handle {{ background: {BG}; height: 6px; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #3d4352; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar:horizontal {{ height: 0; }}
QToolTip {{ background: {PANEL_2}; color: {TEXT}; border: 1px solid {BORDER}; padding: 4px; }}
QMessageBox {{ background: {PANEL}; }}
QLabel#status {{ color: {MUTED}; }}
QLabel#ok {{ color: {GREEN}; }}
QLabel#bad {{ color: {RED}; }}
"""


def apply(app):
    app.setStyle("Fusion")
    pal = QPalette()
    for role, col in [(QPalette.Window, BG), (QPalette.Base, BG), (QPalette.AlternateBase, PANEL),
                      (QPalette.Text, TEXT), (QPalette.WindowText, TEXT), (QPalette.Button, PANEL_2),
                      (QPalette.ButtonText, TEXT), (QPalette.Highlight, BLUE), (QPalette.HighlightedText, "#000"),
                      (QPalette.ToolTipBase, PANEL_2), (QPalette.ToolTipText, TEXT), (QPalette.PlaceholderText, MUTED)]:
        pal.setColor(role, QColor(col))
    app.setPalette(pal)
    app.setStyleSheet(QSS)

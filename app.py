"""NX Toolkit — entry point.
NX Toolkit —— 程序入口。

When frozen into an exe, the same executable also serves as the nsz command line:
`NX-Toolkit.exe --run-nsz <nsz args>` (there is no separate Python to run `-m nsz`).
打包成 exe 后，同一个可执行文件也充当 nsz 命令行：
`NX-Toolkit.exe --run-nsz <nsz 参数>`（打包后没有独立的 Python 可用来执行 nsz）。
"""
import multiprocessing
import sys


def run_nsz(args):
    # A windowed exe may start without sys.stdout; reattach to the pipe QProcess gave us.
    # 无控制台的 exe 启动时 sys.stdout 可能为空；重新接到 QProcess 提供的管道上。
    if sys.stdout is None:
        sys.stdout = open(1, "w", encoding="utf-8", buffering=1, closefd=False)
    if sys.stderr is None:
        sys.stderr = open(2, "w", encoding="utf-8", buffering=1, closefd=False)
    from nsz import main as nsz_main
    sys.argv = ["nsz", *args]
    nsz_main()


def main():
    from pathlib import Path

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from sakgui import theme
    from sakgui.config import Config
    from sakgui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("NX Toolkit")
    # Bundled files live in sys._MEIPASS when frozen. / 打包后资源文件位于 sys._MEIPASS。
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    app.setWindowIcon(QIcon(str(base / "assets" / "icon.png")))
    theme.apply(app)
    win = MainWindow(Config())
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()  # nsz uses multiprocessing / nsz 使用了多进程
    if len(sys.argv) > 1 and sys.argv[1] == "--run-nsz":
        run_nsz(sys.argv[2:])
    else:
        main()

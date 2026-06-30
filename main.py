import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from qfluentwidgets import setTheme, Theme, qconfig
from gui import MainWindow
import config


if __name__ == '__main__':
    config.HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    qconfig.theme = Theme.DARK
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    setTheme(Theme.DARK)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

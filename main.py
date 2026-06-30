import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from qfluentwidgets import setTheme, Theme, qconfig
from gui import MainWindow, set_dark_palette, GLOBAL_QSS
import config


if __name__ == '__main__':
    config.HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    # HiDPI attributes must be set before QApplication is created
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    qconfig.theme = Theme.DARK
    app = QApplication(sys.argv)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    setTheme(Theme.DARK)

    # 设置全局默认字体（清晰、支持中文）
    default_font = QFont("Microsoft YaHei UI", 9)
    app.setFont(default_font)

    # 强制暗色调色板（覆盖 qfluentwidgets 浅色默认）
    set_dark_palette(app)
    # 应用全局 QSS（确保深色背景生效）
    app.setStyleSheet(GLOBAL_QSS)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

"""主窗口模块。"""
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import FluentWindow


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据分析工具")
        self.resize(1200, 800)
        placeholder = QWidget(self)
        self.addSubInterface(placeholder, None, "占位")

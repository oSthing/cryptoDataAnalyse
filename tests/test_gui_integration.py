"""GUI 集成测试：主窗口与输入区。"""
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from gui import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_creation(qapp):
    window = MainWindow()
    assert window.windowTitle() == "数据分析工具"
    assert window.size().width() == 1200
    assert window.size().height() == 800


def test_input_area_visible(qapp, qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.input_text is not None
    assert window.btn_start is not None
    assert window.btn_import is not None
"""主窗口 + Tab 组件。

应用 8 个样式选择：
- A1 标准暗色（背景 #202020、按钮蓝 #0078d7）
- T1 5 分析 Tab + 日志 Tab
- B3 按钮：Fluent 圆角大（圆角 6px、padding 10×20）
- I3 输入框：#2b2b2b 实色背景
- T2 数据呈现：分组卡片
- B2 模式徽章：透明描边
- P1 进度条：蓝色细线 4px
- TY2 排版：宽松 + 中字号

关键修复：使用 QApplication.setStyleSheet 全局应用 QSS，
确保 qfluentwidgets 主题覆盖不掉我们的样式。
"""
from pathlib import Path
from typing import List, Optional
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QFont, QPalette, QColor, QTextCursor
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QScrollArea, QTextEdit,
    QVBoxLayout, QWidget, QCheckBox,
)
from qfluentwidgets import (
    FluentWindow, PushButton, PrimaryPushButton, ProgressBar, SpinBox,
    InfoBar, setTheme, Theme, FluentIcon as FIF, setThemeColor,
)

import config
from workers import AnalyzerWorker
from analyzer.history import History
from analyzer.chunking import ChunkingConfig
from exporters import to_json, to_markdown


# ===== 样式常量（A1 主色 + TY2 排版）=====
COLOR_BG = "#202020"
COLOR_BG_RAISED = "#2b2b2b"
COLOR_BORDER = "#3a3a3a"
COLOR_BTN_SECONDARY = "#3a3a3a"
COLOR_ACCENT = "#0078d7"
COLOR_TEXT = "#ffffff"
COLOR_TEXT_DIM = "#dddddd"
COLOR_TEXT_MUTED = "#888888"
COLOR_GREEN = "#6cc04a"
COLOR_CYAN = "#4cc2ff"
COLOR_PURPLE = "#b478ff"
COLOR_ORANGE = "#ff8c00"
COLOR_RED = "#ff6b6b"
COLOR_YELLOW = "#f7b500"

FONT_FAMILY = "Microsoft YaHei UI"  # 跨 Windows 版本通用，且支持中文
FONT_MONO = "Consolas"  # 等宽字体用于输入/日志；Windows 自带

FONT_SIZE_TITLE = 18
FONT_SIZE_SUBTITLE = 13
FONT_SIZE_BODY = 12
FONT_SIZE_LABEL = 11
FONT_SIZE_BADGE = 11

GROUP_RADIUS = 8
BADGE_RADIUS = 3
BUTTON_RADIUS = 6

# 全局 QSS：暗色 + 强制深色背景
# 注意：使用 QApplication.setStyleSheet 而非 widget.setStyleSheet，
# 避免 qfluentwidgets 主题覆盖。
GLOBAL_QSS = f"""
QWidget {{
    color: {COLOR_TEXT};
    background-color: {COLOR_BG};
}}
/* 所有文字可选中：QLabel 默认不可选，强制开启 TextSelectableByMouse */
QLabel {{
    color: {COLOR_TEXT};
    background: transparent;
    selection-background-color: {COLOR_ACCENT};
    selection-color: {COLOR_TEXT};
}}
QCheckBox {{
    color: {COLOR_TEXT};
    background: transparent;
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    background: {COLOR_BG_RAISED};
    border: 1px solid {COLOR_CYAN};
    border-radius: 2px;
}}
QCheckBox::indicator:checked {{ background: {COLOR_CYAN}; }}
QScrollArea, QWidget#view {{
    background-color: {COLOR_BG};
    border: none;
}}
/* Windows 原生滚动条样式 */
QScrollBar:vertical {{
    background: {COLOR_BG};
    width: 16px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: #5a5a5a;
    min-height: 24px;
    border: 2px solid {COLOR_BG};
    border-radius: 0px;
}}
QScrollBar::handle:vertical:hover {{
    background: #7a7a7a;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    background: none;
    height: 0;
    border: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    background: {COLOR_BG};
    height: 16px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: #5a5a5a;
    min-width: 24px;
    border: 2px solid {COLOR_BG};
    border-radius: 0px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #7a7a7a;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    background: none;
    width: 0;
    border: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}
QTextEdit, QPlainTextEdit {{
    background-color: {COLOR_BG_RAISED};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 8px;
    selection-background-color: {COLOR_ACCENT};
    selection-color: {COLOR_TEXT};
}}
QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {COLOR_ACCENT}; }}
SpinBox, QSpinBox {{
    background: {COLOR_BG_RAISED};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 2px;
}}
SpinBox:focus, QSpinBox:focus {{ border: 1px solid {COLOR_ACCENT}; }}
SpinBox QLineEdit, QSpinBox QLineEdit {{
    background-color: {COLOR_BG_RAISED};
    color: {COLOR_TEXT};
    border: none;
    padding: 4px 6px;
}}
QProgressBar {{
    background: {COLOR_BG_RAISED};
    border: none;
    height: 4px;
    border-radius: 2px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {COLOR_ACCENT};
    border-radius: 2px;
}}
QPushButton {{
    background-color: {COLOR_BTN_SECONDARY};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: {BUTTON_RADIUS}px;
    padding: 8px 18px;
    font-family: {FONT_FAMILY};
}}
QPushButton:hover {{ background-color: #4a4a4a; }}
QPushButton:pressed {{ background-color: #2a2a2a; }}
QPushButton:disabled {{ color: #666; background: #2a2a2a; }}
PrimaryPushButton {{
    background-color: {COLOR_ACCENT};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_ACCENT};
    border-radius: {BUTTON_RADIUS}px;
    padding: 8px 18px;
    font-family: {FONT_FAMILY};
    font-weight: 500;
}}
PrimaryPushButton:hover {{ background-color: #1a86d9; }}
PrimaryPushButton:pressed {{ background-color: #006bbd; }}
PrimaryPushButton:disabled {{ background: #2a4a6a; color: #888; }}
QFrame {{
    background-color: rgba(255, 255, 255, 0.05);
    border: none;
}}
QStatusBar {{
    background: {COLOR_BG};
    color: {COLOR_TEXT};
}}
"""


def make_badge(text: str, color: str) -> QLabel:
    """B2 模式徽章：透明背景 + 彩色描边和文字。"""
    badge = QLabel(text)
    badge.setStyleSheet(
        f"QLabel {{"
        f"  background: transparent;"
        f"  color: {color};"
        f"  border: 1px solid {color};"
        f"  border-radius: 3px;"
        f"  padding: 2px 8px;"
        f"  font-size: {FONT_SIZE_BADGE}px;"
        f"  font-family: {FONT_FAMILY};"
        f"}}"
    )
    return badge


def make_selectable_label(text: str, style: str = "") -> QLabel:
    """创建文字可选中的 QLabel。"""
    lbl = QLabel(text)
    if style:
        lbl.setStyleSheet(style)
    lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return lbl


def style_button(btn, is_primary: bool = False):
    """B3 圆角大按钮：覆盖 qfluentwidgets 默认浅色 QSS。"""
    if is_primary:
        bg = COLOR_ACCENT
        bg_hover = "#1a86d9"
        bg_pressed = "#006bbd"
        border = COLOR_ACCENT
    else:
        bg = COLOR_BTN_SECONDARY
        bg_hover = "#4a4a4a"
        bg_pressed = "#1a1a1a"
        border = COLOR_BORDER
    btn.setStyleSheet(
        f"QPushButton {{"
        f"  color: {COLOR_TEXT};"
        f"  background: {bg};"
        f"  border: 1px solid {border};"
        f"  border-radius: {BUTTON_RADIUS}px;"
        f"  padding: 8px 18px;"
        f"  font-family: {FONT_FAMILY};"
        f"  font-weight: 500;"
        f"}}"
        f"QPushButton:hover {{ background: {bg_hover}; }}"
        f"QPushButton:pressed {{ background: {bg_pressed}; }}"
        f"QPushButton:disabled {{ color: #666; background: #2a2a2a; }}"
    )


def make_group_frame() -> QFrame:
    """T2 分组卡片：半透明白背景。"""
    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame {{"
        f"  background: rgba(255, 255, 255, 0.05);"
        f"  border-radius: {GROUP_RADIUS}px;"
        f"  padding: 12px;"
        f"  border: none;"
        f"}}"
    )
    return frame


def set_dark_palette(app):
    """强制设置 QApplication 调色板为暗色，覆盖 qfluentwidgets 默认浅色。"""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLOR_BG))
    palette.setColor(QPalette.WindowText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.Base, QColor(COLOR_BG_RAISED))
    palette.setColor(QPalette.AlternateBase, QColor(COLOR_BG))
    palette.setColor(QPalette.ToolTipBase, QColor(COLOR_BG_RAISED))
    palette.setColor(QPalette.ToolTipText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.Text, QColor(COLOR_TEXT))
    palette.setColor(QPalette.Button, QColor(COLOR_BG_RAISED))
    palette.setColor(QPalette.ButtonText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.BrightText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.Link, QColor(COLOR_ACCENT))
    palette.setColor(QPalette.Highlight, QColor(COLOR_ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor(COLOR_TEXT))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#666666"))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#666666"))
    app.setPalette(palette)


class StringCard(QFrame):
    """单条字符串的分析结果卡片。"""

    def __init__(self, index: int, raw: str, basic_features: dict, patterns: list, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{"
            f"  background: rgba(255, 255, 255, 0.05);"
            f"  border-radius: {GROUP_RADIUS}px;"
            f"  padding: 12px;"
            f"  border: none;"
            f"}}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 头部：索引 + 原始字符串预览
        preview = raw if len(raw) <= 60 else raw[:60] + "..."
        header = QLabel(f"字符串 {index + 1} · {preview}")
        header.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_LABEL}px; font-family: {FONT_FAMILY};"
        )
        header.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(header)

        # 基本特征行
        features_layout = QHBoxLayout()
        features_layout.setSpacing(16)
        cc = basic_features.get("char_classes", {}) if isinstance(basic_features, dict) else {}
        for label, key in [("长度", "length"), ("唯一字符", "unique_chars"),
                            ("大写", "upper"), ("小写", "lower"), ("数字", "digit")]:
            if key in ("upper", "lower", "digit"):
                value = str(cc.get(key, 0))
            else:
                value = str(basic_features.get(key, 0))
            col = QVBoxLayout()
            col.setSpacing(2)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; background: transparent;")
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            val = QLabel(value)
            val.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 13px; background: transparent;")
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            col.addWidget(lbl)
            col.addWidget(val)
            wrap = QWidget()
            wrap.setLayout(col)
            features_layout.addWidget(wrap)
        features_layout.addStretch()
        features_wrap = QWidget()
        features_wrap.setLayout(features_layout)
        layout.addWidget(features_wrap)

        # 模式徽章行
        if patterns:
            badges_layout = QHBoxLayout()
            badges_layout.setSpacing(4)
            badges_layout.setContentsMargins(0, 0, 0, 0)
            color_map = {
                "Hex": COLOR_CYAN, "Base64": COLOR_GREEN, "Base32": COLOR_GREEN, "Base58": COLOR_GREEN,
                "UUID": COLOR_CYAN, "MD5": COLOR_PURPLE, "SHA-1": COLOR_PURPLE, "SHA-224": COLOR_PURPLE,
                "SHA-256": COLOR_PURPLE, "SHA-384": COLOR_PURPLE, "SHA-512": COLOR_PURPLE, "NTLM": COLOR_PURPLE,
                "bcrypt": COLOR_PURPLE, "Argon2": COLOR_PURPLE,
                "Unix时间戳(秒)": COLOR_ORANGE, "Unix时间戳(毫秒)": COLOR_ORANGE,
                "Windows FILETIME": COLOR_ORANGE, "ISO 8601": COLOR_ORANGE,
                "IPv4": COLOR_CYAN, "IPv6": COLOR_CYAN, "MAC": COLOR_CYAN,
                "邮箱": COLOR_TEXT_MUTED, "URL": COLOR_TEXT_MUTED,
                "JSON": COLOR_GREEN, "XML": COLOR_GREEN, "JWT": COLOR_GREEN, "ASN.1 DER": COLOR_GREEN,
                "RSA公钥PEM": COLOR_YELLOW, "RSA私钥PEM": COLOR_YELLOW, "EC私钥PEM": COLOR_YELLOW,
                "PKCS#8私钥PEM": COLOR_YELLOW, "PGP块": COLOR_YELLOW, "X.509证书": COLOR_YELLOW,
                "SSH公钥": COLOR_YELLOW, "Ethereum地址": COLOR_YELLOW, "Bitcoin地址": COLOR_YELLOW,
                "Monero地址": COLOR_YELLOW, "IPFS CID": COLOR_YELLOW,
                "ECB模式提示": COLOR_RED, "CBC IV候选": COLOR_RED, "AES密钥候选": COLOR_RED,
                "DES密钥候选": COLOR_RED, "PKCS#7填充": COLOR_RED,
                "高熵(像随机数/密钥/加密输出)": COLOR_RED, "低熵(含重复模式)": COLOR_ORANGE,
                "全数字": COLOR_TEXT_DIM, "全字母": COLOR_TEXT_DIM,
                "全大写": COLOR_TEXT_DIM, "全小写": COLOR_TEXT_DIM,
                "可打印ASCII": COLOR_TEXT_DIM, "含中文": COLOR_TEXT_DIM,
            }
            for p in patterns:
                color = color_map.get(p, COLOR_TEXT_DIM)
                badges_layout.addWidget(make_badge(p, color))
            badges_layout.addStretch()
            badges_wrap = QWidget()
            badges_wrap.setLayout(badges_layout)
            layout.addWidget(badges_wrap)


class AnalysisInterface(QScrollArea):
    """主分析界面：输入区 + 按钮 + 进度 + 结果卡片。"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.layout = QVBoxLayout(self.view)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(14)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setObjectName("AnalysisInterface")
        self.view.setObjectName("view")

        # 标题
        self.title_label = QLabel("字符串分析", self)
        self.title_label.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_TITLE}px;"
            f" font-weight: 500; font-family: {FONT_FAMILY}; background: transparent;"
        )
        self.layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("基本特征", self)
        self.subtitle_label.setStyleSheet(
            f"color: {COLOR_CYAN}; font-size: {FONT_SIZE_SUBTITLE}px;"
            f" font-family: {FONT_FAMILY}; background: transparent;"
        )
        self.layout.addWidget(self.subtitle_label)

        # 输入分组
        input_group = make_group_frame()
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        input_label = QLabel("输入数据（每行一条字符串）", self)
        input_label.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_BODY}px; font-weight: 500;"
        )
        input_layout.addWidget(input_label)

        self.input_text = QTextEdit(self)
        self.input_text.setPlaceholderText("在此输入要分析的字符串，每行一条...")
        self.input_text.setMinimumHeight(100)
        font = QFont(FONT_MONO)
        font.setPointSize(10)
        self.input_text.setFont(font)
        # I3 深色输入框：直接 setStyleSheet 覆盖
        self.input_text.setStyleSheet(
            f"QTextEdit {{"
            f"  background: {COLOR_BG_RAISED};"
            f"  color: {COLOR_TEXT};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 4px;"
            f"  padding: 8px;"
            f"  selection-background-color: {COLOR_ACCENT};"
            f"  selection-color: {COLOR_TEXT};"
            f"}}"
            f"QTextEdit:focus {{ border: 1px solid {COLOR_ACCENT}; }}"
        )
        input_layout.addWidget(self.input_text)

        self.hex_checkbox = QCheckBox("输入是 Hex 字符串（按字节切分）", self)
        input_layout.addWidget(self.hex_checkbox)

        self.layout.addWidget(input_group)

        # 分块配置行
        chunk_layout = QHBoxLayout()
        chunk_layout.setSpacing(8)
        for label, attr_name, default in [
            ("分块长度", "chunk_size_spin", config.DEFAULT_CHUNK_SIZE),
            ("窗口大小", "window_size_spin", config.DEFAULT_WINDOW_SIZE),
            ("步长", "window_step_spin", config.DEFAULT_WINDOW_STEP),
        ]:
            lbl = QLabel(label, self)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: {FONT_SIZE_BODY}px; background: transparent;")
            chunk_layout.addWidget(lbl)
            spin = SpinBox(self)
            spin.setRange(1, 1024)
            spin.setValue(default)
            spin.setFixedWidth(80)
            # I3 深色 SpinBox
            spin.setStyleSheet(
                f"QSpinBox {{"
                f"  background: {COLOR_BG_RAISED};"
                f"  color: {COLOR_TEXT};"
                f"  border: 1px solid {COLOR_BORDER};"
                f"  border-radius: 4px;"
                f"  padding: 4px 6px;"
                f"  selection-background-color: {COLOR_ACCENT};"
                f"}}"
                f"QSpinBox::up-button, QSpinBox::down-button {{"
                f"  background: {COLOR_BG_RAISED};"
                f"  border: none;"
                f"  width: 16px;"
                f"}}"
                f"QSpinBox:focus {{ border: 1px solid {COLOR_ACCENT}; }}"
            )
            setattr(self, attr_name, spin)
            chunk_layout.addWidget(spin)
            chunk_layout.addSpacing(12)
        chunk_layout.addStretch()
        self.layout.addLayout(chunk_layout)

        # 按钮行（B3 圆角大）
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        self.btn_start = PrimaryPushButton("开始分析", self)
        self.btn_stop = PushButton("停止", self)
        self.btn_import = PushButton("从文件导入", self)
        self.btn_clear = PushButton("清空", self)
        self.btn_export_json = PushButton("导出 JSON", self)
        self.btn_export_md = PushButton("导出 Markdown", self)
        self.btn_stop.setEnabled(False)

        for btn in [self.btn_start, self.btn_stop, self.btn_import, self.btn_clear,
                     self.btn_export_json, self.btn_export_md]:
            btn.setMinimumHeight(36)
            button_layout.addWidget(btn)
        button_layout.addStretch()
        # 覆盖 qfluentwidgets 内部 QSS，应用深色 B3 风格
        style_button(self.btn_start, is_primary=True)
        for btn in [self.btn_stop, self.btn_import, self.btn_clear,
                     self.btn_export_json, self.btn_export_md]:
            style_button(btn, is_primary=False)
        self.layout.addLayout(button_layout)

        # 进度条（P1 蓝色细线）
        self.progress_label = QLabel("", self)
        self.progress_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_LABEL}px;"
            f" font-family: {FONT_FAMILY}; background: transparent;"
        )
        self.layout.addWidget(self.progress_label)

        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 8)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.layout.addWidget(self.progress_bar)

        # 结果区
        self.result_title = QLabel("分析结果", self)
        self.result_title.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 500;"
            f" margin-top: 6px; background: transparent;"
        )
        self.layout.addWidget(self.result_title)

        self.result_container = QWidget(self)
        self.result_layout = QVBoxLayout(self.result_container)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_layout.setSpacing(8)
        self.result_layout.addStretch()
        self.layout.addWidget(self.result_container)

        # 状态
        self.status_label = QLabel("就绪", self)
        self.status_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_LABEL}px; font-family: {FONT_FAMILY}; background: transparent;"
        )
        self.layout.addWidget(self.status_label)

        self.layout.addStretch()

    def clear_results(self):
        while self.result_layout.count() > 1:
            item = self.result_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def populate_results(self, basic_features_list, patterns_list, raw_inputs):
        self.clear_results()
        for i, (bf, pats, raw) in enumerate(zip(basic_features_list, patterns_list, raw_inputs)):
            bf_dict = bf.__dict__ if hasattr(bf, "__dict__") else bf
            card = StringCard(i, raw, bf_dict, pats, self)
            self.result_layout.insertWidget(self.result_layout.count() - 1, card)


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据分析工具")
        self.resize(1200, 800)

        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[AnalyzerWorker] = None
        self.current_result: Optional[dict] = None
        self.history = History(config.HISTORY_FILE, max_entries=config.HISTORY_MAX_ENTRIES)

        # 5 个 Tab
        self.tab_basic = self._create_basic_tab()
        self.tab_common = self._create_common_substring_tab()
        self.tab_chunk = self._create_chunk_tab()
        self.tab_diff = self._create_diff_tab()
        self.tab_log = self._create_log_tab()

        self.addSubInterface(self.tab_basic, FIF.SEARCH, "基本特征")
        self.addSubInterface(self.tab_common, FIF.LINK, "公共子串")
        self.addSubInterface(self.tab_chunk, FIF.CUT, "分块分析")
        self.addSubInterface(self.tab_diff, FIF.SEND, "差异比对")
        self.addSubInterface(self.tab_log, FIF.DOCUMENT, "日志")

        # 暴露属性给测试
        self.input_text = self.tab_basic.input_text
        self.hex_checkbox = self.tab_basic.hex_checkbox
        self.chunk_size_spin = self.tab_basic.chunk_size_spin
        self.window_size_spin = self.tab_basic.window_size_spin
        self.window_step_spin = self.tab_basic.window_step_spin
        self.btn_start = self.tab_basic.btn_start
        self.btn_stop = self.tab_basic.btn_stop
        self.btn_import = self.tab_basic.btn_import
        self.btn_clear = self.tab_basic.btn_clear
        self.btn_export_json = self.tab_basic.btn_export_json
        self.btn_export_md = self.tab_basic.btn_export_md
        self.progress_bar = self.tab_basic.progress_bar
        self.status_label = self.tab_basic.status_label
        self.log_text = self.tab_log.log_text

        # 信号连接
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_import.clicked.connect(self._on_import_clicked)
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        self.btn_export_json.clicked.connect(lambda: self._on_export_clicked("json"))
        self.btn_export_md.clicked.connect(lambda: self._on_export_clicked("md"))

    def _create_basic_tab(self) -> AnalysisInterface:
        return AnalysisInterface(self)

    def _create_log_tab(self) -> QWidget:
        widget = QScrollArea(self)
        widget.setObjectName("LogInterface")
        view = QWidget(widget)
        view.setObjectName("view")
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        widget.setWidget(view)
        widget.setWidgetResizable(True)
        widget.setStyleSheet("QScrollArea, QWidget#view { background: transparent; }")

        title = QLabel("运行日志", widget)
        title.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_TITLE}px;"
            f" font-weight: 500; background: transparent;"
        )
        layout.addWidget(title)

        log_group = make_group_frame()
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(0, 0, 0, 0)
        widget.log_text = QTextEdit(widget)
        widget.log_text.setReadOnly(True)
        font = QFont(FONT_MONO)
        font.setPointSize(10)
        widget.log_text.setFont(font)
        widget.log_text.setMinimumHeight(500)
        # I3 深色日志区
        widget.log_text.setStyleSheet(
            f"QTextEdit {{"
            f"  background: {COLOR_BG_RAISED};"
            f"  color: {COLOR_TEXT_DIM};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 4px;"
            f"  padding: 8px;"
            f"  selection-background-color: {COLOR_ACCENT};"
            f"}}"
        )
        log_layout.addWidget(widget.log_text)
        layout.addWidget(log_group)

        self.log_text = widget.log_text
        return widget

    def _create_common_substring_tab(self) -> QWidget:
        """Tab 2: 公共子串/子序列。"""
        widget = QScrollArea(self)
        widget.setObjectName("CommonSubstringInterface")
        view = QWidget(widget)
        view.setObjectName("view")
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        widget.setWidget(view)
        widget.setWidgetResizable(True)
        widget.setStyleSheet("QScrollArea, QWidget#view { background: transparent; }")

        title = QLabel("公共子串 / 子序列", widget)
        title.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_TITLE}px;"
            f" font-weight: 500; background: transparent;"
        )
        layout.addWidget(title)

        # 检索行：最小长度
        filter_layout = QHBoxLayout()
        filter_label = QLabel("最小长度:", widget)
        filter_label.setStyleSheet(
            f"color: {COLOR_TEXT_DIM}; font-size: {FONT_SIZE_BODY}px; background: transparent;"
        )
        filter_layout.addWidget(filter_label)

        widget.min_length_spin = SpinBox(widget)
        widget.min_length_spin.setRange(1, 1024)
        widget.min_length_spin.setValue(1)
        widget.min_length_spin.setFixedWidth(80)
        widget.min_length_spin.setStyleSheet(
            f"QSpinBox {{"
            f"  background: {COLOR_BG_RAISED};"
            f"  color: {COLOR_TEXT};"
            f"  border: 1px solid {COLOR_BORDER};"
            f"  border-radius: 4px;"
            f"  padding: 4px 6px;"
            f"}}"
            f"QSpinBox::up-button, QSpinBox::down-button {{"
            f"  background: {COLOR_BG_RAISED};"
            f"  border: none;"
            f"  width: 16px;"
            f"}}"
            f"QSpinBox:focus {{ border: 1px solid {COLOR_ACCENT}; }}"
        )
        filter_layout.addWidget(widget.min_length_spin)
        filter_layout.addStretch()

        widget.apply_btn = PushButton("应用筛选", widget)
        style_button(widget.apply_btn, is_primary=True)
        widget.apply_btn.setMinimumHeight(28)
        widget.apply_btn.clicked.connect(self._apply_common_substring_filter)
        filter_layout.addWidget(widget.apply_btn)

        layout.addLayout(filter_layout)

        widget.content_layout = QVBoxLayout()
        widget.content_layout.setSpacing(10)
        content_wrap = QWidget(widget)
        content_wrap.setLayout(widget.content_layout)
        layout.addWidget(content_wrap)
        layout.addStretch()

        return widget

    def _apply_common_substring_filter(self):
        """根据当前 min_length 重新过滤并显示公共子串。"""
        if not self.current_result:
            return
        inputs = self.current_result.get("inputs", [])
        # 重新计算
        min_length = self.tab_common.min_length_spin.value()
        from analyzer.common_substring import analyze as cs_analyze
        cs_result = cs_analyze(inputs, min_length=min_length)
        cs_data = {
            "pairwise": {f"{i},{j}": v for (i, j), v in cs_result.pairwise.items()},
            "multi": cs_result.multi,
            "common_prefix": cs_result.common_prefix,
            "common_suffix": cs_result.common_suffix,
            "all_pairwise": {f"{i},{j}": v for (i, j), v in cs_result.all_pairwise.items()},
            "all_multi": cs_result.all_multi,
        }
        repeat_data = self.current_result.get("repeat_substring", [])
        self._populate_common_substring_tab(cs_data, inputs, repeat_data=repeat_data)

    def _populate_common_substring_tab(self, cs_data: dict, raw_inputs: list,
                                       repeat_data: list = None):
        """填充公共子串 Tab 内容。

        显示 4 部分：
        0. 单串内重复最多的子串（每条字符串一张卡片）
        1. 公共前缀/后缀
        2. 所有公共子串（按 min_length 过滤，all_pairwise + all_multi）
        3. 最长公共子串（pairwise + multi）
        """
        if not hasattr(self.tab_common, 'content_layout'):
            return
        layout = self.tab_common.content_layout
        # 清空现有内容
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # 0. 单串内重复最多的子串
        if repeat_data:
            for entry in repeat_data:
                idx = entry.get("index", 0)
                subs_data = entry.get("substrings", [])
                if not subs_data:
                    continue
                raw = raw_inputs[idx] if idx < len(raw_inputs) else ""
                preview = raw if len(raw) <= 50 else raw[:50] + "..."
                repeat_card = self._make_info_card(
                    f"串{idx+1} 内重复子串 · {preview}",
                    f"共 {len(subs_data)} 个子串出现 ≥ 2 次"
                )
                for sub_info in subs_data[:30]:  # 限制显示前 30
                    sub = sub_info["sub"]
                    count = sub_info["count"]
                    positions = sub_info["positions"]
                    pos_str = ", ".join(str(p) for p in positions[:8])
                    if len(positions) > 8:
                        pos_str += f" ... +{len(positions) - 8}"
                    style = (f"color: {COLOR_ORANGE}; font-family: {FONT_MONO};"
                             f" font-size: 11px; background: transparent; padding: 1px 0;")
                    line = make_selectable_label(
                        f"  次数 {count:3d}  长度{len(sub):3d}  `{sub}`  (位置: {pos_str})",
                        style
                    )
                    line.setParent(repeat_card)
                    repeat_card.layout().addWidget(line)
                if len(subs_data) > 30:
                    more = make_selectable_label(
                        f"  ... 还有 {len(subs_data) - 30} 个",
                        f"color: {COLOR_TEXT_MUTED}; font-style: italic;"
                        f" font-size: 11px; background: transparent;"
                    )
                    more.setParent(repeat_card)
                    repeat_card.layout().addWidget(more)
                layout.addWidget(repeat_card)

        # 公共前缀/后缀
        prefix = cs_data.get("common_prefix", 0)
        suffix = cs_data.get("common_suffix", 0)
        if prefix > 0 or suffix > 0:
            card = self._make_info_card(
                "公共前缀 / 后缀",
                f"公共前缀长度: {prefix}    公共后缀长度: {suffix}"
            )
            layout.addWidget(card)

        # 解析 all_pairwise（key 形如 "0,1"）
        all_pairwise = cs_data.get("all_pairwise", {})
        # key 是 "i,j" 字符串，需解析
        parsed_all_pairwise = {}
        for k, v in all_pairwise.items():
            i, j = k.split(",")
            parsed_all_pairwise[(int(i), int(j))] = v
        all_multi = cs_data.get("all_multi", [])

        # 全部公共子串（多串）
        if all_multi:
            multi_card = self._make_info_card(f"全部公共子串（多串 · {len(all_multi)} 个）", "")
            for sub, positions in all_multi:
                pos_str = ", ".join(f"串{i+1}@{p}" for i, p in enumerate(positions))
                style = (f"color: {COLOR_TEXT_DIM}; font-family: {FONT_MONO};"
                         f" font-size: 12px; background: transparent; padding: 2px 0;")
                line = make_selectable_label(
                    f"  · 长度{len(sub):3d}  `{sub}`  (位置: {pos_str})",
                    style
                )
                line.setParent(multi_card)
                multi_card.layout().addWidget(line)
            layout.addWidget(multi_card)

        # 全部公共子串（两两）
        if parsed_all_pairwise:
            for (i, j), subs in sorted(parsed_all_pairwise.items()):
                if not subs:
                    continue
                pair_card = self._make_info_card(
                    f"全部公共子串 · 串{i+1} ↔ 串{j+1} ({len(subs)} 个)",
                    ""
                )
                # 限制显示前 100 个，避免太长
                for sub, pos_i, pos_j in subs[:100]:
                    style = (f"color: {COLOR_TEXT_DIM}; font-family: {FONT_MONO};"
                             f" font-size: 11px; background: transparent; padding: 1px 0;")
                    line = make_selectable_label(
                        f"  长度{len(sub):3d}  `{sub}`  (串{i+1}@{pos_i}, 串{j+1}@{pos_j})",
                        style
                    )
                    line.setParent(pair_card)
                    pair_card.layout().addWidget(line)
                if len(subs) > 100:
                    more = make_selectable_label(
                        f"  ... 还有 {len(subs) - 100} 个",
                        f"color: {COLOR_TEXT_MUTED}; font-style: italic;"
                        f" font-size: 11px; background: transparent;"
                    )
                    more.setParent(pair_card)
                    pair_card.layout().addWidget(more)
                layout.addWidget(pair_card)

        # 最长公共子串（多串）
        multi = cs_data.get("multi", [])
        if multi:
            multi_card = self._make_info_card(f"最长公共子串（多串 · {len(multi)} 个）", "")
            for sub, positions in multi:
                pos_str = ", ".join(f"串{i+1}@{p}" for i, p in enumerate(positions))
                style = (f"color: {COLOR_CYAN}; font-family: {FONT_MONO};"
                         f" font-size: 12px; background: transparent; padding: 2px 0;")
                line = make_selectable_label(
                    f"  · 长度{len(sub):3d}  `{sub}`  (位置: {pos_str})",
                    style
                )
                line.setParent(multi_card)
                multi_card.layout().addWidget(line)
            layout.addWidget(multi_card)

        # 最长公共子串（两两）
        pairwise = cs_data.get("pairwise", {})
        if pairwise:
            for key, subs in sorted(pairwise.items()):
                i, j = key.split(",")
                i, j = int(i), int(j)
                if subs:
                    pair_card = self._make_info_card(
                        f"最长公共子串 · 串{i+1} ↔ 串{j+1}",
                        ""
                    )
                    for sub, pos_i, pos_j in subs[:5]:
                        style = (f"color: {COLOR_CYAN}; font-family: {FONT_MONO};"
                                 f" font-size: 12px; background: transparent; padding: 2px 0;")
                        line = make_selectable_label(
                            f"  长度{len(sub):3d}  `{sub}`  (串{i+1}@{pos_i}, 串{j+1}@{pos_j})",
                            style
                        )
                        line.setParent(pair_card)
                        pair_card.layout().addWidget(line)
                    if len(subs) > 5:
                        more = make_selectable_label(
                            f"  ... +{len(subs) - 5} more (长度相同)",
                            f"color: {COLOR_TEXT_MUTED}; font-style: italic;"
                            f" font-size: 11px; background: transparent;"
                        )
                        more.setParent(pair_card)
                        pair_card.layout().addWidget(more)
                    layout.addWidget(pair_card)
                else:
                    card = self._make_info_card(
                        f"串{i+1} ↔ 串{j+1}",
                        "  (无公共子串)"
                    )
                    layout.addWidget(card)

        if not (prefix > 0 or suffix > 0 or all_multi or parsed_all_pairwise
                or multi or pairwise):
            empty = make_selectable_label(
                "(无公共子串数据)",
                f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_BODY}px; background: transparent;"
            )
            empty.setParent(self.tab_common)
            layout.addWidget(empty)

    def _create_chunk_tab(self) -> QWidget:
        """Tab 3: 分块分析。"""
        widget = QScrollArea(self)
        widget.setObjectName("ChunkingInterface")
        view = QWidget(widget)
        view.setObjectName("view")
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        widget.setWidget(view)
        widget.setWidgetResizable(True)
        widget.setStyleSheet("QScrollArea, QWidget#view { background: transparent; }")

        title = QLabel("分块分析", widget)
        title.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_TITLE}px;"
            f" font-weight: 500; background: transparent;"
        )
        layout.addWidget(title)

        widget.content_layout = QVBoxLayout()
        widget.content_layout.setSpacing(10)
        content_wrap = QWidget(widget)
        content_wrap.setLayout(widget.content_layout)
        layout.addWidget(content_wrap)
        layout.addStretch()

        return widget

    def _populate_chunk_tab(self, chunk_data: dict, raw_inputs: list):
        """填充分块 Tab 内容。"""
        if not hasattr(self.tab_chunk, 'content_layout'):
            return
        layout = self.tab_chunk.content_layout
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        chunks_by_idx = chunk_data.get("chunks", {})
        duplicates = chunk_data.get("duplicates", {})

        if not chunks_by_idx:
            empty = make_selectable_label(
                "(无分块数据)",
                f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_BODY}px; background: transparent;"
            )
            empty.setParent(self.tab_chunk)
            layout.addWidget(empty)
            return

        for idx, chunks in sorted(chunks_by_idx.items(), key=lambda x: int(x[0])):
            raw = raw_inputs[int(idx)] if int(idx) < len(raw_inputs) else ""
            preview = raw if len(raw) <= 50 else raw[:50] + "..."

            dup_count = len(duplicates.get(idx, []))
            subtitle = f"{len(chunks)} 个分块"
            if dup_count > 0:
                subtitle += f"  ·  {dup_count} 个重复"

            card = self._make_info_card(f"串{idx+1} · {preview}", subtitle)

            # 分块表格
            for chunk in chunks[:50]:  # 限制显示前 50 个
                dup_badge = " [重复]" if chunk.get("is_duplicate") else ""
                content_preview = chunk['content'] if len(chunk['content']) <= 40 else chunk['content'][:40] + "..."
                style = f"color: {COLOR_TEXT_DIM}; font-family: {FONT_MONO};"
                if chunk.get("is_duplicate"):
                    style += f" color: {COLOR_ORANGE};"
                style += " font-size: 11px; background: transparent; padding: 1px 0;"
                row = make_selectable_label(
                    f"  #{chunk['index']:3d}  `{content_preview}`  "
                    f"SHA256: {chunk['sha256'][:16]}...{dup_badge}",
                    style
                )
                row.setParent(card)
                card.layout().addWidget(row)
            if len(chunks) > 50:
                more = make_selectable_label(
                    f"  ... 还有 {len(chunks)-50} 个分块",
                    f"color: {COLOR_TEXT_MUTED}; font-style: italic;"
                    f" font-size: 11px; background: transparent;"
                )
                more.setParent(card)
                card.layout().addWidget(more)

            layout.addWidget(card)

    def _create_diff_tab(self) -> QWidget:
        """Tab 4: 差异比对。"""
        widget = QScrollArea(self)
        widget.setObjectName("DiffInterface")
        view = QWidget(widget)
        view.setObjectName("view")
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        widget.setWidget(view)
        widget.setWidgetResizable(True)
        widget.setStyleSheet("QScrollArea, QWidget#view { background: transparent; }")

        title = QLabel("差异比对", widget)
        title.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_TITLE}px;"
            f" font-weight: 500; background: transparent;"
        )
        layout.addWidget(title)

        widget.content_layout = QVBoxLayout()
        widget.content_layout.setSpacing(10)
        content_wrap = QWidget(widget)
        content_wrap.setLayout(widget.content_layout)
        layout.addWidget(content_wrap)
        layout.addStretch()

        return widget

    def _populate_diff_tab(self, diff_data: dict, raw_inputs: list):
        """填充差异比对 Tab 内容。"""
        if not hasattr(self.tab_diff, 'content_layout'):
            return
        layout = self.tab_diff.content_layout
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        hamming = diff_data.get("hamming", {})
        levenshtein = diff_data.get("levenshtein", {})
        jaccard = diff_data.get("jaccard", {})

        if not hamming:
            empty = make_selectable_label(
                "(无差异比对数据)",
                f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_BODY}px; background: transparent;"
            )
            empty.setParent(self.tab_diff)
            layout.addWidget(empty)
            return

        for key in sorted(hamming.keys()):
            i, j = key.split(",")
            i, j = int(i), int(j)

            h_val = hamming.get(key, -1)
            l_val = levenshtein.get(key, 0)
            j_val = jaccard.get(key, 0.0)

            h_str = f"{h_val}" if h_val >= 0 else "不等长"
            j_str = f"{j_val:.3f}"

            raw_i = raw_inputs[i] if i < len(raw_inputs) else ""
            raw_j = raw_inputs[j] if j < len(raw_inputs) else ""
            preview_i = raw_i if len(raw_i) <= 25 else raw_i[:25] + "..."
            preview_j = raw_j if len(raw_j) <= 25 else raw_j[:25] + "..."

            card = self._make_info_card(
                f"串{i+1} ↔ 串{j+1}",
                f"  `{preview_i}` ↔ `{preview_j}`"
            )
            metrics = make_selectable_label(
                f"  汉明距离: {h_str}    "
                f"编辑距离: {l_val}    "
                f"Jaccard: {j_str}",
                f"color: {COLOR_CYAN}; font-family: {FONT_MONO};"
                f" font-size: 12px; background: transparent; padding: 4px 0;"
            )
            metrics.setParent(card)
            card.layout().addWidget(metrics)
            layout.addWidget(card)

    def _make_info_card(self, title: str, subtitle: str = "") -> QFrame:
        """通用分组卡片。"""
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{"
            f"  background: rgba(255, 255, 255, 0.05);"
            f"  border-radius: {GROUP_RADIUS}px;"
            f"  padding: 12px;"
            f"  border: none;"
            f"}}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(6)

        title_label = QLabel(title, card)
        title_label.setStyleSheet(
            f"color: {COLOR_CYAN}; font-size: 13px; font-weight: 500;"
            f" background: transparent;"
        )
        card_layout.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle, card)
            sub_label.setStyleSheet(
                f"color: {COLOR_TEXT_MUTED}; font-size: 11px;"
                f" background: transparent;"
            )
            card_layout.addWidget(sub_label)

        return card

    def _create_placeholder_tab(self, title: str) -> QWidget:
        widget = QWidget(self)
        widget.setObjectName(f"Placeholder_{title}")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        title_label = QLabel(title, widget)
        title_label.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_TITLE}px;"
            f" font-weight: 500; background: transparent;"
        )
        layout.addWidget(title_label)
        info = QLabel("(结果展示区 - 后续任务实现)", widget)
        info.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_BODY}px;"
            f" background: transparent;"
        )
        layout.addWidget(info)
        layout.addStretch()
        widget.setStyleSheet("QWidget { background: transparent; }")
        return widget

    def _append_log(self, msg: str):
        self.log_text.append(msg)
        self.log_text.moveCursor(QTextCursor.End)

    def _on_start_clicked(self):
        raw = self.input_text.toPlainText().strip()
        if not raw:
            InfoBar.warning("警告", "请输入数据", duration=2000, parent=self)
            return

        strings = [line for line in raw.split('\n') if line.strip()]

        oversized = [s for s in strings if len(s) > config.WARN_INPUT_LENGTH]
        if oversized:
            InfoBar.warning(
                "提示",
                f"{len(oversized)} 条字符串超过 {config.WARN_INPUT_LENGTH // 1024}KB，分析可能较慢",
                duration=3000,
                parent=self,
            )

        if len(strings) > config.WARN_STRINGS:
            InfoBar.warning(
                "提示",
                f"输入了 {len(strings)} 条字符串，可能需要较长时间",
                duration=3000,
                parent=self,
            )

        chunk_config = ChunkingConfig(
            chunk_size=self.chunk_size_spin.value(),
            window_size=self.window_size_spin.value(),
            window_step=self.window_step_spin.value(),
            is_hex=self.hex_checkbox.isChecked(),
        )

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("分析中...")

        self.worker_thread = QThread()
        self.worker = AnalyzerWorker(strings, chunk_config=chunk_config)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_analysis_finished)
        self.worker.progress.connect(self._on_progress)
        self.worker.log_msg.connect(self._append_log)
        self.worker.status_changed.connect(self._on_status_changed)

        self.worker_thread.start()

    def _on_stop_clicked(self):
        if self.worker:
            self.worker.stop()
            self._append_log("已请求停止...")

    def _on_import_clicked(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择文本文件", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                content = Path(filename).read_text(encoding='utf-8')
                self.input_text.setPlainText(content)
                InfoBar.success("成功", f"已导入 {len(content)} 字符", duration=2000, parent=self)
            except (OSError, UnicodeDecodeError) as e:
                InfoBar.error("错误", f"导入失败: {e}", duration=3000, parent=self)

    def _on_clear_clicked(self):
        self.input_text.clear()
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("就绪")
        self.tab_basic.clear_results()
        self.current_result = None

    def _on_export_clicked(self, fmt: str):
        if not self.current_result:
            InfoBar.warning("警告", "没有可导出的分析结果", duration=2000, parent=self)
            return
        if fmt == "json":
            content = to_json(self.current_result)
            default_name = "analysis.json"
            filt = "JSON Files (*.json)"
        else:
            content = to_markdown(self.current_result)
            default_name = "analysis.md"
            filt = "Markdown Files (*.md)"
        filename, _ = QFileDialog.getSaveFileName(self, "保存分析结果", default_name, filt)
        if filename:
            try:
                Path(filename).write_text(content, encoding='utf-8')
                InfoBar.success("成功", f"已导出到 {filename}", duration=2000, parent=self)
            except OSError as e:
                InfoBar.error("错误", f"导出失败: {e}", duration=3000, parent=self)

    def _on_progress(self, current: int, total: int, task_name: str):
        self.progress_bar.setValue(current)
        self.tab_basic.progress_label.setText(f"[{current}/{total}] {task_name}")
        self.status_label.setText(f"[{current}/{total}] {task_name}")

    def _on_status_changed(self, status: str):
        if status == "Idle":
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.status_label.setText("完成")
            self.tab_basic.progress_label.setText("")

    def _on_analysis_finished(self, result: dict):
        self.current_result = result
        self.history.add(result['inputs'], result)
        self._append_log("分析完成，已保存到历史记录")

        basic = result.get("basic_features", [])
        patterns = result.get("patterns", [])
        inputs = result.get("inputs", [])

        # 填充各 Tab
        if basic and patterns and inputs:
            self.tab_basic.populate_results(basic, patterns, inputs)
        if "common_substring" in result:
            self._populate_common_substring_tab(
                result["common_substring"],
                inputs,
                repeat_data=result.get("repeat_substring", []),
            )
        if "chunking" in result:
            self._populate_chunk_tab(result["chunking"], inputs)
        if "diff" in result:
            self._populate_diff_tab(result["diff"], inputs)

        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()

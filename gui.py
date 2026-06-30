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
"""
from pathlib import Path
from typing import List, Optional
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QScrollArea, QTextEdit,
    QVBoxLayout, QWidget, QCheckBox, QSizePolicy,
)
from qfluentwidgets import (
    FluentWindow, PushButton, PrimaryPushButton, ProgressBar, SpinBox,
    InfoBar, FluentIcon as FIF, SubtitleLabel, BodyLabel,
)

import config
from workers import AnalyzerWorker
from analyzer.history import History
from analyzer.chunking import ChunkingConfig
from exporters import to_json, to_markdown


# ===== 样式常量（Y2 排版 + A1 主色）=====
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

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"

FONT_SIZE_TITLE = 18
FONT_SIZE_SUBTITLE = 13
FONT_SIZE_BODY = 12
FONT_SIZE_LABEL = 11
FONT_SIZE_BADGE = 11

GROUP_RADIUS = 8
BADGE_RADIUS = 3
BUTTON_RADIUS = 6

# 全局 QSS：暗色 + 透出 Fluent 主题
GLOBAL_QSS = """
QWidget { color: white; background: transparent; }
QLabel { color: white; background: transparent; }
QCheckBox { color: white; background: transparent; spacing: 6px; }
QCheckBox::indicator {
    width: 14px; height: 14px;
    background: #2b2b2b;
    border: 1px solid #4cc2ff;
    border-radius: 2px;
}
QCheckBox::indicator:checked { background: #4cc2ff; }
QScrollArea, QWidget#view { background: transparent; border: none; }
QTextEdit {
    background-color: #2b2b2b;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px;
    selection-background-color: #0078d7;
    selection-color: white;
}
QTextEdit:focus { border: 1px solid #0078d7; }
SpinBox { background: transparent; border: none; }
SpinBox QLineEdit {
    background-color: #2b2b2b;
    color: white;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 4px 6px;
}
SpinBox QLineEdit:focus { border: 1px solid #0078d7; }
QProgressBar {
    background: #2b2b2b;
    border: none;
    height: 4px;
    border-radius: 2px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: #0078d7;
    border-radius: 2px;
}
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


def make_group_frame() -> QFrame:
    """T2 分组卡片：半透明白背景。"""
    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame {{"
        f"  background: rgba(255, 255, 255, 0.05);"
        f"  border-radius: {GROUP_RADIUS}px;"
        f"  padding: 12px;"
        f"}}"
    )
    return frame


class StringCard(QFrame):
    """单条字符串的分析结果卡片。"""

    def __init__(self, index: int, raw: str, basic_features: dict, patterns: list, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{"
            f"  background: rgba(255, 255, 255, 0.05);"
            f"  border-radius: {GROUP_RADIUS}px;"
            f"  padding: 12px;"
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
        layout.addWidget(header)

        # 基本特征行
        features_layout = QHBoxLayout()
        features_layout.setSpacing(16)
        for label, key in [("长度", "length"), ("唯一字符", "unique_chars"),
                            ("大写", None), ("小写", None), ("数字", None)]:
            if key:
                value = str(basic_features.get(key, 0))
            else:
                cc = basic_features.get("char_classes", {})
                cn_map = {"大写": "upper", "小写": "lower", "数字": "digit"}
                value = str(cc.get(cn_map[label], 0))
            col = QVBoxLayout()
            col.setSpacing(2)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
            val = QLabel(value)
            val.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 13px;")
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
            # 颜色映射
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
            f" font-weight: 500; font-family: {FONT_FAMILY};"
        )
        self.layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("基本特征", self)
        self.subtitle_label.setStyleSheet(
            f"color: {COLOR_CYAN}; font-size: {FONT_SIZE_SUBTITLE}px; font-family: {FONT_FAMILY};"
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
        font.setPointSize(11)
        self.input_text.setFont(font)
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
            lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: {FONT_SIZE_BODY}px;")
            chunk_layout.addWidget(lbl)
            spin = SpinBox(self)
            spin.setRange(1, 1024)
            spin.setValue(default)
            spin.setFixedWidth(80)
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
        self.layout.addLayout(button_layout)

        # 进度条（P1 蓝色细线）
        self.progress_label = QLabel("", self)
        self.progress_label.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_LABEL}px; font-family: {FONT_FAMILY};"
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
            f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 500; margin-top: 6px;"
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
            f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_LABEL}px; font-family: {FONT_FAMILY};"
        )
        self.layout.addWidget(self.status_label)

        self.layout.addStretch()

    def clear_results(self):
        """清除结果卡片。"""
        while self.result_layout.count() > 1:  # 保留最后的 stretch
            item = self.result_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def populate_results(self, basic_features_list, patterns_list, raw_inputs):
        """填充结果卡片。"""
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

        # 应用全局 QSS
        self.setStyleSheet(GLOBAL_QSS)

        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[AnalyzerWorker] = None
        self.current_result: Optional[dict] = None
        self.history = History(config.HISTORY_FILE, max_entries=config.HISTORY_MAX_ENTRIES)

        # 5 个 Tab：基本特征 / 公共子串 / 分块 / 差异比对 / 日志
        self.tab_basic = self._create_basic_tab()
        self.tab_common = self._create_placeholder_tab("公共子串 / 子序列")
        self.tab_chunk = self._create_placeholder_tab("分块分析")
        self.tab_diff = self._create_placeholder_tab("差异比对")
        self.tab_log = self._create_log_tab()

        self.addSubInterface(self.tab_basic, FIF.SEARCH, "基本特征")
        self.addSubInterface(self.tab_common, FIF.LINK, "公共子串")
        self.addSubInterface(self.tab_chunk, FIF.CUT, "分块分析")
        self.addSubInterface(self.tab_diff, FIF.SEND, "差异比对")
        self.addSubInterface(self.tab_log, FIF.DOCUMENT, "日志")

        # 暴露属性给测试（指向基本特征 Tab）
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
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_TITLE}px; font-weight: 500;"
        )
        layout.addWidget(title)

        log_group = make_group_frame()
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(0, 0, 0, 0)
        widget.log_text = QTextEdit(widget)
        widget.log_text.setReadOnly(True)
        font = QFont(FONT_MONO)
        font.setPointSize(11)
        widget.log_text.setFont(font)
        widget.log_text.setMinimumHeight(500)
        log_layout.addWidget(widget.log_text)
        layout.addWidget(log_group)

        # 暴露属性到主窗口（覆盖之前的 setattr）
        self.log_text = widget.log_text
        return widget

    def _create_placeholder_tab(self, title: str) -> QWidget:
        widget = QWidget(self)
        widget.setObjectName(f"Placeholder_{title}")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        title_label = QLabel(title, widget)
        title_label.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: {FONT_SIZE_TITLE}px; font-weight: 500;"
        )
        layout.addWidget(title_label)
        info = QLabel("(结果展示区 - 后续任务实现)", widget)
        info.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: {FONT_SIZE_BODY}px;"
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
        self.progress_label.setText(f"[{current}/{total}] {task_name}")
        self.status_label.setText(f"[{current}/{total}] {task_name}")

    def _on_status_changed(self, status: str):
        if status == "Idle":
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.status_label.setText("完成")
            self.progress_label.setText("")

    def _on_analysis_finished(self, result: dict):
        self.current_result = result
        self.history.add(result['inputs'], result)
        self._append_log("分析完成，已保存到历史记录")

        # 填充结果卡片
        basic = result.get("basic_features", [])
        patterns = result.get("patterns", [])
        inputs = result.get("inputs", [])
        if basic and patterns and inputs:
            self.tab_basic.populate_results(basic, patterns, inputs)

        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()

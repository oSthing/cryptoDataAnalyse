"""主窗口 + Tab 组件。"""
from pathlib import Path
from typing import List, Optional
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QScrollArea, QTextEdit, QVBoxLayout, QWidget, QCheckBox
)
from qfluentwidgets import (
    FluentWindow, PushButton, PrimaryPushButton, ProgressBar, SpinBox,
    InfoBar, setTheme, Theme, FluentIcon as FIF, SubtitleLabel, BodyLabel,
)

import config
from workers import AnalyzerWorker
from analyzer.history import History
from analyzer.chunking import ChunkingConfig
from exporters import to_json, to_markdown


class AnalysisInterface(QScrollArea):
    """主分析界面：参照参考项目结构（ScrollArea + QWidget#view 透明 + QLabel 白字）。"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.layout = QVBoxLayout(self.view)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setObjectName("AnalysisInterface")
        self.view.setObjectName("view")

        # 参照参考项目：透明背景透出 FluentWindow 暗色 + Label 白字
        self.setStyleSheet("""
            QScrollArea, QWidget#view { background: transparent; }
            QLabel { color: white; }
        """)

        # 标题
        self.title = SubtitleLabel("字符串分析", self)
        self.layout.addWidget(self.title)

        # 输入分组
        self.input_group = QFrame(self)
        self.input_group.setObjectName("input_group")
        self.input_group.setStyleSheet("""
            QFrame#input_group {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        input_group_layout = QVBoxLayout(self.input_group)

        input_label = BodyLabel("输入数据（每行一条字符串）：", self)
        input_label.setStyleSheet("color: white; font-weight: bold;")
        input_group_layout.addWidget(input_label)

        self.input_text = QTextEdit(self)
        self.input_text.setPlaceholderText("在此输入要分析的字符串，每行一条...")
        self.input_text.setMinimumHeight(200)
        font = self.input_text.font()
        font.setFamily("Consolas")
        self.input_text.setFont(font)
        input_group_layout.addWidget(self.input_text)

        self.hex_checkbox = QCheckBox("输入是 Hex 字符串（按字节切分）", self)
        self.hex_checkbox.setStyleSheet("color: white;")
        input_group_layout.addWidget(self.hex_checkbox)

        self.layout.addWidget(self.input_group)

        # 分块配置行
        chunk_layout = QHBoxLayout()
        chunk_label = BodyLabel("分块长度:", self)
        chunk_label.setStyleSheet("color: white;")
        chunk_layout.addWidget(chunk_label)
        self.chunk_size_spin = SpinBox(self)
        self.chunk_size_spin.setRange(1, 1024)
        self.chunk_size_spin.setValue(config.DEFAULT_CHUNK_SIZE)
        chunk_layout.addWidget(self.chunk_size_spin)

        chunk_layout.addSpacing(20)
        ws_label = BodyLabel("窗口大小:", self)
        ws_label.setStyleSheet("color: white;")
        chunk_layout.addWidget(ws_label)
        self.window_size_spin = SpinBox(self)
        self.window_size_spin.setRange(1, 1024)
        self.window_size_spin.setValue(config.DEFAULT_WINDOW_SIZE)
        chunk_layout.addWidget(self.window_size_spin)

        chunk_layout.addSpacing(20)
        st_label = BodyLabel("步长:", self)
        st_label.setStyleSheet("color: white;")
        chunk_layout.addWidget(st_label)
        self.window_step_spin = SpinBox(self)
        self.window_step_spin.setRange(1, 1024)
        self.window_step_spin.setValue(config.DEFAULT_WINDOW_STEP)
        chunk_layout.addWidget(self.window_step_spin)

        chunk_layout.addStretch()
        self.layout.addLayout(chunk_layout)

        # 按钮行
        button_layout = QHBoxLayout()
        self.btn_start = PrimaryPushButton("开始分析", self)
        self.btn_stop = PushButton("停止", self)
        self.btn_import = PushButton("从文件导入", self)
        self.btn_clear = PushButton("清空", self)
        self.btn_stop.setEnabled(False)

        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_stop)
        button_layout.addWidget(self.btn_import)
        button_layout.addWidget(self.btn_clear)
        button_layout.addStretch()
        self.btn_export_json = PushButton("导出 JSON", self)
        self.btn_export_md = PushButton("导出 Markdown", self)
        button_layout.addWidget(self.btn_export_json)
        button_layout.addWidget(self.btn_export_md)
        self.layout.addLayout(button_layout)

        # 进度
        progress_label = BodyLabel("处理进度:", self)
        progress_label.setStyleSheet("color: white;")
        self.layout.addWidget(progress_label)
        self.progress_bar = ProgressBar(self)
        self.layout.addWidget(self.progress_bar)

        # 日志分组
        self.log_group = QFrame(self)
        self.log_group.setObjectName("log_group")
        self.log_group.setStyleSheet("""
            QFrame#log_group {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        log_group_layout = QVBoxLayout(self.log_group)

        log_label = BodyLabel("当前状态简报:", self)
        log_label.setStyleSheet("color: white;")
        log_group_layout.addWidget(log_label)

        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        log_font = self.log_text.font()
        log_font.setFamily("Consolas")
        self.log_text.setFont(log_font)
        self.log_text.setMinimumHeight(150)
        log_group_layout.addWidget(self.log_text)

        self.layout.addWidget(self.log_group)

        # 状态
        self.status_label = BodyLabel("就绪", self)
        self.status_label.setStyleSheet("color: white;")
        self.layout.addWidget(self.status_label)

        self.layout.addStretch()


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据分析工具")
        self.resize(1200, 800)

        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[AnalyzerWorker] = None
        self.current_result: Optional[dict] = None
        self.history = History(config.HISTORY_FILE, max_entries=config.HISTORY_MAX_ENTRIES)

        # 创建主界面（参照参考项目的 ScrollArea + view 结构）
        self.analysis_interface = AnalysisInterface(self)
        self.addSubInterface(self.analysis_interface, FIF.SEARCH, "分析")

        # 暴露属性给测试
        self.input_text = self.analysis_interface.input_text
        self.hex_checkbox = self.analysis_interface.hex_checkbox
        self.chunk_size_spin = self.analysis_interface.chunk_size_spin
        self.window_size_spin = self.analysis_interface.window_size_spin
        self.window_step_spin = self.analysis_interface.window_step_spin
        self.btn_start = self.analysis_interface.btn_start
        self.btn_stop = self.analysis_interface.btn_stop
        self.btn_import = self.analysis_interface.btn_import
        self.btn_clear = self.analysis_interface.btn_clear
        self.btn_export_json = self.analysis_interface.btn_export_json
        self.btn_export_md = self.analysis_interface.btn_export_md
        self.progress_bar = self.analysis_interface.progress_bar
        self.log_text = self.analysis_interface.log_text
        self.status_label = self.analysis_interface.status_label

        # 信号连接
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_import.clicked.connect(self._on_import_clicked)
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        self.btn_export_json.clicked.connect(lambda: self._on_export_clicked("json"))
        self.btn_export_md.clicked.connect(lambda: self._on_export_clicked("md"))

    def _append_log(self, msg: str):
        self.log_text.append(msg)
        self.log_text.moveCursor(QTextCursor.End)

    def _on_start_clicked(self):
        raw = self.input_text.toPlainText().strip()
        if not raw:
            InfoBar.warning("警告", "请输入数据", duration=2000, parent=self)
            return

        strings = [line for line in raw.split('\n') if line.strip()]

        # 长度警告
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
        self.status_label.setText(f"[{current}/{total}] {task_name}")

    def _on_status_changed(self, status: str):
        if status == "Idle":
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.status_label.setText("完成")

    def _on_analysis_finished(self, result: dict):
        self.current_result = result
        self.history.add(result['inputs'], result)
        self._append_log(f"分析完成，已保存到历史记录")

        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
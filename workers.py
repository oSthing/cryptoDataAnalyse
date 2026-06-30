"""异步分析 Worker，在 QThread 中执行所有分析器。"""
from dataclasses import asdict
from datetime import datetime
from typing import List
from PyQt5.QtCore import QObject, pyqtSignal

from analyzer.basic_features import analyze_all
from analyzer.pattern import detect_all
from analyzer.common_substring import analyze as cs_analyze
from analyzer.chunking import analyze as chunk_analyze, ChunkingConfig
from analyzer.diff import analyze as diff_analyze
from analyzer.periodicity import analyze as period_analyze
from analyzer.bit_analysis import analyze as bit_analyze
from analyzer.multi_string import analyze as ms_analyze
from analyzer.repeat_substring import analyze as repeat_analyze


class AnalyzerWorker(QObject):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int, int, str)
    log_msg = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, strings: List[str], chunk_config: ChunkingConfig = None,
                 substring_min_length: int = 1):
        super().__init__()
        self.strings = strings
        self.chunk_config = chunk_config or ChunkingConfig()
        self.substring_min_length = substring_min_length
        self.is_running = True
        self._cancel_check_interval = 1000

    def stop(self):
        self.is_running = False

    def _check_cancel(self):
        if not self.is_running:
            raise InterruptedError("分析已取消")

    def _check_cancel_loop(self, i: int):
        if i % self._cancel_check_interval == 0 and not self.is_running:
            raise InterruptedError("分析已取消")

    def run(self):
        try:
            self.status_changed.emit("Running")
            total_steps = 8
            result = {
                "timestamp": datetime.now().isoformat(),
                "inputs": self.strings,
            }

            # 1. 基本特征
            self.log_msg.emit("[1/8] 计算基本特征...")
            self.progress.emit(1, total_steps, "基本特征")
            result["basic_features"] = analyze_all(self.strings)

            # 2. 模式识别
            self.log_msg.emit("[2/8] 模式识别...")
            self.progress.emit(2, total_steps, "模式识别")
            result["patterns"] = detect_all(self.strings)

            # 3. 公共子串/子序列
            self._check_cancel()
            self.log_msg.emit("[3/8] 公共子串/子序列...")
            self.progress.emit(3, total_steps, "公共子串/子序列")
            cs_result = cs_analyze(self.strings, min_length=self.substring_min_length)
            result["common_substring"] = {
                "pairwise": {f"{i},{j}": v for (i, j), v in cs_result.pairwise.items()},
                "multi": cs_result.multi,
                "common_prefix": cs_result.common_prefix,
                "common_suffix": cs_result.common_suffix,
                "all_pairwise": {f"{i},{j}": v for (i, j), v in cs_result.all_pairwise.items()},
                "all_multi": cs_result.all_multi,
            }

            # 4. 单串内重复最多的子串
            self._check_cancel()
            self.log_msg.emit("[4/8] 单串内重复子串...")
            self.progress.emit(4, total_steps, "单串重复子串")
            repeat_results = repeat_analyze(self.strings, min_length=2, min_count=2, max_results=50)
            # RepeatResult 是 dataclass，需解包为 dict
            result["repeat_substring"] = [
                {
                    "index": i,
                    "substrings": [
                        {"sub": s, "count": c, "positions": pos}
                        for s, c, pos in r.substrings
                    ],
                }
                for i, r in enumerate(repeat_results)
            ]

            # 5. 分块分析
            self._check_cancel()
            self.log_msg.emit("[5/8] 分块分析...")
            self.progress.emit(5, total_steps, "分块分析")
            chunk_result = chunk_analyze(self.strings, self.chunk_config)
            result["chunking"] = {
                "chunks": {i: [asdict(c) for c in chunks] for i, chunks in chunk_result.chunks.items()},
                "duplicates": chunk_result.duplicates,
            }

            # 6. 差异比对
            self._check_cancel()
            self.log_msg.emit("[6/8] 差异比对...")
            self.progress.emit(6, total_steps, "差异比对")
            diff_result = diff_analyze(self.strings)
            result["diff"] = {
                "hamming": {f"{i},{j}": v for (i, j), v in diff_result.hamming.items()},
                "levenshtein": {f"{i},{j}": v for (i, j), v in diff_result.levenshtein.items()},
                "jaccard": {f"{i},{j}": v for (i, j), v in diff_result.jaccard.items()},
            }

            # 7. 周期性
            self._check_cancel()
            self.log_msg.emit("[7/8] 周期性检测...")
            self.progress.emit(7, total_steps, "周期性")
            period_result = period_analyze(self.strings)
            result["periodicity"] = [asdict(p) for p in period_result]

            # 8. 比特层分析
            self._check_cancel()
            self.log_msg.emit("[8/8] 比特层分析...")
            self.progress.emit(8, total_steps, "比特层")
            bit_result = bit_analyze(self.strings)
            result["bit_analysis"] = [asdict(b) for b in bit_result]

            # 8. 多串关联
            self._check_cancel()
            self.log_msg.emit("[8/8] 多串关联...")
            self.progress.emit(8, total_steps, "多串关联")
            ms_result = ms_analyze(self.strings)
            result["multi_string"] = asdict(ms_result)

            self.log_msg.emit("分析完成")
            self.status_changed.emit("Idle")
            self.finished.emit(result)
        except InterruptedError:
            self.log_msg.emit("分析已取消")
            self.status_changed.emit("Stopped")
        except Exception as e:
            self.log_msg.emit(f"错误: {e}")
            self.status_changed.emit("Error")

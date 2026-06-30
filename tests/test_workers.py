"""测试 AnalyzerWorker：在 QThread 线程中协调所有分析器。"""
import pytest
from PyQt5.QtCore import QCoreApplication, Qt
from workers import AnalyzerWorker


@pytest.fixture(scope="module")
def qapp():
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app


def test_worker_runs_all_analyzers(qapp):
    strings = ["abc123", "abc456"]
    worker = AnalyzerWorker(strings)

    results = {}
    worker.finished.connect(lambda r: results.update({"data": r}), Qt.DirectConnection)

    import threading
    thread = threading.Thread(target=worker.run)
    thread.start()
    thread.join(timeout=10)

    assert "data" in results
    r = results["data"]
    assert r["inputs"] == strings
    assert len(r["basic_features"]) == 2


def test_worker_stop(qapp):
    strings = ["a" * 10000] * 10
    worker = AnalyzerWorker(strings)
    worker.stop()
    # 不应抛异常
    import threading
    thread = threading.Thread(target=worker.run)
    thread.start()
    thread.join(timeout=5)

# dataAnalyse

密码学字符串分析工具。输入一条或多条字符串，自动分析其结构特征、共性、差异和模式识别。

## 功能

- **基本特征 + 模式识别**：长度、字符类、唯一字符数；25+ 密码学/编码模式识别
- **最长公共子串/子序列**
- **分块分析**：固定长度、滑动窗口、Hex 模式
- **差异比对**：汉明距离、编辑距离、Jaccard 相似度
- **周期性检测**
- **比特层分析**：含 NIST 随机性测试子集
- **多串关联**：拼接还原、长度递进检测
- **历史记录**：最近 20 次分析
- **导出**：JSON / Markdown

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 测试

```bash
pytest
```

## 技术栈

Python 3.10+ / PyQt5 / qfluentwidgets

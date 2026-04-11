# 股票 UP 主知识库

基于 Andrej Karpathy [LLM 知识库方法论](https://karpathy.ai/blog/llm-workflows.html) 构建的股票直播内容知识库。

## 快速开始

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate

# 初始化
python tools/ingest.py --all
python tools/compile.py --all

# 提问
python tools/qa.py "B2买入法的核心条件"

# 健康检查
python tools/lint.py
```

## 文档

- [使用手册](docs/usage.md)

## 目录结构

```
zgnb/
├── raw/           # 原始素材（视频转录 + PDF 总结）
├── concepts/      # LLM 编译的核心概念词条
├── wiki/          # 主题地图与输出归档
├── index.md       # 总索引
└── tools/         # CLI 工具链
```

## 核心工作流

1. **数据导入** (`ingest.py`)：把外部素材整理进 `raw/`
2. **LLM 编译** (`compile.py`)：自动生成 `concepts/`、`wiki/maps/`、`index.md`
3. **问答** (`qa.py`)：基于知识库内容智能回答
4. **输出** (`output.py`)：把答案归档为 Markdown / 幻灯片 / 图表
5. **健康检查** (`lint.py`)：维护知识库质量

## 技术栈

- Python 3.11+
- DeepSeek API (via OpenAI SDK)
- Obsidian (前端)

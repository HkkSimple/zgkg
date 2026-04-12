# 股票 UP 主知识库

基于 **Andrej Karpathy LLM 知识库方法论** 构建的股票直播内容知识库。

> 核心理念：人类负责收集原始素材，LLM 负责自动编译、整理和持续维护。知识库会随着你的每次查询而自动积累、优化。

---

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
- [知识库方法论](AGENT.md)

## 目录结构

```
zgnb/
├── raw/           # 原始素材（视频转录 + PDF 总结）——只读，永不手动修改
├── concepts/      # LLM 自动编译的核心概念词条
├── wiki/          # 主题地图、输出归档与健康检查报告
│   ├── maps/      # 主题导航地图
│   └── outputs/   # 问答沉淀的输出文件
├── images/        # 图片等附件
├── outputs/       # 生成的报告、对比分析、问题解答
├── index.md       # 总索引（LLM 自动维护）
└── tools/         # CLI 工具链
```

## 核心工作流（Karpathy 模式）

1. **Data Ingest（数据导入）**：`ingest.py` 把外部素材整理进 `raw/`
2. **LLM Compilation（编译）**：`compile.py` 自动生成 `concepts/`、`wiki/maps/`、`index.md`
3. **Query & Filing Back（问答与沉淀）**：`qa.py` 基于知识库智能回答，`output.py` 把答案归档为 Markdown / 幻灯片 / 图表
4. **Linting（健康检查）**：`lint.py` 扫描矛盾、缺失与优化建议，维护知识库质量

## 技术栈

- Python 3.11+
- DeepSeek API (via OpenAI SDK)
- Obsidian (前端)

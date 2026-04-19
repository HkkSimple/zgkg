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

## 两种查询方式对比

本知识库支持两种查询方式，根据问题类型选择最合适的：

| 对比项 | 直接对话问 Claude（推荐） | 走 `qa.py` 自动化流程 |
|---|---|---|
| **视觉能力** | ✅ 能直接阅读图片型 PDF、K 线图、图表 | ❌ 纯文本检索，无法"看图" |
| **文件召回** | ✅ 主动搜索 `raw/`、`concepts/`、`wiki/` 全部目录及子目录 | ⚠️ 关键词匹配，对子目录和图鉴类素材召回不全 |
| **上下文长度** | ✅ 200K+ tokens，可一次性读完 B1/B2 图鉴全文（20K） | ❌ 截断到 2000 字符，图鉴类素材只能读到第 2-3 个案例 |
| **图鉴素材** | ✅ 边看文字描述边对照图片，理解 K 线形态细节 | ❌ 概念词条只有一句话概要，丢失"KDJ 勾到大负值"等关键细节 |
| **跨文件关联** | ✅ 可同时打开多个文件对比分析 | ⚠️ 仅按概念名召回关联文件 |
| **自动化** | ❌ 需要对话交互 | ✅ 一键提问，适合脚本化 |
| **成本** | 免费 | 消耗 DeepSeek API token |

### 使用建议

- **图鉴类、需要看图的问题** → 直接对话问 Claude  
  例："给我对比 B1 完美一和完美二的区别，结合华纳药厂和澄天伟业的图"

- **概念定义、文本类快速问答** → 走 `qa.py`  
  例：`python tools/qa.py "B2 买入法的核心条件有哪些"`

- **深度研究、多文件综合分析** → 直接对话问 Claude  
  例："对比 2025 空谷幽兰和 2026 静水流深两个系列对 B1 买点的不同理解"

> **注意**：当前 `qa.py` 对图鉴类（`type: chart-atlas`）素材基本不可用，因为无法看图且截断严重。如需让 `qa.py` 支持图鉴，需增强概念词条（写入详细形态描述）并优化召回逻辑。

## 技术栈

- Python 3.11+
- DeepSeek API (via OpenAI SDK)
- Obsidian (前端)

# ZGNB 知识库使用说明

基于 **LLM 驱动个人知识库构建方法论**（Karpathy 模式）：将大语言模型作为「全职图书管理员」，把原始资料自动编译成结构化的 Markdown Wiki，而非依赖耗时的人工整理或复杂的 RAG 系统。

---

## 这是什么？

一个关于 **ZGNB** 的综合知识库。

涵盖主题（按需扩展）：
- 待补充...

---

## 核心理念

- **从手动记录到 AI 编译**：人类负责收集高质量原始素材并把握方向；目录结构、摘要提取、概念分类、双向链接等全部由 LLM 自动生成和维护。
- **Wiki 是 LLM 的领地**：在个人知识库规模（约 100 篇文章、40 万字左右）下，现代 LLM 已足够智能，可直接阅读全部关键数据并维护索引，无需引入向量数据库等复杂架构。
- **知识库会自我生长**：每次查询和输出的结果都会归档回知识库，形成持续积累的闭环。

---

## 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│  Data Ingest（收集原始素材）                                 │
│  ├─ 文章、论文、代码仓库、数据集、图片等扔进 raw/            │
│  └─ 人类是收集者，素材是「不可变的精选文档」                 │
├─────────────────────────────────────────────────────────────┤
│  LLM Compilation（LLM 自动编译）                             │
│  ├─ 生成摘要：为 raw/ 中每个文档撰写要点摘要                 │
│  ├─ 提取概念：识别核心概念，在 wiki/ 中生成百科式词条        │
│  ├─ 建立链接：在不同页面间自动创建 [[双向链接]]              │
│  └─ 维护索引：自动更新 INDEX.md 和分类目录                   │
├─────────────────────────────────────────────────────────────┤
│  Query & Filing Back（查询与知识沉淀）                       │
│  ├─ 向 LLM 提出复杂问题，它会在 Wiki 中自主检索、推理        │
│  ├─ 输出不仅限于聊天气泡，而是生成 Markdown / 幻灯片 / 图表  │
│  └─ 将输出的答案「归档」回 wiki/ 或 outputs/，充实知识库     │
└─────────────────────────────────────────────────────────────┘
```

---

## 文件夹结构

```
zgnb/
├── raw/           ← 原始素材（视频转录 + PDF 总结）——只读，永不手动修改
├── concepts/      ← LLM 自动编译的核心概念词条（百科式页面）
├── wiki/          ← 主题地图与输出归档
│   ├── maps/      ← 主题导航地图（快速定位相关概念）
│   └── outputs/   ← 问答沉淀的输出文件
├── images/        ← 图片等附件
├── outputs/       ← 生成的报告、对比分析、问题解答
├── index.md       ← 总索引（LLM 自动维护）
└── tools/         ← CLI 工具链
```

### 各目录说明

| 目录 | 规则 | 内容 |
|------|------|------|
| `raw/` | **只读**，永不手动修改 | 视频转录、PDF 总结、文章、博客等原始素材 |
| `concepts/` | **AI 维护**，完全由 LLM 生成 | 核心概念词条，融合 `raw/` 中多来源素材 |
| `wiki/` | **AI 维护**，完全由 LLM 生成 | 主题地图 (`maps/`)、问答沉淀 (`outputs/`)、健康检查报告 |
| `outputs/` | **AI 生成**，人类可筛选归档 | 研究报告、对比分析、问题解答、Marp 幻灯片 |
| `index.md` | **AI 维护** | 知识库总索引入口 |

---

## 维基整理规则

1. 每个核心主题一个 `.md` 文件
2. 开头写一段简短摘要（2-3 句话）
3. 用 `[[topic-name]]` 链接相关主题
4. 维护 `INDEX.md` 作为总索引
5. 添加新素材时，更新相关维基文章
6. 文件命名使用 kebab-case

---

## 工具栈推荐

| 角色 | 工具 | 说明 |
|------|------|------|
| 前端 IDE | Obsidian | 查看 Markdown、Graph View、双向链接可视化 |
| 素材捕获 | Obsidian Web Clipper | 一键将网页转为干净 Markdown，图片下载到本地 |
| 数据格式 | Markdown | 体积小、无平台锁定、LLM 最友好的格式 |
| 核心驱动 | DeepSeek API | 通过 OpenAI SDK 调用，长上下文 + 代码能力强的模型 |
| CLI 环境 | Python 3.11+ | 本地工具链运行环境 |

---

## 核心工作流程

```
看到好内容 → 扔进 raw/ → 让 AI 整理到 wiki/ → 有问题时查 wiki/ → 答案存 outputs/
```

在 zgnb 中，工具链直接对应了方法论的三层架构：**Data Ingest → LLM Compilation → Query & Filing Back → Linting**。

### 环境准备

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

确保 `.env` 中已配置 `DEEPSEEK_API_KEY`。

### 第一步：初始化（首次运行）

```bash
# 1. 导入所有原始素材
python tools/ingest.py --all

# 2. 全量编译（耗时较长，取决于 API 速度）
python tools/compile.py --all

# 3. 查看编译产物
ls concepts/
ls wiki/maps/
cat index.md
```

### 第二步：Data Ingest（日常更新）

**新增视频转录**

假设新视频转录放在 `/some/path/new-video/`，包含若干 `.txt`：

```bash
python tools/ingest.py --source /some/path/new-video/
python tools/compile.py --new-only
python tools/lint.py
```

**新增 PDF 文章**

```bash
python tools/ingest.py --articles --source /some/path/
python tools/compile.py --new-only
```

### 第三步：Query & Filing Back（问答与输出）

**单次提问**

```bash
python tools/qa.py "B2买入法的核心条件有哪些"
python tools/qa.py "这个UP主如何看半导体板块"
```

**交互模式**

```bash
python tools/qa.py --interactive
```

**输出为 Markdown 文章**

```bash
python tools/output.py --format md --question "少妇战法的买入逻辑"
```

结果保存在 `wiki/outputs/YYYY-MM-DD-少妇战法的买入逻辑.md`

**生成 Marp 幻灯片**

```bash
python tools/output.py --format slides --question "B2买入法实战体系"
```

在 Obsidian 中安装 Marp 插件后可直接预览为幻灯片。

**生成主题分布图**

```bash
python tools/output.py --format chart --question "topic-distribution"
```

**交互式对话问答（Claude Code 中直接提问）**

除了运行 `qa.py`，你也可以在 Claude Code 对话中直接基于知识库提问。这种方式更适合探索性、交叉对比类问题。

**两种方式的对比**

| | `qa.py` | 直接对话问答 |
|---|---|---|
| **触发方式** | 命令行脚本 | 在 Claude Code 中直接输入问题 |
| **召回机制** | 关键词匹配概念文件名 | LLM 按需主动读取相关文件 |
| **上下文范围** | 匹配到的概念（前 4000 字）+ 溯源 raw | 可读取完整文件，可全库 Grep |
| **追问能力** | 无 | 支持多轮追问和澄清 |
| **产物归档** | 自动保存到 `wiki/outputs/` | 需手动触发归档 |
| **适用场景** | 精确术语查询、批量问答、需要存档 | 探索性提问、跨概念对比、自然语言描述 |

**直接问答的检索机制**

Claude Code 不会预加载全部 concepts。当你提问时，它会根据语义判断需要读取哪些概念文件，用 Read 工具读取完整词条（不受 4000 字限制），如需跨文件关联，还会用 Grep 全库搜索，然后综合回答。

**归档方式：由 LLM 自动整理**

对话结束后，如果你认为回答有价值，直接说：

> "把刚才关于 XX 的问答归档到知识库"

Claude 会自动将问题和回答按规范格式整理，保存到 `wiki/outputs/YYYY-MM-DD-问题摘要.md`。文件格式如下：

```markdown
---
type: output
date: YYYY-MM-DD
question: 原始问题
---

# 问题

原始问题

# 回答

整理后的完整回答
```

归档完成后，该文件即可在 Obsidian 中查看，并作为知识库的一部分沉淀。

### 第四步：Linting（健康体检）

每周执行一次：

```bash
python tools/lint.py
```

打开 `wiki/health-check-YYYY-MM-DD.md` 查看：
- 哪些 `raw` 素材还没被概念引用
- 哪些内部链接失效
- 数据矛盾与优化建议

---

## 日常维护：Linting 详细说明

像程序员维护代码一样，定期让 LLM 对整个知识库执行「健康检查」：

- **排查矛盾**：发现知识库中相互矛盾的数据、过时的结论
- **补全缺失**：主动调用网络搜索工具，补充缺失信息和逻辑环节
- **挖掘关联**：发现潜在关联，建议新词条主题
- **修复孤立页面**：优化无链接页面，增强网状结构

在 zgnb 中，`tools/lint.py` 会自动完成上述检查并生成报告。

---

## 内容分层策略（重要）

- **`raw/articles/`（PDF 总结）**：体系框架、概念定义的主要来源
- **`raw/videos/`（直播转录）**：案例、实时观点、市场点评的主要来源
- **`concepts/`**：LLM 自动维护的词条，通常融合了两类来源
- **`wiki/maps/`**：主题地图，帮助你快速导航到相关概念
- **`wiki/outputs/`**：你自己的问答沉淀

---

## 故障排查

### `compile.py` 报错 "LLM call failed"
- 检查 `.env` 中 `DEEPSEEK_API_KEY` 是否正确
- 检查网络能否访问 `https://api.deepseek.com`

### `ingest.py` 没有生成 raw 文件
- 确认 `--source` 路径下有 `.txt` 或 `.pdf` 文件
- 使用 `--force` 覆盖已有文件

### `qa.py` 返回"信息不足"
- 说明该概念尚未被 `compile.py` 编译到 `concepts/` 中
- 检查 `index.md` 是否包含相关主题
- 可尝试全量重编译 `compile.py --all`

---

## 当前关注方向

待补充...

---

## 主题扩展原则

当某个方向积累足够内容时，在 wiki/ 中新建专题文件：
- 待补充...
- ...按需添加

---

## 参考来源

- [Andrej Karpathy：大语言模型构建个人知识库的实践指南 - 知乎](https://zhuanlan.zhihu.com/p/2023724659573564910)

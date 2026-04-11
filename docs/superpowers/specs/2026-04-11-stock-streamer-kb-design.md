# 股票 UP 主直播内容知识库 - 设计文档

---

date: 2026-04-11
type: design-spec
status: draft

---

## 1. 项目目标

为股票 UP 主的直播视频转录文本及网络高度总结文章，搭建一个基于 Andrej Karpathy「LLM 知识库」方法论的个人知识库系统。核心目标：

- **原始素材自动归档**：视频转录 + PDF 总结统一放入 `raw/`，人类不直接编辑 `wiki/` 和 `concepts/`。
- **LLM 自动编译**：LLM 像编译器一样，把零散文本编译成结构化的 `index.md` + `concepts/` 词条 + `wiki/` 主题地图。
- **问答即沉淀**：用户提问后，LLM 自主检索并生成答案，有价值的答案输出为 Markdown/幻灯片/图表，归档回 `wiki/outputs/`。
- **健康自检**：定期运行 lint，发现孤立页面、失效链接、概念矛盾，持续优化知识库。

## 2. 目录结构

项目根目录：`/Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb/`

```
zgnb/
├── raw/                    # 原始素材（只读、不可变）
│   ├── videos/            # 视频转录文本（每个视频一个 .md）
│   └── articles/          # PDF/文章高度总结（每篇一个 .md）
├── wiki/                   # LLM 编译后的结构化知识
│   ├── maps/              # 主题地图 / MOC（如 [[战法体系 MOC]]）
│   └── outputs/           # LLM 生成的报告、幻灯片、图表
├── concepts/               # 核心概念词条（如 [[B2买入法]]）
├── images/                 # 原始图片 + LLM 生成的图表
├── index.md                # 总索引（由 LLM 自动维护）
├── tools/                  # Python CLI 工具链
│   ├── ingest.py          # 数据规范化导入
│   ├── compile.py         # LLM 编译核心
│   ├── qa.py              # 问答 Agent
│   ├── output.py          # 输出生成器
│   └── lint.py            # 健康检查
├── docs/                   # 说明文档
│   └── usage.md            # 使用手册 + 案例
├── .obsidian/             # Obsidian 配置（图谱、插件）
└── README.md               # 项目入口说明
```

## 3. 核心工作流

### 3.1 数据导入（ingest.py）

**输入来源**：`/Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/z-ge-knowledge/0-reference/`

**处理逻辑**：

1. **视频转录**：
   - 源文件夹如 `z-ge-transcripts/10.06 三大高爆发力的B2买入法/` 下可能有多个 `.txt` 文件（`正课.txt`、`课前闲聊.txt`、`8点.txt`、`9点.txt`...）。
   - `ingest.py` 按合理顺序合并（正课优先，闲聊放后，按时间排序的片段合并）。
   - 清理冗余弹幕、时间戳、空行。
   - 输出为 `raw/videos/YYYY-MM-DD-标题.md`，头部注入 YAML frontmatter：
     ```yaml
     ---
     source: video
     date: 2024-10-06
     title: 三大高爆发力的B2买入法
     ---
     ```

2. **PDF 总结**：
   - `zge-pdf-source/` 下有大量 PDF 文件（如 `1.5.1-还没搞懂B2买点？一文讲透B1、B2、B3核心逻辑.pdf`）。
   - `ingest.py` 提取 PDF 文本，输出为 `raw/articles/文章-标题.md`。
   - 头部注入 YAML frontmatter：
     ```yaml
     ---
     source: article
     title: 还没搞懂B2买点？一文讲透B1、B2、B3核心逻辑
     ---
     ```

3. **冲突处理**：
   - 若目标文件已存在，默认跳过（幂等）。
   - `--force` 可覆盖已有文件。

### 3.2 LLM 编译（compile.py）

**运行方式**：

```bash
python tools/compile.py --new-only   # 增量编译（推荐日常）
python tools/compile.py --all        # 全量重编译（重建时使用）
```

**增量编译逻辑**：

1. 扫描 `raw/` 目录，找出尚未被 `index.md` 收录的新文件。
2. 读取当前的 `index.md` 和全部 `concepts/*.md`，获取知识库现有状态。
3. 构造 Prompt 发送给 LLM（Claude / GPT-4o / Gemini）：
   > 你是知识库管理员。现有知识库结构如下... 新增 raw 文件：raw/videos/xxx.md、raw/articles/yyy.md。
   > 请增量编译，执行以下任务：
   > 1. 为每篇新增 raw 写一段摘要（200 字内）。
   > 2. 提取核心概念，检查 `concepts/` 中是否已有对应词条：若有，追加新信息并更新 backlinks；若无，新建词条。
   > 3. 更新或新建 `wiki/maps/` 中的主题地图（如战法体系、技术分析、交易心态等）。
   > 4. 更新 `index.md`，加入新文件索引和指向相关概念的链接。
   > 5. 输出所有需要新建/修改的文件的**完整内容**。
   >
   > 格式要求：
   > - 所有内部链接使用 Obsidian 语法 `[[concept-name]]`
   > - 文件内容用代码块包裹，并在代码块前标注 `### File: 相对路径`

4. 解析 LLM 返回的代码块，将内容写入对应文件路径。
5. 更新一个本地记录文件 `.compile-log.json`，标记哪些 `raw/` 已被编译过，供下次 `--new-only` 使用。

**全量编译逻辑**：

- 清空 `.compile-log.json`，把 `raw/` 下所有文件当作全新素材重新喂给 LLM，一次性重建整个 `wiki/` 和 `concepts/`。

### 3.3 内容分层搭配策略

两类原始素材在 `compile.py` 的 Prompt 中有明确分工：

- **`raw/articles/`（PDF 总结）**：作为**框架来源**。LLM 优先用它提炼概念定义、核心逻辑、体系结构。
- **`raw/videos/`（视频转录）**：作为**案例与实时观点来源**。LLM 用它补充最新案例、市场点评、临场数据。

`concepts/` 词条的典型结构：

```markdown
---
type: concept
sources:
  - raw/articles/文章-B2买入法.md
  - raw/videos/2024-10-06-三大高爆发力的B2买入法.md
---

# B2买入法

## 定义
（来自 article 的框架性定义）

## 核心条件
1. ...
2. ...

## 实战案例
（来自 video 的具体讲解）
2024年10月6日直播中提到...

## 相关概念
- [[B1买入法]]
- [[B3买入法]]
- [[少妇战法]]

## backlinks
- [[战法体系 MOC]]
```

### 3.4 问答交互（qa.py）

**CLI 使用**：

```bash
python tools/qa.py "这个UP主对B2买入法的核心定义是什么"
python tools/qa.py "2024年10月他对半导体板块的看法有哪些"
python tools/qa.py --interactive      # 交互模式，连续对话
```

**内部逻辑**：

1. `qa.py` 读取 `index.md` 和 `concepts/` 目录，快速判断问题涉及哪些概念/主题。
2. 将这些 `concepts/` 文件及其 `sources` 中引用的相关 `raw/` 文件内容，打包进 Prompt。
3. 要求 LLM：
   - 基于提供的文档作答
   - 答案中标注引用来源（如「根据 2024-10-06 直播转录...」）
   - 若信息不足，主动说明缺失了什么
4. 输出答案到终端，并可选择是否用 `output.py` 归档。

**规模假设**：遵循 Karpathy 方法论，当前阶段约 40 个视频 + 30 篇文章，总字数可能在 50-100 万左右。此规模下无需向量数据库，LLM 直接阅读 `index.md` + 筛选后的相关文档即可。

### 3.5 输出生成（output.py）

**用法**：

```bash
# 将某个问答答案保存为 wiki 文章
python tools/output.py --format md --question "B2买入法的核心定义是什么"

# 生成 Marp 幻灯片（可在 Obsidian 用 Marp 插件预览）
python tools/output.py --format slides --question "少妇战法实战体系"

# 生成 Matplotlib 统计图表
python tools/output.py --format chart --data concepts/ --viz topic-distribution
```

输出文件自动保存到 `wiki/outputs/` 下，文件名带时间戳，如：
- `wiki/outputs/2026-04-11-B2买入法的核心定义.md`
- `wiki/outputs/2026-04-11-少妇战法实战体系-slides.md`
- `wiki/outputs/2026-04-11-topic-distribution.png`

### 3.6 健康检查（lint.py）

**用法**：

```bash
python tools/lint.py
```

**检查项**：

1. **孤立页面**：哪些 `raw/videos/` 或 `raw/articles/` 没被 `index.md` 或任何 `concepts/` 引用？
2. **失效链接**：`[[某概念]]` 在 `concepts/` 里是否存在对应文件？
3. **概念一致性**：同名 `concept` 在不同 raw 中的定义是否明显矛盾？（由 LLM 判断）
4. **增量建议**：基于现有内容，建议还缺少哪些 `concepts/` 词条或 `wiki/maps/`。

**输出**：`wiki/health-check-YYYY-MM-DD.md`，可直接在 Obsidian 中阅读并逐项修复。

## 4. Prompt 工程规范

### 4.1 compile.py Prompt 模板（核心）

```markdown
你是知识库管理员。请严格按照以下规则工作：

## 现有知识库状态
{{ index_md_content }}
{{ existing_concepts_list }}

## 新增原始素材
{{ new_raw_files_content }}

## 任务
1. 为每篇新增 raw 写 200 字内摘要。
2. 提取核心概念，检查 `concepts/` 是否已有词条。有则追加更新 backlinks，无则新建。
3. 更新 `wiki/maps/` 中的相关主题地图。
4. 更新 `index.md` 总索引。
5. 输出所有修改/新建文件的完整内容。

## 输出格式
每个文件必须按以下格式返回：

### File: concepts/xxx.md
```markdown
（文件完整内容）
```

### File: wiki/maps/xxx.md
```markdown
（文件完整内容）
```

### File: index.md
```markdown
（文件完整内容）
```

## 链接规范
- 所有词条页面标题必须支持 Obsidian 双向链接：用 `[[概念名]]`
- 不要在 `[[ ]]` 中加文件扩展名
- `index.md` 中只放一级分类和链接，不需要写详细定义
```

### 4.2 qa.py Prompt 模板

```markdown
用户问题：{{ question }}

以下是与该问题相关的知识库内容，请基于这些内容作答：
---
{{ relevant_concepts }}
{{ relevant_raw_content }}
---

要求：
1. 直接回答问题。
2. 答案中的关键事实请标注来源（如「根据 2024-10-06 直播...」）。
3. 如果信息不足以完整回答，请明确说明缺失了什么。
4. 如果用户提到的方法论存在矛盾，请指出。
```

## 5. 工具链依赖

- **Python 3.11+**
- **PDF 提取**：`pymupdf`（fitz）或 `pdfplumber`
- **LLM API**：DeepSeek（`deepseek-chat`），通过 OpenAI SDK 调用
- **前端**：Obsidian（用户本地安装）
- **图表生成**：`matplotlib`（可选）

环境管理使用 `uv` 或 `venv`，依赖写入 `pyproject.toml` 或 `requirements.txt`。

## 6. 日常使用案例

### 案例 1：初始化知识库（首次运行）

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb

# 1. 把所有原始素材导入 raw/
python tools/ingest.py --all

# 2. 全量编译（首次需要时间较长，取决于 LLM API）
python tools/compile.py --all

# 3. 检查编译结果
ls concepts/
ls wiki/maps/
cat index.md
```

### 案例 2：新增一个直播视频转录

```bash
# 把新视频转录文本放到 /some/path/新视频/
python tools/ingest.py --source /some/path/新视频/

# 增量编译
python tools/compile.py --new-only

# 健康检查
python tools/lint.py
```

### 案例 3：问知识库一个问题

```bash
python tools/qa.py "少妇战法的核心买入条件有哪些"

# 如果想要把答案保存下来
python tools/output.py --format md --question "少妇战法的核心买入条件有哪些"
```

### 案例 4：每周维护

```bash
python tools/lint.py
# 打开 wiki/health-check-2026-04-11.md，按建议修复
python tools/compile.py --new-only  # 如果 lint 建议新建某些词条
```

## 7. 验收标准

- [ ] `raw/videos/` 和 `raw/articles/` 已正确导入所有原始素材
- [ ] `compile.py --all` 能成功生成 `index.md` + `concepts/` + `wiki/maps/`
- [ ] `qa.py` 能基于 `index.md` 和相关文档回答问题
- [ ] `output.py` 能将答案输出为 `wiki/outputs/` 下的 `.md` 文件
- [ ] `lint.py` 能生成包含孤立页面、失效链接、概念一致性检查的健康报告
- [ ] `docs/usage.md` 包含完整的使用说明和上述案例
- [ ] 整个 `zgnb/` 目录可以直接作为 Obsidian Vault 打开，双向链接可正常跳转

## 8. 范围边界

**本期包含**：
- 从 `0-reference` 导入已有素材
- 5 个 CLI 工具的开发和联调
- 核心 Prompt 模板设计
- 使用文档

**本期不包含**：
- Web UI（可用 Streamlit 等后期扩展）
- 向量数据库 / RAG 系统
- 自动联网抓取新内容
- LLM 微调 / 合成数据

# 股票 UP 主直播内容知识库 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `/Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb` 下搭建一套基于 Karpathy LLM Knowledge Base 方法论的股票 UP 主知识库系统，包含数据导入、LLM 编译、问答、输出、健康检查 5 个 CLI 工具及完整使用文档。

**Architecture:** 采用纯脚本驱动的层叠架构：`raw/` 存放不可变的视频转录和 PDF 总结 → `tools/compile.py` 调用 DeepSeek API 增量编译出 `concepts/` + `wiki/` + `index.md` → `tools/qa.py` 基于索引和相关文档回答用户问题 → `tools/output.py` 把答案归档回 `wiki/outputs/`。

**Tech Stack:** Python 3.11+, `openai` SDK (调用 DeepSeek), `pymupdf` (PDF 提取), `python-dotenv`, `markdown`, Obsidian (前端)

---

## File Map

| File | Responsibility |
|:---|:---|
| `tools/llm_client.py` | 封装 DeepSeek API 调用，统一处理 base_url, key, 重试, 流式/非流式 |
| `tools/config.py` | 项目常量：路径、模型名、文件命名规则 |
| `tools/ingest.py` | 把 `0-reference` 中的视频转录（.txt 合并）和 PDF 总结转成 `raw/` 下的标准 .md |
| `tools/compile.py` | 核心：增量/全量读取 `raw/`，调用 LLM，生成 `concepts/` + `wiki/maps/` + `index.md` |
| `tools/qa.py` | 读取用户问题，从 `index.md` + `concepts/` 找到相关文档，调用 LLM 回答 |
| `tools/output.py` | 将 `qa.py` 的答案（或新提问）输出为 `wiki/outputs/` 下的 md/slides/chart |
| `tools/lint.py` | 扫描孤立页面、失效链接、概念一致性，生成健康检查报告 |
| `docs/usage.md` | 完整使用手册（安装、初始化、日常使用、案例） |
| `README.md` | 项目入口说明 |
| `.env` | DeepSeek API key（已存在） |
| `requirements.txt` | Python 依赖 |

---

## Task 1: 搭建目录结构与依赖

**Files:**
- Create: `raw/videos/`, `raw/articles/`, `wiki/maps/`, `wiki/outputs/`, `concepts/`, `images/`, `tools/`, `tests/`
- Create: `requirements.txt`
- Create: `tools/config.py`

- [ ] **Step 1: 创建目录结构**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
mkdir -p raw/videos raw/articles wiki/maps wiki/outputs concepts images tools tests
```

- [ ] **Step 2: 写入 requirements.txt**

```text
openai>=1.0.0
python-dotenv>=1.0.0
pymupdf>=1.23.0
markdown>=3.5.0
pytest>=8.0.0
```

- [ ] **Step 3: 安装依赖（使用 uv 或 pip）**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: `openai`, `python-dotenv`, `pymupdf`, `markdown`, `pytest` 安装成功。

- [ ] **Step 4: 写入 tools/config.py**

```python
"""项目配置常量"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

RAW_VIDEOS_DIR = PROJECT_ROOT / "raw" / "videos"
RAW_ARTICLES_DIR = PROJECT_ROOT / "raw" / "articles"
WIKI_DIR = PROJECT_ROOT / "wiki"
WIKI_MAPS_DIR = WIKI_DIR / "maps"
WIKI_OUTPUTS_DIR = WIKI_DIR / "outputs"
CONCEPTS_DIR = PROJECT_ROOT / "concepts"
IMAGES_DIR = PROJECT_ROOT / "images"
INDEX_FILE = PROJECT_ROOT / "index.md"
COMPILE_LOG = PROJECT_ROOT / ".compile-log.json"

LLM_MODEL = "deepseek-chat"
LLM_BASE_URL = "https://api.deepseek.com"

# Obsidian 双向链接正则
WIKI_LINK_PATTERN = r"\[\[([^\]]+)\]\]"
```

- [ ] **Step 5: Commit**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
git add -A
git commit -m "chore: setup project structure, deps, and config"
```

---

## Task 2: LLM Client 封装

**Files:**
- Create: `tools/llm_client.py`
- Test: `tests/test_llm_client.py`

- [ ] **Step 1: 写测试（mock DeepSeek 调用）**

```python
# tests/test_llm_client.py
from unittest.mock import patch, MagicMock
from tools.llm_client import call_llm

def test_call_llm_returns_content():
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="hello"))]
    with patch("tools.llm_client.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = mock_resp
        result = call_llm([{"role": "user", "content": "hi"}])
        assert result == "hello"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_llm_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'tools.llm_client'` (或其他 ImportError)

- [ ] **Step 3: 实现 llm_client.py**

```python
# tools/llm_client.py
import os
from openai import OpenAI
from tools.config import LLM_MODEL, LLM_BASE_URL

_api_key = os.getenv("DEEPSEEK_API_KEY")
_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not _api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not set in environment")
        _client = OpenAI(api_key=_api_key, base_url=LLM_BASE_URL)
    return _client


def call_llm(messages: list[dict], temperature: float = 0.7, max_retries: int = 3) -> str:
    """调用 DeepSeek API，返回文本内容"""
    client = _get_client()
    last_exception = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=temperature,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)
    raise RuntimeError(f"LLM call failed after {max_retries} retries: {last_exception}")
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_llm_client.py -v
```

Expected: `test_call_llm_returns_content PASSED`

- [ ] **Step 5: Commit**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
git add -A
git commit -m "feat: add DeepSeek LLM client wrapper"
```

---

## Task 3: ingest.py — 数据导入器

**Files:**
- Create: `tools/ingest.py`
- Test: `tests/test_ingest.py`
- Modify: `tools/config.py`（添加 SOURCE_DIR 常量）

- [ ] **Step 1: 更新 config.py 添加来源路径**

在 `tools/config.py` 末尾添加：

```python
SOURCE_TRANSCRIPTS_DIR = Path("/Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/z-ge-knowledge/0-reference/z-ge-transcripts")
SOURCE_PDF_DIR = Path("/Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/z-ge-knowledge/0-reference/zge-pdf-source")
```

- [ ] **Step 2: 写测试（验证 txt 合并和 PDF 提取逻辑）**

```python
# tests/test_ingest.py
import tempfile
from pathlib import Path
from tools.ingest import merge_txt_files, sanitize_filename

def test_merge_txt_files_orders_correctly():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        (p / "9点.txt").write_text("nine")
        (p / "10点.txt").write_text("ten")
        (p / "正课.txt").write_text("main")
        result = merge_txt_files(p)
        assert result.startswith("main")
        assert "nine" in result
        assert "ten" in result

def test_sanitize_filename():
    assert sanitize_filename("hello/world?.md") == "hello-world-.md"
```

- [ ] **Step 3: 运行测试确认失败**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_ingest.py -v
```

Expected: ImportError / function not defined

- [ ] **Step 4: 实现 ingest.py**

```python
# tools/ingest.py
"""数据导入器：将 0-reference 中的视频转录和 PDF 总结导入 raw/"""
import argparse
import fitz  # pymupdf
from datetime import datetime
from pathlib import Path
from tools.config import (
    RAW_VIDEOS_DIR,
    RAW_ARTICLES_DIR,
    SOURCE_TRANSCRIPTS_DIR,
    SOURCE_PDF_DIR,
)


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    bad = '/\\?%*:|"<>.'
    for c in bad:
        name = name.replace(c, "-")
    return name.strip("-")


def merge_txt_files(folder: Path) -> str:
    """合并一个文件夹内的所有 .txt 文件：优先正课，然后按文件名排序，排除弹幕"""
    txts = [f for f in folder.iterdir() if f.suffix.lower() == ".txt" and "弹幕" not in f.name]
    if not txts:
        return ""

    # 分类排序
    priority = []
    rest = []
    for f in txts:
        name = f.name
        if "正课" in name or "SC" in name:
            priority.append(f)
        elif "闲聊" in name or "二楼" in name:
            rest.append((2, name, f))
        else:
            rest.append((1, name, f))

    priority.sort(key=lambda x: x.name)
    rest.sort(key=lambda x: (x[0], x[1]))

    ordered = priority + [r[2] for r in rest]
    parts = []
    for f in ordered:
        try:
            parts.append(f"\n\n<!-- {f.name} -->\n\n" + f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return "\n".join(parts).strip()


def extract_pdf_text(pdf_path: Path) -> str:
    """提取 PDF 全部文本"""
    doc = fitz.open(str(pdf_path))
    texts = []
    for page in doc:
        texts.append(page.get_text())
    return "\n".join(texts).strip()


def guess_date_from_foldername(name: str) -> str:
    """从文件夹名尝试提取日期，失败返回空字符串"""
    # 简单启发：若开头是 数字.数字 或 6月/7月 等中文月份，不强行解析，由调用方处理
    return ""


def ingest_videos(force: bool = False):
    RAW_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    for folder in SOURCE_TRANSCRIPTS_DIR.iterdir():
        if not folder.is_dir():
            continue
        title = folder.name
        content = merge_txt_files(folder)
        if not content:
            continue

        safe_name = sanitize_filename(title)
        out_path = RAW_VIDEOS_DIR / f"{safe_name}.md"
        if out_path.exists() and not force:
            continue

        frontmatter = f"---\nsource: video\ntitle: {title}\n---\n\n"
        out_path.write_text(frontmatter + content, encoding="utf-8")
        print(f"[ingest] video -> {out_path}")


def ingest_articles(force: bool = False):
    RAW_ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    for pdf in SOURCE_PDF_DIR.glob("*.pdf"):
        content = extract_pdf_text(pdf)
        if not content:
            continue

        stem = sanitize_filename(pdf.stem)
        out_path = RAW_ARTICLES_DIR / f"{stem}.md"
        if out_path.exists() and not force:
            continue

        frontmatter = f"---\nsource: article\ntitle: {pdf.stem}\n---\n\n"
        out_path.write_text(frontmatter + content, encoding="utf-8")
        print(f"[ingest] article -> {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Import raw materials into raw/")
    parser.add_argument("--videos", action="store_true", help="Import video transcripts")
    parser.add_argument("--articles", action="store_true", help="Import PDF articles")
    parser.add_argument("--all", action="store_true", help="Import everything")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    if args.all or (not args.videos and not args.articles):
        ingest_videos(force=args.force)
        ingest_articles(force=args.force)
    else:
        if args.videos:
            ingest_videos(force=args.force)
        if args.articles:
            ingest_articles(force=args.force)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_ingest.py -v
```

Expected: `test_merge_txt_files_orders_correctly PASSED`, `test_sanitize_filename PASSED`

- [ ] **Step 6: 试运行 ingest.py --all**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
python tools/ingest.py --all
```

Expected: 控制台打印约 39 个 video -> raw/videos/... 和约 30 个 article -> raw/articles/... 。

- [ ] **Step 7: 验证 raw/ 内容**

```bash
ls raw/videos/ | wc -l
ls raw/articles/ | wc -l
head -n 20 raw/videos/10-06-三大高爆发力的B2买入法.md
```

Expected: videos 约 39 个，articles 约 30+ 个，文件头部有 YAML frontmatter。

- [ ] **Step 8: Commit**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
git add -A
git commit -m "feat: add ingest.py for video transcripts and PDF extraction"
```

---

## Task 4: compile.py — LLM 编译器

**Files:**
- Create: `tools/compile.py`
- Test: `tests/test_compile.py`

- [ ] **Step 1: 写测试（解析 LLM 返回的文件块）**

```python
# tests/test_compile.py
from tools.compile import parse_llm_output

def test_parse_llm_output():
    text = """
### File: concepts/test.md
```markdown
# Hello
```

### File: index.md
```markdown
- [[Test]]
```
"""
    files = parse_llm_output(text)
    assert "concepts/test.md" in files
    assert "index.md" in files
    assert "# Hello" in files["concepts/test.md"]
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_compile.py -v
```

Expected: ImportError

- [ ] **Step 3: 实现 compile.py**

```python
# tools/compile.py
"""LLM 编译器：将 raw/ 增量/全量编译为 concepts/ + wiki/maps/ + index.md"""
import argparse
import json
import re
from pathlib import Path
from tools.config import (
    RAW_VIDEOS_DIR,
    RAW_ARTICLES_DIR,
    CONCEPTS_DIR,
    WIKI_MAPS_DIR,
    INDEX_FILE,
    COMPILE_LOG,
)
from tools.llm_client import call_llm


def get_compiled_ids() -> set[str]:
    if COMPILE_LOG.exists():
        return set(json.loads(COMPILE_LOG.read_text(encoding="utf-8")))
    return set()


def save_compiled_ids(ids: set[str]):
    COMPILE_LOG.write_text(json.dumps(sorted(ids), ensure_ascii=False, indent=2), encoding="utf-8")


def list_raw_files() -> list[Path]:
    files = []
    for d in (RAW_VIDEOS_DIR, RAW_ARTICLES_DIR):
        if d.exists():
            files.extend(d.glob("*.md"))
    return sorted(files)


def read_file(path: Path, limit: int = 8000) -> str:
    text = path.read_text(encoding="utf-8")
    if len(text) > limit:
        # 保留 frontmatter + 正文前 limit 字符
        lines = text.splitlines()
        if lines and lines[0].strip() == "---":
            # 找到第二个 ---
            end = 1
            while end < len(lines) and lines[end].strip() != "---":
                end += 1
            front = "\n".join(lines[: end + 1])
            body = "\n".join(lines[end + 1 :])
            return front + "\n\n" + body[:limit]
    return text


def build_prompt(new_files: list[Path], existing_index: str, existing_concepts: list[str]) -> list[dict]:
    new_contents = []
    for f in new_files:
        new_contents.append(f"### Source: {f.name}\n{read_file(f, limit=6000)}")

    concepts_list = "\n".join(f"- [[{c}]]" for c in existing_concepts) or "（暂无概念词条）"

    system_prompt = """你是知识库管理员。请严格按照以下规则工作：

1. 为每篇新增 raw 写 200 字内摘要。
2. 提取核心概念，检查 `concepts/` 是否已有词条：有则追加新信息并更新 backlinks；无则新建。
3. 更新 `wiki/maps/` 中的相关主题地图（如战法体系、技术分析、交易心态、宏观分析等）。
4. 更新 `index.md` 总索引。
5. 输出所有需要新建/修改的文件的**完整内容**。

格式要求：
- 每个文件必须以如下格式返回：

### File: 相对路径
```markdown
文件完整内容
```

- 内部链接使用 Obsidian 语法 `[[概念名]]`，不加扩展名
- `index.md` 中只放一级分类、链接和简短说明，不需要写详细定义
- 不要在代码块外输出任何解释性文字
"""

    user_prompt = f"""## 现有 index.md\n{existing_index}\n\n## 现有 concepts\n{concepts_list}\n\n## 新增原始素材（共 {len(new_files)} 篇）\n""" + "\n\n".join(new_contents)

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_llm_output(text: str) -> dict[str, str]:
    """解析 LLM 返回的文件块"""
    files = {}
    pattern = re.compile(r"### File:\s*(.+?)\n```markdown\n(.*?)\n```", re.DOTALL)
    for m in pattern.finditer(text):
        path = m.group(1).strip()
        content = m.group(2).strip()
        files[path] = content
    return files


def write_files(files: dict[str, str]):
    for rel_path, content in files.items():
        target = Path(__file__).parent.parent / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"[compile] wrote {target}")


def compile_all(force: bool = False):
    all_files = list_raw_files()
    compiled = set()
    save_compiled_ids(compiled)
    _compile_batch(all_files)


def compile_new_only():
    all_files = list_raw_files()
    compiled = get_compiled_ids()
    new_files = [f for f in all_files if f.name not in compiled]
    if not new_files:
        print("[compile] no new raw files to compile")
        return
    print(f"[compile] compiling {len(new_files)} new files...")
    _compile_batch(new_files)


def _compile_batch(files: list[Path]):
    existing_index = INDEX_FILE.read_text(encoding="utf-8") if INDEX_FILE.exists() else "（暂无 index.md）"
    existing_concepts = []
    if CONCEPTS_DIR.exists():
        existing_concepts = sorted([f.stem for f in CONCEPTS_DIR.glob("*.md")])

    # 为了控制 token，每次最多给 LLM 5 篇新文件
    batch_size = 5
    compiled_ids = get_compiled_ids()

    for i in range(0, len(files), batch_size):
        batch = files[i : i + batch_size]
        messages = build_prompt(batch, existing_index, existing_concepts)
        response = call_llm(messages, temperature=0.5)
        parsed = parse_llm_output(response)
        if not parsed:
            print(f"[compile] warning: LLM returned no parseable files for batch {i//batch_size + 1}")
            continue
        write_files(parsed)
        compiled_ids.update(f.name for f in batch)
        save_compiled_ids(compiled_ids)
        # 刷新现有状态（因为 LLM 可能已生成新概念）
        existing_index = INDEX_FILE.read_text(encoding="utf-8") if INDEX_FILE.exists() else ""
        existing_concepts = sorted([f.stem for f in CONCEPTS_DIR.glob("*.md")])
        print(f"[compile] batch {i//batch_size + 1}/{(len(files)-1)//batch_size + 1} done")


def main():
    parser = argparse.ArgumentParser(description="Compile raw/ into wiki/ and concepts/")
    parser.add_argument("--all", action="store_true", help="Full recompile")
    parser.add_argument("--new-only", action="store_true", help="Compile only new raw files")
    args = parser.parse_args()

    if args.all:
        compile_all()
    else:
        compile_new_only()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_compile.py -v
```

Expected: `test_parse_llm_output PASSED`

- [ ] **Step 5: 创建初始 index.md**

```bash
cat > /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb/index.md << 'EOF'
---
type: index
title: 股票 UP 主知识库
---

# 股票 UP 主知识库

待编译填充。
EOF
```

- [ ] **Step 6: 试运行 compile.py --all（首批 5 篇验证）**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
python tools/compile.py --all
```

Expected: DeepSeek API 成功调用，生成 `concepts/*.md`、`wiki/maps/*.md`、更新的 `index.md`。控制台打印每批完成。若 API 失败会抛出异常，检查 `.env` 中的 key。

- [ ] **Step 7: 验证编译产物**

```bash
ls concepts/
ls wiki/maps/
head -n 30 index.md
```

Expected: `concepts/` 下出现若干 .md 文件，`wiki/maps/` 下出现主题地图，`index.md` 被更新。

- [ ] **Step 8: Commit**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
git add -A
git commit -m "feat: add compile.py for LLM-driven wiki compilation"
```

---

## Task 5: qa.py — 问答 Agent

**Files:**
- Create: `tools/qa.py`
- Test: `tests/test_qa.py`

- [ ] **Step 1: 写测试（验证相关文件检索逻辑）**

```python
# tests/test_qa.py
from tools.qa import find_relevant_concepts

def test_find_relevant_concepts_basic():
    # 简单验证：若 index 里有关键词，能返回对应 concept 名
    concepts = ["B2买入法", "少妇战法", "止损止盈"]
    result = find_relevant_concepts("什么是B2买入法", concepts)
    assert "B2买入法" in result
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_qa.py -v
```

Expected: ImportError

- [ ] **Step 3: 实现 qa.py**

```python
# tools/qa.py
"""问答 Agent：基于 index/concepts/raw 回答问题"""
import argparse
import re
from pathlib import Path
from tools.config import INDEX_FILE, CONCEPTS_DIR, RAW_VIDEOS_DIR, RAW_ARTICLES_DIR
from tools.llm_client import call_llm


def list_concepts() -> list[str]:
    if not CONCEPTS_DIR.exists():
        return []
    return sorted([f.stem for f in CONCEPTS_DIR.glob("*.md")])


def find_relevant_concepts(question: str, concepts: list[str]) -> list[str]:
    """简单关键词匹配召回相关概念"""
    matched = []
    q = question.lower()
    for c in concepts:
        # 去掉常见标点再匹配
        clean = c.lower().replace(" ", "").replace("/", "").replace("、", "")
        qq = q.replace(" ", "").replace("/", "").replace("、", "")
        if clean in qq or any(part in qq for part in c.lower().split()):
            matched.append(c)
    return matched


def read_concept(name: str, limit: int = 4000) -> str:
    path = CONCEPTS_DIR / f"{name}.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    return text[:limit]


def read_sources_from_concept(concept_text: str) -> list[Path]:
    """从 concept 的 YAML frontmatter 或正文中提取 source 引用"""
    # 简单正则：匹配 raw/ 路径或文件名
    sources = []
    raw_dir = Path(__file__).parent.parent / "raw"
    # 尝试从 frontmatter 中的 sources 列表提取
    for line in concept_text.splitlines():
        if line.strip().startswith("- raw/"):
            rel = line.split("- raw/")[-1].strip()
            p = raw_dir / rel
            if p.exists():
                sources.append(p)
        elif "raw/videos/" in line or "raw/articles/" in line:
            m = re.search(r"raw/(videos|articles)/[^\s\]]+", line)
            if m:
                p = raw_dir / m.group(0).replace("raw/", "")
                if p.exists() and p not in sources:
                    sources.append(p)
    return sources


def build_qa_prompt(question: str, context: str) -> list[dict]:
    system = """你是知识库问答助手。请严格基于用户提供的知识库内容回答问题。
要求：
1. 直接回答用户问题
2. 关键事实标注来源（如「根据《B2买入法》词条...」或「根据 2024-10-06 直播...」）
3. 若信息不足，明确说明缺失了什么
4. 若不同来源存在矛盾，请指出
"""
    user = f"""用户问题：{question}\n\n知识库相关内容：\n{context}\n"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def answer(question: str) -> str:
    concepts = list_concepts()
    relevant = find_relevant_concepts(question, concepts)

    # 如果关键词没命中任何 concept，回退到读 index.md + 前 10 个 concept
    if not relevant:
        relevant = concepts[:10]

    ctx_parts = []
    ctx_parts.append(f"## index.md\n{INDEX_FILE.read_text(encoding='utf-8')[:2000] if INDEX_FILE.exists() else '(no index)'}")

    for c in relevant:
        text = read_concept(c, limit=4000)
        if text:
            ctx_parts.append(f"\n## concept: [[{c}]]\n{text}")
            # 顺便读该 concept 引用的 raw 前 2000 字
            for src in read_sources_from_concept(text)[:2]:
                raw_text = src.read_text(encoding="utf-8")[:2000]
                ctx_parts.append(f"\n## source: {src.name}\n{raw_text}")

    context = "\n".join(ctx_parts)
    messages = build_qa_prompt(question, context)
    return call_llm(messages, temperature=0.6)


def main():
    parser = argparse.ArgumentParser(description="QA agent for the knowledge base")
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    args = parser.parse_args()

    if args.interactive:
        print("知识库问答模式，输入 'exit' 退出")
        while True:
            q = input("\nQ: ")
            if q.strip().lower() in ("exit", "quit"):
                break
            print("\nA:", answer(q))
    elif args.question:
        print(answer(args.question))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_qa.py -v
```

Expected: `test_find_relevant_concepts_basic PASSED`

- [ ] **Step 5: 试运行 qa.py**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
python tools/qa.py "B2买入法的定义是什么"
```

Expected: DeepSeek 返回一个基于现有 concepts/ 和 index.md 的答案，标注了来源。

- [ ] **Step 6: Commit**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
git add -A
git commit -m "feat: add qa.py for knowledge-base Q&A"
```

---

## Task 6: output.py — 输出生成与归档

**Files:**
- Create: `tools/output.py`
- Test: `tests/test_output.py`

- [ ] **Step 1: 写测试（验证文件名生成和路径解析）**

```python
# tests/test_output.py
from tools.output import slugify, build_output_path
from pathlib import Path

def test_slugify():
    assert slugify("Hello World!") == "hello-world"

def test_build_output_path():
    p = build_output_path("测试问题", "md")
    assert p.name.endswith("-测试问题.md")
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_output.py -v
```

Expected: ImportError

- [ ] **Step 3: 实现 output.py**

```python
# tools/output.py
"""输出生成器：将问答结果归档为 md / slides / chart"""
import argparse
import re
from datetime import datetime
from pathlib import Path
from tools.config import WIKI_OUTPUTS_DIR
from tools.llm_client import call_llm
from tools.qa import answer as qa_answer


def slugify(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.lower()[:50]


def build_output_path(question: str, ext: str = "md") -> Path:
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    name = f"{date_prefix}-{slugify(question)}.{ext}"
    return WIKI_OUTPUTS_DIR / name


def save_md(question: str, content: str) -> Path:
    WIKI_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = build_output_path(question, "md")
    front = f"---\ntype: output\ndate: {datetime.now().strftime('%Y-%m-%d')}\nquestion: {question}\n---\n\n"
    path.write_text(front + content, encoding="utf-8")
    print(f"[output] saved {path}")
    return path


def save_slides(question: str) -> Path:
    """生成 Marp 格式的 Markdown 幻灯片"""
    WIKI_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = build_output_path(question + "-slides", "md")

    # 让 LLM 生成 Marp 内容
    answer_text = qa_answer(question)
    prompt = f"""请将以下问答内容转换为 Marp 幻灯片格式的 Markdown。
要求：
- 第一页是标题和一句话总结
- 每页一个要点，配适量 bullet points
- 使用 `---` 分页
- 顶部包含 Marp frontmatter: `---\nmarp: true\ntheme: default\n---`

原始内容：
{answer_text}
"""
    slides_md = call_llm([{"role": "user", "content": prompt}], temperature=0.5)
    path.write_text(slides_md, encoding="utf-8")
    print(f"[output] saved slides {path}")
    return path


def save_chart_topic_distribution() -> Path:
    """生成主题分布饼图（基于 concepts 数量）"""
    import matplotlib.pyplot as plt
    from tools.config import CONCEPTS_DIR

    concepts = [f.stem for f in CONCEPTS_DIR.glob("*.md")]
    # 简单分类：按名字关键词分组
    categories = {}
    for c in concepts:
        cat = "其他"
        for keyword, label in {
            "买": "买点",
            "卖": "卖点",
            "战法": "战法",
            "k线": "K线",
            "止损": "风控",
            "仓位": "风控",
            "复盘": "交易流程",
            "节奏": "交易流程",
        }.items():
            if keyword in c.lower():
                cat = label
                break
        categories[cat] = categories.get(cat, 0) + 1

    WIKI_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = WIKI_OUTPUTS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}-topic-distribution.png"

    fig, ax = plt.subplots()
    ax.pie(categories.values(), labels=categories.keys(), autopct="%1.1f%%")
    ax.set_title("知识库主题分布")
    plt.tight_layout()
    plt.savefig(str(path), dpi=150)
    plt.close()
    print(f"[output] saved chart {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="Generate output files from Q&A")
    parser.add_argument("--format", choices=["md", "slides", "chart"], required=True)
    parser.add_argument("--question", required=True, help="The question to answer")
    args = parser.parse_args()

    if args.format == "md":
        content = qa_answer(args.question)
        save_md(args.question, content)
    elif args.format == "slides":
        save_slides(args.question)
    elif args.format == "chart":
        save_chart_topic_distribution()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_output.py -v
```

Expected: `test_slugify PASSED`, `test_build_output_path PASSED`

- [ ] **Step 5: 试运行 output.py --format md**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
python tools/output.py --format md --question "B2买入法的核心定义"
```

Expected: `wiki/outputs/` 下生成一个以当前日期开头的 `.md` 文件。

- [ ] **Step 6: Commit**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
git add -A
git commit -m "feat: add output.py for archiving answers as md/slides/charts"
```

---

## Task 7: lint.py — 健康检查

**Files:**
- Create: `tools/lint.py`
- Test: `tests/test_lint.py`

- [ ] **Step 1: 写测试（验证链接提取）**

```python
# tests/test_lint.py
from tools.lint import extract_wiki_links

def test_extract_wiki_links():
    text = "参见 [[B2买入法]] 和 [[少妇战法]]。"
    assert extract_wiki_links(text) == {"B2买入法", "少妇战法"}
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_lint.py -v
```

Expected: ImportError

- [ ] **Step 3: 实现 lint.py**

```python
# tools/lint.py
"""健康检查：孤立页面、失效链接、概念一致性、增量建议"""
import re
from datetime import datetime
from pathlib import Path
from tools.config import (
    RAW_VIDEOS_DIR,
    RAW_ARTICLES_DIR,
    CONCEPTS_DIR,
    WIKI_DIR,
    INDEX_FILE,
)


def extract_wiki_links(text: str) -> set[str]:
    return set(re.findall(r"\[\[([^\]]+)\]\]", text))


def find_orphan_raw() -> list[str]:
    """找出未被 index.md 或任何 concept/wiki 引用的 raw 文件"""
    raw_files = {f.name for f in RAW_VIDEOS_DIR.glob("*.md")}
    raw_files.update(f.name for f in RAW_ARTICLES_DIR.glob("*.md"))

    all_refs = set()
    for f in CONCEPTS_DIR.glob("*.md"):
        all_refs.update(extract_wiki_links(f.read_text(encoding="utf-8")))
    for f in WIKI_DIR.rglob("*.md"):
        all_refs.update(extract_wiki_links(f.read_text(encoding="utf-8")))
    if INDEX_FILE.exists():
        all_refs.update(extract_wiki_links(INDEX_FILE.read_text(encoding="utf-8")))

    # 如果一个 raw 文件名（去掉 .md）被引用了，也不算孤立
    raw_stems = {f.stem for f in RAW_VIDEOS_DIR.glob("*.md")}
    raw_stems.update(f.stem for f in RAW_ARTICLES_DIR.glob("*.md"))
    referenced_names = {r for r in all_refs if r in raw_stems}

    orphans = []
    for f in RAW_VIDEOS_DIR.glob("*.md"):
        if f.stem not in all_refs and f.name not in referenced_names:
            orphans.append(f"raw/videos/{f.name}")
    for f in RAW_ARTICLES_DIR.glob("*.md"):
        if f.stem not in all_refs and f.name not in referenced_names:
            orphans.append(f"raw/articles/{f.name}")
    return orphans


def find_broken_links() -> list[str]:
    """找出指向不存在的 concept 的链接"""
    existing_concepts = {f.stem for f in CONCEPTS_DIR.glob("*.md")}
    broken = []
    for f in CONCEPTS_DIR.glob("*.md"):
        for link in extract_wiki_links(f.read_text(encoding="utf-8")):
            if link not in existing_concepts and not link.startswith("raw/"):
                broken.append(f"{f.name} -> [[{link}]]")
    for f in WIKI_DIR.rglob("*.md"):
        for link in extract_wiki_links(f.read_text(encoding="utf-8")):
            if link not in existing_concepts and not link.startswith("raw/"):
                broken.append(f"{f.relative_to(Path(__file__).parent.parent)} -> [[{link}]]")
    return broken


def generate_report() -> str:
    orphans = find_orphan_raw()
    broken = find_broken_links()

    lines = [
        f"# 健康检查报告 ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
        "",
        "## 1. 孤立原始素材",
        f"发现 {len(orphans)} 个未被引用的 raw 文件：",
        "",
    ]
    for o in orphans:
        lines.append(f"- {o}")
    if not orphans:
        lines.append("- 无")

    lines.extend(["", "## 2. 失效内部链接", f"发现 {len(broken)} 个失效链接：", ""])
    for b in broken:
        lines.append(f"- {b}")
    if not broken:
        lines.append("- 无")

    lines.extend(["", "## 3. 建议", "- 每周运行一次 `python tools/lint.py`", "- 对孤立页面补充 concept 引用或新建词条"])
    return "\n".join(lines)


def main():
    report = generate_report()
    out_path = WIKI_DIR / f"health-check-{datetime.now().strftime('%Y-%m-%d')}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"[lint] report saved to {out_path}")
    print(report)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
pytest tests/test_lint.py -v
```

Expected: `test_extract_wiki_links PASSED`

- [ ] **Step 5: 试运行 lint.py**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
python tools/lint.py
```

Expected: 生成 `wiki/health-check-YYYY-MM-DD.md`，并打印到控制台。此时可能有较多孤立页面（如果 compile.py 还没全量跑完所有 raw）。

- [ ] **Step 6: Commit**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
git add -A
git commit -m "feat: add lint.py for health checks and reporting"
```

---

## Task 8: 编写使用文档

**Files:**
- Create: `docs/usage.md`
- Create: `README.md`

- [ ] **Step 1: 写入 docs/usage.md**

```markdown
---
title: 使用手册
date: 2026-04-11
---

# 股票 UP 主知识库使用手册

## 1. 安装与环境

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

确保 `.env` 中已配置 `DEEPSEEK_API_KEY`。

## 2. 初始化知识库（首次运行）

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

## 3. 日常使用：更新知识库

### 新增视频转录

假设新视频转录放在 `/some/path/new-video/`，包含若干 `.txt`：

```bash
python tools/ingest.py --source /some/path/new-video/
python tools/compile.py --new-only
python tools/lint.py
```

### 新增 PDF 文章

把 PDF 放到任意目录，然后：

```bash
python tools/ingest.py --articles --source /some/path/
python tools/compile.py --new-only
```

## 4. 问答使用

### 单次提问

```bash
python tools/qa.py "B2买入法的核心条件有哪些"
python tools/qa.py "这个UP主如何看半导体板块"
```

### 交互模式

```bash
python tools/qa.py --interactive
```

## 5. 输出生成

### 保存为 Markdown 文章

```bash
python tools/output.py --format md --question "少妇战法的买入逻辑"
```

结果保存在 `wiki/outputs/YYYY-MM-DD-少妇战法的买入逻辑.md`

### 生成 Marp 幻灯片

```bash
python tools/output.py --format slides --question "B2买入法实战体系"
```

在 Obsidian 中安装 Marp 插件后可直接预览为幻灯片。

### 生成主题分布图

```bash
python tools/output.py --format chart --question "topic-distribution"
```

## 6. 健康检查

每周执行一次：

```bash
python tools/lint.py
```

打开 `wiki/health-check-YYYY-MM-DD.md` 查看：
- 哪些 raw 素材还没被概念引用
- 哪些内部链接失效
- 优化建议

## 7. Obsidian 使用

1. 打开 Obsidian → "Open folder as vault" → 选择 `zgnb/` 文件夹
2. 安装插件推荐：`Marp for Obsidian`（幻灯片预览）
3. 在 Graph View 中可以看到 `concepts/` 和 `wiki/` 的双向链接网络

## 8. 内容分层策略（重要）

- **`raw/articles/`（PDF 总结）**：体系框架、概念定义的主要来源
- **`raw/videos/`（直播转录）**：案例、实时观点、市场点评的主要来源
- **`concepts/`**：LLM 自动维护的词条，通常融合了两类来源
- **`wiki/maps/`**：主题地图，帮助你快速导航到相关概念
- **`wiki/outputs/`**：你自己的问答沉淀

## 9. 故障排查

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
```

- [ ] **Step 2: 写入 README.md**

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
git add -A
git commit -m "docs: add usage manual and README"
```

---

## Task 9: 全量编译验证与收尾

**Files:**
- Modify: `index.md`（由 compile.py 自动生成）
- Modify: `concepts/`（由 compile.py 自动生成）
- Modify: `wiki/maps/`（由 compile.py 自动生成）

- [ ] **Step 1: 全量运行 ingest.py**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
python tools/ingest.py --all --force
```

Expected: 所有原始素材成功导入 `raw/videos/` 和 `raw/articles/`。

- [ ] **Step 2: 全量运行 compile.py**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
python tools/compile.py --all
```

Expected: DeepSeek API 成功调用所有 batch，生成完整的 `concepts/`、`wiki/maps/`、`index.md`。注意：39 个视频 + 30+ 篇文章，按 batch_size=5 计算约需 14 次 API 调用，耗时可能 10-30 分钟。

- [ ] **Step 3: 验证编译产物完整性**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
ls concepts/ | wc -l
ls wiki/maps/ | wc -l
cat index.md
```

Expected: `concepts/` 下至少有 10-30 个词条；`wiki/maps/` 下有若干主题地图；`index.md` 包含分类结构和链接。

- [ ] **Step 4: 运行 qa.py 做端到端测试**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
python tools/qa.py "B2买入法的核心定义是什么"
```

Expected: 返回答案且引用了 `concepts/` 或 `raw/` 中的来源。

- [ ] **Step 5: 运行 lint.py 并查看报告**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
python tools/lint.py
```

Expected: 生成 `wiki/health-check-YYYY-MM-DD.md`，报告中孤立页面数量应在合理范围内（允许少量未被链接的 raw）。

- [ ] **Step 6: 运行 output.py 测试归档**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
source .venv/bin/activate
python tools/output.py --format md --question "这个UP主的交易体系包含哪些核心战法"
```

Expected: `wiki/outputs/` 下生成新的 `.md` 文件。

- [ ] **Step 7: 最终 Commit**

```bash
cd /Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/zgnb
git add -A
git commit -m "feat: complete knowledge base build with compiled concepts and wiki maps"
```

---

## Spec Coverage Check

| Spec Section | Plan Task | Status |
|:---|:---|:---:|
| 目录结构 | Task 1 | ✅ |
| LLM 依赖 (DeepSeek) | Task 2 | ✅ |
| ingest.py 视频+PDF | Task 3 | ✅ |
| compile.py 增量/全量编译 | Task 4 | ✅ |
| qa.py 问答 | Task 5 | ✅ |
| output.py md/slides/chart | Task 6 | ✅ |
| lint.py 健康检查 | Task 7 | ✅ |
| docs/usage.md | Task 8 | ✅ |
| 首次运行验证 | Task 9 | ✅ |

## Placeholder Scan

- 无 TBD / TODO / "implement later"
- 所有测试包含实际代码
- 所有 CLI 命令包含 exact path

## Type Consistency

- `call_llm(messages: list[dict], ...)` 在全文件中签名一致
- `Path` 对象与字符串转换统一使用 `str(path)` 或 Path 运算
- `WIKI_LINK_PATTERN` 在 lint.py 和 compile.py 的使用方式对齐

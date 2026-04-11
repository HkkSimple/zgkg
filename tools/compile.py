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
        lines = text.splitlines()
        if lines and lines[0].strip() == "---":
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
5. 输出所有需要新建/修改的文件的完整内容。

格式要求：
- 每个文件必须以如下格式返回：

### File: 相对路径
```markdown
文件完整内容
```

- 内部链接使用 Obsidian 语法 [[概念名]]，不加扩展名
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

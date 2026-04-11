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
    raw = set(re.findall(r"\[\[([^\]]+)\]\]", text))
    # handle pipe links: [[Target|Display]] -> Target
    return {r.split("|")[0].strip() for r in raw}


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

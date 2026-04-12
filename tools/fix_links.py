"""自动修复失效链接：为所有不存在的 [[concept]] 创建 stub 页面"""
import re
from pathlib import Path
from tools.config import CONCEPTS_DIR, WIKI_DIR, INDEX_FILE, WIKI_LINK_PATTERN


def extract_wiki_links(text: str) -> set[str]:
    return set(re.findall(WIKI_LINK_PATTERN, text))


def extract_target(link: str) -> str:
    """处理 [[A|B]] 管道链接，返回实际目标 A"""
    if "|" in link:
        return link.split("|")[0].strip()
    return link.strip()


def find_missing_concepts() -> set[str]:
    existing = {f.stem for f in CONCEPTS_DIR.glob("*.md")}
    all_links = set()
    for f in CONCEPTS_DIR.glob("*.md"):
        for link in extract_wiki_links(f.read_text(encoding="utf-8")):
            all_links.add(extract_target(link))
    for f in WIKI_DIR.rglob("*.md"):
        for link in extract_wiki_links(f.read_text(encoding="utf-8")):
            all_links.add(extract_target(link))
    if INDEX_FILE.exists():
        for link in extract_wiki_links(INDEX_FILE.read_text(encoding="utf-8")):
            all_links.add(extract_target(link))
    # 排除明显不是 concept 的（如 raw/ 路径、带 # 锚点的链接）
    return {l for l in all_links if not l.startswith("raw/") and "#" not in l and l not in existing}


def create_stubs():
    missing = find_missing_concepts()
    if not missing:
        print("[fix_links] no missing concepts")
        return
    for name in sorted(missing):
        path = CONCEPTS_DIR / f"{name}.md"
        path.write_text(
            f"---\ntype: concept\nstub: true\n---\n\n# {name}\n\n"
            "该词条尚未完成详细定义，由 Link Fixer 自动创建占位。\n"
            "后续可通过 `compile.py` 增量编译或手动补充内容。\n",
            encoding="utf-8"
        )
        print(f"[fix_links] stub created: {path}")
    print(f"[fix_links] total stubs created: {len(missing)}")


if __name__ == "__main__":
    create_stubs()

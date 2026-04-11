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
    sources = []
    raw_dir = Path(__file__).parent.parent / "raw"
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

    if not relevant:
        relevant = concepts[:10]

    ctx_parts = []
    ctx_parts.append(f"## index.md\n{INDEX_FILE.read_text(encoding='utf-8')[:2000] if INDEX_FILE.exists() else '(no index)'}")

    for c in relevant:
        text = read_concept(c, limit=4000)
        if text:
            ctx_parts.append(f"\n## concept: [[{c}]]\n{text}")
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

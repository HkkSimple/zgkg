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

    answer_text = qa_answer(question)
    prompt = f"""请将以下问答内容转换为 Marp 幻灯片格式的 Markdown。
要求：
- 第一页是标题和一句话总结
- 每页一个要点，配适量 bullet points
- 使用 --- 分页
- 顶部包含 Marp frontmatter: ---\nmarp: true\ntheme: default\n---

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

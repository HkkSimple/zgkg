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

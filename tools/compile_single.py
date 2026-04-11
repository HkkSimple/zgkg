"""单独编译一个 raw 文件"""
import sys
from pathlib import Path
from tools.compile import build_prompt, parse_llm_output, write_files, INDEX_FILE, CONCEPTS_DIR
from tools.llm_client import call_llm

def compile_one(raw_path: Path):
    existing_index = INDEX_FILE.read_text(encoding="utf-8") if INDEX_FILE.exists() else "（暂无 index.md）"
    existing_concepts = sorted([f.stem for f in CONCEPTS_DIR.glob("*.md")])
    messages = build_prompt([raw_path], existing_index, existing_concepts)
    print(f"[compile_single] processing {raw_path.name}...")
    response = call_llm(messages, temperature=0.5)
    parsed = parse_llm_output(response)
    if not parsed:
        print(f"[compile_single] warning: no parseable output for {raw_path.name}")
        print("Raw response snippet:")
        print(response[:500])
        return
    write_files(parsed)
    print(f"[compile_single] done {raw_path.name}")

if __name__ == "__main__":
    for name in sys.argv[1:]:
        p = Path("raw/videos") / name
        if not p.exists():
            p = Path("raw/articles") / name
        if p.exists():
            compile_one(p)
        else:
            print(f"File not found: {name}")

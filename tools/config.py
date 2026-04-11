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

SOURCE_TRANSCRIPTS_DIR = Path("/Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/z-ge-knowledge/0-reference/z-ge-transcripts")
SOURCE_PDF_DIR = Path("/Volumes/ZT/OpenClaw-Box/workspace/Kbrain/projects/z-ge-knowledge/0-reference/zge-pdf-source")

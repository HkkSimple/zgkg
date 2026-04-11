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
        assert "main" in result and result.index("main") < result.index("ten")
        assert "nine" in result
        assert "ten" in result

def test_sanitize_filename():
    assert sanitize_filename("hello/world?.md") == "hello-world--md"

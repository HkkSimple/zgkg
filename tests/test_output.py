from tools.output import slugify, build_output_path
from pathlib import Path

def test_slugify():
    assert slugify("Hello World!") == "hello-world"

def test_build_output_path():
    p = build_output_path("测试问题", "md")
    assert p.name.endswith("-测试问题.md")

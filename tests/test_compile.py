from tools.compile import parse_llm_output

def test_parse_llm_output():
    text = """
### File: concepts/test.md
```markdown
# Hello
```

### File: index.md
```markdown
- [[Test]]
```
"""
    files = parse_llm_output(text)
    assert "concepts/test.md" in files
    assert "index.md" in files
    assert "# Hello" in files["concepts/test.md"]

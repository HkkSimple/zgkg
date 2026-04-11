from tools.lint import extract_wiki_links

def test_extract_wiki_links():
    text = "参见 [[B2买入法]] 和 [[少妇战法]]。"
    assert extract_wiki_links(text) == {"B2买入法", "少妇战法"}

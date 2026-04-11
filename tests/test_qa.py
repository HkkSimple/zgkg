from tools.qa import find_relevant_concepts

def test_find_relevant_concepts_basic():
    concepts = ["B2买入法", "少妇战法", "止损止盈"]
    result = find_relevant_concepts("什么是B2买入法", concepts)
    assert "B2买入法" in result

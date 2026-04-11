from unittest.mock import patch, MagicMock
from tools.llm_client import call_llm

def test_call_llm_returns_content():
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="hello"))]
    with patch("tools.llm_client.OpenAI") as MockClient, \
         patch("tools.llm_client._api_key", "test-key"):
        MockClient.return_value.chat.completions.create.return_value = mock_resp
        result = call_llm([{"role": "user", "content": "hi"}])
        assert result == "hello"

# tools/llm_client.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from tools.config import LLM_MODEL, LLM_BASE_URL

load_dotenv()
_api_key = os.getenv("DEEPSEEK_API_KEY")
_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not _api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not set in environment")
        _client = OpenAI(api_key=_api_key, base_url=LLM_BASE_URL)
    return _client


def call_llm(messages: list[dict], temperature: float = 0.7, max_retries: int = 3) -> str:
    """调用 DeepSeek API，返回文本内容"""
    client = _get_client()
    last_exception = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=temperature,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)
    raise RuntimeError(f"LLM call failed after {max_retries} retries: {last_exception}")

# tools/llm_client.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from tools.config import LLM_BASE_URL

load_dotenv()
_api_key = os.getenv("DEEPSEEK_API_KEY")
_client = None

# 可用模型：
# - deepseek-v4-flash（默认，速度快、成本低）
# - deepseek-v4-pro（深度思考，质量更高）
#
# 推理模式（reasoning_effort）：
# - "high"（默认，开启深度思考）
# - "max"（最高质量推理，消耗更多 token）
# - 不传或 None（非思考模式，直接输出答案）
#
# 思考模式（通过 extra_body 开启，可读取 reasoning_content）：
# extra_body={"thinking": {"type": "enabled"}}

DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_REASONING_EFFORT = "high"


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not _api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not set in environment")
        _client = OpenAI(api_key=_api_key, base_url=LLM_BASE_URL)
    return _client


def call_llm(
    messages: list[dict],
    model: str = None,
    temperature: float = 0.7,
    reasoning_effort: str = None,
    extra_body: dict = None,
    max_retries: int = 2,
) -> str:
    """调用 DeepSeek API，返回文本内容。

    参数:
        messages: 对话消息列表
        model: 模型名称，默认 deepseek-v4-flash
        temperature: 采样温度
        reasoning_effort: 推理强度，默认 "high"，设为 None 可关闭思考模式
        extra_body: 额外请求体，如 {"thinking": {"type": "enabled"}}
        max_retries: 最大重试次数
    """
    client = _get_client()

    model = model or DEFAULT_MODEL
    reasoning_effort = reasoning_effort if reasoning_effort is not None else DEFAULT_REASONING_EFFORT

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }

    if reasoning_effort:
        kwargs["reasoning_effort"] = reasoning_effort

    if extra_body:
        kwargs["extra_body"] = extra_body

    last_exception = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)
    raise RuntimeError(f"LLM call failed after {max_retries} retries: {last_exception}")

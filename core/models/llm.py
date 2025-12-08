"""
大语言模型封装
统一管理LLM相关功能
使用 OpenRouter API 统一管理所有大模型调用
"""
import os
import re
from openai import OpenAI
from config.settings import settings


def create_openrouter_client(model: str = None) -> OpenAI:
    """
    创建 OpenRouter 客户端
    
    Args:
        model: 模型名称，如果为None则使用配置中的默认模型
        
    Returns:
        OpenAI客户端实例（配置为 OpenRouter API）
    """
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY 未配置，请设置环境变量或 .env 文件")
    
    client = OpenAI(
        api_key=api_key,
        base_url='https://openrouter.ai/api/v1',
        default_headers={
            "HTTP-Referer": "https://github.com/your-repo",  # 可选：用于追踪
            "X-Title": "GraphRAG",  # 可选：应用名称
        }
    )
    return client


def create_deepseek_client() -> OpenAI:
    """
    创建 LLM 客户端（使用 OpenRouter）
    保持向后兼容的接口名称
    
    Returns:
        OpenAI客户端实例（配置为 OpenRouter API）
    """
    return create_openrouter_client()


def generate_answer(client: OpenAI, question: str, model: str = None, system_prompt: str = None) -> str:
    """
    使用 OpenRouter 生成答案
    
    Args:
        client: OpenRouter 客户端
        question: 问题文本
        model: 模型名称，如果为None则使用配置中的默认模型
        system_prompt: 系统提示词，如果为None则使用默认提示词
        
    Returns:
        生成的答案（已清理Markdown格式）
    """
    if model is None:
        model = settings.OPENROUTER_LLM_MODEL
    
    if system_prompt is None:
        system_prompt = "你是一个能力非常强大的助手。请使用纯文本格式回答，不要使用任何 Markdown 格式、HTML 标签或代码块。"
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {"role": "user", "content": question},
        ],
        temperature=0.7,
        max_tokens=2048,
        stream=False,
    )
    
    content = response.choices[0].message.content
    
    # 后处理：移除可能的 Markdown 格式标记
    # 移除 Markdown 粗体 **text**
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
    # 移除 Markdown 斜体 *text*
    content = re.sub(r'\*(.*?)\*', r'\1', content)
    # 移除 Markdown 标题 # ## ###
    content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
    # 移除代码块标记 ```
    content = re.sub(r'```[\s\S]*?```', '', content)
    # 移除行内代码标记 `
    content = re.sub(r'`([^`]+)`', r'\1', content)
    # 移除 HTML 标签
    content = re.sub(r'<[^>]+>', '', content)
    # 移除多余的换行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()


def generate_deepseek_answer(client: OpenAI, question: str) -> str:
    """
    使用 LLM 生成答案（使用 OpenRouter）
    保持向后兼容的接口名称
    
    Args:
        client: LLM 客户端
        question: 问题文本
        
    Returns:
        生成的答案（已清理Markdown格式）
    """
    return generate_answer(client, question)


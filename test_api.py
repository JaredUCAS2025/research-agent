#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试新 API 配置是否正常工作"""

import os
import sys
from openai import OpenAI

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 从 .env 读取配置
api_key = "7bRnT4jH6*yU3c"
base_url = "http://157.148.13.64:8000/v1"
model = "Qwen3.5-122B-A10B"

print(f"测试 API 配置:")
print(f"  Base URL: {base_url}")
print(f"  Model: {model}")
print()

try:
    client = OpenAI(api_key=api_key, base_url=base_url)

    print("发送测试请求...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个有帮助的助手。"},
            {"role": "user", "content": "请用 JSON 格式回复：{\"status\": \"ok\", \"message\": \"测试成功\"}"}
        ],
        timeout=30.0,
    )

    content = response.choices[0].message.content
    print(f"[OK] API 响应成功!")
    print(f"响应内容:\n{content}")
    print()

    # 尝试解析 JSON
    import json
    try:
        parsed = json.loads(content.strip())
        print(f"[OK] JSON 解析成功: {parsed}")
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 解析失败: {e}")
        print("这可能导致论文分析失败")

except Exception as e:
    print(f"[ERROR] API 调用失败: {e}")
    print("请检查:")
    print("  1. API 地址是否正确")
    print("  2. API Key 是否有效")
    print("  3. 网络连接是否正常")

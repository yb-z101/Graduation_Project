import requests
import time
from typing import Optional, Dict, Any
from app.core.config import settings

def clean_code_output(code: str) -> str:
    """
    清理模型返回的代码，移除代码块标记和多余的前缀
    """
    code = code.strip()
    code = code.replace('```python', '').replace('```', '').strip()
    if code.startswith('python'):
        code = code[6:].strip()
    if '```' in code:
        parts = code.split('```')
        if len(parts) >= 3:
            code = parts[1].strip()
    return code

def call_qwen(prompt: str, retries: int = 3) -> str:
    """
    调用 Qwen API，支持重试机制
    """
    if not settings.llm.qwen_api_key:
        return "错误：未配置QWEN API密钥"
    
    headers = {
        "Authorization": f"Bearer {settings.llm.qwen_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "qwen-turbo",
        "input": {"prompt": prompt},
        "parameters": {"result_format": "text", "temperature": 0.7, "max_tokens": 1024}
    }
    
    for attempt in range(retries):
        try:
            response = requests.post(settings.llm.qwen_api_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("output", {}).get("text", f"返回格式异常：{result}")
        except Exception as e:
            if attempt == retries - 1:
                return f"调用大模型失败：{str(e)}"
            time.sleep(2)  # 等待2秒后重试


def call_deepseek(prompt: str, retries: int = 3) -> str:
    """
    调用 DeepSeek API，支持重试机制
    """
    if not settings.llm.deepseek_api_key:
        return "错误：未配置DeepSeek API密钥"
    
    headers = {
        "Authorization": f"Bearer {settings.llm.deepseek_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    for attempt in range(retries):
        try:
            response = requests.post(settings.llm.deepseek_api_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", f"返回格式异常：{result}")
        except Exception as e:
            if attempt == retries - 1:
                return f"调用大模型失败：{str(e)}"
            time.sleep(2)  # 等待2秒后重试


def call_volcengine(prompt: str, retries: int = 3) -> str:
    """
    调用火山引擎 Doubao API，支持重试机制
    """
    api_key = "1f75115a-150e-4f9a-8631-48fb469449ef"  # 使用用户提供的API Key
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "doubao-seed-2-0-lite-260215",  # 使用用户提供的模型名称
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    for attempt in range(retries):
        try:
            # 使用正确的API路径
            response = requests.post("https://ark.cn-beijing.volces.com/api/v3/chat/completions", json=data, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", f"返回格式异常：{result}")
        except Exception as e:
            if attempt == retries - 1:
                return f"调用大模型失败：{str(e)}"
            time.sleep(2)  # 等待2秒后重试


def call_spark(prompt: str, retries: int = 3) -> str:
    """
    调用星火大模型 API，支持重试机制
    """
    # 使用HTTP协议的APIPassword
    api_password = "nTOQvDczWHLvfehWFjbA:BxmSBIaCQVDrcuKQmXkw"
    
    headers = {
        "Authorization": f"Bearer {api_password}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "spark-x",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    for attempt in range(retries):
        try:
            response = requests.post("https://spark-api-open.xf-yun.com/v2/chat/completions", json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", f"返回格式异常：{result}")
        except Exception as e:
            if attempt == retries - 1:
                return f"调用大模型失败：{str(e)}"
            time.sleep(2)  # 等待2秒后重试


def call_zhipu(prompt: str, retries: int = 3) -> str:
    if not settings.llm.zhipu_api_key:
        return "错误：未配置智谱清言API密钥"
    
    headers = {
        "Authorization": f"Bearer {settings.llm.zhipu_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "glm-4-flash",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    for attempt in range(retries):
        try:
            response = requests.post(settings.llm.zhipu_api_url, json=data, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", f"返回格式异常：{result}")
        except Exception as e:
            if attempt == retries - 1:
                return f"调用大模型失败：{str(e)}"
            time.sleep(2)


def call_llm(model_id: str, prompt: str, retries: int = 3) -> str:
    """
    统一调用大模型的接口
    model_id: 模型ID，可选值：ali-qwen, deepseek, volcengine, spark
    """
    if model_id == "ali-qwen":
        return call_qwen(prompt, retries)
    elif model_id == "deepseek":
        return call_deepseek(prompt, retries)
    elif model_id == "volcengine":
        return call_volcengine(prompt, retries)
    elif model_id == "spark":
        return call_spark(prompt, retries)
    elif model_id == "zhipu":
        return call_zhipu(prompt, retries)
    else:
        return f"错误：不支持的模型ID：{model_id}"

def test_qwen_api(prompt: str) -> str:
    """
    测试 Qwen API 连接
    """
    return call_qwen(prompt)

def generate_sql(schema_info: str, user_query: str, db_type: str, model_id: str = "ali-qwen") -> str:
    """
    根据表结构和用户查询生成 SQL 语句
    """
    prompt = f"""
严格按照以下要求生成SQL语句：
1. 仅返回可执行的SELECT查询语句，不要任何多余文字（如解释、注释、```sql标记）
2. 适配数据库类型：{db_type}
3. 基于以下表结构：
{schema_info}
4. 回答用户问题：{user_query}
5. 禁止包含DROP/DELETE/ALTER等危险操作
"""
    return call_llm(model_id, prompt).strip().replace("```sql", "").replace("```", "")

def generate_pandas_code(df_info: dict, user_query: str, history: list = None, model_id: str = "ali-qwen") -> str:
    """
    生成 pandas 代码，可结合历史对话。
    history: 格式为 [{"role": "user/assistant", "content": "消息", ...}]
    """
    col_desc = "\n".join([f"- {c['name']} ({c['type']})" for c in df_info['columns']])
    sample_rows = df_info.get('sample_rows', [])
    sample_desc = "示例数据前3行：\n" + "\n".join([str(row) for row in sample_rows]) if sample_rows else "无示例数据"

    history_text = ""
    if history:
        recent = history[-3:]
        history_lines = []
        for h in recent:
            prefix = "用户" if h['role'] == 'user' else "助手"
            history_lines.append(f"{prefix}: {h['content']}")
        if history_lines:
            history_text = "历史对话：\n" + "\n".join(history_lines) + "\n\n"

    prompt = f"""
你是一个Python数据分析专家。用户有一个pandas DataFrame，包含以下列：
{col_desc}

{sample_desc}

{history_text}
用户现在想进行以下分析：{user_query}

请生成pandas代码来完成这个分析。要求：
1. 代码必须将最终结果赋值给变量 `result`，`result` 必须是一个pandas DataFrame。
2. 仅使用pandas和Python内置函数，不要导入其他模块。
3. 代码应简洁高效，只包含必要的操作。
4. 不要包含任何解释性文字，只返回纯Python代码。
"""
    code = call_llm(model_id, prompt)
    return clean_code_output(code)

def generate_pandas_code_with_context(df_info: dict, user_query: str, history: list = None,
                                       model_id: str = "ali-qwen",
                                       last_result=None, last_columns=None) -> str:
    col_desc = "\n".join([f"- {c['name']} ({c['type']})" for c in df_info['columns']])
    sample_rows = df_info.get('sample_rows', [])
    sample_desc = "示例数据前3行：\n" + "\n".join([str(row) for row in sample_rows]) if sample_rows else "无示例数据"

    history_text = ""
    if history:
        recent = history[-5:]
        history_lines = []
        for h in recent:
            prefix = "用户" if h.get('role') == 'user' else "助手"
            content = h.get('content', '')
            if len(content) > 300:
                content = content[:300] + "..."
            history_lines.append(f"{prefix}: {content}")
        if history_lines:
            history_text = "历史对话：\n" + "\n".join(history_lines) + "\n\n"

    context_hint = ""
    if last_result and last_columns:
        preview_lines = []
        for row in last_result[:5]:
            preview_lines.append(str(dict(zip(last_columns, [row.get(c, '') for c in last_columns]))))
        context_hint = f"""
【重要 - 上一次分析结果可用】
用户之前的分析产生了一个中间结果，已存储在变量 `last_result` 中（pandas DataFrame）。
该结果的列：{', '.join(last_columns)}
数据预览（前5行）：
{chr(10).join(preview_lines)}

如果当前问题需要基于之前的结果继续分析（如"根据上面的结果画图"、"进一步筛选"、"排序"等），请直接使用 `last_result` 变量作为数据源。
如果当前问题是全新的独立分析（如"计算XX"、"统计YY"），请忽略 `last_result`，使用原始 `df` 变量。
"""

    prompt = f"""
你是一个Python数据分析专家。用户有一个pandas DataFrame，包含以下列：
{col_desc}

{sample_desc}

{history_text}
{context_hint}
用户现在想进行以下分析：{user_query}

请生成pandas代码来完成这个分析。要求：
1. 代码必须将最终结果赋值给变量 `result`，`result` 必须是一个pandas DataFrame。
2. 可用变量：`df`（原始完整数据）、`last_result`（上次的计算结果，如适用）
3. 仅使用pandas和Python内置函数，不要导入其他模块。
4. 代码应简洁高效，只包含必要的操作。
5. 不要包含任何解释性文字，只返回纯Python代码。
"""
    code = call_llm(model_id, prompt)
    return clean_code_output(code)

def generate_clean_code(df_info: dict, clean_instruction: str, history: list = None, model_id: str = "ali-qwen") -> str:
    """
    根据用户清洗指令生成 pandas 清洗代码。
    要求：代码最终将清洗后的 DataFrame 赋值给变量 `df`（覆盖原变量）。
    """
    col_desc = "\n".join([f"- {c['name']} ({c['type']})" for c in df_info['columns']])
    sample_rows = df_info.get('sample_rows', [])
    sample_desc = "示例数据前3行：\n" + "\n".join([str(row) for row in sample_rows]) if sample_rows else "无示例数据"

    history_text = ""
    if history:
        recent = history[-3:]
        history_lines = []
        for h in recent:
            prefix = "用户" if h['role'] == 'user' else "助手"
            history_lines.append(f"{prefix}: {h['content']}")
        if history_lines:
            history_text = "历史对话：\n" + "\n".join(history_lines) + "\n\n"

    prompt = f"""
你是一个Python数据分析专家。用户有一个pandas DataFrame，包含以下列：
{col_desc}

{sample_desc}

{history_text}
用户希望对数据进行清洗操作，指令如下：{clean_instruction}

请生成pandas代码来完成这个清洗任务。要求：
1. 代码必须将清洗后的DataFrame赋值给变量 `df`，覆盖原df。
2. 仅使用pandas和Python内置函数，不要导入其他模块。
3. 代码应简洁高效，只包含必要的操作（如 dropna, fillna, drop_duplicates 等）。
4. 不要包含任何解释性文字，只返回纯Python代码。
"""
    code = call_llm(model_id, prompt)
    return clean_code_output(code)

def generate_analysis_summary(analysis_result: Any, user_query: str, model_id: str = "ali-qwen") -> str:
    """
    生成数据分析摘要
    """
    prompt = f"""
你是一个数据分析专家，请根据以下信息生成一个简洁明了的分析摘要：

用户查询：{user_query}

分析结果：{str(analysis_result)}

要求：
1. 摘要应简洁明了，直接回答用户问题
2. 不要包含任何引导性短语，直接给出核心结论
3. 语言自然，符合中文表达习惯
4. 长度控制在100字以内
"""
    return call_llm(model_id, prompt).strip()
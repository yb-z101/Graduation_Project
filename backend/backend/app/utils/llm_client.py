import requests
from app.core.config import settings

def call_qwen(prompt: str) -> str:
    if not settings.qwen_api_key:
        return "错误：未配置QWEN API密钥"
    headers = {
        "Authorization": f"Bearer {settings.qwen_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen-turbo",
        "input": {"prompt": prompt},
        "parameters": {"result_format": "text", "temperature": 0.7, "max_tokens": 1024}
    }
    try:
        response = requests.post(settings.qwen_api_url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get("output", {}).get("text", f"返回格式异常：{result}")
    except Exception as e:
        return f"调用大模型失败：{str(e)}"

def test_qwen_api(prompt: str) -> str:
    return call_qwen(prompt)

def generate_sql(schema_info: str, user_query: str, db_type: str) -> str:
    prompt = f"""
严格按照以下要求生成SQL语句：
1. 仅返回可执行的SELECT查询语句，不要任何多余文字（如解释、注释、```sql标记）
2. 适配数据库类型：{db_type}
3. 基于以下表结构：
{schema_info}
4. 回答用户问题：{user_query}
5. 禁止包含DROP/DELETE/ALTER等危险操作
"""
    return call_qwen(prompt).strip().replace("```sql", "").replace("```", "")

def generate_pandas_code(df_info: dict, user_query: str, history: list = None) -> str:
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
    code = call_qwen(prompt).strip()
    code = code.replace('```python', '').replace('```', '').strip()
    if code.startswith('python'):
        code = code[6:].strip()
    if '```' in code:
        parts = code.split('```')
        if len(parts) >= 3:
            code = parts[1].strip()
    return code

def generate_clean_code(df_info: dict, clean_instruction: str, history: list = None) -> str:
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
    code = call_qwen(prompt).strip()
    code = code.replace('```python', '').replace('```', '').strip()
    if code.startswith('python'):
        code = code[6:].strip()
    if '```' in code:
        parts = code.split('```')
        if len(parts) >= 3:
            code = parts[1].strip()
    return code
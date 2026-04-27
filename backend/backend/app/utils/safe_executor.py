import pandas as pd
import numpy as np
import io
import contextlib
import sys
import re
from typing import Tuple, Optional

def execute_pandas_code(code: str, df: pd.DataFrame, extra_vars: dict = None) -> pd.DataFrame:
    """
    安全执行 pandas 代码，返回结果 DataFrame。
    限制：只允许 pandas、numpy 和内置函数，禁用危险操作。
    """
    # 先清理已知的无害import语句（因为safe_globals中已经提供了这些模块）
    code = code.replace('import pandas as pd', '')
    code = code.replace('import numpy as np', '')
    code = code.replace('import pandas', '')
    code = code.replace('import numpy', '')

    # 检查代码中是否包含危险操作（在清理无害import之后检查）
    dangerous_patterns = [
        r'import\s+',           # 清理后仍存在其他import则拦截
        r'open\s*\(',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__\s*\(',
        r'os\.',
        r'subprocess\.',
        r'sys\.',
        r'file\.',
        r'write\s*\(',
        r'read\s*\(',
        r'input\s*\(',
        r'raw_input\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code):
            raise RuntimeError(f"代码中包含危险操作: {pattern}")
    
    # 准备安全环境
    safe_globals = {
        'pd': pd,
        'np': np,
        'df': df,
        '__builtins__': {
            'print': print,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'any': any,
            'all': all,
            'sum': sum,
            'max': max,
            'min': min,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'reversed': reversed,
            'type': type,
            'isinstance': isinstance,
            'bool': bool,
            'set': set,
        }
    }

    if extra_vars:
        for key, val in extra_vars.items():
            try:
                safe_globals[key] = val
            except Exception:
                pass

    local_vars = {}
    try:
        # 打印处理后的代码，用于调试
        print(f"处理后的代码: {code}")
        
        # 重定向 stdout 以捕获 print 输出（可选）
        output_capture = io.StringIO()
        with contextlib.redirect_stdout(output_capture):
            exec(code, safe_globals, local_vars)
        # 预期 local_vars 中有一个名为 'result' 的变量，或者代码直接修改了 df 并返回
        # 我们约定：生成的代码必须将最终结果赋值给变量 'result'（DataFrame）
        if 'result' in local_vars:
            result = local_vars['result']
            # 确保返回值是 DataFrame
            if isinstance(result, pd.DataFrame):
                return result
            else:
                raise RuntimeError("代码执行结果不是 DataFrame")
        else:
            # 如果没找到 result，尝试返回 df（假设代码直接操作了 df）
            return df
    except Exception as e:
        # 打印错误信息，用于调试
        print(f"执行代码时出错: {str(e)}")
        raise RuntimeError(f"执行代码失败: {str(e)}")
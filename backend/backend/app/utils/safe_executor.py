import pandas as pd
import io
import contextlib
import sys

def execute_pandas_code(code: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    安全执行 pandas 代码，返回结果 DataFrame。
    限制：只允许 pandas 和内置函数，禁用危险操作。
    """
    # 准备安全环境
    safe_globals = {
        'pd': pd,
        'df': df,
        '__builtins__': {
            'print': print,  # 允许打印（可捕获输出）
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
        }
    }
    # 限制危险模块
    safe_globals['__import__'] = None  # 禁止导入

    local_vars = {}
    try:
        # 重定向 stdout 以捕获 print 输出（可选）
        output_capture = io.StringIO()
        with contextlib.redirect_stdout(output_capture):
            exec(code, safe_globals, local_vars)
        # 预期 local_vars 中有一个名为 'result' 的变量，或者代码直接修改了 df 并返回
        # 我们约定：生成的代码必须将最终结果赋值给变量 'result'（DataFrame）
        if 'result' in local_vars:
            return local_vars['result']
        else:
            # 如果没找到 result，尝试返回 df（假设代码直接操作了 df）
            return df
    except Exception as e:
        raise RuntimeError(f"执行代码失败: {str(e)}")
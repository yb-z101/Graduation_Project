import pytest
import pandas as pd
from app.utils.safe_executor import execute_pandas_code


def test_execute_pandas_code():
    """测试执行 pandas 代码"""
    # 创建测试数据
    df = pd.DataFrame({
        "name": ["张三", "李四", "王五"],
        "age": [28, 32, 24],
        "department": ["技术部", "市场部", "产品部"]
    })
    
    # 测试简单的过滤操作
    code = """
result = df[df['age'] > 25]
"""
    result = execute_pandas_code(code, df)
    assert len(result) == 2
    assert list(result['name']) == ["张三", "李四"]
    
    # 测试排序操作
    code = """
result = df.sort_values('age', ascending=False)
"""
    result = execute_pandas_code(code, df)
    assert list(result['name']) == ["李四", "张三", "王五"]
    
    # 测试分组操作
    code = """
result = df.groupby('department').size().reset_index(name='count')
"""
    result = execute_pandas_code(code, df)
    assert len(result) == 3
    assert list(result['department']) == ["产品部", "技术部", "市场部"]


def test_execute_pandas_code_with_dangerous_operations():
    """测试执行包含危险操作的代码"""
    # 创建测试数据
    df = pd.DataFrame({
        "name": ["张三", "李四", "王五"],
        "age": [28, 32, 24],
        "department": ["技术部", "市场部", "产品部"]
    })
    
    # 测试包含 import 语句的代码
    code = """
import os
result = df
"""
    with pytest.raises(RuntimeError):
        execute_pandas_code(code, df)
    
    # 测试包含 open 语句的代码
    code = """
open('test.txt', 'w').write('test')
result = df
"""
    with pytest.raises(RuntimeError):
        execute_pandas_code(code, df)

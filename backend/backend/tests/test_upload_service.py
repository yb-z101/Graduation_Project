import pytest
import pandas as pd
import io
from app.services.upload_service import parse_csv_excel_from_bytes


def test_parse_csv_file():
    """测试解析 CSV 文件"""
    # 创建一个简单的 CSV 文件内容
    csv_content = b"name,age,department\n张三,28,技术部\n李四,32,市场部\n王五,24,产品部"
    df = parse_csv_excel_from_bytes(csv_content, "test.csv")
    
    # 验证解析结果
    assert len(df) == 3
    assert list(df.columns) == ["name", "age", "department"]
    assert df.iloc[0]["name"] == "张三"
    assert df.iloc[1]["age"] == 32
    assert df.iloc[2]["department"] == "产品部"


def test_parse_excel_file():
    """测试解析 Excel 文件"""
    # 创建一个简单的 Excel 文件内容
    df = pd.DataFrame({
        "name": ["张三", "李四", "王五"],
        "age": [28, 32, 24],
        "department": ["技术部", "市场部", "产品部"]
    })
    
    # 将 DataFrame 转换为 Excel 文件内容
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_content = excel_buffer.getvalue()
    
    # 解析 Excel 文件
    parsed_df = parse_csv_excel_from_bytes(excel_content, "test.xlsx")
    
    # 验证解析结果
    assert len(parsed_df) == 3
    assert list(parsed_df.columns) == ["name", "age", "department"]
    assert parsed_df.iloc[0]["name"] == "张三"
    assert parsed_df.iloc[1]["age"] == 32
    assert parsed_df.iloc[2]["department"] == "产品部"


def test_parse_invalid_file():
    """测试解析无效文件"""
    # 创建一个无效文件内容
    invalid_content = b"invalid content"
    
    # 验证解析失败
    with pytest.raises(ValueError):
        parse_csv_excel_from_bytes(invalid_content, "test.txt")

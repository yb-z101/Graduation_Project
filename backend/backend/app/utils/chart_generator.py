import pandas as pd
from typing import Dict, Any


def generate_chart_config(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    """
    根据 DataFrame 自动生成 ECharts 配置（简化版）。
    """
    if df.empty:
        return {}

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    category_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    if category_cols and numeric_cols:
        x_col = category_cols[0]
        y_col = numeric_cols[0]
        x_data = df[x_col].tolist()
        y_data = df[y_col].tolist()
        # 简单判断是否为时间序列（尝试转换为日期）
        try:
            pd.to_datetime(x_data, errors='raise')
            chart_type = 'line'
        except:
            chart_type = 'bar'

        return {
            "title": {"text": query[:30] + "..." if query else "数据分析结果"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data, "name": x_col},
            "yAxis": {"type": "value", "name": y_col},
            "series": [{"name": y_col, "type": chart_type, "data": y_data}],
            "grid": {"containLabel": True}
        }
    elif len(numeric_cols) >= 2:
        return {
            "title": {"text": query[:30] + "..."},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": df.index.tolist()},
            "yAxis": {"type": "value"},
            "series": [{"name": col, "type": "line", "data": df[col].tolist()} for col in numeric_cols],
            "grid": {"containLabel": True}
        }
    return {}
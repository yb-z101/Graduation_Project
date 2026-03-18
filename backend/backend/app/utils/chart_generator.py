import pandas as pd
import numpy as np
from typing import Dict, Any, List


def generate_chart_config(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    """
    根据 DataFrame 自动生成 ECharts 配置，支持多种图表类型。
    """
    if df.empty:
        return {}

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    category_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = []
    
    # 尝试识别日期列
    for col in df.columns:
        try:
            pd.to_datetime(df[col], errors='raise')
            date_cols.append(col)
        except:
            pass

    # 根据查询内容和数据特点选择图表类型
    chart_type = determine_chart_type(query, df, numeric_cols, category_cols, date_cols)
    
    # 如果用户没有指定图表类型，默认使用表格，不生成图表
    if chart_type == 'table':
        return {}
    
    # 生成对应类型的图表配置
    if chart_type == 'pie':
        return generate_pie_chart(df, query, category_cols, numeric_cols)
    elif chart_type == 'scatter':
        return generate_scatter_chart(df, query, numeric_cols)
    elif chart_type == 'radar':
        return generate_radar_chart(df, query, numeric_cols)
    elif chart_type == 'line':
        return generate_line_chart(df, query, date_cols, numeric_cols, category_cols)
    elif chart_type == 'bar':
        return generate_bar_chart(df, query, category_cols, numeric_cols)
    else:
        return {}


def determine_chart_type(query: str, df: pd.DataFrame, numeric_cols: List[str], category_cols: List[str], date_cols: List[str]) -> str:
    """
    根据查询内容和数据特点确定最合适的图表类型。
    """
    query_lower = query.lower()
    
    # 根据查询关键词确定图表类型
    if any(word in query_lower for word in ['饼图', 'pie']):
        return 'pie'
    elif any(word in query_lower for word in ['散点图', 'scatter']):
        return 'scatter'
    elif any(word in query_lower for word in ['雷达图', 'radar']):
        return 'radar'
    elif any(word in query_lower for word in ['折线图', 'line']):
        return 'line'
    elif any(word in query_lower for word in ['柱状图', '条形图', 'bar']):
        return 'bar'
    
    # 如果用户没有指定图表类型，默认使用表格
    return 'table'
    
    # 根据数据特点确定图表类型（如果需要默认图表类型）
    # if date_cols and numeric_cols:
    #     return 'line'
    # elif category_cols and numeric_cols and len(category_cols) == 1 and len(numeric_cols) == 1:
    #     if len(df) <= 10:
    #         return 'bar'
    #     else:
    #         return 'line'
    # elif category_cols and numeric_cols and len(df[category_cols[0]].unique()) <= 8:
    #     return 'pie'
    # elif len(numeric_cols) >= 2:
    #     return 'scatter'
    # elif len(numeric_cols) >= 3:
    #     return 'radar'
    # 
    # return 'bar'

def generate_pie_chart(df: pd.DataFrame, query: str, category_cols: List[str], numeric_cols: List[str]) -> Dict[str, Any]:
    """
    生成饼图配置。
    """
    if not category_cols or not numeric_cols:
        return {}
    
    cat_col = category_cols[0]
    num_col = numeric_cols[0]
    
    # 对数据进行分组和聚合
    grouped = df.groupby(cat_col)[num_col].sum().reset_index()
    
    return {
        "title": {"text": query[:30] + "..." if query else "数据分析结果"},
        "tooltip": {"trigger": "item", "formatter": "{a} <br/>{b}: {c} ({d}%)"},
        "legend": {"orient": "vertical", "left": "left", "data": grouped[cat_col].tolist()},
        "series": [{
            "name": num_col,
            "type": "pie",
            "radius": "50%",
            "data": [
                {"value": row[num_col], "name": row[cat_col]}
                for _, row in grouped.iterrows()
            ],
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowOffsetX": 0,
                    "shadowColor": "rgba(0, 0, 0, 0.5)"
                }
            }
        }]
    }

def generate_scatter_chart(df: pd.DataFrame, query: str, numeric_cols: List[str]) -> Dict[str, Any]:
    """
    生成散点图配置。
    """
    if len(numeric_cols) < 2:
        return {}
    
    x_col = numeric_cols[0]
    y_col = numeric_cols[1]
    
    return {
        "title": {"text": query[:30] + "..." if query else "数据分析结果"},
        "tooltip": {"trigger": "item"},
        "xAxis": {"type": "value", "name": x_col},
        "yAxis": {"type": "value", "name": y_col},
        "series": [{
            "name": f"{x_col} vs {y_col}",
            "type": "scatter",
            "data": [
                [row[x_col], row[y_col]]
                for _, row in df.iterrows()
            ],
            "symbolSize": 8
        }]
    }

def generate_radar_chart(df: pd.DataFrame, query: str, numeric_cols: List[str]) -> Dict[str, Any]:
    """
    生成雷达图配置。
    """
    if len(numeric_cols) < 3:
        return {}
    
    # 只使用前5个数值列
    radar_cols = numeric_cols[:5]
    
    # 计算每列的最大值作为雷达图的最大值
    max_values = [df[col].max() for col in radar_cols]
    
    return {
        "title": {"text": query[:30] + "..." if query else "数据分析结果"},
        "tooltip": {"trigger": "item"},
        "radar": {
            "indicator": [
                {"name": col, "max": max_val}
                for col, max_val in zip(radar_cols, max_values)
            ]
        },
        "series": [{
            "name": "数据指标",
            "type": "radar",
            "data": [{
                "value": [df[col].mean() for col in radar_cols],
                "name": "平均值"
            }]
        }]
    }

def generate_line_chart(df: pd.DataFrame, query: str, date_cols: List[str], numeric_cols: List[str], category_cols: List[str]) -> Dict[str, Any]:
    """
    生成折线图配置。
    """
    if not numeric_cols:
        return {}
    
    # 确定x轴数据
    if date_cols:
        x_col = date_cols[0]
        x_data = pd.to_datetime(df[x_col]).dt.strftime('%Y-%m-%d').tolist()
    elif category_cols:
        x_col = category_cols[0]
        x_data = df[x_col].tolist()
    else:
        x_data = df.index.tolist()
    
    # 检查是否有姓名列
    name_col = None
    if '姓名' in df.columns:
        name_col = '姓名'
    elif 'name' in df.columns:
        name_col = 'name'
    
    series = []
    for col in numeric_cols:
        series_item = {
            "name": col,
            "type": "line",
            "data": df[col].tolist(),
            "smooth": True
        }
        
        # 如果有姓名列，添加标注
        if name_col:
            series_item["label"] = {
                "show": True,
                "position": "top",
                "formatter": lambda params, name_data=df[name_col].tolist(): name_data[params.dataIndex]
            }
        
        series.append(series_item)
    
    return {
        "title": {"text": query[:30] + "..." if query else "数据分析结果"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": x_data, "name": x_col if 'x_col' in locals() else "索引"},
        "yAxis": {"type": "value"},
        "series": series,
        "grid": {"containLabel": True}
    }

def generate_bar_chart(df: pd.DataFrame, query: str, category_cols: List[str], numeric_cols: List[str]) -> Dict[str, Any]:
    """
    生成柱状图配置。
    """
    if not category_cols or not numeric_cols:
        return {}
    
    x_col = category_cols[0]
    x_data = df[x_col].tolist()
    
    return {
        "title": {"text": query[:30] + "..." if query else "数据分析结果"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": x_data, "name": x_col},
        "yAxis": {"type": "value"},
        "series": [{
            "name": col,
            "type": "bar",
            "data": df[col].tolist()
        } for col in numeric_cols],
        "grid": {"containLabel": True}
    }

def generate_default_chart(df: pd.DataFrame, query: str, numeric_cols: List[str], category_cols: List[str]) -> Dict[str, Any]:
    """
    生成默认图表配置。
    """
    if category_cols and numeric_cols:
        x_col = category_cols[0]
        y_col = numeric_cols[0]
        x_data = df[x_col].tolist()
        y_data = df[y_col].tolist()
        
        return {
            "title": {"text": query[:30] + "..." if query else "数据分析结果"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data, "name": x_col},
            "yAxis": {"type": "value", "name": y_col},
            "series": [{"name": y_col, "type": "bar", "data": y_data}],
            "grid": {"containLabel": True}
        }
    elif len(numeric_cols) >= 2:
        return {
            "title": {"text": query[:30] + "..." if query else "数据分析结果"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": df.index.tolist()},
            "yAxis": {"type": "value"},
            "series": [{"name": col, "type": "line", "data": df[col].tolist()} for col in numeric_cols],
            "grid": {"containLabel": True}
        }
    return {}
import pandas as pd
import numpy as np
from typing import Dict, Any, List


def generate_chart_config(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    """
    根据 DataFrame 自动生成 ECharts 配置，支持多种图表类型。
    """
    if df.empty:
        return {}

    # 确保只选择真正的数值列，避免字符串列
    numeric_cols = []
    for col in df.columns:
        try:
            # 尝试转换为数值，如果成功就认为是数值列
            pd.to_numeric(df[col], errors='raise')
            numeric_cols.append(col)
        except:
            continue
    
    category_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = []
    
    # 尝试识别日期列
    for col in df.columns:
        try:
            pd.to_datetime(df[col], errors='raise')
            date_cols.append(col)
        except:
            pass

    # 如果没有数值列，就不生成图表
    if not numeric_cols:
        return {}

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
    

def generate_pie_chart(df: pd.DataFrame, query: str, category_cols: List[str], numeric_cols: List[str]) -> Dict[str, Any]:
    """
    生成饼图配置。
    """
    if not category_cols or not numeric_cols:
        return {}
    
    # 简单选择第一个分类列和第一个数值列
    name_col = category_cols[0]
    num_col = numeric_cols[0]
    
    # 对数据进行分组和聚合
    grouped = df.groupby(name_col)[num_col].sum().reset_index()
    
    # 美观的颜色方案
    colors = [
        '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
        '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#2f4554'
    ]
    
    return {
        "title": {
            "text": query[:30] + "..." if query else "数据分析结果",
            "left": "center",
            "textStyle": {
                "fontSize": 16,
                "fontWeight": "bold"
            }
        },
        "tooltip": {
            "trigger": "item",
            "formatter": "{a} <br/>{b}: {c} ({d}%)"
        },
        "legend": {
            "orient": "vertical",
            "left": "left",
            "top": "middle",
            "data": grouped[name_col].tolist()
        },
        "series": [{
            "name": num_col,
            "type": "pie",
            "radius": ["40%", "70%"],
            "center": ["60%", "50%"],
            "data": [
                {"value": row[num_col], "name": row[name_col]}
                for _, row in grouped.iterrows()
            ],
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowOffsetX": 0,
                    "shadowColor": "rgba(0, 0, 0, 0.5)"
                }
            },
            "label": {
                "show": True,
                "formatter": "{b}: {c}"
            },
            "color": colors
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
        "title": {
            "text": query[:30] + "..." if query else "数据分析结果",
            "left": "center",
            "textStyle": {
                "fontSize": 16,
                "fontWeight": "bold"
            }
        },
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}<br/>{a}: ({c})"
        },
        "xAxis": {
            "type": "value",
            "name": x_col,
            "nameLocation": "middle",
            "nameGap": 30,
            "splitLine": {
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "yAxis": {
            "type": "value",
            "name": y_col,
            "nameLocation": "middle",
            "nameGap": 40,
            "splitLine": {
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "series": [{
            "name": f"{x_col} vs {y_col}",
            "type": "scatter",
            "data": [
                [row[x_col], row[y_col]]
                for _, row in df.iterrows()
            ],
            "symbolSize": 12,
            "itemStyle": {
                "color": "#5470c6",
                "opacity": 0.8
            }
        }],
        "grid": {
            "containLabel": True,
            "left": "10%",
            "right": "10%",
            "top": "15%",
            "bottom": "15%"
        }
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
    max_values = [df[col].max() * 1.1 for col in radar_cols]
    
    return {
        "title": {
            "text": query[:30] + "..." if query else "数据分析结果",
            "left": "center",
            "textStyle": {
                "fontSize": 16,
                "fontWeight": "bold"
            }
        },
        "tooltip": {
            "trigger": "item"
        },
        "legend": {
            "data": ["数据值"],
            "bottom": "5%"
        },
        "radar": {
            "indicator": [
                {"name": col, "max": max_val}
                for col, max_val in zip(radar_cols, max_values)
            ],
            "shape": "polygon",
            "splitNumber": 5,
            "axisName": {
                "textStyle": {
                    "color": "#333"
                }
            },
            "splitLine": {
                "lineStyle": {
                    "color": "#e0e0e0"
                }
            },
            "splitArea": {
                "show": True,
                "areaStyle": {
                    "color": ["rgba(84, 112, 198, 0.05)", "rgba(84, 112, 198, 0.1)"]
                }
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#e0e0e0"
                }
            }
        },
        "series": [{
            "name": "数据指标",
            "type": "radar",
            "data": [{
                "value": [df[col].mean() for col in radar_cols],
                "name": "平均值",
                "areaStyle": {
                    "color": "rgba(84, 112, 198, 0.3)"
                },
                "lineStyle": {
                    "color": "#5470c6",
                    "width": 2
                },
                "itemStyle": {
                    "color": "#5470c6"
                }
            }]
        }]
    }


def generate_line_chart(df: pd.DataFrame, query: str, date_cols: List[str], numeric_cols: List[str], category_cols: List[str]) -> Dict[str, Any]:
    """
    生成折线图配置。
    """
    if not numeric_cols:
        return {}
    
    # 数据验证：检查是否有学号列，如果有且数值过大，可能是错误数据
    if '学号' in df.columns:
        # 检查学号列的值是否异常大（可能被当作数值列使用了）
        try:
            student_id_sample = df['学号'].iloc[0]
            if isinstance(student_id_sample, (int, float)) and student_id_sample > 100000:
                # 学号被错误地当作数值列，移除它
                if '学号' in numeric_cols:
                    numeric_cols.remove('学号')
                if not numeric_cols:
                    return {}
        except:
            pass
    
    # 确定x轴数据
    name_col = None
    x_data = []
    x_col_name = ""
    
    # 优先选择班级列
    if '班级' in df.columns:
        name_col = '班级'
        x_data = df[name_col].tolist()
        x_col_name = '班级'
    elif 'class' in df.columns:
        name_col = 'class'
        x_data = df[name_col].tolist()
        x_col_name = '班级'
    elif '姓名' in df.columns:
        name_col = '姓名'
        x_data = df[name_col].tolist()
        x_col_name = '姓名'
    elif 'name' in df.columns:
        name_col = 'name'
        x_data = df[name_col].tolist()
        x_col_name = '姓名'
    elif date_cols:
        x_col = date_cols[0]
        x_data = pd.to_datetime(df[x_col]).dt.strftime('%Y-%m-%d').tolist()
        x_col_name = x_col
    elif category_cols:
        x_col = category_cols[0]
        x_data = df[x_col].tolist()
        x_col_name = x_col
    else:
        x_data = df.index.tolist()
        x_col_name = "索引"
    
    # 美观的颜色方案
    colors = [
        '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
        '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'
    ]
    
    series = []
    for idx, col in enumerate(numeric_cols):
        series_item = {
            "name": col,
            "type": "line",
            "data": df[col].tolist(),
            "smooth": False,
            "symbol": "circle",
            "symbolSize": 8,
            "lineStyle": {
                "width": 3,
                "color": colors[idx % len(colors)]
            },
            "itemStyle": {
                "color": colors[idx % len(colors)]
            },
            "areaStyle": {
                "color": {
                    "type": "linear",
                    "x": 0,
                    "y": 0,
                    "x2": 0,
                    "y2": 1,
                    "colorStops": [
                        {"offset": 0, "color": colors[idx % len(colors)] + "80"},
                        {"offset": 1, "color": colors[idx % len(colors)] + "10"}
                    ]
                }
            },
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{c}"
            }
        }
        series.append(series_item)
    
    return {
        "title": {
            "text": query[:30] + "..." if query else "数据分析结果",
            "left": "center",
            "textStyle": {
                "fontSize": 16,
                "fontWeight": "bold"
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            }
        },
        "legend": {
            "data": numeric_cols,
            "top": "10%"
        },
        "xAxis": {
            "type": "category",
            "data": x_data,
            "name": x_col_name,
            "nameLocation": "middle",
            "nameGap": 35,
            "axisLabel": {
                "rotate": 45 if len(x_data) > 8 else 0
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#333"
                }
            }
        },
        "yAxis": {
            "type": "value",
            "splitLine": {
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "series": series,
        "grid": {
            "containLabel": True,
            "left": "10%",
            "right": "10%",
            "top": "20%",
            "bottom": "20%"
        }
    }


def generate_bar_chart(df: pd.DataFrame, query: str, category_cols: List[str], numeric_cols: List[str]) -> Dict[str, Any]:
    """
    生成柱状图配置。
    """
    if not numeric_cols:
        return {}
    
    # 数据验证：检查是否有学号列，如果有且数值过大，可能是错误数据
    if '学号' in df.columns:
        # 检查学号列的值是否异常大（可能被当作数值列使用了）
        try:
            student_id_sample = df['学号'].iloc[0]
            if isinstance(student_id_sample, (int, float)) and student_id_sample > 100000:
                # 学号被错误地当作数值列，移除它
                if '学号' in numeric_cols:
                    numeric_cols.remove('学号')
                if not numeric_cols:
                    return {}
        except:
            pass
    
    # 优先选择班级列作为分类（对于班级平均分场景）
    name_col = None
    x_data = []
    x_col_name = ""
    
    # 优先选择班级列
    if '班级' in df.columns:
        name_col = '班级'
        x_data = df[name_col].tolist()
        x_col_name = '班级'
    elif 'class' in df.columns:
        name_col = 'class'
        x_data = df[name_col].tolist()
        x_col_name = '班级'
    elif '姓名' in df.columns:
        name_col = '姓名'
        x_data = df[name_col].tolist()
        x_col_name = '姓名'
    elif 'name' in df.columns:
        name_col = 'name'
        x_data = df[name_col].tolist()
        x_col_name = '姓名'
    elif category_cols:
        x_col = category_cols[0]
        x_data = df[x_col].tolist()
        x_col_name = x_col
    else:
        x_data = df.index.tolist()
        x_col_name = "索引"
    
    # 美观的颜色方案
    colors = [
        '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
        '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#2f4554'
    ]
    
    series = []
    for idx, col in enumerate(numeric_cols):
        series_item = {
            "name": col,
            "type": "bar",
            "data": df[col].tolist(),
            "barWidth": "60%",
            "itemStyle": {
                "color": colors[idx % len(colors)],
                "borderRadius": [4, 4, 0, 0]
            },
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{c}"
            }
        }
        series.append(series_item)
    
    return {
        "title": {
            "text": query[:30] + "..." if query else "数据分析结果",
            "left": "center",
            "textStyle": {
                "fontSize": 16,
                "fontWeight": "bold"
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "legend": {
            "data": numeric_cols,
            "top": "10%"
        },
        "xAxis": {
            "type": "category",
            "data": x_data,
            "name": x_col_name,
            "nameLocation": "middle",
            "nameGap": 35,
            "axisLabel": {
                "rotate": 45 if len(x_data) > 8 else 0
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#333"
                }
            }
        },
        "yAxis": {
            "type": "value",
            "splitLine": {
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "series": series,
        "grid": {
            "containLabel": True,
            "left": "10%",
            "right": "10%",
            "top": "20%",
            "bottom": "20%"
        }
    }

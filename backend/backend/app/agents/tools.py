import pandas as pd
from typing import Dict, Any, List, Optional


def get_data_summary(df: pd.DataFrame, columns: list) -> Dict[str, Any]:
    if df is None or df.empty:
        return {"error": "数据为空", "row_count": 0, "col_count": 0}

    col_info = []
    numeric_cols = []
    for col in columns:
        col_name = col.get('name', '')
        col_type = col.get('type', 'unknown')
        col_info.append({"name": col_name, "type": col_type})
        if 'int' in str(col_type).lower() or 'float' in str(col_type).lower():
            numeric_cols.append(col_name)

    null_counts = df.isnull().sum().to_dict()
    return {
        "row_count": len(df),
        "col_count": len(columns),
        "columns": col_info,
        "numeric_columns": numeric_cols,
        "null_summary": {k: int(v) for k, v in null_counts.items() if v > 0},
        "has_missing": df.isnull().any().any()
    }


def describe_column(df: pd.DataFrame, column_name: str) -> Dict[str, Any]:
    if df is None or column_name not in df.columns:
        return {"error": f"列 {column_name} 不存在"}

    series = df[column_name]
    result = {
        "column": column_name,
        "dtype": str(series.dtype),
        "count": int(series.count()),
        "unique_count": int(series.nunique()),
        "null_count": int(series.isnull().sum())
    }

    if pd.api.types.is_numeric_dtype(series):
        result.update({
            "mean": float(series.mean()) if not series.empty else None,
            "std": float(series.std()) if len(series) > 1 else None,
            "min": float(series.min()),
            "max": float(series.max()),
            "median": float(series.median()),
            "q25": float(series.quantile(0.25)),
            "q75": float(series.quantile(0.75))
        })
    else:
        value_counts = series.value_counts().head(10)
        result["top_values"] = [{"value": str(k), "count": int(v)} for k, v in value_counts.items()]

    return result


def detect_outliers(df: pd.DataFrame, column_name: str) -> Dict[str, Any]:
    if df is None or column_name not in df.columns:
        return {"error": f"列 {column_name} 不存在"}

    series = df[column_name]
    if not pd.api.types.is_numeric_dtype(series):
        return {"error": f"列 {column_name} 不是数值类型，无法检测异常值"}

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers_mask = (series < lower_bound) | (series > upper_bound)
    outliers_df = df[outliers_mask]

    outlier_records = []
    if len(outliers_df) > 0:
        name_col = _find_name_column(df.columns)
        for _, row in outliers_df.iterrows():
            record = {"value": float(row[column_name]), "deviation": ""}
            if name_col and name_col in row.index:
                record["name"] = str(row[name_col])
            val = row[column_name]
            if val < lower_bound:
                record["deviation"] = f"偏低 {abs(float(val - lower_bound)):.1f}"
            elif val > upper_bound:
                record["deviation"] = f"偏高 {abs(float(val - upper_bound)):.1f}"
            outlier_records.append(record)

    return {
        "column": column_name,
        "total_outliers": int(outliers_mask.sum()),
        "outlier_ratio": round(float(outliers_mask.sum()) / len(series) * 100, 2),
        "bounds": {"lower": float(lower_bound), "upper": float(upper_bound)},
        "outliers": outlier_records[:10]
    }


def compare_columns(df: pd.DataFrame, col_a: str, col_b: str) -> Dict[str, Any]:
    if df is None or col_a not in df.columns or col_b not in df.columns:
        return {"error": "列不存在"}

    series_a = df[col_a]
    series_b = df[col_b]

    result = {
        "column_a": col_a,
        "column_b": col_b,
        "both_numeric": pd.api.types.is_numeric_dtype(series_a) and pd.api.types.is_numeric_dtype(series_b)
    }

    if result["both_numeric"]:
        correlation = series_a.corr(series_b)
        result["correlation"] = round(float(correlation), 4) if not pd.isna(correlation) else None
        result["interpretation"] = _interpret_correlation(correlation)
    else:
        try:
            cross_tab = pd.crosstab(series_a, series_b)
            result["cross_table_shape": list(cross_tab.shape)]
            result["note": "分类变量交叉表，无法计算相关系数"
        except Exception as e:
            result["error"] = str(e)

    return result


def get_chat_history(history: list) -> Dict[str, Any]:
    if not history:
        return {"total_messages": 0, "messages": []}

    user_queries = [h.get('content', '') for h in history if h.get('role') == 'user']
    ai_responses = [h.get('content', '') for h in history if h.get('role') == 'assistant']

    return {
        "total_messages": len(history),
        "user_query_count": len(user_queries),
        "recent_queries": user_queries[-5:] if user_queries else [],
        "topics_covered": list(set([_extract_topic(q) for q in user_queries if _extract_topic(q)]))
    }


def _find_name_column(columns: list) -> Optional[str]:
    name_keywords = ['姓名', 'name', '名字', '名称', '员工', 'student', '用户']
    for col in columns:
        if any(kw in str(col).lower() for kw in name_keywords):
            return col
    return None


def _interpret_correlation(corr: float) -> str:
    if pd.isna(corr):
        return "无相关性"
    abs_corr = abs(corr)
    if abs_corr >= 0.8:
        direction = "正" if corr > 0 else "负"
        return f"强{direction}相关 ({corr:.2f})"
    elif abs_corr >= 0.5:
        direction = "正" if corr > 0 else "负"
        return f"中等{direction}相关 ({corr:.2f})"
    elif abs_corr >= 0.3:
        direction = "正" if corr > 0 else "负"
        return f"弱{方向}相关 ({corr:.2f})"
    else:
        return f"几乎无相关 ({corr:.2f})"


def _extract_topic(query: str) -> str:
    topic_keywords = ['排名', '平均', '最大', '最小', '总计', '趋势', '对比', '分布', '异常']
    for kw in topic_keywords:
        if kw in query:
            return kw
    return query[:10] if query else ""

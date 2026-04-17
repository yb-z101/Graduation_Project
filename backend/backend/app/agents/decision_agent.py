import json
from typing import Dict, Any
import pandas as pd

from app.utils.llm_client import call_llm
from app.agents.tools import (
    get_data_summary,
    describe_column,
    detect_outliers,
    compare_columns,
    get_chat_history
)


class DecisionAgent:
    def __init__(self, model_id: str = 'ali-qwen'):
        self.model_id = model_id
        self.max_rounds = 3

    def analyze(self, df: pd.DataFrame, columns: list, user_query: str,
               history: list = None) -> Dict[str, Any]:
        reasoning_steps = []
        findings = []
        warnings = []
        suggestions = []

        try:
            # Round 1: 全局扫描
            step1_result = self._round1_global_scan(df, columns)
            reasoning_steps.append({
                "round": 1,
                "thought": "全局扫描数据集结构和基本统计信息",
                "action": "get_data_summary",
                "observation": step1_result
            })
            if "error" not in step1_result:
                findings.append(f"数据集包含 {step1_result['row_count']} 条记录，{step1_result['col_count']} 个字段")
                if step1_result.get('has_missing'):
                    warnings.append(f"发现缺失值: {list(step1_result['null_summary'].keys())}")

            # Round 2: 模式发现
            numeric_cols = [c['name'] for c in columns if 'int' in c.get('type', '') or 'float' in c.get('type', '')]
            step2_results = self._round2_pattern_discovery(df, columns, numeric_cols[:3])
            for tool_name, result in step2_results.items():
                reasoning_steps.append({
                    "round": 2,
                    "thought": f"使用 {tool_name} 深入分析",
                    "action": tool_name,
                    "observation": result
                })
                if "error" not in result:
                    if tool_name == "detect_outliers" and result.get("total_outliers", 0) > 0:
                        warnings.append(f"在 {result.get('column')} 中发现 {result['total_outliers']} 个异常值 (占比{result.get('outlier_ratio', 0)}%)")
                        findings.append(f"异常值范围: [{result.get('bounds', {}).get('lower')}, {result.get('bounds', {}).get('upper')}]")

            # Round 3: 综合分析与历史结合
            history_info = None
            if history:
                history_info = get_chat_history(history)
                reasoning_steps.append({
                    "round": 3,
                    "thought": "分析用户历史查询意图",
                    "action": "get_chat_history",
                    "observation": history_info
                })

            # 生成决策建议
            report = self._generate_decision_report(
                user_query, findings, warnings, suggestions,
                step1_result, step2_results, history_info, numeric_cols
            )

            return {
                "report_type": "decision_support",
                "summary": f"基于对数据的综合分析，已完成 {len(reasoning_steps)} 轮推理检查",
                "sections": [
                    {"type": "finding", "title": "📊 核心发现", "priority": "high", "content": findings},
                    {"type": "warning", "title": "⚠️ 风险提示", "priority": "medium", "content": warnings},
                    {"type": "suggestion", "title": "💡 行动建议", "priority": "high", "content": suggestions}
                ],
                "reasoning_steps": reasoning_steps,
                "confidence_score": 0.80 if len(findings) > 0 else 0.5
            }

        except Exception as e:
            return {
                "report_type": "decision_support",
                "error": str(e),
                "summary": f"分析过程中出现错误: {str(e)}"
            }

    def _round1_global_scan(self, df: pd.DataFrame, columns: list) -> Dict[str, Any]:
        return get_data_summary(df, columns)

    def _round2_pattern_discovery(self, df: pd.DataFrame, columns: list,
                                    numeric_cols: list) -> Dict[str, Any]:
        results = {}

        for col in numeric_cols[:2]:
            desc = describe_column(df, col)
            results[f"describe_{col}"] = desc

            outliers = detect_outliers(df, col)
            results[f"detect_outliers_{col}"] = outliers

        if len(numeric_cols) >= 2:
            comp = compare_columns(df, numeric_cols[0], numeric_cols[1])
            results["compare_columns"] = comp

        return results

    def _generate_decision_report(self, user_query: str, findings: list,
                                   warnings: list, suggestions: list,
                                   summary_data: dict, pattern_data: dict,
                                   history_info: dict, numeric_cols: list) -> list:

        context_for_llm = f"""你是一位资深数据分析师。请基于以下分析结果生成简洁的决策建议。

## 用户目标
{user_query}

## 数据概况
- 记录数: {summary_data.get('row_count', '?')}
- 字段数: {summary_data.get('col_count', '?')}
- 数值字段: {', '.join(numeric_cols) if numeric_cols else '无'}

## 已发现的要点
{chr(10).join('- ' + f for f in findings) if findings else '暂无明显模式'}

## 风险/异常点
{chr(10).join('- ' + w for w in warnings) if warnings else '未检测到明显异常'}

## 要求
请给出 3-5 条具体的、可操作的建议。每条建议用数字编号，一行一条。
格式示例：
1. 建议1的具体内容
2. 建议2的具体内容
"""

        response = call_llm(self.model_id, context_for_llm)
        if response and '调用大模型失败' not in response:
            lines = [line.strip().lstrip('0123456789.、）) ') 
                      for line in response.split('\n') 
                      if line.strip() and len(line.strip()) > 5]
            suggestions.extend(lines[:5])

        if not suggestions:
            suggestions = [
                "建议关注数值字段的分布情况，识别潜在的数据质量问题",
                "考虑对关键字段进行分组聚合分析以获得更深入的洞察",
                "如需进一步分析，可以针对具体指标进行趋势或对比分析"
            ]

        return suggestions

from langgraph.graph import StateGraph, END
from typing import Dict, Any
from app.utils.llm_client import call_qwen, generate_pandas_code, generate_clean_code
from app.utils.safe_executor import execute_pandas_code
from app.utils.chart_generator import generate_chart_config


# 定义工作流状态类型
typing_state = Dict[str, Any]


# 定义工作流节点
def process_query(state: typing_state) -> typing_state:
    """处理用户查询"""
    try:
        # 获取原始数据和SQL内容
        original_data = state.get('data')
        sql_content = state.get('sql_content')
        
        # 获取用户查询和历史记录
        user_query = state.get('user_query', '').lower()
        history = state.get('history', [])
        
        # 识别非数据分析类问题
        non_analysis_keywords = ['你好', '您好', 'hi', 'hello', '早上好', '下午好', '晚上好', '谢谢', '再见', '拜拜', '你是谁', '你叫什么', '介绍一下自己']
        is_non_analysis = any(keyword in user_query for keyword in non_analysis_keywords)
        
        # 对于非数据分析类问题，直接调用大模型回答
        if is_non_analysis:
            # 构建对话历史
            history_text = ""
            if history:
                recent = history[-3:]
                history_lines = []
                for h in recent:
                    prefix = "用户" if h['role'] == 'user' else "助手"
                    history_lines.append(f"{prefix}: {h['content']}")
                if history_lines:
                    history_text = "历史对话：\n" + "\n".join(history_lines) + "\n\n"
            
            # 生成回复
            prompt = f"{history_text}用户现在说：{state.get('user_query', '')}\n\n请以友好的语气回复用户，不要进行数据分析。"
            analysis_summary = call_qwen(prompt)
            
            # 确保回复不是空的
            if not analysis_summary or '调用大模型失败' in analysis_summary:
                analysis_summary = "你好！我是智能数据分析助手，有什么可以帮您的吗？"
        elif sql_content:
            # 处理SQL文件
            # 优化SQL内容，只提取关键部分
            sql_lines = sql_content.strip().split('\n')
            # 过滤掉注释和空行
            filtered_lines = [line for line in sql_lines if line.strip() and not line.strip().startswith('--')]
            # 限制行数，避免提示过长
            limited_sql = '\n'.join(filtered_lines[:10])
            
            # 检查用户查询是否包含图表相关关键词
            user_query = state.get('user_query', '')
            wants_chart = any(k in user_query for k in ["图表", "画图", "可视化", "折线图", "柱状图", "饼图"])
            
            # 构建包含SQL内容的提示
            prompt = f"用户上传了SQL文件，内容如下：\n```sql\n{limited_sql}\n{'...' if len(filtered_lines) > 10 else ''}\n```\n\n用户的问题：{user_query}\n\n请分析SQL文件内容并回答用户的问题，提供清晰、专业的分析结果。"
            
            if wants_chart:
                prompt += "\n\n如果用户请求生成图表，请提供数据的结构信息，包括列名和数据类型，以便前端生成图表。"
            
            analysis_summary = call_qwen(prompt)
            
            # 确保回复不是空的
            if not analysis_summary or '调用大模型失败' in analysis_summary:
                analysis_summary = "已对SQL文件进行分析，您可以询问具体的问题以获取更详细的分析结果。"
            
            # 对于SQL文件，我们也尝试生成一些示例数据来支持图表生成
            # 这里我们模拟一些数据，实际应用中可能需要执行SQL查询
            try:
                # 尝试从SQL文件中提取表结构信息
                import re
                table_matches = re.findall(r'CREATE TABLE\s+([a-zA-Z0-9_]+)\s*\(([\s\S]*?)\)', sql_content, re.IGNORECASE)
                
                if table_matches:
                    # 提取列信息
                    table_name, columns_def = table_matches[0]
                    column_matches = re.findall(r'\s*([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_]+)', columns_def)
                    
                    if column_matches:
                        # 生成示例数据
                        import pandas as pd
                        import numpy as np
                        
                        # 构建列名和数据类型
                        columns = []
                        for col_name, col_type in column_matches:
                            columns.append(col_name)
                        
                        # 生成示例数据
                        sample_data = []
                        for i in range(5):
                            row = {}
                            for col in columns:
                                # 根据列名生成示例数据
                                if 'name' in col.lower() or '姓名' in col:
                                    row[col] = f'用户{i+1}'
                                elif 'age' in col.lower() or '年龄' in col:
                                    row[col] = np.random.randint(20, 40)
                                elif 'salary' in col.lower() or '工资' in col:
                                    row[col] = np.random.randint(5000, 15000)
                                elif 'department' in col.lower() or '部门' in col:
                                    depts = ['技术部', '产品部', '运营部', '市场部', '销售部']
                                    row[col] = depts[np.random.randint(0, len(depts))]
                                else:
                                    row[col] = i + 1
                            sample_data.append(row)
                        
                        # 创建DataFrame
                        df = pd.DataFrame(sample_data)
                        state['analysis_result'] = df
            except Exception as e:
                # 如果生成示例数据失败，忽略错误
                pass
        else:
            # 处理常规数据文件
            if original_data is None:
                state['analysis_summary'] = "错误：没有数据可供分析"
                return state
            
            # 生成分析代码
            df_info = {
                'columns': state.get('columns', []),
                'sample_rows': original_data.head(3).to_dict('records')
            }
            code = generate_pandas_code(df_info, state.get('user_query', ''), history)

            # 执行代码（若LLM生成空/异常代码，则回退到直接用原数据，避免整条链路报错）
            try:
                if not code or not code.strip():
                    raise RuntimeError("生成代码为空")
                result = execute_pandas_code(code, original_data)
            except Exception as exec_err:
                state['error'] = f"数据查询失败: {str(exec_err)}"
                result = original_data

            state['analysis_result'] = result

            # 生成文本分析结果
            analysis_summary = ""
            
            # 首先检查用户查询是否包含特定关键词
            if '几个' in user_query or '多少' in user_query or '数量' in user_query:
                # 回答数量问题
                if '员工' in user_query or '人' in user_query:
                    # 直接使用原始数据的行数
                    count = len(original_data)
                    analysis_summary = f"共 {count} 个"
                    if count > 0:
                        # 列出所有名称
                        if '姓名' in original_data.columns:
                            names = original_data['姓名'].tolist()
                            analysis_summary += f"，分别是{', '.join(names)}"
                        elif 'name' in original_data.columns:
                            names = original_data['name'].tolist()
                            analysis_summary += f"，分别是{', '.join(names)}"
                elif '部门' in user_query:
                    # 统计部门数量
                    if '部门' in original_data.columns:
                        unique_depts = original_data['部门'].unique().tolist()
                        count = len(unique_depts)
                        analysis_summary = f"共 {count} 个部门"
                        if count > 0:
                            analysis_summary += f"，分别是{', '.join(unique_depts)}"
                    elif 'department' in original_data.columns:
                        unique_depts = original_data['department'].unique().tolist()
                        count = len(unique_depts)
                        analysis_summary = f"共 {count} 个部门"
                        if count > 0:
                            analysis_summary += f"，分别是{', '.join(unique_depts)}"
                    else:
                        analysis_summary = "数据中没有部门列"
                else:
                    # 其他数量问题
                    count = len(result)
                    analysis_summary = f"共 {count} 条"
            elif '最小' in user_query:
                # 回答最小值问题
                if '年龄' in user_query:
                    if '年龄' in original_data.columns:
                        min_age_row = original_data.loc[original_data['年龄'].idxmin()]
                        name = min_age_row.get('姓名', min_age_row.get('name', '未知'))
                        age = min_age_row['年龄']
                        analysis_summary = f"{name}，{age}岁"
                    elif 'age' in original_data.columns:
                        min_age_row = original_data.loc[original_data['age'].idxmin()]
                        name = min_age_row.get('姓名', min_age_row.get('name', '未知'))
                        age = min_age_row['age']
                        analysis_summary = f"{name}，{age}岁"
                    else:
                        analysis_summary = "数据中没有年龄列"
                else:
                    # 其他最小值问题
                    if len(result) > 0:
                        analysis_summary = f"最小值为 {result.min().iloc[0]}"
            elif '最大' in user_query:
                # 回答最大值问题
                if '年龄' in user_query:
                    if '年龄' in original_data.columns:
                        max_age_row = original_data.loc[original_data['年龄'].idxmax()]
                        name = max_age_row.get('姓名', max_age_row.get('name', '未知'))
                        age = max_age_row['年龄']
                        analysis_summary = f"{name}，{age}岁"
                    elif 'age' in original_data.columns:
                        max_age_row = original_data.loc[original_data['age'].idxmax()]
                        name = max_age_row.get('姓名', max_age_row.get('name', '未知'))
                        age = max_age_row['age']
                        analysis_summary = f"{name}，{age}岁"
                    else:
                        analysis_summary = "数据中没有年龄列"
                else:
                    # 其他最大值问题
                    if len(result) > 0:
                        analysis_summary = f"最大值为 {result.max().iloc[0]}"
            elif '平均' in user_query or '均值' in user_query:
                # 回答平均值问题
                if '年龄' in user_query:
                    if '年龄' in original_data.columns:
                        avg_age = original_data['年龄'].mean()
                        analysis_summary = f"平均年龄为 {avg_age:.1f} 岁"
                    elif 'age' in original_data.columns:
                        avg_age = original_data['age'].mean()
                        analysis_summary = f"平均年龄为 {avg_age:.1f} 岁"
                    else:
                        analysis_summary = "数据中没有年龄列"
                else:
                    # 其他平均值问题
                    if len(result) > 0:
                        avg_value = result.mean().iloc[0]
                        analysis_summary = f"平均值为 {avg_value:.1f}"
            elif '数据分析' in user_query:
                # 通用数据分析请求
                analysis_summary = f"已对数据进行分析，共 {len(original_data)} 条记录"
                if '姓名' in original_data.columns:
                    names = original_data['姓名'].tolist()
                    analysis_summary += f"，包含员工：{', '.join(names)}"
                elif 'name' in original_data.columns:
                    names = original_data['name'].tolist()
                    analysis_summary += f"，包含员工：{', '.join(names)}"
            else:
                # 其他问题，生成通用回答
                if len(result) > 0:
                    # 检查结果是否与原始数据相同
                    # 注意：Index 之间直接用 `==` 可能触发 “Lengths must match to compare”
                    same_columns = False
                    try:
                        same_columns = (
                            len(result.columns) == len(original_data.columns)
                            and result.columns.equals(original_data.columns)
                        )
                    except Exception:
                        same_columns = False

                    if len(result) == len(original_data) and same_columns:
                        # 可能是查询所有数据
                        analysis_summary = f"共 {len(result)} 条数据"
                        if '姓名' in result.columns:
                            names = result['姓名'].tolist()
                            analysis_summary += f"，分别是{', '.join(names)}"
                        elif 'name' in result.columns:
                            names = result['name'].tolist()
                            analysis_summary += f"，分别是{', '.join(names)}"
                    else:
                        # 其他分析结果
                        analysis_summary = f"分析结果: 共 {len(result)} 条数据"
                        if len(result) <= 5:
                            # 结果较少，直接列出
                            if '姓名' in result.columns:
                                names = result['姓名'].tolist()
                                analysis_summary += f"，分别是{', '.join(names)}"
                            elif 'name' in result.columns:
                                names = result['name'].tolist()
                                analysis_summary += f"，分别是{', '.join(names)}"
                else:
                    analysis_summary = "没有找到符合条件的数据"
        
        state['analysis_summary'] = analysis_summary

        # 添加到历史记录
        history.append({
            'role': 'user',
            'content': state.get('user_query', '')
        })
        history.append({
            'role': 'assistant',
            'content': analysis_summary
        })
        state['history'] = history
    except Exception as e:
        state['error'] = f"处理查询失败: {str(e)}"
        state['analysis_summary'] = f"处理查询失败: {str(e)}"
    return state


def generate_visualization(state: typing_state) -> typing_state:
    """生成可视化图表"""
    try:
        # 只有当用户明确请求生成图表时，才生成图表
        user_query = state.get('user_query', '') or ''
        wants_chart = any(k in user_query for k in ["生成图表", "画图", "可视化", "折线图", "柱状图", "饼图"])
        if state.get('analysis_result') is not None and wants_chart:
            state['chart_option'] = generate_chart_config(state.get('analysis_result'), state.get('user_query', ''))
    except Exception as e:
        state['error'] = f"生成图表失败: {str(e)}"
    return state


def clean_data(state: typing_state) -> typing_state:
    """数据清洗"""
    try:
        # 生成清洗代码
        df_info = {
            'columns': state.get('columns', []),
            'sample_rows': state.get('data', None).head(3).to_dict('records') if state.get('data') is not None else []
        }
        code = generate_clean_code(df_info, "请对数据进行基本清洗，包括处理缺失值、重复值等")

        # 执行代码
        result = execute_pandas_code(code, state.get('data'))
        state['data'] = result
    except Exception as e:
        state['error'] = f"数据清洗失败: {str(e)}"
    return state


# 创建工作流图
def create_analysis_workflow():
    workflow = StateGraph(typing_state)

    # 添加节点
    workflow.add_node("process_query", process_query)
    workflow.add_node("generate_visualization", generate_visualization)
    workflow.add_node("clean_data", clean_data)

    # 添加边
    workflow.set_entry_point("process_query")
    workflow.add_edge("process_query", "generate_visualization")
    workflow.add_edge("generate_visualization", END)
    workflow.add_edge("clean_data", "process_query")

    # 编译工作流
    return workflow.compile()
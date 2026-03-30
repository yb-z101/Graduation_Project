from langgraph.graph import StateGraph, END
from typing import Dict, Any
import pandas as pd
from app.utils.llm_client import call_llm, generate_pandas_code, generate_clean_code
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
        
        # 获取用户查询、历史记录和模型ID
        user_query = state.get('user_query', '').lower()
        history = state.get('history', [])
        model_id = state.get('model_id', 'ali-qwen')  # 默认使用阿里云 Qwen 模型
        
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
            analysis_summary = call_llm(model_id, prompt)
            
            # 确保回复不是空的
            if not analysis_summary or '调用大模型失败' in analysis_summary:
                analysis_summary = "你好！我是智能数据分析助手，有什么可以帮您的吗？"
        elif sql_content:
            # 处理SQL文件 - 新逻辑
            sql_result = state.get('sql_result')
            
            # 检查用户查询是否包含图表相关关键词
            user_query = state.get('user_query', '')
            wants_chart = any(k in user_query for k in ["图表", "画图", "可视化", "折线图", "柱状图", "饼图"])
            
            if sql_result and sql_result.get('tables'):
                # 基于实际的表结构和数据进行分析
                tables = sql_result['tables']
                
                # 构建表信息
                table_info = []
                for table in tables:
                    table_name = table['table_name']
                    columns = table['columns']
                    row_count = table['row_count']
                    
                    column_info = []
                    for col in columns:
                        column_info.append(f"{col['name']} ({col['type']})")
                    
                    table_info.append(f"表名：{table_name}（{row_count}行）\n列：{', '.join(column_info)}")
                
                table_info_str = '\n\n'.join(table_info)
                
                # 获取第一个表的数据用于分析
                first_table = tables[0]
                
                # 构建包含实际数据的提示
                prompt = f"用户上传了SQL文件，已在tempsql_db数据库中执行并创建了{len(tables)}个表。\n\n表结构：\n{table_info_str}\n\n第一个表的数据样本（前5行）：\n{str(first_table['data'][:5])}\n\n用户的问题：{user_query}\n\n请基于实际的数据回答用户的问题，提供清晰、专业、简洁的分析结果。直接给出关键信息和结论，避免冗长的解释和无关内容。"
                
                if wants_chart:
                    prompt += "\n\n如果用户请求生成图表，请提供数据的结构信息，包括列名和数据类型，以便前端生成图表。"
                
                analysis_summary = call_llm(model_id, prompt)
                
                # 确保回复不是空的
                if not analysis_summary or '调用大模型失败' in analysis_summary:
                    analysis_summary = "已对SQL文件进行分析，您可以询问具体的问题以获取更详细的分析结果。"
                
                # 使用第一个表的数据作为分析结果
                import pandas as pd
                df = pd.DataFrame(first_table['data'])
                state['analysis_result'] = df
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

            # 检查用户是否明确要求展示表格或图表
            wants_table = any(k in user_query for k in ["表格", "table", "列表"])
            wants_chart = any(k in user_query for k in ["图表", "画图", "可视化", "折线图", "柱状图", "饼图", "条形图", "散点图", "雷达图"])
            
            # 生成自然语言分析摘要
            try:
                result_str = result.to_string(max_rows=20, max_cols=10)
                prompt = f"""用户查询：{user_query}

数据分析结果：
{result_str}

请用自然语言回答用户的问题，要求：
1. 直接给出答案，不要使用表格或列表格式
2. 语言自然流畅，符合中文表达习惯
3. 只回答用户问的内容，不要列出所有数据
4. 如果有多个信息点，用一句话连贯地总结
5. 字数控制在50-150字之间
"""
                llm_answer = call_llm(model_id, prompt)
                if llm_answer and "调用大模型失败" not in llm_answer and len(llm_answer.strip()) > 10:
                    analysis_summary = llm_answer.strip()
                    # 如果用户没有明确要求表格，就不展示表格
                    if not wants_table:
                        state['skip_table'] = True
                else:
                    # LLM回答失败，使用简单提示
                    analysis_summary = "分析完成，请查看下方的数据表格和图表。"
            except Exception:
                # 如果出错，使用简单提示
                analysis_summary = "分析完成，请查看下方的数据表格和图表。"
        
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
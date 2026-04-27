from langgraph.graph import StateGraph, END
from typing import Dict, Any, Optional
from app.utils.llm_client import call_llm, generate_pandas_code, generate_pandas_code_with_context, generate_clean_code, generate_sql
from app.utils.safe_executor import execute_pandas_code
from app.utils.chart_generator import generate_chart_config
from app.utils.intent_classifier import IntentClassifier


# 定义工作流状态类型
typing_state = Dict[str, Any]


def extract_chart_data(llm_response: str) -> Optional[Any]:
    """多种策略尝试从LLM回答中提取图表数据，失败返回None"""
    import re
    import json
    import pandas as pd
    
    strategies = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
        r'(\{[\s\S]*\})'
    ]
    
    for pattern in strategies:
        match = re.search(pattern, llm_response)
        if match:
            try:
                data = json.loads(match.group(1))
                if 'chart_data' in data:
                    return pd.DataFrame(data['chart_data'])
            except Exception:
                continue
    return None


def build_context_aware_data(tables_info: list, intent_type: str, query: str) -> str:
    import pandas as pd
    context_parts = []
    
    for tinfo in tables_info:
        tname = tinfo['table_name']
        cols = tinfo['columns']
        data = tinfo['data']
        col_names = [c['name'] for c in cols]
        numeric_cols = [c['name'] for c in cols if c['type'] in ('int', 'float', 'number', 'int64', 'float64')]
        
        if intent_type == 'ranking_sort':
            context_parts.append(f"### {tname}:\n- 列: {', '.join(col_names)}\n")
            if numeric_cols and data:
                df = pd.DataFrame(data)
                for num_col in numeric_cols[:3]:
                    try:
                        sorted_df = df.sort_values(by=num_col, ascending=False)
                        top5 = sorted_df.head(5)
                        name_col = next((c for c in col_names if any(k in str(c).lower() for k in ['姓名', 'name', '名字'])), col_names[0])
                        if name_col in df.columns:
                            rankings = [(row[name_col], row[num_col]) for _, row in top5.iterrows() if name_col in row.index]
                            context_parts.append(f"- {num_col} Top5: {rankings[:5]}\n")
                    except Exception:
                        pass
                        
        elif intent_type == 'visualization':
            context_parts.append(f"### {tname} ({len(data)}行):\n- 列: {', '.join(col_names)}\n")
            if numeric_cols and data:
                df = pd.DataFrame(data)
                for num_col in numeric_cols[:2]:
                    try:
                        context_parts.append(f"- {num_col}: min={df[num_col].min()}, max={df[num_col].max()}, avg={df[num_col].mean():.1f}\n")
                    except Exception:
                        pass
                        
        elif intent_type == 'statistical_analysis':
            context_parts.append(f"### {tname} ({len(data)}行):\n- 列: {', '.join(col_names)}\n")
            if data:
                try:
                    df = pd.DataFrame(data)
                    context_parts.append(f"- 统计摘要:\n{df.describe().to_string()}\n")
                except Exception:
                    pass
                    
        else:
            context_parts.append(f"### {tname} ({len(data)}行):\n- 列: {', '.join(col_names)}\n- 数据样本(前3行): {data[:3]}\n")
    
    return '\n'.join(context_parts)


def generate_intent_specific_prompt(intent_type: str, intent_config: dict,
                                   chart_intent: dict, table_info_str: str,
                                   context_data: str, user_query: str,
                                   total_tables: int, total_rows: int) -> str:
    base_info = f"""你是一个专业的数据分析助手。已成功加载数据。

## 📊 数据概览
- 共 {total_tables} 个表，{total_rows} 条记录
- 表结构：
{table_info_str}

## 📝 数据详情
{context_data}

## ❓ 用户问题
{user_query}

---

⛔ **绝对禁止的行为（违反则回答无效）**：
1. **禁止列出超过5条的数据记录**——不要输出"共X条数据，分别是张三,李四,王五..."这种格式
2. **禁止返回全量原始数据**——用户要的是分析结论，不是数据倾倒
3. **禁止回复"共XX条数据"作为主要内容**——这只是统计信息，不是答案
4. 如果用户问的是具体数据（如某人的成绩），只返回匹配的那几条，不要返回全部
"""
    
    prompt_map = {
        'ranking_sort': f"""
---

## 📌 回答要求（排名/排序类）
1. **直接给出排名结果**，格式如下：
   **【排名结果】**
   排名 | 指标值 | 备注
   ---|---|---
   1 | ... | ...
   
2. 文字总结不超过100字，重点突出Top3和最后3名
3. 不要列举所有数据！只显示关键排名节点

{'## 📈 图表要求\n如果需要生成图表，请同时返回JSON格式的图表数据' if chart_intent.get('requested') else ''}
""",
        'visualization': f"""
---

## 📌 回答要求（图表可视化类）
1. **文字回复控制在50字以内**，例如："已为您生成{chart_intent.get('type') or ''}图，展示了..."
2. **必须返回JSON格式的图表数据**：
   ```json
   {{
     "chart_data": [
       {{"name": "类别", "value": 数值}}
     ],
     "chart_type": "{chart_intent.get('type') or 'bar'}"
   }}
   ```
3. 图表数据要完整准确，确保能正确渲染
4. JSON和文字之间用空行分隔
""",
        'statistical_analysis': """
---

## 📌 回答要求（统计分析类）
1. 直接给出统计结论，不要重复数据
2. 格式示例："XX的平均值为YY，最大值为ZZ，最小值为WW"
3. 如有异常值或特殊发现，单独指出
4. 总字数控制在80字以内
""",
        'data_display': """
---

## 📌 回答要求（数据展示类）
1. 先给出数据集概况（表名、记录数、主要字段）
2. 如果数据量>20条，分组汇总展示；如果≤20条，可简要列出
3. 重点突出关键字段的分布情况
4. 总字数控制在120字以内
""",
        'general_query': """
---

## 📌 回答要求（通用查询）
1. 基于提供的数据准确回答
2. 语言简洁专业，直接给出结论
3. 不要罗列所有原始数据
4. 如果涉及具体记录，最多列出5条关键记录
5. 总字数控制在100字以内
"""
    }
    
    specific_instruction = prompt_map.get(intent_type, prompt_map['general_query'])
    return base_info + specific_instruction


# 定义工作流节点
def _is_context_continuation(user_query: str, history: list, last_result) -> bool:
    """判断当前问题是否为上下文延续性提问（子问题）"""
    if not last_result or not history:
        return False
    context_keywords = [
        '刚才', '刚刚', '上次', '上面', '之前的', '之前的', '上一步', '前一步',
        '刚才的', '刚刚的', '上次的', '上面的', '之前的', '之前的',
        '取上一步', '根据上面', '基于刚才', '之前的结果', '根据刚才',
        '排名前', '前几名', '筛选出', '继续', '这几类', '这些数据', '它们的',
        '用表格', '展示', '显示', '画图', '图表', '可视化', '柱状图', '折线图', '饼图',
        '排序', '按', '从高到低', '从低到高', '升序', '降序',
        '将刚才', '把刚才', '把上面', '将上面', '把之前', '将之前',
        '这个', '这些', '那', '那些', '其中', '当中的',
    ]
    query_lower = user_query.lower()
    for kw in context_keywords:
        if kw in query_lower:
            return True
    if history:
        last_user_msg = ''
        for h in reversed(history):
            if h.get('role') == 'user':
                last_user_msg = h.get('content', '')
                break
        if last_user_msg and len(last_user_msg) > 5:
            return True
    return False


def process_query(state: typing_state) -> typing_state:
    """处理用户查询"""
    try:
        # 获取原始数据和SQL内容
        original_data = state.get('data')
        sql_content = state.get('sql_content')
        
        # 获取用户查询、历史记录和模型ID
        user_query = state.get('user_query', '').lower()
        user_query_original = state.get('user_query', '')
        history = state.get('history', [])
        model_id = state.get('model_id', 'ali-qwen')
        
        # 获取上下文信息
        last_result = state.get("last_result")
        last_result_columns = state.get("last_result_columns", [])
        is_continuation = _is_context_continuation(user_query_original, history, last_result)
        state['is_context_continuation'] = is_continuation
        print(f"[CONTEXT-DEBUG] 上下文判断: is_continuation={is_continuation} | has_last_result={bool(last_result)} | query='{user_query_original[:40]}'")
        
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
            # 处理SQL文件 - 通用多表处理逻辑
            sql_result = state.get('sql_result')
            user_query = state.get('user_query', '')

            # 🆕 强制打印调试信息
            print(f"\n{'='*60}")
            print(f"[SQL-ANALYSIS] 开始处理SQL文件查询")
            print(f"[SQL-ANALYSIS] 用户问题: {user_query}")
            print(f"[SQL-ANALYSIS] sql_content长度: {len(sql_content) if sql_content else 0}")
            print(f"[SQL-ANALYSIS] sql_result类型: {type(sql_result)}")
            if sql_result:
                print(f"[SQL-ANALYSIS] sql_result keys: {list(sql_result.keys()) if isinstance(sql_result, dict) else 'N/A'}")
                tables = sql_result.get('tables') if isinstance(sql_result, dict) else None
                print(f"[SQL-ANALYSIS] tables存在: {bool(tables)}")
                if tables and isinstance(tables, dict):
                    print(f"[SQL-ANALYSIS] 表数量: {len(tables)}")
                    for tkey, tval in tables.items():
                        data_count = len(tval.get('data', [])) if isinstance(tval, dict) else 0
                        tname = tval.get('original_name', tkey) if isinstance(tval, dict) else tkey
                        print(f"[SQL-ANALYSIS]   - {tname}: {data_count}行数据")
            print(f"{'='*60}\n")

            # 检查用户查询是否包含图表相关关键词
            wants_chart = any(k in user_query for k in ["图表", "画图", "可视化", "折线图", "柱状图", "饼图"])

            # 🆕 增强判断条件：即使tables为空但有sql_content，也尝试解析
            has_valid_sql_data = False
            if sql_result and isinstance(sql_result, dict):
                tables = sql_result.get('tables')
                if tables and isinstance(tables, dict) and len(tables) > 0:
                    # 至少有一个表有数据
                    for tname, tdata in tables.items():
                        if isinstance(tdata, dict) and len(tdata.get('data', [])) > 0:
                            has_valid_sql_data = True
                            break

            if has_valid_sql_data:
                tables = sql_result['tables']
                table_names = list(tables.keys())
                total_tables = len(table_names)

                # 数据完整性校验
                total_rows_in_tables = sum(len(t.get('data', [])) for t in tables.values())
                print(f"[SQL-DEBUG] SQL文件解析完成: {total_tables}个表, 共{total_rows_in_tables}条数据")

                # 上下文延续性提问处理：如果有last_result且判断为子问题，走pandas代码路径
                if is_continuation and last_result and last_result_columns:
                    print(f"[SQL-CONTEXT] 检测到上下文延续性提问，走last_result路径")
                    import pandas as pd
                    try:
                        lr_df = pd.DataFrame(last_result, columns=last_result_columns)
                    except Exception:
                        lr_df = None
                    
                    if lr_df is not None and not lr_df.empty:
                        df_info = {
                            'columns': [{'name': c, 'type': str(lr_df[c].dtype)} for c in lr_df.columns],
                            'sample_rows': lr_df.head(10).to_dict('records'),
                            'total_rows': len(lr_df)
                        }
                        code = generate_pandas_code_with_context(
                            df_info, user_query_original, history,
                            model_id=model_id,
                            last_result=last_result,
                            last_columns=last_result_columns
                        )
                        exec_extra_vars = {"last_result": lr_df}
                        original_df = original_data if original_data is not None else lr_df
                        try:
                            if not code or not code.strip():
                                raise RuntimeError("生成代码为空")
                            result = execute_pandas_code(code, original_df, extra_vars=exec_extra_vars)
                        except Exception as exec_err:
                            state['error'] = f"数据查询失败: {str(exec_err)}"
                            result = None
                        
                        if result is not None:
                            state['analysis_result'] = result
                            is_fallback = (result is original_df) or (len(result) >= len(original_df) * 0.9)
                            if not is_fallback:
                                try:
                                    state['last_result'] = result.to_dict('records')
                                    state['last_result_columns'] = result.columns.tolist() if hasattr(result, 'columns') else []
                                except Exception:
                                    pass
                            else:
                                print(f"[SQL-CONTEXT] 本次结果为全量回退（{len(result)}行），保留原有last_result")
                            
                            sample = result.head(10).to_string() if result is not None and not result.empty else "无数据"
                            analysis_summary = call_llm(model_id, f"基于以下数据回答问题：{user_query_original}\n\n数据：\n{sample}")
                            if not analysis_summary or '调用大模型失败' in analysis_summary:
                                analysis_summary = f"分析完成，共 {len(result) if result is not None else 0} 条数据"
                        else:
                            analysis_summary = "分析执行失败，请重新描述您的问题"
                        
                        state['analysis_summary'] = analysis_summary
                        state['total_rows'] = len(lr_df)
                        return state

                for tname, tdata in tables.items():
                    actual_rows = len(tdata.get('data', []))
                    print(f"[SQL-DEBUG]   表{tdata.get('original_name', tname)}: {actual_rows}行")

                # 构建所有表的详细信息
                all_tables_info = []
                for tname, tdata in tables.items():
                    original_name = tdata['original_name']
                    columns = tdata['columns']
                    row_count = tdata['row_count']

                    col_info = [f"{c['name']} ({c['type']})" for c in columns]
                    all_tables_info.append({
                        'table_key': tname,
                        'table_name': original_name,
                        'columns': columns,
                        'column_info_str': ', '.join(col_info),
                        'row_count': row_count,
                        'data': tdata['data']
                    })

                # 构建表结构描述字符串
                table_info_lines = [f"表{i+1}：{t['table_name']}（{t['row_count']}行）\n   列：{t['column_info_str']}" for i, t in enumerate(all_tables_info)]
                table_info_str = '\n\n'.join(table_info_lines)

                # 🆕 无数据降级处理（移到这里，确保table_info_str已定义）
                if total_rows_in_tables == 0:
                    analysis_summary = f"⚠️ SQL文件已成功执行，创建了 **{total_tables} 个表结构**，但表中暂无INSERT数据。\n\n## 📋 已创建的表：\n{table_info_str}\n\n💡 提示：如果您的SQL文件包含INSERT语句，请检查语法是否正确。"
                    state['analysis_summary'] = analysis_summary
                    return state

                # 智能判断用户意图
                is_show_all_request = any(kw in user_query.lower() for kw in [
                    '展示', '显示', '查看', '所有', '全部', '有哪些',
                    '内容', '数据', '表格', 'table', 'show all',
                    'list', '一览'
                ])
                
                # 检查是否是图表需求
                wants_chart = any(k in user_query for k in ["生成图表", "画图", "可视化", "折线图", "柱状图", "饼图"])
                
                # 如果是图表需求，优先走多表查询逻辑，不走展示所有数据
                if wants_chart:
                    is_show_all_request = False

                is_specific_table_query = False
                target_table = None

                # 检查是否针对特定表名查询
                for tinfo in all_tables_info:
                    if tinfo['table_name'].lower() in user_query.lower() or \
                       tinfo['table_name'].replace('_', '').lower() in user_query.replace(' ', '').replace('_', '').lower():
                        is_specific_table_query = True
                        target_table = tinfo
                        break

                # 根据查询类型决定处理策略
                if is_show_all_request and not is_specific_table_query and total_tables > 1:
                    # 场景1: 用户要求展示所有数据/所有表 → 返回所有表的摘要 + 每个表的数据
                    state['is_multi_table_response'] = True
                    state['multi_table_data'] = {}

                    summary_parts = [f"✅ **SQL文件已成功解析，包含 {total_tables} 个数据表**（共{total_rows_in_tables}条记录）：\n"]

                    for i, tinfo in enumerate(all_tables_info):
                        table_data = tinfo['data']
                        actual_data_len = len(table_data)

                        # 智能决定返回多少数据
                        if actual_data_len <= 30:
                            display_data = table_data
                            data_note = f"（共{actual_data_len}条，已全部展示）"
                        else:
                            display_data = table_data[:30]
                            data_note = f"（共{actual_data_len}条，展示前30条）"

                        import pandas as pd
                        df = pd.DataFrame(display_data) if len(display_data) > 0 else pd.DataFrame()
                        state['multi_table_data'][tinfo['table_name']] = {
                            'data': display_data,
                            'columns': tinfo['columns'],
                            'row_count': actual_data_len,
                            'display_count': len(display_data),
                            'note': data_note
                        }

                        summary_parts.append(
                            f"\n### 📊 **表{i+1}: {tinfo['table_name']}** {data_note}\n"
                            f"- **列信息**: {tinfo['column_info_str']}\n"
                            f"- **数据量**: {actual_data_len}条记录"
                        )

                    analysis_summary = '\n'.join(summary_parts)

                elif is_specific_table_query and target_table:
                    # 场景2: 用户针对特定表查询 → 返回该表的完整数据
                    table_data = target_table['data']
                    actual_data_len = len(table_data)

                    if actual_data_len <= 50:
                        display_data = table_data
                        data_note = f"（共{actual_data_len}条）"
                    else:
                        display_data = table_data[:50]
                        data_note = f"（共{actual_data_len}条，展示前50条）"

                    # 生成SQL语句
                    try:
                        single_table_info = f"表名：{target_table['table_name']}（{target_table['row_count']}行）\n列：{target_table['column_info_str']}"
                        generated_sql = generate_sql(single_table_info, user_query, 'SQLite', model_id)
                        state['generated_sql'] = generated_sql
                    except Exception as e:
                        print(f"生成SQL失败: {e}")
                        state['generated_sql'] = None

                    prompt = f"""你是一个数据分析助手。用户上传了SQL文件，已经成功执行并提取了完整数据。

## ⚠️ 重要提示：你已经拥有完整的实际数据，不是空表！

📋 **当前查询表**: {target_table['table_name']}
📊 **数据总量**: {actual_data_len}条记录（你拥有全部数据）

### 表结构：
{single_table_info}

### 实际数据样本（前10行）：
{str(display_data[:10])}

### 用户问题：{user_query}

**要求**：
1. 基于以上真实数据回答，不要说"没有数据"或"只有建表语句"
2. 如果用户要求数据展示，说明共有多少条记录
3. 提供清晰、专业、简洁的分析结果
4. 直接给出关键信息和结论
"""

                    if wants_chart:
                        prompt += "\n\n如果用户请求生成图表，请提供数据的结构信息。"

                    analysis_summary = call_llm(model_id, prompt)

                    import pandas as pd
                    df = pd.DataFrame(display_data)
                    state['analysis_result'] = df
                    state['current_table_name'] = target_table['table_name']
                    state['total_rows'] = actual_data_len
                    state['displayed_rows'] = len(display_data)

                else:
                    # 场景3: 使用三层架构处理多表查询（意图分类 + 上下文裁剪 + 精准Prompt）
                    print(f"[SQL-ANALYSIS] 多表查询模式（三层架构）")
                    
                    # Layer 1: 意图分类
                    intent_type, intent_config = IntentClassifier.classify(user_query, history)
                    chart_intent = IntentClassifier.extract_chart_intent(user_query)
                    print(f"[AI-ANALYSIS] 意图识别: {intent_type} | 图表意图: {chart_intent}")
                    
                    # Layer 2: 构建上下文感知的精简数据（避免信息过载导致冗余回复）
                    context_data = build_context_aware_data(all_tables_info, intent_type, user_query)
                    
                    # 生成SQL（保留原有功能）
                    sql_generation_prompt = f"""你是一个SQL生成助手。用户上传了包含{total_tables}个表的SQL文件。

## 📋 所有表结构
{table_info_str}

## ❓ 用户问题
{user_query}

## 📌 要求
1. 生成一个可以回答用户问题的SQL查询语句
2. 使用上面定义的表名和列名
3. 只返回SQL语句，不要其他内容
4. 用SQLite语法
"""
                    
                    try:
                        generated_sql = call_llm(model_id, sql_generation_prompt)
                        if '```sql' in generated_sql:
                            generated_sql = generated_sql.split('```sql')[1].split('```')[0].strip()
                        elif '```' in generated_sql:
                            generated_sql = generated_sql.split('```')[1].split('```')[0].strip()
                        state['generated_sql'] = generated_sql
                    except Exception as e:
                        print(f"[SQL-ANALYSIS] SQL生成失败: {e}")
                        state['generated_sql'] = None
                    
                    # Layer 3: 根据意图类型生成精准Prompt并调用LLM
                    analysis_prompt = generate_intent_specific_prompt(
                        intent_type=intent_type,
                        intent_config=intent_config,
                        chart_intent=chart_intent,
                        table_info_str=table_info_str,
                        context_data=context_data,
                        user_query=user_query,
                        total_tables=total_tables,
                        total_rows=total_rows_in_tables
                    )
                    
                    analysis_summary = call_llm(model_id, analysis_prompt)
                    
                    # 尝试从AI回复中提取查询结果数据
                    extracted_result_data = None
                    extracted_table_name = None
                    
                    import re
                    result_match = re.search(r'\*\*【查询结果】\*\*\s*\n\s*表名:\s*(\w+)\s*\n([\s\S]*?)(?=\n\n|\n$|$)', analysis_summary)
                    if result_match:
                        extracted_table_name = result_match.group(1).strip()
                        result_text = result_match.group(2).strip()
                        
                        data_lines = [line.strip() for line in result_text.split('\n') if line.strip() and not line.startswith('*')]
                        if data_lines and len(data_lines) > 0:
                            target_tinfo = None
                            for tinfo in all_tables_info:
                                if tinfo['table_name'].lower() == extracted_table_name.lower():
                                    target_tinfo = tinfo
                                    break
                            
                            if target_tinfo:
                                columns = [c['name'] for c in target_tinfo['columns']]
                                parsed_rows = []
                                for line in data_lines[:20]:
                                    values = re.split(r'[,\t|]', line)
                                    if len(values) == len(columns):
                                        row_dict = {col: val.strip() for col, val in zip(columns, values)}
                                        parsed_rows.append(row_dict)
                                
                                if parsed_rows:
                                    extracted_result_data = parsed_rows
                                    print(f"[SQL-ANALYSIS] ✅ 成功提取查询结果: {len(parsed_rows)}条记录 from {extracted_table_name}")
                    
                    if extracted_result_data:
                        import pandas as pd
                        state['analysis_result'] = pd.DataFrame(extracted_result_data)
                        state['current_table_name'] = extracted_table_name
                        state['is_multi_table_response'] = False
                        state['multi_table_data'] = None
                    else:
                        state['analysis_result'] = None
                        state['is_multi_table_response'] = False
                        state['multi_table_data'] = None
                    
                    if wants_chart:
                        chart_df = extract_chart_data(analysis_summary)
                        if chart_df is not None:
                            state['analysis_result'] = chart_df

                # 确保回复不是空的
                if not analysis_summary or '调用大模型失败' in analysis_summary:
                    analysis_summary = "已对SQL文件进行分析，您可以询问具体的问题以获取更详细的分析结果。"
            else:
                # 🆕 增强降级处理：当sql_result无效时，从sql_content中智能提取数据
                print(f"[SQL-ANALYSIS] ⚠️ sql_result无效，进入增强降级处理模式")
                print(f"[SQL-ANALYSIS]   尝试从sql_content中解析数据...")

                # 尝试解析SQL内容中的INSERT语句
                import re
                insert_pattern = r'INSERT\s+INTO\s+`?(\w+)`?\s*\(([^)]+)\)\s*VALUES\s*\(([^;]+)\);'
                inserts = re.findall(insert_pattern, sql_content, re.IGNORECASE | re.DOTALL)

                if inserts:
                    print(f"[SQL-ANALYSIS] ✅ 找到 {len(inserts)} 条INSERT语句")

                    # 构建表信息
                    table_info_parts = []
                    all_extracted_data = {}

                    for i, (table_name, columns_str, values_str) in enumerate(inserts):
                        # 解析列名
                        columns = [c.strip().strip('`') for c in columns_str.split(',')]
                        # 解析值
                        values = [v.strip().strip("'\"") for v in values_str.split(',')]

                        # 创建数据字典
                        if len(columns) == len(values):
                            row_dict = {col: val for col, val in zip(columns, values)}
                            if table_name not in all_extracted_data:
                                all_extracted_data[table_name] = []
                            all_extracted_data[table_name].append(row_dict)

                            table_info_parts.append(
                                f"### 表{i+1}: {table_name}\n"
                                f"- 列: {', '.join(columns)}\n"
                                f"- 数据行数: {len(all_extracted_data[table_name])}"
                            )

                    if all_extracted_data:
                        # 有提取到数据，构建多表响应
                        state['is_multi_table_response'] = True
                        state['multi_table_data'] = {}

                        summary_parts = [f"✅ **从SQL文件中提取到 {len(all_extracted_data)} 个表的数据**：\n"]

                        for tname, tdata_list in all_extracted_data.items():
                            import pandas as pd
                            df = pd.DataFrame(tdata_list)
                            state['multi_table_data'][tname] = {
                                'data': df.to_dict('records'),
                                'columns': [{'name': col, 'type': str(df[col].dtype)} for col in df.columns],
                                'row_count': len(df),
                                'display_count': len(df),
                                'note': f"（共{len(df)}条）"
                            }
                            summary_parts.append(f"\n📊 **{tname}**: {len(df)}条记录\n")

                        analysis_summary = '\n'.join(summary_parts)
                        print(f"[SQL-ANALYSIS] ✅ 成功构建多表数据响应")
                    else:
                        # 解析失败，使用改进的提示词
                        limited_sql = sql_content[:2000] if len(sql_content) > 2000 else sql_content
                        prompt = f"""你是一个数据分析助手。用户上传了一个SQL文件。

## ⚠️ 重要：该文件包含实际的INSERT数据，不是空表！

### SQL文件内容（前2000字符）：
```sql
{limited_sql}
{'... (文件较长，已截断)' if len(sql_content) > 2000 else ''}
```

### 用户问题：{user_query}

**要求**：
1. 从SQL文件的INSERT语句中提取实际数据并展示
2. 如果用户要求数据展示，请列出所有记录
3. 不要说"没有数据"或"只有建表语句"，SQL文件中明确包含了INSERT数据
4. 提供清晰、专业的分析结果
"""

                        if wants_chart:
                            prompt += "\n\n如果用户请求生成图表，请提供数据的结构信息。"

                        analysis_summary = call_llm(model_id, prompt)
                else:
                    # 没有找到INSERT语句，使用原始SQL内容分析
                    limited_sql = sql_content[:1500] if len(sql_content) > 1500 else sql_content
                    prompt = f"用户上传了SQL文件，内容如下：\n```sql\n{limited_sql}\n{'...' if len(sql_content) > 1500 else ''}\n```\n\n用户的问题：{user_query}\n\n请分析SQL文件内容并回答用户的问题，提供清晰、专业的分析结果。"

                    if wants_chart:
                        prompt += "\n\n如果用户请求生成图表，请提供数据的结构信息。"

                    analysis_summary = call_llm(model_id, prompt)

                # 确保回复不是空的
                if not analysis_summary or '调用大模型失败' in analysis_summary:
                    analysis_summary = "已对SQL文件进行分析，您可以询问具体的问题以获取更详细的分析结果。"
        else:
            # 处理常规数据文件
            if original_data is None:
                state['analysis_summary'] = "错误：没有数据可供分析"
                return state
            
            # 生成分析代码
            df_info = {
                'columns': state.get('columns', []),
                'sample_rows': original_data.head(20).to_dict('records'),
                'total_rows': len(original_data)
            }
            
            state['total_rows'] = len(original_data)
            
            _use_context = bool(last_result and last_result_columns)
            print(f"[CONTEXT-DEBUG] 代码生成: user_query='{user_query_original[:30]}...' | has_last_result={_use_context} | rows={len(last_result) if last_result else 0} | cols={last_result_columns}")
            
            # 使用带上下文的代码生成（当有历史结果时）
            if last_result and last_result_columns:
                code = generate_pandas_code_with_context(
                    df_info, user_query_original, history,
                    model_id=model_id,
                    last_result=last_result,
                    last_columns=last_result_columns
                )
            else:
                code = generate_pandas_code(df_info, user_query_original, history)

            # 构建额外变量注入执行环境
            exec_extra_vars = {}
            if last_result and last_result_columns:
                try:
                    lr_df = pd.DataFrame(last_result, columns=last_result_columns)
                    exec_extra_vars["last_result"] = lr_df
                    print(f"[EXEC] last_result已注入执行环境: {len(lr_df)}行 × {list(lr_df.columns)}")
                except Exception as inject_err:
                    print(f"[EXEC] 警告: last_result注入失败 ({inject_err})，将尝试用原始df替代")
                    # 注入失败时不设置last_result，LLM代码如果用到会报错
                    # 但至少不会崩溃，后续会被 except 捕获

            # 执行代码（带智能重试：如果last_result相关代码失败，回退到无上下文版本）
            code_exec_failed = False
            result = None
            
            try:
                if not code or not code.strip():
                    raise RuntimeError("生成代码为空")
                result = execute_pandas_code(code, original_data, extra_vars=exec_extra_vars)
            except Exception as exec_err:
                err_msg = str(exec_err)
                print(f"[EXEC] 第一次执行失败: {err_msg}")
                
                # 如果错误是 last_result 未定义，且原本有上下文，尝试用无上下文代码重试
                if "'last_result'" in err_msg or "'last_result' is not defined" in err_msg:
                    if last_result and last_result_columns:
                        print("[EXEC] 检测到last_result未定义错误，尝试用无上下文代码重试...")
                        try:
                            fallback_code = generate_pandas_code(df_info, user_query_original, history)
                            if fallback_code and fallback_code.strip():
                                result = execute_pandas_code(fallback_code, original_data)
                                print("[EXEC] 重试成功（使用无上下文代码）")
                                code_exec_failed = False
                        except Exception as retry_err:
                            print(f"[EXEC] 重试也失败: {retry_err}")
                
                if result is None:
                    state['error'] = f"数据查询失败: {exec_err}"
                    code_exec_failed = True

            # 代码执行失败时，analysis_result设为None，避免全量数据泄漏到展示层
            if code_exec_failed or result is None:
                state['analysis_result'] = None
                state['last_result'] = last_result
                state['last_result_columns'] = last_result_columns
            else:
                state['analysis_result'] = result
            
            # 持久化本次结果供下次对话使用
            # 只有代码执行失败时才不更新last_result，正常执行结果无论大小都更新
            if not code_exec_failed and result is not None:
                is_exact_fallback = (result is original_data)
                if not is_exact_fallback:
                    try:
                        state['last_result'] = result.to_dict('records')
                        state['last_result_columns'] = result.columns.tolist() if hasattr(result, 'columns') else []
                        print(f"[CONTEXT] last_result已更新: {len(result)}行 × {len(result.columns) if hasattr(result, 'columns') else 0}列")
                    except Exception:
                        pass
                else:
                    print(f"[CONTEXT] 本次结果为原始数据引用（{len(result)}行），保留原有last_result不变")
            else:
                print(f"[CONTEXT] 代码执行失败，保留原有last_result不变")

            # 生成文本分析结果
            analysis_summary = ""
            
            # 代码执行失败时，直接返回错误信息，避免后续对None调用len()
            if code_exec_failed or result is None:
                state['analysis_summary'] = state.get('error') or '数据处理执行失败，请重新描述您的问题'
                return state
            
            # 首先检查用户查询是否包含图表相关关键词
            wants_chart = any(k in user_query for k in ["图表", "画图", "可视化", "折线图", "柱状图", "饼图"])
            
            # 如果是图表请求，不使用硬编码逻辑，让pandas代码和图表生成器处理
            if not wants_chart:
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
                        # 其他数量问题，回退到LLM生成摘要
                        if len(result) > 0:
                            sample = result.head(5).to_string()
                            analysis_summary = call_llm(model_id, f"基于以下数据回答问题：{user_query}\n\n数据：\n{sample}")
                            if not analysis_summary or '调用大模型失败' in analysis_summary:
                                analysis_summary = f"共 {len(result)} 条记录"
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
                        # 其他最小值问题，回退到LLM
                        if len(result) > 0:
                            sample = result.head(5).to_string()
                            analysis_summary = call_llm(model_id, f"基于以下数据回答问题：{user_query}\n\n数据：\n{sample}")
                            if not analysis_summary or '调用大模型失败' in analysis_summary:
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
                        # 其他最大值问题，回退到LLM
                        if len(result) > 0:
                            sample = result.head(5).to_string()
                            analysis_summary = call_llm(model_id, f"基于以下数据回答问题：{user_query}\n\n数据：\n{sample}")
                            if not analysis_summary or '调用大模型失败' in analysis_summary:
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
                        # 其他平均值问题，回退到LLM
                        if len(result) > 0:
                            sample = result.head(5).to_string()
                            analysis_summary = call_llm(model_id, f"基于以下数据回答问题：{user_query}\n\n数据：\n{sample}")
                            if not analysis_summary or '调用大模型失败' in analysis_summary:
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
                    # 其他问题，回退到LLM生成摘要
                    if len(result) > 0:
                        sample = result.head(10).to_string()
                        analysis_summary = call_llm(model_id, f"基于以下数据回答问题：{user_query}\n\n数据：\n{sample}")
                        if not analysis_summary or '调用大模型失败' in analysis_summary:
                            analysis_summary = f"分析结果: 共 {len(result)} 条数据"
                    else:
                        analysis_summary = "没有找到符合条件的数据"
            else:
                # 图表请求，不使用硬编码逻辑，让图表生成器处理数据
                analysis_summary = "已为您生成图表"
                # 如果result和原始数据相同，优先使用last_result作为图表数据源
                try:
                    if result is not None and original_data is not None:
                        same_columns = (
                            len(result.columns) == len(original_data.columns)
                            and result.columns.equals(original_data.columns)
                        )
                        if len(result) == len(original_data) and same_columns:
                            # 结果为全量数据，尝试用last_result替代
                            if last_result and last_result_columns:
                                try:
                                    lr_df = pd.DataFrame(last_result, columns=last_result_columns)
                                    state['analysis_result'] = lr_df
                                    print(f"[CHART-DATA] 图表数据从全量切换为last_result: {len(lr_df)}行")
                                except Exception:
                                    pass
                            # 如果没有last_result，保持analysis_result不变（图表生成器会处理）
                except Exception:
                    pass
        
        state['analysis_summary'] = analysis_summary

        # 智能选择分析结果区展示的数据
        from app.utils.response_parser import extract_tables_from_text, pick_best_display_data
        try:
            extracted = extract_tables_from_text(analysis_summary)
            ar = state.get('analysis_result')
            display_df = pick_best_display_data(
                extracted,
                ar,
                original_data if original_data is not None else pd.DataFrame()
            )
            # 额外检查：如果display_df接近全量数据，不展示
            if display_df is not None and original_data is not None and not original_data.empty:
                try:
                    ratio = len(display_df) / len(original_data)
                    same_cols = set(display_df.columns) == set(original_data.columns)
                    if ratio >= 0.9 and same_cols:
                        print(f"[DISPLAY] display_df接近全量数据（{len(display_df)}/{len(original_data)}={ratio:.1%}），不展示")
                        display_df = None
                except Exception:
                    pass

            if display_df is not None:
                state['display_result'] = display_df.to_dict('records')
                state['display_columns'] = display_df.columns.tolist()
                print(f"[DISPLAY] 分析结果区将展示: {len(display_df)}行 × {len(display_df.columns)}列 | 来源: {'文本提取' if extracted else '代码执行'}")
            else:
                if ar is not None and original_data is not None and not ar.empty:
                    try:
                        ratio = len(ar) / len(original_data)
                        same_cols = set(ar.columns) == set(original_data.columns)
                        if ratio < 0.9 or not same_cols:
                            state['display_result'] = ar.to_dict('records')
                            state['display_columns'] = ar.columns.tolist()
                            print(f"[DISPLAY] 兜底使用analysis_result: {len(ar)}行 × {len(ar.columns)}列")
                        else:
                            state['display_result'] = None
                            state['display_columns'] = []
                            print(f"[DISPLAY] 分析结果区不展示（结果为全量数据 {len(ar)}/{len(original_data)}={ratio:.1%}）")
                    except Exception:
                        state['display_result'] = None
                        state['display_columns'] = []
                else:
                    state['display_result'] = None
                    state['display_columns'] = []
                    print(f"[DISPLAY] 分析结果区不展示（无结构化数据）")
        except Exception as e:
            print(f"[DISPLAY] 智能选择失败: {e}")
            state['display_result'] = None
            state['display_columns'] = []

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
        user_query = state.get('user_query', '') or ''
        chart_keywords = ["图表", "画图", "可视化", "折线图", "柱状图", "饼图", "组合图", "散点图", "条形图", "面积图", "雷达图"]
        wants_chart = any(k in user_query for k in chart_keywords)
        
        # 优先使用display_result（智能筛选后的数据），而非analysis_result
        chart_data = state.get('analysis_result')
        display_result = state.get('display_result')
        display_columns = state.get('display_columns', [])
        if display_result and display_columns:
            try:
                import pandas as pd
                chart_data = pd.DataFrame(display_result, columns=display_columns)
            except Exception:
                pass
        
        if chart_data is not None and wants_chart:
            # 兜底：如果chart_data是原始全量数据，尝试用last_result画图
            original_data = state.get('data')
            is_chart_full_fallback = False
            if original_data is not None:
                try:
                    is_chart_full_fallback = len(chart_data) >= len(original_data) * 0.9
                except Exception:
                    pass

            if is_chart_full_fallback:
                lr = state.get('last_result')
                lc = state.get('last_result_columns', [])
                if lr and lc:
                    try:
                        chart_data = pd.DataFrame(lr, columns=lc)
                        print(f"[CHART] 图表数据从全量回退切换为last_result: {len(chart_data)}行")
                    except Exception:
                        pass

            state['chart_option'] = generate_chart_config(chart_data, user_query)
            
            # 探究性问题：出图后追加文字分析结论
            exploratory_keywords = ["看看是不是", "分析一下", "结论", "是否", "有没有", "关系", "趋势", "规律", "帮我看看", "判断", "比较"]
            is_exploratory = any(k in user_query for k in exploratory_keywords)
            
            if is_exploratory:
                try:
                    data_summary = ""
                    if display_result and display_columns:
                        data_summary = f"数据列：{', '.join(display_columns)}\n数据行数：{len(display_result)}\n前5行：{str(display_result[:5])}"
                    elif state.get('analysis_result') is not None:
                        ar = state['analysis_result']
                        data_summary = f"数据列：{', '.join(ar.columns.tolist())}\n数据行数：{len(ar)}\n前5行：{ar.head(5).to_dict('records')}"
                    
                    analysis_prompt = f"""用户的问题：{user_query}

基于以下分析数据结果，请用200字左右的中文给出明确的结论和业务洞察。要求：
1. 必须引用具体的数据和数值
2. 直接回答用户的问题（如"是不是..."就回答"是/否，因为..."）
3. 语言简洁专业，不要重复问题描述

数据结果：
{data_summary}
"""
                    chart_analysis = call_llm(state.get('model_id', 'ali-qwen'), analysis_prompt)
                    if chart_analysis:
                        existing_summary = state.get('analysis_summary', '')
                        state['analysis_summary'] = existing_summary + "\n\n📊 **图表分析结论**：\n" + chart_analysis if existing_summary else "📊 **图表分析结论**：\n" + chart_analysis
                        print(f"[CHART-ANALYSIS] 已生成图表分析结论: {chart_analysis[:80]}...")
                except Exception as e:
                    print(f"[CHART-ANALYSIS] 生成图表分析结论失败: {e}")
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
from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from app.utils.llm_client import call_qwen, generate_pandas_code, generate_clean_code
from app.utils.safe_executor import execute_pandas_code
from app.utils.chart_generator import generate_chart_config


# 定义工作流状态
class AnalysisState:
    def __init__(self):
        self.session_id: str = None
        self.file_name: str = None
        self.data: Any = None
        self.columns: List[Dict] = None
        self.user_query: str = None
        self.analysis_result: Any = None
        self.chart_option: Dict = None
        self.error: str = None
        self.history: List[Dict] = []


# 定义工作流节点
def process_query(state: AnalysisState) -> AnalysisState:
    """处理用户查询"""
    try:
        # 生成分析代码
        df_info = {
            'columns': state.columns,
            'sample_rows': state.data[:3] if state.data else []
        }
        code = generate_pandas_code(df_info, state.user_query, state.history)

        # 执行代码
        result = execute_pandas_code(code, state.data)
        state.analysis_result = result

        # 添加到历史记录
        state.history.append({
            'role': 'user',
            'content': state.user_query
        })
        state.history.append({
            'role': 'assistant',
            'content': f"分析结果: {result.head().to_dict()}"
        })
    except Exception as e:
        state.error = f"处理查询失败: {str(e)}"
    return state


def generate_visualization(state: AnalysisState) -> AnalysisState:
    """生成可视化图表"""
    try:
        if state.analysis_result is not None:
            state.chart_option = generate_chart_config(state.analysis_result, state.user_query)
    except Exception as e:
        state.error = f"生成图表失败: {str(e)}"
    return state


def clean_data(state: AnalysisState) -> AnalysisState:
    """数据清洗"""
    try:
        # 生成清洗代码
        df_info = {
            'columns': state.columns,
            'sample_rows': state.data[:3] if state.data else []
        }
        code = generate_clean_code(df_info, "请对数据进行基本清洗，包括处理缺失值、重复值等")

        # 执行代码
        result = execute_pandas_code(code, state.data)
        state.data = result
    except Exception as e:
        state.error = f"数据清洗失败: {str(e)}"
    return state


# 创建工作流图
def create_analysis_workflow():
    workflow = StateGraph(AnalysisState)

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
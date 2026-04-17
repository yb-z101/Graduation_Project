from typing import Dict, List, Tuple
import re


class IntentClassifier:
    INTENT_PATTERNS = {
        'data_display': {
            'keywords': ['展示', '显示', '查看', '所有', '全部', '有哪些', '一览', 'list'],
            'patterns': [r'列出.*(?:所有|全部)', r'看看.*有(?:哪些|什么)'],
            'priority': 1,
            'response_style': 'summary_table'
        },
        'ranking_sort': {
            'keywords': ['排名', '排序', '高低', 'top', '前几', '倒数', '从高到低', '从低到高'],
            'patterns': [r'按.*排(?:名|序)', r'.*高低.*排', r'按.*(?:从高到低|从低到高)'],
            'priority': 2,
            'response_style': 'ranked_list'
        },
        'visualization': {
            'keywords': ['图表', '画图', '可视化', '柱状图', '折线图', '饼图', '散点图', '雷达图'],
            'patterns': [],
            'priority': 3,
            'response_style': 'chart_focused'
        },
        'statistical_analysis': {
            'keywords': ['平均', '均值', '总和', '总计', '最大值', '最小值', '中位数', '标准差'],
            'patterns': [r'最(?:大|小)(?:的)?', r'平(?:均|均值)', r'总(?:和|计)'],
            'priority': 4,
            'response_style': 'statistical_summary'
        },
        'conditional_query': {
            'keywords': ['多少个', '几个', '数量', '满足', '条件', '筛选', '谁.*最', '哪个.*最'],
            'patterns': [r'.*的.*是(?:多少|哪些)', r'谁.*(?:最|有)', r'(?:满足|符合).*条件'],
            'priority': 5,
            'response_style': 'filtered_result'
        },
        'trend_comparison': {
            'keywords': ['趋势', '变化', '增长', '下降', '对比', '差异', '相关性', '分布'],
            'patterns': [r'.*(?:趋势|变化|增长|下降)', r'.*(?:对比|差异|比较)'],
            'priority': 6,
            'response_style': 'trend_analysis'
        }
    }

    @classmethod
    def classify(cls, query: str, history: List[Dict] = None) -> Tuple[str, Dict]:
        query_lower = query.lower().strip()

        for intent_type, config in cls.INTENT_PATTERNS.items():
            if 'patterns' in config:
                for pattern in config['patterns']:
                    if re.search(pattern, query_lower):
                        return intent_type, config

        matched_intents = []
        for intent_type, config in cls.INTENT_PATTERNS.items():
            keyword_matches = sum(1 for kw in config['keywords'] if kw in query_lower)
            if keyword_matches > 0:
                matched_intents.append((intent_type, config, keyword_matches))

        if matched_intents:
            matched_intents.sort(key=lambda x: (-x[2], x[1]['priority']))
            return matched_intents[0][0], matched_intents[0][1]

        return 'general_query', {'response_style': 'concise_summary'}

    @classmethod
    def extract_chart_intent(cls, query: str) -> Dict:
        query_lower = query.lower()
        chart_types = {
            'bar': ['柱状图', '条形图', 'bar'],
            'line': ['折线图', '曲线图', 'line', '趋势'],
            'pie': ['饼图', '占比', '分布', 'pie', '比例'],
            'scatter': ['散点图', '相关性', 'scatter'],
            'radar': ['雷达图', '多维', 'radar']
        }

        for chart_type, keywords in chart_types.items():
            if any(kw in query_lower for kw in keywords):
                return {'type': chart_type, 'requested': True}

        return {'type': None, 'requested': any(kw in query_lower for kw in ['图表', '画图', '可视化'])}

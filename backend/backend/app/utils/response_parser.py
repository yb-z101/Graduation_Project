import re
import json
import pandas as pd
from typing import List, Optional


def extract_markdown_tables(text: str) -> List[pd.DataFrame]:
    results = []
    pattern = r'\|(.+)\|\n\|[\s\-:|]+\|\n((?:\|.+\|\n?)+)'
    matches = re.finditer(pattern, text)
    for match in matches:
        try:
            header_line = match.group(1).strip()
            data_lines = match.group(2).strip().split('\n')
            headers = [h.strip() for h in header_line.split('|') if h.strip()]
            rows = []
            for line in data_lines:
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if len(cells) == len(headers):
                    parsed = []
                    for c in cells:
                        c = c.replace(',', '').replace('**', '').strip()
                        try:
                            if '.' in c:
                                parsed.append(float(c))
                            else:
                                parsed.append(int(c))
                        except ValueError:
                            parsed.append(c)
                    rows.append(parsed)
            if rows and headers:
                results.append(pd.DataFrame(rows, columns=headers))
        except Exception:
            continue
    return results


def extract_csv_blocks(text: str) -> List[pd.DataFrame]:
    results = []
    pattern = r'```csv\s*\n([\s\S]*?)```'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    for match in matches:
        try:
            import io
            df = pd.read_csv(io.StringIO(match.group(1).strip()))
            if not df.empty:
                results.append(df)
        except Exception:
            continue
    return results


def extract_json_blocks(text: str) -> List[pd.DataFrame]:
    results = []
    pattern = r'```json\s*\n([\s\S]*?)```'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    for match in matches:
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                results.append(pd.DataFrame(data))
        except Exception:
            continue
    return results


def extract_tables_from_text(text: str) -> List[pd.DataFrame]:
    if not text:
        return []
    all_tables = []
    all_tables.extend(extract_markdown_tables(text))
    all_tables.extend(extract_csv_blocks(text))
    all_tables.extend(extract_json_blocks(text))
    return all_tables


def pick_best_display_data(
    extracted_tables: List[pd.DataFrame],
    code_result: pd.DataFrame,
    original_data: pd.DataFrame
) -> Optional[pd.DataFrame]:
    if extracted_tables:
        best = max(extracted_tables, key=lambda df: len(df.columns) * len(df))
        return best

    if code_result is not None and not code_result.empty:
        try:
            is_same_as_original = (
                len(code_result) == len(original_data) and
                set(code_result.columns) == set(original_data.columns)
            )
        except Exception:
            is_same_as_original = False

        if not is_same_as_original:
            return code_result

    return None

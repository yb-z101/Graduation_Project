import re

class SQLSecurity:
    """SQL安全校验（防止注入、校验语法）"""
    # 危险SQL关键词（禁止删/改/建表等操作）
    DANGEROUS_KEYWORDS = ["DROP", "DELETE", "ALTER", "TRUNCATE", "INSERT", "UPDATE", "CREATE", "RENAME"]

    @classmethod
    def check_safety(cls, sql: str) -> bool:
        """校验SQL安全性：禁止危险操作"""
        if not sql or sql.strip() == "":
            return False
        sql_upper = sql.strip().upper()
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in sql_upper:
                return False
        return True

    @classmethod
    def validate_mysql_syntax(cls, sql: str) -> bool:
        """简单校验MySQL SELECT语法合法性"""
        sql_upper = sql.strip().upper()
        # 仅允许SELECT开头的查询语句
        if not sql_upper.startswith(("SELECT", "WITH")):
            return False
        # 检查括号匹配
        if sql.count("(") != sql.count(")"):
            return False
        return True
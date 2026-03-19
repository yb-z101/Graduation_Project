import requests
import time

# 模拟用户上传SQL文件
url = "http://localhost:8000/api/v1/upload"

# 创建一个正确的SQL文件内容
sql_content = """CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    age INT,
    department VARCHAR(50),
    salary DECIMAL(10, 2)
);

INSERT INTO employees (id, name, age, department, salary) VALUES
(1, '张三', 28, '技术部', 8000.00),
(2, '李四', 35, '市场部', 12000.00),
(3, '王五', 42, '管理部', 15000.00);
"""

# 上传SQL文件
files = {'file': ('user_upload.sql', sql_content, 'text/plain')}
response = requests.post(url, files=files)

print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")

# 等待一段时间，确保表创建完成
time.sleep(1)

# 检查数据库中是否创建了临时表
import subprocess
result = subprocess.run(['mysql', '-u', 'root', '-p123456', '-e', 'USE tempsql_db; SHOW TABLES;'], capture_output=True, text=True)
print("\n数据库表列表：")
print(result.stdout)
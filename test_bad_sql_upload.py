import requests

# 测试上传有问题的SQL文件
url = "http://localhost:8084/api/v1/upload"

# 创建一个有语法错误的SQL文件
bad_sql = "CREATE TABLE employees (id INT PRIMARY KEY, name VARCHAR(50)"  # 缺少右括号

# 上传有问题的SQL文件
files = {'file': ('bad_sql.sql', bad_sql, 'text/plain')}
response = requests.post(url, files=files)

print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")
import requests

# 测试SQL文件分析
url = "http://localhost:8000/api/v1/session/send_message"

# 发送分析请求
payload = {
    "session_id": "55122370-b4af-42f0-8a63-c6de9d24b5ce",
    "message": "分析一下员工数据，包括平均工资、部门分布等"
}

response = requests.post(url, data=payload)

print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")
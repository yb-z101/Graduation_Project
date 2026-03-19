import requests

# 测试前端SQL文件上传（带会话ID）
url = "http://localhost:8084/api/v1/upload"

# 打开并读取SQL文件
with open('test_upload.sql', 'rb') as f:
    files = {'file': ('test_upload.sql', f, 'text/plain')}
    data = {'session_id': 'test_session_id'}
    response = requests.post(url, files=files, data=data)

print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")
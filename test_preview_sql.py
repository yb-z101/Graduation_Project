import requests

# 测试SQL文件预览
url = "http://localhost:8000/api/v1/preview"

# 打开并读取SQL文件
with open('test_upload.sql', 'rb') as f:
    files = {'file': ('test_upload.sql', f, 'text/plain')}
    response = requests.post(url, files=files)

print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")
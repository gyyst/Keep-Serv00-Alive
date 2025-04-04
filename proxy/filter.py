import requests
import os
import sys
from urllib.parse import urlparse

# 从环境变量获取URL并解析为host和path
url = os.getenv('SUB_URL')
parsed_url = urlparse(url)
host = parsed_url.netloc
path = parsed_url.path

# 从result.txt读取内容作为payload
# 使用os.path获取绝对路径，确保在不同环境下都能正确找到文件
current_dir = os.path.dirname(os.path.abspath(__file__))
result_file_path = os.path.join(current_dir, 'result.txt')
with open(result_file_path, 'r', encoding='utf-8') as f:
    payload = f.read().strip()

headers = {
   'authority': host,
   'method': 'POST',
   'path': path,
   'scheme': 'https',
   'accept': '*/*',
   'accept-language': 'zh-CN,zh;q=0.9',
   'cache-control': 'max-age=0',
   'origin': f'https://{host}',
   'priority': 'u=1, i',
   'referer': url,
   'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
   'sec-ch-ua-mobile': '?0',
   'sec-ch-ua-platform': '"Windows"',
   'sec-fetch-dest': 'empty',
   'sec-fetch-mode': 'cors',
   'sec-fetch-site': 'same-origin',
   'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
   'content-type': 'text/plain;charset=UTF-8',
   'Host': host,
   'Connection': 'keep-alive'
}

# 检查 URL 是否为空
if url is None:
    raise ValueError("URL cannot be None")
response = requests.request("POST", str(url), headers=headers, data=payload)

print(response.text)
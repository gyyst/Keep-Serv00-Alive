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
with open('proxy/result.txt', 'r', encoding='utf-8') as f:
    payload = f.read().strip()

# 如果文件内容为空则跳过后续操作
if not payload:
    print("文件内容为空，跳过请求操作")
    sys.exit(0)

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
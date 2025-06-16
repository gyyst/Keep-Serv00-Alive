import requests
import os
import sys
import base64
import urllib.parse
from urllib.parse import urlparse

# 从环境变量获取URL并解析为host和path
url = os.getenv('SUB_URL')
if url is None:
    raise ValueError("URL cannot be None")

parsed_url = urlparse(url)
host = parsed_url.netloc
path = parsed_url.path

# 从result.txt读取内容作为payload
with open('proxy/base64.txt', 'r', encoding='utf-8') as f:
    payload = f.read().strip()

# 如果文件内容为空则跳过后续操作
if not payload:
    print("文件内容为空，跳过请求操作")
    sys.exit(0)

# 判断payload是否为base64，如果是则先解码base64，再进行URL解码
def is_base64(sb):
    try:
        # 尝试解码并重新编码匹配
        if isinstance(sb, str):
            sb_bytes = bytes(sb, 'utf-8')
        else:
            sb_bytes = sb
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False

if is_base64(payload):
    try:
        decoded_payload = base64.b64decode(payload).decode('utf-8')
        payload = urllib.parse.unquote(decoded_payload)
    except Exception as e:
        print(f"解码失败: {e}")
        sys.exit(1)

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

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

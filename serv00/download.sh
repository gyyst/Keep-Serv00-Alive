#!/bin/bash

# 定义文件下载的 URL
APP_JS_URL="https://raw.githubusercontent.com/gyyst/Keep-Serv00-Alive/refs/heads/main/serv00/app.js"
PROCESSES_JS_URL="https://raw.githubusercontent.com/gyyst/Keep-Serv00-Alive/refs/heads/main/serv00/processes.js"

# 定义本地保存的文件名
APP_JS_FILE="app.js"
PROCESSES_JS_FILE="processes.js"

# 下载 app.js
echo "正在下载 $APP_JS_FILE..."
curl -o "$APP_JS_FILE" "$APP_JS_URL"

# 检查下载是否成功
if [ $? -eq 0 ]; then
  echo "$APP_JS_FILE 下载成功！"
else
  echo "$APP_JS_FILE 下载失败，请检查网络连接或 URL 是否正确。"
  exit 1
fi

# 下载 processes.js
echo "正在下载 $PROCESSES_JS_FILE..."
curl -o "$PROCESSES_JS_FILE" "$PROCESSES_JS_URL"

# 检查下载是否成功
if [ $? -eq 0 ]; then
  echo "$PROCESSES_JS_FILE 下载成功！"
else
  echo "$PROCESSES_JS_FILE 下载失败，请检查网络连接或 URL 是否正确。"
  exit 1
fi

echo "所有文件下载完成！"
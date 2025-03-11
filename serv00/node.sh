#!/bin/bash

# 输入参数
USERNAME=$(whoami)
DEFAULT_DOMAIN="cron.${USERNAME}.serv00.net"
read -p "请输入域名（默认: $DEFAULT_DOMAIN）: " DOMAIN
IP=$(devil vhost list all | awk '/^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/ {print $1; exit}')
echo "请将域名A记录指向->$IP"
DOMAIN=${DOMAIN:-$DEFAULT_DOMAIN}
NODE="/usr/local/bin/node22"

# 删除旧网站 (强制清除)
echo "正在删除旧网站..."
devil www del $DOMAIN
rm -rf "/home/$USERNAME/domains/$DOMAIN"

# 创建新 Node.js 网站
echo "正在创建新网站..."
devil www add $DOMAIN nodejs $NODE production

# 进入网站目录
WEBSITE_DIR="/home/$USERNAME/domains/$DOMAIN"
PUBLIC_NODEJS_DIR="$WEBSITE_DIR/public_nodejs"

# 重命名 public 目录
echo "正在配置目录结构..."
cd $PUBLIC_NODEJS_DIR 
mv public static
echo '目录重命名完成'

# 安装依赖
echo "正在安装 Node.js 依赖..."
cd $PUBLIC_NODEJS_DIR
npm22 install express

cd $PUBLIC_NODEJS_DIR
bash <(curl -Ls https://raw.githubusercontent.com/gyyst/Keep-Serv00-Alive/refs/heads/main/serv00/download.sh)

echo "----------------------------------------"
echo "部署完成！请通过以下方式验证："
echo "1. 访问 https://$DOMAIN 并添加upptime等监控程序"
echo "2. 查看日志：ssh $USERNAME@$DOMAIN tail -f $WEBSITE_DIR/logs/error.log"
echo "3. 在 $PUBLIC_NODEJS_DIR/processes.js处添加需要守护的程序"
echo "4. 检查进程：ssh $USERNAME@$DOMAIN ps aux | grep node"
echo "----------------------------------------"
#!/bin/bash

# Docker中国区安装配置脚本
# 作者: MiniMax Agent
# 日期: 2025-11-01
# 适用于中国云服务器环境的Docker安装和优化配置

set -e  # 遇到错误时退出

echo "=== Docker中国区安装配置脚本开始执行 ==="

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo "错误: 此脚本需要root权限运行，请使用 sudo 执行" 
   exit 1
fi

# Docker配置文件路径
DOCKER_CONFIG="/etc/docker/daemon.json"
BACKUP_FILE="/etc/docker/daemon.json.backup.$(date +%Y%m%d_%H%M%S)"

# 检查Docker是否已安装
check_docker_installed() {
    if command -v docker &> /dev/null; then
        echo "✅ 检测到Docker已安装，版本: $(docker --version)"
        return 0
    else
        echo "❌ Docker未安装"
        return 1
    fi
}

# 安装Docker（适用于CentOS/RHEL/Ubuntu）
install_docker() {
    echo "步骤1: 开始安装Docker..."
    
    # 检测操作系统类型
    if [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        echo "检测到CentOS/RHEL系统"
        
        # 安装必要工具
        yum install -y yum-utils device-mapper-persistent-data lvm2
        
        # 添加Docker官方仓库（使用阿里云镜像）
        yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
        
        # 安装Docker
        yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        
    elif [ -f /etc/debian_version ]; then
        # Ubuntu/Debian
        echo "检测到Ubuntu/Debian系统"
        
        # 更新包索引
        apt-get update
        
        # 安装必要工具
        apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
        
        # 添加Docker官方GPG密钥（使用阿里云镜像）
        curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # 添加Docker仓库（使用阿里云镜像）
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # 更新包索引
        apt-get update
        
        # 安装Docker
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        
    else
        echo "❌ 不支持的操作系统，请手动安装Docker"
        exit 1
    fi
    
    # 启动并启用Docker服务
    systemctl start docker
    systemctl enable docker
    
    echo "✅ Docker安装完成"
}

# 备份原有Docker配置
backup_docker_config() {
    echo "步骤2: 备份原有Docker配置..."
    
    if [ -f "$DOCKER_CONFIG" ]; then
        cp "$DOCKER_CONFIG" "$BACKUP_FILE"
        echo "已备份原配置到: $BACKUP_FILE"
    else
        echo "Docker配置文件不存在，将创建新配置"
    fi
}

# 配置中国优化的Docker设置
configure_docker_for_china() {
    echo "步骤3: 配置Docker为中国网络环境优化..."
    
    # 创建优化的Docker配置文件
    cat > "$DOCKER_CONFIG" << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com",
    "https://docker.1panel.live",
    "https://ghcr.nju.edu.cn"
  ],
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true
}
EOF

    echo "已创建中国优化的Docker配置"
}

# 显示配置内容
show_config() {
    echo "步骤4: 显示Docker配置内容..."
    echo "配置文件路径: $DOCKER_CONFIG"
    echo "配置内容:"
    cat "$DOCKER_CONFIG"
}

# 重启Docker服务
restart_docker() {
    echo "步骤5: 重启Docker服务..."
    
    systemctl restart docker
    
    # 等待Docker服务启动
    sleep 5
    
    # 检查Docker服务状态
    if systemctl is-active --quiet docker; then
        echo "✅ Docker服务重启成功"
    else
        echo "❌ Docker服务重启失败，请检查配置"
        # 如果重启失败，恢复备份
        if [ -f "$BACKUP_FILE" ]; then
            echo "正在恢复备份配置..."
            cp "$BACKUP_FILE" "$DOCKER_CONFIG"
            systemctl restart docker
            echo "已恢复原配置"
        fi
        exit 1
    fi
}

# 验证配置
verify_config() {
    echo "步骤6: 验证Docker配置..."
    
    # 显示Docker信息
    echo "Docker版本信息:"
    docker version --format '客户端版本: {{.Client.Version}}'
    docker version --format '服务端版本: {{.Server.Version}}'
    
    echo ""
    echo "配置的镜像源:"
    docker info | grep -A 15 "Registry Mirrors" || echo "镜像源配置可能需要重启Docker后生效"
    
    echo ""
    echo "Docker存储驱动:"
    docker info | grep "Storage Driver"
    
    echo ""
    echo "Docker运行状态:"
    systemctl status docker --no-pager -l
}

# 测试镜像拉取
test_image_pull() {
    echo "步骤7: 测试镜像拉取（使用轻量级镜像）..."
    
    # 尝试拉取一个小的测试镜像
    if timeout 30 docker pull hello-world &> /dev/null; then
        echo "✅ 镜像拉取测试成功"
        docker rmi hello-world &> /dev/null || true
    else
        echo "⚠️ 镜像拉取测试失败，可能是网络问题，请检查镜像源配置"
    fi
}

# 显示使用说明
show_usage() {
    echo ""
    echo "=== Docker安装配置完成 ==="
    echo ""
    echo "常用命令:"
    echo "  查看Docker状态:    systemctl status docker"
    echo "  启动Docker服务:    systemctl start docker"
    echo "  停止Docker服务:    systemctl stop docker"
    echo "  重启Docker服务:    systemctl restart docker"
    echo "  查看Docker信息:    docker info"
    echo "  拉取镜像示例:      docker pull nginx"
    echo "  运行容器示例:      docker run -d -p 80:80 nginx"
    echo ""
    echo "配置文件位置: $DOCKER_CONFIG"
    echo "备份文件位置: $BACKUP_FILE"
    echo ""
    echo "如果遇到问题，可以:"
    echo "1. 检查网络连接"
    echo "2. 查看Docker日志: journalctl -u docker"
    echo "3. 恢复备份配置: cp $BACKUP_FILE $DOCKER_CONFIG && systemctl restart docker"
}

# 主执行流程
main() {
    # 检查Docker是否已安装
    if check_docker_installed; then
        echo "Docker已安装，跳过安装步骤"
    else
        install_docker
    fi
    
    backup_docker_config
    configure_docker_for_china
    show_config
    restart_docker
    verify_config
    test_image_pull
    show_usage
}

# 执行主函数
main

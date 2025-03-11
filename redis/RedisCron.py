import os
import json
import requests
import redis

def get_redis_configs():
    """从指定URL获取Redis配置"""
    config_url = os.getenv('REDIS_CONFIG_URL')
    if not config_url:
        raise ValueError("Missing REDIS_CONFIG_URL environment variable")
    
    try:
        response = requests.get(config_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise ConnectionError(f"Failed to fetch Redis config: {e}")

def update_redis(config):
    """更新单个Redis实例"""
    host = config.get("host")
    port = config.get("port", 6379)
    password = config.get("password")
    db = config.get("db", 0)
    try:
        r = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            socket_timeout=5
        )
        # 删除现有键
        r.delete("a")
        # 写入新值
        r.set("a", "b")
        print(f"✅ Updated Redis: {host}:{port}")
    except Exception as e:
        print(f"❌ Failed to update {host}:{port}: {str(e)}")

def main():
    try:
        configs = get_redis_configs()
        for config in configs:
            update_redis(config)
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()

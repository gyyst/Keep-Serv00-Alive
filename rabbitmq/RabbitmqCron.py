import os
import sys
import json
import requests
import pika

def send_ping_to_rabbitmq(config):
    host = config.get('host')
    port = config.get('port', 5672)
    username = config.get('username')
    password = config.get('password')
    vhost = config.get('vhost', '/')
    exchange_name = 'ping'  # 固定为 'ping' 交换机名称
    exchange_type = config.get('exchange_type', 'direct')  # 默认使用 fanout 类型

    try:
        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=vhost,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # 声明交换机（确保存在且持久化）
        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=exchange_type,
            durable=True
        )
        
        # 发送消息
        message = 'ping'
        channel.basic_publish(
            exchange=exchange_name,
            routing_key='',  # 对于 fanout 类型，路由键无效
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)  # 消息持久化
        )
        print(f"Sent 'ping' to {exchange_name} on {host}:{port}")
        connection.close()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)

def main():
    config_url = os.getenv('RABBITMQ_CONFIG_URL')
    if not config_url:
        print("Error: RABBITMQ_CONFIG_URL environment variable not set.", file=sys.stderr)
        sys.exit(1)
    
    try:
        response = requests.get(config_url, timeout=10)
        response.raise_for_status()
        configs = response.json()
    except Exception as e:
        print(f"Failed to fetch or parse config: {str(e)}", file=sys.stderr)
        sys.exit(1)
    for config in configs:
        send_ping_to_rabbitmq(config)

if __name__ == "__main__":
    main()
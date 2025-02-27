import os
import json
import time
import random
import requests
from bs4 import BeautifulSoup

# 从环境变量读取配置
ACCOUNTS_JSON = json.loads(os.getenv('ACCOUNTS_JSON'))
TELEGRAM_CONFIG = json.loads(os.getenv('TELEGRAM_JSON'))
PASSWORD = os.getenv('DASHBOARD_PASSWORD')
RESULTS_FILE = 'last_results.json'

def generate_random_user_agent():
    browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']
    os_versions = [
        'Windows NT 10.0; Win64; x64',
        'Macintosh; Intel Mac OS X 10_15_7',
        'X11; Linux x86_64'
    ]
    return (
        f"Mozilla/5.0 ({random.choice(os_versions)}) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) "
        f"{random.choice(browsers)}/{random.randint(70, 100)}.0.0.0 Safari/537.36"
    )

def get_csrf_token(text):
    soup = BeautifulSoup(text, 'html.parser')
    token_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    return token_input['value'] if token_input else None

def process_account(account):
    session = requests.Session()
    results = []
    username = account['username']
    panel_type = account['type']
    
    # 设置基础URL
    base_url = (
        'https://panel.ct8.pl' if panel_type == 'ct8' 
        else f"https://panel{account['panelnum']}.serv00.com"
    )
    login_url = f"{base_url}/login/?next=/cron/"
    
    try:
        # 第一次GET请求获取CSRF token
        headers = {'User-Agent': generate_random_user_agent()}
        response = session.get(login_url, headers=headers)
        csrf_token = get_csrf_token(response.text)
        
        if not csrf_token:
            raise Exception("CSRF token not found")
        
        # 登录请求
        login_data = {
            'username': username,
            'password': account['password'],
            'csrfmiddlewaretoken': csrf_token,
            'next': '/cron/'
        }
        
        response = session.post(
            login_url,
            data=login_data,
            headers=headers,
            allow_redirects=False
        )
        
        if response.status_code != 302:
            raise Exception("Login failed")
        
        # 处理cron任务
        cron_url = f"{base_url}/cron/"
        response = session.get(cron_url, headers=headers)
        
        for command in account['cronCommands']:
            try:
                if command in response.text:
                    results.append({
                        'success': True,
                        'message': f"Cron任务已存在: {command}"
                    })
                    continue
                
                # 添加新cron任务
                add_url = f"{base_url}/cron/add/"
                response_add = session.get(add_url, headers=headers)
                new_csrf = get_csrf_token(response_add.text)
                
                if not new_csrf:
                    raise Exception("Add cron CSRF token not found")
                
                cron_data = {
                    'csrfmiddlewaretoken': new_csrf,
                    'spec': 'manual',
                    'minute_time_interval': 'every',
                    'minute': '5',
                    'hour_time_interval': 'each',
                    'hour': '*',
                    'day_time_interval': 'each',
                    'day': '*',
                    'month_time_interval': 'each',
                    'month': '*',
                    'dow_time_interval': 'each',
                    'dow': '*',
                    'command': command,
                    'comment': 'Auto added cron job'
                }
                
                response_post = session.post(
                    add_url,
                    data=cron_data,
                    headers=headers,
                    allow_redirects=False
                )
                
                if response_post.status_code == 302:
                    results.append({
                        'success': True,
                        'message': f"成功添加cron任务: {command}"
                    })
                    send_telegram(f"账号 {username} 成功添加任务: {command}")
                else:
                    raise Exception(f"添加任务失败: {command}")
                
            except Exception as e:
                results.append({'success': False, 'message': str(e)})
                send_telegram(f"账号 {username} 错误: {str(e)}")
            
            time.sleep(random.randint(1, 8))  # 随机延迟
        
        return {
            'username': username,
            'type': panel_type,
            'cronResults': results,
            'lastRun': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
    
    except Exception as e:
        return {
            'username': username,
            'type': panel_type,
            'cronResults': [{'success': False, 'message': str(e)}],
            'lastRun': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }

def send_telegram(message):
    if not TELEGRAM_CONFIG:
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['telegramBotToken']}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CONFIG['telegramBotUserId'],
        'text': message
    }
    try:
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"Telegram通知发送失败: {str(e)}")

def main():
    start_time = time.time()
    all_results = []
    accounts = json.loads(ACCOUNTS_JSON)['accounts']
    
    for account in accounts:
        result = process_account(account)
        all_results.append(result)
        time.sleep(random.randint(1, 5))  # 账户间延迟
    
    # 保存结果
    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_results, f)
    
    # 发送总结通知
    duration = time.time() - start_time
    success_count = sum(1 for r in all_results if all(c['success'] for c in r['cronResults']))
    message = (
        f"任务执行完成！耗时: {duration:.1f}秒\n"
        f"成功账户: {success_count}/{len(accounts)}\n"
        f"详细结果已保存至 {RESULTS_FILE}"
    )
    send_telegram(message)

if __name__ == "__main__":
    main()

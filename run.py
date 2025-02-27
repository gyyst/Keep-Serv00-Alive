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
    browser = random.choice(browsers)
    version = random.randint(70, 100)
    os_list = [
        'Windows NT 10.0; Win64; x64',
        'Macintosh; Intel Mac OS X 10_15_7',
        'X11; Linux x86_64'
    ]
    return f'Mozilla/5.0 ({random.choice(os_list)}) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/{version}.0.0.0 Safari/537.36'

def get_csrf_token(html):
    soup = BeautifulSoup(html, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    return csrf_input['value'] if csrf_input else None

def combine_cookies(*cookies_list):
    cookie_dict = {}
    for cookies in cookies_list:
        if cookies:
            for cookie in cookies.split('; '):
                if '=' in cookie:
                    name, value = cookie.split('=', 1)
                    cookie_dict[name.strip()] = value.split(';', 1)[0].strip()
    return '; '.join([f'{k}={v}' for k, v in cookie_dict.items()])

def login_account(account):
    result_template = {
        'username': account['username'],
        'type': account['type'],
        'cronResults': [],
        'lastRun': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    print(f'当前用户: {account["username"]}')
    try:
        # 初始化请求参数
        base_url = 'https://panel.ct8.pl' if account['type'] == 'ct8' else f'https://panel{account["panelnum"]}.serv00.com'
        login_url = f'{base_url}/login/?next=/cron/'
        user_agent = generate_random_user_agent()
        session = requests.Session()

        # 第一阶段：获取初始Cookie和CSRF
        headers = {
            'User-Agent': user_agent,
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': login_url
        }
        init_res = session.get(login_url, headers=headers)
        if init_res.status_code != 200:
            raise Exception(f'初始化请求失败: {init_res.status_code}')

        csrf_token = get_csrf_token(init_res.text)
        if not csrf_token:
            raise Exception('未找到CSRF Token')

        # print(f'已成功获取Cookie和CSRF Token: {csrf_token}')
        # 第二阶段：提交登录表单
        login_data = {
            'username': account['username'],
            'password': account['password'],
            'csrfmiddlewaretoken': csrf_token,
            'next': '/cron/'
        }
        login_res = session.post(
            login_url,
            data=login_data,
            headers=headers,
            allow_redirects=False
        )
        print(login_res)
        # 验证登录结果
        if login_res.status_code != 302 or login_res.headers.get('Location') != '/cron/':
            raise Exception('登录失败，凭证错误或验证失败')

        # 第三阶段：获取Cron列表
        cron_list_url = f'{base_url}/cron/'
        cron_list_res = session.get(cron_list_url, headers=headers)
        if cron_list_res.status_code != 200:
            raise Exception('获取Cron列表失败')
        # print(cron_list_res.text)
        # 处理每个Cron命令
        for command in account['cronCommands']:
            cron_result = {'command': command, 'success': False, 'message': ''}
            try:
                # 检查是否已存在
                if command in cron_list_res.text:
                    cron_result.update({
                        'success': True,
                        'message': f'Cron已存在: {command}'
                    })
                    result_template['cronResults'].append(cron_result)
                    continue

                # 获取添加页面的CSRF
                add_cron_url = f'{base_url}/cron/add/'
                add_page_res = session.get(add_cron_url, headers=headers)
                new_csrf = get_csrf_token(add_page_res.text)
                if not new_csrf:
                    raise Exception('添加页面CSRF获取失败')

                # 构建表单数据（与JS完全一致）
                form_data = {
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

                # 带重试的提交逻辑
                max_retries = 2
                for attempt in range(max_retries):
                    post_headers = headers.copy()
                    post_headers.update({
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Origin': base_url,
                        'Referer': add_cron_url
                    })
                    
                    add_res = session.post(
                        add_cron_url,
                        data=form_data,
                        headers=post_headers,
                        allow_redirects=False
                    )

                    # 检查响应状态
                    if add_res.status_code in [302, 200]:
                        # 二次验证是否真正添加成功
                        verify_res = session.get(cron_list_url, headers=headers)
                        if command in verify_res.text:
                            cron_result.update({
                                'success': True,
                                'message': f'成功添加Cron: {command} (尝试次数: {attempt+1})'
                            })
                            break
                        else:
                            if attempt == max_retries - 1:
                                raise Exception('添加后验证失败')
                            time.sleep(2)
                    else:
                        if attempt == max_retries - 1:
                            raise Exception(f'添加请求失败: {add_res.status_code}')
                        time.sleep(2)

                result_template['cronResults'].append(cron_result)
                
            except Exception as e:
                cron_result['message'] = str(e)
                result_template['cronResults'].append(cron_result)

            # 添加随机延迟
            time.sleep(random.randint(1, 8))

        return result_template

    except Exception as e:
        result_template['cronResults'] = [{
            'success': False,
            'message': f'关键错误: {str(e)}'
        }]
        return result_template

def send_telegram(message):
    if not TELEGRAM_CONFIG:
        return

    url = f'https://api.telegram.org/bot{TELEGRAM_CONFIG["telegramBotToken"]}/sendMessage'
    try:
        requests.post(url, json={
            'chat_id': TELEGRAM_CONFIG['telegramBotUserId'],
            'text': message
        }, timeout=10)
    except Exception as e:
        print(f'Telegram通知失败: {str(e)}')

def main():
    all_results = []
    accounts = ACCOUNTS_JSON['accounts']

    for account in accounts:
        result = login_account(account)
        all_results.append(result)
        time.sleep(random.randint(1, 5))

    print(all_results)
    # 保存结果
    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    # 发送总结报告
    success_count = sum(1 for r in all_results if all(c['success'] for c in r['cronResults']))
    report = (
        f"执行完成 - 总账户数: {len(accounts)}\n"
        f"成功账户: {success_count}\n"
        f"失败账户: {len(accounts) - success_count}\n"
        f"详细情况: {json.dumps(all_results, indent=2, ensure_ascii=False)}"
    )
    send_telegram(report)

if __name__ == '__main__':
    main()

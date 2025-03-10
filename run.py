import os
import json
import time
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import html

# 新增：从 URL 获取账户配置
def fetch_accounts_from_url():
    host_url = os.getenv('HOST_URL')
    if not host_url:
        raise ValueError("❌ HOST_URL 环境变量未设置")

    try:
        # 添加请求头避免被拦截
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }
        
        # 添加 10 秒超时和 SSL 验证
        response = requests.get(
            host_url,
            headers=headers,
            timeout=10,
            verify=True
        )
        response.raise_for_status()  # 检查 HTTP 状态码
        
        # 验证 JSON 结构
        data = response.json()
        if 'accounts' not in data:
            raise ValueError("⚠️ 无效的 JSON 结构: 缺少 accounts 字段")
        
        return data
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"🔗 网络请求失败: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("📄 响应内容不是有效 JSON")

# 从环境变量读取配置
ACCOUNTS_JSON = fetch_accounts_from_url()
TELEGRAM_CONFIG = json.loads(os.getenv('TELEGRAM_JSON'))
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

def combine_cookies(cookies1, cookies2):
    cookie_map = {}
    
    def parse_cookie_string(cookie_str):
        cookie_str = cookie_str or ''  # 处理None的情况
        for cookie in cookie_str.split(','):
            cookie = cookie.strip()
            if not cookie:
                continue
            # 提取分号前的内容并去除空格
            cookie_part = cookie.split(';', 1)[0].strip()
            # 分割cookie名称和值
            parts = cookie_part.split('=', 1)
            if len(parts) != 2:
                continue
            name, value = parts[0].strip(), parts[1].strip()
            # 仅当名称和值都存在时保存
            if name and value:
                cookie_map[name] = value
    
    parse_cookie_string(cookies1)
    parse_cookie_string(cookies2)
    
    # 生成合并后的cookie字符串
    return '; '.join([f"{name}={value}" for name, value in cookie_map.items()])

def login_account(account):
    result_template = {
        'username': account['username'],
        'type': account['type'],
        'cronResults': [],
        'lastRun': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
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
        initialCookies=init_res.headers['set-cookie']
        # 第二阶段：提交登录表单
        login_data = {
            'username': account['username'],
            'password': account['password'],
            'csrfmiddlewaretoken': csrf_token,
            'next': '/cron/'
        }
        headers.update({
                        "Cookie":initialCookies,
                        "Content-Type": "application/x-www-form-urlencoded"
                    })
        login_res = session.post(
            login_url,
            data=login_data,
            headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': login_url,
            'User-Agent': user_agent,
            'Cookie': initialCookies,
            },
            allow_redirects=False
        )
        # 验证登录结果
        if login_res.status_code != 302 or login_res.headers.get('location') != '/cron/':
            raise Exception('登录失败，凭证错误或验证失败')
        loginCookies = login_res.headers.get('set-cookie')

        allCookies=combine_cookies(initialCookies,loginCookies)
        # 第三阶段：获取Cron列表
        cron_list_url = f'{base_url}/cron/'
        headers.update({
            'Cookie':allCookies
        })
        cron_list_res = session.get(cron_list_url, headers={
          'Cookie': allCookies,
          'User-Agent': user_agent,
        })
        if cron_list_res.status_code != 200:
            raise Exception('获取Cron列表失败')

        # 处理每个Cron命令
        for command in account['cronCommands']:
            cron_result = {'command': command, 'success': False, 'message': ''}
            try:
                # 检查是否已存在
                escaped_command = html.escape(command, quote=True)
                if escaped_command in cron_list_res.text:
                    cron_result.update({
                        'success': True,
                        'message': f'Cron已存在: {command}'
                    })
                    result_template['cronResults'].append(cron_result)
                    continue

                # 获取添加页面的CSRF
                add_cron_url = f'{base_url}/cron/add'
                add_page_res = session.get(add_cron_url, headers={
                    'Cookie': allCookies,
                    'User-Agent': user_agent,
                    'Referer': cron_list_url,
                })
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
                    
                    add_res = session.post(
                        add_cron_url,
                        data=form_data,
                        headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Cookie': allCookies,
                        'User-Agent': user_agent,
                        'Referer': add_cron_url,
                        'Origin': base_url,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Upgrade-Insecure-Requests': '1'
                        },
                        allow_redirects=False
                    )

                    # 检查响应状态
                    if add_res.status_code in [302, 200]:
                        # 二次验证是否真正添加成功
                        verify_res = session.get(cron_list_url, headers={
                            'Cookie': allCookies,
                            'User-Agent': user_agent,
                        })

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
            time.sleep(random.randint(10, 20))

        return result_template

    except Exception as e:
        result_template['cronResults'] = [{
            'success': False,
            'message': f'关键错误: {str(e)}'
        }]
        return result_template
def format_cron_report(data):
    report = []
    
    for user in data:
        # 转换时间格式
        last_run = datetime.strptime(user["lastRun"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # 构建用户信息
        user_info = [
            f"👤 用户: {user['username']} ({user['type']})",
            f"🕒 最后运行: {last_run}",
            "📋 Cron结果:"
        ]
        
        # 处理每个cron任务
        for cron in user["cronResults"]:
            status = "✅" if cron["success"] else "❌"
            user_info.append(f"{status} {cron['command']}")
        
        report.append("\n".join(user_info))
    
    # 添加消息头尾
    final_report = [
        "📊 Cron状态报告",
        "===================",
        *report,
        "\n🔔 所有任务状态更新完成"
    ]
    
    return "\n\n".join(final_report)

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
        
def cleanup_old_files(directory, days_to_keep=30):
    now = time.time()
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getmtime(filepath)
            if file_age > days_to_keep * 86400:  # 删除超过指定天数的文件
                os.remove(filepath)
def main():
    all_results = []
    accounts = ACCOUNTS_JSON['accounts']

    for account in accounts:
        result = login_account(account)
        all_results.append(result)
        time.sleep(random.randint(10, 25))

    # 创建 history 目录（如果不存在）
    history_dir = 'history'
    os.makedirs(history_dir, exist_ok=True)

    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    history_file = os.path.join(history_dir, f'results_{timestamp}.json')

    # 保存结果到 history 目录
    with open(history_file, 'w') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    cleanup_old_files('history', days_to_keep=30)
    # 保存结果
    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    # 发送总结报告
    success_count = sum(1 for r in all_results if all(c['success'] for c in r['cronResults']))
    report = (
        f"执行完成 - 总账户数: {len(accounts)}\n"
        f"成功账户: {success_count}\n"
        f"失败账户: {len(accounts) - success_count}\n"
        f"{format_cron_report(all_results)}"
    )
    send_telegram(report)

if __name__ == '__main__':
    main()

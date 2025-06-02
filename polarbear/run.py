import os
import json
import requests

def main():
    # Load secrets from GitHub Actions environment variable
    secret_json = os.getenv('SWAP_VPS_SECRET_JSON')
    if not secret_json:
        print("SWAP_VPS_SECRET_JSON is not set.")
        return

    try:
        secret_data = json.loads(secret_json)
    except json.JSONDecodeError as e:
        print("Error decoding secret JSON:", e)
        return

    swapname = secret_data.get('swapname')
    swappass = secret_data.get('swappass')
    pay_urls = secret_data.get('pay_urls', [])
    if not swapname or not swappass or not pay_urls:
        print("Missing swapname, swappass, or pay_urls in secrets.")
        return

    session = requests.Session()
    url_get = 'https://vps.polarbear.nyc.mn/'

    try:
        response = session.get(url_get, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error during GET request:", e)
        return

    swapuuid = session.cookies.get('swapuuid')
    if not swapuuid:
        print("swapuuid not found in cookies")
        return

    url_login = 'https://vps.polarbear.nyc.mn/index/login/?referer='
    login_data = {
        'swapname': swapname,
        'swappass': swappass
    }
    headers_login = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response_login = session.post(url_login, data=login_data, headers=headers_login, timeout=10)
        response_login.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error during login POST request:", e)
        return

    # Loop over pay_urls
    for idx, url_pay in enumerate(pay_urls, start=1):
        try:
            response_pay = session.post(url_pay, timeout=10)
            response_pay.raise_for_status()
            response_text = response_pay.text
            print(f"Pay request ({idx}) status:", response_pay.status_code)
            
            if "免费产品已经帮您续期到当前时间的最大续期时间" in response_text:
                print(f"Pay request ({idx}) SUCCESS: Free product has been renewed to the maximum date.")
            else:
                print(f"Pay request ({idx}) WARNING: Renewal success indicator not found.")
                
            print(f"Pay request ({idx}) response:", response_text)
        except requests.exceptions.RequestException as e:
            print(f"Error during pay POST request ({idx}):", e)

if __name__ == '__main__':
    main()

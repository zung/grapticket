import json
import random

import re
import requests

session = requests.session()

_data = {
    'ctx':'/otn/',
    'globalRepeatSubmitToken': '',
    'global_lang': 'zh_CN',
    'sessionInit': '',
    'isShowNotice': '',
    'CLeftTicketUrl': '',
    'isTestFlow': '',
    'isMobileCheck': '',
    'passport_appId': 'otn',
    'passport_login': 'https://kyfw.12306.cn/passport/web/login',
    'passport_captcha': 'https://kyfw.12306.cn/passport/captcha/captcha-image',
    'passport_authuam': 'https://kyfw.12306.cn/passport/web/auth/uamtk',
    'passport_captcha_check': 'https://kyfw.12306.cn/passport/captcha/captcha-check',
    'passport_authclient': 'uamauthclient',
    'passport_loginPage': 'login/init',
    'passport_okPage': 'index/initMy12306',
    'passport_proxy_captcha':  'login/init'
}

def index():
    url = 'https://kyfw.12306.cn/otn/login/init'
    res = session.get(url, verify=False)
    get_captcha()


def check_captcha():
    """校验验证码"""
    code = input("请输入验证码：")
    url = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
    data = {
        'answer': code,
        'login_site': 'E',
        'rand': 'sjrand'
    }
    res = session.post(url, data=data, verify=False)
    msg = json.loads(res.text)

    print(msg['result_message'])

    if msg['result_code'] == '4':
        start_login()
    else:
        get_captcha()


def start_login():
    """开始登录"""
    url = 'https://kyfw.12306.cn/passport/web/login'
    username = input("请输入用户名：")
    password = input("请输入密码：")

    data = {
        "username": username,
        "password": password,
        "appid": 'otn'
    }

    res = session.post(url, data=data, verify=False)
    msg = json.loads(res.text)

    print(msg)

    if msg['result_code'] == 0:
        check_login()


def check_login():
    """验证是否已经登录"""
    url = _data['passport_authuam']
    data = {
        'appid': _data['passport_appId'],
        'withCredentials': True
    }
    res = session.post(url, data=data, verify=False)
    msg = json.loads(res.text)

    tk = None

    if msg['result_code'] == 0: # 已经登录
        if msg['apptk']:
            tk = msg['apptk']
        else:
            tk = msg['newapptk']
        if tk:
            uampasswort(tk)
        else:
            print('token为空')
    else:
        print(msg['result_message'])


def uampasswort(tk):
    url = 'https://kyfw.12306.cn' + _data['ctx'] + _data['passport_authclient']
    data = {
        'tk': tk
    }
    res = session.post(url, data=data, verify=False)
    msg = json.loads(res.text)

    if msg['result_code'] == 0: # 验证通过
        # 跳转到指定页面
        get_passengers()
    else:
        print(msg['result_message'])


def get_captcha():
    """获取验证码图片,并保存到本地"""
    r = str(random.random())
    url = 'https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand&' + r
    res = session.get(url, verify=False)
    f = open('captcha.png', 'wb')
    f.write(res.content)
    f.close()

    check_captcha()


def get_passengers():
    url = 'https://kyfw.12306.cn/otn/passengers/init'
    res = session.get(url, verify=False)
    html = res.text
    pa = r'var passengers=(.*?);\n var pageSize ='
    passengers = re.findall(pa, html)
    peoples = json.loads(passengers[0].replace("'", '"'))

    print(json.dumps(peoples, sort_keys=True, indent=2))


if __name__ == '__main__':
    index()

import base64
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
        get_left_ticket_log()

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
    """获取联系人"""
    url = 'https://kyfw.12306.cn/otn/passengers/init'
    res = session.get(url, verify=False)
    html = res.text
    pa = r'var passengers=(.*?);\n var pageSize ='
    passengers = re.findall(pa, html)
    peoples = json.loads(passengers[0].replace("'", '"'))

    return peoples


def get_left_ticket_log():
    url = 'https://kyfw.12306.cn/otn/leftTicket/log?leftTicketDTO.train_date=2017-11-06&leftTicketDTO.from_station=\
    JGK&leftTicketDTO.to_station=UCK&purpose_codes=ADULT'
    res = session.get(url, verify=False)
    msg = json.loads(res.text)
    print(msg)
    if msg['status'] and msg['validateMessagesShowId'] == '_validatorMessage':
        get_left_ticket()
    else:
        print(msg)


def get_left_ticket():
    url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=2017-11-07&leftTicketDTO.from_station=JGK&leftTicketDTO.to_station=UCK&purpose_codes=ADULT'
    res = session.get(url, verify=False)
    msg = json.loads(res.text)
    print(json.dumps(msg, sort_keys=True, indent=2, ensure_ascii=False))
    results = msg['data']['result']

    info = []
    train = {}

    for result in results:
        cols = result.split('|')
        train['车次'] = cols[3]
        train['出发站'] = get_name_by_code(cols[4])
        train['到达站'] = get_name_by_code(cols[5])
        train['出发时间'] = cols[8]
        train['到达时间'] = cols[9]
        train['历时'] = cols[10]
        train['当日到达'] = cols[11]
        info.append(train)

        for i, c in enumerate(cols):
            if i == 0 or i == 12:
                continue
            print('%s:\t%s'%(i + 1, c), end=' ')
            if (i+1) % 9 == 0:
                print('')
        print('')

    print(info)



def base642str(_base64):
    return base64.b64decode(_base64)


def get_station_names():
    """获取所有站点名字"""
    url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9030'
    res = session.get(url, verify=False)
    js = res.text
    result = js.split("'")[1]
    stations = {}
    for city in result.split('@'):
        if city:
            s = city.split('|')
            stations[s[2]] = {}
            stations[s[2]]['汉字'] = s[1]
            stations[s[2]]['简拼'] = s[0]
            stations[s[2]]['全拼'] = s[3]
    json.dump(stations, open('stations.json', 'w'))


def get_name_by_code(code):
    stations = json.load(open('stations.json', 'r'))
    return stations[code]['汉字']


if __name__ == '__main__':
    # index()
    get_left_ticket()
    # get_station_names()
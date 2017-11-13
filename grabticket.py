import json
import random
import re
from urllib.parse import quote, unquote

import datetime
import requests
import urllib3
from PIL import Image

from urllib3.exceptions import InsecureRequestWarning

# 禁用安全请求警告
urllib3.disable_warnings(InsecureRequestWarning)

_data = {
    'ctx': '/otn/',
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
    'passport_proxy_captcha': 'login/init'
}

headers = {
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0(Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept-Language": "zh-CN, zh; q=0.9",
}

session = requests.session()
session.headers = headers


def index():
    url = 'https://kyfw.12306.cn/otn/login/init'
    res = session.get(url, verify=False)
    get_captcha()


def check_captcha():
    """校验验证码"""
    img = Image.open('captcha.png')
    img.show()

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

    if msg['result_code'] == 0:  # 已经登录
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
    print(res.text)
    msg = json.loads(res.text)

    if msg['result_code'] == 0:  # 验证通过
        # 跳转到指定页面
        get_left_ticket()

    else:
        print(msg['result_message'])


def check_user():
    """验证用户"""
    url = 'https://kyfw.12306.cn/otn/login/checkUser'
    data = {'_json_att': ''}
    res = session.post(url, data=data, verify=False, headers={'If-Modified-Since': '0',
                                                              'Cache-Control': 'no-cache',
                                                              'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'})
    msg = json.loads(res.text)
    print('验证用户')
    print(msg)
    if msg['status']:
        if msg['data']['flag']:
            return True

    else:
        print(msg['messages'])
    return False


def submit_order(t, _f, _t):
    """提交预订单"""

    url = 'https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest'
    trainDate = str2date_format1(t['出发日'])
    backDate = trainDate

    data = {
        "secretStr": unquote(t['secretStr']),
        "train_date": trainDate,
        "back_train_date": backDate,
        "tour_flag": "dc",
        "purpose_codes": "ADULT",
        "query_from_station_name": _f,
        "query_to_station_name": _t,
        "undefined": None
    }

    if not check_user():
        return False

    res = session.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, verify=False)

    msg = json.loads(res.text)
    print(msg)
    if msg['status']:
        if msg['data'] == 'Y':
            print('您选择的列车距开车时间很近了，\n请确保有足够的时间抵达车站，\n并办理换取纸质车票、安全检查、\
            实名制验证及检票等手续，以免耽误您的旅行。')
        # 跳转到确认乘客人页面
        confirm_passenger()
    else:
        print(msg['messages'])
        return False


def confirm_passenger():
    """确认乘客信息"""
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
    res = session.get(url, verify=False)
    # print(res.text)

    token_pattern = r'var globalRepeatSubmitToken = \'(.*?)\';'
    token = re.findall(token_pattern, res.text)[0]

    pattern = r'var ticketInfoForPassengerForm=(.*?);'
    ticketInfoStr = re.findall(pattern, res.text)[0]  # 车票信息
    ticketInfoStr = ticketInfoStr.replace('\'', '"')
    ticketInfoJson = json.loads(ticketInfoStr)
    print(json.dumps(ticketInfoJson, sort_keys=True, indent=2, ensure_ascii=False))

    trainInfo = ticketInfoJson['queryLeftTicketRequestDTO']  # 列车信息
    leftTicketStr = ticketInfoJson['leftTicketStr']
    train_date = trainInfo['train_date']

    # 星期几
    weekday = get_weekday_by_date(datetime.date(int(train_date[:4]), int(train_date[4:6]), int(train_date[6:8])))

    print("列车信息(以下余票信息仅供参考)")
    print(str2date_format1(train_date) + '（' + weekday + '） ' + trainInfo['station_train_code'] + '次 ' \
          + trainInfo['from_station_name'] + '站（' + trainInfo['start_time'] + '开）' \
          + "--" + trainInfo['to_station_name'] + '站（' + trainInfo['arrive_time'] + '到）')
    print('-----------------------------------------------------------------')
    leftDetails = ticketInfoJson['leftDetails']
    for det in leftDetails:
        print(det + '\t', end='')

    # 获取乘客信息
    normal_passengers = get_passengers(token)
    if normal_passengers:
        print("乘客信息")
        for passenger in normal_passengers:
            print('1.' + passenger['passenger_name'])

    while True:
        k = input('选择乘客，请输入%d - %d之间的数字来选择车次：' % (1, len(normal_passengers)))
        if not k.isdigit():
            print('请输入数值类型！')
            continue
        k = int(k)
        if k < 1 or k > len(normal_passengers):
            print('输入有误!请重新输入')
            continue

        p = normal_passengers[k - 1]
        break

    passengerTicketStr = get_passenger_tickets()

    formData = {

    }

    # 验证订单
    flag = check_order_info(token, passengerTicketStr, oldPassengerStr=None, tour_flag=None)
    if flag:  # 验证成功
        queueCountData = get_queue_count(formData)  # 获取队列计数
        # 提交订单

    else:
        flag = False


def get_queue_count(data):
    """获取队列计数"""
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount'
    res = session.post(url, data=data, verify=False)
    msg = json.loads(res.text)
    if msg['status']:
        return msg['data']
    else:
        print(msg['messages'])
        return False


def get_weekday_by_date(date):
    """根据日期获取当前是星期几"""
    weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    return weekday[date.weekday()]


def get_standard_time(date):
    """获取标准时间"""
    return date.strftime('%a %b %Y %H:%M:%S ') + 'GMT+0800 (中国标准时间)'


def get_passenger_tickets(limitTickets):
    str = ''
    for v in limitTickets:
        av = v['seat_type'] + ',0,' + v['ticket_type'] + ',' + v['name'] + ',' \
             + v['id_type'] + ',' + v['id_no'] + ',' + v['phone_no'] + ',' \
             + 'N' if v['save_status'] == '' else 'Y'
        str += av + '_'
    return str[:len(str) - 1]


def get_old_passengers(ticketInfoStr, limitTickets):
    str = ''
    for v in limitTickets:
        pass


def limit_tickets():
    """获取限购车票的列表"""
    pass


def ticket_submit_order():
    """获取车票提交订单信息"""
    tso = json.load(open('ticket_submit_order.json', 'r', encoding='utf-8'))
    print(tso)


def check_order_info(token, passengerTicketStr, oldPassengerStr, tour_flag):
    """验证订单信息"""
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo'
    data = {
        'cancel_flag': '2',
        'bed_level_order_num': '000000000000000000000000000000',
        'passengerTicketStr': passengerTicketStr,
        'oldPassengerStr': oldPassengerStr,
        'tour_flag': tour_flag,
        'randCode': '',
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': token
    }

    res = session.post(url, data=data, verify=False)
    msg = json.loads(res.text)
    if msg['status'] and msg['data']['submitStatus']:
        return True
    else:
        print(msg['messages'])
        return False


def str2date_format1(str):
    """字符串转日期格式 yyyy-MM-dd"""
    l = list(str)
    l.insert(4, '-')
    l.insert(-2, '-')
    return ''.join(l)


def get_captcha():
    """获取验证码图片,并保存到本地"""
    r = str(random.random())
    url = 'https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand&' + r
    res = session.get(url, verify=False)
    f = open('captcha.png', 'wb')
    f.write(res.content)
    f.close()

    check_captcha()


def get_passengers(token):
    """获取乘客信息"""
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs'
    data = {
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': token
    }
    res = session.post(url, data=data, verify=False)
    html = res.text
    msg = json.loads(html)
    if msg['status'] and msg['data']['isExist']:
        return msg['data']['normal_passengers']
    else:
        print("没有获取到乘客信息")
        return None


def get_pass_code():
    r = str(random.random())
    url = 'https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=passenger&rand=randp&' + r
    res = session.get(url, verify=False)
    print(res.text)
    return True


def get_left_ticket_log(d, f, t):
    url = 'https://kyfw.12306.cn/otn/leftTicket/log?leftTicketDTO.train_date=' + d + '&leftTicketDTO.from_station=' \
          + f + '&leftTicketDTO.to_station=' + t + '&purpose_codes=ADULT'
    res = session.get(url, verify=False)
    msg = json.loads(res.text)
    print(msg)
    if msg['status'] and msg['validateMessagesShowId'] == '_validatorMessage':
        return True
    else:
        print(msg)
    return False


def get_left_ticket():
    d = input('请输入出发日(如:2017-11-07):')
    if not re.match(r'\d{4}(-\d{2}){2}', d):
        print('日期格式不对')
        get_left_ticket()

    f = input('请输入出发地（简拼/全拼/汉字）:')
    t = input('请输入目的地（简拼/全拼/汉字）:')

    _from = get_code_by_input(f)
    _to = get_code_by_input(t)

    fromStation = quote(get_code_by_input(_from) + ',' + _from).replace('\\', '%')
    toStation = quote(get_code_by_input(_to) + ',' + _to).replace('\\', '%')
    print(fromStation)

    cookies = {
        "_jc_save_fromDate": d,
        "_jc_save_fromStation": fromStation,
        "_jc_save_toDate": d,
        "_jc_save_toStation": toStation,
        "_jc_save_wfdc_flag": "dc",
    }

    requests.utils.add_dict_to_cookiejar(session.cookies, cookies)

    # ck = requests.utils.cookiejar_from_dict(cookies)
    # session.cookies = ck

    if not get_left_ticket_log(d, _from, _to):
        return None

    url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=' + d + '&leftTicketDTO.from_station=' \
          + _from + '&leftTicketDTO.to_station=' + _to + '&purpose_codes=ADULT'
    res = session.get(url, verify=False)
    msg = json.loads(res.text)
    print(json.dumps(msg, sort_keys=True, indent=2, ensure_ascii=False))
    results = msg['data']['result']

    info = []

    for result in results:
        cols = result.split('|')
        train = {}
        train['车次'] = cols[3]
        train['出发站'] = get_code_by_input(cols[4])
        train['到达站'] = get_code_by_input(cols[5])
        train['出发时间'] = cols[8]
        train['到达时间'] = cols[9]
        train['历时'] = cols[10]
        train['当日到达'] = cols[11]
        train['出发日'] = cols[13]
        train['商务座特等座'] = cols[32]
        train['一等座'] = cols[31]
        train['二等座'] = cols[30]
        train['高级软卧'] = cols[21]
        train['软卧'] = cols[23]
        train['动卧'] = cols[33]
        train['硬卧'] = cols[28]
        train['软座'] = cols[24]
        train['硬座'] = cols[29]
        train['无座'] = cols[26]
        train['其它'] = cols[22]
        train['secretStr'] = cols[0]
        if cols[0]:
            info.append(train)

        for i, c in enumerate(cols):
            if i == 0 or i == 12:
                continue
            print('%s:\t%s' % (i + 1, c), end=' ')
            if (i + 1) % 9 == 0:
                print('')
        print('')

    print(json.dumps(info, sort_keys=True, indent=2, ensure_ascii=False))

    t = {}
    while True:
        k = input('开始预订，请输入%d - %d之间的数字来选择车次：' % (1, len(info)))
        if not k.isdigit():
            print('请输入数值类型！')
            continue
        k = int(k)
        if k < 1 or k > len(info):
            print('输入有误!请重新输入')
            continue

        t = info[k - 1]
        if submit_order(t, get_code_by_input(_from), get_code_by_input(_to)):
            break
        else:
            continue


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
    json.dump(stations, open('stationsb.json', 'w'))


def get_code_by_input(value):
    stations = json.load(open('stationsb.json', 'r'))
    for key in stations.keys():
        if value in stations[key].values():
            return key
    else:
        return stations[value]['汉字']


if __name__ == '__main__':
    index()
    # get_left_ticket()
    # get_station_names()
    # ticket_submit_order()
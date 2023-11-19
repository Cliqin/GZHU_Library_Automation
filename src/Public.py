import traceback
import timeout_decorator
from loguru import logger
import requests
import json
import datetime
import time
import re
import httpx
import random
from lxml import etree
from rsa import RSA
from urllib.parse import unquote

BASIC_URL = 'http://libbooking.gzhu.edu.cn/ic-web'
DT = datetime.datetime


class Login:
    def __init__(self, XueHao, MiMa, pushplus):
        """请求定制"""
        self.rr = httpx.Client()
        # xpath搜索路径
        self.xpath_rules = {
            'lt': '//input[@id="lt"]/@value',
            'execution': '//input[@name="execution"]/@value'
        }
        # 请求头
        self.headers = {
            "Host": "libbooking.gzhu.edu.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.42",
            "token": "a50b1863a0394feab1e4de8d3f370c97",
            "Origin": "http://libbooking.gzhu.edu.cn",
            "Referer": "http://libbooking.gzhu.edu.cn/",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive"
        }
        # 个人账号信息
        self.XueHao = XueHao  # 学号
        self.MiMa = MiMa  # 密码
        self.pushplus = pushplus  # 'da9840d244194425bb1d1435fcd662da'

    '''获取登陆url'''

    def Get_LoginUrl(self):
        try:
            params = {
                "finalAddress": "http://libbooking.gzhu.edu.cn",
                "errPageUrl": "http://libbooking.gzhu.edu.cn/#/error",
                "manager": "false",
                "consoleType": "16"
            }
            # 获得重定向url
            redirect = self.rr.get(url=BASIC_URL + '/auth/address', params=params).json()['data']
            # get重定向url
            res = self.rr.get(redirect)
            # 返回应答报文的请求头的Location 里面有login_url
            return self.login(res.headers.get('Location'))
        except Exception as e:
            logger.error(f'\nget_loginUrl error\n错误信息:{e}')
            self.notify('图书馆登陆异常信息', f'学号:{self.XueHao}\nget_loginUrl error\n错误信息:{e}')

    '''获取cookie'''

    def login(self, login_url):
        try:
            execution = 'e1s1'  # 应该是固定的
            # 请求登录url获取lt参数 因为他会变
            res = self.rr.get(url=login_url)
            html = etree.HTML(res.text)
            lt = html.xpath(self.xpath_rules['lt'])[0]
            # 把密码和那些参数用RSA加密
            rsa = RSA().strEnc(self.XueHao + self.MiMa + lt)
            data = {
                'rsa': rsa,
                'ul': len(self.XueHao),
                'pl': len(self.MiMa),
                'lt': lt,
                'execution': execution,
                '_eventId': 'submit',
            }
            # 提交登陆请求
            res = self.rr.post(url=login_url, data=data, timeout=60)
            # 返回的请求头有ticket信息
            location = res.headers.get('Location')
            ticket = re.findall('ticket=(.*)', location)[0]  # 获取ticket
            # 获得location unitoken uuid 参数
            location = self.rr.get(f"{re.findall('service=(.*)', login_url)[0]}?ticket={ticket}"
                                   ).headers.get('Location')
            # 2023.9.23更新编码问题
            # unitoken = re.findall('uniToken=(.*)', str(location))[0]  # 获取unitoken
            # uuid = re.findall('uuid=(.*?)&', str(location))[0]  # 获取 uuid

            decoded_url = unquote(location)
            unitoken = re.findall('uniToken=(.*)', str(decoded_url))[0]  # 获取unitoken
            uuid = re.findall('uuid=(.*?)&', str(decoded_url))[0]  # 获取 uuid
            params = {"manager": "false", "uuid": uuid, "consoleType": "16", "uniToken": unitoken}
            # 获取 cookies
            get_cookie_res = self.rr.get(
                url="http://libbooking.gzhu.edu.cn/ic-web//auth/token",
                params=params,
                headers=self.headers
            ).headers.get('Set-Cookie')

            # 如果没获取到,就重新来吧
            if not get_cookie_res:
                return None

            # 分割ic-cookie
            IC_cookie = 'ic-cookie=' + re.findall('ic-cookie=(.*?);', get_cookie_res)[0]
            return IC_cookie
        except Exception as e:
            logger.error(f'\nlogin error\n错误信息:{e}')
            self.notify('图书馆登陆异常信息', f'学号:{self.XueHao}\nlogin error\n错误信息:{e}')
            return

    '''假如密码失效启动通知'''

    def notify(self, title, content):
        if self.pushplus:
            data = {"token": self.pushplus, "title": title, "content": content}
            print(requests.post("http://www.pushplus.plus/send/", data=data).text)


'''更新Cookie'''


def Update_Cookie(self):
    # 测试此时的cookies能否可以使用
    self.Cookie = None
    counter = 0
    while self.Cookie is None or len(self.Cookie) == 0:
        print(f'第{counter + 1}次尝试登陆')
        if counter > 20:
            return 'error'
        self.Cookie = Login(self.XueHao, self.MiMa, self.pushplus).Get_LoginUrl()
        time.sleep(1)
        counter += 1
    self.header['Cookie'] = self.Cookie
    with open('cookie.txt', 'w') as file:
        file.write(self.Cookie)


'''每天6点多的预约'''


def Broadly_Submit(self, reps=1, timeFlag=None, randomFlag=None):
    message = []
    rsvDay = datetime.date.today() + datetime.timedelta(days=1)  # 时间推后一天
    wday = int(rsvDay.weekday())  # 获取星期 例:0为星期一
    rsvDay = rsvDay.strftime('%Y-%m-%d')  # 字符串化:2023-04-11
    seatNo = self.SeatNo
    if randomFlag:
        seatNo = [seatNo[random.randint(0, len(seatNo) - 1)]]
    if timeFlag:
        Wait_OnTime(1, self.myTime)
    for rep in range(reps):
        for no in seatNo:
            for rsv in self.RsvTime_seat[wday]:
                res = Rsv_Submit(self, rsvDay, str(no), rsv[0], rsv[1]).json()
                message.append(f'{rsvDay} {no} {rsv[0]} {rsv[1]} {[self.Id]} {Color(res["message"], 6)}')

    rsvDay = datetime.date.today() + datetime.timedelta(days=2)  # 依次往后倒推
    wday = int(rsvDay.weekday())  # 获取星期 0为星期一
    rsvDay = rsvDay.strftime('%Y-%m-%d')  # 字符串化:2023-04-11
    roomNo = self.RoomNo
    if timeFlag:
        Wait_OnTime(2, self.myTime)
    for rep in range(reps):
        for no in roomNo:
            for rsv in self.RsvTime_seminar[wday]:
                res = Rsv_Submit(self, rsvDay, str(no), rsv[0], rsv[1]).json()
                message.append(f'{rsvDay} {self.RoomList[no]} {rsv[0]} {rsv[1]} {[self.Id]} {Color(res["message"], 6)}')
    return message


'''查看我的预约'''


def My_Reserve(self, flag=None):
    url = BASIC_URL + '/reserve/resvInfo'
    # 默认请求表单 请求所有时间段 除了结束的预约信息
    params = {
        'beginDate': '2022-04-17',
        'endDate': '2025-09-13',
        'needStatus': 262,
        'page': 1,
        'pageNum': 100,
        'orderKey': 'gmt_create',
    }

    # 是否查询累计预约时间
    if flag:
        # 只查询总预约
        params['needStatus'] = 128
        # 只查询该月份的
        if flag == 2:
            today = DT.today()
            params['beginDate'] = today.strftime('%Y-%m-01')
            params['endDate'] = today.strftime('%Y-%m-31')
        # 只查询上月份的
        elif flag == 3:
            thatDay = DT.today() + datetime.timedelta(days=-31)
            params['beginDate'] = thatDay.strftime('%Y-%m-01')
            params['endDate'] = thatDay.strftime('%Y-%m-31')
        # 发送第一次查询请求
        res = requests.get(url=url, headers=self.header, params=params).json()
        # 判断是否继续翻页查询
        seminar, rseminar, seat, rseat = Total_Span(res['data'])
        roundTime = res['count'] / 100 - 1
        while roundTime > 0:
            params['page'] += 1
            # 继续发请求,并继续记录时间总和
            res = requests.get(url=url, headers=self.header, params=params).json()
            tmp1, tmp2, tmp3, tmp4 = Total_Span(res['data'])
            seminar += tmp1
            rseminar += tmp2
            seat += tmp3
            rseat += tmp4

            roundTime -= 1
        return TS_Span(seminar), TS_Span(rseminar), TS_Span(seat), TS_Span(rseat)

    # 只需要查询当前预约的信息即可
    res = requests.get(url=url, headers=self.header, params=params).json()
    myList = []
    for i in res['data']:
        bt = i['resvBeginTime']
        et = i['resvEndTime']
        item = {
            'no': i['resvDevInfoList'][0]['devName'],
            'uuid': i['uuid'],
            'bt': DT.fromtimestamp(bt / 1000).strftime('%Y-%m-%d %H:%M'),
            'et': DT.fromtimestamp(et / 1000).strftime('%H:%M'),
            'status': i['resvStatus']
        }
        myList.append(item)
    return myList


'''预约发送请求函数'''


def Rsv_Submit(self, rsvday, dev, start, end, friendFlag=None):
    url = BASIC_URL + '/reserve'
    # 判断是否研讨室还是座位
    if '-' in str(dev):
        '''座位'''
        seat = {
            "appAccNo": self.Id,
            "captcha": "",
            "memberKind": 1,
            "memo": "搞学习",
            "resvBeginTime": f"{rsvday} {start}",
            "resvDev": [calc_dev_no(dev)],
            "resvEndTime": f"{rsvday} {end}",
            "resvMember": [self.Id],
            "resvProperty": 0,
            "sysKind": 8,
            "testName": "",
        }
        return requests.post(url=url, headers=self.header, json=seat)
    '''研讨室'''
    seminar = {
        'addServices': [],
        'appAccNo': self.Id,
        'appUrl': "",
        'captcha': "",
        'memberKind': 2,
        'memo': "学习",
        'resvBeginTime': f"{rsvday} {start}",
        'resvDev': [dev],
        'resvEndTime': f"{rsvday} {end}",
        'resvKind': 2,
        # 如果有朋友标志,则在列表后添加朋友Id
        'resvMember': [self.Id, self.FriendId] if friendFlag else [self.Id],
        'resvProperty': 0,
        'sysKind': 1,
        'testName': "学习",
    }
    return requests.post(url=url, headers=self.header, json=seminar)


'''修改预约(需要改动)'''


def Rescheduling(self):
    """显示已预约的信息,再进行选择"""
    res = My_Reserve(self)
    for index, i in enumerate(res):
        tmp = Color(f"{i['no']} \t{i['bt']}", 1)
        print(f"{index}\t {tmp}--{i['et']}\t状态:{status(i['status'])}")
    p = int(input('请选择序号0-20\n'))
    # optimal = [[0, 0, 0], 0]  # [[开始时间,结束时间,时间间隔],房号]  毫秒级
    today = res[p]["bt"][:10]
    dev = res[p]["no"]
    previous = [today, res[p]["bt"][11:], res[p]["et"], dev]
    print('你已选中', Color(previous, 6))
    # 前头自动补零操作: 补两个零
    new_bhour = str('%02d' % int(input('请输入开始小时:\t')))
    new_bmin = str('%02d' % int(input('请输入开始分钟:\t')))
    new_ehour = str('%02d' % int(input('请输入结束小时:\t')))
    new_emin = str('%02d' % int(input('请输入结束分钟:\t')))
    polish = [today, f'{new_bhour}:{new_bmin}', f'{new_ehour}:{new_emin}', dev]
    print('转换前', Color(previous, 6))
    print('转换后', Color(polish, 6))
    confirm = input('1--提交|0--撤回操作\n')
    if confirm == '1':
        if '-' in polish[3]:
            print(dev, Cancel_Submit(self, res[p]["uuid"]).json()['message'])

            res = Rsv_Submit(self, polish[0], polish[3], polish[1] + ':00', polish[2] + ':00').json()
            print(today, polish[3], polish[1] + ':00', polish[2] + ':00', Color(res['message'], 6))

            res = Rsv_Submit(self, previous[0], previous[3], previous[1] + ':00', previous[2] + ':00').json()
            print('重新选回座位', Color(res['message'], 6))
            return
        for i, v in self.RoomList.items():
            if v == polish[3]:
                print(dev, Cancel_Submit(self, res[p]["uuid"]).json()['message'])

                res = Rsv_Submit(self, polish[0], i, polish[1] + ':00', polish[2] + ':00').json()
                print(today, polish[3], polish[1] + ':00', polish[2] + ':00', Color(res['message'], 6))

                res = Rsv_Submit(self, previous[0], i, previous[1] + ':00', previous[2] + ':00').json()
                print('重新选回座位', Color(res['message'], 6))
                return
    else:
        print('已撤回')


'''精准发送预约表单'''


def Precision_Submit(self, optimal, minUser):
    # 判断是否有预约位置信息
    if optimal[1] == 0:
        return
    # 输入数据
    rsvDay = DT.fromtimestamp(optimal[0][0] / 1000).strftime('%Y-%m-%d')  # 预约日期
    devId = optimal[1]  # 预约房间
    sT = DT.fromtimestamp(optimal[0][0] / 1000).strftime('%H:%M:%S')  # 开始时间
    eT = DT.fromtimestamp(optimal[0][1] / 1000).strftime('%H:%M:%S')  # 结束时间
    if minUser == 1:
        res = Rsv_Submit(self, rsvDay, devId, sT, eT).json()
        return f"{rsvDay}, {self.RoomList[devId]}, {sT}, {eT}, {[self.Id]}, {Color(res['message'], 6)}"
    elif minUser == 2:
        res = Rsv_Submit(self, rsvDay, devId, sT, eT, 1).json()
        return f"{rsvDay}, {self.RoomList[devId]}, {sT}, {eT}, {[self.Id, self.FriendId]}, {Color(res['message'], 6)}"


'''取消某个预约'''


def Cancel_Submit(self, uuid):
    try:
        return requests.post(url=BASIC_URL + '/reserve/delete', headers=self.header, json={'uuid': uuid}, timeout=20)
    except Exception as e:
        print(e)
        exit(0)


'''签到与暂离回来功能'''


def Clock_In(self, dev):
    # 判断是自习室还是研讨室
    if '-' in dev:
        # 自习室所需要用到的url
        login_url = BASIC_URL + '/phoneSeatReserve/login'  # 登陆
        signSeat_url = BASIC_URL + '/phoneSeatReserve/sign'  # 签到
        comeBack_url = BASIC_URL + '/phoneSeatReserve/comeback'  # 暂离返回

        login_data = {
            "devSn": calc_dev_no(dev),
            "unionId": "o8QfLt2M2Pz0h04ArxMG6SeWdarc",
            "type": "1",
            "bind": 0,
            "loginType": 2
        }
        login_res = requests.post(url=login_url, headers=self.header, json=login_data).json()

        if login_res['data']['reserveInfo'] is None:
            return '该预约还未生效,请稍后再试'
        # 如果生效了,会生成一个新的resvId出来,通过这个resvId来进行sign和comeback
        resvId = login_res['data']['reserveInfo']['resvId']
        sign_res = requests.post(url=signSeat_url, headers=self.header, json={"resvId": resvId}).json()
        comeback_res = requests.post(url=comeBack_url, headers=self.header, json={"resvId": resvId}).json()
        return sign_res['message'] + '\t' + comeback_res['message']
    else:
        for index, i in self.RoomList.items():
            if i == dev:
                signRoom_url = BASIC_URL + '/pad/accountByQR'  # 签到
                data = {
                    "szLogonName": self.XueHao,
                    "szPassword": self.MiMa,
                    "szCtrlSn": 1017,
                    "timeStamp": "84d426c725b32474aa0bc5f4a4e530cb"  # 加密时间戳,就差这一步,我草,一座大山,始终跨越不了
                }
                # stampValid_url = fBASIC_URL+'/pad/valid?timeStamp={data["timeStamp"]}'

                return requests.post(url=signRoom_url, headers=self.header, json=data).text


'''设置Predator定时器'''


def Timer_Predator(self, date, keepTime=None):
    @timeout_decorator.timeout(keepTime)
    def do_time():
        Predator(self, date)

    def do():
        Predator(self, date)

    # 判断keepTime是否为0或None
    if keepTime:
        do_time()
    else:
        do()


'''时刻捕获空缺的时间段'''


def Predator(self, date):
    rsvDay = datetime.datetime.strptime(date, '%Y-%m-%d')
    weekday = int(rsvDay.weekday())  # 获取星期 0为星期一
    print(f'预约日期: {rsvDay} 星期: {weekday + 1}')
    rsvDay = rsvDay.strftime('%Y%m%d')  # 字符串化:20230411

    optimal = [[0, 0, 0], 0]  # [[开始时间,结束时间,时间间隔],房号]
    minUser = 1
    print('正在检索中,请耐心等待')
    while optimal[0][2] == 0:
        # 获得所有房间的信息
        data = Retrieve(self, rsvDay).json()
        if weekday == 4:
            '''星期五'''
            for i in data['data']:
                if i["devId"] in self.RoomList.keys():
                    resvInfo = i['resvInfo']
                    # startTime         endTime
                    sT1, eT1 = sortSpan(f'{rsvDay} 13:30:00', f'{rsvDay} 16:30:00', resvInfo)
                    sT2, eT2 = sortSpan(f'{rsvDay} 18:30:00', f'{rsvDay} 21:30:00', resvInfo)
                    # temp1[开始时间,结束时间,时间间隔]
                    tmp1 = optimalSpan(sT1, eT1)
                    tmp2 = optimalSpan(sT2, eT2)

                    # 如果temp1的间隔比较大
                    if tmp1[2] > tmp2[2]:
                        if tmp1[2] > optimal[0][2]:
                            optimal = [tmp1, i['devId']]  # 获取的最大时间间隔 以及研讨室的名称
                            minUser = i['minUser']
                    else:
                        if tmp2[2] > optimal[0][2]:
                            optimal = [tmp2, i['devId']]  # 获取的最大时间间隔 以及研讨室的名称
                            minUser = i['minUser']
        else:
            '''其他星期'''
            for i in data['data']:
                # 先分隔时间段并排序start和end
                if i["devId"] in self.RoomList.keys():
                    resvInfo = i['resvInfo']
                    # startTime         endTime
                    sT, eT = sortSpan(f'{rsvDay} 13:30:00', f'{rsvDay} 21:30:00', resvInfo)
                    tmp1 = optimalSpan(sT, eT)
                    # temp1[开始时间,结束时间,时间间隔]
                    if tmp1[2] > optimal[0][2]:
                        optimal = [tmp1, i['devId']]  # 获取的最大时间间隔 以及研讨室的名称
                        minUser = i['minUser']
        # 休息一秒再查询
        time.sleep(1)

    nowStamp = round(time.time() * 1000)

    # 如果开始时间与当前时间很接近时,推迟半小时预约
    if abs(nowStamp - optimal[0][0]) <= 450000:
        optimal[0][0] = nowStamp + 1800000

    a = ChineseTime(optimal[0][0])
    b = ChineseTime(optimal[0][1])
    tmp = [[a, b, round(optimal[0][2] / 3600000, 2)], self.RoomList[optimal[1]]]
    print('转化optimal: ', tmp, minUser)
    print(Precision_Submit(self, optimal, minUser))


'''获得某一天某个房间的预约时间预约情况'''


def Retrieve(self, date):
    params = {
        'sysKind': '1',
        'resvDates': date,
        'page': '1',
        'pageSize': '100',
        'labIds': '101497594',
        'kindId': ''
    }
    return requests.get(url=BASIC_URL + '/reserve?', headers=self.header, params=params)


'''获取AccId,拿来预约的身份码'''


def Get_Accid(self):
    url = BASIC_URL + f'/account/getMembers?key={self.XueHao}&page=1&pageNum=10'
    return requests.get(url=url, headers=self.header).json()['data'][0]['accNo']


'''时间戳delta返回小时数'''


def TS_Span(delta):
    # delta为datetime.delta类型的值  四舍五入保留两位小数点返回   返回的单位是小时
    return round(delta.days * 24 + delta.seconds / 3600, 2)


'''计算总预约时间'''


def Total_Span(data):
    tmp = DT.fromtimestamp(1684403600) - DT.fromtimestamp(1684403600)
    seminar, rseminar, seat, rseat = tmp, tmp, tmp, tmp

    for i in data:
        if '-' in i['resvDevInfoList'][0]['devName']:
            bt = DT.fromtimestamp(i['resvBeginTime'] / 1000)
            seat += DT.fromtimestamp(i['resvEndTime'] / 1000) - bt
            rseat += DT.fromtimestamp(i['resvEndRealTime'] / 1000) - bt
        else:
            bt = DT.fromtimestamp(i['resvBeginTime'] / 1000)
            seminar += DT.fromtimestamp(i['resvEndTime'] / 1000) - bt
            rseminar += DT.fromtimestamp(i['resvEndRealTime'] / 1000) - bt

    return seminar, rseminar, seat, rseat


'''时间戳转变中文格式'''


def ChineseTime(no):
    length = len(str(no))
    if length == 10:
        return DT.fromtimestamp(no).strftime('%Y-%m-%d %H:%M:%S')
    elif length == 13:
        return DT.fromtimestamp(no / 1000).strftime('%Y-%m-%d %H:%M:%S')


'''状态表'''


def status(no):
    statusDic = {
        # 1: '预约成功',
        # 256: '待审核',
        # 512: '审核未通过',
        # 1024: '审核通过',
        2: '待生效',
        4: '已生效',
        8: '未缴费',
        16: '已违约',
        32: '已缴费',
        64: '已签到',
        128: '已结束',
        2048: '已暂离',
    }
    mes = ''

    for k, v in statusDic.items():
        mes += f'{v} ' if k == (no & k) else ''

    return mes


'''计算是否有可预约时间'''


def optimalSpan(startList, endList):
    optimal = [0, 0, 0]  # [开始时间,结束时间,时间间隔]
    # 时间仍为时间戳格式
    nowStamp = round(time.time() * 1000)
    # 从结束时间列表进行遍历
    for index, i in enumerate(endList):
        # 当前时间大于某个结束时间
        if nowStamp > i:
            # 但当前时间小于当前位置的开始时间
            if nowStamp < startList[index]:
                i = nowStamp
            # 否则 跳过这一轮无意义的比较
            else:
                continue
        # 3600等于一个小时 (秒级时间戳)
        oneHour = 3600000
        # 存在大于等于2.5小时小于等于4小时的时间段哦
        if oneHour * 2.5 <= (startList[index] - i) <= oneHour * 4:
            tmp = [0, 0, 0]
            tmp[0] = i
            tmp[1] = startList[index]
            tmp[2] = tmp[1] - tmp[0]
            if optimal[2] < tmp[2]:
                optimal = tmp
        # 存在大于4小时的时间段
        elif oneHour * 4 < (startList[index] - i):
            tmp = [0, 0, 0]
            tmp[0] = i
            # 减少到3.8小时
            tmp[1] = i + oneHour * 4
            tmp[2] = tmp[1] - tmp[0]
            if optimal[2] < tmp[2]:
                optimal = tmp

    return optimal


'''对获取的时间排序'''


def sortSpan(margin_start, margin_end, time_list):
    # 把参数 格式化为date格式
    margin_start_date = DT.strptime(margin_start, '%Y%m%d %H:%M:%S')
    margin_end_date = DT.strptime(margin_end, '%Y%m%d %H:%M:%S')
    # 生成时间戳
    margin_start_stamp = int(DT.timestamp(margin_start_date)) * 1000
    margin_end_stamp = int(DT.timestamp(margin_end_date)) * 1000

    startTimes = []
    endTimes = [margin_start_stamp]

    for i in time_list:
        # 判断 该时间段是否在 限定时间段内
        if i['startTime'] >= margin_start_stamp and i['endTime'] <= margin_end_stamp:
            startTimes.append(i['startTime'])
            endTimes.append(i['endTime'])

    startTimes.append(margin_end_stamp)
    startTimes.sort()
    endTimes.sort()

    return startTimes, endTimes


'''座位dev转换'''


def calc_dev_no(no):
    temp = no.split('-')
    if 'A' not in temp[1] and 'B' not in temp[1]:
        end = int(temp[1])
    else:
        end = int(temp[1][1:])

    # 判断楼号,变换对应的值
    match temp[0]:
        case '101':
            return 101266684 + end - 1
        case '103':
            return 101267044 + end - 1
        case '202':
            if end >= 65:
                return 101267600 + end - 1
            return 100586795 + end - 1
        case '203':
            if end >= 45:
                return 101267648 + end - 1
            if end >= 41:
                return 101267194 + end - 1
            return 100586859 + end - 1
        case '204':
            if end >= 41:
                return 101267656 + end - 1
            if end >= 37:
                return 101267202 + end - 1
            return 100586899 + end - 1
        case '205':
            if end >= 33:
                return 101267544 + end - 1
            return 100586943 + end - 1
        case '206':
            if end >= 73:
                return 101267628 + end - 1
            return 100586975 + end - 1
        case '2C':
            return 101267154 + end - 1
        case '301':
            if end >= 69:
                return 101267552 + end - 1
            return 100587058 + end - 1
        case '303':
            if end >= 17:
                return 101267242 + end - 1
            return 100587126 + end - 1
        case '306':
            if end >= 65:
                return 101267704 + end - 1
            return 100589685 + end - 1
        case '307':
            return 100589749 + end - 1
        case '3A':
            if end >= 189:
                return 101267572 + end - 1
            if end >= 62:
                return 100588305 + end - 1
            return 100587336 + end - 1
        case '3C':
            if end >= 62:
                return 100588434 + end - 1
            return 100587398 + end - 1
        case '401':
            if end >= 165:
                return 101267783 + end - 1
            if end >= 69:
                return 100587459 + end - 1
            return 101267879 + end - 1
        case '402':
            if end >= 57:
                return 101267987 + end - 1
            return 100587623 + end - 1
        case '406':
            return 100587679 + end - 1
        case '417':
            if end >= 61:
                return 101268003 + end - 1
            return 100587723 + end - 1
        case '418':
            return 100587783 + end - 1
        case '4A':
            if end >= 189:
                return 101267891 + end - 1
            if end >= 62:
                return 100588494 + end - 1
            return 100587819 + end - 1
        case '4C':
            if end >= 62:
                return 100588622 + end - 1
            return 100587880 + end - 1
        case '501':
            if 'A' in temp[1]:
                return 101266289 + end - 1
            if end >= 201:
                return 101267895 + end - 1
            return 100587942 + end - 1
        case '502':
            if end >= 61:
                return 101268039 + end - 1
            if end >= 49:
                return 101266590 + end - 1
            return 100588142 + end - 1
        case '511':
            if end >= 61:
                return 101268055 + end - 1
            if 'A' in temp[1]:
                return 101266341 + end - 1
            if 'B' in temp[1]:
                return 101266406 + end - 1
            return 100588206 + end - 1
        case '513':
            return 100588869 + end - 1
        case '514':
            return 100589941 + end - 1
        case '5C':
            if end > 1:
                return 101266490 + end - 1
            return 101266489 + end - 1
        case 'M':
            if 'M301' in temp[0]:
                return 101268394 + end - 1
            return 100646438 + end - 1


'''准点等待'''


def Wait_OnTime(flag, myTime=None):
    # 座位
    if myTime is None:
        myTime = [[6, 15, 1], [6, 30, 1]]
    if flag == 1:
        tomorrow = DT.replace(DT.now(), hour=myTime[0][0], minute=myTime[0][1], second=myTime[0][2])
        print(f'等待到{tomorrow}再执行预约座位')
        time.sleep((tomorrow - DT.now()).seconds)
    # 研讨室
    elif flag == 2:
        tomorrow = DT.replace(DT.now(), hour=myTime[1][0], minute=myTime[1][1], second=myTime[1][2])
        print(f'等待到{tomorrow}再执行预约研讨室')
        time.sleep((tomorrow - DT.now()).seconds)


'''彩色打印字符串'''


def Color(s, color=None):
    a = "\033[0"
    match color:
        case 1:
            return f"{a};91m{s}{a}m"  # 红
        case 2:
            return f"{a};92m{s}{a}m"  # 绿
        case 3:
            return f"{a};93m{s}{a}m"  # 黄
        case 4:
            return f"{a};94m{s}{a}m"  # 蓝
        case 5:
            return f"{a};95m{s}{a}m"  # 紫
        case 6:
            return f"{a};96m{s}{a}m"  # 宝石色
    return f"{a};97m{s}{a}m"  # 默认高亮

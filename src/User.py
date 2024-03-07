import json

import timeout_decorator
import requests

from src.Login import Login
from src.Public import *

BASIC_URL = 'http://libbooking.gzhu.edu.cn/ic-web'
DT = datetime.datetime


class User:

    def __init__(self, config):
        # config = dict(config)
        self.WaitTime = config.get('waitTime') or [6, 15, 1]  # 定时等待
        """个人信息配置"""
        self.XueHao = config.get('account')  # 学号
        self.MiMa = config.get('password')  # 密码
        self.Id = config.get('selfAccid')  # 个人账号ID
        self.FriendId = config.get('friendAccid') or [1]
        self.FriendFlag = config.get('friendFlag') or 0
        '''座位配置'''
        self.Weekday = config.get('weekday')
        self.DevNo = config.get('devName')  # 座位
        self.DevTimeSpan = config.get('timeSpan')
        self.pushplus = config.get('pushplus')
        self.Cookie = config.get('cookie')

        if self.Cookie == '':
            logger.error('cookie.txt未填写登录信息')

        '''请求配置'''

        self.header = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'libbooking.gzhu.edu.cn',
            'Cookie': self.Cookie,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.41',
        }

    def Switch_Config(self, config):
        self.FriendFlag = config.get('friendFlag')
        self.Weekday = config.get('weekday')
        self.DevNo = config.get('devName')  # 座位
        self.DevTimeSpan = config.get('timeSpan')

    def Check_Cookie(self):
        try:
            ifValid = self.Cancel_Submit('10593406fd2049bc864a53486593b3b1').json()
            if '未登录' in ifValid['message']:
                self.Update_Cookie()
        except json.decoder.JSONDecodeError as e:
            logger.exception(f'Check_Cookie Error,{e}')

    def __str__(self):
        return f"学号:{self.XueHao}\n" \
               f"密码:*************\n" \
               f"我的Accid:{self.Id}\n" \
               f"朋友Accid:{self.FriendId}\n" \
               f"是否携带朋友:{self.FriendFlag}\n" \
               f"预约日:{self.Weekday}\n" \
               f"设备名:{self.DevNo}\n" \
               f"设备时间段:{self.DevTimeSpan}\n" \
               f"pushplus:{self.pushplus}\n" \
               f"cookie:{self.Cookie}\n"

    '''更新Cookie'''

    def Update_Cookie(self):
        # 测试此时的cookies能否可以使用
        self.Cookie = None
        count = 0
        while self.Cookie is None or len(self.Cookie) == 0:
            logger.error(f'try to log in with {count + 1}th times')
            if count > 20:
                return '多次尝试都登陆不了'
            self.Cookie = Login(self.XueHao, self.MiMa, self.pushplus).Get_LoginUrl()
            count += 1
            time.sleep(3)

        # 更新程序里的cookie
        self.header['Cookie'] = self.Cookie
        # 更新程序外的cookie
        with open('./cookie.txt', 'w') as file:
            file.write(self.Cookie)

    '''每天6点多的预约'''

    def Broadly_Submit(self, timeFlag=None):
        messages = []
        DevNo = str(self.DevNo)
        if '#' in DevNo[0]:
            rsvDay = datetime.date.today() + datetime.timedelta(days=0)  # 时间推后零天
            DevNo = DevNo.replace("#", "")
        elif '-' in DevNo:
            rsvDay = datetime.date.today() + datetime.timedelta(days=1)  # 时间推后一天
        else:
            rsvDay = datetime.date.today() + datetime.timedelta(days=3)  # 时间推后三天

        wday = int(rsvDay.weekday())  # 获取星期 例:0为星期一
        rsvDay = rsvDay.strftime('%Y-%m-%d')  # 字符串化:2023-04-11
        # 等待到规定时间再进行预约
        if timeFlag:
            Wait_OnTime(self.WaitTime)
        # 判断该天需不需要预约
        if int(self.Weekday[wday]):
            # 时间段循环
            for tSpan in self.DevTimeSpan:
                res = '解析失败'
                try:
                    info = {
                        'rsvDay': rsvDay,
                        'dev': DevNo,
                        'bt': tSpan[0],
                        'et': tSpan[1]

                    }
                    res = self.Rsv_Submit(info).json()
                    messages.append(f'{rsvDay} {DevNo} {tSpan[0]}-{tSpan[1]} {Color(res["message"], 6)}')
                except json.decoder.JSONDecodeError as e:
                    logger.exception(f'JSONDecodeError, {e}')
                    messages.append(f'{rsvDay} {DevNo} {tSpan[0]}-{tSpan[1]} {Color(res, 6)}')
        else:
            messages.append(f'{rsvDay} {DevNo}{Color(["此座位您今天不想预约"], 6)}')
        return messages

    '''精准预约发送请求函数'''

    def Rsv_Submit(self, info, minUser=2):
        url = BASIC_URL + '/reserve'

        resvMember = [self.Id]
        if self.FriendFlag:
            for i in range(minUser - 1):
                resvMember.append(self.FriendId[i])

        '''座位'''
        data = {
            "appAccNo": self.Id,
            "captcha": "",
            "memberKind": 1,
            "memo": "搞学习",
            "resvBeginTime": f"{info.get('rsvDay')} {info.get('bt')}",
            "resvDev": [calc_dev_no(info.get('dev'))],
            "resvEndTime": f"{info.get('rsvDay')} {info.get('et')}",
            "resvMember": resvMember,
            "resvProperty": 0,
            "sysKind": 8,
            "testName": "学习",
        }
        # 判断是否研讨室还是座位
        if '-' not in str(info['dev']):
            '''研讨室'''
            to_update = {
                'addServices': [],
                'appUrl': "",
                'memberKind': 2,
                'resvKind': 2,
                'sysKind': 1,
            }
            data.update(to_update)

        return requests.post(url=url, headers=self.header, json=data)

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
                'resvId': i['resvDevInfoList'][0]['resvId'],
                'devId': i['resvDevInfoList'][0]['devId'],
                'devSn': i['resvDevInfoList'][0]['devSn'],
                'uuid': i['uuid'],
                'bt': DT.fromtimestamp(bt / 1000).strftime('%Y-%m-%d %H:%M'),
                'et': DT.fromtimestamp(et / 1000).strftime('%H:%M'),
                'status': i['resvStatus']
            }
            myList.append(item)
        return myList

    '''抢预约的精准发送表单'''

    def Precision_Submit(self, optimal, minUser):
        # 判断是否有预约位置信息
        if optimal[1] == 0:
            logger.error("无预约位置信息")
            return
        # 输入数据
        rsvDay = DT.fromtimestamp(optimal[0][0] / 1000).strftime('%Y-%m-%d')  # 预约日期
        devId = optimal[1]  # 预约房间
        sT = DT.fromtimestamp(optimal[0][0] / 1000).strftime('%H:%M:%S')  # 开始时间
        eT = DT.fromtimestamp(optimal[0][1] / 1000).strftime('%H:%M:%S')  # 结束时间
        info = {
            'rsvDay': rsvDay,
            'dev': devId,
            'bt': sT,
            'et': eT
        }
        if minUser == 1:
            self.FriendFlag = 0
            res = self.Rsv_Submit(info).json()
            return f"{rsvDay}, {devId}, {sT}, {eT}, {[self.Id]}, {Color(res['message'], 6)}"
        else:
            self.FriendFlag = 1
            res = self.Rsv_Submit(info, minUser=minUser).json()
            return f"{rsvDay}, {devId}, {sT}, {eT},  {Color(res['message'], 6)}"

    '''取消某个预约'''

    def Cancel_Submit(self, uuid):
        try:
            return requests.post(url=BASIC_URL + '/reserve/delete', headers=self.header, json={'uuid': uuid},
                                 timeout=20)
        except Exception as e:
            logger.exception(e)
            exit(0)

    '''签到与暂离回来功能'''

    def Clock_In(self, devSn):
        # 判断是自习室还是研讨室
        # 自习室所需要用到的url
        login_url = BASIC_URL + '/phoneSeatReserve/login'  # 登陆
        signSeat_url = BASIC_URL + '/phoneSeatReserve/sign'  # 签到
        comeBack_url = BASIC_URL + '/phoneSeatReserve/comeback'  # 暂离返回

        login_data = {
            "devSn": devSn,
            "unionId": "o8QfLt2M2Pz0h04ArxMG6SeWdarc",
            "type": "1",
            "bind": 0,
            "loginType": 2
        }
        login_res = requests.post(url=login_url, headers=self.header, json=login_data).json()

        if login_res['data'] is None:
            logger.error("login_res['data'] 找不到")
            return "data 找不到"
        else:
            if login_res['data']['reserveInfo'] is None:
                logger.error('可能该预约还未生效,请稍后再试')
                return '可能该预约还未生效,请稍后再试'
        # 会生成一个resvId出来,通过这个resvId来进行sign和comeback
        resvId = login_res['data']['reserveInfo']['resvId']
        sign_res = requests.post(url=signSeat_url, headers=self.header, json={"resvId": resvId}).json()
        comeback_res = requests.post(url=comeBack_url, headers=self.header, json={"resvId": resvId}).json()
        return sign_res['message'] + '\t' + comeback_res['message']

        # 研讨室
        # signRoom_url = BASIC_URL + '/pad/accountByQR'  # 签到
        # data = {
        #     "szLogonName": self.XueHao,
        #     "szPassword": self.MiMa,
        #     "szCtrlSn": 1017,
        #     "timeStamp": "84d426c725b32474aa0bc5f4a4e530cb"  # 加密时间戳,就差这一步,我草,一座大山,始终跨越不了
        # }
        # # stampValid_url = fBASIC_URL+'/pad/valid?timeStamp={data["timeStamp"]}'
        #
        # return requests.post(url=signRoom_url, headers=self.header, json=data).text

    '''设置Predator定时器'''

    def Timer_Predator(self, date, seatRoom=None, marginSpan=None, keepTime=None, minHour=4):
        @timeout_decorator.timeout(keepTime)
        def do_time():
            return self.Predator(date=date, seatRoom=seatRoom, marginSpan=marginSpan, minHour=minHour)

        def do():
            return self.Predator(date=date, seatRoom=seatRoom, marginSpan=marginSpan, minHour=minHour)

        # 判断keepTime是否为0或None
        if keepTime:
            return do_time()
        else:
            return do()

    '''时刻捕获空缺的时间段'''

    def Predator(self, date, seatRoom=None, marginSpan=None, minHour=4):
        seminarFlag = True
        # 判断是座位还是研讨室
        if seatRoom:
            seminarFlag = False

        rsvDay = datetime.datetime.strptime(date, '%Y-%m-%d')
        weekday = int(rsvDay.weekday())  # 获取星期 0为星期一
        logger.info(f'预约日期: {rsvDay} 星期: {weekday + 1} 限定时间范围: {marginSpan}')
        logger.info('正在检索中,请耐心等待')

        rsvDay = rsvDay.strftime('%Y%m%d')  # 字符串化:20230411

        optimal = [[0, 0, 0], 0]  # [[开始时间,结束时间,时间间隔],房号]
        minUser = 1

        while optimal[0][2] == 0:
            # 获得所有房间的信息
            data = self.Retrieve(date=rsvDay, seatRoom=seatRoom, seminarFlag=seminarFlag).json()
            '''星期五'''
            if seminarFlag and weekday == 4:
                for i in data['data']:
                    if '-' not in i['devName'] or i['devName'] not in RoomList.values():
                        continue
                    sT1, eT1 = sortSpan(f'{rsvDay} 13:30:00', f'{rsvDay} 16:30:00', i['resvInfo'])
                    sT2, eT2 = sortSpan(f'{rsvDay} 18:30:00', f'{rsvDay} 21:30:00', i['resvInfo'])
                    # temp1[开始时间,结束时间,时间间隔]
                    tmp1 = optimalSpan(sT1, eT1, minHour)
                    tmp2 = optimalSpan(sT2, eT2, minHour)

                    # 如果temp1的间隔比较大
                    if tmp1[2] < tmp2[2]:
                        tmp1 = tmp2

                    if tmp1[2] > optimal[0][2]:
                        optimal = [tmp1, i['devName']]  # 获取的最大时间间隔 以及研讨室的名称
                        minUser = i['minUser']

            else:
                '''其他星期'''
                for i in data['data']:
                    if '-' not in i['devName'] and i['devName'] not in RoomList.values():
                        continue
                    sT, eT = sortSpan(f'{rsvDay} {i["openTimes"][-1]["openStartTime"]}:00',
                                      f'{rsvDay} {i["openTimes"][-1]["openEndTime"]}:00', i['resvInfo'])

                    tmp1 = optimalSpan(sT, eT)  # temp1[开始时间,结束时间,时间间隔]
                    marginStartStamp = tmp1[0]
                    marginEndStamp = tmp1[1]
                    if marginSpan:
                        # 把参数 格式化为date格式
                        marginStart = DT.strptime(f'{rsvDay} {marginSpan[0]}', '%Y%m%d %H:%M:%S')
                        marginEnd = DT.strptime(f'{rsvDay} {marginSpan[1]}', '%Y%m%d %H:%M:%S')
                        # 生成时间戳
                        marginStartStamp = int(DT.timestamp(marginStart)) * 1000
                        marginEndStamp = int(DT.timestamp(marginEnd)) * 1000
                    if tmp1[0] >= marginStartStamp and tmp1[1] <= marginEndStamp:
                        if tmp1[2] > optimal[0][2]:
                            optimal = [tmp1, i['devName']]  # 获取的最大时间间隔 以及研讨室的名称
                            minUser = i['minUser']
            # 休息一秒再查询
            time.sleep(1)
        nowStamp = round(time.time() * 1000)

        # 如果开始时间与当前时间很接近时,推迟15分钟预约
        if abs(nowStamp - optimal[0][0]) <= 450000:
            optimal[0][0] = nowStamp + 900000

        return self.Precision_Submit(optimal, minUser)

    '''获得某一天某个房间的预约时间预约情况'''

    def Retrieve(self, date, seatRoom=None, seminarFlag=True):

        if seminarFlag:
            # 对研讨室发起查询
            params = {
                'sysKind': '1',
                'resvDates': date,  # 20231210
                'page': '1',
                'pageSize': '100',
                'labIds': '101497594',
                'kindId': ''
            }
        else:
            # 对座位区域发起查询
            params = {
                'roomIds': 100647013 if seatRoom is None else seatRoom,  # 101 区域
                'resvDates': date,  # 20231210
                'sysKind': 8,
            }
        return requests.get(url=BASIC_URL + '/reserve?', headers=self.header, params=params)

    '''获取AccId,拿来预约的身份码'''

    def Get_Accid(self):
        url = BASIC_URL + f'/account/getMembers?key={self.XueHao}&page=1&pageNum=10'
        return requests.get(url=url, headers=self.header).json()['data'][0]['accNo']

from Schedule import *


class User:

    def __init__(self):
        """个人信息配置"""
        with open('configure.json', 'r', encoding='utf-8') as fp:
            config = json.loads(fp.read())
            self.XueHao = config['account']  # 学号
            self.MiMa = config['password']  # 密码
            self.Id = config['self_accid']  # 个人账号ID
            self.FriendId = config['friend_accid']  # 朋友ID
            self.SeatNo = config['seat']  # 座位
            self.RoomNo = config['room']  # 研讨室
            self.RsvTime_seat = RsvTime_seat
            self.RsvTime_seminar = RsvTime_seminar
            self.RoomList = RoomList
            self.pushplus = config['pushplus']

        # 更新cookie到文本里
        with open('cookie.txt', 'r', encoding='utf-8') as fp:
            self.Cookie = fp.read()
            if self.Cookie == '':
                logger.info('cookie.txt未填写登录信息')

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

    def __call__(self):

        for _ in range(100):
            try:
                ifValid = Cancel_Submit(self, '10593406fd2049bc864a53486593b3b1').json()
                if '未登录' in ifValid['message']:
                    Update_Cookie(self)
                mode = input('1--常规约丨2--抢约丨3--取消约丨4--签到丨5--我的|6--总时长|7--纠正|8--签到(实验)|9--改约|0--退出\n')

                if mode == '1':
                    message = Broadly_Submit(self)
                    for i in message:
                        print(i)
                elif mode == '2':
                    date = input('请输入日期(例:2023-6-26)\n')
                    keeptime = float(input('请输入持续搜索时间(单位/秒)|无需定时请输入0\n'))
                    Timer_Predator(self, date, keeptime)
                elif mode == '3':
                    '''显示已预约的信息,再进行选择'''
                    res = My_Reserve(self)
                    for index, i in enumerate(res):
                        tmp = f"{i['no']} \t{i['bt']}"
                        print(f"{index}\t{Color(tmp, 1)}--{i['et']}\t状态:{status(i['status'])}")
                    p = int(input('请选择序号0-20\n'))
                    today = res[p]["bt"][:10]
                    dev = res[p]["no"]
                    previous = [today, res[p]["bt"][11:], res[p]["et"], dev]
                    print('你已选中', Color(previous, 6))
                    confirm = input('1--提交|0--撤回操作\n')
                    if confirm == '1':
                        print(Cancel_Submit(self, res[p]['uuid']).json()['message'])
                    else:
                        print('已撤回')
                elif mode == '4':
                    res = My_Reserve(self)
                    for i in res:
                        # 判断是否已暂离或已生效
                        if i['status'] == 3141 or i['status'] == 1029:
                            print(i['no'], Clock_In(self, i['no']))
                    print('签到操作完成')
                elif mode == '5':
                    '''显示已预约的信息'''
                    res = My_Reserve(self)
                    for index, i in enumerate(res):
                        tmp = f"{i['no']} \t{i['bt']}"
                        print(f"{index}\t{Color(tmp, 2)}--{i['et']}\t状态:{status(i['status'])}")
                elif mode == '6':
                    r, rr, s, rs = My_Reserve(self, 1)
                    tmp = f'总计: 研讨室: {r}时(约)-{rr}时(实)   \t座位: {s}时(约)-{rs}时(实)'
                    print(Color(tmp, 6))
                    r, rr, s, rs = My_Reserve(self, 2)
                    tmp = f'本月: 研讨室: {r}时(约)-{rr}时(实)   \t座位: {s}时(约)-{rs}时(实)'
                    print(Color(tmp, 2))
                    r, rr, s, rs = My_Reserve(self, 3)
                    tmp = f'上月: 研讨室: {r}时(约)-{rr}时(实)   \t座位: {s}时(约)-{rs}时(实)'
                    print(Color(tmp, 3))
                elif mode == '7':
                    tmp = Get_Accid(self)
                    if not self.Id == tmp:
                        self.Id = tmp
                        with open('configure.json', 'r', encoding='utf-8') as fp:
                            tmp_config = json.loads(fp.read())
                            tmp_config['self_accid'] = tmp
                        with open('configure.json', 'w', encoding='utf-8') as fp:
                            fp.write(json.dumps(tmp_config))
                    print('纠正完毕')
                elif mode == '8':
                    print(Clock_In(self, '研讨间E13'))
                elif mode == '9':
                    Rescheduling(self)
                elif mode == '0':
                    exit(0)
                else:
                    print('输入错误')
            except Exception:
                logger.error(traceback.format_exc())


if __name__ == "__main__":
    User()()

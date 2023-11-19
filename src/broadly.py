from Schedule import *


class User:

    def __init__(self, myTime=None):
        """个人信息配置"""
        self.myTime = myTime if myTime else [[6, 15, 1], [6, 30, 1]]
        
        self.RsvTime_seat = RsvTime_seat
        self.RsvTime_seminar = RsvTime_seminar
        self.RoomList = RoomList
        with open('configure.json', 'r', encoding='utf-8') as fp:
            config = json.loads(fp.read())
            
            self.XueHao = config['account']  # 学号
            self.MiMa = config['password']  # 密码
            self.Id = config['self_accid']  # 个人账号ID
            self.FriendId = config['friend_accid']  # 朋友ID
            self.SeatNo = config['seat']  # 座位
            self.RoomNo = config['room']  # 研讨室
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

    '''自身函数'''

    def __call__(self):
        try:
            ifValid = Cancel_Submit(self, '10593406fd2049bc864a53486593b3b1').json()
            if '未登录' in ifValid['message']:
                Update_Cookie(self)
            message = Broadly_Submit(self, reps=2, timeFlag=1, randomFlag=1)
            for i in message:
                print(i)
        except Exception:
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    User()()

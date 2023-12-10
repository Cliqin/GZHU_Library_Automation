from loguru import logger
import traceback
import json
import threading

from src.SeatRoom import SeatRoom
from src.Public import *
from src.User import User


def MyConfig():
    # 获取本地用户配置
    with open('./userInfo.json', 'r', encoding='utf-8') as fp:
        myConfig = json.loads(fp.read())
        # 转成字典
        myConfig = dict(myConfig)
    # 获取本地cookie
    with open('./cookie.txt', 'r', encoding='utf-8') as fp:
        myConfig['cookie'] = fp.read()
    return myConfig


def MyUser(config=None):
    if config is None:
        myConfig = MyConfig()
    else:
        myConfig = config
    # 创建实例(还暂时没有预约信息)
    myUser = User(config=myConfig)
    # 检查登陆状态
    myUser.Check_Cookie()
    # 获取本地cookie
    with open('./cookie.txt', 'r', encoding='utf-8') as fp:
        myConfig['cookie'] = fp.read()

    return myUser, myConfig


def MyReserveThread(config, item, timeFlag=None):
    config.update(item)
    user, config = MyUser(config)
    msgs = user.Broadly_Submit(timeFlag=timeFlag)
    # 输出信息
    for i in msgs:
        print(i)


def Clock():
    user, config = MyUser()
    res = user.My_Reserve()
    for i in res:
        # 判断是否已暂离或已生效
        if i['status'] == 3141 or i['status'] == 1029:
            print(i['no'], user.Clock_In(i['devSn']))
    print('签到操作完成')


class Shell:
    def __init__(self, mySchedule):
        self.mySchedule = mySchedule

    def __call__(self, *args, **kwargs):
        # 返回一个更新好cookie的user和config
        user, config = MyUser()

        try:
            for _ in range(100):
                mode = input(
                    '1--常规约 丨 2--抢约 丨 3--取消约 | 4--改约 丨 5--签到 丨 6--我的预约 | 7--总时长 | 8--更新身份 | 9--查看配置 | 0--退出 \n')
                # 每次循环都检查一次登陆状态
                user.Check_Cookie()

                if mode == '1':
                    sub_mode = input("1--遍历schedule | 2--指定约\n")
                    if sub_mode == '1':
                        # 导入预约信息
                        for item in self.mySchedule:
                            config.update(item)
                            user.Switch_Config(config=config)
                            msgs = user.Broadly_Submit(timeFlag=0)
                            for i in msgs:
                                print(i)
                    elif sub_mode == '2':
                        info = {}

                        dayDelta = int(input("0--今天 | 1--明天 | 2--后天\n"))
                        rsvDay = datetime.date.today() + datetime.timedelta(days=dayDelta)  # 时间推后一天

                        info['date'] = rsvDay.strftime('%Y-%m-%d')  # 字符串化:2023-04-11
                        info['dev'] = input("请输入设备名字 例: 101-001 | 研讨间E09\n")
                        # 前头自动补零操作: 补两个零
                        info['bt'] = str('%02d' % int(input('请输入开始小时:\t'))) + ":"
                        info['bt'] += str('%02d' % int(input('请输入开始分钟:\t'))) + ":00"
                        info['et'] = str('%02d' % int(input('请输入结束小时:\t'))) + ":"
                        info['et'] += str('%02d' % int(input('请输入结束分钟:\t'))) + ":00"
                        polish = [info['date'], info['dev'], info['bt'], info['et']]
                        print('请确认', Color(polish, 6))
                        confirm = input('1--提交|0--撤回操作\n')
                        if confirm == '1':
                            res = user.Rsv_Submit(info['date'], info['dev'], info['bt'], info['et']).json()
                            print(Color(res["message"], 6))
                        else:
                            print('已撤回')

                elif mode == '2':
                    date = input('请输入日期(例:2023-6-26)\n')
                    date = date if len(date) else "2023-12-10"

                    index = input("如果是座位,请输入座位所在楼层(回车默认选研讨间)\n")
                    index = int(index) - 1 if len(index) else None

                    marginSpan = None
                    seatRoom = None
                    if index >= 0:
                        for i, v in enumerate(SeatRoom[index]["children"]):
                            print(i, v['name'], v['id'])

                        seatRoom = SeatRoom[index]["children"][int(input("请继续选择\n"))]['id']

                        marginStart = input("输入所抢时段\n开始时段(例13:00)回车默认不做限制\t")
                        marginEnd = input("\n输入所抢时段\n结束小时(14:00)回车默认不做限制\t")

                        marginSpan = [marginStart + ":00", marginEnd + ":00"] if len(marginStart) or len(
                            marginEnd) else None

                    keepTime = input('\n请输入持续搜索时间(单位/秒)|无需定时请输入0\n')
                    keepTime = float(keepTime) if len(keepTime) else 0
                    user.Timer_Predator(date=date, seatRoom=seatRoom, marginSpan=marginSpan, keepTime=keepTime)
                elif mode == '3':
                    '''显示已预约的信息,再进行选择'''
                    res = user.My_Reserve()
                    for index, i in enumerate(res):
                        tmp = f"{i['no']} \t{i['bt']}"
                        print(f"{index}\t{Color(tmp, 1)}--{i['et']}\t状态:{status(i['status'])}")
                    p = int(input('请选择序号0-20\n'))

                    selected = f'{res[p]["no"]} {res[p]["bt"][:10]} {res[p]["bt"][11:]}--{res[p]["et"]}'
                    print('你已选中', p, Color(selected, 6))

                    confirm = input('1--提交|0--撤回操作\n')
                    if confirm == '1':
                        print(user.Cancel_Submit(res[p]['uuid']).json()['message'])
                    else:
                        print('已撤回')
                elif mode == '4':
                    user.Rescheduling()
                elif mode == '5':
                    res = user.My_Reserve()
                    for i in res:
                        # 判断是否已暂离或已生效
                        if i['status'] == 3141 or i['status'] == 1029:
                            print(i['no'], user.Clock_In(i['devSn']))
                    print('签到操作完成')
                elif mode == '6':
                    '''显示已预约的信息'''
                    res = user.My_Reserve()
                    for index, i in enumerate(res):
                        tmp = f"{i['no']} \t{i['bt']}"
                        print(f"{index}\t{Color(tmp, 2)}--{i['et']}\t状态:{status(i['status'])}")
                elif mode == '7':
                    r, rr, s, rs = user.My_Reserve(1)
                    tmp = f'总计: 研讨室: {r}时(约)-{rr}时(实)   \t座位: {s}时(约)-{rs}时(实)'
                    print(Color(tmp, 6))
                    r, rr, s, rs = user.My_Reserve(2)
                    tmp = f'本月: 研讨室: {r}时(约)-{rr}时(实)   \t座位: {s}时(约)-{rs}时(实)'
                    print(Color(tmp, 2))
                    r, rr, s, rs = user.My_Reserve(3)
                    tmp = f'上月: 研讨室: {r}时(约)-{rr}时(实)   \t座位: {s}时(约)-{rs}时(实)'
                    print(Color(tmp, 3))
                elif mode == '8':
                    tmp_Id = user.Get_Accid()
                    if not user.Id == tmp_Id:
                        # 更新程序里的
                        user.Id = tmp_Id
                        # 更新程序外的
                        with open('./userInfo.json', 'r', encoding='utf-8') as fp:
                            tmp_config = json.loads(fp.read())
                            tmp_config['selfAccid'] = tmp_Id
                        with open('./userInfo.json', 'w', encoding='utf-8') as fp:
                            fp.write(json.dumps(tmp_config))
                        print('更新完毕', user.Id)
                    else:
                        print('无需更新')
                elif mode == '9':
                    print(user)
                    # print(user.Clock_In('研讨间E13'))
                elif mode == '0':
                    exit(0)
                else:
                    print('输入错误')
        except Exception:
            logger.error(traceback.format_exc())

    def Reserve(self):
        # 返回一个config
        config = MyConfig()
        # 导入预约信息
        threads = []
        # 开启多线程预约
        for item in self.mySchedule:
            # 传入等待时间参数
            thread = threading.Thread(target=MyReserveThread, args=(config, item, 1))
            threads.append(thread)

        [thread.start() for thread in threads]
        [thread.join() for thread in threads]
        print("All threads are done")

from loguru import logger
import traceback
import json
import threading

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
            print(i['no'], user.Clock_In(i['no']))
    print('签到操作完成')


class Shell:
    def __init__(self, mySchedule):
        self.mySchedule = mySchedule

    def __call__(self, *args, **kwargs):
        # 返回一个更新好cookie的user和config(可以在这里开线程)
        user, config = MyUser()

        try:
            for _ in range(100):
                mode = input('1--常规约丨2--抢约丨3--取消约丨4--签到丨5--我的预约|6--总时长|7--更新身份|8--查看配置|9--改约|0--退出\n')
                # 每次循环都检查一次登陆状态
                user.Check_Cookie()

                if mode == '1':
                    # 导入预约信息
                    for item in self.mySchedule:
                        config.update(item)
                        user.Switch_Config(config=config)
                        msgs = user.Broadly_Submit(timeFlag=0)
                        for i in msgs:
                            print(i)
                elif mode == '2':
                    date = input('请输入日期(例:2023-6-26)\n')
                    keeptime = float(input('请输入持续搜索时间(单位/秒)|无需定时请输入0\n'))
                    user.Timer_Predator(date, keeptime)
                elif mode == '3':
                    '''显示已预约的信息,再进行选择'''
                    res = user.My_Reserve()
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
                        print(user.Cancel_Submit(res[p]['uuid']).json()['message'])
                    else:
                        print('已撤回')
                elif mode == '4':
                    res = user.My_Reserve()
                    for i in res:
                        # 判断是否已暂离或已生效
                        if i['status'] == 3141 or i['status'] == 1029:
                            print(i['no'], user.Clock_In(i['no']))
                    print('签到操作完成')
                elif mode == '5':
                    '''显示已预约的信息'''
                    res = user.My_Reserve()
                    for index, i in enumerate(res):
                        tmp = f"{i['no']} \t{i['bt']}"
                        print(f"{index}\t{Color(tmp, 2)}--{i['et']}\t状态:{status(i['status'])}")
                elif mode == '6':
                    r, rr, s, rs = user.My_Reserve(1)
                    tmp = f'总计: 研讨室: {r}时(约)-{rr}时(实)   \t座位: {s}时(约)-{rs}时(实)'
                    print(Color(tmp, 6))
                    r, rr, s, rs = user.My_Reserve(2)
                    tmp = f'本月: 研讨室: {r}时(约)-{rr}时(实)   \t座位: {s}时(约)-{rs}时(实)'
                    print(Color(tmp, 2))
                    r, rr, s, rs = user.My_Reserve(3)
                    tmp = f'上月: 研讨室: {r}时(约)-{rr}时(实)   \t座位: {s}时(约)-{rs}时(实)'
                    print(Color(tmp, 3))
                elif mode == '7':
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
                elif mode == '8':
                    print(user)
                    # print(user.Clock_In('研讨间E13'))
                elif mode == '9':
                    user.Rescheduling()
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
        for item in self.mySchedule:
            thread = threading.Thread(target=MyReserveThread, args=(config, item, 1))
            threads.append(thread)

        [thread.start() for thread in threads]
        [thread.join() for thread in threads]
        print("All threads are done")

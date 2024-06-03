import datetime
from datetime import timedelta
import time
from loguru import logger

BASIC_URL = 'http://libbooking.gzhu.edu.cn/ic-web'
DT = datetime.datetime
RoomList = {
    101266675: '低音研讨室C03',
    101266676: '低音研讨室C04',
    101266677: '低音研讨室C05',
    101266678: '低音研讨室C06',
    101266658: '研讨间E05',
    101266659: '研讨间E07',
    101266653: '研讨间E08',
    101266660: '研讨间E09',
    101266670: '研讨间E10',
    101266661: '研讨间E11',
    101266669: '研讨间E12',
    101266662: '研讨间E13',
    101266668: '研讨间E14',
    101266663: '研讨间E15',
    101266664: '研讨间E17',
    101266665: '研讨间E18',
    101266655: '学习室E21',
    101266672: '学习室E23',
    101266673: '学习室E24',
    101266674: '学习室E25',
}
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
        2: '待生效',
        4: '已生效',
        8: '未缴费',
        16: '已违约',
        32: '已缴费',
        64: '已签到',
        128: '已结束',
        # 256: '待审核',
        # 512: '审核未通过',
        # 1024: '审核通过',
        2048: '已暂离',
    }
    mes = ''

    for k, v in statusDic.items():
        mes += f'{v} ' if k == (no & k) else ''

    return mes


'''计算是否有可预约时间'''


def optimalSpan(startList, endList, minHour=4):
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
        # 3600000等于一个小时 (秒级时间戳)
        oneHour = 3600000
        # 存在大于等于2.5小时小于等于4小时的时间段哦
        if oneHour * minHour <= (startList[index] - i) <= oneHour * 4:
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


def calc_dev_no(devName):
    # 这是转换研讨室的
    if '-' not in devName:
        for key, value in RoomList.items():
            if value == devName:
                return key

    # 以下都是转换座位的
    temp = devName.split('-')
    if temp[0] == devName:
        logger.error(f"您的预约设备号有误---{devName}")
        exit(0)
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


def Wait_OnTime(myWaitTime=None):
    # 座位
    if myWaitTime is None:
        myWaitTime = [6, 15, 1]

    tomorrow = DT.replace(DT.now(), hour=myWaitTime[0], minute=myWaitTime[1], second=myWaitTime[2], microsecond=500000)
    print(f'等待到{tomorrow}再执行预约')
    time.sleep(abs((tomorrow - DT.now()).total_seconds()))


# def Wait_OnTime(myWaitTime=None):
#     # 默认等待时间为当天的6:15:01
#     if myWaitTime is None:
#         myWaitTime = [6, 15, 1]
#
#     # 获取当前时间
#     now = DT.now()
#
#     # 设定目标时间为当天的指定时间
#     target_time = now.replace(hour=myWaitTime[0], minute=myWaitTime[1], second=myWaitTime[2], microsecond=0)
#
#     # 如果目标时间已经过去，设定为次日同一时间
#     # if target_time <= now:
#     #     target_time += timedelta(days=1)
#
#     print(f'当前时间: {now}')
#     print(f'等待到 {target_time} 再执行预约')
#
#     # 计算需要等待的总秒数
#     total_sleep_seconds = (target_time - now).total_seconds()
#
#     # 等待直到接近目标时间
#     while True:
#         now = DT.now()
#         if now >= target_time:
#             break
#         sleep_duration = (target_time - now).total_seconds()
#         # 如果剩余时间大于0.1秒，分阶段睡眠
#         if sleep_duration > 0.1:
#             time.sleep(0.1)
#         else:
#             time.sleep(sleep_duration)
#             break
#
#     # 打印达到目标时间的实际时间
#     print(f'达到时间: {DT.now()}')


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

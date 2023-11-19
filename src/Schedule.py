from Public import *

# 钻空子的信息
RoomList = {
    101266675: '低音研讨室C03',
    101266676: '低音研讨室C04',
    101266677: '低音研讨室C05',
    101266678: '低音研讨室C06',
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

# 座位
RsvTime_seat = [
    [['10:00:00', '14:00:00'], ['14:00:00', '17:30:00'], ['17:30:00', '21:30:00']],  # 一   6.26
    [['10:00:00', '14:00:00'], ['14:00:00', '17:30:00'], ['17:30:00', '21:30:00']],  # 二   6.27
    [['10:00:00', '14:00:00'], ['14:00:00', '17:30:00'], ['17:30:00', '21:30:00']],  # 三   6.21
    [['10:00:00', '14:00:00'], ['14:00:00', '17:30:00'], ['17:30:00', '21:30:00']],  # 四   6.22
    [['10:00:00', '14:00:00'], ['14:00:00', '17:30:00'], ['17:30:00', '21:30:00']],  # 五   6.23
    [['10:00:00', '14:00:00'], ['14:00:00', '17:30:00'], ['17:30:00', '21:30:00']],  # 六   6.24
    [['10:00:00', '14:00:00'], ['14:00:00', '17:30:00'], ['17:30:00', '21:30:00']],  # 日   6.25
]
# RsvTime_seat = [[], [], [], [], [], [], []]
# 研讨室
RsvTime_seminar = [
    [['14:00:00', '17:30:00']],  # 星期一   9.11
    [['14:00:00', '17:30:00'], ['17:30:00', '21:30:00']],  # 星期二   9.5
    [['9:00:00', '12:00:00'], ['18:00:00', '21:30:00']],  # 星期三   9.6
    [['9:00:00', '12:00:00'], ['18:00:00', '21:30:00']],  # 星期四   9.7
    [['14:00:00', '16:30:00'], ['18:30:00', '21:30:00']],  # 星期五   9.8
    [['9:00:00', '12:00:00'], ['14:00:00', '17:30:00'], ['17:30:00', '21:30:00']],  # 星期六   9.9
    [['9:00:00', '12:00:00'], ['14:00:00', '17:30:00'], ['17:30:00', '21:30:00']],  # 星期日   9.10
]

# 座位的信息 第十周修改
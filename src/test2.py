import time
import datetime
import random

# for t in range(100):
#     # for j in range(100):
#     print(f"{t}  \033[1;{t}m" + "这个字会变色" + f"\033[0m")

# 获取当前时间
a = datetime.datetime.now().timestamp()
print(a)
# 16815558000
# 把时间戳转化为时间
b = datetime.datetime.fromtimestamp(1698570606).strftime('%Y-%m-%d %H:%M:%S')
print(b)
# 获取时间戳  (秒级时间戳)
now = datetime.datetime.today()
t1 = now.strftime('%Y-%m-01')
t2 = now + datetime.timedelta(days=31)

# 指定一个时间生成时间戳
tmp1 = datetime.datetime.strptime('2023-06-15', '%Y-%m-%d')
print(tmp1.weekday()+1)
stamp1 = datetime.datetime.timestamp(tmp1)

# print(str(c).split(".")[0])
# print(str(stamp1).split(".")[0])
# print((stamp2 - stamp1))


t = time.time()
# print(t)  # 原始时间数据
# print(int(t))  # 秒级时间戳
# print(int(round(t * 1000)))  # 毫秒级时间戳
# print(int(round(t * 1000000)))  # 微秒级时间戳

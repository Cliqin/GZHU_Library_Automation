from lxml import etree
from urllib.parse import unquote
import re
import httpx
from loguru import logger
import requests

from src.rsa import RSA

BASIC_URL = 'http://libbooking.gzhu.edu.cn/ic-web'


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

            tmp_url = str(re.findall('service=(.*)', login_url)[0])
            # 从unicode转成utf-8
            tmp_url = unquote(tmp_url)
            location_res = self.rr.get(url=f"{tmp_url}?ticket={ticket}")

            # 获得location unitoken uuid 参数
            location = location_res.headers.get('Location')
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

# --*-- coding:utf-8 ---*---

import sys
import json
import requests
import math
import StringIO
import gzip
import rsa
import uuid
import time
import logging
import datetime


reload(sys)
sys.setdefaultencoding('utf8')


UUID = str(uuid.uuid1())
PUBLIC_KEY_FILE = './api_pub.key'
LOG_FILE = "/tmp/baidu_tongji_report.log"


ACCOUNT_TYPE = '1'                        # 百度统计的账号类型：ZhanZhang:1, FengChao:2, Union:3, Columbus:4
USER_NAME = 'xxxxxxxxx'                   # 百度统计的用户名
PASS_WORD = 'xxxxxxxxxxxxxxxxxx'          # 百度统计的密码
TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxxxxx'     # 百度统计的Token


API_URL = 'https://api.baidu.com/json/tongji/v1/ReportService'                  # 百度统计的查询接口
LOGIN_URL = 'https://api.baidu.com/sem/common/HolmesLoginService'               # 百度统计的登录接口
SC_URL = 'https://sc.ftqq.com/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.send'        # Server酱的消息接口


def encrypt(data):
    # 加载公钥
    with open(PUBLIC_KEY_FILE) as publickfile:
        p = publickfile.read()
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(p)

    # 用公钥加密
    n = int(math.ceil(len(data) * 1.0 / 117))
    ret = ''
    for i in range(n):
        gzdata = data[i * 117:(i + 1) * 117]
        ret += rsa.encrypt(gzdata, pubkey)
    return ret


# 解压gzip
def gzdecode(data):
    f = StringIO.StringIO(data)
    gziper = gzip.GzipFile(fileobj=f, compresslevel=9)
    data2 = gziper.read()
    gziper.close()
    return data2


# 压缩gzip
def gzencode(data):
    f = StringIO.StringIO()
    gziper = gzip.GzipFile(fileobj=f, mode='wb', compresslevel=9, )
    gziper.write(data)
    gziper.close()
    return f.getvalue()


# 日期解析器
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


# 发送消息
def sendMessage(title, content):
    data = {'text': title, 'desp': content}
    response = requests.get(SC_URL, params=data)
    return response.content


class BaiduTongji(object):
    ucid = None
    st = None

    def __init__(self, username, password, token):
        self.username = username
        self.password = password
        self.token = token

        # login
        # self.prelogin()
        ret = self.dologin()
        self.ucid = str(ret['ucid'])
        self.st = ret['st']

    def prelogin(self):
        data = {'username': self.username,
                'token': self.token,
                'functionName': 'preLogin',
                'uuid': UUID,
                'request': {'osVersion': 'windows', 'deviceType': 'pc', 'clientVersion': '1.0'},
                }

        headers = {'UUID': UUID, 'account_type': ACCOUNT_TYPE,
                   'Content-Type': 'data/gzencode and rsa public encrypt;charset=UTF-8'
                   }

        # 压缩
        post_data = gzencode(json.dumps(data))
        # 加密
        post_data = encrypt(post_data)

        resp = requests.post(LOGIN_URL, data=post_data, headers=headers)
        ret = json.loads(gzdecode(resp.content[8:]))
        print 'prelogin:', ret

    def dologin(self):
        data = {'username': self.username,
                'token': self.token,
                'functionName': 'doLogin',
                'uuid': UUID,
                'request': {'password': self.password}
                }

        headers = {'UUID': UUID, 'account_type': ACCOUNT_TYPE,
                   'Content-Type': 'data/gzencode and rsa public encrypt;charset=UTF-8'
                   }

        # 压缩
        post_data = gzencode(json.dumps(data))
        # 加密
        post_data = encrypt(post_data)
        # post
        resp = requests.post(LOGIN_URL, data=post_data, headers=headers)
        ret = json.loads(gzdecode(resp.content[8:]))
        if ret['retcode'] == 0:
            print u'dologin:', ret['retmsg'], ' ucid:', ret['ucid'], ' st:', ret['st']
        return ret

    def dologout(self):
        data = {'username': self.username,
                'token': self.token,
                'functionName': 'doLogout',
                'uuid': UUID,
                'request': {'ucid': self.ucid, 'st': self.st, }
                }

        headers = {'UUID': UUID, 'account_type': ACCOUNT_TYPE,
                   'Content-Type': 'data/gzencode and rsa public encrypt;charset=UTF-8'
                   }

        # 压缩
        post_data = gzencode(json.dumps(data))
        # 加密
        post_data = encrypt(post_data)
        # post
        resp = requests.post(LOGIN_URL, data=post_data, headers=headers)
        ret = json.loads(gzdecode(resp.content[8:]))
        print 'logout:', ret['retmsg']

    def getsitelist(self):
        url = API_URL + '/getSiteList'
        headers = {'UUID': UUID, 'USERID': self.ucid, 'Content-Type': 'data/json;charset=UTF-8'}
        data = {'header': {'username': self.username, 'password': self.st, 'token': self.token,
                           'account_type': ACCOUNT_TYPE, },
                'body': None, }
        post_data = json.dumps(data)
        resp = requests.post(url, data=post_data, headers=headers)
        # print resp.json()
        return resp.json()['body']['data'][0]['list']

    def getdata(self, para):
        url = API_URL + '/getData'
        headers = {'UUID': UUID, 'USERID': self.ucid, 'Content-Type': 'data/json;charset=UTF-8'}
        data = {'header': {'username': self.username, 'password': self.st, 'token': self.token,
                           'account_type': ACCOUNT_TYPE, },
                'body': para, }

        post_data = json.dumps(data, cls=DateEncoder)
        resp = requests.post(url, data=post_data, headers=headers)
        # print resp.json()
        return resp.json()['body']


'''
        # 地域分布报告 visit/district/a
                                        # pv_count (浏览量(PV))
                                        # pv_ratio (浏览量占比，%)
                                        # visit_count (访问次数)
                                        # visitor_count (访客数(UV))
                                        # new_visitor_count (新访客数)
                                        # new_visitor_ratio (新访客比率，%)
                                        # ip_count (IP 数)
                                        # bounce_ratio (跳出率，%)
                                        # avg_visit_time (平均访问时长，秒)
                                        # avg_visit_pages (平均访问页数)
                                        # trans_count (转化次数)
                                        # trans_ratio (转化率，%)
        # 网站概况 overview/getTimeTrendRpt
                                        # pv_count (浏览量(PV))
                                        # visitor_count (访客数(UV))
                                        # ip_count (IP 数)
                                        # bounce_ratio (跳出率，%)
                                        # avg_visit_time (平均访问时长，秒)
        # 趋势分析 trend/time/a
                                        # pv_count (浏览量(PV))
                                        # pv_ratio (浏览量占比，%)
                                        # visit_count (访问次数)
                                        # visitor_count (访客数(UV))
                                        # new_visitor_count (新访客数)
                                        # new_visitor_ratio (新访客比率，%)
                                        # ip_count (IP 数)
                                        # bounce_ratio (跳出率，%)
                                        # avg_visit_time (平均访问时长，秒)
                                        # avg_visit_pages (平均访问页数)
                                        # trans_count (转化次数)
                                        # trans_ratio (转化率，%)
                                        # avg_trans_cost (平均转化成本，元)
                                        # income (收益，元)
                                        # profit (利润，元)
                                        # roi (投资回报率，%)



'''


'''
        # Http 请求参数
                            para = {
                                    'site_id': site_id,  # 站点ID
                                    'method': 'trend/time/a',  # 趋势分析报告
                                    'start_date': '20170316',  # 所查询数据的起始日期
                                    'end_date': '20170320',  # 所查询数据的结束日期
                                    'metrics': 'pv_count,visitor_count',  # 所查询指标为PV和UV
                                    'max_results': '0',  # 返回所有条数
                                    'gran': 'day',  # 按天粒度  day/hour/week/month
                                    }
'''


# 查询网站概况的统计数据
def queryOverviewData():
    bdtj = BaiduTongji(USER_NAME, PASS_WORD, TOKEN)
    sites = bdtj.getsitelist()
    site_id = sites[0]['site_id']

    today = ''.join(time.strftime("%Y-%m-%d", time.localtime()))
    yesterday = datetime.date.today() + datetime.timedelta(-1)
    para = {'site_id': site_id,
            'method': 'overview/getTimeTrendRpt',
            'start_date': yesterday,
            'end_date': today,
            'metrics': 'pv_count,visitor_count,ip_count,bounce_ratio,avg_visit_time',
            'max_results': '0',
            'gran': 'day',
            }

    # 查询数据
    data = bdtj.getdata(para)
    # print json.dumps(data['data'][0]['result']['items'], indent=4)

    # 日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename=LOG_FILE)

    # 打印查询结果
    logging.info(json.dumps(data['data'][0]['result']['items']))

    # 今日数据
    today_data = data['data'][0]['result']['items'][1][1]
    today_date = json.dumps(data['data'][0]['result']['items'][0][1])[7:-2].replace('/','-')

    # 昨日数据
    yesterday_data = data['data'][0]['result']['items'][1][0]
    yesterday_date = json.dumps(data['data'][0]['result']['items'][0][0])[7:-2].replace('/','-')

    # 数据格式化
    str_format = ''.join((
            '<form>'
            '  <table>',
            '   <tr>',
            '    <th>统计日期</th>',
            '      <th>今天（{today_date}）</th>',
            '      <th>昨天（{yesterday_date}）</th>',
            '   </tr>\n',
            '   <tr>',
            '      <td>浏览量（PV）</td>',
            '      <td>{today_pv_count}          </td>',
            '      <td>{yesterday_pv_count}</td>',
            '   </tr>\n\n',
            '   <tr>',
            '      <td>访客数（UV）</td>',
            '      <td>{today_visitor_count}          </td>',
            '      <td>{yesterday_visitor_count}</td>',
            '   </tr>\n\n',
            '   <tr>',
            '      <td>IP数       </td>',
            '      <td>{today_ip_count}          </td>',
            '      <td>{yesterday_ip_count}</td>',
            '   </tr>\n\n',
            '   <tr>',
            '      <td>跳出率    </td>',
            '      <td>{today_bounce_ratio}%       </td>',
            '      <td>{yesterday_bounce_ratio}%</td>',
            '   </tr>\n\n',
            '   <tr>',
            '      <td>平均访问时长</td>',
            '      <td>{today_avg_visit_minute}:{today_avg_visit_second}        </td>',
            '      <td>{yesterday_avg_visit_minute}:{yesterday_avg_visit_second}</td>',
            '   </tr>',
            '  </table>',
            '</form>'))

    report = str_format.format(
            today_date=today_date,
            today_pv_count=today_data[0],
            today_visitor_count=today_data[1],
            today_ip_count=today_data[2],
            today_bounce_ratio=today_data[3],
            today_avg_visit_minute=today_data[4]/60,
            today_avg_visit_second=today_data[4] % 60,
            yesterday_date=yesterday_date,
            yesterday_pv_count=yesterday_data[0],
            yesterday_visitor_count=yesterday_data[1],
            yesterday_ip_count=yesterday_data[2],
            yesterday_bounce_ratio=yesterday_data[3],
            yesterday_avg_visit_minute=yesterday_data[4]/60,
            yesterday_avg_visit_second=yesterday_data[4] % 60)

        # 发送消息
        title = ''.join(('百度统计报表（', time.strftime("%m-%d %H:%M", time.localtime()), '）'))
        msgResp = sendMessage(title, report)
        msgResult = json.loads(msgResp)
        if msgResult['errno'] == 0:
            logging.info('message send successed!')
        else:
            logging.error(''.join(('message send faild: ', msgResult)))

if __name__ == '__main__':

    queryOverviewData()


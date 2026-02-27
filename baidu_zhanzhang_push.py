# -*- coding: utf-8 -*-

import re
import logging
import subprocess
from io import StringIO
from urllib import request

# 站点域名
domain = 'www.example.com'

# 在百度站长申请的推送用的准入密钥
token = 'xxxxxxxxxxxxxxxxx'

# 站点地图的URL
site_map_url = 'https://www.example.com/sitemap.xml'

# 最大的链接推送数量
push_max_lines = 1000

# 推送的URL链接文件
push_urls_file = "/tmp/baidu_zhanzhang_push_url.txt"

# 数据推送的接口
push_url = 'http://data.zz.baidu.com/urls?site={domain}&token={token}'.format(domain=domain, token=token)

# 日志文件
log_file = "/tmp/baidu/baidu_zhanzhang_push.log"

def regexpMatchUrl(content):
    pattern = re.findall(r'(http|https):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?', content, re.IGNORECASE)
    if pattern:
        return True
    else:
        return False

def regexpMatchWebSite(content):
    pattern = re.findall(r''.join(domain), content, re.IGNORECASE)
    if pattern:
        return True
    else:
        return False

def getUrl(content):
    pattern = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+.html', content, re.IGNORECASE)
    if pattern:
        return pattern[0]
    else:
        return ''

def createUrlFile(url_file_path, max_lines):
    content = request.urlopen(site_map_url).read().decode('utf8')
    website_map_file = StringIO(content)
    url_file = open(url_file_path, 'w')
    index = 0
    for line in website_map_file:
        if(regexpMatchUrl(line) and regexpMatchWebSite(line)):
            url = getUrl(line)
            if(url != ''):
                index = index + 1
                url_file.writelines(url + "\n")
                if(index >= max_lines):
                    break
    url_file.close()
    website_map_file.close()

def pushUrlFile(url, url_file_path, log_file):
    shell_cmd_line = "curl -H 'Content-Type:text/plain' --data-binary @" + url_file_path + " " + '\"' + url + '\"'
    (status, output) = subprocess.getstatusoutput(shell_cmd_line)
    logging.info(output + "\n")
    # print(shell_cmd_line)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename=log_file)
    createUrlFile(push_urls_file, push_max_lines)
    pushUrlFile(push_url, push_urls_file, log_file)


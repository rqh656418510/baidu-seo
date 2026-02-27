# -*- coding: utf-8 -*-

import re
import os
import logging
import subprocess
from io import StringIO
from urllib import request

# 站点域名
domain = 'www.example.com'

# 搜索资源平台申请的唯一识别ID
app_id = 'xxxxxxxxxxxxxxxxx'

# 搜索资源平台申请的提交用的准入密钥
token = 'xxxxxxxxxxxxxxxxxxxxxx'

# 站点地图的URL
site_map_url = 'https://www.example.com/sitemap.xml'

# 最大的提交数量（天级收录配额）
day_submit_max_lines = 10

# 提交链接的接口
day_submit_url = 'http://data.zz.baidu.com/urls?appid={app_id}&token={token}&type=realtime'.format(app_id=app_id, token=token)

# 提交的URL链接文件
day_submit_urls_file = "/tmp/baidu_xiongzhang_day_submit_url.txt"

# 记录历史提交位置的索引文件（索引从一开始）
day_record_file = "/tmp/baidu_xiongzhang_day_record.txt"

# 日志文件
log_file = "/tmp/baidu_xiongzhang_day.log"

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

def writeRecordFile(record_file_path, content):
    record_file = open(record_file_path, 'w')
    record_file.writelines(content)
    record_file.close()

def readRecordFile(record_file_path):
    content = "0"
    if(os.path.exists(record_file_path)):
        record_file = open(record_file_path, 'r')
        content = record_file.readline()
        record_file.close()
        if(len(content) == 0):
            content = "0"
    return content

def countWebsiteMapUrl():
    total = 0
    content = request.urlopen(site_map_url).read().decode('utf8')
    website_map_file = StringIO(content)
    for line in website_map_file:
        if(regexpMatchUrl(line) and regexpMatchWebSite(line)):
            total = total + 1
    website_map_file.close()
    return total

def createUrlFile(url_file_path, max_lines):
    old_index = readRecordFile(day_record_file)
    content = request.urlopen(site_map_url).read().decode('utf8')
    website_map_file = StringIO(content)
    url_file = open(url_file_path, 'w')

    # write url file
    index = 0
    number = 0
    for line in website_map_file:
        if(regexpMatchUrl(line) and regexpMatchWebSite(line)):
            if(index < int(old_index)):
                index = index + 1
                continue
            url = getUrl(line)
            if(url != ''):
                index = index + 1
                number = number + 1
                url_file.writelines(url + "\n")
                if(number >= max_lines):
                    break

    # update record file
    if(index == countWebsiteMapUrl()):
        writeRecordFile(day_record_file, str(0))
    else:
        writeRecordFile(day_record_file, str(index))

    # close file
    url_file.close()
    website_map_file.close()

def submitUrlFile(url, url_file_path, log_file):
    shell_cmd_line = "curl -H 'Content-Type:text/plain' --data-binary @" + url_file_path + " " + '\"' + url + '\"'
    (status, output) = subprocess.getstatusoutput(shell_cmd_line)
    logging.info(output + "\n")
    # print(shell_cmd_line)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename=log_file)
    createUrlFile(day_submit_urls_file, day_submit_max_lines)
    submitUrlFile(day_submit_url, day_submit_urls_file, log_file)


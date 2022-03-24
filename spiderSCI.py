# -*- coding: utf-8 -*-
from codecs import ignore_errors
import requests
from bs4 import BeautifulSoup
import os
# import re
import time
from pandas.core.api import (
    DataFrame,
)

# 定义全局变量
PMID_LIST = []  # 文献的PMID
DOI_LIST = []  # 文献的DOI
TITLE_LIST = []  # 要下载的文献名
YEAR_LIST = []  # 要下载的文献年份

path = ".\\Downloaded\\"

# 下载失败文献的表头
paper_data = DataFrame(columns=['PMID', 'title', 'Year', 'doi'])

failCount = 0
successCount = 0


def extractDoiPmidTitleYear(filename_in):
    """提取文件中的PMID,TITLE,YEAR,DOI"""

    # 打开文件
    file = open(filename_in, mode='r', encoding='utf-8')
    flag = True
    for line in file.readlines():
        # 过滤行标题
        if flag:
            flag = False
            continue
        # 分割字符串
        line = line.replace('\n', '')
        line = line.split(',')
        if not line:
            return 0
        # 去除题目中的转义字符
        line[1] = line[1].replace('\\', '-')
        line[1] = line[1].replace('/', '-')
        if line:
            PMID_LIST.append(line[0])
            TITLE_LIST.append(line[1])
            YEAR_LIST.append(line[2])
            DOI_LIST.append(line[3])
    file.close()

    return len(PMID_LIST)


def Download(url, articleIndex):
    ArticleMessage = TITLE_LIST[articleIndex] + YEAR_LIST[articleIndex]
    file = path + ArticleMessage + ".pdf"
    head = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'
    }  # 20210607更新，防止HTTP403错误
    if os.path.exists(file) == False:
        r = requests.get(url, headers=head)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "html.parser")
        # 如何SCI-HUB未收录：查看源代码发现如果出现div标签的属性为about,则说明未收录
        paper_list = soup.find_all('div', attrs={'id': 'about'})
        paper_record = {}
        if paper_list:
            global failCount
            failCount += 1
            paper_record['PMID'] = PMID_LIST[articleIndex]
            paper_record['title'] = TITLE_LIST[articleIndex]
            paper_record['Year'] = YEAR_LIST[articleIndex]
            paper_record['doi'] = DOI_LIST[articleIndex]
            # 当前文献下载失败，输出失败的文献名
            error_message = ArticleMessage + 'is download failed!!!'
            # 将失败的文献写入csv文件(先将paper_data变为全局变量)
            global paper_data
            paper_data = paper_data.append(paper_record, ignore_index=True)
            print(error_message)
            print('The %d article failed, total failed article: %d !!!' %
                  (articleIndex, failCount))

            return

        # 如果获取到页面
        download_url = soup.iframe.attrs["src"]  # 注：由于从SCI-HUB下载文献可能存在网络问题，
        # 如果该处报错，重新启动程序下载即可
        download_r = requests.get(download_url, headers=head)
        download_r.raise_for_status()
        with open(file, "wb+") as temp:
            temp.write(download_r.content)
        print('No.%d' % articleIndex, ArticleMessage + "pdf downloaded!")
    else:
        print(ArticleMessage + "pdf already exists!")
    global successCount
    successCount += 1
    print('No.%d' % articleIndex,
          'Total success download %d article!!!' % (successCount))


def main(filename):
    """函数处理主体"""
    if os.path.exists(path) == False:
        os.mkdir(path)
    if os.path.exists("error.txt") == True:
        os.remove("error.txt")

    # 提取CSV文件中的文献信息
    literature_num = extractDoiPmidTitleYear(filename)
    # 如果无文献，直接退出
    if not literature_num:
        print('%s not have literature!' % filename)
    else:
        print('%s have %d literature' % (filename, literature_num))

    # 记录下载文献开始时间
    start_time = time.time()
    # 下载文献
    for num in range(literature_num):
        url = "https://www.sci-hub.ren/doi:" + DOI_LIST[num] + "#"
        Download(url, num)

    # 下载失败的文件输出到文件中
    paper_data.to_csv('./failDownload.csv', index=False)

    # 下载完成
    print('All article download complete!!!')
    successRate = successCount/literature_num * 100
    print('from SCI-HUB download %d Article, fail %d article, success rate is %.2f %%'
          % (literature_num, failCount, successRate))
    # 记录下载文献结束时间
    end_time = time.time()
    run_time = end_time - start_time
    hour = run_time // 3600
    min = run_time % 3600 // 60
    sec = run_time % 60
    # 输出总用时
    print('Total time spent downloading literature: %d 小时 %d 分钟 %d 秒'
          % (hour, min, sec))


if __name__ == '__main__':
    main("Capacitive.csv")

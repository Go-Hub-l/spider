# -*- coding: utf-8 -*-
from codecs import ignore_errors
import requests
from bs4 import BeautifulSoup
import os
import re
import time
from pandas.core.api import (
    DataFrame,
)
from fake_useragent import UserAgent


# 获取随机User_Agent伪装
def get_fake_User_Agent():
    # 随机获取User_Agent
    ua = UserAgent()
    user_anget = ua.random
    return user_anget

# 爬虫类


class spider(object):
    def __init__(self, path, csv_file, try_count) -> None:
        self._pmid_list = []            # 文献的PMID
        self._title_list = []           # 要下载的文献名
        self._year_list = []            # 要下载的文献年份
        self._doi_list = []             # 文献的DOI
        self._path = path               # 下载的文献保存的文件夹路径
        self._paper_data = []           # 写入表格的数据
        self._fail_count = 0            # 下载失败文章数
        self._success_count = 0         # 下载成功文章数
        self._total_count = 0           # 总文章数
        self._max_try_time = try_count  # 最大尝试次数
        self._file_name = csv_file      # 准备好下载信息的csv文件
        self._already_download = 0      # 已经下载的文献

    # 初始化表头
    def init_everythind(self, columns=None):
        if columns:
            self.inin_table_head(columns)
        else:
            self.inin_table_head()

    def inin_table_head(self, columns=['PMID', 'title', 'Year', 'doi']):
        """初始化表头"""
        self._paper_data = DataFrame(columns=columns)
    # def table_head(self, columns):
    #     self._paper_data = DataFrame(columns=['PMID', 'title', 'Year', 'doi'])

    # 下载失败文献的表头
    # paper_data = DataFrame(columns=['PMID', 'title', 'Year', 'doi'])
    def filter_illegal_character(self, title):
        title = title.replace('"', '')

        chararter = re.compile(r'[\/:*?,;<>|]', re.I)
        chararter = chararter.findall(title)
        for ch in chararter:
            title = title.replace(ch, '-')

        return title

    def extractDoiPmidTitleYear(self, filename_in):
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
            # 正则表达式匹配 PMID
            pattern_PMID = re.compile('(\d{8}).*', re.I)
            match_PMID = pattern_PMID.findall(line)
            # 正则表达式匹配 TITLE
            pattern_TITLE = re.compile('\d{8},(.*),\d{4},.*', re.I)
            match_TITLE = pattern_TITLE.findall(line)
            # 正则表达式匹配 YEAR
            pattern_YEAR = re.compile('\d{8},.*,(\d{4}),{0,1}10\..*', re.I)
            match_YEAR = pattern_YEAR.findall(line)
            # 正则表达式匹配 DOI
            pattern_DOI = re.compile('\d{8},.*,\d{4},(10\..*)', re.I)
            match_DOI = pattern_DOI.findall(line)
            # 判断正则表达式是否匹配成功
            if not self.PTYDIsNull(match_PMID, match_TITLE,
                                   match_YEAR, match_DOI, line):
                return len(self._pmid_list)

            # 去除题目中的所有不合法字符
            match_TITLE[0] = self.filter_illegal_character(match_TITLE[0])
            if line:
                self._pmid_list.append(match_PMID[0])
                self._title_list.append(match_TITLE[0])
                self._year_list.append(match_YEAR[0])
                self._doi_list.append(match_DOI[0])
        file.close()

        return len(self._pmid_list)

    def add_fail_download_to_table(self, pmid, title, year, doi):
        """下载失败的问下添加进表格"""
        paper_record = {}
        paper_record['PMID'] = pmid
        paper_record['title'] = title
        paper_record['Year'] = year
        paper_record['doi'] = doi

        self._paper_data = self._paper_data.append(
            paper_record, ignore_index=True)

    def Download(self, url, articleIndex):
        ArticleMessage = self._title_list[articleIndex] + \
            self._year_list[articleIndex]
        file = self._path + ArticleMessage + ".pdf"
        head = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'
        }
        head = {
            'user-agent': get_fake_User_Agent()
        }

        if os.path.exists(file) == False:
            try:
                r = requests.get(url, headers=head)
                r.raise_for_status()
                r.encoding = r.apparent_encoding
            except Exception as e:
                print('Download article: %s' % e)
                self._fail_count += 1
                print('The %d article failed, total failed article: %d !!!' %
                      (articleIndex, self._fail_count))
                return
            soup = BeautifulSoup(r.text, "html.parser")
            # 如何SCI-HUB未收录：查看源代码发现如果出现div标签的属性为about,则说明未收录
            paper_list = soup.find_all('div', attrs={'id': 'about'})
            if paper_list:
                self._fail_count += 1
                # 下载失败的文献写入表格
                self.add_fail_download_to_table(self._pmid_list[articleIndex],
                                                self._title_list[articleIndex],
                                                self._year_list[articleIndex],
                                                self._doi_list[articleIndex])
                # 当前文献下载失败，输出失败的文献名
                error_message = ArticleMessage + 'is download failed!!!'
                print(error_message)
                print('The %d article failed, total failed article: %d !!!' %
                      (articleIndex, self._fail_count))

                return
            # 如果获取到页面
            # 注：由于从SCI-HUB下载文献可能存在网络问题，
            download_url = soup.iframe.attrs["src"]
            # 如果该处报错，重新启动程序下载即可
            try:
                download_r = requests.get(download_url, headers=head)
                download_r.raise_for_status()
                with open(file, "wb+") as temp:
                    temp.write(download_r.content)
                print('No.%d' % articleIndex, ArticleMessage + "pdf downloaded!")
            except Exception as e:
                # 下载失败的文献写入表格
                self.add_fail_download_to_table(self._pmid_list[articleIndex],
                                                self._title_list[articleIndex],
                                                self._year_list[articleIndex],
                                                self._doi_list[articleIndex])

                print('Download article: %s' % e)
                self._fail_count += 1
                print('The %d article failed, total failed article: %d !!!' %
                      (articleIndex, self._fail_count))
                return
        else:
            self._already_download += 1
            print(ArticleMessage + "pdf already exists, repeated article %d!" %
                  self._already_download)

        self._success_count += 1
        print('No.%d' % articleIndex,
              'Total success download %d article!!!' % (self._success_count))

    # 判断正则表达式提取的PMID, TITLE, YEAR, DOI 是否为空
    def PTYDIsNull(self, pLst, tLst, yLst, dLst, Message):
        if len(pLst) == 0:
            print(Message, 'extract PMID failed!!!')
            return False
        if len(tLst) == 0:
            print(Message, 'extract TITLE failed!!!')
            return False
        if len(yLst) == 0:
            print(Message, 'extract YEAR failed!!!')
            return False
        if len(dLst) == 0:
            print(Message, 'extract DOI failed!!!')
            return False
        return True

    def run(self):
        """函数处理主体"""
        if os.path.exists(self._path) == False:
            os.mkdir(self._path)
        if os.path.exists("error.txt") == True:
            os.remove("error.txt")

        # 提取CSV文件中的文献信息
        literature_num = self.extractDoiPmidTitleYear(self._file_name)
        # 如果无文献，直接退出
        if not literature_num:
            print('%s not have literature!' % self._file_name)
        else:
            print('%s have %d literature' % (self._file_name, literature_num))

        # 记录下载文献开始时间
        start_time = time.time()
        # 下载文献
        for num in range(61, literature_num):
            url = "https://www.sci-hub.ren/doi:" + self._doi_list[num] + "#"
            res = self.Download(url, num)

        # 下载失败的文件输出到文件中
        self._paper_data.to_csv('./failDownload.csv', index=False)

        # 下载完成
        print('All article download complete!!!')
        successRate = self._success_count/literature_num * 100
        print('from SCI-HUB download %d Article, fail %d article, success rate is %.2f %%'
              % (literature_num, self._fail_count, successRate))
        # 记录下载文献结束时间
        end_time = time.time()
        run_time = end_time - start_time
        hour = run_time // 3600
        min = run_time % 3600 // 60
        sec = run_time % 60
        # 输出总用时
        print('Total time spent downloading literature: %d 小时 %d 分钟 %d 秒'
              % (hour, min, sec))


def main(filename):
    path = ".\\ppper\\"
    spider_sci = spider(path, filename, 3)
    # 初始化
    spider_sci.init_everythind()
    spider_sci.run()


if __name__ == '__main__':
    main("Capacitive.csv")

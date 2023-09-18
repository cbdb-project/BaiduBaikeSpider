import requests
from bs4 import BeautifulSoup
import random
import time
import json
from tqdm import tqdm
import sys
import os


not_found_word_file = 'Not_found_keyword_list.txt'
all_info_file = 'all_crawled_info.csv'
log_file = 'log.txt'

url_prefix = {'1':'https://baike.baidu.com/item/', '2':'https://baike.deno.dev/item/'}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}


# get crawled keyword
def get_already_crwal_set(crawled_keyword_file):
    LOG_info('******************************************************************************')
    LOG_info('loading crawled baike keyword...')
    Crawled_keyword_set = set()
    Crawled_url_set = set()
    with open(crawled_keyword_file, 'r', encoding='utf-8') as reader:
        lines = reader.readlines()
        for line in tqdm(lines, desc='crawling'):
            a_data = json.loads(line)
            Crawled_keyword_set.add(a_data["keyword"])
            Crawled_url_set.add(a_data["url"])
    LOG_info("done, " + str(len(Crawled_keyword_set)) + " keyword has been crawled from Baidu Baike")
    return Crawled_keyword_set, Crawled_url_set


# get not found keyword
def get_not_found_set(not_found_word_file):
    LOG_info('loading not found keyword set...')
    with open(not_found_word_file, 'r', encoding='utf-8') as reader:
        lines = reader.readlines()
    Not_found_set = set(map(lambda x: x.strip(), lines)) 
    LOG_info('done, ' + str(len(Not_found_set)) + " keyword not found in Baidu Baike")
    return Not_found_set


# given keyword, get url
def get_crawl_url(Api, keyword_list):
    new_url_list = []
    for keyword in keyword_list:
        new_url_list.append([keyword, url_prefix[Api] + keyword])
    return new_url_list


def cookies_string_to_dict(cookies_string):
    cookies_dict = {}
    for cookie in cookies_string.split("; "):
        if "=" in cookie:
            key, value = cookie.split("=", 1)  # 将字符串分为两部分：键和值
            cookies_dict[key] = value
    return cookies_dict


# given url, crawl content
def crawl_content(url_list, Not_found_set, Api, Option, cookies=''):

    if Api == '1':
        # Load cookies from file
        with open('./cookies.txt', 'r') as f:
            cookies = f.read()

        if cookies == '':
            print("Please save the cookies in the file 'cookies.txt'")
        else:
            cookies_dict = cookies_string_to_dict(cookies)

        for keyword, url in tqdm(url_list):

            response = requests.get(url+"", headers=headers, cookies=cookies_dict, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # if keyword doest exist
            if soup.find('meta', attrs={'name': 'description'}) == None:
                LOG_info(keyword + " not found in Baidu Baike")
                Not_found(keyword, Not_found_set)
            else:
                LOG_info(keyword + " found in Baidu Baike, now crawling...")
                title = soup.find('h1').get_text()
                meta_tag = soup.find('meta', attrs={'name': 'description'})
                main_content = meta_tag['content']
                main_content = main_content.replace(' ', '').replace('\n', '').replace('\xa0', '')
                found_and_record(keyword, url, title, main_content)
            rest_time = random.random() * 10
            LOG_info('rest for ' + str(rest_time) + "secs")
            time.sleep(rest_time)

            if Option == 'multiple':
                links = get_multiple_urls(soup)
                for i in range(len(links)):
                    url = links[i]
                    response = requests.get(url+"", headers=headers, cookies=cookies_dict, timeout=10)
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # if keyword doest exist
                    if soup.find('meta', attrs={'name': 'description'}) == None:
                        LOG_info(keyword + " not found in Baidu Baike")
                        Not_found(keyword, Not_found_set)
                    else:
                        LOG_info(keyword + str(i+2) + " found in Baidu Baike, now crawling...")
                        title = soup.find('h1').get_text()
                        meta_tag = soup.find('meta', attrs={'name': 'description'})
                        main_content = meta_tag['content']
                        main_content = main_content.replace(' ', '').replace('\n', '').replace('\xa0', '')
                        found_and_record(keyword, url, title, main_content)

                    rest_time = random.random() * 20
                    LOG_info('rest for ' + str(rest_time) + "secs")
                    time.sleep(rest_time)

    elif Api == '2':
        print("Crawling from unofficial api...")
        for keyword, url in tqdm(url_list):
            response = requests.get(url+"", headers=headers).json()
            if response['status'] != 200:
                LOG_info(keyword + " not found in Baidu Baike")
                Not_found(keyword, Not_found_set)
            else:
                LOG_info(keyword + " found in Baidu Baike, now crawling...")
                title = response['data']['itemName']
                content = response['data']['description']
                found_and_record(keyword, url, title, content)

                if Option == 'multiple':
                    item_list_url = url.replace('/item/', '/item_list/')
                    list_response = requests.get(item_list_url+"", headers=headers).json()
                    item_num = len(list_response['data']['list'])
                    if item_num > 1:
                        for i in range(item_num-1):
                            index = i + 2
                            item_url = url + '?n=' + str(index)
                            item_response = requests.get(item_url+"", headers=headers).json()
                            LOG_info(keyword + '_' + str(index) + " found in Baidu Baike, now crawling...")
                            title = item_response['data']['itemName']
                            content = item_response['data']['description']
                            found_and_record(keyword, item_url, title, content)

            rest_time = random.random() * 10
            LOG_info('rest for ' + str(rest_time) + "secs")
            time.sleep(rest_time)


    LOG_info('crawl done')
    LOG_info('******************************************************************************')


def Not_found(key_word, Not_found_set):
    if key_word in Not_found_set:
        return
    else:
        with open("Not_found_keyword_list.txt", 'a', encoding='utf-8') as writer:
            writer.write(key_word + '\n')
        Not_found_set.add(key_word)


def record_keyword_allinfo(all_info_file, a_data):
    with open(all_info_file, 'a', encoding='utf-8-sig') as writer:
        values = a_data.values()
        texts = ",".join(values)
        writer.write(texts + '\n')


def found_and_record(keyword, url, title, content):
    a_data = {"keyword": keyword, 
              "url": url,
              "title": title,
              "content": content}
    record_keyword_allinfo(all_info_file, a_data)
    return a_data


def crawl_main(keyword_list, Not_found_set, Api, Option):
    new_url_list = get_crawl_url(Api, keyword_list)
    try:
        crawl_content(new_url_list, Not_found_set, Api, Option)
    except:
        if Api == '1':
            print("Some error happened.\nPlease check if you have already updated the cookies in the file 'cookies.txt'")

    
def read_keyword_file(keyword_file):
    with open(keyword_file, 'r', encoding='utf-8') as reader:
        lines = reader.readlines()
        keyword = list(map(lambda x: x.strip(), lines))
    return keyword


def get_multiple_urls(soup):
    if soup.find('ul', class_='polysemantList-wrapper cmn-clearfix') == None:
        return []
    else:
        ul_tag = soup.find('ul', class_='polysemantList-wrapper cmn-clearfix')
        links = [a['href'] for a in ul_tag.find_all('a')]
        links = ["https://baike.baidu.com" + link for link in links]
        return links


def LOG_info(message):
    print(message)
    with open(log_file, 'a', encoding='utf-8') as writer:
        writer.write(message + '\n')


class Baike_spider():
    def __init__(self, api, option):
        self.Not_found_set = get_not_found_set(not_found_word_file)
        self.Api = api
        self.Option = option

    def crawl_from_file(self, keyword_file):
        if not os.path.exists(keyword_file):
            print("file not exists, plz check again")    
            sys.exit(1)
        else:
            print('reading keyword file ....')

        keyword_list = read_keyword_file(keyword_file)
        with open(all_info_file, 'r', encoding='utf-8-sig') as f:
            crawled_keyword_list = [line.split(',')[0] for line in f.readlines()]
        keyword_list = list(set(keyword_list) - set(crawled_keyword_list))

        total_nums = len(keyword_list)
        LOG_info('--------------------------------------')
        LOG_info("file_name:" + keyword_file + " contains " + str(total_nums) + " keyword in total will be crawled")
        LOG_info('Crawling...')
        LOG_info('....................')

        crawl_main(keyword_list, self.Not_found_set, self.Api, self.Option)


if __name__ == "__main__":
    api = input('Please input 1 or 2:\n1. crawl from official website of baidu\n2. crawl from unofficial api\n')
    option_value = 'multiple'   # 设置为'multiple'将爬取同名词条的所有义项, 设置为'single'只爬取第一个义项  
    keyword_file = 'keyword.txt'
    baike_spider = Baike_spider(api=api, option=option_value)
    baike_spider.crawl_from_file(keyword_file)

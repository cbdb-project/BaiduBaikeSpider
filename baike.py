import requests
from bs4 import BeautifulSoup
import random
import time
import json
from tqdm import tqdm
import sys
import os

# create a random list from 1 to 198
def random_list():
    random_list = []
    while len(random_list) < 198:
        num = random.randint(1, 198)
        if num not in random_list:
            random_list.append(num)
    return random_list

print(random_list())


url_prefix = "https://baike.baidu.com/item/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

not_found_word_file = 'Not_found_keyword_list.txt'
all_info_file = 'all_crawled_info.csv'
log_file = 'log.txt'


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
def get_crawl_url(keyword_list):
    new_url_list = []
    for keyword in keyword_list:
        new_url_list.append([keyword, url_prefix + keyword])
    return new_url_list


# given url, crawl content
def crawl_content(url_list, Not_found_set, Option):
    for keyword, url in tqdm(url_list):
        response = requests.get(url+"", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # if keyword doest exist
        if soup.find('meta', attrs={'name': 'description'}) == None:
            LOG_info(keyword + " not found in Baidu Baike")
            Not_found(keyword, Not_found_set)
        else:
            LOG_info(keyword + " found in Baidu Baike, now crawling...")
            found_and_record(keyword, url, soup)
        rest_time = random.random() * 20
        LOG_info('rest for ' + str(rest_time) + "secs")
        time.sleep(rest_time)

        if Option == 'multiple':
            links = get_multiple_urls(soup)
            for i in range(len(links)):
                url = links[i]
                response = requests.get(url+"", headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')

                # if keyword doest exist
                if soup.find('meta', attrs={'name': 'description'}) == None:
                    LOG_info(keyword + " not found in Baidu Baike")
                    Not_found(keyword, Not_found_set)
                else:
                    LOG_info(keyword + str(i+2) + " found in Baidu Baike, now crawling...")
                    found_and_record(keyword, url, soup)

                rest_time = random.random() * 20
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


def found_and_record(keyword, url, soup):    
    title = soup.find('h1').get_text()
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    main_content = meta_tag['content']
    main_content = main_content.replace(' ', '').replace('\n', '').replace('\xa0', '')
    a_data = {"keyword": keyword, 
              "url": url,
              "title": title,
              "content": main_content}
    record_keyword_allinfo(all_info_file, a_data)
    return a_data


def crawl_main(keyword_list, Not_found_set, Option):
    new_url_list = get_crawl_url(keyword_list)
    crawl_content(new_url_list, Not_found_set, Option)

    
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
    def __init__(self, option):
        self.Not_found_set = get_not_found_set(not_found_word_file)
        self.Option = option

    def crawl_from_file(self, keyword_file):
        if not os.path.exists(keyword_file):
            print("file not exists, plz check again")    
            sys.exit(1)
        else:
            print('reading keyword file ....')

        keyword_list = read_keyword_file(keyword_file)

        total_nums = len(keyword_list)
        LOG_info('--------------------------------------')
        LOG_info("file_name:" + keyword_file + " contains " + str(total_nums) + " keyword in total will be crawled")
        LOG_info('Crawling...')
        LOG_info('....................')

        crawl_main(keyword_list, self.Not_found_set, self.Option)


if __name__ == "__main__":
    option_value = 'multiple'   # 设置为'multiple'将爬取同名词条的所有义项, 设置为'single'只爬取第一个义项  
    file_name = 'keyword.txt'
    baike_spider = Baike_spider(option=option_value)
    baike_spider.crawl_from_file(file_name)

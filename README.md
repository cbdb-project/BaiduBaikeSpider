# BaiduBaikeSpider

## Description
The program was developed based on [Baike_spider](https://github.com/JinJackson/Baike_spider).

Added new features:

1.Supports retrieving multiple synonyms for the same entry.

2.Set cookies to avoid the authentication from Baidu.

3.Crawl from [Unofficial API](https://github.com/vikiboss/deno-functions/tree/main/functions/baike).

## Usage
Place the keywords you want to crawl into the 'keyword.txt' file, one word per line, and then run baike.py.

Input the cookies munually to the 'cookies.txt' file before crawling. (Skip this step if using only the unofficial API)

Run the program. Input '1' to crawl from official website, or input '2' to crawl from unofficial api.

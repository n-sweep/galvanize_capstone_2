import os
import re
import json
from tqdm import tqdm
from time import sleep
from bs4 import BeautifulSoup
from pymongo import MongoClient

try:
    from crawler import Crawler
except:
    from src.crawler import Crawler

driver = Crawler()
client = MongoClient('192.168.0.211', 27017)
db = client['reverb']
link_coll = db['links']
sales_coll = db['sales']
data_coll = db['data']

brands = [
    'Teisco',
    'Travis',
    'Kramer',
    'Music Man',
    'Norma',
    'Martin',
    'National',
    'Taylor',
    'Airline',
    'Gibson',
    'G&L',
    'Harmony',
    'Danelectro',
    'Fender',
    'Rickenbacker',
    'Ibanez',
    'Hagstrom',
    'Mosrite',
    'Epiphone',
    'Gretsch',
    'Paul Reed Smith',
    'Reverend',
    'Silvertone',
    'Schecter',
    'Guild',
    'Supro',
    'BC Rich',
    'B.C. Rich',
    'ESP',
    'Ibanez',
    'Jackson',
    'Yamaha',
    'Framus',
    'Ovation'
]


def price_to_float(price):
    f = float(price[1:].replace(',', ''))
    return round(f, 2)

def hot_soup(html=None):
    """Return a beautiful soup object from the driver's current source"""
    html = html if html else driver.page_source
    return BeautifulSoup(html, 'html.parser')

def login():
    """Login to Reverb.com"""
    soup = hot_soup()
    
    # Find login button
    start = soup.find('a', class_='site-header__nav__link--login')
    driver.bsel(start).click()
    sleep(1)
    soup = hot_soup()
    
    # Find Username & Password fields
    usn = soup.find(id='user_session_login')
    psw = soup.find(id='user_session_password')
    username = driver.bsel(usn)
    password = driver.bsel(psw)
    
    # Load, enter, submit credentials
    with open('config.json', 'r') as f:
        conf = json.load(f)
        username.send_keys(conf['REVERB_LOGIN'])
        password.send_keys(conf['REVERB_PASS'])
    
    submit = soup.find('input', attrs={'type': 'submit'})
    driver.bsel(submit).click()

def scrape_links(collection, timeout):
    page = 1
    count = 0
    print('Scraping links...\n')
    while True:
        soup = hot_soup()
        tiles = soup.find('ul', class_='tiles')
        links = tiles.find_all('a', class_='csp-square-card__inner')
        
        scraped = [{'title': l.find('h3').text, 'link': l['href']} for l in links]
        count += len(scraped)
        collection.insert_many(scraped)
        
        print(f'Scraped page {page}, {count} total records gathered.\n')
        
        nxt = soup.find('li', class_='pagination__page pagination__page--next')
        if nxt:
            # Click next button
            page += 1
            driver.bsel(nxt).click()
            sleep(timeout)
        else:
            # All links have been gathered
            break

def scrape_transactions(links, collection):
    guide = 0
    count = 0
    for document in links:
        title = document['title']
        link = document['link']
        transaction_count = 0

        driver.get(link)
        
        # Collect all transactions from a price guide
        while True:
            sleep(1)
            soup = hot_soup()
            transactions = soup.find_all('tr', class_='transaction')

            if transactions:
                for transaction in transactions:
                    date = transaction.find(class_='date').text
                    cond = transaction.find(class_='condition').text
                    price = transaction.find(class_='final').text
                    collection.insert_one({
                        'title': title,
                        'date': date,
                        'cond': cond,
                        'price': price_to_float(price)
                    })
                    transaction_count += 1
            else:
                # There are no transactions in this price guide.
                print(f'{title} has no transactions.\n')
                break

            nxt = soup.find('button', attrs={'title': 'Next'})

            if not nxt or 'disabled' in nxt.attrs:
                # All transactions have been collected                              
                guide += 1
                count += transaction_count
                print(f'{transaction_count} transactions recorded for {title}.\n')
                break
                
            else:
                # Click next button
                driver.bsel(nxt).click()
    
    print(f'{count} transactions scraped from {guide} guides.\n')

def scrape_pages(links, collection, timeout):
    for link in tqdm(links, ascii=True):
        driver.get(link)
        sleep(timeout)
        html = driver.page_source
        link_coll.update_one({'link': link}, {'$set': {'html': html}})

def parse_title(title):
    # This works in a jupyter notebook but fails running this script???
    regex = r")(?:(?:(.+)((?:Early|Mid|Late)-?\s?'?\d+s|" \
            r"\d{4}\s?-\s?\d{4})(.*))|" \
            r"(?:(.+)(\d{4}s?)(.*))|" \
            r"(?:(.+)(\d{2}s?)(.*)))$"
    regex = r"(" + '|'.join(brands) + regex
    groups = re.match(regex, title, re.IGNORECASE).groups()
    feats = [g.strip() if g else None for g in groups if g is not None]

    return {k: feats[i] for i, k in enumerate(['Brand', 'Model', 'Year', 'Color'])}

def commit_titles_data(documents, collection):
    for doc in documents:
        data = parse_title(doc['title'])
        doc.update(data)
        #data_coll.insert_one(doc)

def scrape():
    timeout = 1
    driver.get('https://reverb.com/price-guide/electric-guitars')

    print('Logging in...\n')
    login()
    sleep(timeout)

    # scrape_links(link_coll, timeout)

    # links = link_coll.find({}, {'_id':0}, no_cursor_timeout=True)
    # scrape_transactions(links, data_coll)

    # scrape_pages(link_coll.distinct('link'), link_coll, timeout)
    # links.close()

    print('Scraping Complete.')

def main():
    docs = link_coll.find({'html': {'$exists': True}}, {'_id': 0, 'html': 0, 'link': 0})
    commit_titles_data(docs, data_coll)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)

driver.cleanup()

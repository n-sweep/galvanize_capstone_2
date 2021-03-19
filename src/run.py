import os
import json
from time import sleep
from crawler import Crawler
from bs4 import BeautifulSoup
from pymongo import MongoClient

driver = Crawler()
client = MongoClient('192.168.0.211', 27017)
db = client['reverb']
link_coll = db['links']
data_coll = db['data']


brands = [
    'Gibson',
    'Fender',
    'Rickenbacker',
    'Ibanez',
    'Epiphone',
    'Gretsch',
    'Paul Reed Smith',
    'Reverend',
    'Schecter',
    'Guild'
]

def hot_soup():
    """Return a beautiful soup object from the driver's current source"""
    return BeautifulSoup(driver.page_source, 'html.parser')

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

def scrape_transactions(links, collection, timeout):
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
                        'price': price
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
                print(f'{transaction_count} transactions recorded for {title}.\n')
                break
                
            else:
                # Click next button
                driver.bsel(nxt).click()
    
    print(f'{count} transactions scraped from {guide} guides.\n')

def main():
    timeout = 2
    driver.get('https://reverb.com/price-guide/electric-guitars')

    print('Logging in...\n')
    login()
    sleep(timeout)

#    scrape_links(link_coll, timeout)

    links = link_coll.find({}, {'_id':0}, no_cursor_timeout=True)
    scrape_transactions(links, data_coll, timeout)
    links.close()

    print('Scraping Complete.')

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)

driver.cleanup()

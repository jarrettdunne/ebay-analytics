import os 
import pandas as pd
import numpy as np
import re
import time

from bs4 import BeautifulSoup

'''
'transactions-date'
**'transaction--image'**
'transaction--desc'
'transaction--amount
'transaction--fees'
'transaction--net'
'transaction--running-total'
'transaction--details'

'''


def collection(html):
    with open(html) as fp:
        soup = BeautifulSoup(fp, 'html.parser')

    header = soup.find_all("header", {"class": "transactions-header-v2"})
    for name in header:
        header_spans = (name.find_all("span", {"class": "each-as-row"}))

    columns = list()
    for t in header_spans:
        columns.append(t.text.split()[0])

    df = pd.DataFrame(columns=columns)

    transactions_list = soup.find_all("div", {"class": "transaction--content-wrapper"})

    for item in transactions_list:
        i = len(df)
        dates = item.find_all('div', {'class': 'transactions-date'})
        df.loc[i, 'Date'] = dates[0].find('span').text

        orders = item.find_all('div', {'class': 'transaction--desc'})
        
        descs = item.find_all('div', {'class': 'transaction--desc'})
        desc = descs[0].find('span', {'class': 'BOLD'}).text
        df.loc[i, 'Description'] = desc

        if desc == 'Order':
            names = item.find_all('div', {'class': 'transaction--desc'})
            names= names[0].find_all('span', {'class': ''})
            print(names[1].text)
            df.loc[i, 'Name'] = names[1].text
        else:
            df.loc[i, 'Name'] = np.NaN

        amounts = item.find_all('div', {'class': 'transaction--amount'})
        try:
            df.loc[i, 'Amount'] = amounts[0].find('span', {'class': 'each-as-row'}).text
        except AttributeError:
            df.loc[i, 'Fees'] = np.NaN

        fees = item.find_all('div', {'class': 'transaction--fees'})
        try:
            df.loc[i, 'Fees'] = fees[0].find('span', {'class': 'each-as-row'}).text
        except AttributeError:
            df.loc[i, 'Fees'] = np.NaN

        nets = item.find_all('div', {'class': 'transaction--net'})
        df.loc[i, 'Net'] = nets[0].find('span', {'class': 'each-as-row'}).text

        totals = item.find_all('div', {'class': 'transaction--running-total'})
        df.loc[i, 'Total'] = totals[0].find('span', {'class': 'SECONDARY'}).text

        # details = item.find_all('div', {'class': 'transaction--details'})
    return df


if __name__ == "__main__":
    rootdir = os.getcwd()
    pages = os.listdir(rootdir + '/pages')
    l = len(pages)

    def make_csv(pages):
        df = pd.DataFrame()
        for page in pages:
            page = os.getcwd() + '/pages/' + page
            df = pd.concat([df, collection(page)], ignore_index=True)
            print(df)
        df.to_csv(f'data/eBay_transactions_{time.time()}.csv')

    def make_df(df, l):
            while l > 0:
                print(l)
                html = f'pages/page_{l}.html'
                new_df = collection(html)
                print(new_df)
                l -= 1
                return pd.concat([new_df, make_df(df, l)], ignore_index=True)


    # df = make_df(pd.DataFrame(), l)
    # df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
    # df.to_csv(f'data/eBay_transactions_{time.time()}.csv')


    # html = 'pages/page_1.html'
    # print(pages)
    # df = make_csv(pages)

    for page in pages:
        page = os.getcwd() + '/pages/' + page
        df = collection(page)

        # print(df)
import pandas as pd
import numpy as np
import re

csv = pd.read_csv('Transaction_report_20240101_20240801.csv')
csv.replace('--', np.nan, inplace=True)
report = csv[csv['Type'] != 'Payout']
report = report[['Transaction creation date', 'Type', 'Order number', 'Net amount', 'Item title']]
# report.ffill(inplace=True)
# report.bfill(inplace=True)
report.rename(columns={'Transaction creation date': 'Date'}, inplace=True)
# print(report[report['Date'].str.contains('apr', case=False)])
# report = report[~report['Date'].str.contains('apr', case=False)]
orders = report[report['Type'] == 'Order']
n, m = orders.shape
ref = dict()
for i in range(n):
    order = orders['Order number'].iloc[i]
    item = orders['Item title'].iloc[i]
    ref[order] = item

n, m = report.shape
for i in range(n):
    title = np.nan
    try:
        if report['Item title'].iloc[i] is np.nan:
            report['Item title'].iloc[i] = ref[report['Order number'].iloc[i]]
    except KeyError:
        print('key not found')
print(report)

cabi = report[report['Item title'].str.contains('cabi', case=False, na=False)]
# print(cabi.to_string())
bydate = cabi.groupby(['Date'])['Net amount'].sum()
# print(bydate)
res = cabi.groupby(['Item title'])['Net amount'].sum()
# print(sum(res), sum(res)/2)

# res = report[report['Type'] == 'Payout']
# print(res['Net amount'])
# net = report.groupby('Order number')['Net amount'].sum()
# print(net)
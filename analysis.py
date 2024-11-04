import glob
import os
import pandas as pd
import numpy as np

if __name__ == "__main__":
    list_of_files = glob.glob(os.getcwd() + '/data/*') # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getctime)

    df = pd.read_csv(latest_file)
    orders = df[df['Description'] == 'Order']
    print(orders)
    cabi_orders = orders[orders['Name'].str.contains('CAbi')]
    print(cabi_orders)
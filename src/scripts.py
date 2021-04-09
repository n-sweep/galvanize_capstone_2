import math
import numpy as np
import pandas as pd
import pickle as pk
import matplotlib.pyplot as plt
from pymongo import MongoClient
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor

client = MongoClient('192.168.0.209', 27017)
db = client['reverb']
sales_coll = db['sales']
data_coll = db['data']
link_coll = db['links']

def year_to_int(year):
    # If the year is already a digit, we're done
    if year.isdigit():
        return int(year)
    
    # Check for "early"/"mid"/"late" and build year integer accordingly
    # "Early 70s" becomes a random year between 1970 and 1973 
    for eml, nums in eml_dict.items():
        if eml in year:
            year = year.strip('s').replace("'", '').replace('-', ' ').split()[1]
            year = int('19' + year if len(year) < 4 else year)
            year += np.random.randint(*eml_dict[eml])
            return year
    
    if '-' in year: # Here we find date ranges such as "1938-1943"
        splt = year.split('-')
        low = int(splt[0])
        high = int(splt[1])
        
    else:  # Here we find 2-digit year strings such as "60s"
        # Add 19 if only decade is included
        base = '19' + year if len(year) < 4 else year
        # Remove apostrophes and pluralisations
        base = base.replace("'", '').strip('s')
        low = int(base)
        high = low + 9
    
    # Find average year of all guitars from date range already stored
    avg = round(int_years[(int_years >= low) & (int_years <= high)].mean())
    return avg
    print(year)

data_df = pd.DataFrame(list(data_coll.find({},{'_id':0})))
sales_df = pd.DataFrame(list(sales_coll.find({},{'_id':0})))
sales_df['date'] = pd.to_datetime(sales_df['date'], format='%m/%d/%Y')
sales = sales_df.groupby('title').mean().round(2)
records = sales_df.value_counts('title').to_frame()
data_df = data_df.merge(sales.rename(columns={'price': 'mean_sale'}), on='title')
data_df = data_df.merge(records.rename(columns={0: 'num_records'}), on='title')
int_years = pd.Series([int(year) for year in data_df['year'] if year.isdigit()])

# For years that include 'early', 'mid' or 'late' we'll choose a year at random
eml_dict = {
    'early': (0, 4),
    'mid': (4, 7),
    'late': (7, 10)
}
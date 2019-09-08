import pandas as pd
import numpy as np
import json
import io
import random

def prepareSalesData(csvfile):
    #Read store 20 sales
    store20_sales = pd.read_csv(csvfile, index_col=None)
    # Create Year column for grouping data
    store20_sales['Date'] = pd.to_datetime(store20_sales['Date'])
    store20_sales['Year'] = store20_sales['Date'].dt.year

    #Sort weekly sales by department
    store20_sales = store20_sales.sort_values(['Date', 'Dept'], ascending=True).reset_index(drop=True)
    #Select columns of interest
    store20_mod_sales = store20_sales[['Year', 'Date', 'Weekly_Sales', 'Dept', 'IsHoliday']]
    #Select departments with 143 weekly sales
    store20_mod_sales = store20_mod_sales.groupby(store20_mod_sales.Dept, as_index=True).filter(lambda x: len(x['Weekly_Sales']) > 142)

    #Map department numbers to categorical variables
    dept_list = store20_mod_sales['Dept'].unique()
    cat_values = [i for i in range(0, len(dept_list))]

    df_dept = pd.DataFrame(dept_list, index=cat_values, columns=['Dept'])
    df_dept['cat']=df_dept.index

    store20_mod_sales = store20_mod_sales.merge(df_dept, on=['Dept'])

    return store20_mod_sales

def getTestSales(prepdsales, test_key):
    #There a total of 66 departments, with 143 weekly sales
    #Create a dictionary of weekly sales for a given year dept
    testSet = dict(list(prepdsales.groupby('Dept', as_index=True)))
    #Write test json to the current directory
    writeSales(test_key, testSet)

    return testSet

def getTrainSales(prepdsales, train_key, prediction_length):
    testSet = dict(list(prepdsales.groupby('Dept', as_index=True)))
    trainingSet = dict()
    for dept in testSet.keys():
        trainingSet[dept] = testSet[dept][:-prediction_length]
    writeSales(train_key, trainingSet)

    return trainingSet
    
def writeSales(filename, data):
    #data is dictionary
    file=open(filename, 'w')
    keys=list(data.keys())
    random.shuffle(keys)
    for dept in keys:
        #On JSON sample per line; we've 66 samples in total (trainingSet)
        line = "\"start\":\"2010-01-01 00:00:00\",\"target\":{}, \"cat\":{}, \"dynamic_feat\":[{}]".format(data[dept]['Weekly_Sales'].tolist(), data[dept]['cat'].unique().tolist(), data[dept]['IsHoliday'].tolist())
        file.write('{'+line+'}\n')

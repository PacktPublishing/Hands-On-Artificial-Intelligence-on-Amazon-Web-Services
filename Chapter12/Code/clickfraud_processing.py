import boto3
import pandas as pd
import numpy as np
import os
import tarfile
import joblib
import xgboost as xgbst
import datetime as dt
import matplotlib.pyplot as plt
from itertools import cycle, islice

def upload_to_s3(bucket, channel, file):
    """
    input: S3 bucket name, folder on the bucket, RecordIO file to upload
    """
    s3 = boto3.resource('s3')
    data = open(file, "rb") # read in binary mode
    key = channel
    #Key is location on S3 bucket, Body - binary data
    s3.Bucket(bucket).put_object(Key=key, Body=data)

    
def create_date_ftrs(df_ckFraud, col_name):
    """
    create day, hour, minute, second features
    """
    df_ckFraud = df_ckFraud.copy()
    
    df_ckFraud['day'] = df_ckFraud[col_name].dt.day.astype('uint8') ## dt is accessor object for date like properties
    df_ckFraud['hour'] = df_ckFraud[col_name].dt.hour.astype('uint8')
    df_ckFraud['minute'] = df_ckFraud[col_name].dt.minute.astype('uint8')
    df_ckFraud['second'] = df_ckFraud[col_name].dt.second.astype('uint8')
    
    return df_ckFraud


def count_clicks(df_ckFraud):
    # Get all ip address related click counts
    ip_wday_cnt = df_ckFraud.groupby(['ip', 'day', 'hour'])['os'].count().reset_index()
    ip_wday_cnt.columns = ['ip', 'day', 'hour', 'clicks_by_ip_day_hr']
    
    ip_channel_cnt = df_ckFraud.groupby(['ip', 'hour', 'channel'])['os'].count().reset_index()
    ip_channel_cnt.columns = ['ip', 'hour', 'channel', 'clicks_by_ip_hr_chnl']
    
    ip_os_cnt = df_ckFraud.groupby(['ip', 'hour', 'os'])['channel'].count().reset_index()
    ip_os_cnt.columns = ['ip', 'hour', 'os', 'clicks_by_ip_hr_os']
    
    ip_app_cnt = df_ckFraud.groupby(['ip', 'hour', 'app'])['os'].count().reset_index()
    ip_app_cnt.columns = ['ip', 'hour', 'app', 'clicks_by_ip_hr_app']
    
    ip_device_cnt = df_ckFraud.groupby(['ip', 'hour', 'device'])['os'].count().reset_index()
    ip_device_cnt.columns = ['ip', 'hour', 'device', 'clicks_by_ip_hr_device']
    
    df_ckFraud = pd.merge(df_ckFraud, ip_wday_cnt, on=['ip', 'day', 'hour'], how='left', sort=False)
    df_ckFraud = pd.merge(df_ckFraud, ip_channel_cnt, on=['ip', 'hour', 'channel'], how='left', sort=False)
    df_ckFraud = pd.merge(df_ckFraud, ip_os_cnt, on=['ip', 'hour', 'os'], how='left', sort=False)
    df_ckFraud = pd.merge(df_ckFraud, ip_app_cnt, on=['ip', 'hour', 'app'], how='left', sort=False)
    df_ckFraud = pd.merge(df_ckFraud, ip_device_cnt, on=['ip', 'hour', 'device'], how='left', sort=False)
    
    return df_ckFraud

def encode_cat_ftrs(df_ckFraud):
    cat_ftrs = ['app','device','os','channel']
    
    for c in cat_ftrs:
        df_ckFraud[c+'_freq'] = df_ckFraud[c].map(df_ckFraud.groupby(c).size() / df_ckFraud.shape[0])
#         indexer = pd.factorize(df_ckFraud[c], sort=True)[1]
#         df_ckFraud[c+'_factrzr'] = indexer.get_indexer(df_ckFraud[c])
    return df_ckFraud

def plot_ftr_imp(model_file):
    tar = tarfile.open(model_file, "r:gz")
    for member in tar.getmembers():
     f = tar.extractfile(member)
     if f is not None:
         content = f.read()
    tar.extractall()

    fil = open('xgboost-model', 'rb')

    ## Load model file back into generate predictions & view feature importance
    xgb_local_ckFraud = joblib.load(fil)

    ## Close
    fil.close()

    ## Chart variable importance

    fig, ax = plt.subplots(figsize=(6,6))
    xgbst.plot_importance(xgb_local_ckFraud, max_num_features=8, height=0.8, ax=ax, show_values = False)
    plt.title('Click Fraud Model Feature Importance')
    plt.show()
    
def plot_clickcnt_ftr(df_ckFraud, ftr, exp_num):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    #my_colors = list(islice(cycle(['b', 'g', 'r', 'c', 'm', 'y', 'k']), None, 10))
    my_colors = list(islice(cycle(['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']), None, 10))
    
    df_ckFraud.groupby(ftr)['day'].count().sort_values(ascending=False).head(10).plot(kind='bar', ax=ax1, color=my_colors)
    ax1.set_xlabel(ftr)
    ax1.set_ylabel("Number of Clicks")
    ax1.set_title("Experiment #{}: Number of Clicks by {}".format(exp_num, ftr))

    df_ckFraud[df_ckFraud['is_downloaded'] == 1].groupby(ftr)['day'].count().sort_values(ascending=False).head(10).plot(kind='bar', ax=ax2, color=my_colors)
    ax2.set_xlabel(ftr)
    ax2.set_ylabel("Number of Clicks")
    ax2.set_title(("Experiment #{}: Number of Clicks by {} when apps are downloaded").format(exp_num, ftr))
    fig.subplots_adjust(wspace=1)
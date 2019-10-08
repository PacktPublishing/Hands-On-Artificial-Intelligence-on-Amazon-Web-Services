# Utility Functions for Merchandise Classification

import boto3
import os
import mxnet as mx
import sys
import subprocess
import matplotlib.pyplot as plt
from zipfile import ZipFile
import io
from urllib.parse import urlparse
import json
import numpy as np


# Upload compact representation of images (RecordIO) to S3 bucket

def upload_to_s3(bucket, channel, file):
    """
    input: S3 bucket name, folder on the bucket, RecordIO file to upload
    """
    s3 = boto3.resource('s3')
    data = open(file, "rb") # read in binary mode
    key = channel + '/' + file
    #Key is location on S3 bucket, Body - binary data
    s3.Bucket(bucket).put_object(Key=key, Body=data)

    

# Read zipped images folder present on S3 bucket
    
def extract_zipfile(bucket, key, rel_path):
    """
    input: S3 bucket name, location of zip file on s3 bucket, extract to location
    """
    s3 = boto3.resource('s3')
    obj = s3.Bucket(bucket).Object(key)
    
    with io.BytesIO(obj.get()["Body"].read()) as bf:
        bf.seek(0)
    
        # Read the file as zipfile 
        with ZipFile(bf, mode='r') as zipf:
           zipf.extractall(path=os.path.join('.', rel_path))
    

# Create List file for all images present in a directory

def create_listfile(data_path, prefix_path):
    """
    input: location of data, list file name and path
    """
    # Obtain the path of im2rec.py on the current ec2 instance
    im2rec_path = mx.test_utils.get_im2rec_path()
    #Do not print output from the shell command - python im2rec.py --list --test-ratio=0.2 'merch_data/merch-train.lst' 'merch_data/train'
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(['python', im2rec_path, '--list', '--recursive', prefix_path, data_path],
                          stdout=devnull)  

# Create compact representation of images (RecordIO)

def create_recordio(data_path, prefix_path):
    """
    input: location of data, list file name and path
    """
    # Obtain the path of im2rec.py on the current ec2 instance
    im2rec_path = mx.test_utils.get_im2rec_path()
    with open(os.devnull, 'wb') as devnull:
        subprocess.check_call(['python', im2rec_path, '--num-thread=4', '--pass-through', prefix_path, data_path],
                          stdout=devnull)
# '--resize=224', '--quality=95',

# List objects from designated folder in S3 bucket

def get_items(s3_client, bucket, prefix):
    """
    input: S3 client, S3 bucket name, folder on S3 bucket
    output: names of images in the folder
    """
    response = s3_client.list_objects(Bucket=bucket, Prefix=prefix)
    items = [content['Key'] for content in response['Contents']]
    return items


# Get label for each of the items/objects in output folder

def get_label_img(s3_client, bucket, prefix, test_images, item_categories):
    """
    input: S3 client, S3 bucket name, folder on S3 bucket containing output from image classification, 
    local path for test dataset, array of labels for each of the categories
    output: predicted label and probability
    """
    
    filename = prefix.split('/')[-1]
    s3_client.download_file(bucket, prefix, filename)
    with open(filename) as f:
        data = json.load(f)
        index = np.argmax(data['prediction']) #returns position of largest value
        probability = data['prediction'][index] # get the entry with highest probability
        
    # Format of predictions: {"prediction": [0.23142901062965393, 0.04651607573032379, 0.5318375825881958, 0.1708219051361084, 0.019395463168621063]}

    print("Result: label - " + item_categories[index] + ", probability - " + str(probability))
    #imdecode is used to load raw image files
    img = mx.image.imdecode(open(os.path.join(test_images, os.path.splitext(filename)[0]), 'rb').read())
    plt.imshow(img.asnumpy()); plt.show()
    
    return item_categories[index], probability
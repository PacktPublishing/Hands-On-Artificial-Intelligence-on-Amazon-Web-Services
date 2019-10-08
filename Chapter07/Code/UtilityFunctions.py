## some utility functions
import numpy as np
import csv, jsonlines
import os
import io
import string
import sys
import pandas as pd

# Output data in the format required by object2vec
def load_df_data(df, verbose=True):
    """
    input: a dataframe that 
    has format users - books - ratings - etc
    output: a list, where each row of the list is of the form
    {'in0':userID, 'in1':bookID, 'label':rating}
    """
    to_data_list = list()
    users = list()
    items = list()
    ratings = list()
    
    userIDMap = list()
    
    unique_users = set()
    unique_items = set()
    
    for idx, row in df.iterrows():
        to_data_list.append({'in0':[int(row['user_ind'])], 'in1':[int(row['book_ind'])], 'label':float(row['rating'])})
        users.append(row['user_ind'])
        items.append(row['book_ind'])
        ratings.append(float(row['rating']))
        unique_users.add(row['user_ind'])
        unique_items.add(row['book_ind'])
   
    if verbose:
        print("There are {} ratings".format(len(ratings)))
        print("The ratings have mean: {}, median: {}, and variance: {}".format(
                                            round(np.mean(ratings), 2), 
                                            round(np.median(ratings), 2), 
                                            round(np.var(ratings), 2)))
        print("There are {} unique users and {} unique books".format(len(unique_users), len(unique_items)))
        
    return to_data_list, ratings

# Save jsonlines to a file
def write_data_list_to_jsonl(data_list, to_fname):
    """
    Input: a data list, where each row of the list is a Python dictionary taking form
    {'in0':userID, 'in1':bookID, 'label':rating}
    Output: save the list as a jsonline file
    """
    with jsonlines.open(to_fname, mode='w') as writer:
        for row in data_list:
            #print(row)
            writer.write({'in0':row['in0'], 'in1':row['in1'], 'label':row['label']})
    print("Created {} jsonline file".format(to_fname))
    
 
 #Transform test data in the format required by object2vec
def data_list_to_inference_format(data_list, binarize=True, label_thres=3):
    """
    Input: a data list
    Output: test data and label, acceptable by SageMaker for inference
    """
    data_ = [({"in0":row['in0'], 'in1':row['in1']}, row['label']) for row in data_list]
    print("data_ :", data_)
    data, label = zip(*data_)
    print("data :", data)
    print("label :", label)
    
    infer_data = {"instances":data}
    
    print("infer_data : ", infer_data)
    
    if binarize:
        label = get_binarized_label(list(label), label_thres)
    return infer_data, label

# Compute Mean Squared Error for model evaluation
def get_mse_loss(res, labels):
    if type(res) is dict:
        res = res['predictions']
    assert len(res)==len(labels), 'result and label length mismatch!'
    loss = 0
    for row, label in zip(res, labels):
        if type(row)is dict:
            loss += (row['scores'][0]-label)**2
        else:
            loss += (row-label)**2
    return round(loss/float(len(labels)), 2)

# Create user and books dictionary
# User dictionary: users[userID] : {bookID, rating}
# Book dictionary: books[bookID] : {userID1, userID2..}
def jsnl_to_augmented_data_dict(jsnlRatings):
    """
    Input: json lines that
    has format users - books - ratings - etc
    Output:
      Users dictionary: keys as user ID's; each key corresponds to a list of book ratings by that user
      Books dictionary: keys as book ID's; each key corresponds a list of ratings of that book by different users
    """
    to_users_dict = dict() 
    to_books_dict = dict()
    
    for row in jsnlRatings:
        if row['in0'][0] not in to_users_dict:
            to_users_dict[row['in0'][0]] = [(row['in1'][0], row['label'])]
        else:
            to_users_dict[row['in0'][0]].append((row['in1'][0], row['label']))
        if row['in1'][0] not in to_books_dict:
            to_books_dict[row['in1'][0]] = list(row['in0'])
        else:
            to_books_dict[row['in1'][0]].append(row['in0'])
   
    return to_users_dict, to_books_dict
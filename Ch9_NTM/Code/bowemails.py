import pandas as pd
import numpy as np

from sklearn.preprocessing import normalize
from scipy.sparse import csr_matrix
import os
import boto3
import sagemaker
import io
import sagemaker.amazon.common as smamzc


# Create dataframe containing ordered list of words in vocabulary
def create_vocab(vocab_fn):
    vocab = pd.read_table(vocab_fn, header=None)
    vocab.columns = ['word']
    # sort words first
    vocab.sort_values(by=['word'])
    # assign index
    vocab['word_ID'] = range(1, len(vocab)+1)

    return vocab


# Create bow representation of emails and persist vocab file (filtered)
def prepare_bow_vocab(input_fn, percent_emails, vocab_ip_fn, vocab_op_fn):
    df_emails = pd.read_table(input_fn
                     , compression='gzip'
                     , header=None
                     , sep=' '
                     , skiprows = 3)
    
    df_emails.columns = ['email_ID','word_ID','count']
    # Filter emails to reduce data size
    len_emails = len(df_emails['email_ID'].unique())
    fil_len_emails = int(len_emails * percent_emails)
    # Get list of all email IDs
    emailID_list = df_emails['email_ID'].unique()
    # Get a % of the original emails to avoid memory errors
    emailID_list = emailID_list[0:fil_len_emails]
    # Filter the original dataframe to only include filtered email_id and word_id combinations
    df_emails = df_emails[df_emails['email_ID'].isin(emailID_list)]
    # Pivot email and word ID combinations
    pvt_emails = pd.pivot_table(df_emails, values='count', index='email_ID', columns=['word_ID'], fill_value=0)

    # Create filtered list of vocabulary
    df_vocab = create_vocab(vocab_ip_fn)
    #Only retrieve words that are part of filtered emails dataframe
    vocab_fil = pd.merge(df_vocab, df_emails, on='word_ID', how='inner' )
    words = vocab_fil['word'].unique()

    #Create vocabulary for the filtered dataset
    with open(vocab_op_fn, 'w') as f:
        for item in words:
            f.write("%s\n" % item)

    return pvt_emails

# Convert simple word counts per email to weighted word counts
# Weight is determined by term freq and inverse document freq
# Words that appear frequently within an email but less frequently across all emails are indicative of topics unique to the email in question
def TF_IDF(bag_of_words):
    no_emails = len(bag_of_words)
    dict_IDF = {name: np.log(float(no_emails) / (1+len(bag_of_words[bag_of_words[name] > 0])))  for name in bag_of_words.columns}
    new_BOW = pd.DataFrame()
    for name in bag_of_words.columns:
        new_BOW[name] = bag_of_words[name] * dict_IDF[name]

    return(new_BOW)

# Partition NTM compatible dataset for training
def convert_to_pbr(sprse_matrix, bucket, prefix, fname_template='emails_part{}.pbr', num_parts=2):

    partition_size = sprse_matrix.shape[0] // num_parts
    for i in range(num_parts):
        # Calculate start and end indices
        begin = i*partition_size
        finish = (i+1)*partition_size
        if i+1 == num_parts:
            finish = sprse_matrix.shape[0]

        # Convert sparse matrix to sparse tensor (record io protobuf) - a format required by NTM algorithm
        # pbr - Amazon Record Protobuf format
        data_bytes = io.BytesIO()
        smamzc.write_spmatrix_to_sparse_tensor(array=sprse_matrix[begin:finish], file=data_bytes, labels=None)
        data_bytes.seek(0)

        # Upload to s3 location specified by bucket and prefix
        file_name = os.path.join(prefix, fname_template.format(i))
        boto3.resource('s3').Bucket(bucket).Object(file_name).upload_fileobj(data_bytes)

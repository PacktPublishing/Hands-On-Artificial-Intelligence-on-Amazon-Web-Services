from __future__ import print_function
from __future__ import unicode_literals

#Import required modules

import time
import sys
import os
import shutil
import csv
import boto3

from awsglue.utils import getResolvedOptions

import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.ml.feature import RegexTokenizer, StopWordsRemover, CountVectorizer, Tokenizer, IDF
from pyspark.sql.functions import *
from pyspark.sql import functions as F
from pyspark.sql.window import Window 
from mleap.pyspark.spark_support import SimpleSparkSerializer

from awsglue.utils import getResolvedOptions

from pyspark.ml import Pipeline, Transformer, PipelineModel
from pyspark import since, keyword_only
from pyspark.ml.linalg import SparseVector, DenseVector 


def gen_str(row_arr):
    return (','.join([str(elem) for elem in row_arr.toArray()]))


def main():
    spark = SparkSession.builder.appName("AbcHeadlinesSpark").getOrCreate()
    
    #getResolvedOptions (args, options=argument names that you want to retrieve) gives you access to the arguments that are passed to the SparkML script when running a job
    
    args = getResolvedOptions(sys.argv, ['S3_INPUT_BUCKET',
                                         'S3_INPUT_KEY_PREFIX',
                                         'S3_INPUT_FILENAME',
                                         'S3_OUTPUT_BUCKET',
                                         'S3_OUTPUT_KEY_PREFIX',
                                         'S3_MODEL_BUCKET',
                                         'S3_MODEL_KEY_PREFIX'])

    
    
    #Read the compressed text file containing enron emails encoded as table containing docID, wordID, and count
    abcnewsdf = spark.read.option("header","true").csv(('s3://' + os.path.join(args['S3_INPUT_BUCKET'], args['S3_INPUT_KEY_PREFIX'], args['S3_INPUT_FILENAME'])))
    
    #Filter number of abc news headlines
    #1,103,663 - headlines
    hdl_cnt = abcnewsdf.count()
    #Filter the number of headlines
    hdl_fil_cnt = hdl_cnt * .1
    hdl_fil_cnt = int(hdl_fil_cnt)
    abcnewsdf = abcnewsdf.limit(hdl_fil_cnt)

    #Create features from text
    
    #Tokenizer
    tok = Tokenizer(inputCol="headline_text", outputCol="words") 

    # stop words
    swr = StopWordsRemover(inputCol="words", outputCol="filtered")
    
    # Term frequency
    ctv = CountVectorizer(inputCol="filtered", outputCol="tf", vocabSize=200, minDF=2)

    #Term frequency is weighted by number of times the word appears across all docs in corpus
    # Words that are unique to a headline have more weight - since they define the headline
    idf = IDF(inputCol="tf", outputCol="features")

    # Build the pipeline 
    news_pl = Pipeline(stages=[tok, swr, ctv, idf])
    
    #Transformed dataset
    news_pl_fit = news_pl.fit(abcnewsdf)
    news_ftrs_df = news_pl_fit.transform(abcnewsdf)
    
    gen_str_udf = F.udf(gen_str, StringType())
    
    #Convert Sparse vector to Dense vector
    news_formatted = news_ftrs_df.withColumn('result', gen_str_udf(news_ftrs_df.features))
    
    #Save the Dense vector to csv file
    news_save = news_formatted.select("result")
    news_save.write.option("delimiter", "\t").mode("append").csv('s3://' + os.path.join(args['S3_OUTPUT_BUCKET'], args['S3_OUTPUT_KEY_PREFIX']))
    
    #Save the vocabulary file
    vocab_list = news_pl_fit.stages[2].vocabulary
    vocab_df = spark.createDataFrame(vocab_list, StringType())
    
    vocab_df = vocab_df.coalesce(1) 
    
    vocab_df.write.option("delimiter", "\n").format("text").mode("append").save('s3://' + os.path.join(args['S3_OUTPUT_BUCKET'], args['S3_OUTPUT_KEY_PREFIX']))
    
    # Serialize the tokenizer via MLeap and upload to S3
    SimpleSparkSerializer().serializeToBundle(news_pl_fit, "jar:file:/tmp/model.zip", news_ftrs_df)    
       
    # Unzip as SageMaker expects a .tar.gz file but MLeap produces a .zip file.
    import zipfile
    with zipfile.ZipFile("/tmp/model.zip") as zf:
        zf.extractall("/tmp/model")
        
    # Write back the content as a .tar.gz file
    import tarfile
    with tarfile.open("/tmp/model.tar.gz", "w:gz") as tar:
        tar.add("/tmp/model/bundle.json", arcname='bundle.json')
        tar.add("/tmp/model/root", arcname='root')
    
    s3 = boto3.resource('s3')
    file_name = os.path.join(args['S3_MODEL_KEY_PREFIX'], 'model.tar.gz')
    s3.Bucket(args['S3_MODEL_BUCKET']).upload_file('/tmp/model.tar.gz', file_name)

if __name__ == "__main__":
    main()
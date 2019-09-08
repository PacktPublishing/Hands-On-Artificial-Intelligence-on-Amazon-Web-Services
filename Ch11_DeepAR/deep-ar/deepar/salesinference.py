import io
import boto3
import random
import json
import matplotlib.pyplot as plt
import numpy as np

q1 = '0.1 '
q2 = '0.9'
num_samples = 100 # predict 100 sample series

def buildInferenceData(dept, trainSet, testSet):
    #dept_sales = data[dept]
    holidays = []
    holidays.append(testSet[dept]['IsHoliday'].tolist())
    s = {"start": "2010-01-01 00:00:00", "target": trainSet[dept]['Weekly_Sales'].tolist(), "cat": trainSet[dept]['cat'].unique().tolist(), "dynamic_feat": holidays}
    series = []
    series.append(s)
    configuration = {
        "output_types": ["mean", "quantiles", "samples"],
        "num_samples": num_samples,
        "quantiles": [q1, q2]
    }
    http_data = {
        "instances": series,
        "configuration": configuration
    }
    return json.dumps(http_data)

def getInferenceSeries(result):
    json_result = json.loads(result)
    y_data      = json_result['predictions'][0] #TO DO - check what this representation means
    y_mean      = y_data['mean']
    y_q1        = y_data['quantiles'][q1]
    y_q2        = y_data['quantiles'][q2]
    y_sample    = y_data['samples'][random.randint(0, num_samples)]
    return y_mean, y_q1, y_q2, y_sample

def plotResults(prediction_length, result, truth=False, truth_data=None, truth_label=None):
    x = range(0, prediction_length)
    y_mean, y_q1, y_q2, y_sample = getInferenceSeries(result)
    plt.gcf().clear() #clear the current plot
    mean_label, = plt.plot(x, y_mean, label='mean')
    q1_label, = plt.plot(x, y_q1, label=q1)
    q2_label, = plt.plot(x, y_q2, label=q2)
    sample_label, = plt.plot(x, y_sample, label='sample')

    if truth:
        ground_truth, = plt.plot(x, truth_data, label=truth_label)
        plt.legend(handles=[ground_truth, q2_label, mean_label, q1_label, sample_label])
    else:
        plt.legend(handles=[q2_label, mean_label, q1_label, sample_label])
    plt.yticks(np.arange(0.22, 2.0, 0.1)) #tick marks on y axis, .22 to 2, with 0.1 steps
    plt.show()

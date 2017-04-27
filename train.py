import os

import numpy as np
import pandas as pd
from sklearn.datasets import dump_svmlight_file
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
from sklearn.metrics import accuracy_score, f1_score
from sklearn.svm import SVC

from metrics import *
from utils import *


def load_data(summary, path, logger):

    summary = summary[summary['Include'] == 1]
    summary_train = summary[summary['Test'] == 0]
    summary_test = summary[summary['Test'] == 1]

    train_files = [x.strip(' ') for x in summary_train['File Name']]
    test_files = [x.strip(' ') for x in summary_test['File Name']]

    logger.info('Len train files = ' + str(len(train_files)))
    logger.info('Len test files = ' + str(len(test_files)))

    X_train = np.load(path + train_files[0] + '_data.npy')
    y_train = np.load(path + train_files[0] + '_target.npy')
    X_test = np.load(path + test_files[0] + '_data.npy')
    y_test = np.load(path + test_files[0] + '_target.npy')

    for file in train_files[1:]:
        logger.info(file)
        X_train = np.append(X_train, np.load(
            path + file + '_data.npy'), axis=0)
        y_train = np.append(y_train, np.load(
            path + file + '_target.npy'), axis=0)

    for file in test_files[1:]:
        X_test = np.append(X_test, np.load(path + file + '_data.npy'), axis=0)
        y_test = np.append(y_test, np.load(
            path + file + '_target.npy'), axis=0)

    logger.info('Loaded Data')
    logger.info('Train data shape = ' +
                str(X_train.shape) + str(y_train.shape))
    logger.info('Test data shape = ' + str(X_test.shape) + str(y_test.shape))

    return X_train, y_train, X_test, y_test


def main(logger):

    file_summary = 'input/patient_summary.csv'
    test_files = ['chb01_26.edf', 'chb01_27.edf', 'chb01_29.edf']
    path = 'D:/Tanay_Project/processed/'

    X_train, y_train, X_test, y_test = load_data(
        file_summary, test_files, path, logger)

    model = SVC()
    model.fit(X_train, y_train)
    joblib.dump(model, 'svm.pkl')
    # model = joblib.load('svm.pkl')

    logger.info('Training Done')

    y_p = model.predict(X_test)
    logger.info('accuracy_score = {:.3f}'.format(
        accuracy_score(y_test, y_p) * 100))
    logger.info('f1_score = {:.3f}'.format(f1_score(y_test, y_p) * 100))


def dump_svmlight_dataset(summary, processed_dir, output_dir, logger):
    X_train, y_train, X_test, y_test = load_data(summary,
                                                 processed_dir,
                                                 logger)

    # convert target values to -1 | 1
    y_train[y_train == 0] = -1
    y_test[y_test == 0] = -1

    # convert infs to 0
    X_train[X_train == np.inf] = 0
    X_test[X_test == np.inf] = 0

    X_train[X_train == -np.inf] = 0
    X_test[X_test == -np.inf] = 0

    dump_svmlight_file(X_train, y_train, output_dir +
                       'svmlight_train.dat', zero_based=False)
    dump_svmlight_file(X_test, y_test, output_dir +
                       'svmlight_test.dat', zero_based=False)
    logger.info('Saved files to ' + output_dir)


def svm_light(X_train, y_train, X_test, y_test, logger):
    """
    index: is an integer that should be unique every time you run this function so that the files
    are not overwritten
    """
    dump_svmlight_file(X_train, y_train, 'svmlight/svmlight_train.dat', zero_based=False)
    dump_svmlight_file(
        X_test, y_test, 'svmlight/svmlight_test.dat', zero_based=False)
    logger.info('Saved files')


    train_path = os.path.join('svmlight','svm_learn.exe')
    test_path = os.path.join('svmlight','svm_classify.exe')

    os.system(train_path + ' svmlight/svmlight_train.dat svmlight/model > train.log')
    logger.info("learning done")
    os.system(test_path + ' svmlight/svmlight_test.dat svmlight/model > test.log')
    logger.info("classifying done")
    with open('test.log') as f:
        contents = f.read()
    contents = contents.split('\n')
    precision, recall = contents[-2].split(': ')[1].replace('%','').split('/')
    precision = float(precision)/100
    recall = float(recall)/100
    accuracy = float(contents[-3].split(' ')[4].replace('%',''))/100
    f1 = 2 * (precision * recall) / (precision + recall)
    dump_data_to_csv(
        np.array([accuracy, recall, precision, f1]), 'perf_svm_light.csv')



def random_forest(X_train, y_train, X_test, y_test, logger=None):
    model = RandomForestClassifier()
    y_pred = model.fit(X_train, y_train).predict(X_test)
    [accuracy, recall, precision, f1_score] = evaluate_model(y_test, y_pred)
    dump_data_to_csv(
        np.array([accuracy, recall, precision, f1_score]), 'perf_random_forest.csv')


if __name__ == '__main__':
    logger = setup_logging('logs/', 'svm_train')
    # main()
    summary = pd.read_csv('input/patient_summary.csv')
    summary['File Name'] = summary['File Name'].str.strip(' ')
    summary.index = summary['File Name']
    names = summary['File Name'].dropna()

    patients = ['chb03', 'chb05', 'chb06', 'chb07']
    summary = summary[summary.Include == 1]

    for patient in patients:
        summary.loc[:, 'Include'] = 0
        print(patient)
        files = names[names.str.contains(patient)]
        #files = files.replace(' ','')
        summary.loc[files, 'Include'] = 1

        dump_svmlight_dataset(
            summary, 'D:/Tanay_Project/processed/', 'D:/Tanay_Project/svmlight/', logger)
        os.system('D:/Tanay_Project/svmlight/svm_learn.exe D:/Tanay_Project/svmlight/svmlight_train.dat D:/Tanay_Project/svmlight/model > train' + patient + '.log')
        logger.info("learning done")
        os.system('D:/Tanay_Project/svmlight/svm_classify.exe D:/Tanay_Project/svmlight/svmlight_test.dat D:/Tanay_Project/svmlight/model > test' + patient + '.log')
        logger.info("classifying done")

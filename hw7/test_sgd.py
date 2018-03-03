"""
Manual tests for visually inspecting the optimization progess.
Normally passed test cases are disablled with x prefix, other cases are prefixed with test_
to enable pytest discovery mechanism.
"""

import pytest
import pandas as pd
import random

from dmia.classifiers import LogisticRegression
from dmia.classifiers.model import *
from dmia.classifiers.opt import *
from dmia.classifiers.data_iter import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
#from sklearn import


@pytest.fixture(scope="module")
def dataset():
    train_df = pd.read_csv('./data/train.csv')
    train_df.Prediction.value_counts(normalize=True)
    review_summaries = list(train_df['Reviews_Summary'].values)
    review_summaries = [l.lower() for l in review_summaries]
    vectorizer = TfidfVectorizer()
    tfidfed = vectorizer.fit_transform(review_summaries)
    X = tfidfed
    y = train_df.Prediction.values
    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.7, random_state=42)
    train = Dataset(X_train, y_train)
    valid = Dataset(X_test, y_test)
    return train, valid


def train_lr(train, valid, params):
    clf = LogisticRegression()
    clf.train(train.X, train.y, **params)
    train_loss, _ = clf.loss(clf.append_biases(train.X), train.y)
    valid_loss, _ = clf.loss(clf.append_biases(valid.X), valid.y)
    return train_loss, valid_loss


def Xtest_simple_sgd(dataset):
    opt_params = {
        "lr_decay": "t_power",
        "lr_decay_params": {"a": 1.0, "t_power": 0.5}
    }
    optimizer = SGDOptimizer(**opt_params)
    params = {
        "optimizer": optimizer,
        "verbose": True,
        "calc_full_loss_every_n_batches": 100,
        "batch_size": 50,
        "num_iters": 1,
        "reg": 1e-5,
        "learning_rate": 10.0
    }
    train, valid = dataset
    print "Simple SGD with lr decay as 1/sqrt(t) and params %s %s" % (params, opt_params)
    train_lr(train, valid, params)
    #assert False


def Xtest_sgd_with_adagrad(dataset):
    opt_params = {
        "lr_decay": "adagrad",
        "lr_decay_params": {"a": 1.0}
    }
    optimizer = SGDOptimizer(**opt_params)
    params = {
        "optimizer": optimizer,
        "verbose": True,
        "calc_full_loss_every_n_batches": 100,
        "batch_size": 50,
        "num_iters": 1,
        "reg": 1e-5,
        "learning_rate": 10.0
    }
    print "SGD with Adgrad lr decay, params = %s %s" % (params, opt_params)
    train, valid = dataset
    train_lr(train, valid, params)


def Xtest_ftrl_adagrad(dataset):
    opt_params = {
        "lr_decay": "adagrad",
        "lr_decay_params": {"a": 1.0}
    }
    optimizer = FTRLOptimizer(**opt_params)
    params = {
        "optimizer": optimizer,
        "verbose": True,
        "calc_full_loss_every_n_batches": 100,
        "batch_size": 50,
        "num_iters": 1,
        "reg": 1e-5,
        "l1": 1e-7,
        "learning_rate": 20.0
    }
    train, valid = dataset
    model = FTRLLogRegModel(train.X.shape[1] + 1,
                l2=params["reg"], l1=params["l1"], lr=params["learning_rate"])
    params["model"] = model

    print "FTRL SGD with Adgrad lr decay, params = %s %s" % (params, opt_params)
    train_lr(train, valid, params)


def test_svrg_adagrad(dataset):
    opt_params = {
        "lr_decay": "adagrad",
        "lr_decay_params": {"a": 1.0}
    }
    optimizer = SVRGOptimizer(**opt_params)
    params = {
        "optimizer": optimizer,
        "verbose": True,
        "calc_full_loss_every_n_batches": 100,
        "batch_size": 50,
        "num_iters": 3,
        "reg": 1e-5,
        "learning_rate": 10.0
    }
    train, valid = dataset
    dim = train.X.shape[1] + 1
    model = SVRGLogRegModel(dim, data_shape=(train.X.shape[0], dim),
                l2=params["reg"], lr=params["learning_rate"])
    params["model"] = model
    print "SVRG with Adgrad lr decay, params = %s %s" % (params, opt_params)
    train_lr(train, valid, params)


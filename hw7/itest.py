#!/usr/bin/env python
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


def train_lr(train, valid, params):
    clf = LogisticRegression()
    clf.train(train.X, train.y, **params)
    train_loss, _ = clf.loss(clf.append_biases(train.X), train.y)
    valid_loss, _ = clf.loss(clf.append_biases(valid.X), valid.y)
    return train_loss, valid_loss


if __name__ == "__main__":

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
    train_lr(train, valid, params)


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
    train_lr(train, valid, params)




#!/usr/bin/env python
import pandas as pd
import random


from dmia.classifiers import LogisticRegression
from dmia.classifiers.model import LogRegModel, SparseLogRegModel
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

def params_iter(cat_grid, rv_grid, num_samples=None):
    cnt = 0
    while True:
        if num_samples and cnt >= num_samples:
            raise StopIteration
        point = {}
        for param, interval in rv_grid.iteritems():
            point[param] = random.uniform(*interval)
        for param, vals in cat_grid.iteritems():
            point[param] = random.choice(vals)
        cnt += 1
        yield point

def find_best_params(train, valid, cat_grid, rv_grid, num_samples):
    default_params = {
        "verbose": False,
        "calc_full_loss_every_n_batches": 10000
    }
    best_train_loss = 1e+12
    best_valid_loss = 1e+12
    best_train_params = None
    best_valid_params = None
    for params in params_iter(cat_grid=cat_grid, rv_grid=rv_grid, num_samples=num_samples):
        #print "trying point: %s" % params
        default_params.update(params)
        train_loss, valid_loss = train_lr(train, valid, default_params)
        #print train_loss, valid_loss
        if train_loss < best_train_loss:
            best_train_params = params
            best_train_loss = train_loss
        if valid_loss < best_valid_loss:
            best_valid_params = params
            best_valid_loss = valid_loss

    print "train", best_train_loss, best_train_params
    print "valid", best_valid_loss, best_valid_params
    return best_valid_loss, best_valid_params


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

    rv_grid = {
        "batch_size": (32, 512)
    }
    cat_grid = {
        "num_iters": [1, 2, 3, 4, 5, 6, 7],
        "reg": (1e-7, 1e-6, 1e-5, 1e-4, 1e-3),
        "learning_rate": (1e-3, 1e-2, 1e-1, 1.0, 1e+1, 50.0)
    }
    find_best_params(train, valid, cat_grid, rv_grid, num_samples=40)

    rv_grid = {
        "learning_rate": (1.0, 20.0),
        "batch_size": (40, 80),
        "reg": (1e-7, 1e-5),
    }
    cat_grid = {
        "num_iters": [3, 4, 5],
    }
    find_best_params(train, valid, cat_grid, rv_grid, num_samples=20)



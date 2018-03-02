#!/usr/bin/env python
import pandas as pd
import random
from copy import deepcopy
import sys
import inspect
import multiprocessing as mp

from dmia.classifiers import LogisticRegression
from dmia.classifiers.model import *
from dmia.classifiers.opt import *
from dmia.classifiers.data_iter import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer


MAX_COEFF = 5
MIN_COEFF = 0.2

NSHOTS = 60

def get_sampling_interval(val):
    return (MIN_COEFF * val, MAX_COEFF * val)


def get_cat_sampling_distr(val):
    return [val - 1, val, val + 1]


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


def find_best_params(train, valid, cat_grid, rv_grid, num_samples, default_params):
    best_train_loss = 1e+12
    best_valid_loss = 1e+12
    best_train_params = None
    best_valid_params = None
    aux_params = deepcopy(default_params)
    for params in params_iter(cat_grid=cat_grid, rv_grid=rv_grid, num_samples=num_samples):
        #print "trying point: %s" % params
        aux_params.update(params)
        train_loss, valid_loss = train_lr(train, valid, aux_params)
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


def exp_sgd(train, valid, num_samples=NSHOTS):
    sys.stdout = open("log.%s" % inspect.currentframe().f_code.co_name, "w")
    print 80 * "="
    print "Pure SGD experiment"
    opt_params = {}
    optimizer = SGDOptimizer(**opt_params)

    params = {
        "optimizer": optimizer,
        "verbose": False,
        "calc_full_loss_every_n_batches": 100,
    }
    rv_grid = {
        "batch_size": (50, 200)
    }
    cat_grid = {
        "num_iters": [3, 4, 5, 6, 7],
        "reg": (1e-7, 1e-6, 1e-5, 1e-4, 1e-3),
        "learning_rate": (1e-2, 1e-1, 1.0, 10, 50.0)
    }

    print "First shot"
    best_loss, params = find_best_params(train, valid, cat_grid, rv_grid, num_samples, params)
    rv_grid = {
        "learning_rate": get_sampling_interval(params["learning_rate"]),
        "batch_size": get_sampling_interval(params["batch_size"]),
        "reg": get_sampling_interval(params["reg"]),
    }
    cat_grid = {
        "num_iters": get_cat_sampling_distr(params["num_iters"]),
    }
    print "Second shot"
    best_loss2, params2 = find_best_params(train, valid, cat_grid, rv_grid, num_samples, params)


def exp_sgd_lr_decay(train, valid, num_samples=NSHOTS):
    sys.stdout = open("log.%s" % inspect.currentframe().f_code.co_name, "w")
    print 80 * "="
    print "Pure SGD experiment + simple lr decay"
    opt_params = {
        "lr_decay": "t_power",
        "lr_decay_params": {"a": 1.0, "t_power": 0.5}
    }
    optimizer = SGDOptimizer(**opt_params)
    params = {
        "optimizer": optimizer,
        "verbose": False,
        "calc_full_loss_every_n_batches": 1000,
    }
    rv_grid = {
        "batch_size": (50, 200)
    }
    cat_grid = {
        "num_iters": [3, 4, 5, 6, 7],
        "reg": (1e-7, 1e-6, 1e-5, 1e-4, 1e-3),
        "learning_rate": (1e-2, 1e-1, 1.0, 10, 50.0)
    }

    print "First shot"
    best_loss, params = find_best_params(train, valid, cat_grid, rv_grid, num_samples, params)
    rv_grid = {
        "learning_rate": get_sampling_interval(params["learning_rate"]),
        "batch_size": get_sampling_interval(params["batch_size"]),
        "reg": get_sampling_interval(params["reg"]),
    }
    cat_grid = {
        "num_iters": get_cat_sampling_distr(params["num_iters"]),
    }
    print "Second shot"
    best_loss2, params2 = find_best_params(train, valid, cat_grid, rv_grid, num_samples, params)


def exp_ftrl_adagrad(train, valid, num_samples=NSHOTS):
    sys.stdout = open("log.%s" % inspect.currentframe().f_code.co_name, "w")
    print 80 * "="
    print "FTRL + Adagrad"
    opt_params = {
        "lr_decay": "adagrad",
        "lr_decay_params": {"a": 1.0}
    }
    optimizer = FTRLOptimizer(**opt_params)
    params = {
        "optimizer": optimizer,
        "model_cls": FTRLLogRegModel,
        "verbose": False,
        "calc_full_loss_every_n_batches": 100,
    }
    rv_grid = {
        "batch_size": (50, 200)
    }
    cat_grid = {
        "num_iters": [3, 4, 5, 6, 7],
        "reg": (1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3),
        "l1": (1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3),
        "learning_rate": (1e-2, 1e-1, 1.0, 10, 50.0)
    }
    print "First shot"
    best_loss, params = find_best_params(train, valid, cat_grid, rv_grid, num_samples, params)
    rv_grid = {
        "learning_rate": get_sampling_interval(params["learning_rate"]),
        "batch_size": get_sampling_interval(params["batch_size"]),
        "reg": get_sampling_interval(params["reg"]),
        "l1": get_sampling_interval(params["l1"]),
    }
    cat_grid = {
        "num_iters": get_cat_sampling_distr(params["num_iters"]),
    }
    print "Second shot"
    best_loss2, params2 = find_best_params(train, valid, cat_grid, rv_grid, num_samples, params)


def exp_sgd_adagrad(train, valid, num_samples=NSHOTS):
    sys.stdout = open("log.%s" % inspect.currentframe().f_code.co_name, "w")
    print 80 * "="
    print "Pure SGD + Adagrad"
    opt_params = {
        "lr_decay": "adagrad",
        "lr_decay_params": {"a": 1.0}
    }
    optimizer = SGDOptimizer(**opt_params)
    params = {
        "optimizer": optimizer,
        "verbose": False,
        "calc_full_loss_every_n_batches": 100,
    }
    rv_grid = {
        "batch_size": (50, 200)
    }
    cat_grid = {
        "num_iters": [3, 4, 5, 6, 7],
        "reg": (1e-7, 1e-6, 1e-5, 1e-4, 1e-3),
        "learning_rate": (1e-2, 1e-1, 1.0, 10, 50.0)
    }
    print "First shot"
    best_loss, params = find_best_params(train, valid, cat_grid, rv_grid, num_samples, params)
    rv_grid = {
        "learning_rate": get_sampling_interval(params["learning_rate"]),
        "batch_size": get_sampling_interval(params["batch_size"]),
        "reg": get_sampling_interval(params["reg"]),
    }
    cat_grid = {
        "num_iters": get_cat_sampling_distr(params["num_iters"]),
    }
    print "Second shot"
    best_loss2, params2 = find_best_params(train, valid, cat_grid, rv_grid, num_samples, params)


def exp_svrg_adagrad(train, valid, num_samples=NSHOTS):
    sys.stdout = open("log.%s" % inspect.currentframe().f_code.co_name, "w")
    print 80 * "="
    print "SVRG + Adagrad"
    opt_params = {
        "lr_decay": "adagrad",
        "lr_decay_params": {"a": 1.0}
    }
    optimizer = SVRGOptimizer(**opt_params)
    params = {
        "model_cls": SVRGLogRegModel,
        "optimizer": optimizer,
        "verbose": False,
        "calc_full_loss_every_n_batches": 100,
    }
    rv_grid = {
        "batch_size": (50, 200)
    }
    cat_grid = {
        "num_iters": [3, 4, 5, 6, 7],
        "reg": (1e-7, 1e-6, 1e-5, 1e-4, 1e-3),
        "learning_rate": (1e-2, 1e-1, 1.0, 10, 50.0)
    }
    print "First shot"
    best_loss, params = find_best_params(train, valid, cat_grid, rv_grid, num_samples, params)
    rv_grid = {
        "learning_rate": get_sampling_interval(params["learning_rate"]),
        "batch_size": get_sampling_interval(params["batch_size"]),
        "reg": get_sampling_interval(params["reg"]),
    }
    cat_grid = {
        "num_iters": get_cat_sampling_distr(params["num_iters"]),
    }
    print "Second shot"
    best_loss2, params2 = find_best_params(train, valid, cat_grid, rv_grid, num_samples, params)

if __name__ == "__main__":

    train_df = pd.read_csv('./data/train.csv')
    train_df.Prediction.value_counts(normalize=True)
    review_summaries = list(train_df['Reviews_Summary'].values)
    vectorizer = TfidfVectorizer()
    tfidfed = vectorizer.fit_transform(review_summaries)
    X = tfidfed
    y = train_df.Prediction.values
    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.7, random_state=42)
    train = Dataset(X_train, y_train)
    valid = Dataset(X_test, y_test)

    pool = []
    for fname in (exp_sgd, exp_sgd_lr_decay, exp_sgd_adagrad, exp_ftrl_adagrad, exp_svrg_adagrad):
        p = mp.Process(target=fname, args=(train, valid))
        p.start()
        pool.append(p)
    for p in pool:
        p.join()

import numpy as np
from scipy import sparse

from data_iter import SimpleDataIter, Dataset
from opt import *
from model import *


class LogisticRegression(object):
    def __init__(self):
        self.loss_history = None
        self.opt = None
        self.model = None
        self.calc_full_loss_every_n_batches = 1

    def _train(self, diter, num_iters=100, num_steps=None, verbose=False):
        self.loss_history = []
        cnt = 0
        for it in xrange(num_iters):
            self.opt.on_iter_begin(it, diter, self.model)
            diter.reset()
            for batch in diter:
                cnt += 1
                if verbose and cnt % self.calc_full_loss_every_n_batches == 0:
                    # loss calculation is not sparse due to regularization
                    loss, _ = self.loss(batch.X, batch.y)
                    print 'iteration %d from %d, instance %d: loss %f' % (it, num_iters, cnt, loss)
                    self.loss_history.append(loss)
                else:
                    loss, _ = self.loss(batch.X, batch.y, only_data_loss=True)
                self.opt.step(self.model)

                if num_steps and cnt >= num_steps:
                    break
            self.opt.on_iter_end(it, diter, self.model)

    def train(self, X, y, learning_rate=1e-3, reg=1e-5, l1=0.0, num_iters=1,
              batch_size=200, optimizer=None, model=None, model_cls=None,
              verbose=False, calc_full_loss_every_n_batches=1, num_steps=None):
        """
        Train this classifier using stochastic gradient descent.

        Inputs:
        - X: N x D array of training data. Each training point is a D-dimensional
             column.
        - y: 1-dimensional array of length N with labels 0-1, for 2 classes.
        - learning_rate: (float) learning rate for optimization.
        - reg: (float) regularization strength.
        - num_iters: (integer) number of steps to take when optimizing
        - batch_size: (integer) number of training examples to use at each step.
        - verbose: (boolean) If true, print progress during optimization.

        Outputs:
        A list containing the value of the loss function at each training iteration.
        """
        # Add a column of ones to X for the bias sake.
        X = LogisticRegression.append_biases(X)
        self.calc_full_loss_every_n_batches = calc_full_loss_every_n_batches

        if not self.model:
            if optimizer is None:
                self.opt = SGDOptimizer()
            else:
                self.opt = optimizer
            if model_cls:
                self.model = model_cls(X.shape[1], lr=learning_rate, l2=reg, l1=l1, data_shape=X.shape)
            elif model:
                self.model = model
            else:
                self.model = LogRegModel(X.shape[1], lr=learning_rate, l2=reg, data_shape=X.shape)
            self.model.init()
            self.opt.init_model(self.model)

        diter = SimpleDataIter(batch_size=batch_size, dataset=Dataset(X, y))
        self._train(diter, num_iters=num_iters, verbose=verbose, num_steps=None)
        return self

    def train2(self, diter, learning_rate=1e-3, reg=1e-5, num_iters=100,
               batch_size=200, verbose=False):
        """
        Memory-friendly version of train
        """
        raise NotImplementedError

    def predict_proba(self, X, append_bias=False):
        """
        Use the trained weights of this linear classifier to predict probabilities for
        data points.

        Inputs:
        - X: N x D array of data. Each row is a D-dimensional point.
        - append_bias: bool. Whether to append bias before predicting or not.

        Returns:
        - y_proba: Probabilities of classes for the data in X. y_pred is a 2-dimensional
          array with a shape (N, 2), and each row is a distribution of classes [prob_class_0, prob_class_1].
        """
        if append_bias:
            X = LogisticRegression.append_biases(X)

        p = self.model.predict_proba(X)
        y_proba = np.vstack([1 - p, p]).T
        return y_proba

    def predict(self, X):
        """
        Use the ```predict_proba``` method to predict labels for data points.
        Inputs:
        - X: N x D array of training data. Each column is a D-dimensional point.

        Returns:
        - y_pred: Predicted labels for the data in X. y_pred is a 1-dimensional
          array of length N, and each element is an integer giving the predicted
          class.
        """
        y_proba = self.predict_proba(X, append_bias=True)
        y_pred = y_proba.argmax(axis=1)
        return y_pred

    def loss(self, X, y, only_data_loss=False):
        """Logistic Regression loss function.
        Do forward pass in LR model, store examples probabilities and gradients on model instance.
        Calculate loss and gradients
        Inputs:
        - X: N x D array of data. Data are D-dimensional rows
        - y: 1-dimensional array of length N with labels 0-1, for 2 classes
        - full_loss: True - calculate data + regularization loss, False - only data-loss
        Returns:
        a tuple of:
        - loss as single float
        - data gradient with respect to weights w; an array of same shape as w
        """
        loss, g = self.model.loss(X, y, only_data_loss=only_data_loss)
        return loss, g

    @staticmethod
    def append_biases(X):
        # WTF: implicit conversion to sparse format should be done somewhere else.
        return sparse.hstack((X, np.ones(X.shape[0])[:, np.newaxis])).tocsr()

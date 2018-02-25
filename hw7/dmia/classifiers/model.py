import scipy
from scipy.sparse import csr_matrix
import numpy as np

__all__ = "LogRegModel SparseLogRegModel".split()


class Model(object):
    pass


class LogRegModel(Model):
    """
    Container for model parameters - both explicit and latent, required for
    optimization algorithm. We are mixing here internals of model and optimization
    algorithm in single class, things which are normally thought of as independent entities.
    However, such controlled abstraction leak gives us possibility to fully utilize sparsity
    in data for efficient computation.
    """

    def __init__(self, dim, lr=1e-3, l2=0.0):
        self.dim = dim
        self.l2 = l2
        self.w = None  # weight vector. last weight = bias
        self.p = None  # predictions
        self.g = None  # data gradient
        self.lr = lr
        self.lr_coeff = 1.0

    def init(self):
        if self.w is None:
            self.w = np.random.randn(self.dim) * 0.01

    def predict_proba(self, X):
        self.p = scipy.special.expit(X.dot(self.w))
        return self.p

    def loss(self, X, y, only_data_loss=False):
        p = self.predict_proba(X)
        loss = -np.inner(y, np.log(p)) - np.inner((1 - y), np.log(1 - p))
        # XXX: do we need a safer/faster log here? profile
        if not only_data_loss:
            loss += self.l2 * self.w[:-1].dot(self.w[:-1])
        self.g = (p - y) * X  # average data gradient
        num_train = X.shape[0]
        self.g /= num_train
        loss /= num_train
        return loss, self.g


class SparseLogRegModel(Model):
    """
    Logistic regression model with parameters decomposed into scale scalar and
    scale-free parameter vector. This is a common trick to have sparse parameter updates
    in sgd with quadratic regularization.
    """
    def __init__(self, dim, l2=0.0, sparse_w=False, sparse_g=False):
        self.dim = dim
        self.l2 = 0.0
        self.scale = 1.0
        self.x = None
        self.p = None  # predictions
        self.g = None  # data gradient
        self.sparse_w = sparse_w
        self.sparse_g = sparse_g
        self.lr = 1.0

    def init(self):
        if self.x is None:
            if self.sparse_w:
                self.x = csr_matrix(np.random.randn(self.dim) * 0.01)
            else:
                self.x = np.random.randn(self.dim) * 0.01

    @property
    def w(self):
        return self.scale * self.x

    def predict_proba(self, X):
        self.p = scipy.special.expit(self.scale * X.dot(self.x))
        return self.p

    def loss(self, X, y, only_data_loss=False):
        p = self.predict_proba(X)
        loss = -np.inner(y, np.log(p)) - np.inner((1 - y), np.log(1 - p))
        # XXX: do we need a safer/faster log here? profile
        if not only_data_loss:
            loss += self.l2 * self.w[:-1].dot(self.w[:-1])
        self.g = (p - y) * X  # average data gradient
        if self.sparse_g:
            self.g = csr_matrix(self.g)

        num_train = X.shape[0]
        self.g /= num_train
        loss /= num_train
        return loss, self.g


class FTRLLogRegModel(Model):
    def __init__(self):
        self.w = None
        self.z = None


class SVRGLogRegModel(Model):
    pass
import scipy
from scipy.sparse import csr_matrix
import numpy as np

__all__ = ["LogRegModel", "SparseLogRegModel", "FTRLLogRegModel", "SVRGLogRegModel"]


class Model(object):
    def __init__(self, dim, **kwargs):
        raise NotImplementedError
    def init(self):
        raise NotImplementedError
    def predict_proba(self, X, w=None):
        raise NotImplementedError
    def loss(self, X, y, only_data_loss=False):
        raise  NotImplementedError


class LogRegModel(Model):
    """
    Container for model parameters - both explicit and latent, required for
    optimization algorithm.
    """
    NAME = "logreg"

    def __init__(self, dim, **kwargs):
        self.dim = dim
        self.data_shape = kwargs.get("data_shape", (None, None))
        self.l2 = kwargs.get("l2", 0.0)
        self.l1 = kwargs.get("l1", 0.0)
        self.lr = kwargs.get("lr", 1e-3)
        self.w = None  # weight vector. last weight = bias
        self.p = None  # predictions
        self.g = None  # data gradient
        self.lr_coeff = 1.0

    def init(self):
        if self.w is None:
            # model.w = np.random.randn(self.dim) * 0.01
            self.w = np.zeros(self.dim)

    def predict_proba(self, X, w=None):
        weights = self.w if w is None else w
        self.p = scipy.special.expit(X.dot(weights))
        return self.p

    def loss(self, X, y, only_data_loss=False):
        p = self.predict_proba(X)
        loss = -np.inner(y, np.log(p)) - np.inner((1 - y), np.log(1 - p))
        # XXX: do we need a safer/faster log here? profile
        if not only_data_loss:
            loss += self.l2 * self.w[:-1].dot(self.w[:-1])
        self.g = (p - y) * X  # average data gradient, but numpy makes it a dense vector
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
    NAME = "sparse_logreg"

    def __init__(self, dim, **kwargs):
        self.dim = dim
        self.l2 = kwargs.get("l2", 0.0)
        self.l1 = kwargs.get("l1", 0.0)
        self.lr = kwargs.get("lr", 1e-3)
        self.sparse_g = kwargs.get("sparse_g")
        self.sparse_w = kwargs.get("sparse_w")
        self.scale = 1.0
        self.x = None
        self.p = None  # predictions
        self.g = None  # data gradient
        self.lr_coeff = 1.0

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
        self.g = (p - y) * X  # average data gradient, sparse in reality, but numpy makes it a dense vector
        if self.sparse_g:
            self.g = csr_matrix(self.g)

        num_train = X.shape[0]
        self.g /= num_train
        loss /= num_train
        return loss, self.g


class FTRLLogRegModel(LogRegModel):
    """
    https://static.googleusercontent.com/media/research.google.com/ru//pubs/archive/41159.pdf
    """
    NAME = "ftrl_logreg"

    def __init__(self, dim, **kwargs):
        super(FTRLLogRegModel, self).__init__(dim, **kwargs)
        self.alpha = kwargs.get("alpha", 1.0)
        self.beta = kwargs.get("beta", 1.0)

    def init(self):
        self.n = np.zeros(self.dim)
        self.z = np.zeros(self.dim)
        self.w = np.zeros(self.dim)

    def update_w(self):
        c = (self.beta + np.sqrt(self.n)) / self.alpha + self.l2
        # all ops below are not sparse (we ignore the data sparsity)
        zero = np.abs(self.z) < self.l1
        nonzero = ~zero
        self.w[zero] = 0
        self.w[nonzero] = -(self.z[nonzero] - self.l1 * np.sign(self.z[nonzero])) / c[nonzero]


    def loss(self, X, y, only_data_loss=False):
        self.update_w()
        loss, g = super(FTRLLogRegModel, self).loss(X, y, only_data_loss=only_data_loss)
        return loss, g


class SVRGLogRegModel(LogRegModel):
    """
    https://papers.nips.cc/paper/4937-accelerating-stochastic-gradient-descent-using-predictive-variance-reduction.pdf
    """
    NAME = "svrg_logreg"

    def __init__(self, dim, **kwargs):
        super(SVRGLogRegModel, self).__init__(dim, **kwargs)

    def init(self):
        self.g_sum = np.zeros(self.dim)
        self.g0 = np.zeros(self.dim)
        self.w0 = np.zeros(self.dim)
        self.w = np.zeros(self.dim)

    def loss(self, X, y, only_data_loss=False, svrg=True):
        p = self.predict_proba(X)
        loss = -np.inner(y, np.log(p)) - np.inner((1 - y), np.log(1 - p))
        # XXX: do we need a safer/faster log here? profile
        if not only_data_loss:
            loss += self.l2 * self.w[:-1].dot(self.w[:-1])

        # average data gradient, but numpy makes it a dense vector
        self.g = (p - y) * X
        num_train = X.shape[0]
        self.g /= num_train
        loss /= num_train
        # calculate gradient using stored weights from previous iteration
        if svrg:
            p0 = self.predict_proba(X, w=self.w0)
            self.g0 = (p0 - y) * X
            self.g0 /= num_train

        return loss, self.g

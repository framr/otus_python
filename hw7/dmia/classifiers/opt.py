import numpy as np

from lrdecay import LR_DECAY_MAPPING

__all__ = ["SVRGOptimizer", "FTRLOptimizer", "SGDOptimizer", "SparseSGDOptimizer"]


class Optimizer(object):
    def __init__(self, lr_decay=None, lr_decay_params=None):
        self.lr_decay_type = lr_decay
        self.lr_decay_params = lr_decay_params or {}
        self.lr_decay = None

    def init_model(self, model):
        if self.lr_decay:
            self.lr_decay = LR_DECAY_MAPPING[self.lr_decay_type](self.lr_decay_params)
            self.lr_decay.init(model)

    def step(self, model):
        raise NotImplementedError

    def on_iter_end(self, it, diter, model):
        pass

    def on_iter_begin(self, it, diter, model):
        pass


class SGDOptimizer(Optimizer):
    def step(self, model):
        l2 = model.l2 / model.data_shape[0]
        lr = model.lr * model.lr_coeff
        full_g = model.g
        full_g[:-1] += 2 * l2 * model.w[:-1]
        model.w -= lr * full_g

        if self.lr_decay:
            self.lr_decay.step(model)

class SparseSGDOptimizer(Optimizer):
    def step(self, model):
        l2 = model.l2 / model.data_shape[0]
        lr = model.lr * model.lr_coeff
        new_scale = model.scale * (1 - 2 * lr * l2)
        lr_eff = (lr / model.scale) / (1 - 2 * lr * l2)
        model.x[:-1] -= lr_eff * model.g[:-1]
        model.x[-1] = (model.scale * model.x[-1] - lr * model.g[-1]) / new_scale
        model.scale = new_scale

        if self.lr_decay:
            self.lr_decay.step(model)


class FTRLOptimizer(Optimizer):
    """
    https://static.googleusercontent.com/media/research.google.com/ru//pubs/archive/41159.pdf
    """
    def __init__(self, alpha=1.0, beta=1.0, lr_decay=None, lr_decay_params=None):
        super(FTRLOptimizer, self).__init__(lr_decay=lr_decay, lr_decay_params=lr_decay_params)
        self.alpha = alpha
        self.beta = beta

    def init_model(self, model):
        if model.NAME not in ("ftrl_logreg"):
            raise ValueError("ftrl optimizer should be used in conjunction with FTRL model")

    def step(self, model):
        s = (np.sqrt(model.n + model.g * model.g) - np.sqrt(model.n)) / model.alpha
        model.z += model.g - s * model.w
        model.n += model.g * model.g


class SVRGOptimizer(Optimizer):
    """
    https://papers.nips.cc/paper/4937-accelerating-stochastic-gradient-descent-using-predictive-variance-reduction.pdf
    """
    def init_model(self, model):
        super(SVRGOptimizer, self).__init__(model)
        if model.NAME not in ("svrg_logreg"):
            raise ValueError("svrg optimizer should be used in conjunction with svrg model")

    def step(self, model):
        l2 = model.l2 / model.data_shape[0]
        lr = model.lr * model.lr_coeff
        g = model.g
        g[:-1] += 2 * l2 * model.w[:-1]
        model.w -= lr * (g - model.g0 + model.g_sum)
        if self.lr_decay:
            self.lr_decay.step(model)

    def on_iter_begin(self, it, diter, model):
        diter.reset()
        model.g_sum = np.zeros(model.dim)
        loss_sum = 0
        model.w0[:] = model.w[:]
        for batch in diter:
            loss, g = model.loss(batch.X, batch.y, svrg=False)
            model.g_sum += g * batch.X.shape[0]
            loss_sum += loss * batch.X.shape[0]
        model.g_sum /= model.data_shape[0]

    def on_iter_end(self, it, diter, model):
        pass

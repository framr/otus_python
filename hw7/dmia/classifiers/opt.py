from math import pow


__all__ = ["FTRLOptimizer", "SGDOptimizer"]



class LRDecay(object):
    def step(self, model):
        raise NotImplementedError


class TPowerLRDecay(LRDecay):
    def __init__(self, t_power=0.5, a=0.0):
        self.t_power = t_power
        self.a = a
        self.t = 1  # time counter

    def step(self, model):
        model.lr_coeff = 1.0 / (self.a + pow(self.t, self.t_power))
        self.t += 1


class Adagrad(LRDecay):
    def __init__(self):



LR_DECAY_MAPPING = {
    "t_power": TPowerLRDecay,
    "adagrad": Adagrad
}


class Optimizer(object):
    def __init__(self, lr_decay=None, lr_decay_params=None):
        self.lr_decay = lr_decay
        self.lr_decay_params = lr_decay_params or {}

    def step(self):
        raise NotImplementedError


class SGDOptimizer(Optimizer):
    def step(self, X, y, model):
        l2 = model.l2 / X.shape[0]
        lr = model.lr * model.lr_coeff
        full_g = model.g
        full_g[:-1] += 2 * l2 * model.w[:-1]
        model.w -= lr * full_g


class SparseSGDOptimizer(Optimizer):
    def step(self, X, y, model):
        l2 = model.l2 / X.shape[0]
        lr = model.lr * model.lr_coeff
        new_scale = model.scale * (1 - 2 * lr * l2)
        lr_eff = (lr / model.scale) / (1 - 2 * lr * l2)
        model.x[:-1] -= lr_eff * model.g[:-1]
        model.x[-1] = (model.scale * model.x[-1] - lr * model.g[-1]) / new_scale
        model.scale = new_scale


class FTRLOptimizer(Optimizer):
    pass


class SVRGOptimizer(Optimizer):
    pass

__all__ = ["FTRLOptimizer", "SGDOptimizer"]


class Optimizer(object):
    def __init__(self, lr):
        self.lr0 = lr

    def step(self):
        raise NotImplementedError


class SparseSGDOptimizer(Optimizer):
    def step(self, X, y, model):
        l2 = model.l2 / X.shape[0]
        lr = model.lr * self.lr0
        new_scale = model.scale * (1 - 2 * lr * l2)
        lr_eff = (lr / model.scale) / (1 - 2 * lr * l2)
        model.x[:-1] -= lr_eff * model.g[:-1]
        model.x[-1] = (model.scale * model.x[-1] - lr * model.g[-1]) / new_scale
        model.scale = new_scale


class SGDOptimizer(Optimizer):
    def step(self, X, y, model):
        l2 = model.l2 / X.shape[0]
        lr = self.lr0 * self.lr
        model.w -= lr * model.g
        model.w[:-1] -= 2 * lr * l2 * model.w[:-1] / X.shape[0]


class FTRLOptimizer(Optimizer):
    pass


class SVRGOptimizer(Optimizer):
    pass

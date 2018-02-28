import numpy as np
from math import pow

__all__ = ["TPowerLRDecay", "Adagrad"]


class LRDecay(object):
    def init_model(self, model):
        pass

    def step(self, model):
        raise NotImplementedError


class TPowerLRDecay(LRDecay):
    def __init__(self, t_power=0.5, a=1.0):
        self.t_power = t_power
        self.a = a
        self.t = 1  # time counter

    def step(self, model):
        model.lr_coeff = 1.0 / (self.a + pow(self.t, self.t_power))
        self.t += 1


class Adagrad(LRDecay):
    def __init__(self, a=1.0):
        self.a = a
        self.t = 1.0

    def init_model(self, model):
        if model.NAME not in ("logreg", "sparse_logreg"):
            raise ValueError("adagrad currently does not support %s model" % model.NAME)
        model.g2_sum = np.zeros(model.dim)

    def step(self, model):
        # XXX: check that it correctly works with sparse gradients
        model.lr_coeff = 1.0 / (self.a + np.sqrt(model.g2_sum))
        model.g2_sum += model.g * model.g


LR_DECAY_MAPPING = {
    "t_power": TPowerLRDecay,
    "adagrad": Adagrad
}

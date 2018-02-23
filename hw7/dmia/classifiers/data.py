from collections import namedtuple
import numpy as np

Dataset = namedtuple("Dataset", "X y")


class DataIter(object):
    def __init__(self, batch_size=128, dataset=None, datastream=None):
        self.batch_size = batch_size
        self.dataset = dataset
        self.datastream = datastream

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError


class SimpleDataIter(object):
    def __next__(self):
        indices = np.random.choice(self.dataset.X.shape[0], replace=True)
        return Dataset(self.dataset.X[indices], self.dataset.y[indices])

    def reset(self):
        pass

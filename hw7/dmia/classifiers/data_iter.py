from collections import namedtuple
import numpy as np

Dataset = namedtuple("Dataset", "X y")


class DataIter(object):
    def __init__(self, batch_size=128, dataset=None, datastream=None):
        self.batch_size = batch_size
        self.dataset = dataset
        self.datastream = datastream

    def __iter__(self):
        raise NotImplementedError

    def next(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError


class SimpleDataIter(DataIter):
    def __init__(self, batch_size=128, dataset=None, max_examples=None):
        super(SimpleDataIter, self).__init__(batch_size=batch_size, dataset=dataset)
        self.num_examples = 0
        self.dataset_size = dataset.X.shape[0]
        self.max_examples = max_examples or self.dataset_size

    def __iter__(self):
        return self

    def next(self):
        if self.num_examples >= self.max_examples:
            raise StopIteration
        indices = np.random.choice(self.dataset_size, self.batch_size, replace=True)
        self.num_examples += len(indices)
        return Dataset(self.dataset.X[indices], self.dataset.y[indices])

    def reset(self):
        self.num_examples = 0

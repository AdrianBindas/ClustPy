import numpy as np
from cluspy.subspace.SubKmeans import SubKmeans
from cluspy.nonredundant.NrKmeans import _mdl_costs


def _get_n_clusters(X, max_n_clusters, add_noise_space, repetitions, mdl_for_noisespace,
                    outliers, max_iter, random_state):
    n_clusters = 2
    min_costs = np.inf
    best_subkmeans = None
    while n_clusters <= max_n_clusters:
        tmp_min_costs = np.inf
        tmp_best_subkmeans = None
        for i in range(repetitions):
            subkmeans = SubKmeans(n_clusters, add_noise_space, mdl_for_noisespace, outliers, max_iter, random_state)
            subkmeans.fit(X)
            costs = _mdl_costs(X, subkmeans)[0]
            if costs < tmp_min_costs:
                tmp_min_costs = costs
                tmp_best_subkmeans = subkmeans
        if tmp_min_costs < min_costs:
            min_costs = tmp_min_costs
            best_subkmeans = tmp_best_subkmeans
            n_clusters += 1
        else:
            break
    return best_subkmeans


class MDLSubKmeans():

    def __init__(self, max_n_clusters=np.inf, add_noise_space=True, repetitions=10, mdl_for_noisespace=True,
                 outliers=False,
                 max_iter=300, random_state=None):
        self.max_n_clusters = max_n_clusters
        self.add_noise_space = add_noise_space
        self.repetitions = repetitions
        self.mdl_for_noisespace = mdl_for_noisespace
        self.outliers = outliers
        self.max_iter = max_iter
        self.random_state = random_state

    def fit(self, X):
        subkmeans = _get_n_clusters(X, self.max_n_clusters, self.add_noise_space, self.repetitions,
                                    self.mdl_for_noisespace,
                                    self.outliers, self.max_iter, self.random_state)
        self.labels = subkmeans.labels
        self.centers = subkmeans.centers
        self.n_clusters = subkmeans.n_clusters
        self.V = subkmeans.V
        self.P = subkmeans.P
        self.m = subkmeans.m

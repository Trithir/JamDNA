import faiss
import numpy as np

class Index:
    def __init__(self, dim=128):
        self.index = faiss.IndexFlatL2(dim)

    def add(self, vecs):
        self.index.add(vecs.astype("float32"))

    def search(self, vec, k=5):
        D, I = self.index.search(vec.astype("float32"), k)
        return D, I

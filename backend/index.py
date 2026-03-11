import faiss
import numpy as np

class Index:

	def __init__(self, dim=256):
		self.index = faiss.IndexFlatIP(dim)

	def add(self, vecs):
		vecs = vecs.astype("float32")
		faiss.normalize_L2(vecs)
		self.index.add(vecs)

	def search(self, vec, k=5):
		vec = vec.astype("float32")
		faiss.normalize_L2(vec)
		D, I = self.index.search(vec, k)
		return D, I

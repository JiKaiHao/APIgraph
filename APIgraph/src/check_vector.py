# check_vectors.py
import numpy as np
import os

def load(path):
    return np.load(path)

X_mal = load(r'vectors/graph_vector\mal_2016.npy')
X_ben = load(r'vectors/graph_vector\ben_2016.npy')
#此处根据需要修改，增加或者减少

print(f"Malware samples: {len(X_mal)} | Benign samples: {len(X_ben)}")
print(f"Feature dim: {X_mal.shape[1]}")

# 统计每个样本非零特征数
mal_nonzero = np.sum(X_mal, axis=1)
ben_nonzero = np.sum(X_ben, axis=1)

print(f"Malware avg non-zero: {mal_nonzero.mean():.1f} ± {mal_nonzero.std():.1f}")
print(f"Benign  avg non-zero: {ben_nonzero.mean():.1f} ± {ben_nonzero.std():.1f}")

# 看是否有交集
common_features = np.sum(np.logical_and(X_mal.sum(axis=0), X_ben.sum(axis=0)))
print(f"Common active clusters: {common_features}")

# 看是否有恶意独有簇
mal_unique = np.sum(X_mal.sum(axis=0) > 0) - common_features
ben_unique = np.sum(X_ben.sum(axis=0) > 0) - common_features
print(f"Malware unique clusters: {mal_unique}")
print(f"Benign unique clusters: {ben_unique}")
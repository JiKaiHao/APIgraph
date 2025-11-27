#map2000.py
import pickle

with open('res/method_cluster_mapping_2000.pkl', 'rb') as f:
    mapping = pickle.load(f)

print("前 10 个 key 示例：")
for i, key in enumerate(list(mapping.keys())[:10]):
    print(f"  {i+1}. {key}")
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import numpy as np
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False
DIRECT_VECTOR_DIR = "vectors/direct_vector"
GRAPH_VECTOR_DIR = "vectors/graph_vector"
TEST_YEAR = 2022
TRAIN_YEARS = [2016, 2017, 2018, 2019, 2020, 2021]

svm_params = {'kernel': 'linear', 'C': 1.0, 'class_weight': 'balanced', 'probability': True, 'random_state': 42}
rf_params = {'n_estimators': 300, 'class_weight': 'balanced', 'random_state': 42, 'n_jobs': -1}


def load_and_align(dir_path, year, kind="mal", target_dim=6486):
    path = os.path.join(dir_path, f"{kind}_{year}.npy")
    if not os.path.exists(path):
        print(f"   [警告] 缺失: {path}")
        return np.zeros((0, target_dim), dtype=np.uint8)
    vec = np.load(path)
    if vec.shape[1] >= target_dim:
        return vec[:, :target_dim]
    else:
        pad = np.zeros((vec.shape[0], target_dim - vec.shape[1]), dtype=np.uint8)
        return np.hstack([vec, pad])


# 确定基准维度
print("正在确定基准维度（2016年）")
dim_2016 = load_and_align(DIRECT_VECTOR_DIR, 2016, "mal").shape[1]
print("加载并对齐 2022 测试集...")
X_test_dre = np.vstack([
    load_and_align(DIRECT_VECTOR_DIR, TEST_YEAR, "mal", dim_2016),
    load_and_align(DIRECT_VECTOR_DIR, TEST_YEAR, "ben", dim_2016)
])
y_test_dre = np.concatenate([
    np.ones(load_and_align(DIRECT_VECTOR_DIR, TEST_YEAR, "mal", dim_2016).shape[0]),
    np.zeros(load_and_align(DIRECT_VECTOR_DIR, TEST_YEAR, "ben", dim_2016).shape[0])
])

X_test_graph = np.vstack([
    np.load(os.path.join(GRAPH_VECTOR_DIR, f"mal_{TEST_YEAR}.npy")),
    np.load(os.path.join(GRAPH_VECTOR_DIR, f"ben_{TEST_YEAR}.npy"))
])
y_test_graph = np.concatenate([
    np.ones(np.load(os.path.join(GRAPH_VECTOR_DIR, f"mal_{TEST_YEAR}.npy")).shape[0]),
    np.zeros(np.load(os.path.join(GRAPH_VECTOR_DIR, f"ben_{TEST_YEAR}.npy")).shape[0])
])

print(f"测试集就绪 → Drebin {X_test_dre.shape} | APIgraph {X_test_graph.shape}\n")

print("单一年份的训练")
def train_eval(model, X_tr, y_tr, X_te, y_te):
    if X_tr.shape[0] == 0 or X_tr.shape[1] == 0:
        return 0.0, 0.0, 0.0, 0.0
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    return (
        accuracy_score(y_te, pred),
        f1_score(y_te, pred, average='binary', zero_division=0),
        precision_score(y_te, pred, average='binary', zero_division=0),
        recall_score(y_te, pred, average='binary', zero_division=0)
    )


res = {
    'single': {'drebin': {'SVM': [], 'RF': [], 'ENS': []}, 'graph': {'SVM': [], 'RF': [], 'ENS': []}},
    'cum': {'drebin': {'SVM': [], 'RF': [], 'ENS': []}, 'graph': {'SVM': [], 'RF': [], 'ENS': []}}
}


for year in TRAIN_YEARS:
    print(f"\n仅用 {year} 年训练")

    # Drebin
    mal = load_and_align(DIRECT_VECTOR_DIR, year, "mal", dim_2016)
    ben = load_and_align(DIRECT_VECTOR_DIR, year, "ben", dim_2016)
    X_tr = np.vstack([mal, ben])
    y_tr = np.concatenate([np.ones(mal.shape[0]), np.zeros(ben.shape[0])])
    X_te = X_test_dre  # 已经对齐过

    svm = SVC(**svm_params)
    rf = RandomForestClassifier(**rf_params)
    ens = VotingClassifier(estimators=[('svm', SVC(**svm_params)), ('rf', RandomForestClassifier(**rf_params))],
                           voting='soft')

    acc_svm, f1_svm, _, _ = train_eval(svm, X_tr, y_tr, X_te, y_test_dre)
    acc_rf, f1_rf, _, _ = train_eval(rf, X_tr, y_tr, X_te, y_test_dre)
    acc_ens, f1_ens, _, _ = train_eval(ens, X_tr, y_tr, X_te, y_test_dre)

    res['single']['drebin']['SVM'].append(acc_svm)
    res['single']['drebin']['RF'].append(acc_rf)
    res['single']['drebin']['ENS'].append(acc_ens)

    print(f"   Drebin   | SVM: {acc_svm:.4f}  RF: {acc_rf:.4f}  ENS: {acc_ens:.4f}")

    # APIgraph
    mal_g = np.load(os.path.join(GRAPH_VECTOR_DIR, f"mal_{year}.npy"))
    ben_g = np.load(os.path.join(GRAPH_VECTOR_DIR, f"ben_{year}.npy"))
    X_g = np.vstack([mal_g, ben_g])
    y_g = np.concatenate([np.ones(mal_g.shape[0]), np.zeros(ben_g.shape[0])])

    acc_svm, f1_svm, _, _ = train_eval(svm, X_g, y_g, X_test_graph, y_test_graph)
    acc_rf, f1_rf, _, _ = train_eval(rf, X_g, y_g, X_test_graph, y_test_graph)
    acc_ens, f1_ens, _, _ = train_eval(ens, X_g, y_g, X_test_graph, y_test_graph)

    res['single']['graph']['SVM'].append(acc_svm)
    res['single']['graph']['RF'].append(acc_rf)
    res['single']['graph']['ENS'].append(acc_ens)

    print(f"   APIgraph | SVM: {acc_svm:.4f}  RF: {acc_rf:.4f}  ENS: {acc_ens:.4f}")
print("开始 累加训练模式（统一2016维度）")

cum_X_dre = None
cum_y_dre = None
cum_X_g = None
cum_y_g = None

for year in TRAIN_YEARS:
    print(f"\n从2016开始累加至 {year} 年")

    #无graph的累加训练
    mal = load_and_align(DIRECT_VECTOR_DIR, year, "mal", dim_2016)
    ben = load_and_align(DIRECT_VECTOR_DIR, year, "ben", dim_2016)
    X_year = np.vstack([mal, ben])
    y_year = np.concatenate([np.ones(mal.shape[0]), np.zeros(ben.shape[0])])

    cum_X_dre = X_year if cum_X_dre is None else np.vstack([cum_X_dre, X_year])
    cum_y_dre = y_year if cum_y_dre is None else np.concatenate([cum_y_dre, y_year])

    acc_svm, _, _, _ = train_eval(SVC(**svm_params), cum_X_dre, cum_y_dre, X_test_dre, y_test_dre)
    acc_rf, _, _, _ = train_eval(RandomForestClassifier(**rf_params), cum_X_dre, cum_y_dre, X_test_dre, y_test_dre)
    acc_ens, _, _, _ = train_eval(
        VotingClassifier(estimators=[('svm', SVC(**svm_params)), ('rf', RandomForestClassifier(**rf_params))],
                         voting='soft'),
        cum_X_dre, cum_y_dre, X_test_dre, y_test_dre)

    res['cum']['drebin']['SVM'].append(acc_svm)
    res['cum']['drebin']['RF'].append(acc_rf)
    res['cum']['drebin']['ENS'].append(acc_ens)
    print(f"   Drebin   | SVM: {acc_svm:.4f}  RF: {acc_rf:.4f}  ENS: {acc_ens:.4f}")

    # APIgraph 累加
    mal_g = np.load(os.path.join(GRAPH_VECTOR_DIR, f"mal_{year}.npy"))
    ben_g = np.load(os.path.join(GRAPH_VECTOR_DIR, f"ben_{year}.npy"))
    X_year_g = np.vstack([mal_g, ben_g])
    y_year_g = np.concatenate([np.ones(mal_g.shape[0]), np.zeros(ben_g.shape[0])])
    cum_X_g = X_year_g if cum_X_g is None else np.vstack([cum_X_g, X_year_g])
    cum_y_g = y_year_g if cum_y_g is None else np.concatenate([cum_y_g, y_year_g])

    acc_svm, _, _, _ = train_eval(SVC(**svm_params), cum_X_g, cum_y_g, X_test_graph, y_test_graph)
    acc_rf, _, _, _ = train_eval(RandomForestClassifier(**rf_params), cum_X_g, cum_y_g, X_test_graph, y_test_graph)
    acc_ens, _, _, _ = train_eval(
        VotingClassifier(estimators=[('svm', SVC(**svm_params)), ('rf', RandomForestClassifier(**rf_params))],
                         voting='soft'),
        cum_X_g, cum_y_g, X_test_graph, y_test_graph)

    res['cum']['graph']['SVM'].append(acc_svm)
    res['cum']['graph']['RF'].append(acc_rf)
    res['cum']['graph']['ENS'].append(acc_ens)
    print(f"   APIgraph | SVM: {acc_svm:.4f}  RF: {acc_rf:.4f}  ENS: {acc_ens:.4f}")

# 创建图片文件夹
os.makedirs("结果图片", exist_ok=True)

# 指标中英文对照
metrics = [
    ("Accuracy",     "准确率"),
    ("F1-Score",     "F1值"),
    ("Precision",    "精确率"),
    ("Recall",       "召回率")
]

modes = [
    ('single', '单年训练'),
    ('cum',    '累加训练')
]
#颜色不一样
styles = {
    'drebin': {'SVM': ('#d62728', '-',   'o'),
               'RF':  ('#ff7f0e', '--',  'v'),
               'ENS': ('#8c564b', '-.',  'D')},
    'graph':  {'SVM': ('#1f77b4', '-',   's'),
               'RF':  ('#2ca02c', '--',  '^'),
               'ENS': ('#9467bd', '-.',  'P')}
}
for mode_key, mode_name in modes:
    for eng_name, chn_name in metrics:
        plt.figure(figsize=(11, 7))
        idx = {"Accuracy":0, "F1-Score":1, "Precision":2, "Recall":3}[eng_name]
        all_vals = []

        # 画六条线
        for feat, feat_name in [('drebin', '无Graph'), ('graph', '有Graph')]:
            for clf in ['SVM', 'RF', 'ENS']:
                values = []
                for item in res[mode_key][feat][clf]:
                    values.append(item[idx] if isinstance(item, tuple) else item)
                all_vals.extend(values)

                color, ls, marker = styles[feat][clf]
                label = f"{feat_name} ({clf})"
                plt.plot(TRAIN_YEARS, values,
                         color=color, linestyle=ls, marker=marker,
                         linewidth=3.5, markersize=10, markeredgewidth=2,
                         label=label)

        #裁剪空白
        ymin, ymax = min(all_vals), max(all_vals)
        margin = (ymax - ymin) * 0.12
        plt.ylim(max(0.55, ymin - margin), min(1.0, ymax + margin))
        plt.title(f'{chn_name}对比 —— {mode_name}\n（以2022年为测试集）', fontsize=20, pad=25, fontweight='bold')
        plt.xlabel('训练数据截止年份', fontsize=16)
        plt.ylabel(chn_name, fontsize=16)
        plt.xticks(TRAIN_YEARS, fontsize=13)
        plt.yticks(fontsize=13)
        plt.grid(True, alpha=0.4, linestyle=':', linewidth=1.2)
        plt.legend(fontsize=14, framealpha=0.98, fancybox=True, shadow=True, loc='lower right')
        plt.tight_layout()
        filename = f"结果图片/{chn_name}_{mode_key}.png"
        plt.savefig(filename, dpi=500, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"已生成：{filename}")
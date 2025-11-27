#smali_extractor.py
"""
该脚本用于从反编译的Android应用代码中提取API调用特征，并将其转换为向量表示。
这些向量将用于机器学习模型的训练和测试。
主要功能包括：
1. 加载预定义的方法到簇的映射关系
2. 从smali代码中提取API调用
3. 将API调用转换为向量表示
4. 保存处理后的向量数据
"""
import os  # 提供与操作系统交互的功能
import re  # 用于正则表达式匹配
import pickle  # 用于对象的序列化和反序列化
import numpy as np  # 用于科学计算
from tqdm import tqdm  # 用于显示进度条

# 定义项目根路径和簇映射文件的路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CLUSTER_PATH = os.path.join(PROJECT_ROOT, 'res', 'method_cluster_mapping_2000.pkl')

# 加载簇映射文件
print(f"Loading cluster mapping from: {CLUSTER_PATH}")
with open(CLUSTER_PATH, 'rb') as f:
    METHOD_TO_CLUSTER = pickle.load(f)  # 从pickle文件中加载方法到簇的映射

NUM_CLUSTERS = 2000  # 定义簇的数量
print(f"Loaded {len(METHOD_TO_CLUSTER):,} methods → {NUM_CLUSTERS} clusters")

# 编译用于匹配API调用的正则表达式模式
INVOKE_PATTERN = re.compile(r'invoke-\w+[^,]+,\s*(L[^;]+;->[^(\s]+)')

def extract_apis_from_smali_content(content: str) -> set:
    """
    从smali代码内容中提取API调用
    该函数通过分析smali代码内容，识别并提取所有Android框架相关的API调用。
    使用正则表达式匹配invoke类型的指令，然后解析出类路径和方法名。
    参数:
        content: smali代码内容字符串，包含要分析的smali代码
    返回:
        包含所有API调用的集合
    """
    apis = set()
    for line in content.splitlines():
        match = INVOKE_PATTERN.search(line)  # 使用正则表达式匹配API调用
        if match:
            full = match.group(1)
            # 只处理Android框架相关的API
            if full.startswith(('Landroid/', 'Ljava/', 'Ljavax/')):
                class_path = full.split(';->')[0][1:]  # 去 L
                class_path = class_path.replace('/', '.')  # / → .
                method_name = full.split(';->')[1].split('(')[0]
                if method_name == '<init>':
                    method_name = 'init'  # 或 '__init__'，测试哪个对
                api_key = f"{class_path}.{method_name}"
                apis.add(api_key)
    return apis

def process_directory(decompiled_dir: str, output_npy: str):
    """
    处理反编译APK目录，提取API特征并保存为向量文件
    参数:
        decompiled_dir (str): 反编译APK的根目录路径
        output_npy (str): 输出的.npy文件路径
    """
    # 获取目录下所有子目录（即每个反编译的APK目录）
    subdirs = [os.path.join(decompiled_dir, d) for d in os.listdir(decompiled_dir)
               if os.path.isdir(os.path.join(decompiled_dir, d))]

    # 如果没有找到子目录，打印警告并返回
    if not subdirs:
        print(f"[Warning] No decompiled APKs in {decompiled_dir}")
        return

    vectors = []
    print(f"\nProcessing {len(subdirs)} decompiled APKs in {decompiled_dir}")
    # 使用tqdm进度条处理每个子目录
    for subdir in tqdm(subdirs, desc=os.path.basename(decompiled_dir)):
        # 定位到smali目录
        smali_dir=os.path.join(subdir, 'smali')
        # 如果smali目录不存在，创建全零向量
        if not os.path.exists(smali_dir):
            print(f"  [Warning] No smali in {os.path.basename(subdir)}")
            vec=np.zeros(NUM_CLUSTERS, dtype=np.int8)
        else:
            # 存储所有API的集合
            all_apis = set()
            # 遍历smali目录下的所有.smali文件
            for root, _, files in os.walk(smali_dir):
                for f in files:
                    if f.endswith('.smali'):
                        # 读取文件内容并提取API
                        with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as ff:
                            content=ff.read()
                            apis=extract_apis_from_smali_content(content)
                            all_apis.update(apis)
            # 创建特征向量
            vec = np.zeros(NUM_CLUSTERS, dtype=np.int8)
            hit = 0
            # 将API映射到特征向量
            for api in all_apis:
                if api in METHOD_TO_CLUSTER:
                    vec[METHOD_TO_CLUSTER[api]] = 1
                    hit += 1
            print(f"  {os.path.basename(subdir)}: {len(all_apis)} APIs → {hit} hits")
        vectors.append(vec)
    # 保存特征向量到.npy文件
    np.save(output_npy, np.array(vectors))
    print(f"Saved {output_npy}")

if __name__ == '__main__':
    # 创建输出目录
    os.makedirs("vectors", exist_ok=True)
    # 处理训练集和测试集的恶意和良性APK
    process_directory(r'D:\code\python\APIgraph\APIGraph-master\src\decompiled\bad_2016',  'vectors/graph_vector/mal_2016.npy')
    process_directory(r'D:\code\python\APIgraph\APIGraph-master\src\decompiled\good_2016', 'vectors/graph_vector/X_ben_2016.npy')
    process_directory(r'D:\code\python\APIgraph\APIGraph-master\src\decompiled\bad_2017',   'vectors/graph_vector/mal_2017.npy')
    process_directory(r'D:\code\python\APIgraph\APIGraph-master\src\decompiled\good_2017',  'vectors/graph_vector/ben_2017.npy')
    #你可以根据需要增加或者减少
    print("\n所有向量生成完毕！现在运行 check_vector.py")
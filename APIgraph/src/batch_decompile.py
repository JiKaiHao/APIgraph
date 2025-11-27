# batch_decompile.py
"""
批量反编译APK文件的脚本
使用apktool工具对指定目录下的所有APK文件进行反编译
并将结果输出到指定的目录结构中
"""
import os
import subprocess
from tqdm import tqdm

def decompile_apk(apk_path, output_dir):
    """
    使用apktool反编译单个APK文件
    参数:
        apk_path (str): 要反编译的APK文件路径
        output_dir (str): 反编译结果的输出目录
    """
    cmd=["apktool.bat", "d", apk_path, "-f", "-o", output_dir]
    # 执行反编译命令，不显示输出信息
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def batch_decompile(apk_dir, decompiled_root):
    """
    批量反编译指定目录下的所有APK文件
    参数:
        apk_dir (str): 包含APK文件的源目录
        decompiled_root (str): 反编译结果的根目录
    """
    # 创建输出目录（如果不存在）
    os.makedirs(decompiled_root, exist_ok=True)
    # 获取目录下所有APK文件
    apks = [f for f in os.listdir(apk_dir) if f.endswith('.apk')]
    # 使用tqdm显示进度条
    for apk in tqdm(apks, desc=os.path.basename(apk_dir)):
        apk_path=os.path.join(apk_dir, apk)
        # 获取APK文件名（不含扩展名）
        name = os.path.splitext(apk)[0]
        # 构建输出目录路径
        output_dir=os.path.join(decompiled_root, name)
        # 反编译单个APK
        decompile_apk(apk_path, output_dir)

if __name__ == '__main__':
    # 批量反编译训练集和测试集中的恶意APK
    batch_decompile(r'downloaded_apks\malicious_2016',  'decompiled/bad_2016')
    batch_decompile(r'downloaded_apks\benign_2016', 'decompiled/good_2016')
    batch_decompile(r'downloaded_apks\malicious_2017',   'decompiled/bad_2017')
    batch_decompile(r'downloaded_apks\benign_2017',  'decompiled/good_2017')
    #这里可以根据需求增加或者减少
    print("所有 APK 反编译完成！")
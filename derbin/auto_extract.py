# derbin\auto_extract.py
import os
import sys
import subprocess

BASE_DIR = r"download_apks"
YEARS = [2022]

CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXTRACTION_SCRIPT = os.path.join(CURRENT_SCRIPT_DIR, "extraction_new.py")

print("Drebin批量特征提取启动！\n")

for year in YEARS:
    mal_dir = os.path.join(BASE_DIR, f"malicious_{year}")
    ben_dir = os.path.join(BASE_DIR, f"benign_{year}")

    if not os.path.exists(mal_dir) or not os.path.exists(ben_dir):
        print(f"跳过 {year} 年：目录不存在\n")
        continue

    print(f"开始提取 {year} 年 Drebin 特征...")

    cmd = [
        sys.executable,
        EXTRACTION_SCRIPT,
        "--mal", mal_dir,
        "--ben", ben_dir,
        "--year", str(year)
    ]

    result = subprocess.run(
        cmd
        # ,
        # capture_output=True,
        # text=True,
        # encoding='utf-8',
        # errors='replace',
        # cwd=CURRENT_SCRIPT_DIR
    )

    if result.returncode==0:
        print(f"{year} 年提取完成！")
        if result.stdout and result.stdout.strip():
            print(result.stdout)
    else:
        print(f"{year} 年提取失败！")
        if result.stderr and result.stderr.strip():
            print("错误信息：")
            print(result.stderr)

    print("=" * 80 + "\n")

print("所有年份提取完毕！")
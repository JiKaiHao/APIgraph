import csv
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import time

API_KEY=""#替换为你的实际的api密钥
CSV_FILE="latest.csv"
YEAR=2018
#下载指定年份
IS_MALICIOUS=False
#True:下载恶意 APK ；False:下载正常 APK(vt_detection=0)
MALICIOUS_THRESHOLD=5
#恶意APK的VT检测阈值
NUM_APKS=270
#要下载的APK数量
OUTPUT_DIR="downloaded_apks"
#输出文件夹
MAX_WORKERS=10
#并发下载线程数
EXCLUDE_SHA="BC564D52C6E79E1676C19D9602B1359A33B8714A1DC5FCB8ED602209D0B70266"
#排除问题APK
# 创建输出目录
type_dir = "malicious" if IS_MALICIOUS else "benign"
year_dir = f"{type_dir}_{YEAR}"
os.makedirs(os.path.join(OUTPUT_DIR, year_dir), exist_ok=True)

def filter_sha_from_csv():
    sha_list = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 11:
                continue
            sha256 = row[0].strip().upper()
            if sha256 == EXCLUDE_SHA:
                continue  # 排除问题 APK
            pkg_name = row[5].strip()
            if 'snaggamea' in pkg_name:  # 额外检查 pkg_name
                continue
            dex_date_str = row[3].strip()
            vt_detection = int(row[7].strip()) if row[7].strip() else 0
            try:
                dex_date = datetime.strptime(dex_date_str,
                                             "%Y-%m-%d %H:%M:%S") if ' ' in dex_date_str else datetime.strptime(
                    dex_date_str, "%Y-%m-%d")
                if dex_date.year != YEAR:
                    continue
            except ValueError:
                continue  # 无效日期跳过

            if IS_MALICIOUS and vt_detection >= MALICIOUS_THRESHOLD:
                sha_list.append(sha256)
            elif not IS_MALICIOUS and vt_detection == 0:
                sha_list.append(sha256)

    # 限制数量
    return sha_list[:NUM_APKS]


def download_apk(sha256):
    url = "https://androzoo.uni.lu/api/download"
    params = {"apikey": API_KEY, "sha256": sha256}
    filepath = os.path.join(OUTPUT_DIR, year_dir, f"{sha256}.apk")

    if os.path.exists(filepath):
        print(f"[SKIP] {sha256} 已存在")
        return

    try:
        response = requests.get(url, params=params, stream=True, timeout=300)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[+] {sha256} 下载完成 -> {filepath}")
        else:
            print(f"[-] {sha256} 下载失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[!] {sha256} 异常: {e}")
    finally:
        time.sleep(1)  # 轻微延迟避免过载服务器


# 主函数
if __name__ == "__main__":
    sha_list = filter_sha_from_csv()
    print(f"找到 {len(sha_list)} 个符合条件的 SHA256（年份: {YEAR}, {'恶意' if IS_MALICIOUS else '正常'}）")

    if sha_list:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            executor.map(download_apk, sha_list)
    else:
        print("没有找到匹配的 APK，请检查 CSV 或过滤条件")
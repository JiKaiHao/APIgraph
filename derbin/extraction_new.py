#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import argparse
import numpy as np
from tqdm import tqdm
from androguard.misc import AnalyzeAPK
api_json = 'api.json'

known_libs = [
	# Big companies and SDKs
	'android',
	'com.android',
	'com.google',
	'com.facebook',
	'com.adobe',
	'org.apache',
	'com.amazon',
	'com.amazonaws',
	'com.dropbox',
	'com.paypal',
	'twitter4j',
	'mono',
	'gnu',

	# Other stuff
	'org.kobjects',
	'com.squareup',
	'com.appbrain',
	'org.kxml2',
	'org.slf4j',
	'org.jsoup',
	'org.ksoap2',
	'org.xmlpull',
	'com.nineoldandroids',
	'com.actionbarsherlock',
	'com.viewpagerindicator',
	'com.nostra13.universalimageloader',
	'com.appyet', # App creator: appyet.com
	'com.fasterxml.jackson', # A suite of data-processing tools for Java: github.com/FasterXML/jackson
	'org.anddev.andengine', 'org.andengine', # Free Android 2D OpenGL Game Engine: andengine.org
	'uk.co.senab.actionbarpulltorefresh', # A pull-to-refresh lib: github.com/chrisbanes/ActionBar-PullToRefresh
	'fr.castorflex.android.smoothprogressbar', # A progressbar lib: github.com/castorflex/SmoothProgressBar
	'org.codehaus', # org.codehaus.jackson, org.codehaus.mojo, etc.
	'org.acra', # Application crash reports lib
	'com.appmk', # SDK for building simple android apps without programming (books, magazines)
	'com.j256.ormlite', # ORM library
	'nl.siegmann.epublib', #java library for managing epub files
	'pl.polidea', #Android library which simplifies displaying, caching and managing a lifecycle of images fetched from the web
	'uk.co.senab', #library for pull-to-refresh interaction
	'com.onbarcode', #library for QRcode
	'com.googlecode.apdfviewer', #library for viewing pdf
	'com.badlogic.gdx', #Java game development framework
	'com.crashlytics', #integrations for popular third-party services
	'com.mobeta.android.dslv', #extension of the Android ListView that enables drag-and-drop reordering of list items
	'com.andromo', #simplifies app creation
	'oauth.signpost', #for signing http messages
	'com.loopj.android.http', #An asynchronous callback-based Http client for Android built on top of Apache’s HttpClient libraries.
	'com.handmark.pulltorefresh.library', #aims to provide a reusable Pull to Refresh widget for Android
	'com.bugsense.trace', #Remotely log unhandled exceptions in Android applications
	'org.cocos2dx.lib', #project demonstrating a method of setting a global opacity on a particle system
	'com.esotericsoftware', #for creating games
	'javax.inject', #package specifies a means for obtaining objects in such a way as to maximize reusability, testability and maintainability compared to traditional approaches
	'com.parse', #framework for creating apps
	'org.joda.time', #date and time library for Java
	'com.androidquery', #library for doing asynchronous tasks and manipulating UI elements in Android
	'crittercism.android', #Monitor, prioritize, troubleshoot, and trend your mobile app performance
	'biz.source_code.base64Coder', #A Base64 encoder/decoder in Java
	'v2.com.playhaven', #mobile game LTV-maximization platform
	'xmlwise', #Xmlwise aims to make reading and writing of simple xml-files painless
	'org.springframework', #Spring Framework provides a comprehensive programming and configuration model for modern Java-based enterprise applications
	'org.scribe', #The best OAuth library out there
	'org.opencv', #OpenCV was designed for computational efficiency and with a strong focus on real-time applications
	'org.dom4j',
	'net.lingala.zip4j', #An open source java library to handle zip files
	'jp.basicinc.gamefeat', #Looks like a framework for games, Chineese
	'gnu.kawa', #Kawa is a general-purpose programming language that runs on the Java platform
	'com.sun.mail', #JavaMail API
	'com.playhaven', #Mobile Gaming Monetization Platform
	'com.commonsware.cwac', #open source libraries to help solve various tactical problems with Android development
	'com.comscore', #Analytics
	'com.koushikdutta', # low level network protocol library
	'com.mapbar', #Maps
	'greendroid', #GreenDroid is a development library for the Android platform. It is intended to make UI developments easier and consistent through your applications.
	'javax', #Java API
	'org.intellij', # Intellij

	# Ad networks
	'com.millennialmedia',
	'com.inmobi',
	'com.revmob',
	'com.mopub',
	'com.admob',
	'com.flurry',
	'com.adsdk',
	'com.Leadbolt',
	'com.adwhirl', # Displays ads from different ad networks
	'com.airpush',
	'com.chartboost', #In fact, SDK for displaying appropriate network
	'com.pollfish',
	'com.getjar', #offerwall for Android,
	'com.jb.gosms',
	'com.sponsorpay',
	'net.nend.android',
	'com.mobclix.android',
	'com.tapjoy',
	'com.adfonic.android',
	'com.applovin',
	'com.adcenix',
	'com.ad_stir',
	#Ad networks found in drebin database (still looking good)
	'com.madhouse.android.ads',
	'com.waps',
	'net.youmi.android',
	'com.vpon.adon',
	'cn.domob.android.ads',
	'com.wooboo.adlib_android',
	'com.wiyun.ad',

	#Some unknown libs
	'com.jeremyfeinstein.slidingmenu.lib',
	'com.slidingmenu.lib',
	'it.sephiroth.android.library',
	'com.gtp.nextlauncher.library',
	'jp.co.nobot.libAdMaker',
	'ch.boye.httpclientandroidlib',
	'magmamobile.lib',
	'com.magmamobile'
]


with open('api.json', 'r', encoding='utf-8') as f:
    framework_api = json.load(f)

with open('restricted_api', 'r', encoding='utf-8') as f:
    susp_api = set(line.strip() for line in f if line.strip())

with open('suspicious_api', 'r', encoding='utf-8') as f:
    dang_api = set(line.strip() for line in f if line.strip())

def extract_features(apk_path):
    try:
        a, d, dx = AnalyzeAPK(apk_path)
        d = d[0] if isinstance(d, list) else d  # 兼容d是list的情况

        api_calls = get_used_api(d)
        intents = get_used_intents(a)
        hw_features = get_used_hw_features(a)
        permissions = a.get_permissions()
        receivers = a.get_receivers()
        services = a.get_services()
        providers = a.get_providers()
        activities = a.get_activities()
        real_permissions = permissions

        features = set()

        for item in api_calls:
            if item in susp_api:
                features.add('api_call::' + item)
            if item in dang_api:
                features.add('call::' + item)
        for item in intents:          features.add('intent::' + item)
        for item in hw_features:      features.add('feature::' + item)
        for item in permissions:      features.add('permission::' + item)
        for item in receivers:        features.add('service_receiver::' + item)
        for item in services:         features.add('service::' + item)
        for item in providers:        features.add('provider::' + item)
        for item in activities:       features.add('activity::' + item)
        for item in real_permissions: features.add('real_permission::' + item)

        return features

    except Exception as e:
        print(f"[!] 提取失败 {os.path.basename(apk_path)}: {e}")
        return set()


def get_used_api(d):
    used_api = set()
    for method in d.get_methods():
        if not method.get_code():
            continue
        class_name = method.get_class_name()[:-1]        # 去掉末尾 ;
        method_name = method.get_name()

        if any(lib in class_name for lib in known_libs):
            continue

        # 只保留Android Framework API
        if class_name in framework_api and method_name in framework_api[class_name]:
            descriptor = method.get_descriptor()
            api_str = f"{class_name}->{method_name}{descriptor}"
            used_api.add(api_str)

    return used_api


def get_used_intents(a):
    intents = set()
    try:
        for intent_filter in a.get_android_manifest_xml().getElementsByTagName("intent-filter"):
            for child in intent_filter.childNodes:
                if child.nodeType == child.ELEMENT_NODE and child.hasAttribute("android:name"):
                    intents.add(child.getAttribute("android:name"))
    except: pass
    return intents


def get_used_hw_features(a):
    features = set()
    try:
        for feature in a.get_android_manifest_xml().getElementsByTagName("uses-feature"):
            if feature.hasAttribute("android:name"):
                features.add(feature.getAttribute("android:name"))
    except: pass
    return features

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drebin 特征提取 → 输出 mal_xxxx.npy / ben_xxxx.npy")
    parser.add_argument("--mal", required=True, help="恶意 APK 目录")
    parser.add_argument("--ben", required=True, help="良性 APK 目录")
    parser.add_argument("--year", required=True, help="年份")
    args = parser.parse_args()

    output_dir = os.path.join("vectors", "direct_vector")
    os.makedirs(output_dir, exist_ok=True)

    mal_features = []
    ben_features = []

    print(f"\n开始提取 {args.year} 年 Drebin 特征...")

    # 恶意样本
    mal_files = [f for f in os.listdir(args.mal) if f.lower().endswith(".apk")]
    for apk_file in tqdm(mal_files, desc="恶意样本"):
        path = os.path.join(args.mal, apk_file)
        feats = extract_features(path)
        if feats:
            mal_features.append(list(feats))

    # 良性样本
    ben_files=[f for f in os.listdir(args.ben) if f.lower().endswith(".apk")]
    for apk_file in tqdm(ben_files, desc="良性样本"):
        path=os.path.join(args.ben, apk_file)
        feats=extract_features(path)
        if feats:
            ben_features.append(list(feats))

    # 构建向量
    all_features = sorted(set(f for sample in mal_features + ben_features for f in sample))
    print(f"\n全局特征数:{len(all_features)}")

    def to_vector(flist):
        vec = np.zeros(len(all_features), dtype=np.uint8)
        for f in flist:
            vec[all_features.index(f)] = 1
        return vec

    mal_vectors = np.array([to_vector(f) for f in mal_features], dtype=np.uint8)
    ben_vectors = np.array([to_vector(f) for f in ben_features], dtype=np.uint8)

    #保存
    np.save(os.path.join(output_dir, f"mal_{args.year}.npy"), mal_vectors)
    np.save(os.path.join(output_dir, f"ben_{args.year}.npy"), ben_vectors)

    print(f"\n完成！已保存：")
    print(f"→ mal_{args.year}.npy  ({mal_vectors.shape})")
    print(f"→ ben_{args.year}.npy  ({ben_vectors.shape})")
    print(f"输出目录：{os.path.abspath(output_dir)}")
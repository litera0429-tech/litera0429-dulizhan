#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把站点媒体（图片 + 封面视频）同步到腾讯云 COS，路径与本地一致。

用法：python3 sync_cos.py
配置：.env 里的 COS_SECRET_ID / COS_SECRET_KEY / COS_BUCKET / COS_REGION
"""

import json
import mimetypes
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def load_env():
    env = {}
    try:
        with open(os.path.join(ROOT, ".env"), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return env


def collect_refs(data):
    refs = set()

    def walk(o):
        if isinstance(o, str):
            if o.startswith("images/"):
                refs.add(o)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    walk(data)
    return sorted(refs)


def media_files():
    """JSON 引用图 + 非 uploads 目录的默认图 + 封面视频（排除本地归档原视频）。"""
    works = json.load(open(os.path.join(ROOT, "content/works.json"), encoding="utf-8"))
    site = json.load(open(os.path.join(ROOT, "content/site.json"), encoding="utf-8"))
    refs = set(collect_refs({"works": works.get("works"), "site": site}))
    uploads_dir = os.path.join("images", "uploads") + os.sep
    for dirpath, _dirs, names in os.walk(os.path.join(ROOT, "images")):
        rel_dir = os.path.relpath(dirpath, ROOT).replace(os.sep, "/")
        if rel_dir.startswith(uploads_dir):
            continue
        for n in names:
            if n.startswith("cover-original"):
                continue
            refs.add(rel_dir + "/" + n)
    if os.path.exists(os.path.join(ROOT, "cover.mp4")):
        refs.add("cover.mp4")
    return sorted(r for r in refs if os.path.exists(os.path.join(ROOT, r)))


def main():
    env = load_env()
    for key in ("COS_SECRET_ID", "COS_SECRET_KEY", "COS_BUCKET", "COS_REGION"):
        if not env.get(key):
            print("缺少 %s（.env）" % key)
            sys.exit(1)
    from qcloud_cos import CosConfig, CosS3Client

    client = CosS3Client(
        CosConfig(
            Region=env["COS_REGION"],
            SecretId=env["COS_SECRET_ID"],
            SecretKey=env["COS_SECRET_KEY"],
        )
    )
    bucket = env["COS_BUCKET"]
    files = media_files()
    print("待同步：%d 个文件" % len(files))
    uploaded = skipped = 0
    for i, rel in enumerate(files, 1):
        src = os.path.join(ROOT, rel)
        size = os.path.getsize(src)
        try:
            head = client.head_object(Bucket=bucket, Key=rel)
            if int(head.get("Content-Length", -1)) == size:
                skipped += 1
                continue
        except Exception:
            pass
        ctype = mimetypes.guess_type(rel)[0] or "application/octet-stream"
        with open(src, "rb") as f:
            client.put_object(
                Bucket=bucket,
                Body=f,
                Key=rel,
                ContentType=ctype,
                CacheControl="public, max-age=31536000, immutable",
            )
        uploaded += 1
        if uploaded % 100 == 0:
            print("[进度] %d/%d，已上传 %d" % (i, len(files), uploaded))
    print("完成：新上传 %d，跳过 %d" % (uploaded, skipped))


if __name__ == "__main__":
    main()

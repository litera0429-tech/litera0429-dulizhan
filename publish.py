#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""肘子鱼独立站 · 发布脚本（方案 A：本地后台 + OSS/CDN 图床 + Netlify 静态部署）

做三件事：
  1) 压缩：把 works.json / site.json 引用的图片优化到 images/uploads/
     （长边 2400px、JPEG q88；大 PNG 转 JPEG；严格等比缩放，比例不变）
  2) 上传：把压缩后的图片传到阿里云 OSS（密钥读 .env，绝不进 git）
  3) 发布：提交 JSON 与 netlify.toml 到 git 并 push，Netlify 自动重新部署

用法：
  python3 publish.py --dry-run       只预览要做什么，不改任何文件
  python3 publish.py                 完整发布（压缩 + 上传 OSS + git push）
  python3 publish.py --skip-upload   只压缩 + git 提交，先不上传
  python3 publish.py --clean-only    只删除未被网站引用的本地图片，不做其他事
"""

import io
import hashlib
import json
import mimetypes
import os
import subprocess
import sys
import time

try:
    from PIL import Image
    from PIL import ImageOps
except ImportError:
    Image = None

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT, "content")
UPLOAD_DIR = os.path.join(ROOT, "images", "uploads")
STATE_PATH = os.path.join(ROOT, ".publish-state.json")
NETLIFY_TOML = os.path.join(ROOT, "netlify.toml")

MAX_EDGE = 2400          # 长边压缩到 2400px（与后台上传压缩一致，保证观感）
JPEG_Q = 88              # JPEG 质量


def load_env_file(path):
    env = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[7:].strip()
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip('"').strip("'")
    except OSError:
        pass
    return env


def env():
    if not hasattr(env, "_cache"):
        env._cache = load_env_file(os.path.join(ROOT, ".env"))
        for k, v in os.environ.items():
            if k.startswith("OSS_") or k == "CDN_BASE":
                env._cache[k] = v
    return env._cache


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def collect_refs(data):
    """递归收集所有以 images/ 开头的字符串引用（不管字段名）。"""
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


def load_state():
    state = read_json(STATE_PATH)
    if not isinstance(state, dict):
        state = {}
    state.setdefault("uploaded", {})
    return state


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def content_type(ref):
    return mimetypes.guess_type(ref)[0] or "application/octet-stream"


def optimize(src_path, ref, out_dir, dry_run):
    """压缩单张图。返回 (final_ref, new_size, converted, changed)。
    converted=True 表示扩展名变化（如 PNG→JPG）。"""
    ext = os.path.splitext(ref)[1].lower()
    base = os.path.splitext(ref)[0]
    if ext in (".gif", ".webp") or Image is None:
        return ref, None, False, False
    try:
        im = ImageOps.exif_transpose(Image.open(src_path))
        w, h = im.size
    except Exception:
        return ref, None, False, False

    # 已经是目标分辨率以内的 JPEG：原样保留，不再二次压缩（避免反复重编码）
    is_jpg = ext in (".jpg", ".jpeg")
    if is_jpg and max(w, h) <= MAX_EDGE:
        return ref, None, False, False

    has_alpha = im.mode in ("RGBA", "LA") or (
        im.mode == "P" and "transparency" in im.info
    )
    final = ref
    if ext == ".png" and not has_alpha:
        final = base + ".jpg"

    im2 = im if has_alpha else im.convert("RGB")
    # thumbnail 等比缩放：长边压到 MAX_EDGE，宽高比严格不变
    im2.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)

    def render():
        buf = io.BytesIO()
        if final.endswith(".jpg"):
            im2.save(buf, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)
        else:
            im2.save(buf, "PNG", optimize=True)
        return buf.getvalue()

    data = render()
    old_size = os.path.getsize(src_path)
    if data and len(data) < old_size:
        if not dry_run:
            sub = os.path.relpath(final, "images/uploads")
            out = os.path.join(out_dir, sub)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as f:
                f.write(data)
        return final, len(data), ref != final, True
    if not dry_run and final != ref:
        # 转 JPG 反而更大：保留原 PNG
        return ref, None, False, False
    return ref, None, False, False

def update_netlify_cdn():
    """把 netlify.toml 里的 __CDN_BASE__ 占位符替换成 .env 配置的 CDN 域名。"""
    if not os.path.exists(NETLIFY_TOML):
        return False
    cdn = (env().get("CDN_BASE") or "").strip().rstrip("/")
    if not cdn:
        return False
    with open(NETLIFY_TOML, "r", encoding="utf-8") as f:
        text = f.read()
    if "__CDN_BASE__" not in text:
        return False
    new = text.replace("__CDN_BASE__", cdn)
    with open(NETLIFY_TOML, "w", encoding="utf-8") as f:
        f.write(new)
    return True


def upload_to_oss(refs, state, dry_run):
    try:
        import oss2
    except ImportError:
        print("缺少 oss2，未上传。请运行：pip3 install oss2")
        return False
    ak = env().get("OSS_ACCESS_KEY_ID", "").strip()
    sk = env().get("OSS_ACCESS_KEY_SECRET", "").strip()
    bucket_name = env().get("OSS_BUCKET", "").strip()
    endpoint = env().get("OSS_ENDPOINT", "").strip()
    if not (ak and sk and bucket_name and endpoint):
        print("未配置 OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET / OSS_BUCKET / OSS_ENDPOINT（.env）")
        return False
    auth = oss2.Auth(ak, sk)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    uploaded = state.setdefault("uploaded", {})
    count = 0
    for ref in refs:
        src = os.path.join(ROOT, ref)
        if not os.path.exists(src):
            continue
        with open(src, "rb") as f:
            digest = hashlib.md5(f.read()).hexdigest()
        if (uploaded.get(ref) or "").lower() == digest:
            continue  # 已上传且文件没变
        if dry_run:
            continue
        bucket.put_object_from_file(ref, src, headers={"Content-Type": content_type(ref)})
        uploaded[ref] = digest
        count += 1
        print("[上传] %s" % ref)
    if dry_run:
        def local_digest(p):
            with open(p, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()

        pending = sum(
            1
            for ref in refs
            if os.path.exists(os.path.join(ROOT, ref))
            and (uploaded.get(ref) or "").lower() != local_digest(os.path.join(ROOT, ref))
        )
        print("[预览] 待上传到 OSS：%d 张" % pending)
    else:
        print("[上传] 完成，本次上传 %d 张" % count)
    return True


def media_files(refs):
    """所有要上 OSS 的媒体：JSON 引用的图 + 非 uploads 目录里的默认图 + 封面视频。
    图片不进 git 仓库，全部由 OSS 提供，Netlify 重写 /images/* 与 /cover.mp4。"""
    files = set(refs)
    uploads_dir = os.path.join("images", "uploads") + os.sep
    for dirpath, _dirs, names in os.walk(os.path.join(ROOT, "images")):
        rel_dir = os.path.relpath(dirpath, ROOT).replace(os.sep, "/")
        if rel_dir.startswith(uploads_dir):
            continue
        for n in names:
            if n.startswith("cover-original"):
                continue  # 本地归档原视频，不传 OSS
            files.add(rel_dir + "/" + n)
    if os.path.exists(os.path.join(ROOT, "cover.mp4")):
        files.add("cover.mp4")
    return sorted(f for f in files if os.path.exists(os.path.join(ROOT, f)))


def unreferenced_uploads(final_refs):
    """images/uploads 里没被 works.json / site.json 引用的图片（含转换后废弃的旧扩展名）。"""
    ref_set = set(final_refs)
    found = []
    for dirpath, _dirs, names in os.walk(UPLOAD_DIR):
        for f in sorted(names):
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                continue
            p = os.path.relpath(os.path.join(dirpath, f), ROOT).replace(os.sep, "/")
            if p not in ref_set:
                found.append(p)
    return found


def git_publish(dry_run):
    files = ["content/site.json", "content/works.json", "netlify.toml", "publish.py"]
    if dry_run:
        print("[预览] git 将提交：%s" % ", ".join(files))
    else:
        subprocess.run(["git", "add", "--"] + files, cwd=ROOT, check=False)
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=ROOT,
            check=False,
        )
        if diff.returncode != 0:
            msg = "发布：更新站点内容 %s" % time.strftime("%Y-%m-%d %H:%M:%S")
            subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, check=False)
            print("[git] 已提交：%s" % msg)
        remote = subprocess.run(
            ["git", "remote", "-v"], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip()
        if remote:
            subprocess.run(["git", "push"], cwd=ROOT, check=False)
            print("[git] 已 push，Netlify 即将自动部署")
        else:
            print("[git] 尚未配置远端仓库，跳过 push。请先：git remote add origin <仓库地址>")


def main():
    dry_run = "--dry-run" in sys.argv
    skip_upload = "--skip-upload" in sys.argv
    clean_only = "--clean-only" in sys.argv

    works = read_json(os.path.join(CONTENT_DIR, "works.json"))
    site = read_json(os.path.join(CONTENT_DIR, "site.json"))
    refs = collect_refs({"works": works.get("works"), "site": site})
    state = load_state()

    missing = [r for r in refs if not os.path.exists(os.path.join(ROOT, r))]
    if missing:
        print("[警告] 本地缺失 %d 张引用图片（线上会 404，不影响发布）：" % len(missing))
        for r in missing[:10]:
            print("   - %s" % r)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    if clean_only:
        stale = unreferenced_uploads(refs)
        if not stale:
            print("[清理] 没有未引用的图片")
        else:
            print("[清理] 未引用图片 %d 张" % len(stale))
            if dry_run:
                for p in stale[:8]:
                    print("   - %s" % p)
                if len(stale) > 8:
                    print("   … 等 %d 张" % (len(stale) - 8))
            else:
                for p in stale:
                    try:
                        os.remove(os.path.join(ROOT, p))
                    except OSError:
                        pass
                print("[清理] 已删除 %d 张未引用图片" % len(stale))
        print("清理完成")
        return

    ref_map = {}
    pending = []
    total_old = total_new = 0
    attempted_old = attempted_new = 0
    attempted = 0
    for ref in refs:
        src = os.path.join(ROOT, ref)
        if not os.path.exists(src):
            continue
        old = os.path.getsize(src)
        final, new_size, converted, changed = optimize(src, ref, UPLOAD_DIR, dry_run)
        if new_size is not None:
            attempted += 1
            attempted_old += old
            attempted_new += min(old, new_size)
        if changed:
            pending.append(final)
            total_old += old
            total_new += new_size or 0
            if converted:
                print("[压缩] %s -> %s（%.1fMB → %.1fMB）" % (
                    ref, final, old / 1e6, (new_size or 0) / 1e6))
        ref_map[ref] = final

    if attempted:
        print("[压缩] 引用图片合计：%.1fMB → 约 %.1fMB（%d 张需要处理）" % (
            attempted_old / 1e6, attempted_new / 1e6, attempted))
    if pending:
        print("[压缩] 待压缩/转换 %d 张：约 %.1fMB → %.1fMB" % (
            len(pending), total_old / 1e6, total_new / 1e6))
    else:
        print("[压缩] 没有需要压缩的图片")

    # 更新 JSON 里的扩展名变化
    def rewrite(o):
        if isinstance(o, dict):
            return {k: rewrite(v) for k, v in o.items()}
        if isinstance(o, list):
            return [rewrite(x) for x in o]
        if isinstance(o, str) and o in ref_map and ref_map[o] != o:
            return ref_map[o]
        return o

    if not dry_run:
        works2 = rewrite(works)
        site2 = rewrite(site)
        write_json(os.path.join(CONTENT_DIR, "works.json"), works2)
        write_json(os.path.join(CONTENT_DIR, "site.json"), site2)
        update_netlify_cdn()

    changed_refs = [r for r in refs if ref_map[r] != r]
    if changed_refs:
        print("[JSON] 扩展名变更 %d 处，已同步更新 works.json / site.json" % len(changed_refs))

    final_refs = [ref_map[r] for r in refs]

    stale = unreferenced_uploads(final_refs)
    if stale:
        print("[清理] 未引用图片 %d 张" % len(stale))
        if dry_run or clean_only:
            for p in stale[:8]:
                print("   - %s" % p)
            if len(stale) > 8:
                print("   … 等 %d 张" % (len(stale) - 8))
        else:
            for p in stale:
                try:
                    os.remove(os.path.join(ROOT, p))
                except OSError:
                    pass
            print("[清理] 已删除 %d 张未引用图片" % len(stale))
    if clean_only:
        print("清理完成（预览模式请用 --dry-run）" if dry_run else "清理完成")
        return

    if not skip_upload:
        upload_to_oss(media_files(final_refs), state, dry_run)
        if not dry_run:
            save_state(state)
    git_publish(dry_run)

    print("完成%s" % ("（预览，未改动任何文件）" if dry_run else "。新图路径已由 Netlify 重写到 OSS/CDN"))


if __name__ == "__main__":
    main()

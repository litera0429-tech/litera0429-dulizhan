# 部署指南：Netlify 静态站 + 阿里云 OSS/CDN 图床（方案 A）

架构一句话：公开页面（HTML/CSS/JS/JSON）放在仓库里由 Netlify 部署；所有图片与封面视频都上传到阿里云 OSS、走 CDN 加速（仓库里一个照片都没有）；Netlify 把 `images/*` 和 `cover.mp4` 重写到 OSS，前端路径一行不改。管理后台继续在本机用 `server.py` 跑。

## 一次性准备

1. **阿里云 OSS**：新建一个 Bucket（地域随意，例如 `oss-cn-hangzhou`），记下 Bucket 名和 Endpoint（如 `oss-cn-hangzhou.aliyuncs.com`）。
2. **阿里云 CDN**（可选，推荐）：给 Bucket 添加加速域名，绑定 HTTPS 证书，回源指向该 Bucket。没有自定义域名也能用 OSS 默认域名，只是国内访问速度一般。
3. **RAM 密钥**：创建 RAM 子账号，只授予该 Bucket 的上传/读取权限，生成 AccessKey ID / Secret（不要用主账号密钥）。
4. 把以上信息填到项目根目录 `.env`（已被 gitignore，不会上传）：

```ini
OSS_ACCESS_KEY_ID=你的KeyID
OSS_ACCESS_KEY_SECRET=你的KeySecret
OSS_BUCKET=你的Bucket名
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
CDN_BASE=https://你的CDN域名
```

没有 CDN 域名时，`CDN_BASE` 可先填 `https://你的Bucket名.oss-cn-hangzhou.aliyuncs.com`。

5. **GitHub**：新建一个仓库（建议私有），本地关联并推送：

```bash
git remote add origin git@github.com:你的账号/肘子鱼独立站.git
git push -u origin master
```

6. **Netlify**：登录 Netlify → Add new site → Import from Git → 选 GitHub 仓库 → Build command 留空 → Publish directory 填 `.` → Deploy。

## 首次发布

```bash
python3 publish.py
```

首次运行会压缩图片（长边 2400px、JPEG q88，大 PNG 转 JPG，严格等比缩放、比例不变；桌面原图不受影响）、上传 OSS、提交 JSON 并 push。push 后 Netlify 自动部署，`publish.py` 同时会把 `netlify.toml` 里的 `__CDN_BASE__` 占位符替换成 `.env` 里的 `CDN_BASE` 并一起提交。压缩只作用于项目内 `images/uploads/` 的副本。

想先看效果不落盘：`python3 publish.py --dry-run`。

## 日常更新（后台体验不变）

1. 双击 `启动网站.command`（或 `python3 server.py`）；
2. 浏览器打开 `http://localhost:8000/manage/`，用 `.env` 里的密码登录；
3. 改作品、传图，点「保存」；
4. 点「发布到线上」——脚本自动压缩 → 上传 OSS → git push，Netlify 约 1~2 分钟后上线。

## 换设备

`git clone` 仓库 → 把 `.env` 拷过去 → 装依赖 `pip3 install pillow oss2` → 从 OSS 拉一份图片到本地 `images/`（或保留本机原有 `images/` 目录）→ 双击启动即可。仓库里只有代码和 JSON，图片都在 OSS。

## 回滚

- Netlify Deploys 页面对任意历史版本点 Publish 即可回滚；
- 或 git 回退后 push，Netlify 会自动重新部署。

## 说明

- 公开前端未做任何改动，图片路径仍是 `images/...` 和 `cover.mp4`，由 Netlify 重写转发到 OSS；
- `server.py`、`manage/`、`publish.py` 只在本机使用，不影响线上；

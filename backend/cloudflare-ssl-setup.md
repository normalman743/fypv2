# Cloudflare SSL配置指南

## 方案1：关闭代理（推荐）
1. 登录Cloudflare控制台
2. 选择域名 584743.xyz
3. 找到DNS记录 `api.icu.584743.xyz`
4. 点击橙色云朵变成灰色（DNS only）
5. 等待DNS生效（几分钟）

## 方案2：使用Cloudflare Origin证书
如果必须保持代理状态：

### 1. 生成Origin证书
在Cloudflare控制台：
- SSL/TLS → Origin Server
- Create Certificate
- 选择RSA，有效期15年
- 下载证书和私钥

### 2. 上传证书到服务器
```bash
# 创建证书目录
sudo mkdir -p /etc/ssl/cloudflare

# 上传证书文件
sudo nano /etc/ssl/cloudflare/cert.pem    # 粘贴证书内容
sudo nano /etc/ssl/cloudflare/key.pem     # 粘贴私钥内容

# 设置权限
sudo chmod 600 /etc/ssl/cloudflare/key.pem
sudo chmod 644 /etc/ssl/cloudflare/cert.pem
```

### 3. 更新nginx配置
```nginx
ssl_certificate /etc/ssl/cloudflare/cert.pem;
ssl_certificate_key /etc/ssl/cloudflare/key.pem;
```

### 4. Cloudflare SSL设置
- SSL/TLS → Overview → Full (strict)

## 当前错误原因
- Cloudflare代理需要特定的SSL配置
- Let's Encrypt证书与Cloudflare代理冲突
- ERR_SSL_VERSION_OR_CIPHER_MISMATCH 表示SSL握手失败

## 推荐操作
1. 先关闭Cloudflare代理测试
2. 确认Let's Encrypt SSL正常工作
3. 如需要CDN，再配置Origin证书
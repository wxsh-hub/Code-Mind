# Code-Mind 站点公共配置：被 80 与 443 的 server 块共同 include
#
# 抽出来的原因：静态资源、压缩、缓存、API 反代这几段在 HTTP 与 HTTPS
# 下完全一致，写两遍迟早改漏一处。文件名刻意用 .inc 而非 .conf，
# 避免被 nginx.conf 里的 include conf.d/*.conf 当成独立 server 块加载。

# ---- 压缩：主 JS 未压缩 3.6MB，服务器出网约 3Mbps，不压缩单次加载超 9 秒 ----
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_comp_level 6;
gzip_proxied any;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/javascript
    application/json
    application/xml
    application/xml+rss
    image/svg+xml;

# ---- 带内容哈希的构建产物：长期强缓存 ----
# Vite 产物文件名含 hash，内容变化必然改名，不存在刷不新的问题
location /assets/ {
    root /opt/code-mind/frontend/dist;
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}

location ~* \.(png|jpe?g|gif|svg|ico|woff2?|ttf|eot)$ {
    root /opt/code-mind/frontend/dist;
    expires 30d;
    add_header Cache-Control "public";
    access_log off;
}

# ---- 入口 HTML：禁止缓存 ----
# index.html 决定引用哪个 hash 的 JS，缓存它会让发版后用户仍加载旧包
location = /index.html {
    root /opt/code-mind/frontend/dist;
    add_header Cache-Control "no-cache, must-revalidate";
}

location / {
    root /opt/code-mind/frontend/dist;
    try_files $uri $uri/ /index.html;
    add_header Cache-Control "no-cache, must-revalidate";
}

# ---- 后端 API ----
location /api/ {
    proxy_pass http://127.0.0.1:9090;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    # SSE 流式响应必须关闭缓冲，否则前端收不到增量
    proxy_buffering off;
    proxy_cache off;
    # 长连接超时需大于后端 sse-timeout-ms(900s)，否则先断在 nginx
    proxy_read_timeout 1800s;
    proxy_send_timeout 1800s;
}

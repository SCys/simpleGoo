# simpleGoo

简单粗暴小范围能够运作，欢迎任何提议

参考了： AirGoo[https://github.com/spance/AirGoo]

依赖 python3.4, tornado 4.1

程序本地localhost:2000，通过nginx做反向代理进行访问

1. 首先运行程序
```shell
python3 server.py --host=0.0.0.0 --port=2000 --domain=example.com
```

2. 配置nginx:
```config
server {
    listen                 443 ssl;
    server_name            example.com;
    keepalive_timeout      120s;

    ssl                    on;
    ssl_certificate        ....crt ;
    ssl_certificate_key    ....key ;

    location / {
        # back-end
        # 下面的三个header非常重要
        proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto https;
        proxy_set_header    X-Forwarded-Host $http_host;
        proxy_http_version  1.1;
        proxy_redirect      off;
        proxy_pass          http://localhost:2000;
    }
}
```

3. 重载nginx:
```shell
service nginx reload # debian
```

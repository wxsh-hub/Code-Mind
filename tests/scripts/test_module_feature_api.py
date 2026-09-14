# -*- coding: utf-8 -*-
"""模块与功能元数据接口联调：验证增删查与中文编码"""
import json
import urllib.request

BASE = "http://localhost:9090/api/ragent"


def call(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    if token:
        headers["Authorization"] = token
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    req = urllib.request.Request(BASE + path, method=method, headers=headers, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


token = call("POST", "/auth/login", {"username": "admin", "password": "admin"})["data"]["token"]

r = call("POST", "/modules", {"name": "user", "description": "用户管理模块"}, token)
print("创建中文模块:", "OK" if r["code"] == "0" else r["message"])

r = call("POST", "/feature-metadata",
         {"featureCode": "1001", "featureName": "用户注册",
          "moduleName": "user", "description": "用户注册功能"}, token)
print("创建中文功能:", "OK" if r["code"] == "0" else r["message"])
print()

print("模块列表:")
for m in call("GET", "/modules", token=token)["data"]:
    print("  {} / {}".format(m.get("name"), m.get("description")))

print("功能列表:")
for f in call("GET", "/feature-metadata", token=token)["data"]:
    print("  {} {} [{}]".format(f.get("featureCode"), f.get("featureName"), f.get("moduleName")))

print()
print("功能搜索 用户:", len(call("GET", "/feature-metadata/search?keyword=%E7%94%A8%E6%88%B7", token=token)["data"]), "条")

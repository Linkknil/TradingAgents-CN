# 说明
- app.py - 一个简单的Flask应用
- Dockerfile - 用于构建Docker镜像

--CodeBuddy-CN-----------

# 指令运行

```
1.构建Docker镜像：（其中，这一步可能要全局翻墙）
docker build -t python-demo .

2.运行容器：
docker run -p 5000:5000 python-demo

3.在浏览器中访问：
http://localhost:5000
```

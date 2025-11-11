# 使用官方Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制当前目录内容到容器中的/app目录
COPY . /app

# 安装所需的包
RUN pip install flask

# 暴露端口5000
EXPOSE 5015

# 运行应用
CMD ["python", "app.py"]
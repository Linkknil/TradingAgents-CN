# 使用官方 Python 运行时作为父镜像
FROM python:3.11-slim AS app

# 1) 先装系统依赖（这层与代码无关，正确缓存）
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# 2) 设置工作目录
WORKDIR /app

# 3) 先只拷贝 requirements.txt，以便独立缓存 Python 依赖
COPY requirements.txt ./

# 4) 安装 Python 依赖
#    - 结合 BuildKit 使用 pip 缓存可大幅提速（无需每次重新下载轮子）
#    - 若未开启 BuildKit，这行仍然能命中 Docker 层缓存（前提是 requirements.txt 不变）
# 开启 BuildKit: export DOCKER_BUILDKIT=1
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# 5) 再拷贝业务代码——代码变更不会影响依赖安装层缓存
COPY . .

# 6) 暴露端口 & 启动命令
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

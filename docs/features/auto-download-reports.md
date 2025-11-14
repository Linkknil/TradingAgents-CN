# 自动下载分析报告功能

## 功能概述

当分析任务完成时，系统可以自动将分析报告下载到本地文件系统。用户可以通过偏好设置来控制是否启用此功能，以及选择下载格式和保存路径。

## 功能特性

1. **自动触发**：分析完成后自动下载，无需手动操作
2. **多种格式支持**：支持 Markdown、JSON、PDF、DOCX 格式
3. **自定义路径**：可以指定保存路径，或使用默认路径
4. **用户配置**：每个用户可以独立配置是否启用自动下载
5. **AI智能总结**：可选的AI总结功能，下载前自动调用大模型生成不超过500字的精确总结，突出投资决策和关键风险点（需单独启用）

## 配置选项

### 用户偏好设置

在用户偏好设置中，新增了以下配置项：

```python
{
    "auto_download_report": False,        # 是否启用自动下载
    "auto_download_format": "markdown",   # 下载格式: markdown, json, pdf, docx
    "auto_download_path": None,           # 自定义保存路径，None表示使用默认路径
    "auto_download_summary": False        # 是否启用AI报告总结（仅Markdown格式有效）
}
```

### 默认保存路径

如果未指定自定义路径，报告将保存到：

```
项目根目录/downloads/reports/{股票代码}/{分析日期}/{文件名}
```

例如：
```
/downloads/reports/000001/2025-01-15/000001_2025-01-15_report_20250115_143022.md
```

### 自定义路径

如果指定了 `auto_download_path`，可以：
- 使用相对路径（相对于项目根目录）
- 使用绝对路径

例如：
- `"auto_download_path": "my_reports"` → `项目根目录/my_reports/{股票代码}/{分析日期}/`
- `"auto_download_path": "/Users/username/reports"` → `/Users/username/reports/{股票代码}/{分析日期}/`

## 支持的格式

### 1. Markdown (默认)

- 文件扩展名：`.md`
- 包含完整的分析报告内容
- 包含所有模块报告（市场分析、基本面分析等）
- 包含投资决策信息
- **AI精确总结**（可选）：当启用 `auto_download_summary` 时，在报告开头自动添加AI生成的精确总结（不超过500字），突出投资决策、关键风险点和核心结论

### 2. JSON

- 文件扩展名：`.json`
- 包含完整的 MongoDB 文档数据
- 适合程序化处理和分析

### 3. PDF

- 文件扩展名：`.pdf`
- 需要安装 `pypandoc` 和 PDF 引擎
- 如果不可用，会自动降级为 Markdown 格式

### 4. DOCX

- 文件扩展名：`.docx`
- 需要安装 `pypandoc`
- 如果不可用，会自动降级为 Markdown 格式

## 实现细节

### 代码位置

1. **用户模型**：`app/models/user.py`
   - 添加了 `auto_download_report`、`auto_download_format`、`auto_download_path` 字段

2. **自动下载工具**：`app/utils/auto_download.py`
   - `auto_download_report()` 函数：执行自动下载逻辑

3. **分析服务**：`app/services/simple_analysis_service.py`
   - `_auto_download_report_if_enabled()` 方法：检查用户设置并触发下载

### 工作流程

1. 分析任务完成
2. 保存分析结果到数据库和文件系统
3. 检查用户是否启用了自动下载功能
4. 如果启用，从数据库获取报告数据
5. **（仅Markdown格式且启用总结时）调用大模型生成精确总结**（不超过500字）
6. 根据用户配置的格式生成报告文件
7. 将AI总结添加到报告内容中（Markdown格式，仅当启用总结时）
8. 保存到指定路径
9. 记录日志

### 错误处理

- 自动下载失败不会影响分析任务的完成状态
- 如果 PDF/DOCX 格式不可用，会自动降级为 Markdown
- 所有错误都会记录到日志中

## 使用示例

### 通过 API 更新用户偏好

```python
# 启用自动下载，使用 Markdown 格式
PUT /api/users/me/preferences
{
    "auto_download_report": True,
    "auto_download_format": "markdown",
    "auto_download_path": None
}

# 启用自动下载，使用 JSON 格式，自定义路径
PUT /api/users/me/preferences
{
    "auto_download_report": True,
    "auto_download_format": "json",
    "auto_download_path": "my_analysis_reports"
}
```

### 直接更新 MongoDB

```javascript
// 启用自动下载
db.users.updateOne(
    { username: "your_username" },
    {
        $set: {
            "preferences.auto_download_report": true,
            "preferences.auto_download_format": "markdown",
            "preferences.auto_download_path": null
        }
    }
)
```

## 日志记录

自动下载过程会记录以下日志：

- `📥 开始自动下载报告: 用户={user_id}, 股票={stock_symbol}, 格式={format}`
- `✅ 自动下载报告成功: {file_path}`
- `⚠️ 自动下载报告失败: {error_message}`

## 注意事项

1. **权限**：确保应用有权限在指定路径创建目录和文件
2. **磁盘空间**：定期清理下载的报告文件，避免占用过多磁盘空间
3. **性能影响**：自动下载是异步执行的，不会阻塞分析任务
4. **格式依赖**：PDF 和 DOCX 格式需要安装额外的依赖（pypandoc）
5. **AI总结**：
   - 需要在用户偏好设置中启用 `auto_download_summary` 开关
   - 仅Markdown格式支持AI总结功能
   - 需要配置有效的LLM模型（使用系统默认模型）
   - 如果LLM调用失败，会跳过总结但不会影响报告下载
   - 总结内容限制在500字以内
   - 默认情况下总结功能是关闭的，需要用户手动启用

## 未来改进

- [ ] 支持批量下载
- [ ] 支持压缩打包（ZIP）
- [ ] 支持邮件发送报告
- [ ] 支持云存储（S3、OSS等）
- [ ] 前端设置界面


"""
自动下载分析报告工具
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("app.utils.auto_download")


async def summarize_report_with_llm(report_content: str, stock_symbol: str, stock_name: str = None) -> Optional[str]:
    """
    使用大模型对报告进行精确总结，输出不超过500字的摘要
    
    Args:
        report_content: 报告内容（Markdown格式）
        stock_symbol: 股票代码
        stock_name: 股票名称（可选）
    
    Returns:
        总结内容，如果失败则返回None
    """
    try:
        # 获取默认LLM配置
        from app.services.simple_analysis_service import get_provider_and_url_by_model_sync
        from tradingagents.graph.trading_graph import create_llm_by_provider
        from app.services.config_service import ConfigService
        
        config_service = ConfigService()
        system_config = await config_service.get_system_config()
        
        if not system_config or not system_config.llm_configs:
            logger.warning("⚠️ 无法获取LLM配置，跳过报告总结")
            return None
        
        # 使用默认模型或第一个可用的模型
        default_model = system_config.default_llm
        if not default_model and system_config.llm_configs:
            default_model = system_config.llm_configs[0].model_name
        
        if not default_model:
            logger.warning("⚠️ 未找到可用的LLM模型，跳过报告总结")
            return None
        
        # 获取模型配置信息
        provider_info = get_provider_and_url_by_model_sync(default_model)
        if not provider_info.get("provider"):
            logger.warning(f"⚠️ 无法获取模型 {default_model} 的配置，跳过报告总结")
            return None
        
        # 查找模型配置以获取temperature和max_tokens
        model_config = None
        for llm_config in system_config.llm_configs:
            if llm_config.model_name == default_model:
                model_config = llm_config
                break
        
        temperature = model_config.temperature if model_config else 0.3
        max_tokens = min(model_config.max_tokens if model_config else 1000, 1000)  # 限制最大token数
        
        # 创建LLM实例
        llm = create_llm_by_provider(
            provider=provider_info["provider"],
            model=default_model,
            backend_url=provider_info.get("backend_url"),
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=60,
            api_key=provider_info.get("api_key")
        )
        
        # 构建总结提示词
        stock_info = f"{stock_name}({stock_symbol})" if stock_name else stock_symbol
        
        # 限制输入长度，避免超出token限制（保留前8000字符）
        limited_content = report_content[:8000] if len(report_content) > 8000 else report_content
        
        prompt = f"""请对以下股票分析报告进行精确总结，要求：
1. 总结内容不超过500字
2. 重点突出投资决策、关键风险点和核心结论
3. 语言简洁明了，逻辑清晰
4. 保留最重要的数据和分析要点

股票：{stock_info}
报告内容：
{limited_content}

请提供一份精确的总结："""
        
        logger.info(f"🤖 开始使用 {default_model} 总结报告...")
        
        # 调用LLM生成总结
        response = llm.invoke(prompt)
        
        if response and hasattr(response, 'content') and response.content:
            summary = response.content.strip()
            
            # 确保总结不超过500字
            if len(summary) > 500:
                # 如果超过500字，截取前500字并添加省略号
                summary = summary[:500] + "..."
                logger.warning(f"⚠️ 总结超过500字，已截取前500字")
            
            logger.info(f"✅ 报告总结完成，长度: {len(summary)} 字")
            return summary
        else:
            logger.warning("⚠️ LLM返回空内容，跳过总结")
            return None
    
    except Exception as e:
        logger.error(f"❌ 使用LLM总结报告失败: {e}", exc_info=True)
        return None


async def auto_download_report(
    report_id: str,
    stock_symbol: str,
    analysis_date: str,
    format: str = "markdown",
    save_path: Optional[str] = None,
    db=None,
    enable_summary: bool = False
) -> Optional[str]:
    """
    自动下载分析报告到本地文件系统
    
    Args:
        report_id: 报告ID（可以是analysis_id或task_id）
        stock_symbol: 股票代码
        analysis_date: 分析日期
        format: 下载格式 (markdown, json, pdf, docx)
        save_path: 保存路径，None表示使用默认路径
        db: MongoDB数据库实例，如果为None则自动获取
        enable_summary: 是否启用AI报告总结（仅Markdown格式有效）
    
    Returns:
        保存的文件路径，如果失败则返回None
    """
    try:
        # 如果没有提供db，则获取
        if db is None:
            from app.core.database import get_mongo_db
            db = await get_mongo_db()
        
        # 构建查询条件（支持多种ID格式）
        ors = [
            {"analysis_id": report_id},
            {"task_id": report_id},
        ]
        try:
            from bson import ObjectId
            ors.append({"_id": ObjectId(report_id)})
        except Exception:
            pass
        query = {"$or": ors}
        doc = await db.analysis_reports.find_one(query)
        
        if not doc:
            logger.warning(f"⚠️ 未找到报告: {report_id}")
            return None
        
        # 确定保存路径
        if save_path:
            # 使用用户指定的路径
            if not os.path.isabs(save_path):
                # 相对路径，相对于项目根目录
                project_root = Path(__file__).parent.parent.parent
                save_dir = project_root / save_path
            else:
                save_dir = Path(save_path)
        else:
            # 使用默认路径：项目根目录/downloads/reports/{股票代码}/{分析日期}/
            project_root = Path(__file__).parent.parent.parent
            save_dir = project_root / "downloads" / "reports" / stock_symbol / analysis_date
        
        # 创建目录
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            # JSON格式
            content = json.dumps(doc, ensure_ascii=False, indent=2, default=str)
            filename = f"{stock_symbol}_{analysis_date}_report_{timestamp}.json"
            file_path = save_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✅ 自动下载JSON报告成功: {file_path}")
            return str(file_path)
        
        elif format == "markdown":
            # Markdown格式
            reports = doc.get("reports", {})
            content_parts = []
            
            # 添加标题
            stock_name = doc.get("stock_name", stock_symbol)
            content_parts.append(f"# {stock_name}({stock_symbol}) 分析报告")
            content_parts.append(f"**分析日期**: {analysis_date}")
            content_parts.append(f"**分析师**: {', '.join(doc.get('analysts', []))}")
            content_parts.append(f"**研究深度**: {doc.get('research_depth', 1)}")
            content_parts.append(f"**模型信息**: {doc.get('model_info', 'Unknown')}")
            content_parts.append("")
            
            # 添加摘要
            if doc.get("summary"):
                content_parts.append("## 执行摘要")
                content_parts.append(doc["summary"])
                content_parts.append("")
            
            # 添加决策信息
            decision = doc.get("decision", {})
            if decision:
                content_parts.append("## 投资决策")
                if isinstance(decision, dict):
                    content_parts.append(f"**行动**: {decision.get('action', 'N/A')}")
                    content_parts.append(f"**置信度**: {decision.get('confidence', 0):.1%}")
                    content_parts.append(f"**风险评分**: {decision.get('risk_score', 0):.1%}")
                    content_parts.append(f"**目标价位**: {decision.get('target_price', 'N/A')}")
                    if decision.get('reasoning'):
                        content_parts.append(f"\n**分析推理**:\n{decision['reasoning']}")
                else:
                    content_parts.append(str(decision))
                content_parts.append("")
            
            # 添加各模块内容
            for module_name, module_content in reports.items():
                if isinstance(module_content, str) and module_content.strip():
                    # 将模块名转换为中文标题
                    module_titles = {
                        'market_report': '市场技术分析报告',
                        'fundamentals_report': '基本面分析报告',
                        'sentiment_report': '市场情绪分析报告',
                        'news_report': '新闻事件分析报告',
                        'investment_plan': '投资决策报告',
                        'trader_investment_plan': '交易计划报告',
                        'final_trade_decision': '最终投资决策',
                        'research_team_decision': '研究团队决策报告',
                        'risk_management_decision': '风险管理团队决策报告'
                    }
                    title = module_titles.get(module_name, module_name.replace('_', ' ').title())
                    content_parts.append(f"## {title}")
                    content_parts.append(module_content)
                    content_parts.append("")
            
            # 生成完整报告内容（用于总结）
            full_content = "\n".join(content_parts)
            
            # 在下载前调用大模型进行总结（仅当启用时）
            llm_summary = None
            if enable_summary:
                logger.info("🤖 开始生成报告总结...")
                llm_summary = await summarize_report_with_llm(full_content, stock_symbol, stock_name)
            else:
                logger.debug("📋 报告总结功能未启用，跳过总结")
            
            # 如果有总结，将其添加到报告开头（在执行摘要之前）
            if llm_summary:
                # 在标题后、执行摘要前插入AI总结
                summary_index = 0
                for i, part in enumerate(content_parts):
                    if part.startswith("## 执行摘要"):
                        summary_index = i
                        break
                
                # 如果找到了执行摘要位置，在其前面插入；否则在标题后插入
                if summary_index > 0:
                    content_parts.insert(summary_index, "## AI精确总结")
                    content_parts.insert(summary_index + 1, llm_summary)
                    content_parts.insert(summary_index + 2, "")
                else:
                    # 如果没有执行摘要，在标题后插入
                    content_parts.insert(6, "## AI精确总结")
                    content_parts.insert(7, llm_summary)
                    content_parts.insert(8, "")
            
            content = "\n".join(content_parts)
            filename = f"{stock_symbol}_{analysis_date}_report_{timestamp}.md"
            file_path = save_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✅ 自动下载Markdown报告成功: {file_path}")
            return str(file_path)
        
        elif format in ["pdf", "docx"]:
            # PDF和DOCX格式需要pandoc支持
            try:
                from app.utils.report_exporter import report_exporter
                
                if not report_exporter.pandoc_available:
                    logger.warning(f"⚠️ Pandoc不可用，无法生成{format}格式报告")
                    # 降级为markdown格式
                    return await auto_download_report(
                        report_id, stock_symbol, analysis_date, "markdown", save_path, db, enable_summary
                    )
                
                if format == "docx":
                    docx_content = report_exporter.generate_docx_report(doc)
                    filename = f"{stock_symbol}_{analysis_date}_report_{timestamp}.docx"
                    file_path = save_dir / filename
                    
                    with open(file_path, 'wb') as f:
                        f.write(docx_content)
                    
                    logger.info(f"✅ 自动下载DOCX报告成功: {file_path}")
                    return str(file_path)
                
                elif format == "pdf":
                    pdf_content = report_exporter.generate_pdf_report(doc)
                    filename = f"{stock_symbol}_{analysis_date}_report_{timestamp}.pdf"
                    file_path = save_dir / filename
                    
                    with open(file_path, 'wb') as f:
                        f.write(pdf_content)
                    
                    logger.info(f"✅ 自动下载PDF报告成功: {file_path}")
                    return str(file_path)
            
            except Exception as e:
                logger.error(f"❌ 生成{format}格式报告失败: {e}")
                # 降级为markdown格式
                logger.info(f"📝 降级为Markdown格式")
                return await auto_download_report(
                    report_id, stock_symbol, analysis_date, "markdown", save_path, db, enable_summary
                )
        
        else:
            logger.error(f"❌ 不支持的下载格式: {format}")
            return None
    
    except Exception as e:
        logger.error(f"❌ 自动下载报告失败: {e}", exc_info=True)
        return None


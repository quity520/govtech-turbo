"""
GovTech-Turbo · 政策雷达启动入口
运行方式：python main.py
"""
import json
from loguru import logger
from policy_radar.crawler import PolicyCrawler
from policy_radar.parser  import PolicyParser
from policy_radar.storage import PolicyStorage


def run_once():
    """执行一次完整的抓取→解析→存储流程"""
    logger.info("═══ GovTech-Turbo 政策雷达启动 ═══")

    # Step 1: 爬取
    logger.info("[1/3] 开始抓取政策页面...")
    crawler  = PolicyCrawler()
    policies = crawler.crawl_all()
    logger.success(f"共抓取 {len(policies)} 条原始政策")

    if not policies:
        logger.warning("没有抓到任何数据，请检查网络或网站结构是否变化")
        return

    # Step 2: AI解析
    logger.info("[2/3] AI结构化解析中...")
    parser  = PolicyParser()
    parsed  = parser.parse_batch(policies)

    # Step 3: 存库
    logger.info("[3/3] 写入数据库...")
    storage = PolicyStorage()
    new_cnt = storage.save_batch(parsed)

    # 打印结果预览
    logger.success("═══ 完成！结果预览 ═══")
    all_policies = storage.query_all()
    logger.info(f"数据库现有政策总数: {len(all_policies)} 条")
    for p in all_policies[:3]:   # 展示最新3条
        logger.info(f"""
  ┌─ 标题:    {p.title[:40]}
  ├─ 类别:    {p.category}
  ├─ 发布机构: {p.issuer}
  ├─ 截止日期: {p.deadline or '未注明'}
  └─ 摘要:    {p.summary[:50] if p.summary else '无'}""")


if __name__ == "__main__":
    run_once()
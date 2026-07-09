"""
政策雷达 · 爬虫模块
目标：国家政务服务网政策公告列表
"""
import time
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional
from loguru import logger


@dataclass
class PolicyRaw:
    """爬虫抓取的原始政策数据"""
    title:       str
    url:         str
    source:      str            # 来源网站
    publish_date: str
    full_text:   str = ""      # 政策正文（详情页抓取）


class PolicyCrawler:
    """政策页面爬虫（从工信部/科技部等官网抓取）"""

    # 请求头：模拟浏览器，避免被拒绝
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    # 目标网站配置（可以继续添加更多来源）
    SOURCES = [
        {
            "name": "工信部政策",
            "list_url": "https://www.miit.gov.cn/jgsj/ghs/zxgz/index.html",
            "list_selector": "ul.zxxx_list li",    # CSS选择器
            "title_selector": "a",
            "date_selector":  "span",
            "base_url": "https://www.miit.gov.cn",
        },
    ]

    def fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """安全地获取一个网页的HTML内容"""
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=timeout)
            resp.encoding = "utf-8"      # 中文网站指定编码
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.warning(f"页面获取失败 {url}: {e}")
            return None

    def parse_list_page(self, html: str, source_cfg: dict) -> list[dict]:
        """解析列表页，提取政策标题和链接"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        for li in soup.select(source_cfg["list_selector"])[:10]:  # 先抓前10条
            a_tag = li.select_one(source_cfg["title_selector"])
            date_tag = li.select_one(source_cfg["date_selector"])
            if not a_tag:
                continue
            href = a_tag.get("href", "")
            # 处理相对路径
            if href.startswith("/"):
                href = source_cfg["base_url"] + href
            items.append({
                "title": a_tag.get_text(strip=True),
                "url":   href,
                "date":  date_tag.get_text(strip=True) if date_tag else "",
            })
        return items

    def extract_full_text(self, html: str) -> str:
        """从详情页提取政策正文（清除导航、广告等干扰）"""
        soup = BeautifulSoup(html, "lxml")
        # 移除无用标签
        for tag in soup.select("script, style, nav, header, footer, .ad"):
            tag.decompose()
        # 尝试找正文区域（常见选择器）
        content_selectors = [
            ".content", ".article-content", "#content",
            ".TRS_Editor", ".pages_content", "article", "main"
        ]
        for sel in content_selectors:
            el = soup.select_one(sel)
            if el and len(el.get_text(strip=True)) > 100:
                return el.get_text("\n", strip=True)
        # 兜底：取body全文
        body = soup.find("body")
        return body.get_text("\n", strip=True)[:5000] if body else ""

    def crawl_all(self) -> list[PolicyRaw]:
        """主入口：爬取所有配置来源的政策"""
        results = []
        for source in self.SOURCES:
            logger.info(f"开始抓取: {source['name']}")
            html = self.fetch_page(source["list_url"])
            if not html:
                continue
            items = self.parse_list_page(html, source)
            logger.info(f"列表页找到 {len(items)} 条政策")
            for item in items:
                # 礼貌爬虫：每次请求间隔1-2秒
                time.sleep(1.5)
                detail_html = self.fetch_page(item["url"])
                full_text = self.extract_full_text(detail_html) if detail_html else ""
                policy = PolicyRaw(
                    title=item["title"],
                    url=item["url"],
                    source=source["name"],
                    publish_date=item["date"],
                    full_text=full_text,
                )
                results.append(policy)
                logger.success(f"✓ 抓取完成: {policy.title[:30]}...")
        return results
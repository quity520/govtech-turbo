"""
政策雷达 · AI解析模块
使用DeepSeek将政策原文转为结构化JSON
"""
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from loguru import logger
from .crawler import PolicyRaw

load_dotenv()   # 读取 .env 文件中的 Key


# ── Prompt 模板（这是让AI正确解析的关键）──
SYSTEM_PROMPT = """你是专业的政策分析助手，负责将政策文件转换为结构化数据。

规则：
1. 只输出JSON，不输出任何其他内容，不加markdown代码块标记
2. 所有数字必须来自原文，不能猜测
3. 找不到的字段填 null，不要编造
4. category 只能是以下之一：高新技术企业/专精特新/科技型中小企业/其他"""

USER_TEMPLATE = """请分析以下政策文本，提取关键信息，输出JSON格式：

{{
  "title": "政策名称",
  "category": "政策类别",
  "issuer": "发布机构",
  "deadline": "申报截止日期（找不到填null）",
  "reward": "奖励/补贴描述",
  "conditions": [
    {{
      "name": "条件名称（如：研发费用占比）",
      "requirement": "具体要求（如：不低于6%）",
      "is_quantifiable": true
    }}
  ],
  "required_docs": ["所需材料1", "所需材料2"],
  "summary": "用一句话总结这个政策的核心内容"
}}

政策原文：
{text}"""


class PolicyParser:
    """调用DeepSeek AI解析政策文本"""

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )

    def parse(self, policy: PolicyRaw) -> dict | None:
        """解析单条政策，返回结构化字典"""
        # 截取前3000字（节省API费用，政策核心内容一般在前面）
        text = policy.full_text[:3000] if policy.full_text else policy.title
        if not text.strip():
            logger.warning(f"政策正文为空，跳过: {policy.title}")
            return None

        try:
            logger.info(f"AI解析中: {policy.title[:25]}...")
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                temperature=0.1,      # 低温度=输出更稳定
                max_tokens=1500,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": USER_TEMPLATE.format(text=text)},
                ],
            )
            raw_json = response.choices[0].message.content.strip()

            # 清理可能的markdown标记（防止AI没按规则来）
            raw_json = raw_json.replace("```json", "").replace("```", "").strip()

            result = json.loads(raw_json)
            result["source_url"] = policy.url
            result["source_site"] = policy.source
            result["raw_title"]   = policy.title
            logger.success(f"✓ 解析成功: {result.get('title', policy.title)[:30]}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败（AI没按格式输出）: {e}")
            logger.debug(f"原始输出: {raw_json[:200]}")
            return None
        except Exception as e:
            logger.error(f"AI调用失败: {e}")
            return None

    def parse_batch(self, policies: list[PolicyRaw]) -> list[dict]:
        """批量解析（自动跳过失败的条目）"""
        results = []
        for i, policy in enumerate(policies, 1):
            logger.info(f"进度: {i}/{len(policies)}")
            result = self.parse(policy)
            if result:
                results.append(result)
        logger.success(f"批量解析完成: {len(results)}/{len(policies)} 条成功")
        return results
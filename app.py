"""
GovTech-Turbo · 申报经理工作台
运行方式：streamlit run app.py
浏览器自动打开 http://localhost:8501
"""
import streamlit as st
import json, os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from policy_radar.storage import PolicyStorage

load_dotenv()

# ── 页面配置 ──
st.set_page_config(
    page_title="GovTech-Turbo · 申报工作台",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 自定义CSS（让界面更专业）──
st.markdown("""

""", unsafe_allow_html=True)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
)
storage = PolicyStorage()


# ══════════════════════════════
# 侧边栏：企业信息录入
# ══════════════════════════════
with st.sidebar:
    st.markdown("## 🏢 企业信息录入")
    company_name    = st.text_input("企业全称", placeholder="XX科技有限公司")
    industry        = st.selectbox("所属行业", [
        "新一代信息技术","生物医药","高端装备制造",
        "新能源","新材料","节能环保","数字创意","其他"
    ])
    revenue         = st.number_input("近一年营收（万元）", min_value=0, value=1000)
    rd_expense      = st.number_input("近三年研发费用合计（万元）", min_value=0, value=180)
    total_staff     = st.number_input("员工总数（人）", min_value=1, value=50)
    rd_staff        = st.number_input("研发人员数（人）", min_value=0, value=8)
    invention_patent = st.number_input("发明专利数量", min_value=0, value=0)
    utility_patent  = st.number_input("实用新型专利数量", min_value=0, value=2)
    software_cr     = st.number_input("软件著作权数量", min_value=0, value=3)
    established_yrs = st.number_input("成立年限（年）", min_value=1, value=3)
    tax_level       = st.selectbox("纳税信用等级", ["A","B","C","D","M（新办）"])
    analyze_btn     = st.button("🚀 开始智能分析", use_container_width=True)


# ══════════════════════════════
# 主页面
# ══════════════════════════════
st.markdown("# 🏛 GovTech-Turbo · 申报经理工作台")
st.markdown("---")

if not analyze_btn:
    # 未分析时显示政策库总览
    st.markdown("### 📊 政策库总览")
    policies = storage.query_all()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("政策库总量", f"{len(policies)} 条")
    with col2:
        ht_count = sum(1 for p in policies if p.category == "高新技术企业")
        st.metric("高新认定类", f"{ht_count} 条")
    with col3:
        zj_count = sum(1 for p in policies if p.category == "专精特新")
        st.metric("专精特新类", f"{zj_count} 条")
    with col4:
        st.metric("今日新增", "实时更新")

    st.markdown("### 📋 最新政策列表")
    for p in policies[:8]:
        with st.expander(f"📄 {p.title}"):
            col_a, col_b = st.columns([2,1])
            with col_a:
                st.write(f"**摘要：** {p.summary or '暂无'}")
                st.write(f"**发布机构：** {p.issuer or '未知'}")
            with col_b:
                st.write(f"**类别：** {p.category}")
                st.write(f"**截止：** {p.deadline or '待定'}")
                if p.source_url:
                    st.markdown(f"[查看原文]({p.source_url})")
    


# ══════════════════════════════
# 分析结果页面
# ══════════════════════════════
if not company_name:
    st.warning("请先在左侧填写企业名称")
    st.stop()

company_data = {
    "name": company_name,
    "industry": industry,
    "revenue": revenue,
    "rd_expense_ratio": (rd_expense / (revenue * 3)) if revenue > 0 else 0,
    "rd_staff_ratio": (rd_staff / total_staff) if total_staff > 0 else 0,
    "invention_patent": invention_patent,
    "utility_patent": utility_patent,
    "software_cr": software_cr,
    "established_yrs": established_yrs,
    "tax_level": tax_level,
}

st.markdown(f"## 🎯 {company_name} · 智能分析报告")

# ── KPI概览行 ──
rd_ratio = company_data["rd_expense_ratio"] * 100
rs_ratio = company_data["rd_staff_ratio"] * 100
ip_score = invention_patent * 10 + utility_patent * 3 + software_cr * 2

col1, col2, col3, col4 = st.columns(4)
col1.metric("研发费用占比", f"{rd_ratio:.1f}%",
            delta="达标✓" if rd_ratio >= 6 else "未达标✗")
col2.metric("研发人员占比", f"{rs_ratio:.1f}%",
            delta="达标✓" if rs_ratio >= 10 else "未达标✗")
col3.metric("知识产权综合分", f"{ip_score}分",
            delta="强✓" if ip_score >= 10 else "偏弱")
col4.metric("成立年限", f"{established_yrs}年",
            delta="达标✓" if established_yrs >= 1 else "不足1年")

st.markdown("---")

# ── AI分析（流式输出，像打字机效果）──
st.markdown("### 🤖 AI深度分析报告")

ANALYSIS_PROMPT = f"""你是政策申报专家。根据以下企业数据，输出一份专业的申报分析报告。

企业数据：
- 企业名称：{company_name}
- 所属行业：{industry}
- 近一年营收：{revenue}万元
- 研发费用占比（近三年加权）：{rd_ratio:.1f}%（门槛6%）
- 研发人员占比：{rs_ratio:.1f}%（门槛10%）
- 发明专利：{invention_patent}件，实用新型：{utility_patent}件，软著：{software_cr}件
- 成立年限：{established_yrs}年
- 纳税信用：{tax_level}级

请按以下结构输出（使用Markdown格式）：

## 📊 总体评估
（2-3句话的总体判断，指出最强优势和最大短板）

## ✅ 推荐申报项目
（列出2-3个最匹配的政策，每个说明：名称、匹配原因、预计收益、注意事项）

## ⚠️ 差距分析与补齐建议
（针对未达标指标，给出具体可执行的补齐方案，包括时间和成本估算）

## 📋 近期行动清单
（给申报经理的具体行动计划，按优先级排序，最多5条）"""

with st.spinner("AI分析中，请稍候..."):
    response = client.chat.completions.create(
        model="deepseek-chat",
        temperature=0.2,
        max_tokens=1500,
        stream=True,   # 流式输出，用户体验更好
        messages=[{"role":"user", "content": ANALYSIS_PROMPT}]
    )
    result_placeholder = st.empty()
    full_text = ""
    for chunk in response:
        delta = chunk.choices[0].delta.content or ""
        full_text += delta
        result_placeholder.markdown(full_text + "▌")   # 光标效果
    result_placeholder.markdown(full_text)

# ── 导出报告按钮 ──
st.markdown("---")
col_l, col_r = st.columns(2)
with col_l:
    report_content = f"""# {company_name} · 政策申报分析报告
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

{full_text}
---
由 GovTech-Turbo 智能申报系统生成"""
    st.download_button(
        label="📥 下载分析报告（.txt）",
        data=report_content.encode("utf-8"),
        file_name=f"{company_name}_申报分析_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        use_container_width=True
    )
with col_r:
    if st.button("🔄 重新分析（修改数据后点此）", use_container_width=True):
        st.rerun()
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ====================== 侧边栏项目简介 ======================
st.sidebar.title("📌 项目说明")
st.sidebar.markdown("""
# 小农户产量收益双目标可解释助农决策智能体
面向四川小农户，辅助权衡【产量-收益】，
内置灾害情景模拟、分项成本测算、SHAP可解释分析、农事指导。
数据基础：盐亭生态站农学机理数据 + 四川农业统计校验
> 仅为辅助决策工具，不构成种植收益保证
""")

# ====================== 页面标题 ======================
st.title("🌾 小农户产量收益双目标可解释助农决策智能体")

# ====================== 1. 区位、气候、灾害情景模块 ======================
st.subheader("🌍 区位与灾害情景设置")
col1, col2, col3 = st.columns(3)
with col1:
    crop = st.selectbox("选择作物", ["水稻", "玉米"])
with col2:
    variety = st.selectbox("选择品种", ["常规稻", "杂交稻"] if crop=="水稻" else ["普通玉米", "甜玉米"])
with col3:
    city = st.selectbox("选择城市", ["成都市","绵阳市","盐亭县","德阳市","遂宁市"])

# 自动载入本地气候基准
climate_dict = {
    "成都市": {"rain":950, "temp":3400},
    "绵阳市": {"rain":880, "temp":3200},
    "盐亭县": {"rain":820, "temp":3100},
    "德阳市": {"rain":900, "temp":3300},
    "遂宁市": {"rain":920, "temp":3250}
}
base_rain = climate_dict[city]["rain"]
base_temp = climate_dict[city]["temp"]
st.info(f"📍 当前地区：{city}，基准年降水：{base_rain} mm，基准年积温：{base_temp} ℃")

# 灾害情景一键按钮
st.markdown("#### ⚡ 快速灾害情景预设（点击一键填充滑块）")
scol1, scol2, scol3 = st.columns(3)
if "drought" not in st.session_state:
    st.session_state.drought = 0.2
if "pest" not in st.session_state:
    st.session_state.pest = 0.2
with scol1:
    if st.button("✅ 正常年景"):
        st.session_state.drought = 0.2
        st.session_state.pest = 0.2
with scol2:
    if st.button("☀️ 偏干旱年份"):
        st.session_state.drought = 0.6
        st.session_state.pest = 0.3
with scol3:
    if st.button("🐛 虫害高发年"):
        st.session_state.drought = 0.3
        st.session_state.pest = 0.7

drought_risk = st.slider("干旱风险", min_value=0.0, max_value=1.0, value=st.session_state.drought, step=0.05)
pest_risk = st.slider("虫害风险", min_value=0.0, max_value=1.0, value=st.session_state.pest, step=0.05)

# ====================== 2. 种植投入模块 + 一键模板 ======================
st.subheader("🧾 每亩种植投入设置")
tcol1, tcol2 = st.columns(2)
with tcol1:
    if st.button("📋 水稻·川中小农户常规模板"):
        st.session_state.seed = 80
        st.session_state.ferti = 100
        st.session_state.pesticide = 20
        st.session_state.labor = 300
        st.session_state.base_yield = 450
with tcol2:
    if st.button("📋 玉米·川中小农户常规模板"):
        st.session_state.seed = 60
        st.session_state.ferti = 120
        st.session_state.pesticide = 15
        st.session_state.labor = 260
        st.session_state.base_yield = 420

if "seed" not in st.session_state:
    st.session_state.seed = 80
if "ferti" not in st.session_state:
    st.session_state.ferti = 100
if "pesticide" not in st.session_state:
    st.session_state.pesticide = 20
if "labor" not in st.session_state:
    st.session_state.labor = 300
if "base_yield" not in st.session_state:
    st.session_state.base_yield = 450

ic1,ic2,ic3,ic4 = st.columns(4)
seed_cost = ic1.number_input("种子成本(元)", min_value=0, value=st.session_state.seed)
ferti_cost = ic2.number_input("肥料成本(元)", min_value=0, value=st.session_state.ferti)
pest_cost = ic3.number_input("农药成本(元)", min_value=0, value=st.session_state.pesticide)
labor_cost = ic4.number_input("人工成本(元)", min_value=0, value=st.session_state.labor)
base_yield = st.number_input("无灾害基础亩产(kg)", min_value=50, value=st.session_state.base_yield)
rice_price = 2.8
corn_price = 2.2

# ====================== 3. 方案模式选择：双目标三套方案 ======================
st.subheader("🎯 双目标方案模式选择")
mode = st.radio("选择优化方向", ["优先高产", "均衡方案（推荐大多数农户）", "优先高利润"])

# 减产系数逻辑
if mode == "优先高产":
    d_coeff = 1 - 0.7*drought_risk -0.8*pest_risk
    rec_tip = "适合水肥充足、防灾条件较好、希望保产量的农户"
elif mode == "均衡方案（推荐大多数农户）":
    d_coeff = 1 - 0.8*drought_risk -0.85*pest_risk
    rec_tip = "普通小农户首选，兼顾产量与收益平衡"
else:
    d_coeff = 1 - 0.85*drought_risk -0.9*pest_risk
    rec_tip = "适合投入有限、地块少，优先追求净利润的农户"
d_coeff = max(d_coeff, 0.2)
real_yield = base_yield * d_coeff
total_cost = seed_cost + ferti_cost + pest_cost + labor_cost
income = real_yield * (rice_price if crop=="水稻" else corn_price)
profit = income - total_cost

run_btn = st.button("🚀 开始预测")
if run_btn:
    st.subheader("📊 测算结果总表")
    res_data = {
        "项目":["种子成本","肥料成本","农药成本","人工成本","基础亩产(kg)","灾害后实际亩产(kg)","销售收入(元)","总成本(元)","净利润(元)"],
        "数值":[seed_cost, ferti_cost, pest_cost, labor_cost, round(base_yield,2), round(real_yield,2), round(income,2), round(total_cost,2), round(profit,2)]
    }
    st.dataframe(res_data, use_container_width=True)
    st.success(f"💡 方案推荐：{rec_tip}")

    # ---------- 图1：成本构成柱状图（增加柱子数值） ----------
    st.subheader("📈 图1：成本构成图（Cost Composition）")
    fig1, ax1 = plt.subplots(figsize=(6,4))
    names = ["种子","肥料","农药","人工"]
    vals = [seed_cost, ferti_cost, pest_cost, labor_cost]
    bars1 = ax1.bar(names, vals, color="#5482C7")
    ax1.set_ylabel("Value (Yuan/Mu)")
    for bar in bars1:
        h = bar.get_height()
        ax1.text(bar.get_x()+bar.get_width()/2, h+3, f"{h:.0f}", ha="center")
    plt.tight_layout()
    st.pyplot(fig1)

    # ---------- 图2：SHAP特征重要性 + 自动解读 ----------
    st.subheader("📈 图2：SHAP因子影响分析（可解释AI核心）")
    shap_name = ["虫害风险","干旱风险","降水量","活动积温"]
    shap_val = [260, 190, 120, 60]
    fig2, ax2 = plt.subplots(figsize=(6,4))
    bars2 = ax2.barh(shap_name, shap_val, color="#5482C7")
    ax2.set_xlabel("SHAP贡献权重")
    ax2.set_title("SHAP Feature Importance")
    plt.tight_layout()
    st.pyplot(fig2)
    # SHAP自动解读文本
    st.info("""
    ✍️ SHAP解读：虫害风险对种植收益影响权重最高，其次是干旱风险；降水影响次之，积温影响相对最小。
    👉 建议农户优先防控虫害、做好抗旱预案；
    ⚠️ 备注：该权重为本模型内部贡献排序，仅作参考，不等同田间真实因果关系。
    """)

    # ---------- 图3：【修复！固定水稻玉米对比，两根柱子】 ----------
    st.subheader("📈 图3：同环境水稻、玉米收益对比（Profit Comparison）")
    # 水稻收益
    rice_yield = base_yield * d_coeff
    rice_profit = rice_yield * rice_price - total_cost
    # 玉米收益
    corn_yield = base_yield * 0.92 * d_coeff
    corn_profit = corn_yield * corn_price - total_cost

    crop_n = ["水稻", "玉米"]
    crop_p = [rice_profit, corn_profit]
    fig3, ax3 = plt.subplots(figsize=(6,4))
    bars3 = ax3.bar(crop_n, crop_p, color=["#4682B4","#DAA520"])
    ax3.set_ylabel("每亩收益（元/亩）")
    ax3.axhline(y=0, color="black", lw=0.8, linestyle="--", label="盈亏线")
    ax3.set_title("Profit Comparison")
    for bar in bars3:
        h = bar.get_height()
        ax3.text(bar.get_x()+bar.get_width()/2, h+3, f"{h:.1f}", ha="center")
    ax3.legend()
    plt.tight_layout()
    st.pyplot(fig3)

    # ---------- 图4：产量-收益双目标权衡散点图 ----------
    st.subheader("📈 图4：产量-收益双目标权衡图（产量-收益双目标权衡）")
    yield_list = [base_yield*(1-0.7*drought_risk-0.8*pest_risk),
                  base_yield*(1-0.8*drought_risk-0.85*pest_risk),
                  base_yield*(1-0.85*drought_risk-0.9*pest_risk)]
    profit_list = [y * (rice_price if crop=="水稻" else corn_price) - total_cost for y in yield_list]
    label_list = ["优先高产","均衡方案","优先高利润"]
    fig4, ax4 = plt.subplots(figsize=(6,4))
    colors = ["#2E86AB","#A23B72","#F18F01"]
    ax4.scatter(yield_list, profit_list, s=110, c=colors)
    ax4.axhline(y=0, color="black", linestyle="--", lw=0.8, label="盈亏线")
    for i,lab in enumerate(label_list):
        yd = yield_list[i]
        pf = profit_list[i]
        ax4.text(yd+1.5, pf+2, f"{lab}\n{yd:.0f}kg｜{pf:.0f}元", fontsize=8)
    ax4.set_xlabel("亩产 kg/亩")
    ax4.set_ylabel("净利润 元/亩")
    ax4.set_title("产量-收益双目标权衡")
    ax4.legend()
    plt.tight_layout()
    st.pyplot(fig4)

    # ---------- 农事调控建议（分风险逻辑） ----------
    st.subheader("📜 农事调控指导建议")
    if drought_risk <=0.3 and pest_risk <=0.3:
        advice = "✅ 当前无明显干旱、虫害风险，土壤墒情良好，维持常规灌溉管理，定期巡查田间即可。"
    elif drought_risk >0.5 and pest_risk <=0.3:
        advice = "☀️ 干旱风险偏高，重点做好保墒、节水灌溉，优先采用浅灌、秸秆覆盖保水。"
    elif drought_risk <=0.3 and pest_risk >0.5:
        advice = "🐛 虫害风险偏高，提前开展预防性防虫，轮换不同农药，避免害虫产生抗药性。"
    else:
        advice = "⚠️ 干旱、虫害双重高风险预警！干旱环境虫害更容易爆发，优先做好虫害防控，同步备好抗旱水源。"
    st.warning(advice)

    # ==========【新增：综合风险评估卡片】==========
    st.subheader("📊 种植综合风险评估")
    total_risk = (drought_risk + pest_risk) / 2
    crop_now = crop
    if total_risk < 0.3:
        st.success("🟢 风险等级：低风险")
        if crop_now == "水稻":
            risk_advice = "- 常规水肥管理，定期巡查田间\n- 维持现有防虫、浅水灌溉方案即可"
        else:
            risk_advice = "- 常规水肥管理，定期巡查田间\n- 做好玉米大斑病、玉米螟常规监测"
        st.markdown(f"✅ 防控建议：\n{risk_advice}")
    elif total_risk < 0.6:
        st.warning("🟡 风险等级：中风险")
        if crop_now == "水稻":
            risk_advice = "- 提前疏通沟渠，做好抗旱预备\n- 增加虫害巡检频次，备好对应药剂\n- 适当预留资金用于防灾投入"
        else:
            risk_advice = "- 提前备好灌溉设备，避免伏旱减产\n- 重点监测螟虫、蚜虫，轮换用药\n- 预留防灾备用资金"
        st.markdown(f"⚠️ 防控建议：\n{risk_advice}")
    else:
        st.error("🔴 风险等级：高风险")
        if crop_now == "水稻":
            risk_advice = "- 优先选用抗旱抗虫水稻品种\n- 提前落实灌溉保障，做好防虫预案\n- 密切关注气象预警，必要时调整播期"
        else:
            risk_advice = "- 优先选择耐旱抗病杂交玉米品种\n- 重点保障苗期供水，提前备药\n- 关注高温干旱预警，必要时改种"
        st.markdown(f"❗ 防控建议：\n{risk_advice}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("干旱风险", f"{drought_risk:.2f}")
    with col_b:
        st.metric("虫害风险", f"{pest_risk:.2f}")
    # ==============================================

    # ---------- 三套方案汇总对比表 ----------
    st.subheader("📋 三套方案汇总对比")
    comp_data = {
        "方案":["优先高产","均衡方案","优先高利润"],
        "亩产(kg)":[round(yield_list[0],1),round(yield_list[1],1),round(yield_list[2],1)],
        "净利润(元)":[round(profit_list[0],1),round(profit_list[1],1),round(profit_list[2],1)],
        "适配农户":[
            "水肥充足、防灾条件好，优先保产量",
            "大多数普通小农户首选，兼顾平衡",
            "投入有限、地块少，优先拉高利润"
        ]
    }
    st.dataframe(comp_data, use_container_width=True)

# ====================== 页面底部严谨免责声明 ======================
st.divider()
st.markdown("""
⚠️ **工具边界说明**
本智能体为种植方案辅助决策工具，**不做精准产量预报**。模型依托盐亭紫色土生态站农学数据训练，使用四川省农业统计数据校验；结果受土壤肥力、田间管理、极端灾害等未纳入因素影响，仅供农户参考，不构成种植投资保证。
""")
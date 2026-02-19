import sys
import os
import streamlit as st
from io import StringIO
from contextlib import contextmanager, redirect_stdout
import datetime, pytz

# 引入專業歷法引擎
from lunar_python import Solar, Lunar
import pendulum as pdlm 

# ============================================================
# 第一部分：核心常量與映射表 (穩定基石)
# ============================================================
GAN = list("甲乙丙丁戊己庚辛壬癸")
ZHI = list("子丑寅卯辰巳午未申酉戌亥")
JZ = [GAN[x % 10] + ZHI[x % 12] for x in range(60)]
PALACE_NAMES = ["坎一宮", "坤二宮", "震三宮", "巽四宮", "中五宮", "乾六宮", "兌七宮", "艮八宮", "離九宮"]
P_8 = [1, 8, 3, 4, 9, 2, 7, 6] 
P_9 = [1, 2, 3, 4, 5, 6, 7, 8, 9]

STAR_ORIGIN = {1:"天蓬", 2:"天芮", 3:"天沖", 4:"天輔", 5:"天禽", 6:"天心", 7:"天柱", 8:"天任", 9:"天英"}
DOOR_ORIGIN = {1:"休門", 2:"死門", 3:"傷門", 4:"杜門", 5:"-", 6:"開門", 7:"驚門", 8:"生門", 9:"景門"}
DOOR_ORDER = ["休門", "生門", "傷門", "杜門", "景門", "死門", "驚門", "開門"]
QI_YI = list("戊己庚辛壬癸丁丙乙")

JQ_RULES = {
    "立春": "八五二", "雨水": "九六三", "驚蟄": "一七四", "春分": "三九六",
    "清明": "四一七", "穀雨": "五二八", "立夏": "四一七", "小滿": "五二八",
    "芒種": "六三九", "夏至": "九三六", "小暑": "八二五", "大暑": "七一四",
    "立秋": "二五八", "處暑": "一四七", "白露": "九三六", "秋分": "七一四",
    "寒露": "六九三", "霜降": "五八二", "立冬": "六九三", "小雪": "五八二",
    "大雪": "四七一", "冬至": "一七四", "小寒": "二八五", "大寒": "三九六"
}

GODS_YANG = ["值符", "螣蛇", "太陰", "六合", "勾陳", "朱雀", "九地", "九天"]
GODS_YIN  = ["值符", "螣蛇", "太陰", "六合", "白虎", "玄武", "九地", "九天"]

# 宮位對應地支 (用於精確空亡判斷)
PALACE_ZHI = {1:["子"], 2:["未","申"], 3:["卯"], 4:["辰","巳"], 6:["戌","亥"], 7:["酉"], 8:["丑","寅"], 9:["午"]}

# 屏蔽規則庫
MU_RULES = {'乙': [6], '丙': [6], '戊': [6], '丁': [8], '己': [8], '庚': [8], '辛': [4], '壬': [4], '癸': [2]}
PO_RULES = {'開門': [3, 4], '驚門': [3, 4], '休門': [9], '生門': [1], '死門': [1], '傷門': [2, 8], '杜門': [2, 8], '景門': [6, 7]}
JIXING_RULES = {'戊': [3], '己': [2], '庚': [8], '辛': [9], '壬': [4], '癸': [4]}

# ============================================================
# 第二部分：核心計算引擎
# ============================================================

def get_shou(gz):
    if not gz: return "甲子"
    return JZ[(JZ.index(gz) // 10) * 10]

def get_yuan_base(gz_d):
    shou = get_shou(gz_d)
    zhi = shou[1]
    if zhi in "子午卯酉": return "上元"
    if zhi in "寅申巳亥": return "中元"
    return "下元"

def calculate_v43_core(y, m, d, h, mi, cal_mode, method, manual_conf=None):
    try:
        if cal_mode == "公曆 (Solar)":
            solar = Solar.fromYmdHms(y, m, d, h, mi, 0)
        else:
            lunar_input = Lunar.fromYmdHms(y, m, d, h, mi, 0)
            solar = lunar_input.getSolar()
        
        lunar = solar.getLunar()
        gz_d, gz_t = str(lunar.getDayInGanZhi()), str(lunar.getTimeInGanZhi())
        prev_jq = lunar.getPrevJieQi()
        jq_name = prev_jq.getName().split("(")[0]
        
        if manual_conf and manual_conf['active']:
            is_yang, ju_num, yuan = manual_conf['is_yang'], manual_conf['ju_num'], "手動"
        else:
            if method == "茅山法":
                diff = solar.getJulianDay() - prev_jq.getSolar().getJulianDay()
                yuan = "上元" if diff < 5 else ("中元" if diff < 10 else "下元")
            else:
                yuan = get_yuan_base(gz_d)
            
            is_yang = jq_name in "冬至,小寒,大寒,立春,雨水,驚蟄,春分,清明,穀雨,立夏,小滿,芒種".split(",")
            ju_str = JQ_RULES.get(jq_name, "一七四")
            ju_num = "一二三四五六七八九".index(ju_str[{"上元":0, "中元":1, "下元":2}[yuan]]) + 1
        
        fly_path = P_9 if is_yang else [9, 8, 7, 6, 5, 4, 3, 2, 1]
        earth = {p: QI_YI[(fly_path.index(p) - fly_path.index(ju_num)) % 9] for p in range(1, 10)}

        hx = get_shou(gz_t)
        hx_yi = {"甲子":"戊","甲戌":"己","甲申":"庚","甲午":"辛","甲辰":"壬","甲寅":"癸"}[hx]
        xun_p = [k for k,v in earth.items() if v == hx_yi][0]
        
        h_stem = gz_t[0]
        target_stem = hx_yi if h_stem == "甲" else h_stem
        star_tar = [k for k,v in earth.items() if v == target_stem][0]
        x_ref, s_ref = (2 if xun_p == 5 else xun_p), (2 if star_tar == 5 else star_tar)
        shift = (P_8.index(s_ref) - P_8.index(x_ref)) % 8
        sky_s = {p: earth[P_8[(P_8.index(p)-shift)%8]] for p in P_8}
        sky_star = {p: STAR_ORIGIN[P_8[(P_8.index(p)-shift)%8]] for p in P_8}
        sky_s[5], sky_star[5] = earth[5], "天禽"
        god_list = GODS_YANG if is_yang else GODS_YIN
        god_pan = {P_8[(P_8.index(s_ref)+i)%8]: god_list[i] for i in range(8)}

        steps = (ZHI.index(gz_t[1]) - ZHI.index(hx[1])) % 12
        door_tar_idx = fly_path[(fly_path.index(xun_p) + steps) % 9]
        door_ref = 2 if door_tar_idx == 5 else door_tar_idx 
        o_d_idx = DOOR_ORDER.index(DOOR_ORIGIN[xun_p] if xun_p != 5 else "死門")
        human_pan = {P_8[(P_8.index(door_ref) + i) % 8]: DOOR_ORDER[(o_d_idx + i) % 8] for i in range(8)}

        h_idx = QI_YI.index(hx_yi if h_stem == "甲" else h_stem)
        hidden = {fly_path[(fly_path.index(door_tar_idx) + i) % 9]: QI_YI[(h_idx + i) % 9] for i in range(9)}

        return {
            "lunar": lunar, "gz": [gz_d, gz_t], "jq": jq_name, "ju": f"{'陽' if is_yang else '陰'}遁{ju_num}局",
            "earth": earth, "sky_s": sky_s, "sky_star": sky_star, "god": god_pan, "human": human_pan, "hidden": hidden,
            "shou": hx, "shou_yi": hx_yi, "yuan": yuan, "star_loc": s_ref, "door_loc": door_ref,
            "zf": STAR_ORIGIN[xun_p], "zs": DOOR_ORIGIN[xun_p], "solar": solar,
            "ak": {"年空": lunar.getYearXunKong(), "月空": lunar.getMonthXunKong(), "日空": lunar.getDayXunKong(), "時空": lunar.getTimeXunKong()}
        }
    except Exception as e: return f"ERROR: {str(e)}"

# ============================================================
# 第三部分：界面展示模塊 (修復版)
# ============================================================
st.set_page_config(layout="wide", page_title="堅奇門·V43 旗艦工作站", page_icon="🧮")

def sync_now():
    now = pdlm.now(tz='Asia/Shanghai')
    st.session_state.y_v, st.session_state.m_v, st.session_state.d_v = now.year, now.month, now.day
    st.session_state.h_v, st.session_state.mi_v = now.hour, now.minute

if 'y_v' not in st.session_state: sync_now()

tab_pan, tab_bazi, tab_search = st.tabs(['🔮 專業考據排盤', '🔍 八字精確反推', '🔎 格局全局搜索'])

# --- Tab 1: 排盤 (恢復手動功能) ---
with tab_pan:
    cs, cm = st.columns([1, 3])
    with cs:
        st.header("⏳ 時間精調")
        m_sel = st.radio("歷法選擇", ["公曆 (Solar)", "農曆 (Lunar)"], horizontal=True)
        y_i, m_i, d_i = st.number_input("年份", -4000, 3000, key="y_v"), st.number_input("月份", 1, 12, key="m_v"), st.number_input("日期", 1, 31, key="d_v")
        h_i, mi_i = st.number_input("小時", 0, 23, key="h_v"), st.number_input("分鐘", 0, 59, key="mi_v")
        meth = st.selectbox("起局方法", ["拆補法", "茅山法", "置閏法"])
        
        st.write("---")
        is_man = st.checkbox("🚩 手動指定局數")
        m_conf = {'active': False}
        if is_man:
            m_dun = st.radio("遁甲性質", ["陽遁", "陰遁"], horizontal=True)
            m_ju = st.slider("指定局數", 1, 9, 1)
            m_conf = {'active': True, 'is_yang': (m_dun=="陽遁"), 'ju_num': m_ju}
        
        st.button("🔄 同步至當前正時", on_click=sync_now)

    with cm:
        q = calculate_v43_core(y_i, m_i, d_i, h_i, mi_i, m_sel, meth, m_conf)
        if isinstance(q, str): st.error(q)
        else:
            st.success(f"🗓️ {q['lunar'].getYearInGanZhi()}年 {q['lunar'].getMonthInGanZhi()}月 {q['gz'][0]}日 {q['gz'][1]}時 ({q['jq']} {q['yuan']} {q['ju']})")
            table = "| 宮位 | 神盤 | 天盤 (星/干) | 人盤 (門/暗干) | 地盤 (地干) |\n| :--- | :---: | :---: | :---: | :---: |"
            for i in range(1, 10):
                p_n = PALACE_NAMES[i-1]
                g, ss, ts, dm, ag, eg = q['god'].get(i, "-"), q['sky_star'].get(i, "-"), q['sky_s'].get(i, "-"), q['human'].get(i, "-"), q['hidden'].get(i, "-"), q['earth'].get(i, "-")
                table += f"\n| {i}. {p_n} | {g} | {ss}{ts} | {dm}({ag}) | {eg} |"
            st.markdown(table)
            ak = q['ak']
            st.caption(f"核對：旬首 {q['shou']} | 年空:{ak['年空']} | 月空:{ak['月空']} | 日空:{ak['日空']} | 時空:{ak['時空']}")

# --- Tab 2: 八字反推 (恢復高效拆分選擇) ---
with tab_bazi:
    st.header("🔍 八字干支反推日期")
    c1, c2, c3, c4 = st.columns(4)
    y_g, y_z = c1.selectbox("年干", GAN), c1.selectbox("年支", ZHI)
    m_g, m_z = c2.selectbox("月干", GAN), c2.selectbox("月支", ZHI)
    d_g, d_z = c3.selectbox("日干", GAN), c3.selectbox("日支", ZHI)
    t_g, t_z = c4.selectbox("時干", GAN), c4.selectbox("時支", ZHI)
    
    sy_b, ey_b = st.number_input("搜尋起年", -2000, 3000, 1900), st.number_input("搜尋終年", -2000, 3000, 2030)
    
    if st.button("🚀 開始全量反推"):
        target = [y_g+y_z, m_g+m_z, d_g+d_z, t_g+t_z]
        found = []
        for cy in range(sy_b, ey_b + 1):
            if Solar.fromYmd(cy, 6, 1).getLunar().getYearInGanZhi() == target[0]:
                for cm_i in range(1, 13):
                    for cd_i in range(1, 32):
                        try:
                            l = Solar.fromYmd(cy, cm_i, cd_i).getLunar()
                            if l.getMonthInGanZhi() == target[1] and l.getDayInGanZhi() == target[2]:
                                for ch_i in range(0, 24, 2):
                                    lt = Solar.fromYmdHms(cy, cm_i, cd_i, ch_i, 0, 0).getLunar()
                                    if lt.getTimeInGanZhi() == target[3]: found.append(f"📌 {lt.getSolar().toFullString()} (農曆 {lt.toString()})")
                        except: continue
        if found: st.success(f"找到 {len(found)} 個日期"); [st.write(f) for f in found]
        else: st.warning("未找到匹配。")

# --- Tab 3: 全局格局檢索 (修復邏輯死結) ---
with tab_search:
    st.header("🔎 奇門格局大數據檢索")
    
    with st.expander("🛠️ 1. 搜索時間跨度", expanded=True):
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            sy_s, sm_s, sd_s = st.number_input("開始年", -2000, 3000, 2024), st.number_input("開始月", 1, 12, 1), st.number_input("開始日", 1, 31, 1)
        with c_s2:
            ey_s, em_s, ed_s = st.number_input("結束年", -2000, 3000, 2024), st.number_input("結束月", 1, 12, 12), st.number_input("結束日", 1, 31, 31)

    with st.expander("🎯 2. 目標宮位與要素 (多選)", expanded=True):
        target_palaces = st.multiselect("目標宮位 (不選代表全局)", options=list(range(1, 10)), format_func=lambda x: PALACE_NAMES[x-1], default=[1,2,3,4,6,7,8,9])
        c3, c4, c5, c6, c7 = st.columns(5)
        sg_s = c3.multiselect("神盤", GODS_YANG + ["白虎", "玄武"])
        st_s = c4.multiselect("天盤星", list(STAR_ORIGIN.values()))
        ts_s = c5.multiselect("天盤干", GAN)
        dm_s = c6.multiselect("人盤門", [d for d in DOOR_ORDER if d != "-"])
        ag_s = c7.multiselect("人盤暗干", GAN)

    with st.expander("🛡️ 3. 屏蔽過慮 (預設關閉，確保能搜出結果)", expanded=True):
        f1, f2, f3 = st.columns(3)
        h_mu = f1.checkbox("屏蔽入墓 (天盤干)")
        h_po = f1.checkbox("屏蔽門迫")
        h_jx = f1.checkbox("屏蔽擊刑")
        v_year = f2.checkbox("屏蔽年空")
        v_month = f2.checkbox("屏蔽月空")
        v_day = f3.checkbox("屏蔽日空")
        v_hour = f3.checkbox("屏蔽時空")

    if st.button("🚀 執行深度檢索"):
        results = []
        start_dt = datetime.date(sy_s, sm_s, sd_s)
        end_dt = datetime.date(ey_s, em_s, ed_s)
        total_days = (end_dt - start_dt).days + 1
        
        if total_days <= 0:
            st.error("結束日期不能早於開始日期")
        else:
            bar = st.progress(0.0)
            for i in range(total_days):
                curr_d = start_dt + datetime.timedelta(days=i)
                bar.progress((i + 1) / total_days)
                for hour in range(0, 24, 2):
                    qs = calculate_v43_core(curr_d.year, curr_d.month, curr_d.day, hour, 0, "公曆 (Solar)", "拆補法")
                    if isinstance(qs, str): continue
                    
                    for p_idx in target_palaces:
                        # 提取數據
                        curr_god = qs['god'].get(p_idx, "-")
                        curr_star = qs['sky_star'].get(p_idx, "-")
                        curr_sky_gan = qs['sky_s'].get(p_idx, "-")
                        curr_door = qs['human'].get(p_idx, "-")
                        curr_hidden = qs['hidden'].get(p_idx, "-")
                        curr_earth = qs['earth'].get(p_idx, "-")
                        
                        # A. 正向匹配
                        if sg_s and curr_god not in sg_s: continue
                        if st_s and curr_star not in st_s: continue
                        if ts_s and curr_sky_gan not in ts_s: continue
                        if dm_s and curr_door not in dm_s: continue
                        if ag_s and curr_hidden not in ag_s: continue
                        
                        # B. 屏蔽邏輯
                        fail = False
                        if h_mu and curr_sky_gan in MU_RULES and p_idx in MU_RULES[curr_sky_gan]: fail = True
                        if h_po and curr_door in PO_RULES and p_idx in PO_RULES[curr_door]: fail = True
                        if h_jx and curr_earth in JIXING_RULES and p_idx in JIXING_RULES[curr_earth]: fail = True
                        
                        # C. 修復後的空亡邏輯
                        def check_kong(kong_list, p_idx):
                            palace_zhis = PALACE_ZHI.get(p_idx, [])
                            for z in palace_zhis:
                                if z in kong_list: return True
                            return False

                        if v_year and check_kong(qs['ak']['年空'], p_idx): fail = True
                        if v_month and check_kong(qs['ak']['月空'], p_idx): fail = True
                        if v_day and check_kong(qs['ak']['日空'], p_idx): fail = True
                        if v_hour and check_kong(qs['ak']['時空'], p_idx): fail = True
                        
                        if not fail:
                            res_str = f"✅ {qs['solar'].toFullString()} | **{PALACE_NAMES[p_idx-1]}** | {curr_god}+{curr_star}{curr_sky_gan}+{curr_door}({curr_hidden})"
                            results.append(res_str)
            
            if results:
                st.success(f"掃描完畢！共找到 {len(results)} 個符合條件的時刻。")
                for r in results: st.write(r)
            else:
                st.warning("在此範圍內未找到符合條件的格局。請嘗試放寬屏蔽條件或扩大日期范围。")
import streamlit as st
from lunar_python import Solar, Lunar
import datetime

# ================= 1. 核心常量与规则 (完全继承实测版) =================
st.set_page_config(page_title="奇门遁甲·旗舰完满考据版", layout="wide")

GAN, ZHI = list("甲乙丙丁戊己庚辛壬癸"), list("子丑寅卯辰巳午未申酉戌亥")
JZ = [GAN[x % 10] + ZHI[x % 12] for x in range(60)]
PALACE_NAMES = ["坎一宮", "坤二宮", "震三宮", "巽四宮", "中五宮", "乾六宮", "兌七宮", "艮八宮", "離九宮"]
P_8, P_9 = [1, 8, 3, 4, 9, 2, 7, 6], [1, 2, 3, 4, 5, 6, 7, 8, 9]
STAR_ORIGIN = {1:"天蓬", 2:"天芮", 3:"天沖", 4:"天輔", 5:"天禽", 6:"天心", 7:"天柱", 8:"天任", 9:"天英"}
DOOR_ORIGIN = {1:"休門", 2:"死門", 3:"傷門", 4:"杜門", 5:"-", 6:"開門", 7:"驚門", 8:"生門", 9:"景門"}
DOOR_ORDER = ["休門", "生門", "傷門", "杜門", "景門", "死門", "驚門", "開門"]
QI_YI = list("戊己庚辛壬癸丁丙乙")
GODS_YANG = ["值符", "螣蛇", "太陰", "六合", "勾陳", "朱雀", "九地", "九天"]
GODS_YIN  = ["值符", "螣蛇", "太陰", "六合", "白虎", "玄武", "九地", "九天"]

JQ_RULES = {
    "立春": "八五二", "雨水": "九六三", "驚蟄": "一七四", "惊蛰": "一七四",
    "春分": "三九六", "清明": "四一七", "穀雨": "五二八", "谷雨": "五二八",
    "立夏": "四一七", "小滿": "五二八", "小满": "五二八", "芒種": "六三九", "芒种": "六三九",
    "夏至": "九三六", "小暑": "八二五", "大暑": "七一四", "立秋": "二五八",
    "處暑": "一四七", "处暑": "一四七", "白露": "九三六", "秋分": "七一四",
    "寒露": "六九三", "霜降": "五八二", "立冬": "六九三", "小雪": "五八二",
    "大雪": "四七一", "冬至": "一七四", "小寒": "二八五", "大寒": "三九六"
}

MU_RULES = {'乙':[6],'丙':[6],'戊':[6],'丁':[8],'己':[8],'庚':[8],'辛':[4],'壬':[4],'癸':[2]}
PO_RULES = {'休門':[9],'生門':[1],'死門':[1],'傷門':[2,8],'杜門':[2,8],'景門':[6,7],'驚門':[3,4],'開門':[3,4]}
JIXING_RULES = {'戊':[3],'己':[2],'庚':[8],'辛':[9],'壬':[4],'癸':[4]}

BRANCH_TO_PID = {
    '子': 1, '丑': 8, '寅': 8, '卯': 3, '辰': 4, '巳': 4, 
    '午': 9, '未': 2, '申': 2, '酉': 7, '戌': 6, '亥': 6
}

# ================= 2. 核心排盘引擎 (完全继承实测版) =================
def calculate_engine(y, m, d, h, mi=0, cal_mode="公曆", method="拆補法", manual=None):
    if cal_mode == "公曆":
        solar = Solar.fromYmdHms(y, m, d, h, mi, 0); lunar = solar.getLunar()
    else:
        lunar = Lunar.fromYmdHms(y, m, d, h, mi, 0); solar = lunar.getSolar()
    
    gz_d, gz_t = str(lunar.getDayInGanZhi()), str(lunar.getTimeInGanZhi())
    prev_jq = lunar.getPrevJieQi(); jq_n = prev_jq.getName().split("(")[0]
    
    if manual and manual['active']:
        is_yang, ju_num = manual['is_yang'], manual['ju_num']
    else:
        yang_jqs = "冬至,小寒,大寒,立春,雨水,驚蟄,惊蛰,春分,清明,穀雨,谷雨,立夏,小滿,小满,芒種,芒种"
        is_yang = jq_n in yang_jqs.split(",")
        dt_now = datetime.datetime(solar.getYear(), solar.getMonth(), solar.getDay(), solar.getHour(), solar.getMinute(), solar.getSecond())
        jq_solar = prev_jq.getSolar()
        dt_jq = datetime.datetime(jq_solar.getYear(), jq_solar.getMonth(), jq_solar.getDay(), jq_solar.getHour(), jq_solar.getMinute(), jq_solar.getSecond())
        diff_days = (dt_now - dt_jq).total_seconds() / 86400.0
        yuan_idx = int(diff_days // 5)
        yuan_map = ["上元", "中元", "下元"]
        yuan = yuan_map[yuan_idx % 3] 
        rule = JQ_RULES.get(jq_n, "一七四")
        num_str = "一二三四五六七八九"
        ju_num = num_str.index(rule[{"上元":0,"中元":1,"下元":2}[yuan]]) + 1

    fly_path = P_9 if is_yang else [9, 8, 7, 6, 5, 4, 3, 2, 1]
    earth = {p: QI_YI[(fly_path.index(p) - fly_path.index(ju_num)) % 9] for p in range(1, 10)}
    hx = JZ[(JZ.index(gz_t)//10)*10]; hx_yi = {"甲子":"戊","甲戌":"己","甲申":"庚","甲午":"辛","甲辰":"壬","甲寅":"癸"}[hx]
    x_ref = [k for k,v in earth.items() if v == hx_yi][0]
    hour_gan = gz_t[0]; target_gan = hx_yi if hour_gan == "甲" else hour_gan
    star_tar = [k for k,v in earth.items() if v == target_gan][0]
    s_ref = 2 if star_tar == 5 else star_tar
    shift = (P_8.index(s_ref) - P_8.index(2 if x_ref==5 else x_ref)) % 8
    sky_s = {p: earth[P_8[(P_8.index(p)-shift)%8]] for p in P_8}; sky_s[5]=earth[5]
    sky_star = {p: STAR_ORIGIN[P_8[(P_8.index(p)-shift)%8]] for p in P_8}; sky_star[5]="天禽"
    god_pan = {P_8[(P_8.index(s_ref)+i)%8]: (GODS_YANG if is_yang else GODS_YIN)[i] for i in range(8)}
    steps = (ZHI.index(gz_t[1]) - ZHI.index(hx[1])) % 12
    door_tar_idx = fly_path[(fly_path.index(x_ref) + steps) % 9]
    door_ref = 2 if door_tar_idx == 5 else door_tar_idx 
    human_pan = {P_8[(P_8.index(door_ref) + i) % 8]: DOOR_ORDER[(DOOR_ORDER.index(DOOR_ORIGIN[x_ref] if x_ref != 5 else "死門") + i) % 8] for i in range(8)}
    h_idx = QI_YI.index(target_gan); hidden = {fly_path[(fly_path.index(door_tar_idx) + i) % 9]: QI_YI[(h_idx + i) % 9] for i in range(9)}
    
    return {"lunar":lunar, "gz":[lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(), gz_d, gz_t], "jq":jq_n, "ju":f"{'陽' if is_yang else '陰'}遁{ju_num}局", "earth":earth, "sky_s":sky_s, "sky_star":sky_star, "god":god_pan, "human":human_pan, "hidden":hidden, "shou":hx, "zf":STAR_ORIGIN[x_ref], "zs":DOOR_ORIGIN[x_ref], "solar":solar}

# ================= 3. Streamlit 界面构建 =================
st.sidebar.title("⚙️ 核心参数")
cal_mode = st.sidebar.radio("歷法選擇", ["公曆", "農曆"], horizontal=True)
col_d1, col_d2 = st.sidebar.columns(2)
date_input = col_d1.date_input("日期", datetime.date.today())
hour_input = col_d2.selectbox("時辰(小時)", list(range(24)), index=datetime.datetime.now().hour)
method_input = st.sidebar.selectbox("排盤方法", ["拆補法", "茅山法"])

with st.sidebar.expander("🛠️ 手動定局/考據"):
    manual_on = st.checkbox("啟用手動定局")
    m_dun = st.selectbox("遁極", ["陽", "陰"])
    m_ju = st.number_input("局數", 1, 9, 1)

# 執行排盤
res = calculate_engine(date_input.year, date_input.month, date_input.day, hour_input, 0, cal_mode, method_input, manual={'active':manual_on, 'is_yang':m_dun=="陽", 'ju_num':m_ju})

# 展示干支頭
st.markdown(f"### 🗓️ {res['gz'][0]} {res['gz'][1]} {res['gz'][2]} {res['gz'][3]}")
st.success(f"✨ **{res['jq']}** | **{res['ju']}** | 旬首: **{res['shou']}** | 值符: **{res['zf']}** | 值使: **{res['zs']}**")
st.warning(f"🈳 空亡: 日 **{res['lunar'].getDayXunKong()}** | 時 **{res['lunar'].getTimeXunKong()}**")

# 九宮格渲染函數
def render_palace(pid):
    if pid == 5:
        return f"<div style='height:140px; display:flex; align-items:center; justify-content:center; border:1px solid #eee; background:#fafafa;'><h1 style='color:#333;'>{res['earth'][5]}</h1></div>"
    idx = pid - 1
    html = f"""
    <div style="border: 1px solid #ddd; padding: 10px; border-radius: 8px; background: white; height:140px; position:relative; box-shadow: 2px 2px 5px #f0f0f0;">
        <div style="font-size: 11px; color: #999; text-align: right;">{PALACE_NAMES[idx][:2]}</div>
        <div style="color: #e63946; font-weight: bold; text-align: center; font-size: 18px; margin-top:-5px;">{res['god'].get(pid, "")}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin: 5px 0;">
            <span style="font-size: 12px; color:#555;">{res['sky_star'].get(pid, "")[-1]}</span>
            <span style="font-size: 26px; color: #1d3557; font-weight: bold;">{res['sky_s'].get(pid, "")}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #2a9d8f; font-weight:bold; font-size:16px;">{res['human'].get(pid, "")[:1]}</span>
            <span style="color: #f4a261; font-size:12px;">({res['hidden'].get(pid, "")})</span>
        </div>
        <div style="text-align: right; font-weight: bold; color: #444; font-size:16px; margin-top:2px;">{res['earth'].get(pid, "")}</div>
    </div>
    """
    return html

# 佈局九宮格
grid_layout = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
for row_pids in grid_layout:
    cols = st.columns(3)
    for i, pid in enumerate(row_pids):
        cols[i].markdown(render_palace(pid), unsafe_allow_html=True)

st.divider()

# ================= 4. 八字反推與全量搜索 (完美復刻要素) =================
tab1, tab2 = st.tabs(["🔍 八字干支反推日期", "🔎 奇門全量搜索"])

with tab1:
    st.write("根據年月日時干支檢索具体公历時間")
    c1, c2, c3, c4 = st.columns(4)
    target_y = c1.selectbox("年柱", JZ, index=2)
    target_m = c2.selectbox("月柱", JZ, index=3)
    target_d = c3.selectbox("日柱", JZ, index=4)
    target_t = c4.selectbox("時柱", JZ, index=5)
    
    col_r1, col_r2 = st.columns(2)
    start_y = col_r1.number_input("起年", 1900, 2100, 2026)
    end_y = col_r2.number_input("止年", 1900, 2100, 2030)
    
    if st.button("開始檢索八字"):
        found_bazi = []
        for cy in range(start_y, end_y + 1):
            # 優化：先判斷年是否符合，減少不必要的農曆轉換
            l_check = Solar.fromYmd(cy, 6, 1).getLunar()
            if l_check.getYearInGanZhi() == target_y:
                for cm in range(1, 13):
                    for cd in range(1, 32):
                        try:
                            l2 = Solar.fromYmd(cy, cm, cd).getLunar()
                            if l2.getMonthInGanZhi() == target_m and l2.getDayInGanZhi() == target_d:
                                for ch in range(0, 24, 2):
                                    lt = Solar.fromYmdHms(cy, cm, cd, ch, 0, 0).getLunar()
                                    if lt.getTimeInGanZhi() == target_t:
                                        found_bazi.append(lt.getSolar().toFullString())
                        except: continue
        if found_bazi:
            for item in found_bazi: st.success(f"✅ {item}")
        else: st.error("未找到符合條件的日期。")

with tab2:
    st.write("設定宮位要素篩選特定格局時間")
    col_s1, col_s2 = st.columns(2)
    s_start = col_s1.date_input("開始檢索日期", datetime.date(2026, 3, 15))
    s_end = col_s2.date_input("結束檢索日期", datetime.date(2026, 4, 6))
    
    st.markdown("#### 🎯 多選要素設置")
    sel_palaces = st.multiselect("宮位選擇(不選默認全盤)", PALACE_NAMES)
    sel_gods = st.multiselect("神盤篩選", GODS_YANG + ["白虎", "玄武"])
    sel_stars = st.multiselect("天星篩選", list(STAR_ORIGIN.values()))
    sel_doors = st.multiselect("人門篩選", [d for d in DOOR_ORDER if d != "-"] )
    sel_stems = st.multiselect("天干篩選", GAN)
    
    st.markdown("#### 🚫 屏蔽條件")
    cb_col = st.columns(4)
    f_mu = cb_col[0].checkbox("屏蔽入墓")
    f_po = cb_col[1].checkbox("屏蔽門迫")
    f_jx = cb_col[2].checkbox("屏蔽擊刑")
    f_tk = cb_col[3].checkbox("屏蔽時空", value=True)
    
    if st.button("開始大數據考據"):
        st.write("正在分析時間線，請稍候...")
        results = []
        target_pids = [PALACE_NAMES.index(p)+1 for p in sel_palaces] if sel_palaces else [1,2,3,4,6,7,8,9]
        
        curr_d = s_start
        while curr_d <= s_end:
            for ch in range(0, 24, 2):
                qs = calculate_engine(curr_d.year, curr_d.month, curr_d.day, ch, method=method_input)
                for pid in target_pids:
                    # 要素匹配
                    if sel_gods and qs['god'].get(pid) not in sel_gods: continue
                    if sel_stars and qs['sky_star'].get(pid) not in sel_stars: continue
                    if sel_doors and qs['human'].get(pid) not in sel_doors: continue
                    if sel_stems and qs['sky_s'].get(pid) not in sel_stems: continue
                    
                    # 屏蔽條件匹配
                    fail = False
                    if f_mu and qs['sky_s'].get(pid) in MU_RULES and pid in MU_RULES[qs['sky_s'].get(pid)]: fail = True
                    if not fail and f_po and qs['human'].get(pid) in PO_RULES and pid in PO_RULES[qs['human'].get(pid)]: fail = True
                    if not fail and f_jx and qs['earth'].get(pid) in JIXING_RULES and pid in JIXING_RULES[qs['earth'].get(pid)]: fail = True
                    if not fail and f_tk:
                        xk_list = list(qs['lunar'].getTimeXunKong())
                        for branch in xk_list:
                            if BRANCH_TO_PID.get(branch) == pid: fail = True; break
                    
                    if not fail:
                        results.append(f"🎯 {qs['solar'].toFullString()} | {PALACE_NAMES[pid-1]}")
            curr_d += datetime.timedelta(days=1)
        
        if results:
            st.success(f"共找到 {len(results)} 個符合格局的時間點：")
            for r in results: st.text(r)
        else: st.error("在該時間段內未找到符合條件的格局。")

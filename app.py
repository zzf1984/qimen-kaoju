import streamlit as st
from lunar_python import Solar, Lunar
import datetime

# ================= 1. 核心常量与全屏CSS设置 =================
st.set_page_config(page_title="奇门·考据旗舰版", layout="wide")

# 自定义全屏CSS：针对九宫格美化
st.markdown("""
<style>
    .palace-box {
        border: 2px solid #4A90E2;
        border-radius: 10px;
        padding: 10px;
        background-color: #fcfcfc;
        height: 190px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .palace-name { font-size: 12px; color: #888; text-align: right; }
    .palace-god { font-size: 20px; color: #D0021B; font-weight: bold; text-align: center; }
    .palace-star-row { display: flex; justify-content: space-between; align-items: center; }
    .palace-star { font-size: 14px; color: #333; }
    .palace-sky { font-size: 30px; color: #4A90E2; font-weight: bold; }
    .palace-door-row { display: flex; justify-content: space-between; align-items: center; }
    .palace-door { font-size: 20px; color: #417505; font-weight: bold; }
    .palace-hidden { font-size: 14px; color: #F5A623; }
    .palace-earth { font-size: 20px; color: #333; font-weight: bold; text-align: right; }
</style>
""", unsafe_allow_html=True)

GAN, ZHI = list("甲乙丙丁戊己庚辛壬癸"), list("子丑寅卯辰巳午未申酉戌亥")
JZ = [GAN[x % 10] + ZHI[x % 12] for x in range(60)]
PALACE_NAMES = ["坎一宮", "坤二宮", "震三宮", "巽四宮", "中五宮", "乾六宮", "兌七宮", "艮八宮", "離九宮"]
GRID_ORDER = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
P_8, P_9 = [1, 8, 3, 4, 9, 2, 7, 6], [1, 2, 3, 4, 5, 6, 7, 8, 9]

STAR_ORIGIN = {1:"天蓬", 2:"天芮", 3:"天沖", 4:"天輔", 5:"天禽", 6:"天心", 7:"天柱", 8:"天任", 9:"天英"}
DOOR_ORIGIN = {1:"休門", 2:"死門", 3:"傷門", 4:"杜門", 5:"-", 6:"開門", 7:"驚門", 8:"生門", 9:"景門"}
DOOR_ORDER = ["休門", "生門", "傷門", "杜門", "景門", "死門", "驚門", "開門"]
QI_YI = list("戊己庚辛壬癸丁丙乙")
GODS_YANG = ["值符", "螣蛇", "太陰", "六合", "勾陳", "朱雀", "九地", "九天"]
GODS_YIN  = ["值符", "螣蛇", "太陰", "六合", "白虎", "玄武", "九地", "九天"]

JQ_RULES = {"立春":"八五二", "雨水":"九六三", "驚蟄":"一七四", "惊蛰":"一七四", "春分":"三九六", "清明":"四一七", "穀雨":"五二八", "谷雨":"五二八", "立夏":"四一七", "小滿":"五二八", "小满":"五二八", "芒種":"六三九", "芒种":"六三九", "夏至":"九三六", "小暑":"八二五", "大暑":"七一四", "立秋":"二五八", "處暑":"一四七", "处暑":"一四七", "白露":"九三六", "秋分":"七一四", "寒露":"六九三", "霜降":"五八二", "立冬":"六九三", "小雪":"五八二", "大雪":"四七一", "冬至":"一七四", "小寒":"二八五", "大寒":"三九六"}
MU_RULES = {'乙':[6],'丙':[6],'戊':[6],'丁':[8],'己':[8],'庚':[8],'辛':[4],'壬':[4],'癸':[2]}
PO_RULES = {'休門':[9],'生門':[1],'死門':[1],'傷門':[2,8],'杜門':[2,8],'景門':[6,7],'驚門':[3,4],'開門':[3,4]}
JIXING_RULES = {'戊':[3],'己':[2],'庚':[8],'辛':[9],'壬':[4],'癸':[4]}
BRANCH_TO_PID = {'子':1,'丑':8,'寅':8,'卯':3,'辰':4,'巳':4,'午':9,'未':2,'申':2,'酉':7,'戌':6,'亥':6}

# ================= 2. 核心状态初始化 (同步系统时间) =================
if 'curr_dt' not in st.session_state:
    st.session_state.curr_dt = datetime.datetime.now()

# 快捷跳转函数
def change_time(days=0, hours=0):
    st.session_state.curr_dt += datetime.timedelta(days=days, hours=hours)

# --- 側邊欄：輸入參數 ---
st.sidebar.title("⚙️ 排盤參數")

# 快捷导航按钮布局
nav_col1, nav_col2 = st.sidebar.columns(2)
if nav_col1.button("⬅️ 前一日"): change_time(days=-1)
if nav_col2.button("後一日 ➡️"): change_time(days=1)
nav_col3, nav_col4 = st.sidebar.columns(2)
if nav_col3.button("⏪ 前一時"): change_time(hours=-2)
if nav_col4.button("後一時 ⏩"): change_time(hours=2)

st.sidebar.divider()

# 同步小部件
date_val = st.sidebar.date_input("日期选择", st.session_state.curr_dt.date())
hour_val = st.sidebar.selectbox("小時选择", list(range(24)), index=st.session_state.curr_dt.hour)
# 反向更新状态 (确保手动选择也能同步)
st.session_state.curr_dt = datetime.datetime.combine(date_val, datetime.time(hour_val, 0))

method_input = st.sidebar.selectbox("排盤方法", ["拆補法", "茅山法"])
cal_mode = st.sidebar.radio("歷法轉換", ["公曆", "農曆"], horizontal=True)

with st.sidebar.expander("🛠️ 手動考據模式"):
    manual_on = st.checkbox("啟用手動模式")
    m_dun = st.selectbox("手動遁極", ["陽", "陰"])
    m_ju = st.number_input("手動局數", 1, 9, 1)

# ================= 3. 核心排盘引擎 =================
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
        yuan = ["上元", "中元", "下元"][yuan_idx % 3] 
        rule = JQ_RULES.get(jq_n, "一七四")
        num_str = "一二三四五六七八九"
        ju_num = num_str.index(rule[{"上元":0,"中元":1,"下元":2}[yuan]]) + 1

    fly_path = P_9 if is_yang else [9, 8, 7, 6, 5, 4, 3, 2, 1]
    earth = {p: QI_YI[(fly_path.index(p) - fly_path.index(ju_num)) % 9] for p in range(1, 10)}
    hx = JZ[(JZ.index(gz_t)//10)*10]; hx_yi = {"甲子":"戊","甲戌":"己","甲申":"庚","甲午":"辛","甲辰":"壬","甲寅":"癸"}[hx]
    x_ref = [k for k,v in earth.items() if v == hx_yi][0]
    hour_gan = gz_t[0]; target_gan = hx_yi if hour_gan == "甲" else hour_gan
    star_tar = [k for k,v in earth.items() if v == target_gan][0]
    s_ref_tar, s_ref_ori = (2 if star_tar == 5 else star_tar), (2 if x_ref == 5 else x_ref)
    shift = (P_8.index(s_ref_tar) - P_8.index(s_ref_ori)) % 8
    sky_s = {p: earth[P_8[(P_8.index(p)-shift)%8]] for p in P_8}; sky_s[5]=earth[5]
    sky_star = {p: STAR_ORIGIN[P_8[(P_8.index(p)-shift)%8]] for p in P_8}; sky_star[5]="天禽"
    god_pan = {P_8[(P_8.index(s_ref_tar)+i)%8]: (GODS_YANG if is_yang else GODS_YIN)[i] for i in range(8)}
    steps = (ZHI.index(gz_t[1]) - ZHI.index(hx[1])) % 12
    door_tar_idx = fly_path[(fly_path.index(x_ref) + steps) % 9]
    door_ref_tar = 2 if door_tar_idx == 5 else door_tar_idx 
    human_pan = {P_8[(P_8.index(door_ref_tar) + i) % 8]: DOOR_ORDER[(DOOR_ORDER.index(DOOR_ORIGIN[x_ref] if x_ref != 5 else "死門") + i) % 8] for i in range(8)}
    if door_tar_idx == 5: human_pan[5] = "死門"
    h_idx = QI_YI.index(target_gan); hidden = {fly_path[(fly_path.index(door_tar_idx) + i) % 9]: QI_YI[(h_idx + i) % 9] for i in range(9)}
    
    return {"lunar":lunar, "gz":[lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(), gz_d, gz_t], "jq":jq_n, "ju":f"{'陽' if is_yang else '陰'}遁{ju_num}局", "earth":earth, "sky_s":sky_s, "sky_star":sky_star, "god":god_pan, "human":human_pan, "hidden":hidden, "shou":hx, "zf":STAR_ORIGIN[x_ref], "zs":DOOR_ORIGIN[x_ref], "solar":solar}
# ================= 4. 九宮格渲染與界面展示 =================

# 執行排盤計算 (使用從第一部分同步過來的狀態)
res = calculate_engine(
    st.session_state.curr_dt.year, 
    st.session_state.curr_dt.month, 
    st.session_state.curr_dt.day, 
    st.session_state.curr_dt.hour, 
    0, cal_mode, method_input, 
    manual={'active': manual_on, 'is_yang': m_dun == "陽", 'ju_num': m_ju}
)

# --- 主界面：信息欄 ---
st.markdown(f"### 🗓️ {res['gz'][0]}年 {res['gz'][1]}月 {res['gz'][2]}日 {res['gz'][3]}時")
st.success(f"✨ **{res['jq']}** | **{res['ju']}** | 旬首: **{res['shou']}** | 值符: **{res['zf']}** | 值使: **{res['zs']}**")
st.info(f"🈳 空亡: 日 **{res['lunar'].getDayXunKong()}** | 時 **{res['lunar'].getTimeXunKong()}**")

# 九宮格 HTML 構造
def render_palace(pid):
    idx = pid - 1
    god = res['god'].get(pid, "")
    star = res['sky_star'].get(pid, "")
    sky_gan = res['sky_s'].get(pid, "")
    door = res['human'].get(pid, "")
    hidden_gan = res['hidden'].get(pid, "")
    earth_gan = res['earth'].get(pid, "")
    if pid == 5: star = "天禽" if star == "" else star
    
    html = f"""
    <div class="palace-box">
        <div class="palace-name">{PALACE_NAMES[idx]}</div>
        <div class="palace-god">{god}</div>
        <div class="palace-star-row">
            <span class="palace-star">{star}</span>
            <span class="palace-sky">{sky_gan}</span>
        </div>
        <div class="palace-door-row">
            <span class="palace-door">{door}</span>
            <span class="palace-hidden">({hidden_gan})</span>
        </div>
        <div class="palace-earth">{earth_gan}</div>
    </div>
    """
    return html

# 佈局渲染
for row_pids in GRID_ORDER:
    cols = st.columns(3)
    for i, pid in enumerate(row_pids):
        cols[i].markdown(render_palace(pid), unsafe_allow_html=True)

st.divider()

# ================= 5. 八字分離反推與全要素搜索 =================

tab_bazi, tab_search = st.tabs(["🔍 八字干支分離反推", "🔎 奇門全要素大數據搜索"])

# --- Tab 1: 八字分离反推 ---
with tab_bazi:
    st.write("精確設定四柱的八個字，檢索具體公曆時間。")
    c1, c2, c3, c4 = st.columns(4)
    with c1: yg, yz = st.selectbox("年干", GAN), st.selectbox("年支", ZHI)
    with c2: mg, mz = st.selectbox("月干", GAN, index=2), st.selectbox("月支", ZHI, index=2)
    with c3: dg, dz = st.selectbox("日干", GAN, index=4), st.selectbox("日支", ZHI, index=0)
    with c4: tg, tz = st.selectbox("時干", GAN, index=8), st.selectbox("時支", ZHI, index=0)
    
    col_r1, col_r2 = st.columns(2)
    s_y, e_y = col_r1.number_input("起年", 1900, 2100, 2026), col_r2.number_input("止年", 1900, 2100, 2030)
    
    if st.button("🚀 開始檢索八字"):
        found = []
        for cy in range(s_y, e_y + 1):
            if Solar.fromYmd(cy, 6, 1).getLunar().getYearInGanZhi() == (yg+yz):
                for cm in range(1, 13):
                    for cd in range(1, 32):
                        try:
                            l_d = Solar.fromYmd(cy, cm, cd).getLunar()
                            if l_d.getMonthInGanZhi() == (mg+mz) and l_d.getDayInGanZhi() == (dg+dz):
                                for ch in range(0, 24, 2):
                                    l_h = Solar.fromYmdHms(cy, cm, cd, ch, 0, 0).getLunar()
                                    if l_h.getTimeInGanZhi() == (tg+tz): found.append(l_h.getSolar().toFullString())
                        except: continue
        if found: 
            for t in found: st.success(f"✅ {t}")
        else: st.error("未找到符合條件的時間。")

# --- Tab 2: 全要素搜索 ---
with tab_search:
    st.write("設定宮位要素組合與屏蔽條件進行全量檢索。")
    col_s1, col_s2 = st.columns(2)
    s_start, s_end = col_s1.date_input("搜索起點", datetime.date(2026, 3, 15)), col_s2.date_input("搜索終點", datetime.date(2026, 4, 6))
    
    s_pals = st.multiselect("限定宮位", PALACE_NAMES)
    s_gods = st.multiselect("神盤", GODS_YANG + ["白虎", "玄武"])
    s_stars = st.multiselect("天星", list(STAR_ORIGIN.values()))
    s_doors = st.multiselect("人門", [d for d in DOOR_ORDER if d != "-"])
    cg1, cg2, cg3 = st.columns(3)
    s_skys = cg1.multiselect("天盤干", GAN)
    s_earths = cg2.multiselect("地盤干", GAN)
    s_hiddens = cg3.multiselect("暗干", GAN)
    
    f1, f2, f3, f4 = st.columns(4)
    f_mu, f_po, f_jx, f_xk = f1.checkbox("屏蔽入墓"), f2.checkbox("屏蔽門迫"), f3.checkbox("屏蔽擊刑"), f4.checkbox("屏蔽空亡", value=True)

    if st.button("🔥 開始大數據格局考據"):
        results = []
        pids = [PALACE_NAMES.index(p)+1 for p in s_pals] if s_pals else [1,2,3,4,6,7,8,9]
        curr = s_start
        while curr <= s_end:
            for ch in range(0, 24, 2):
                qs = calculate_engine(curr.year, curr.month, curr.day, ch, method=method_input)
                for pid in pids:
                    if (s_gods and qs['god'].get(pid) not in s_gods) or (s_stars and qs['sky_star'].get(pid) not in s_stars) or (s_doors and qs['human'].get(pid) not in s_doors) or (s_skys and qs['sky_s'].get(pid) not in s_skys) or (s_earths and qs['earth'].get(pid) not in s_earths) or (s_hiddens and qs['hidden'].get(pid) not in s_hiddens): continue
                    fail = False
                    if f_mu and qs['sky_s'].get(pid) in MU_RULES and pid in MU_RULES[qs['sky_s'].get(pid)]: fail = True
                    if not fail and f_po and qs['human'].get(pid) in PO_RULES and pid in PO_RULES[qs['human'].get(pid)]: fail = True
                    if not fail and f_jx and qs['earth'].get(pid) in JIXING_RULES and pid in JIXING_RULES[qs['earth'].get(pid)]: fail = True
                    if not fail and f_xk:
                        for b in list(qs['lunar'].getTimeXunKong()):
                            if BRANCH_TO_PID.get(b) == pid: fail = True; break
                    if not fail: results.append(f"🎯 {qs['solar'].toFullString()} | {PALACE_NAMES[pid-1]}")
            curr += datetime.timedelta(days=1)
        if results:
            st.success(f"找到 {len(results)} 個符合格局的時間：")
            for r in results: st.text(r)
        else: st.error("未找到符合格局。")

st.markdown("---")
st.caption("奇門遁甲考據系統 · 旗艦完滿導航版")

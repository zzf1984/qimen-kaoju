import streamlit as st
from lunar_python import Solar, Lunar
import datetime

# ================= 1. 全局配置与强力 3x3 移动端全景 CSS =================
st.set_page_config(page_title="奇门·全球考据旗舰版", layout="wide")

# 核心黑科技 CSS：强制在手机上保持 3x3 布局，不堆叠
st.markdown("""
<style>
    /* 强制 3x3 容器 */
    .qimen-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 5px;
        width: 100%;
        max-width: 800px;
        margin: 0 auto;
    }
    .palace-box {
        border: 1.5px solid #4A90E2; border-radius: 8px; padding: 8px;
        background-color: #fcfcfc; height: 165px; display: flex;
        flex-direction: column; justify-content: space-between;
        box-shadow: 1px 1px 5px rgba(0,0,0,0.05);
    }
    .palace-name { font-size: 10px; color: #888; text-align: right; margin-top: -5px; }
    .palace-god { font-size: 18px; color: #D0021B; font-weight: bold; text-align: center; }
    .palace-star-row { display: flex; justify-content: space-between; align-items: center; margin-top: -5px; }
    .palace-star { font-size: 12px; color: #333; }
    .palace-sky { font-size: 26px; color: #4A90E2; font-weight: bold; }
    .palace-door-row { display: flex; justify-content: space-between; align-items: center; margin-top: -5px; }
    .palace-door { font-size: 18px; color: #417505; font-weight: bold; }
    .palace-hidden { font-size: 12px; color: #F5A623; }
    .palace-earth { font-size: 18px; color: #333; font-weight: bold; text-align: right; margin-bottom: -5px; }
    
    /* 隐藏 Streamlit 默认的 padding，增加可视区域 */
    .main .block-container { padding-top: 2rem; padding-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

GAN, ZHI = list("甲乙丙丁戊己庚辛壬癸"), list("子丑寅卯辰巳午未申酉戌亥")
JZ = [GAN[x % 10] + ZHI[x % 12] for x in range(60)]
PALACE_NAMES = ["坎一宮", "坤二宮", "震三宮", "巽四宮", "中五宮", "乾六宮", "兌七宮", "艮八宮", "離九宮"]
GRID_ORDER = [3, 8, 1, 2, 4, 6, 7, 0, 5] # 对应索引映射 (巽,离,坤, 震,中,兑, 艮,坎,乾)

# ================= 2. 时间与时区/真太阳时核心 =================
def get_beijing_time():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

if 'curr_dt' not in st.session_state:
    st.session_state.curr_dt = get_beijing_time()

# 侧边栏：排盘参数
st.sidebar.title("🌍 全球考据设置")
utc_offset = st.sidebar.number_input("时区偏移 (UTC)", -12, 14, 8)
longitude = st.sidebar.number_input("所在地经度 (计算真太阳时)", 0.0, 180.0, 120.0)
use_solar_time = st.sidebar.checkbox("开启真太阳时校对", value=False)

# 快捷导航按钮
n1, n2 = st.sidebar.columns(2)
if n1.button("⬅️ 前一日"): st.session_state.curr_dt -= datetime.timedelta(days=1)
if n2.button("後一日 ➡️"): st.session_state.curr_dt += datetime.timedelta(days=1)
n3, n4 = st.sidebar.columns(2)
if n3.button("⏪ 前一時"): st.session_state.curr_dt -= datetime.timedelta(hours=2)
if n4.button("後一時 ⏩"): st.session_state.curr_dt += datetime.timedelta(hours=2)

st.sidebar.divider()

# 日期与分钟选择 (解除年份限制：1-3000年)
# 注意：Streamlit 的 date_input 限制最小为 0001-01-01
d_val = st.sidebar.date_input("选择日期", st.session_state.curr_dt.date(), min_value=datetime.date(1, 1, 1), max_value=datetime.date(3000, 12, 31))
h_val = st.sidebar.number_input("小时 (0-23)", 0, 23, st.session_state.curr_dt.hour)
m_val = st.sidebar.number_input("分钟 (0-59)", 0, 59, st.session_state.curr_dt.minute)

# 更新 Session State
st.session_state.curr_dt = datetime.datetime.combine(d_val, datetime.time(h_val, m_val))

# 真太阳时计算逻辑
working_dt = st.session_state.curr_dt
if use_solar_time:
    # 真太阳时 = 平太阳时 + (经度 - 120) * 4 分钟
    time_diff = (longitude - 120.0) * 4
    working_dt = working_dt + datetime.timedelta(minutes=time_diff)

method_in = st.sidebar.selectbox("排盤方法", ["拆補法", "茅山法"])
cal_in = st.sidebar.radio("歷法轉換", ["公曆", "農曆"], horizontal=True)

with st.sidebar.expander("🛠️ 手動考據"):
    man_on = st.checkbox("手動定局")
    man_dun = st.selectbox("遁", ["陽", "陰"])
    man_ju = st.number_input("局數", 1, 9, 1)
# ================= 3. 核心排盘引擎 (支持真太阳时与刻分) =================
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
P_8, P_9 = [1, 8, 3, 4, 9, 2, 7, 6], [1, 2, 3, 4, 5, 6, 7, 8, 9]

def calculate_engine(y, m, d, h, mi=0, cal_mode="公曆", method="拆補法", manual=None):
    if cal_mode == "公曆": solar = Solar.fromYmdHms(y, m, d, h, mi, 0); lunar = solar.getLunar()
    else: lunar = Lunar.fromYmdHms(y, m, d, h, mi, 0); solar = lunar.getSolar()
    gz_d, gz_t = str(lunar.getDayInGanZhi()), str(lunar.getTimeInGanZhi())
    prev_jq = lunar.getPrevJieQi(); jq_n = prev_jq.getName().split("(")[0]
    if manual and manual['active']: is_yang, ju_num = manual['is_yang'], manual['ju_num']
    else:
        yang_jqs = "冬至,小寒,大寒,立春,雨水,驚蟄,惊蛰,春分,清明,穀雨,谷雨,立夏,小滿,小满,芒種,芒种"
        is_yang = jq_n in yang_jqs.split(",")
        dt_target = datetime.datetime(solar.getYear(), solar.getMonth(), solar.getDay(), solar.getHour(), solar.getMinute())
        jq_solar = prev_jq.getSolar()
        dt_jq = datetime.datetime(jq_solar.getYear(), jq_solar.getMonth(), jq_solar.getDay(), jq_solar.getHour(), jq_solar.getMinute())
        diff_days = (dt_target - dt_jq).total_seconds() / 86400.0
        yuan = ["上元", "中元", "下元"][int(diff_days // 5) % 3] 
        rule = JQ_RULES.get(jq_n, "一七四"); ju_num = "一二三四五六七八九".index(rule[{"上元":0,"中元":1,"下元":2}[yuan]]) + 1
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

# ================= 4. 界面渲染 (3x3 强制全景显示) =================
# 执行计算 (使用 working_dt，包含经纬度修正)
res = calculate_engine(working_dt.year, working_dt.month, working_dt.day, working_dt.hour, working_dt.minute, cal_in, method_in, manual={'active': man_on, 'is_yang': man_dun == "陽", 'ju_num': man_ju})

# 顶部标题栏
st.markdown(f"### 🗓️ 公元 {res['solar'].getYear()}年 {res['solar'].getMonth()}月 {res['solar'].getDay()}日 {res['solar'].getHour()}時{res['solar'].getMinute()}分{' (真太陽時)' if use_solar_time else ''}")
st.success(f"✨ **{res['jq']}** | **{res['ju']}** | 旬首: **{res['shou']}** | 值符: **{res['zf']}** | 值使: **{res['zs']}**")
st.info(f"🈳 空亡: 日 **{res['lunar'].getDayXunKong()}** | 時 **{res['lunar'].getTimeXunKong()}**")

# 构造九宫格 HTML
def get_palace_html(pid):
    idx = pid - 1
    god = res['god'].get(pid, "")
    star = res['sky_star'].get(pid, "")
    sky_gan = res['sky_s'].get(pid, "")
    door = res['human'].get(pid, "")
    hidden_gan = res['hidden'].get(pid, "")
    earth_gan = res['earth'].get(pid, "")
    if pid == 5: star = "天禽" if star == "" else star
    
    return f"""
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

# 渲染 3x3 九宫格 (巽,离,坤, 震,中,兑, 艮,坎,乾)
grid_html = "<div class='qimen-grid'>"
for pid_idx in GRID_ORDER:
    grid_html += get_palace_html(pid_idx + 1)
grid_html += "</div>"

st.markdown(grid_html, unsafe_allow_html=True)
st.divider()
# ================= 5. 千年跨度：八字分離精確反推 (1-3000年) =================

st.header("🔍 歷史考據：八字分離精確反推")
st.write("設定年月日時的八個字，系統將在 3000 年時間跨度內進行“跳躍式”高效檢索。")

with st.expander("點擊展開：八字反推設定", expanded=False):
    # 建立 8 列布局，实现八位分离
    c_y1, c_y2, c_m1, c_m2, c_d1, c_d2, c_t1, c_t2 = st.columns(8)
    y_g = c_y1.selectbox("年干", GAN, key="sy_g")
    y_z = c_y2.selectbox("年支", ZHI, key="sy_z")
    m_g = c_m1.selectbox("月干", GAN, key="sm_g", index=2)
    m_z = c_m2.selectbox("月支", ZHI, key="sm_z", index=2)
    d_g = c_d1.selectbox("日干", GAN, key="sd_g", index=4)
    d_z = c_d2.selectbox("日支", ZHI, key="sd_z", index=0)
    t_g = c_t1.selectbox("時干", GAN, key="st_g", index=8)
    t_z = c_t2.selectbox("時支", ZHI, key="st_z", index=0)
    
    col_range1, col_range2 = st.columns(2)
    search_s_y = col_range1.number_input("檢索起點(公元)", 1, 3000, 960) # 默認北宋
    search_e_y = col_range2.number_input("檢索終點(公元)", 1, 3000, 2030)
    
    if st.button("🚀 啟動千年八字跳躍檢索"):
        t_y, t_m, t_d, t_t = y_g+y_z, m_g+m_z, d_g+d_z, t_g+t_z
        found_bazi = []
        
        # 算法優化：每60年跳躍一次，極速檢索
        first_match_y = -1
        for y in range(search_s_y, search_s_y + 61):
            if Solar.fromYmd(y, 6, 1).getLunar().getYearInGanZhi() == t_y:
                first_match_y = y; break
        
        if first_match_y == -1:
            st.error("該年柱干支配置無效，請檢查。")
        else:
            for cy in range(first_match_y, search_e_y + 1, 60):
                for cm in range(1, 13):
                    # 快速初步過濾月柱
                    if Solar.fromYmd(cy, cm, 15).getLunar().getMonthInGanZhi() == t_m:
                        for cd in range(1, 32):
                            try:
                                l_d = Solar.fromYmd(cy, cm, cd).getLunar()
                                if l_d.getDayInGanZhi() == t_d:
                                    for ch in range(0, 24, 2):
                                        l_h = Solar.fromYmdHms(cy, cm, cd, ch, 0, 0).getLunar()
                                        if l_h.getTimeInGanZhi() == t_t:
                                            found_bazi.append(l_h.getSolar().toFullString())
                            except: continue
            
            if found_bazi:
                st.success(f"✅ 檢索完成！共找到 {len(found_bazi)} 個匹配時間：")
                for f in found_bazi: st.write(f)
            else:
                st.error("❌ 未找到符合該八字組合的時間。")

# ================= 6. 奇門全要素格局搜索 (支持地盤干/暗干/刻分) =================

st.header("🔎 奇門全要素大數據考據")
st.write("設定宮位要素組合與屏蔽條件，精確定位歷史中的特定格局。")

with st.expander("點擊展開：全要素篩選條件", expanded=False):
    col_s1, col_s2 = st.columns(2)
    q_start = col_s1.date_input("搜索起始日期", datetime.date(2026, 3, 15), key="q_s")
    q_end = col_s2.date_input("搜索結束日期", datetime.date(2026, 4, 6), key="q_e")
    
    st.markdown("#### 🎯 要素篩選 (多選，不選則全盤掃描)")
    q_pals = st.multiselect("限定宮位", PALACE_NAMES)
    q_gods = st.multiselect("神盤", GODS_YANG + ["白虎", "玄武"])
    q_stars = st.multiselect("天星", list(STAR_ORIGIN.values()))
    q_doors = st.multiselect("人門", [d for d in DOOR_ORDER if d != "-"])
    
    qc1, qc2, qc3 = st.columns(3)
    q_skys = qc1.multiselect("天盤干", GAN)
    q_earths = qc2.multiselect("地盤干", GAN)
    q_hiddens = qc3.multiselect("暗干", GAN)
    
    st.markdown("#### 🚫 缺陷屏蔽 (攔截瑕疵格局)")
    qf1, qf2, qf3, qf4 = st.columns(4)
    q_mu = qf1.checkbox("屏蔽：入墓", value=False)
    q_po = qf2.checkbox("屏蔽：門迫", value=False)
    q_jx = qf3.checkbox("屏蔽：擊刑", value=False)
    q_xk = qf4.checkbox("屏蔽：空亡", value=True)

    if st.button("🔥 啟動全要素格局掃描"):
        q_results = []
        t_pids = [PALACE_NAMES.index(p)+1 for p in q_pals] if q_pals else [1,2,3,4,6,7,8,9]
        
        curr_d = q_start
        while curr_d <= q_end:
            for ch in range(0, 24, 2):
                # 如果需要分钟级考据，此处可改为更细的步长
                qs = calculate_engine(curr_d.year, curr_d.month, curr_d.day, ch, 0, method=method_in)
                for pid in t_pids:
                    # 要素匹配
                    if q_gods and qs['god'].get(pid) not in q_gods: continue
                    if q_stars and qs['sky_star'].get(pid) not in q_stars: continue
                    if q_doors and qs['human'].get(pid) not in q_doors: continue
                    if q_skys and qs['sky_s'].get(pid) not in q_skys: continue
                    if q_earths and qs['earth'].get(pid) not in q_earths: continue
                    if q_hiddens and qs['hidden'].get(pid) not in q_hiddens: continue
                    
                    # 屏蔽逻辑
                    fail = False
                    if q_mu and qs['sky_s'].get(pid) in MU_RULES and pid in MU_RULES[qs['sky_s'].get(pid)]: fail = True
                    if not fail and q_po and qs['human'].get(pid) in PO_RULES and pid in PO_RULES[qs['human'].get(pid)]: fail = True
                    if not fail and q_jx and qs['earth'].get(pid) in JIXING_RULES and pid in JIXING_RULES[qs['earth'].get(pid)]: fail = True
                    if not fail and q_xk:
                        for b in list(qs['lunar'].getTimeXunKong()):
                            if BRANCH_TO_PID.get(b) == pid: fail = True; break
                    
                    if not fail:
                        q_results.append(f"🎯 {qs['solar'].toFullString()} | {PALACE_NAMES[pid-1]}")
            curr_d += datetime.timedelta(days=1)
            
        if q_results:
            st.success(f"考據完成！找到 {len(q_results)} 個符合格局的時間：")
            for item in q_results: st.text(item)
        else:
            st.error("所選時間段內未發現符合條件的格局。")

st.markdown("---")
st.caption("奇門遁甲考據系統 · 旗艦完滿版 | 支持北京/全球時區 | 真太陽時校對 | 0-3000年跨度")

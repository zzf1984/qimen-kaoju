import streamlit as st
from lunar_python import Solar, Lunar
import datetime

# ================= 1. 全局配置与 3x3 视觉辅助 CSS =================
st.set_page_config(page_title="奇门·全球考据旗舰版", layout="wide")

# 核心 CSS：强制手机 3x3 全景，并配置值符/值使/空亡背景色
st.markdown("""
<style>
    .qimen-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 5px; width: 100%; max-width: 900px; margin: 0 auto;
    }
    .palace-box {
        border: 2px solid #4A90E2; border-radius: 8px; padding: 8px;
        height: 175px; display: flex; flex-direction: column; 
        justify-content: space-between; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        position: relative; overflow: hidden;
    }
    /* 核心文字样式 */
    .palace-name { font-size: 10px; color: #888; text-align: right; z-index: 5; }
    .palace-god { font-size: 19px; color: #D32F2F; font-weight: bold; text-align: center; z-index: 5; }
    .palace-star-row { display: flex; justify-content: space-around; align-items: center; z-index: 5; }
    .palace-star { font-size: 12px; color: #424242; font-weight: bold; }
    .palace-sky { font-size: 30px; color: #1976D2; font-weight: bold; }
    .palace-door-row { display: flex; justify-content: space-around; align-items: center; z-index: 5; }
    .palace-door { font-size: 19px; color: #388E3C; font-weight: bold; }
    .palace-hidden { font-size: 13px; color: #F57C00; font-weight: bold; }
    .palace-earth { font-size: 20px; color: #000000; font-weight: bold; text-align: right; z-index: 5; }
    
    /* 顶部八字栏样式 */
    .bazi-header {
        background-color: #f0f7ff; padding: 10px; border-radius: 8px;
        text-align: center; margin-bottom: 10px; border: 1px solid #cce5ff;
    }
    .main .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# --- 常量定义 ---
GAN, ZHI = list("甲乙丙丁戊己庚辛壬癸"), list("子丑寅卯辰巳午未申酉戌亥")
JZ = [GAN[x % 10] + ZHI[x % 12] for x in range(60)]
PALACE_NAMES = ["坎一宮", "坤二宮", "震三宮", "巽四宮", "中五宮", "乾六宮", "兌七宮", "艮八宮", "離九宮"]
GRID_ORDER = [3, 8, 1, 2, 4, 6, 7, 0, 5] # 巽,离,坤, 震,中,兑, 艮,坎,乾
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

# ================= 2. 时间同步与时区/真太阳时校对 =================
# 强制设定北京时间 UTC+8
tz_beijing = datetime.timezone(datetime.timedelta(hours=8))
if 'curr_dt' not in st.session_state:
    st.session_state.curr_dt = datetime.datetime.now(tz_beijing)

st.sidebar.title("🌍 全球考据设置")
utc_off = st.sidebar.number_input("时区偏移 (UTC)", -12, 14, 8)
lon_val = st.sidebar.number_input("经度 (计算真太阳时)", 0.0, 180.0, 120.0)
use_solar = st.sidebar.checkbox("开启真太阳时校对", value=False)

def change_t(d=0, h=0):
    st.session_state.curr_dt += datetime.timedelta(days=d, hours=h)

c1, c2 = st.sidebar.columns(2)
if c1.button("⬅️ 前一日"): change_t(d=-1)
if c2.button("後一日 ➡️"): change_t(d=1)
c3, c4 = st.sidebar.columns(2)
if c3.button("⏪ 前一時"): change_t(h=-2)
if c4.button("後一時 ⏩"): change_t(h=2)

st.sidebar.divider()
# 解除 1900 限制的数字输入
col_y, col_m, col_d = st.sidebar.columns(3)
sy = col_y.number_input("年", 1, 3000, st.session_state.curr_dt.year)
sm = col_m.number_input("月", 1, 12, st.session_state.curr_dt.month)
sd = col_d.number_input("日", 1, 31, st.session_state.curr_dt.day)
col_h, col_mi = st.sidebar.columns(2)
sh = col_h.number_input("時", 0, 23, st.session_state.curr_dt.hour)
smi = col_mi.number_input("分", 0, 59, st.session_state.curr_dt.minute)

if st.sidebar.button("🚀 执行考据排盘", use_container_width=True):
    st.session_state.curr_dt = datetime.datetime(sy, sm, sd, sh, smi)

# 计算实际时间
working_dt = st.session_state.curr_dt
if use_solar:
    solar_diff = (lon_val - (utc_off * 15)) * 4
    working_dt = working_dt + datetime.timedelta(minutes=solar_diff)

meth_in = st.sidebar.selectbox("排盤方法", ["拆補法", "茅山法"])
cal_in = st.sidebar.radio("歷法轉換", ["公曆", "農曆"], horizontal=True)

with st.sidebar.expander("🛠️ 手動模式"):
    man_on = st.checkbox("手動")
    man_dun = st.selectbox("遁", ["陽", "陰"])
    man_ju = st.number_input("局數", 1, 9, 1)

# ================= 3. 核心排盘引擎 =================
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
    xk_pids = [BRANCH_TO_PID.get(b) for b in list(lunar.getTimeXunKong())]
    return {"lunar":lunar, "gz":[lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(), gz_d, gz_t], "jq":jq_n, "ju":f"{'陽' if is_yang else '陰'}遁{ju_num}局", "earth":earth, "sky_s":sky_s, "sky_star":sky_star, "god":god_pan, "human":human_pan, "hidden":hidden, "shou":hx, "zf_pid":s_ref_tar, "zs_pid":door_ref_tar, "xk_pids":xk_pids, "solar":solar}

# ================= 4. 九宫排盘渲染 =================
res = calculate_engine(working_dt.year, working_dt.month, working_dt.day, working_dt.hour, working_dt.minute, cal_in, meth_in, manual={'active': man_on, 'is_yang': man_dun == "陽", 'ju_num': man_ju})

# 顶部八字同框
st.markdown(f"""
<div class="bazi-header">
    <div style="font-size:11px; color:#666;">公元 {res['solar'].getYear()}年{res['solar'].getMonth()}月{res['solar'].getDay()}日 {res['solar'].getHour()}時{res['solar'].getMinute()}分 {'(真太陽時校對)' if use_solar else ''}</div>
    <div style="display:flex; justify-content:space-around; margin-top:5px;">
        <div style="text-align:center;"><div style="font-size:10px; color:grey;">年柱</div><div style="font-size:19px; font-weight:bold;">{res['gz'][0]}</div></div>
        <div style="text-align:center;"><div style="font-size:10px; color:grey;">月柱</div><div style="font-size:19px; font-weight:bold;">{res['gz'][1]}</div></div>
        <div style="text-align:center;"><div style="font-size:10px; color:grey;">日柱</div><div style="font-size:19px; font-weight:bold;">{res['gz'][2]}</div></div>
        <div style="text-align:center;"><div style="font-size:10px; color:grey;">时柱</div><div style="font-size:19px; font-weight:bold;">{res['gz'][3]}</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

st.success(f"✨ **{res['jq']}** | **{res['ju']}** | 旬首: **{res['shou']}** | 空亡: 時 **{res['lunar'].getTimeXunKong()}**")

def get_palace_html(pid):
    idx, is_xk, is_zf, is_zs = pid-1, pid in res['xk_pids'], pid == res['zf_pid'], pid == res['zs_pid']
    bg = "background-color:#ffffff;"
    if is_xk: bg = "background-color:#eeeeee;" # 空亡灰
    elif is_zf and is_zs: bg = "background-color:#fff59d;" # 叠黄
    elif is_zf: bg = "background:linear-gradient(to bottom, #fff59d 50%, #ffffff 50%);" # 值符上半
    elif is_zs: bg = "background:linear-gradient(to top, #fff59d 50%, #ffffff 50%);" # 值使下半
    
    g, s, sky = res['god'].get(pid,""), res['sky_star'].get(pid,""), res['sky_s'].get(pid,"")
    d, h, e = res['human'].get(pid,""), res['hidden'].get(pid,""), res['earth'].get(pid,"")
    if pid == 5: s = "天禽" if s=="" else s
    return f'<div class="palace-box" style="{bg}"><div class="palace-name">{PALACE_NAMES[idx]}</div><div class="palace-god">{g}</div><div class="palace-star-row"><span class="palace-star">{s}</span><span class="palace-sky">{sky}</span></div><div class="palace-door-row"><span class="palace-door">{door}</span><span class="palace-hidden">({h})</span></div><div class="palace-earth">{e}</div></div>'

gh = '<div class="qimen-grid">'
for p_idx in GRID_ORDER: gh += get_palace_html(p_idx+1)
st.markdown(gh + '</div>', unsafe_allow_html=True)
st.divider()

# ================= 5. 千年反推与全量搜索 =================
tab_b, tab_s = st.tabs(["🔍 八字精確反推", "🔎 全要素格局搜索"])

with tab_b:
    cy1, cy2, cm1, cm2, cd1, cd2, ct1, ct2 = st.columns(8)
    yg, yz = cy1.selectbox("年干", GAN), cy2.selectbox("年支", ZHI)
    mg, mz = cm1.selectbox("月干", GAN, index=2), cm2.selectbox("月支", ZHI, index=2)
    dg, dz = cd1.selectbox("日干", GAN, index=4), cd2.selectbox("日支", ZHI, index=0)
    tg, tz = ct1.selectbox("時干", GAN, index=8), ct2.selectbox("時支", ZHI, index=0)
    cr1, cr2 = st.columns(2)
    sby, sey = cr1.number_input("起年", 0, 3000, 960), cr2.number_input("止年", 0, 3000, 2030)
    if st.button("🚀 开始跳跃式检测"):
        found, t_y, t_m, t_d, t_t = [], yg+yz, mg+mz, dg+dz, tg+tz
        fy = -1
        for y in range(sby, sby+61):
            try:
                if Solar.fromYmd(y, 6, 1).getLunar().getYearInGanZhi() == t_y: fy=y; break
            except: continue
        if fy != -1:
            for cy in range(fy, sey+1, 60):
                for cm in range(1, 13):
                    try:
                        if Solar.fromYmd(cy, cm, 15).getLunar().getMonthInGanZhi() == t_m:
                            for cd in range(1, 32):
                                l_d = Solar.fromYmd(cy, cm, cd).getLunar()
                                if l_d.getDayInGanZhi() == t_d:
                                    for ch in range(0, 24, 2):
                                        l_h = Solar.fromYmdHms(cy, cm, cd, ch, 0, 0).getLunar()
                                        if l_h.getTimeInGanZhi() == t_t: found.append(l_h.getSolar().toFullString())
                    except: continue
        for f in found: st.write(f"✅ {f}")

with tab_s:
    # 搜索逻辑保留之前精准逻辑
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    qy, qm, qd = sc1.number_input("起年", 0, 3000, 2026), sc2.number_input("月", 1, 12, 3), sc3.number_input("日", 1, 31, 15)
    ey, ed = sc4.number_input("止年", 0, 3000, 2026), sc5.number_input("天数", 1, 365, 30)
    q_pal, q_god, q_star, q_door = st.multiselect("宫位", PALACE_NAMES), st.multiselect("神盘", GODS_YANG+["白虎","玄武"]), st.multiselect("天星", list(STAR_ORIGIN.values())), st.multiselect("人门", [d for d in DOOR_ORDER if d!="-"])
    qc1, qc2, qc3 = st.columns(3)
    q_sky, q_earth, q_hidden = qc1.multiselect("天干", GAN), qc2.multiselect("地干", GAN), qc3.multiselect("暗干", GAN)
    f1, f2, f3, f4 = st.columns(4)
    q_mu, q_po, q_jx, q_xk = f1.checkbox("屏蔽：入墓"), f2.checkbox("屏蔽：门迫"), f3.checkbox("屏蔽：击刑"), f4.checkbox("屏蔽：空亡", value=True)
    if st.button("🔥 开始全要素大數據搜索"):
        res_s, pids = [], [PALACE_NAMES.index(p)+1 for p in q_pal] if q_pal else [1,2,3,4,6,7,8,9]
        for i in range(int(ed)):
            cur_d = datetime.date(qy, qm, qd) + datetime.timedelta(days=i)
            for ch in range(0, 24, 2):
                qs = calculate_engine(cur_d.year, cur_d.month, cur_d.day, ch, 0, method=meth_in)
                for pid in pids:
                    if (q_god and qs['god'].get(pid) not in q_god) or (q_star and qs['sky_star'].get(pid) not in q_star) or (q_door and qs['human'].get(pid) not in q_door) or (q_sky and qs['sky_s'].get(pid) not in q_sky) or (q_earth and qs['earth'].get(pid) not in q_earth) or (q_hidden and qs['hidden'].get(pid) not in q_hidden): continue
                    fail = False
                    if q_mu and qs['sky_s'].get(pid) in MU_RULES and pid in MU_RULES[qs['sky_s'].get(pid)]: fail = True
                    if not fail and q_po and qs['human'].get(pid) in PO_RULES and pid in PO_RULES[qs['human'].get(pid)]: fail = True
                    if not fail and q_jx and qs['earth'].get(pid) in JIXING_RULES and pid in JIXING_RULES[qs['earth'].get(pid)]: fail = True
                    if not fail and q_xk and pid in qs['xk_pids']: fail = True
                    if not fail: res_s.append(f"🎯 {qs['solar'].toFullString()} | {PALACE_NAMES[pid-1]}")
        for r in res_s: st.text(r)

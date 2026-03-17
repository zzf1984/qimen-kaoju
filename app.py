import streamlit as st
from lunar_python import Solar, Lunar
import datetime

# ================= 1. 核心常量与全屏CSS设置 =================
st.set_page_config(page_title="奇门·考据旗舰版(历史增强型)", layout="wide")

# 强制全屏CSS
st.markdown("""
<style>
    .palace-box {
        border: 2px solid #4A90E2; border-radius: 10px; padding: 10px;
        background-color: #fcfcfc; height: 195px; display: flex;
        flex-direction: column; justify-content: space-between;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 10px;
    }
    .palace-name { font-size: 12px; color: #888; text-align: right; }
    .palace-god { font-size: 21px; color: #D0021B; font-weight: bold; text-align: center; }
    .palace-star-row { display: flex; justify-content: space-between; align-items: center; }
    .palace-star { font-size: 14px; color: #333; }
    .palace-sky { font-size: 32px; color: #4A90E2; font-weight: bold; }
    .palace-door-row { display: flex; justify-content: space-between; align-items: center; }
    .palace-door { font-size: 20px; color: #417505; font-weight: bold; }
    .palace-hidden { font-size: 14px; color: #F5A623; }
    .palace-earth { font-size: 22px; color: #333; font-weight: bold; text-align: right; }
</style>
""", unsafe_allow_html=True)

GAN, ZHI = list("甲乙丙丁戊己庚辛壬癸"), list("子丑寅卯辰巳午未申酉戌亥")
JZ = [GAN[x % 10] + ZHI[x % 12] for x in range(60)]
PALACE_NAMES = ["坎一宮", "坤二宮", "震三宮", "巽四宮", "中五宮", "乾六宮", "兌七宮", "艮八宮", "離九宮"]
GRID_ORDER = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
P_8, P_9 = [1, 8, 3, 4, 9, 2, 7, 6], [1, 2, 3, 4, 5, 6, 7, 8, 9]

# ================= 2. 北京时间同步逻辑 (修复时差) =================
# 强制设定为东八区时间
tz_beijing = datetime.timezone(datetime.timedelta(hours=8))
if 'curr_dt' not in st.session_state:
    st.session_state.curr_dt = datetime.datetime.now(tz_beijing)

def change_time(days=0, hours=0):
    st.session_state.curr_dt += datetime.timedelta(days=days, hours=hours)

# --- 側邊欄：輸入參數 ---
st.sidebar.title("⚙️ 排盤參數")

# 快捷导航按钮
n1, n2 = st.sidebar.columns(2)
if n1.button("⬅️ 前一日"): change_time(days=-1)
if n2.button("後一日 ➡️"): change_time(days=1)
n3, n4 = st.sidebar.columns(2)
if n3.button("⏪ 前一時"): change_time(hours=-2)
if n4.button("後一時 ⏩"): change_time(hours=2)

st.sidebar.divider()

# 同步时间选择器
d_val = st.sidebar.date_input("日期选择", st.session_state.curr_dt.date())
h_val = st.sidebar.selectbox("時辰(小時)", list(range(24)), index=st.session_state.curr_dt.hour)
st.session_state.curr_dt = datetime.datetime.combine(d_val, datetime.time(h_val, 0))

method_in = st.sidebar.selectbox("排盤方法", ["拆補法", "茅山法"])
cal_in = st.sidebar.radio("歷法轉換", ["公曆", "農曆"], horizontal=True)

with st.sidebar.expander("🛠️ 手動考據/定局模式"):
    man_on = st.checkbox("啟用手動模式")
    man_dun = st.selectbox("手動遁極", ["陽", "陰"])
    man_ju = st.number_input("手動局數", 1, 9, 1)

# ================= 3. 历史增强型排盘引擎 =================
# (常量定义：星、门、神、局数规则等)
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

def calculate_engine(y, m, d, h, mi=0, cal_mode="公曆", method="拆補法", manual=None):
    if cal_mode == "公曆": solar = Solar.fromYmdHms(y, m, d, h, mi, 0); lunar = solar.getLunar()
    else: lunar = Lunar.fromYmdHms(y, m, d, h, mi, 0); solar = lunar.getSolar()
    gz_d, gz_t = str(lunar.getDayInGanZhi()), str(lunar.getTimeInGanZhi())
    prev_jq = lunar.getPrevJieQi(); jq_n = prev_jq.getName().split("(")[0]
    if manual and manual['active']: is_yang, ju_num = manual['is_yang'], manual['ju_num']
    else:
        yang_jqs = "冬至,小寒,大寒,立春,雨水,驚蟄,惊蛰,春分,清明,穀雨,谷雨,立夏,小滿,小满,芒種,芒种"
        is_yang = jq_n in yang_jqs.split(",")
        dt_now = datetime.datetime(solar.getYear(), solar.getMonth(), solar.getDay(), solar.getHour(), solar.getMinute(), solar.getSecond())
        jq_solar = prev_jq.getSolar()
        dt_jq = datetime.datetime(jq_solar.getYear(), jq_solar.getMonth(), jq_solar.getDay(), jq_solar.getHour(), jq_solar.getMinute(), jq_solar.getSecond())
        diff_days = (dt_now - dt_jq).total_seconds() / 86400.0
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
# ================= 4. 九宮格渲染與界面展示 =================

# 執行當前排盤 (使用北京時間同步過來的 session_state)
res = calculate_engine(
    st.session_state.curr_dt.year, 
    st.session_state.curr_dt.month, 
    st.session_state.curr_dt.day, 
    st.session_state.curr_dt.hour, 
    0, cal_in, method_in, 
    manual={'active': man_on, 'is_yang': man_dun == "陽", 'ju_num': man_ju}
)

# --- 主界面：頂部信息 ---
st.markdown(f"### 🗓️ 公元 {res['solar'].getYear()}年 {res['solar'].getMonth()}月 {res['solar'].getDay()}日 | {res['gz'][3]}")
st.success(f"✨ **{res['jq']}** | **{res['ju']}** | 旬首: **{res['shou']}** | 值符: **{res['zf']}** | 值使: **{res['zs']}**")
st.warning(f"🈳 空亡: 日 **{res['lunar'].getDayXunKong()}** | 時 **{res['lunar'].getTimeXunKong()}**")

# 九宮格 HTML 構造
def render_palace(pid):
    idx = pid - 1
    g, s, sky = res['god'].get(pid, ""), res['sky_star'].get(pid, ""), res['sky_s'].get(pid, "")
    d, h, e = res['human'].get(pid, ""), res['hidden'].get(pid, ""), res['earth'].get(pid, "")
    if pid == 5: s = "天禽" if s == "" else s
    
    return f"""
    <div class="palace-box">
        <div class="palace-name">{PALACE_NAMES[idx]}</div>
        <div class="palace-god">{g}</div>
        <div class="palace-star-row">
            <span class="palace-star">{s}</span>
            <span class="palace-sky">{sky}</span>
        </div>
        <div class="palace-door-row">
            <span class="palace-door">{d}</span>
            <span class="palace-hidden">({h})</span>
        </div>
        <div class="palace-earth">{e}</div>
    </div>
    """

# 佈局九宮格
for row_pids in GRID_ORDER:
    cols = st.columns(3)
    for i, pid in enumerate(row_pids):
        cols[i].markdown(render_palace(pid), unsafe_allow_html=True)

st.divider()

# ================= 5. 千年跨度八字分離反推 (0-3000年) =================

st.header("🔍 歷史考據：八字分離精確反推")
st.write("設定年月日時的八個字，系統將在 3000 年時間跨度內進行“跳躍式”高效檢索。")

with st.expander("點擊展開：八字分離設定與搜索", expanded=False):
    # 八位分離選擇
    c_y1, c_y2, c_m1, c_m2, c_d1, c_d2, c_t1, c_t2 = st.columns(8)
    y_g = c_y1.selectbox("年干", GAN); y_z = c_y2.selectbox("年支", ZHI)
    m_g = c_m1.selectbox("月干", GAN, index=2); m_z = c_m2.selectbox("月支", ZHI, index=2)
    d_g = c_d1.selectbox("日干", GAN, index=4); d_z = c_d2.selectbox("日支", ZHI, index=0)
    t_g = c_t1.selectbox("時干", GAN, index=8); t_z = c_t2.selectbox("時支", ZHI, index=0)
    
    col_range1, col_range2 = st.columns(2)
    search_s_y = col_range1.number_input("檢索起點(公元)", 0, 3000, 960) # 默認宋朝建立左右
    search_e_y = col_range2.number_input("檢索終點(公元)", 0, 3000, 2030)
    
    if st.button("🚀 開始千年大數據檢索"):
        t_y, t_m, t_d, t_t = y_g+y_z, m_g+m_z, d_g+d_z, t_g+t_z
        found_list = []
        
        # 算法優化：跳躍式檢索
        # 1. 找到第一個符合年柱的年份
        first_y = -1
        for y in range(search_s_y, search_s_y + 61):
            if Solar.fromYmd(y, 6, 1).getLunar().getYearInGanZhi() == t_y:
                first_y = y; break
        
        if first_y == -1:
            st.error("該年柱干支在歷史循環中配置異常。")
        else:
            # 2. 以60年為步長跳躍搜索
            for cy in range(first_y, search_e_y + 1, 60):
                for cm in range(1, 13):
                    # 快速檢查月柱 (月干支由年干決定，可進一步優化，此處保留邏輯嚴密性)
                    l_m = Solar.fromYmd(cy, cm, 15).getLunar()
                    if l_m.getMonthInGanZhi() == t_m:
                        for cd in range(1, 32):
                            try:
                                l_d = Solar.fromYmd(cy, cm, cd).getLunar()
                                if l_d.getDayInGanZhi() == t_d:
                                    for ch in range(0, 24, 2):
                                        l_h = Solar.fromYmdHms(cy, cm, cd, ch, 0, 0).getLunar()
                                        if l_h.getTimeInGanZhi() == t_t:
                                            found_list.append(l_h.getSolar().toFullString())
                            except: continue
            
            if found_list:
                st.success(f"✅ 檢索完成！在公元 {search_s_y} 至 {search_e_y} 年間，找到 {len(found_list)} 個匹配點：")
                for f in found_list: st.write(f)
            else:
                st.error("❌ 未找到符合條件的時間點。")
# ================= 6. 奇門全要素格局考據 (0-3000年跨度) =================

st.header("🔎 奇門全量要素搜索 (含地盤干、暗干)")
st.write("設定宮位要素組合與屏蔽條件，在歷史長河中精確定位格局。")

with st.expander("點擊展開：多要素篩選與屏蔽設定", expanded=False):
    c_s1, c_s2 = st.columns(2)
    s_date = c_s1.date_input("檢索起點", datetime.date(2026, 3, 15), key="qs_start")
    e_date = c_s2.date_input("檢索終點", datetime.date(2026, 4, 6), key="qs_end")
    
    # 多選要素
    sel_pals = st.multiselect("限定宮位(不選則全盤檢索)", PALACE_NAMES)
    sel_gods = st.multiselect("神盤篩選", GODS_YANG + ["白虎", "玄武"])
    sel_stars = st.multiselect("天星篩選", list(STAR_ORIGIN.values()))
    sel_doors = st.multiselect("人門篩選", [d for d in DOOR_ORDER if d != "-"])
    
    col_g1, col_g2, col_g3 = st.columns(3)
    sel_skys = col_g1.multiselect("天盤干篩選", GAN)
    sel_earths = col_g2.multiselect("地盤干篩選", GAN)
    sel_hiddens = col_g3.multiselect("暗干篩選", GAN)
    
    st.markdown("#### 🚫 屏蔽攔截設定 (剔除以下缺陷格局)")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    f_mu_on = col_f1.checkbox("攔截：入墓", value=False)
    f_po_on = col_f2.checkbox("攔截：門迫", value=False)
    f_jx_on = col_f3.checkbox("攔截：擊刑", value=False)
    f_xk_on = col_f4.checkbox("攔截：空亡", value=True)

    if st.button("🔥 啟動全要素大數據搜索"):
        search_results = []
        # 宫位PID转换
        target_pids = [PALACE_NAMES.index(p)+1 for p in sel_pals] if sel_pals else [1,2,3,4,6,7,8,9]
        
        curr_d = s_date
        total_days = (e_date - s_date).days + 1
        st.write(f"正在分析 {total_days} 天內的所有時辰...")
        
        while curr_d <= e_date:
            for ch in range(0, 24, 2):
                # 執行計算引擎
                qs = calculate_engine(curr_d.year, curr_d.month, curr_d.day, ch, method=method_in)
                
                for pid in target_pids:
                    # 1. 要素匹配 (交集邏輯)
                    if sel_gods and qs['god'].get(pid) not in sel_gods: continue
                    if sel_stars and qs['sky_star'].get(pid) not in sel_stars: continue
                    if sel_doors and qs['human'].get(pid) not in sel_doors: continue
                    if sel_skys and qs['sky_s'].get(pid) not in sel_skys: continue
                    if sel_earths and qs['earth'].get(pid) not in sel_earths: continue
                    if sel_hiddens and qs['hidden'].get(pid) not in sel_hiddens: continue
                    
                    # 2. 屏蔽邏輯精確攔截
                    fail = False
                    # 入墓檢查
                    if f_mu_on:
                        sky_gan = qs['sky_s'].get(pid)
                        if sky_gan in MU_RULES and pid in MU_RULES[sky_gan]: fail = True
                    # 門迫檢查
                    if not fail and f_po_on:
                        door_n = qs['human'].get(pid)
                        if door_n in PO_RULES and pid in PO_RULES[door_n]: fail = True
                    # 擊刑檢查
                    if not fail and f_jx_on:
                        earth_gan = qs['earth'].get(pid)
                        if earth_gan in JIXING_RULES and pid in JIXING_RULES[earth_gan]: fail = True
                    # 空亡檢查 (時空為主)
                    if not fail and f_xk_on:
                        for branch in list(qs['lunar'].getTimeXunKong()):
                            if BRANCH_TO_PID.get(branch) == pid:
                                fail = True; break
                    
                    # 成功過濾
                    if not fail:
                        search_results.append(f"🎯 {qs['solar'].toFullString()} | {PALACE_NAMES[pid-1]}")
            
            curr_d += datetime.timedelta(days=1)
            
        if search_results:
            st.success(f"✅ 考據成功！共找到 {len(search_results)} 個符合條件的格局：")
            # 限制顯示數量，防止頁面卡死，可自行調整
            max_show = 500
            for item in search_results[:max_show]:
                st.text(item)
            if len(search_results) > max_show:
                st.warning(f"注意：搜索結果過多，僅顯示前 {max_show} 條。")
        else:
            st.error("❌ 在該時間區間內未發現符合條件的格局。")

# ================= 7. 系統結語 =================
st.markdown("---")
col_footer1, col_footer2 = st.columns([2, 1])
with col_footer1:
    st.caption("奇門遁甲考據系統 · 旗艦完滿版 | 歷史增強與要素全量版")
    st.caption("本系統基於 lunar-python 核心算法，支持公元 0 年至 3000 年時間跨度。")
with col_footer2:
    st.caption("©️ 2026 老師專屬版 · 傳承與科技結合")

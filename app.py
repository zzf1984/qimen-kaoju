import streamlit as st
from lunar_python import Solar, Lunar
import datetime

# ================= 1. 核心常量与规则 =================
st.set_page_config(page_title="奇门·旗舰完满版", layout="wide")

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

# ================= 2. 核心排盘引擎 =================
def calculate_engine(y, m, d, h, mi=0, cal_mode="公曆", manual=None):
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

# ================= 3. 界面展示 =================
st.title("奇门遁甲·旗舰完满版")

# --- 側邊欄：設置 ---
with st.sidebar:
    st.header("⚙️ 參數設置")
    cal_mode = st.radio("歷法", ["公曆", "農曆"])
    date_val = st.date_input("日期", datetime.date.today())
    hour_val = st.number_input("小時(0-23)", 0, 23, 0)
    
    st.divider()
    manual_on = st.checkbox("手動定局")
    m_dun = st.selectbox("遁", ["陽", "陰"])
    m_ju = st.number_input("局數", 1, 9, 1)

# --- 主界面：排盤 ---
res = calculate_engine(date_val.year, date_val.month, date_val.day, hour_val, 0, cal_mode, manual={'active':manual_on, 'is_yang':m_dun=="陽", 'ju_num':m_ju})

st.subheader(f"🗓️ {res['gz'][0]} {res['gz'][1]} {res['gz'][2]} {res['gz'][3]}")
st.info(f"✨ {res['jq']} | {res['ju']} | 旬首:{res['shou']} | 值符:{res['zf']} | 值使:{res['zs']} | 空亡:日{res['lunar'].getDayXunKong()} 時{res['lunar'].getTimeXunKong()}")

def draw_palace(pid):
    if pid == 5:
        return f"<div style='text-align:center; padding:20px;'><h1 style='color:black;'>{res['earth'][5]}</h1></div>"
    
    idx = pid - 1
    html = f"""
    <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background-color: white;">
        <div style="font-size: 10px; color: gray; text-align: right;">{PALACE_NAMES[idx][:2]}</div>
        <div style="color: red; font-weight: bold; text-align: center;">{res['god'].get(pid, "")}</div>
        <div style="display: flex; justify-content: space-around; align-items: center;">
            <span style="font-size: 12px;">{res['sky_star'].get(pid, "")[-1]}</span>
            <span style="font-size: 24px; color: blue; font-weight: bold;">{res['sky_s'].get(pid, "")}</span>
        </div>
        <div style="display: flex; justify-content: space-around; font-size: 14px;">
            <span style="color: green;">{res['human'].get(pid, "")[:1]}</span>
            <span style="color: orange;">({res['hidden'].get(pid, "")})</span>
        </div>
        <div style="text-align: right; font-weight: bold;">{res['earth'].get(pid, "")}</div>
    </div>
    """
    return html

# 3x3 九宮格佈局
rows = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
for r in rows:
    cols = st.columns(3)
    for i, pid in enumerate(r):
        cols[i].markdown(draw_palace(pid), unsafe_allow_html=True)

st.divider()

# --- 搜索功能 ---
st.header("🔎 奇门全量搜索")
c1, c2, c3 = st.columns(3)
s_start = c1.date_input("開始日期", datetime.date(2026, 3, 15))
s_end = c2.date_input("結束日期", datetime.date(2026, 4, 6))
if st.button("開始考據"):
    st.write("正在檢索...")
    curr = s_start
    found = 0
    while curr <= s_end:
        for ch in range(0, 24, 2):
            # 默認搜索坎一宮
            qs = calculate_engine(curr.year, curr.month, curr.day, ch)
            # 這裡可以根據需要添加更複雜的篩選邏輯
            st.text(f"🎯 {qs['solar'].toFullString()} | 坎一宮")
            found += 1
        curr += datetime.timedelta(days=1)
    st.success(f"檢索完成，找到 {found} 個時辰。")

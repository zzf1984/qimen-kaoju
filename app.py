import sys
import os
# 告诉手机，如果找不到库，就来当前文件夹下找
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import flet as ft
from lunar_python import Solar, Lunar
import datetime

# ================= 1. 核心常量与规则 =================
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

# ================= 2. 核心排盘引擎 (修正时间计算 Bug) =================
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
        
        # 修正：通过 Python 标准 datetime 计算精确的时间差
        dt_now = datetime.datetime(solar.getYear(), solar.getMonth(), solar.getDay(), solar.getHour(), solar.getMinute(), solar.getSecond())
        jq_solar = prev_jq.getSolar()
        dt_jq = datetime.datetime(jq_solar.getYear(), jq_solar.getMonth(), jq_solar.getDay(), jq_solar.getHour(), jq_solar.getMinute(), jq_solar.getSecond())
        
        diff_days = (dt_now - dt_jq).total_seconds() / 86400.0
        
        # 判定上中下元 (每5天为一个周期)
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
    
    hour_gan = gz_t[0]
    target_gan = hx_yi if hour_gan == "甲" else hour_gan
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
    
    h_idx = QI_YI.index(target_gan)
    hidden = {fly_path[(fly_path.index(door_tar_idx) + i) % 9]: QI_YI[(h_idx + i) % 9] for i in range(9)}
    
    return {"lunar":lunar, "gz":[lunar.getYearInGanZhi(), lunar.getMonthInGanZhi(), gz_d, gz_t], "jq":jq_n, "ju":f"{'陽' if is_yang else '陰'}遁{ju_num}局", "earth":earth, "sky_s":sky_s, "sky_star":sky_star, "god":god_pan, "human":human_pan, "hidden":hidden, "shou":hx, "zf":STAR_ORIGIN[x_ref], "zs":DOOR_ORIGIN[x_ref], "solar":solar}

# ================= 3. 界面构建 =================
def main(page: ft.Page):
    page.title = "奇门·旗舰完满版(排盘逻辑修正)"
    page.theme_mode = ft.ThemeMode.LIGHT 
    page.bgcolor = "white"
    page.scroll = "always"

    def mk_dd(options, width, val):
        return ft.Dropdown(value=val, width=width, height=52, color="black", bgcolor="#F2F2F2", border_color="blue", content_padding=ft.padding.only(left=10, top=10, bottom=10), text_style=ft.TextStyle(color="black", size=15, weight="bold"), options=[ft.dropdown.Option(key=x, text=x) for x in options])

    # 1. 排盤面板
    cal_sel = ft.RadioGroup(content=ft.Row([ft.Radio(value="公曆", label="公曆"), ft.Radio(value="農曆", label="農曆")]), value="公曆")
    y_i, m_i, d_i, h_i = ft.TextField(label="年", value="2026", width=80), ft.TextField(label="月", value="3", width=60), ft.TextField(label="日", value="16", width=60), ft.TextField(label="時", value="0", width=60)
    meth_dd = mk_dd(["拆補法", "茅山法"], 140, "拆補法")
    m_cb = ft.Checkbox(label="手动", value=False); m_dun = mk_dd(["陽", "陰"], 90, "陽"); m_ju = mk_dd([str(i) for i in range(1,10)], 90, "1")
    st_gz = ft.Text("🗓️ 請排盤", size=20, weight="bold", color="black"); st_ak = ft.Text("", size=13, color="blue")
    palaces = [ft.Container(width=125, height=145, bgcolor="white", border=ft.border.all(1, "#DDDDDD"), border_radius=8, padding=5) for _ in range(9)]

    def run_calc(e):
        try:
            d = calculate_engine(int(y_i.value), int(m_i.value), int(d_i.value), int(h_i.value), 0, cal_sel.value, meth_dd.value, {'active':m_cb.value, 'is_yang':m_dun.value=="陽", 'ju_num':int(m_ju.value)})
            st_gz.value = f"🗓️ {d['gz'][0]} {d['gz'][1]} {d['gz'][2]} {d['gz'][3]}"
            st_ak.value = f"{d['jq']} {d['ju']} | 旬首:{d['shou']} | 值符:{d['zf']} | 值使:{d['zs']} | 空亡:日{d['lunar'].getDayXunKong()} 時{d['lunar'].getTimeXunKong()}"
            for i in range(1, 10):
                p_idx = i-1
                if i == 5: palaces[p_idx].content = ft.Column([ft.Row([ft.Text(d['earth'][5], size=26, weight="bold", color="black")], alignment="center")], alignment="center")
                else:
                    palaces[p_idx].content = ft.Column([ft.Row([ft.Text(PALACE_NAMES[p_idx][:2], size=8, color="grey")], alignment="end"), ft.Row([ft.Text(d['god'].get(i,""), color="red", weight="bold", size=15)], alignment="center"), ft.Row([ft.Text(d['sky_star'].get(i,"")[-1], size=11), ft.Text(d['sky_s'].get(i,""), size=19, color="blue", weight="bold")], alignment="center"), ft.Row([ft.Text(d['human'].get(i,"")[:1], color="green", size=14), ft.Text(f"({d['hidden'].get(i,'')})", size=11, color="orange")], alignment="center"), ft.Row([ft.Text(d['earth'].get(i,""), size=14, weight="bold", color="black")], alignment="end")], spacing=0)
            page.update()
        except Exception as ex: st_gz.value=f"錯誤:{ex}"; page.update()

    grid = ft.Column([ft.Row([palaces[3], palaces[8], palaces[1]], alignment="center", spacing=5), ft.Row([palaces[2], palaces[4], palaces[6]], alignment="center", spacing=5), ft.Row([palaces[7], palaces[0], palaces[5]], alignment="center", spacing=5)], spacing=5)

    # 2. 八字反推
    def mk_pillar(label): return ft.Row([ft.Text(label, weight="bold", width=40), mk_dd(GAN, 90, "甲"), mk_dd(ZHI, 90, "子")], spacing=5)
    b_y, b_m, b_d, b_t = mk_pillar("年:"), mk_pillar("月:"), mk_pillar("日:"), mk_pillar("时:")
    b_sy, b_ey = ft.TextField(label="起年", value="1900", width=100), ft.TextField(label="终年", value="2030", width=100); b_res = ft.Column()

    def run_bazi(e):
        b_res.controls.clear(); b_res.controls.append(ft.Text("正在檢索...")); page.update()
        target = [b_y.controls[1].value+b_y.controls[2].value, b_m.controls[1].value+b_m.controls[2].value, b_d.controls[1].value+b_d.controls[2].value, b_t.controls[1].value+b_t.controls[2].value]
        for cy in range(int(b_sy.value), int(b_ey.value)+1):
            try:
                l = Solar.fromYmd(cy, 6, 1).getLunar()
                if l.getYearInGanZhi() == target[0]:
                    for cm in range(1, 13):
                        for cd in range(1, 32):
                            l2 = Solar.fromYmd(cy, cm, cd).getLunar()
                            if l2.getMonthInGanZhi() == target[1] and l2.getDayInGanZhi() == target[2]:
                                for ch in range(0, 24, 2):
                                    lt = Solar.fromYmdHms(cy, cm, cd, ch, 0, 0).getLunar()
                                    if lt.getTimeInGanZhi() == target[3]: b_res.controls.append(ft.Text(f"✅ {lt.getSolar().toFullString()}"))
            except: continue
        page.update()

    # 3. 格局搜索
    s_sy, s_sm, s_sd = ft.TextField(label="起年", value="2026", width=80), ft.TextField(label="月", value="3", width=60), ft.TextField(label="日", value="15", width=60)
    s_ey, s_em, s_ed = ft.TextField(label="止年", value="2026", width=80), ft.TextField(label="月", value="4", width=60), ft.TextField(label="日", value="6", width=60)
    def mk_cbs(lb): return [ft.Checkbox(label=x, value=False) for x in lb]
    c_p, c_g, c_s, c_d, c_t, c_e, c_h = mk_cbs(PALACE_NAMES), mk_cbs(GODS_YANG+["白虎","玄武"]), mk_cbs(list(STAR_ORIGIN.values())), mk_cbs([d for d in DOOR_ORDER if d!="-"]), mk_cbs(GAN), mk_cbs(GAN), mk_cbs(GAN)
    
    f_mu, f_po, f_jx = ft.Checkbox(label="墓"), ft.Checkbox(label="迫"), ft.Checkbox(label="刑")
    f_yk, f_mk, f_dk, f_tk = ft.Checkbox(label="年空"), ft.Checkbox(label="月空"), ft.Checkbox(label="日空"), ft.Checkbox(label="时空")
    s_res = ft.ListView(expand=True, height=300)

    def do_search(e):
        s_res.controls.clear(); s_res.controls.append(ft.Text("檢索中...")); page.update()
        st_date = datetime.date(int(s_sy.value), int(s_sm.value), int(s_sd.value))
        en_date = datetime.date(int(s_ey.value), int(s_em.value), int(s_ed.value))
        sel_p = [i+1 for i, c in enumerate(c_p) if c.value] or [1,2,3,4,6,7,8,9]
        sl_g, sl_s, sl_d, sl_t, sl_e, sl_h = [c.label for c in c_g if c.value], [c.label for c in c_s if c.value], [c.label for c in c_d if c.value], [c.label for c in c_t if c.value], [c.label for c in c_e if c.value], [c.label for c in c_h if c.value]
        
        curr, count = st_date, 0
        while curr <= en_date:
            for ch in range(0, 24, 2):
                qs = calculate_engine(curr.year, curr.month, curr.day, ch, method=meth_dd.value)
                for pid in sel_p:
                    match = True
                    if sl_g and qs['god'].get(pid) not in sl_g: match = False
                    if match and sl_s and qs['sky_star'].get(pid) not in sl_s: match = False
                    if match and sl_d and qs['human'].get(pid) not in sl_d: match = False
                    if match and sl_t and qs['sky_s'].get(pid) not in sl_t: match = False
                    if match and sl_e and qs['earth'].get(pid) not in sl_e: match = False
                    if match and sl_h and qs['hidden'].get(pid) not in sl_h: match = False
                    if not match: continue

                    fail = False
                    if f_mu.value and qs['sky_s'].get(pid) in MU_RULES and pid in MU_RULES[qs['sky_s'].get(pid)]: fail = True
                    if not fail and f_po.value and qs['human'].get(pid) in PO_RULES and pid in PO_RULES[qs['human'].get(pid)]: fail = True
                    if not fail and f_jx.value and qs['earth'].get(pid) in JIXING_RULES and pid in JIXING_RULES[qs['earth'].get(pid)]: fail = True
                    if not fail:
                        xk_list = []
                        if f_yk.value: xk_list.extend(list(qs['lunar'].getYearXunKong()))
                        if f_mk.value: xk_list.extend(list(qs['lunar'].getMonthXunKong()))
                        if f_dk.value: xk_list.extend(list(qs['lunar'].getDayXunKong()))
                        if f_tk.value: xk_list.extend(list(qs['lunar'].getTimeXunKong()))
                        for branch in xk_list:
                            if BRANCH_TO_PID.get(branch) == pid: fail = True; break
                    
                    if not fail:
                        s_res.controls.append(ft.Text(f"🎯 {qs['solar'].toFullString()} | {PALACE_NAMES[pid-1]}")); count += 1
            curr += datetime.timedelta(days=1)
        s_res.controls[0].value = f"找到 {count} 個符合。"; page.update()

    page.add(
        ft.Row([ft.Text("歷法:"), cal_sel, y_i, m_i, d_i, h_i, meth_dd], alignment="center"),
        ft.Row([m_cb, m_dun, m_ju, ft.ElevatedButton("执行考据排盘", on_click=run_calc, bgcolor="blue", color="white")], alignment="center"),
        st_gz, st_ak, grid,
        ft.Divider(height=40), ft.Text("🔍 八字干支反推日期", size=22, weight="bold"),
        ft.Column([b_y, b_m, b_d, b_t], horizontal_alignment="center"),
        ft.Row([b_sy, b_ey, ft.ElevatedButton("開始搜索", on_click=run_bazi)], alignment="center"),
        b_res,
        ft.Divider(height=40), ft.Text("🔎 奇门全量搜索", size=22, weight="bold"),
        ft.Row([s_sy, s_sm, s_sd, ft.Text("-"), s_ey, s_em, s_ed, ft.ElevatedButton("開始考據", on_click=do_search, bgcolor="green", color="white")], alignment="center"),
        ft.ExpansionTile(title=ft.Text("🎯 多選要素设置"), controls=[ft.Text("宮位:"),ft.Row(c_p,wrap=True),ft.Text("神盤:"),ft.Row(c_g,wrap=True),ft.Text("天星:"),ft.Row(c_s,wrap=True),ft.Text("人門:"),ft.Row(c_d,wrap=True),ft.Text("天干:"),ft.Row(c_t,wrap=True),ft.Text("地干:"),ft.Row(c_e,wrap=True),ft.Text("暗干:"),ft.Row(c_h,wrap=True)]),
        ft.Row([ft.Text("屏蔽:"), f_mu, f_po, f_jx, ft.Text("|"), f_yk, f_mk, f_dk, f_tk], wrap=True, alignment="center"),
        s_res, ft.Container(height=100)
    )

ft.app(target=main)

"""Taiwan stock universe momentum — TWSE + TPEx all-stock daily closes.

Fetches every common stock on TWSE and TPEx (combined ~2,300 tickers),
resolves 7 reference dates (latest, w1, m1, m3, m6, ytd, y1), computes
percentage returns for each window, and emits sector-level medians.

This is a Wave-1 detector for the AI inference supply chain: show what
has ALREADY moved across ALL Taiwanese equities, grouped by sector, so
the investor can spot "Semis ripped +30% but Electronic Components is
flat" and then go research the lagging feeder sector for Wave-2 targets.

Schema of data/tw_movers.json:
{
  "as_of": "2026-06-01",
  "dates": {
    "latest": "2026-05-29", "w1": "...", "m1": "...",
    "m3": "...", "m6": "...", "ytd": "...", "y1": "..."
  },
  "count": 1700,
  "stocks": [
    {
      "code": "2330", "name": "台積電", "exchange": "TWSE",
      "industry": "晶圓代工", "industry_en": "Foundry",
      "close": 2355.0, "pe": 31.66, "mktcap": 6.108e13,
      "ret_1w": 3.2, "ret_1m": 8.1, "ret_3m": 22.4,
      "ret_6m": 41.0, "ret_ytd": 35.2, "ret_1y": 60.5,
      "tracked": true
    }
  ],
  "sectors": [
    {
      "industry": "半導體", "industry_en": "Semiconductors", "n": 120,
      "median_1w": .., "median_1m": .., "median_3m": ..,
      "median_6m": .., "median_ytd": .., "median_1y": ..
    }
  ]
}

`industry`/`industry_en` are normally the official TWSE/TPEx 2-digit sector,
but for ~150 curated AI-supply-chain names they are overridden with a finer
sub-industry (Foundry / Memory / OSAT / IC Substrate / PCB / CCL / Passive
Components / Cooling / Optical Comms / ...) via SUBINDUSTRY below, so the
wave-map can separate e.g. "Memory ripped but PCB is flat". `mktcap` is NT$
issued-shares x latest close (issued shares from the company-info open data).

Graceful degradation: any HTTP or parse failure preserves the existing
tw_movers.json. The refresh stage records an error in meta.json.sources.tw_universe.
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import date, timedelta
from pathlib import Path
from statistics import median
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

LOG = logging.getLogger(__name__)

TIMEOUT = 30
SLEEP_S = 1.5          # politeness between distinct fetches
CODE_RE = re.compile(r"^[1-9][0-9]{3}$")   # common-stock 4-digit codes

# Industry code -> (zh, en). Unknown codes fall back to ("其他", "Other").
INDUSTRY_MAP: dict[str, tuple[str, str]] = {
    "01": ("水泥", "Cement"),
    "02": ("食品", "Food"),
    "03": ("塑膠", "Plastics"),
    "04": ("紡織纖維", "Textiles"),
    "05": ("電機機械", "Electric Machinery"),
    "06": ("電器電纜", "Electric Appliance & Cable"),
    "08": ("玻璃陶瓷", "Glass & Ceramics"),
    "09": ("造紙", "Paper"),
    "10": ("鋼鐵", "Iron & Steel"),
    "11": ("橡膠", "Rubber"),
    "12": ("汽車", "Automobile"),
    "14": ("建材營造", "Building & Construction"),
    "15": ("航運", "Shipping & Transportation"),
    "16": ("觀光餐旅", "Tourism & Hospitality"),
    "17": ("金融保險", "Finance & Insurance"),
    "18": ("貿易百貨", "Trading & Consumer Goods"),
    "19": ("綜合", "Conglomerate"),
    "20": ("其他", "Other"),
    "21": ("化學工業", "Chemical"),
    "22": ("生技醫療", "Biotech & Medical"),
    "23": ("油電燃氣", "Oil Gas & Electricity"),
    "24": ("半導體", "Semiconductors"),
    "25": ("電腦及週邊設備", "Computer & Peripheral"),
    "26": ("光電", "Optoelectronics"),
    "27": ("通信網路", "Communications & Networking"),
    "28": ("電子零組件", "Electronic Components"),
    "29": ("電子通路", "Electronic Distribution"),
    "30": ("資訊服務", "Information Service"),
    "31": ("其他電子", "Other Electronics"),
    "32": ("文化創意", "Cultural & Creative"),
    "33": ("農業科技", "AgriTech"),
    "34": ("電子商務", "E-commerce"),
    "35": ("綠能環保", "Green Energy & Environmental"),
    "36": ("數位雲端", "Digital Cloud"),
    "37": ("運動休閒", "Sports & Leisure"),
    "38": ("居家生活", "Home & Living"),
    "80": ("管理股票", "Managed Stock"),
}


# Curated sub-industry overrides keyed by bare stock code -> (zh, en).
# The official TWSE/TPEx scheme lumps the whole electronics chain into a handful
# of coarse buckets ("Semiconductors", "Electronic Components", ...). For the AI
# inference supply chain we want finer resolution so the wave-map can show which
# *specific* feeder sector has / hasn't re-rated. Codes here override the coarse
# bucket; every other stock keeps its official sector. All codes validated
# against the live universe (names in trailing comments). Maintain by hand.
SUBINDUSTRY: dict[str, tuple[str, str]] = {
    # --- Foundry 晶圓代工 ---
    "2330": ("晶圓代工", "Foundry"),      # 台積電
    "2303": ("晶圓代工", "Foundry"),      # 聯電
    "6770": ("晶圓代工", "Foundry"),      # 力積電
    "5347": ("晶圓代工", "Foundry"),      # 世界先進
    # --- IC Design 晶片設計 ---
    "2454": ("IC設計", "IC Design"),      # 聯發科
    "3034": ("IC設計", "IC Design"),      # 聯詠
    "2379": ("IC設計", "IC Design"),      # 瑞昱
    "5269": ("IC設計", "IC Design"),      # 祥碩
    "8016": ("IC設計", "IC Design"),      # 矽創
    "6202": ("IC設計", "IC Design"),      # 盛群
    "5274": ("IC設計", "IC Design"),      # 信驊 (BMC — AI server mgmt)
    "3227": ("IC設計", "IC Design"),      # 原相
    "2458": ("IC設計", "IC Design"),      # 義隆
    "2401": ("IC設計", "IC Design"),      # 凌陽
    "3014": ("IC設計", "IC Design"),      # 聯陽
    "4961": ("IC設計", "IC Design"),      # 天鈺
    "6138": ("IC設計", "IC Design"),      # 茂達
    "8081": ("IC設計", "IC Design"),      # 致新
    "6415": ("IC設計", "IC Design"),      # 矽力*-KY
    "6679": ("IC設計", "IC Design"),      # 鈺太
    "6104": ("IC設計", "IC Design"),      # 創惟
    "2436": ("IC設計", "IC Design"),      # 偉詮電
    "5471": ("IC設計", "IC Design"),      # 松翰
    "4952": ("IC設計", "IC Design"),      # 凌通
    "6129": ("IC設計", "IC Design"),      # 普誠
    "8054": ("IC設計", "IC Design"),      # 安國
    "8040": ("IC設計", "IC Design"),      # 九暘
    "3588": ("IC設計", "IC Design"),      # 通嘉
    "6716": ("IC設計", "IC Design"),      # 應廣
    # --- ASIC & Silicon IP 設計服務/矽智財 ---
    "3661": ("設計服務/IP", "ASIC & IP"),  # 世芯-KY
    "3443": ("設計服務/IP", "ASIC & IP"),  # 創意
    "3035": ("設計服務/IP", "ASIC & IP"),  # 智原
    "6533": ("設計服務/IP", "ASIC & IP"),  # 晶心科
    "3529": ("設計服務/IP", "ASIC & IP"),  # 力旺
    "6643": ("設計服務/IP", "ASIC & IP"),  # M31
    # --- Memory 記憶體 ---
    "2337": ("記憶體", "Memory"),         # 旺宏
    "2344": ("記憶體", "Memory"),         # 華邦電
    "2408": ("記憶體", "Memory"),         # 南亞科
    "5351": ("記憶體", "Memory"),         # 鈺創
    "8299": ("記憶體", "Memory"),         # 群聯
    "2451": ("記憶體", "Memory"),         # 創見
    "3260": ("記憶體", "Memory"),         # 威剛
    "4967": ("記憶體", "Memory"),         # 十銓
    "8271": ("記憶體", "Memory"),         # 宇瞻
    "3006": ("記憶體", "Memory"),         # 晶豪科
    "6531": ("記憶體", "Memory"),         # 愛普
    # --- OSAT 封裝測試 ---
    "3711": ("封測", "OSAT"),             # 日月光投控
    "2449": ("封測", "OSAT"),             # 京元電子
    "6239": ("封測", "OSAT"),             # 力成
    "6147": ("封測", "OSAT"),             # 頎邦
    "8150": ("封測", "OSAT"),             # 南茂
    "6271": ("封測", "OSAT"),             # 同欣電
    "2441": ("封測", "OSAT"),             # 超豐
    "8110": ("封測", "OSAT"),             # 華東
    "6451": ("封測", "OSAT"),             # 訊芯-KY
    "8131": ("封測", "OSAT"),             # 福懋科
    "3264": ("封測", "OSAT"),             # 欣銓
    "2369": ("封測", "OSAT"),             # 菱生
    "6257": ("封測", "OSAT"),             # 矽格
    # --- Silicon Wafer 矽晶圓 ---
    "6488": ("矽晶圓", "Silicon Wafer"),   # 環球晶
    "5483": ("矽晶圓", "Silicon Wafer"),   # 中美晶
    "6182": ("矽晶圓", "Silicon Wafer"),   # 合晶
    "3016": ("矽晶圓", "Silicon Wafer"),   # 嘉晶
    "3532": ("矽晶圓", "Silicon Wafer"),   # 台勝科
    "8028": ("矽晶圓", "Silicon Wafer"),   # 昇陽半導體
    # --- Semiconductor Equipment 半導體設備 ---
    "3131": ("半導體設備", "Semi Equipment"),  # 弘塑
    "3583": ("半導體設備", "Semi Equipment"),  # 辛耘
    "6187": ("半導體設備", "Semi Equipment"),  # 萬潤
    "3680": ("半導體設備", "Semi Equipment"),  # 家登
    "6196": ("半導體設備", "Semi Equipment"),  # 帆宣
    "3413": ("半導體設備", "Semi Equipment"),  # 京鼎
    "2467": ("半導體設備", "Semi Equipment"),  # 志聖
    "5443": ("半導體設備", "Semi Equipment"),  # 均豪
    "8091": ("半導體設備", "Semi Equipment"),  # 翔名
    "1560": ("半導體設備", "Semi Equipment"),  # 中砂
    "2464": ("半導體設備", "Semi Equipment"),  # 盟立
    "3030": ("半導體設備", "Semi Equipment"),  # 德律 (test)
    "2360": ("半導體設備", "Semi Equipment"),  # 致茂 (test)
    "3455": ("半導體設備", "Semi Equipment"),  # 由田
    "3563": ("半導體設備", "Semi Equipment"),  # 牧德
    "2404": ("廠務工程", "Fab Engineering"),  # 漢唐 (cleanroom/facility)
    "6139": ("廠務工程", "Fab Engineering"),  # 亞翔 (cleanroom/facility)
    "6667": ("半導體設備", "Semi Equipment"),  # 信紘科
    "5215": ("半導體設備", "Semi Equipment"),  # 科嘉-KY
    "6640": ("半導體設備", "Semi Equipment"),  # 均華
    "6438": ("半導體設備", "Semi Equipment"),  # 迅得
    # --- Semiconductor Materials 半導體材料 ---
    "5234": ("半導體材料", "Semi Materials"),  # 達興材料
    "1785": ("半導體材料", "Semi Materials"),  # 光洋科
    "4755": ("半導體材料", "Semi Materials"),  # 三福化
    "4722": ("半導體材料", "Semi Materials"),  # 國精化
    "1717": ("半導體材料", "Semi Materials"),  # 長興
    "1711": ("半導體材料", "Semi Materials"),  # 永光
    "3354": ("半導體材料", "Semi Materials"),  # 律勝
    "5434": ("半導體材料", "Semi Materials"),  # 崇越 (channel)
    # --- IC Substrate 半導體載板 ---
    "3037": ("IC載板", "IC Substrate"),    # 欣興
    "8046": ("IC載板", "IC Substrate"),    # 南電
    "3189": ("IC載板", "IC Substrate"),    # 景碩
    # --- PCB 印刷電路板 ---
    "4958": ("印刷電路板", "PCB"),         # 臻鼎-KY
    "3044": ("印刷電路板", "PCB"),         # 健鼎
    "2313": ("印刷電路板", "PCB"),         # 華通
    "2368": ("印刷電路板", "PCB"),         # 金像電
    "2367": ("印刷電路板", "PCB"),         # 燿華
    "2316": ("印刷電路板", "PCB"),         # 楠梓電
    "6269": ("印刷電路板", "PCB"),         # 台郡
    "6153": ("印刷電路板", "PCB"),         # 嘉聯益
    "5469": ("印刷電路板", "PCB"),         # 瀚宇博
    "2355": ("印刷電路板", "PCB"),         # 敬鵬
    "6108": ("印刷電路板", "PCB"),         # 競國
    "3715": ("印刷電路板", "PCB"),         # 定穎投控
    "4927": ("印刷電路板", "PCB"),         # 泰鼎-KY
    "8155": ("印刷電路板", "PCB"),         # 博智
    "5439": ("印刷電路板", "PCB"),         # 高技
    "8213": ("印刷電路板", "PCB"),         # 志超
    # --- CCL / Copper-Clad Laminate 銅箔基板 ---
    "2383": ("銅箔基板", "CCL"),           # 台光電
    "6213": ("銅箔基板", "CCL"),           # 聯茂
    "6274": ("銅箔基板", "CCL"),           # 台燿
    "6672": ("銅箔基板", "CCL"),           # 騰輝電子-KY
    "8358": ("銅箔基板", "CCL"),           # 金居
    # --- Passive Components 被動元件 ---
    "2327": ("被動元件", "Passive Components"),  # 國巨
    "2492": ("被動元件", "Passive Components"),  # 華新科
    "3026": ("被動元件", "Passive Components"),  # 禾伸堂
    "2478": ("被動元件", "Passive Components"),  # 大毅
    "6173": ("被動元件", "Passive Components"),  # 信昌電
    "8043": ("被動元件", "Passive Components"),  # 蜜望實
    "2375": ("被動元件", "Passive Components"),  # 凱美
    "3236": ("被動元件", "Passive Components"),  # 千如
    "2472": ("被動元件", "Passive Components"),  # 立隆電
    # --- Connectors 連接器 ---
    "3533": ("連接器", "Connectors"),      # 嘉澤
    "3665": ("連接器", "Connectors"),      # 貿聯-KY
    "2392": ("連接器", "Connectors"),      # 正崴
    "6205": ("連接器", "Connectors"),      # 詮欣
    "3501": ("連接器", "Connectors"),      # 維熹
    "5457": ("連接器", "Connectors"),      # 宣德
    "3003": ("連接器", "Connectors"),      # 健和興
    "6290": ("連接器", "Connectors"),      # 良維
    "3710": ("連接器", "Connectors"),      # 連展投控
    "6279": ("連接器", "Connectors"),      # 胡連
    "6190": ("連接器", "Connectors"),      # 萬泰科
    # --- Thermal & Cooling 散熱 ---
    "3017": ("散熱", "Cooling"),           # 奇鋐
    "3324": ("散熱", "Cooling"),           # 雙鴻
    "3338": ("散熱", "Cooling"),           # 泰碩
    "6230": ("散熱", "Cooling"),           # 尼得科超眾
    "3483": ("散熱", "Cooling"),           # 力致
    "2421": ("散熱", "Cooling"),           # 建準
    "6591": ("散熱", "Cooling"),           # 動力-KY
    "6124": ("散熱", "Cooling"),           # 業強
    "6275": ("散熱", "Cooling"),           # 元山
    # --- Server & ODM 伺服器代工 ---
    "2317": ("伺服器代工", "Server & ODM"),  # 鴻海
    "2382": ("伺服器代工", "Server & ODM"),  # 廣達
    "3231": ("伺服器代工", "Server & ODM"),  # 緯創
    "2356": ("伺服器代工", "Server & ODM"),  # 英業達
    "6669": ("伺服器代工", "Server & ODM"),  # 緯穎
    "2376": ("伺服器代工", "Server & ODM"),  # 技嘉
    "2377": ("伺服器代工", "Server & ODM"),  # 微星
    "3706": ("伺服器代工", "Server & ODM"),  # 神達
    "4938": ("伺服器代工", "Server & ODM"),  # 和碩
    "2324": ("伺服器代工", "Server & ODM"),  # 仁寶
    "8210": ("伺服器代工", "Server & ODM"),  # 勤誠 (chassis)
    "3693": ("伺服器代工", "Server & ODM"),  # 營邦 (chassis)
    # --- Networking 網通 ---
    "2345": ("網通", "Networking"),        # 智邦
    "3596": ("網通", "Networking"),        # 智易
    "6285": ("網通", "Networking"),        # 啟碁
    "5388": ("網通", "Networking"),        # 中磊
    "3380": ("網通", "Networking"),        # 明泰
    "2332": ("網通", "Networking"),        # 友訊
    "4906": ("網通", "Networking"),        # 正文
    "3419": ("網通", "Networking"),        # 譁裕
    "2314": ("網通", "Networking"),        # 台揚
    "2419": ("網通", "Networking"),        # 仲琦
    "2485": ("網通", "Networking"),        # 兆赫
    # --- Optical Comms 光通訊 ---
    "4979": ("光通訊", "Optical Comms"),    # 華星光
    "3450": ("光通訊", "Optical Comms"),    # 聯鈞
    "3363": ("光通訊", "Optical Comms"),    # 上詮
    "4908": ("光通訊", "Optical Comms"),    # 前鼎
    "6442": ("光通訊", "Optical Comms"),    # 光聖
    "4977": ("光通訊", "Optical Comms"),    # 眾達-KY
    "3163": ("光通訊", "Optical Comms"),    # 波若威
    "3081": ("光通訊", "Optical Comms"),    # 聯亞
    "6426": ("光通訊", "Optical Comms"),    # 統新
    "3234": ("光通訊", "Optical Comms"),    # 光環
    # --- Power Supply 電源 ---
    "2308": ("電源", "Power Supply"),      # 台達電
    "2301": ("電源", "Power Supply"),      # 光寶科
    "6282": ("電源", "Power Supply"),      # 康舒
    "3015": ("電源", "Power Supply"),      # 全漢
    "6412": ("電源", "Power Supply"),      # 群電
    "2457": ("電源", "Power Supply"),      # 飛宏
    "3078": ("電源", "Power Supply"),      # 僑威
    "6409": ("電源", "Power Supply"),      # 旭隼 (UPS/inverter)
    # === Names ≥ NT$30B added 2026-06 so every investable name has a sub-industry.
    # Classifications verified (web-checked the non-obvious ones; corrected agent
    # mis-IDs on 雍智/昇達科/亞光/AES-KY). ===
    # --- IC Design ---
    "6526": ("IC設計", "IC Design"),      # 達發 (Airoha, connectivity SoC)
    "4919": ("IC設計", "IC Design"),      # 新唐 (Nuvoton MCU)
    "4966": ("IC設計", "IC Design"),      # 譜瑞-KY (Parade, high-speed interface)
    "2388": ("IC設計", "IC Design"),      # 威盛 (VIA)
    "2363": ("IC設計", "IC Design"),      # 矽統 (SiS)
    # --- Test & Probe (semiconductor test interface + handlers) ---
    "7769": ("測試介面", "Test & Probe"),  # 鴻勁 (test handler + active thermal)
    "6223": ("測試介面", "Test & Probe"),  # 旺矽 (probe cards)
    "6515": ("測試介面", "Test & Probe"),  # 穎崴 (test sockets)
    "6510": ("測試介面", "Test & Probe"),  # 精測 (probe cards)
    "6683": ("測試介面", "Test & Probe"),  # 雍智科技 (test load boards)
    "6217": ("測試介面", "Test & Probe"),  # 中探針 (probe needles)
    # --- Compound Semi (GaAs/SiC/GaN epi & foundry, RF) ---
    "3105": ("化合物半導體", "Compound Semi"),  # 穩懋 (WIN, GaAs foundry)
    "4991": ("化合物半導體", "Compound Semi"),  # 環宇-KY (GaN/SiC epi)
    "2455": ("化合物半導體", "Compound Semi"),  # 全新 (VPEC, GaAs epi)
    "3707": ("化合物半導體", "Compound Semi"),  # 漢磊 (SiC/GaN foundry)
    "4971": ("化合物半導體", "Compound Semi"),  # IET-KY (GaAs/InP epi)
    "8086": ("化合物半導體", "Compound Semi"),  # 宏捷科 (AWSC, GaAs)
    # --- Discrete / Power Semi ---
    "2481": ("功率元件", "Discrete/Power Semi"),  # 強茂 (Panjit)
    "5425": ("功率元件", "Discrete/Power Semi"),  # 台半 (TSC)
    # --- OSAT ---
    "6789": ("封測", "OSAT"),             # 采鈺 (VisEra, CIS packaging)
    "3374": ("封測", "OSAT"),             # 精材 (Xintec, WLCSP)
    "2329": ("封測", "OSAT"),             # 華泰 (OSE)
    # --- Semiconductor Equipment ---
    "7734": ("半導體設備", "Semi Equipment"),  # 印能科技 (adv-pkg warpage/lamination)
    "7828": ("半導體設備", "Semi Equipment"),  # 創新服務 (probe-card automation)
    "7822": ("半導體設備", "Semi Equipment"),  # 倍利科 (semi AOI/metrology)
    "7751": ("半導體設備", "Semi Equipment"),  # 竑騰 (semi automation + inspection)
    "7795": ("半導體設備", "Semi Equipment"),  # 長廣 (ABF-substrate vacuum lamination)
    "6830": ("半導體設備", "Semi Equipment"),  # 汎銓 (MA-tek, failure-analysis lab)
    # --- Semiconductor Materials ---
    "4749": ("半導體材料", "Semi Materials"),  # 新應材 (photoresist/adv-pkg chemicals)
    "8070": ("半導體材料", "Semi Materials"),  # 長華* (EMC/packaging materials)
    # --- Lead Frame ---
    "6548": ("導線架", "Lead Frame"),      # 長科* (leadframe/pre-mold)
    "2486": ("導線架", "Lead Frame"),      # 一詮 (leadframe)
    "2351": ("導線架", "Lead Frame"),      # 順德 (leadframe)
    # --- PCB ---
    "8021": ("印刷電路板", "PCB"),         # 尖點 (PCB micro-drill bits)
    "6191": ("印刷電路板", "PCB"),         # 精成科 (PCB + SMT)
    # --- CCL / laminate material ---
    "1815": ("銅箔基板", "CCL"),           # 富喬 (glass-fibre yarn/fabric)
    "8039": ("銅箔基板", "CCL"),           # 台虹 (Taiflex, FCCL)
    "5475": ("銅箔基板", "CCL"),           # 德宏 (glass fabric for CCL)
    # --- Passive Components ---
    "3042": ("被動元件", "Passive Components"),  # 晶技 (TXC, quartz crystal)
    "2428": ("被動元件", "Passive Components"),  # 興勤 (thermistors)
    "6449": ("被動元件", "Passive Components"),  # 鈺邦 (polymer capacitors)
    "3357": ("被動元件", "Passive Components"),  # 臺慶科 (inductors)
    # --- Connectors ---
    "3023": ("連接器", "Connectors"),      # 信邦 (Sinbon, cable/connector)
    "6197": ("連接器", "Connectors"),      # 佳必琪 (board/wire connectors)
    # --- Thermal & Cooling ---
    "3653": ("散熱", "Cooling"),           # 健策 (heat spreaders/vapor chamber)
    "6805": ("散熱", "Cooling"),           # 富世達 (liquid-cooling quick-connects)
    "2354": ("散熱", "Cooling"),           # 鴻準 (thermal modules + casing)
    "6831": ("散熱", "Cooling"),           # 邁科 (vapor chamber / liquid cooling)
    # --- Networking (telecom/satellite RF) ---
    "3491": ("網通", "Networking"),        # 昇達科 (LEO-satellite RF components)
    # --- Telecom carriers ---
    "2412": ("電信", "Telecom"),           # 中華電
    "3045": ("電信", "Telecom"),           # 台灣大
    "4904": ("電信", "Telecom"),           # 遠傳
    # --- Display / Panel ---
    "3481": ("面板", "Display/Panel"),     # 群創
    "8069": ("面板", "Display/Panel"),     # 元太 (e-paper)
    "2409": ("面板", "Display/Panel"),     # 友達
    "6176": ("面板", "Display/Panel"),     # 瑞儀 (backlight)
    "6116": ("面板", "Display/Panel"),     # 彩晶
    "3673": ("面板", "Display/Panel"),     # TPK-KY (touch)
    "2489": ("面板", "Display/Panel"),     # 瑞軒 (TV/monitor ODM)
    # --- Optical / Lens ---
    "3008": ("光學鏡頭", "Optical/Lens"),   # 大立光
    "3406": ("光學鏡頭", "Optical/Lens"),   # 玉晶光
    "3019": ("光學鏡頭", "Optical/Lens"),   # 亞光 (Asia Optical, cameras/lenses)
    # --- LED ---
    "3714": ("LED", "LED"),               # 富采 (Epistar+Lextar)
    # --- IC / component distribution ---
    "3036": ("IC通路", "IC Distribution"),  # 文曄
    "3702": ("IC通路", "IC Distribution"),  # 大聯大
    "2347": ("IC通路", "IC Distribution"),  # 聯強
    "3090": ("IC通路", "IC Distribution"),  # 日電貿
    "8112": ("IC通路", "IC Distribution"),  # 至上
    "3010": ("IC通路", "IC Distribution"),  # 華立 (materials distribution)
    # --- Industrial PC ---
    "2395": ("工業電腦", "Industrial PC"),  # 研華 (Advantech)
    "5289": ("工業電腦", "Industrial PC"),  # 宜鼎 (Innodisk, industrial storage)
    "3005": ("工業電腦", "Industrial PC"),  # 神基 (Getac, rugged)
    "6414": ("工業電腦", "Industrial PC"),  # 樺漢 (Hartmann)
    # --- PC / Notebook ---
    "2357": ("品牌電腦", "PC/Notebook"),    # 華碩
    "2353": ("品牌電腦", "PC/Notebook"),    # 宏碁
    "2352": ("品牌電腦", "PC/Notebook"),    # 佳世達 (Qisda)
    # --- Battery Pack ---
    "6121": ("電池模組", "Battery Pack"),   # 新普 (Simplo)
    "3211": ("電池模組", "Battery Pack"),   # 順達 (Dynapack)
    "6781": ("電池模組", "Battery Pack"),   # AES-KY (server BBU batteries)
    # --- Casing & Mechanical ---
    "2059": ("機殼機構", "Casing & Mechanical"),  # 川湖 (server slide rails)
    "2474": ("機殼機構", "Casing & Mechanical"),  # 可成 (metal casing)
    "6584": ("機殼機構", "Casing & Mechanical"),  # 南俊國際 (ball guide rails)
    "3376": ("機殼機構", "Casing & Mechanical"),  # 新日興 (hinges)
    # --- EMS (broad contract manufacturing) ---
    "2385": ("電子代工", "EMS"),           # 群光 (Chicony)
    "6278": ("電子代工", "EMS"),           # 台表科 (SMT/PCBA)
    "2312": ("電子代工", "EMS"),           # 金寶 (Kinpo)
    "4915": ("電子代工", "EMS"),           # 致伸 (Primax)
    # --- Robotics ---
    "4585": ("機器人", "Robotics"),        # 達明 (Techman cobots)
    # --- Consumer Devices ---
    "2498": ("消費性電子", "Consumer Devices"),  # 宏達電 (HTC)
    # --- IT Services ---
    "6214": ("資訊服務", "IT Services"),    # 精誠 (Systex)
    # --- E-commerce ---
    "8454": ("電商", "E-commerce"),        # 富邦媒 (momo)
    # --- Fab Engineering (cleanroom/facility) ---
    "5536": ("廠務工程", "Fab Engineering"),  # 聖暉
    "6691": ("廠務工程", "Fab Engineering"),  # 洋基工程
    # === Borderline band (~NT$22-32B) — buffer so price-drift across the NT$30B
    # leaderboard floor doesn't reopen a coarse-label gap. Verified the non-obvious. ===
    "2328": ("連接器", "Connectors"),      # 廣宇 (Foxconn cable/connector/PCB)
    "6715": ("連接器", "Connectors"),      # 嘉基 (high-speed connectors / optical interconnect)
    "3526": ("連接器", "Connectors"),      # 凡甲
    "3515": ("品牌電腦", "PC/Notebook"),    # 華擎 (ASRock motherboards)
    "2362": ("品牌電腦", "PC/Notebook"),    # 藍天 (Clevo notebook ODM)
    "7711": ("工業電腦", "Industrial PC"),  # 永擎 (ASRock Industrial)
    "6166": ("工業電腦", "Industrial PC"),  # 凌華 (ADLINK)
    "6579": ("工業電腦", "Industrial PC"),  # 研揚 (AAEON)
    "3576": ("太陽能", "Solar"),           # 聯合再生 (URE solar)
    "8064": ("半導體設備", "Semi Equipment"),  # 東捷 (panel/semi packaging equipment)
    "3587": ("半導體設備", "Semi Equipment"),  # 閎康 (MA-tek analysis lab)
    "5371": ("面板", "Display/Panel"),     # 中光電 (Coretronic projector/backlight)
    "6456": ("面板", "Display/Panel"),     # GIS-KY (touch/display modules)
    "2393": ("LED", "LED"),               # 億光 (Everlight)
    "2426": ("LED", "LED"),               # 鼎元 (Tyntek LED/sensor)
    "2374": ("光學鏡頭", "Optical/Lens"),   # 佳能 (Ability imaging/optical)
    "6739": ("資訊服務", "IT Services"),    # 竹陞科技 (AIoT smart-factory integration)
    "6561": ("電信", "Telecom"),           # 是方 (Chief Telecom IDC)
    "6291": ("IC設計", "IC Design"),       # 沛亨 (Aimtron power IC)
    "6719": ("IC設計", "IC Design"),       # 力智 (UPI power IC)
    "7749": ("IC設計", "IC Design"),       # 意騰-KY (edge-AI SoC)
    "2476": ("機殼機構", "Casing & Mechanical"),  # 鉅祥 (stamping/hinges)
    "3013": ("機殼機構", "Casing & Mechanical"),  # 晟銘電 (server chassis)
    "7805": ("網通", "Networking"),        # 威聯通 (QNAP NAS)
    "2359": ("機器人", "Robotics"),        # 所羅門 (machine vision/robotics)
    "3033": ("IC通路", "IC Distribution"),  # 威健
    "2439": ("消費性電子", "Consumer Devices"),  # 美律 (Merry acoustics)
}


# ---------------------------------------------------------------------------
# Date resolution
# ---------------------------------------------------------------------------

def _gregorian_to_roc(d: date) -> str:
    """Return ROC-era date string 'YYY/MM/DD' for TPEx API."""
    roc_year = d.year - 1911
    return f"{roc_year}/{d.month:02d}/{d.day:02d}"


def _resolve_reference_dates(today: date) -> dict[str, date]:
    """Return the 7 reference date LABELS -> approximate calendar dates.

    These are walked back to actual trading days by _walk_back_to_trading_day
    before any fetch is issued.
    """
    prev_dec31 = date(today.year - 1, 12, 31)
    return {
        "latest": today,
        "w1":     today - timedelta(days=7),
        "m1":     today - timedelta(days=30),
        "m3":     today - timedelta(days=91),
        "m6":     today - timedelta(days=182),
        "ytd":    prev_dec31,
        "y1":     today - timedelta(days=365),
    }


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_json(url: str) -> Any:
    req = Request(url, headers={"User-Agent": "inference-dashboard/1.0"})
    with urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def _sleep():
    time.sleep(SLEEP_S)


# ---------------------------------------------------------------------------
# TWSE MI_INDEX fetch
# ---------------------------------------------------------------------------

def _twse_url(d: date) -> str:
    return (
        "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
        f"?date={d.strftime('%Y%m%d')}&type=ALLBUT0999&response=json"
    )


def _parse_twse_closes(payload: dict) -> dict[str, dict]:
    """Parse TWSE MI_INDEX JSON -> {code: {close, pe}} for common stocks.

    The table we want has title containing '每日收盤行情' and 16 fields.
    Row indices: [0]=code, [1]=name, [8]=close, [15]=P/E.
    """
    tables = payload.get("tables") or payload.get("data") or []
    target = None
    for tbl in tables:
        if not isinstance(tbl, dict):
            continue
        title = tbl.get("title", "")
        fields = tbl.get("fields") or []
        data = tbl.get("data") or []
        if "每日收盤行情" in title and len(fields) == 16 and data:
            target = tbl
            break
    if target is None:
        # Fallback: table with most rows and 16 fields
        for tbl in tables:
            if not isinstance(tbl, dict):
                continue
            data = tbl.get("data") or []
            fields = tbl.get("fields") or []
            if len(fields) == 16 and len(data) > (len(target.get("data") or []) if target else 0):
                target = tbl
    if target is None:
        return {}

    result: dict[str, dict] = {}
    for row in (target.get("data") or []):
        if not isinstance(row, list) or len(row) < 16:
            continue
        code = str(row[0]).strip()
        if not CODE_RE.match(code):
            continue
        name = str(row[1]).strip()
        close_raw = str(row[8]).replace(",", "").strip()
        pe_raw = str(row[15]).replace(",", "").strip()

        close: float | None = None
        pe: float | None = None
        if close_raw and close_raw not in ("--", "0.00", "0"):
            try:
                v = float(close_raw)
                if v > 0:
                    close = v
            except ValueError:
                pass
        if pe_raw and pe_raw not in ("--", ""):
            try:
                v = float(pe_raw)
                if v > 0:
                    pe = v
            except ValueError:
                pass

        if close is not None:
            result[code] = {"name": name, "close": close, "pe": pe}
    return result


def _fetch_twse_snapshot(d: date) -> dict[str, dict] | None:
    """Fetch TWSE closes for date d. Returns None on non-trading day or error."""
    url = _twse_url(d)
    LOG.debug("TWSE fetch: %s", url)
    try:
        payload = _get_json(url)
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        LOG.warning("TWSE fetch failed for %s: %s", d, e)
        return None

    stat = payload.get("stat", "")
    # On holidays/weekends the stat is a Chinese string like "查詢日期大於..." or "很抱歉"
    if stat != "OK":
        LOG.debug("TWSE: stat=%r on %s (non-trading day)", stat, d)
        return None

    return _parse_twse_closes(payload)


# ---------------------------------------------------------------------------
# TPEx fetch
# ---------------------------------------------------------------------------

def _tpex_url(d: date) -> str:
    roc = _gregorian_to_roc(d)
    return (
        "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/"
        f"stk_wn1430_result.php?l=zh-tw&d={roc}&se=EW"
    )


def _parse_tpex_closes(payload: dict) -> dict[str, dict]:
    """Parse TPEx JSON -> {code: {close}} for common stocks.

    tables[0].data rows: [0]=code, [1]=name, [2]=close (no P/E on TPEx).
    """
    tables = payload.get("tables") or []
    if not tables or not isinstance(tables[0], dict):
        return {}
    rows = tables[0].get("data") or []

    result: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, list) or len(row) < 3:
            continue
        code = str(row[0]).strip()
        if not CODE_RE.match(code):
            continue
        name = str(row[1]).strip()
        close_raw = str(row[2]).replace(",", "").strip()

        close: float | None = None
        if close_raw and close_raw not in ("--", ""):
            try:
                v = float(close_raw)
                if v > 0:
                    close = v
            except ValueError:
                pass

        if close is not None:
            result[code] = {"name": name, "close": close, "pe": None}
    return result


def _fetch_tpex_snapshot(d: date) -> dict[str, dict] | None:
    """Fetch TPEx closes for date d. Returns None on non-trading day or error."""
    url = _tpex_url(d)
    LOG.debug("TPEx fetch: %s", url)
    try:
        payload = _get_json(url)
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        LOG.warning("TPEx fetch failed for %s: %s", d, e)
        return None

    stat = payload.get("stat", "")
    if stat.lower() != "ok":
        LOG.debug("TPEx: stat=%r on %s (non-trading day)", stat, d)
        return None

    return _parse_tpex_closes(payload)


# ---------------------------------------------------------------------------
# Walk-back to nearest trading day
# ---------------------------------------------------------------------------

def _resolve_trading_day(
    target: date,
    twse_cache: dict[date, dict[str, dict]],
    tpex_cache: dict[date, dict[str, dict]],
    max_lookback: int = 12,
) -> date | None:
    """Walk backwards from target until both exchanges have posted close data.

    Returns the resolved trading date, or None if none found within lookback.
    Populates both caches for the resolved date (fetches both exchanges once).

    Requiring BOTH non-empty matters on data-lag days: TWSE can publish its EOD
    file hours before TPEx (seen on Mondays / right after close), where TPEx
    returns stat='ok' with 0 rows. Anchoring on TWSE alone there would silently
    drop the entire ~880-name TPEx universe, so we keep walking back to the most
    recent day where both exchanges have data.
    """
    for delta in range(max_lookback + 1):
        d = target - timedelta(days=delta)
        if d in twse_cache:
            return d  # already resolved (both caches populated for this date)
        _sleep()
        twse = _fetch_twse_snapshot(d)
        if not twse:
            continue
        # TWSE trading day confirmed — TPEx must also have posted for this date.
        _sleep()
        tpex = _fetch_tpex_snapshot(d)
        if not tpex:
            LOG.info("  %s: TWSE posted but TPEx not yet — walking back", d)
            continue
        twse_cache[d] = twse
        tpex_cache[d] = tpex
        return d

    LOG.warning("Could not resolve trading day for target=%s within %d days", target, max_lookback)
    return None


# ---------------------------------------------------------------------------
# Industry classification
# ---------------------------------------------------------------------------

def _to_int(s: Any) -> int | None:
    """Parse an issued-shares string ('25932370067') to int; None on failure."""
    try:
        v = int(str(s).replace(",", "").strip())
        return v if v > 0 else None
    except (ValueError, TypeError):
        return None


# Each company-info fetch returns {code: {"ind": (zh, en), "shares": int|None}}.
# `shares` x latest close gives market cap; `ind` is the coarse official sector
# (later overridden by SUBINDUSTRY for curated names).

def _fetch_company_info_twse() -> dict[str, dict]:
    """TWSE listed company info (industry + issued shares) from TWSE open-data."""
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    LOG.debug("TWSE company-info fetch: %s", url)
    try:
        _sleep()
        data = _get_json(url)
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        LOG.warning("TWSE company-info fetch failed: %s", e)
        return {}

    result: dict[str, dict] = {}
    for row in (data or []):
        code = str(row.get("公司代號", "")).strip()
        if not code:
            continue
        industry_code = str(row.get("產業別", "")).strip().zfill(2)
        zh, en = INDUSTRY_MAP.get(industry_code, ("其他", "Other"))
        result[code] = {
            "ind": (zh, en),
            "shares": _to_int(row.get("已發行普通股數或TDR原股發行股數")),
        }
    return result


def _fetch_company_info_tpex() -> dict[str, dict]:
    """TPEx (OTC) company info (industry + issued shares) from the TPEx open-data host.

    Uses the TPEx openapi host — the TWSE-host t187ap03_O is empty for OTC, which
    is why TPEx names previously fell back to "Other". `SecuritiesIndustryCode`
    follows the same 2-digit scheme as the TWSE listed table; `IssueShares` gives
    issued common shares for market cap.
    """
    url = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"
    LOG.debug("TPEx company-info fetch: %s", url)
    try:
        _sleep()
        data = _get_json(url)
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        LOG.warning("TPEx company-info fetch failed: %s", e)
        return {}

    result: dict[str, dict] = {}
    for row in (data or []):
        code = str(row.get("SecuritiesCompanyCode", "")).strip()
        if not code:
            continue
        industry_code = str(row.get("SecuritiesIndustryCode", "")).strip().zfill(2)
        zh, en = INDUSTRY_MAP.get(industry_code, ("其他", "Other"))
        result[code] = {
            "ind": (zh, en),
            "shares": _to_int(row.get("IssueShares")),
        }
    return result


# ---------------------------------------------------------------------------
# Return computation and sector medians
# ---------------------------------------------------------------------------

def _compute_returns(
    latest_snap: dict[str, dict],
    ref_snaps: dict[str, dict[str, dict]],
    window_labels: list[str],
) -> dict[str, dict[str, float | None]]:
    """For each code in latest_snap compute pct returns vs each ref window.

    Returns {code: {ret_1w: .., ret_1m: .., ...}}.
    """
    out: dict[str, dict[str, float | None]] = {}
    for code, latest_data in latest_snap.items():
        latest_close = latest_data.get("close")
        if latest_close is None:
            continue
        rets: dict[str, float | None] = {}
        for window in window_labels:
            ref_snap = ref_snaps.get(window, {})
            ref_data = ref_snap.get(code)
            if ref_data is None:
                rets[f"ret_{window}"] = None
            else:
                ref_close = ref_data.get("close")
                if ref_close is None or ref_close <= 0:
                    rets[f"ret_{window}"] = None
                else:
                    rets[f"ret_{window}"] = round((latest_close / ref_close - 1) * 100, 1)
        out[code] = rets
    return out


def _compute_sector_medians(stocks: list[dict]) -> list[dict]:
    """Group stocks by industry, compute median returns for each window."""
    windows = ["1w", "1m", "3m", "6m", "ytd", "1y"]
    by_industry: dict[str, dict[str, list[float]]] = {}

    for s in stocks:
        ind = s.get("industry") or "其他"
        ind_en = s.get("industry_en") or "Other"
        if ind not in by_industry:
            by_industry[ind] = {"industry_en": ind_en, "vals": {w: [] for w in windows}}
        for w in windows:
            v = s.get(f"ret_{w}")
            if v is not None:
                by_industry[ind]["vals"][w].append(v)

    sectors = []
    for ind, info in sorted(by_industry.items()):
        n = sum(1 for s in stocks if (s.get("industry") or "其他") == ind)
        sector: dict[str, Any] = {
            "industry": ind,
            "industry_en": info["industry_en"],
            "n": n,
        }
        for w in windows:
            vals = info["vals"][w]
            sector[f"median_{w}"] = round(median(vals), 1) if vals else None
        sectors.append(sector)

    # Sort by median_3m descending (most relevant window for wave-1 detection)
    sectors.sort(key=lambda x: (x.get("median_3m") or -9999), reverse=True)
    return sectors


# ---------------------------------------------------------------------------
# Tracked codes (dashboard players)
# ---------------------------------------------------------------------------

def _load_tracked_codes(players_path: Path) -> set[str]:
    """Return bare numeric codes for all Taiwan-listed player tickers (.TW/.TWO)."""
    if not players_path.exists():
        return set()
    try:
        players = json.loads(players_path.read_text())
    except Exception:
        return set()
    codes: set[str] = set()
    for p in players:
        ticker = str(p.get("ticker", ""))
        if ticker.endswith(".TW") or ticker.endswith(".TWO"):
            code = ticker.split(".")[0]
            codes.add(code)
    return codes


# ---------------------------------------------------------------------------
# Atomic write (standalone-run helper; refresh.py uses its own _write_json)
# ---------------------------------------------------------------------------

def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch(existing: dict | None = None) -> dict:
    """Fetch Taiwan universe closes, compute multi-window returns, emit tw_movers.json payload.

    `existing` is the prior tw_movers.json dict (may be None / empty).
    Returns the fresh payload dict — caller is responsible for writing it.

    Raises on unrecoverable failure so caller can preserve prior state.
    """
    today = date.today()
    ref_dates_approx = _resolve_reference_dates(today)

    twse_cache: dict[date, dict[str, dict]] = {}
    tpex_cache: dict[date, dict[str, dict]] = {}

    LOG.info("Resolving trading dates (walk-back up to 12 days each) ...")
    resolved_dates: dict[str, date | None] = {}
    for label, approx in ref_dates_approx.items():
        resolved = _resolve_trading_day(approx, twse_cache, tpex_cache, max_lookback=12)
        resolved_dates[label] = resolved
        if resolved:
            LOG.info("  %s -> %s", label, resolved)
        else:
            LOG.warning("  %s -> UNRESOLVED", label)

    latest_date = resolved_dates.get("latest")
    if latest_date is None:
        raise RuntimeError("tw_universe: could not resolve latest trading day — no data written")

    latest_twse = twse_cache.get(latest_date, {})
    latest_tpex = tpex_cache.get(latest_date, {})

    if not latest_twse and not latest_tpex:
        raise RuntimeError(f"tw_universe: empty close data for latest date {latest_date}")

    LOG.info("Latest date %s: TWSE=%d stocks, TPEx=%d stocks",
             latest_date, len(latest_twse), len(latest_tpex))

    # Company info: coarse industry + issued shares (for market cap), per exchange.
    LOG.info("Fetching company-info (industry + shares) ...")
    info_twse = _fetch_company_info_twse()
    info_tpex = _fetch_company_info_tpex()
    LOG.info("Company info: TWSE=%d codes, TPEx=%d codes", len(info_twse), len(info_tpex))

    # Build reference snapshots for return computation.
    # resolved_dates keys are "w1","m1","m3","m6","ytd","y1".
    # window_labels (output field suffixes) are "1w","1m","3m","6m","ytd","1y".
    # Map: resolved_dates key -> output window label.
    RESOLVED_KEY_TO_WINDOW = {
        "w1": "1w", "m1": "1m", "m3": "3m",
        "m6": "6m", "ytd": "ytd", "y1": "1y",
    }
    window_labels = ["1w", "1m", "3m", "6m", "ytd", "1y"]
    ref_snaps_twse: dict[str, dict[str, dict]] = {w: {} for w in window_labels}
    ref_snaps_tpex: dict[str, dict[str, dict]] = {w: {} for w in window_labels}
    for rk, w in RESOLVED_KEY_TO_WINDOW.items():
        rd = resolved_dates.get(rk)
        if rd:
            ref_snaps_twse[w] = twse_cache.get(rd, {})
            ref_snaps_tpex[w] = tpex_cache.get(rd, {})

    # Compute returns
    twse_returns = _compute_returns(latest_twse, ref_snaps_twse, window_labels)
    tpex_returns = _compute_returns(latest_tpex, ref_snaps_tpex, window_labels)

    # Tracked codes
    root = Path(__file__).resolve().parent.parent.parent
    players_path = root / "data" / "players.json"
    tracked_codes = _load_tracked_codes(players_path)

    def _resolve_industry(code: str, info: dict) -> tuple[str, str]:
        """Curated sub-industry if present, else the coarse official sector."""
        if code in SUBINDUSTRY:
            return SUBINDUSTRY[code]
        rec = info.get(code)
        return rec["ind"] if rec else ("其他", "Other")

    def _mktcap(code: str, close: float | None, info: dict) -> float | None:
        rec = info.get(code)
        shares = rec.get("shares") if rec else None
        if shares is None or close is None:
            return None
        return round(shares * close)

    # Assemble stocks list
    stocks: list[dict] = []

    for code, rets in twse_returns.items():
        data = latest_twse[code]
        ind_zh, ind_en = _resolve_industry(code, info_twse)
        stock: dict[str, Any] = {
            "code": code,
            "name": data["name"],
            "exchange": "TWSE",
            "industry": ind_zh,
            "industry_en": ind_en,
            "close": data["close"],
            "pe": data.get("pe"),
            "mktcap": _mktcap(code, data["close"], info_twse),
            "ret_1w": rets.get("ret_1w"),
            "ret_1m": rets.get("ret_1m"),
            "ret_3m": rets.get("ret_3m"),
            "ret_6m": rets.get("ret_6m"),
            "ret_ytd": rets.get("ret_ytd"),
            "ret_1y": rets.get("ret_1y"),
            "tracked": code in tracked_codes,
        }
        stocks.append(stock)

    for code, rets in tpex_returns.items():
        if code in twse_returns:
            continue  # TWSE takes precedence if a code appears on both (shouldn't happen)
        data = latest_tpex[code]
        ind_zh, ind_en = _resolve_industry(code, info_tpex)
        stock = {
            "code": code,
            "name": data["name"],
            "exchange": "TPEx",
            "industry": ind_zh,
            "industry_en": ind_en,
            "close": data["close"],
            "pe": None,   # TPEx API doesn't provide P/E
            "mktcap": _mktcap(code, data["close"], info_tpex),
            "ret_1w": rets.get("ret_1w"),
            "ret_1m": rets.get("ret_1m"),
            "ret_3m": rets.get("ret_3m"),
            "ret_6m": rets.get("ret_6m"),
            "ret_ytd": rets.get("ret_ytd"),
            "ret_1y": rets.get("ret_1y"),
            "tracked": code in tracked_codes,
        }
        stocks.append(stock)

    # Sort by ret_3m descending (primary wave-1 signal window), nulls last
    stocks.sort(key=lambda s: (s.get("ret_3m") is None, -(s.get("ret_3m") or 0)))

    sectors = _compute_sector_medians(stocks)

    dates_iso = {
        label: (d.isoformat() if d else None)
        for label, d in resolved_dates.items()
    }

    LOG.info("tw_universe: %d stocks assembled, %d sectors", len(stocks), len(sectors))

    return {
        "as_of": today.isoformat(),
        "dates": dates_iso,
        "count": len(stocks),
        "stocks": stocks,
        "sectors": sectors,
    }


# ---------------------------------------------------------------------------
# Standalone entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    root = Path(__file__).resolve().parent.parent.parent
    out_path = root / "data" / "tw_movers.json"
    prev = {}
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text())
        except Exception:
            pass

    try:
        result = fetch(existing=prev)
        _write_json(out_path, result)
        print(f"OK: {result['count']} stocks written to {out_path}")
        print(f"Dates: {result['dates']}")
        print(f"Sectors ({len(result['sectors'])}):")
        for s in result["sectors"][:10]:
            print(f"  {s['industry_en']:35s}  n={s['n']:4d}  "
                  f"3m={s.get('median_3m'):+.1f}%  1y={s.get('median_1y'):+.1f}%"
                  if s.get('median_3m') is not None and s.get('median_1y') is not None
                  else f"  {s['industry_en']:35s}  n={s['n']:4d}  3m=None")
        print(f"\nTop 10 by ret_3m:")
        for s in result["stocks"][:10]:
            print(f"  {s['code']} {s['name']:16s}  {s['industry_en']:35s}  "
                  f"3m={s.get('ret_3m'):+.1f}%  1y={s.get('ret_1y'):+.1f}%"
                  if s.get('ret_3m') is not None and s.get('ret_1y') is not None
                  else f"  {s['code']} {s['name']:16s}  3m=None")
    except Exception as e:
        LOG.error("tw_universe failed: %s", e)
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)

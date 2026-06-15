import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import sqlite3
import re

st.set_page_config(page_title="天堂W 盟用王表 (穩定商業版)", layout="wide")
st.title("🏰 《天堂W》王表管理系統")

DB_FILE = "boss.db"

# -------------------------------------------------------------------------
# 🛠 輔支函數：強制取得台灣時間 (台北時區 UTC+8)
# -------------------------------------------------------------------------
def get_tw_now():
    return datetime.utcnow() + timedelta(hours=8)

# -------------------------------------------------------------------------
# 1. 資料庫基礎建設
# -------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS boss_info (
            content TEXT PRIMARY KEY,
            real_name TEXT,
            location TEXT,
            cd_minutes INTEGER,
            aliases TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS boss_status (
            content TEXT PRIMARY KEY,
            last_kill TEXT,
            next_spawn TEXT,
            FOREIGN KEY(content) REFERENCES boss_info(content)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM global_settings WHERE key = 'event_mode'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO global_settings VALUES ('event_mode', 'normal')")
        conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM boss_info")
    if cursor.fetchone()[0] == 0:
        raw_boss_json = """
        [
          {"TIME": "30", "CONTENT": "[古魯丁地監第5層][托魯克]已重生", "NAME": "托魯克"},
          {"TIME": "30", "CONTENT": "[古魯丁地監第7層][卡修阿特]已重生", "NAME": "卡修阿特"},
          {"TIME": "30", "CONTENT": "[徘徊者之地][亡命之徒]已重生", "NAME": "亡命之徒"},
          {"TIME": "30", "CONTENT": "[徘徊者之地][亡命之徒]已重生", "NAME": "亡命"},
          {"TIME": "30", "CONTENT": "[淨化大地][咒術師斯科特]已重生", "NAME": "咒術師斯科特"},
          {"TIME": "30", "CONTENT": "[淨化大地][咒術師斯科特]已重生", "NAME": "斯科特"},
          {"TIME": "30", "CONTENT": "[說話之島][佩迪卡]已重生", "NAME": "佩迪卡"},
          {"TIME": "30", "CONTENT": "[說話之島][克頓阿托魯]已重生", "NAME": "克頓阿托魯"},
          {"TIME": "30", "CONTENT": "[說話之島][克頓阿托魯]已重生", "NAME": "克頓"},
          {"TIME": "30", "CONTENT": "[說話之島][哭臉]已重生", "NAME": "哭臉"},
          {"TIME": "30", "CONTENT": "[說話之島][巴魯德拉克]已重生", "NAME": "巴魯德拉克"},
          {"TIME": "30", "CONTENT": "[說話之島][巴魯德拉克]已重生", "NAME": "巴魯"},
          {"TIME": "30", "CONTENT": "[說話之島][斯卡魯斯]已重生", "NAME": "斯卡"},
          {"TIME": "30", "CONTENT": "[說話之島][斯卡魯斯]已重生", "NAME": "斯卡魯斯"},
          {"TIME": "30", "CONTENT": "[說話之島][流口水的齊戈爾]已重生", "NAME": "齊戈爾"},
          {"TIME": "30", "CONTENT": "[說話之島][流口水的齊戈爾]已重生", "NAME": "流口水的齊戈爾"},
          {"TIME": "30", "CONTENT": "[說話之島地監第2層][黑鋼]已重生", "NAME": "黑鋼"},
          {"TIME": "30", "CONTENT": "[黑戰艦第2層][沒落的德佩托]已重生", "NAME": "沒落的德佩托"},
          {"TIME": "30", "CONTENT": "[黑戰艦第2層][沒落的德佩托]已重生", "NAME": "德佩托"},
          {"TIME": "120", "CONTENT": "[亞丁城堡監獄第1層][黑蛇騎士團麥肯]已重生", "NAME": "麥"},
          {"TIME": "120", "CONTENT": "[亞丁城堡監獄第1層][黑蛇騎士團麥肯]已重生", "NAME": "麥肯"},
          {"TIME": "120", "CONTENT": "[亞丁農場][黑虎恰姆帕瓦特]已重生", "NAME": "黑虎"},
          {"TIME": "120", "CONTENT": "[亞丁農場][黑虎恰姆帕瓦特]已重生", "NAME": "黑虎恰姆帕瓦特"},
          {"TIME": "120", "CONTENT": "[光與影子森林][屠殺者莫利提亞]已重生", "NAME": "屠殺者"},
          {"TIME": "120", "CONTENT": "[光與影子森林][屠殺者莫利提亞]已重生", "NAME": "茉莉"},
          {"TIME": "120", "CONTENT": "[光與影子森林][屠殺者莫利提亞]已重生", "NAME": "莫利提亞"},
          {"TIME": "120", "CONTENT": "[古魯丁地監第4層][奧杜亞]已重生", "NAME": "奧杜亞"},
          {"TIME": "120", "CONTENT": "[死亡廢墟][殺戮者]已重生", "NAME": "胖"},
          {"TIME": "120", "CONTENT": "[死亡森林][卡司特王]已重生", "NAME": "卡司特王"},
          {"TIME": "120", "CONTENT": "[死亡森林][卡司特王]已重生", "NAME": "卡王"},
          {"TIME": "120", "CONTENT": "[波若斯妖魔部落][尼羅德]已重生", "NAME": "n"},
          {"TIME": "120", "CONTENT": "[海賊墳墓][乾渴的德雷克]已重生", "NAME": "海賊"},
          {"TIME": "120", "CONTENT": "[海賊墳墓][乾渴的德雷克]已重生", "NAME": "德雷克"},
          {"TIME": "120", "CONTENT": "[瑪幽雪壁][大腳]已重生", "NAME": "大腳"},
          {"TIME": "120", "CONTENT": "[賽蓮號第二區][巴爾博薩夫人]已重生", "NAME": "肥"},
          {"TIME": "120", "CONTENT": "[賽蓮號第二區][巴爾博薩夫人]已重生", "NAME": "夫人"},
          {"TIME": "120", "CONTENT": "[風木東部沙漠][卡爾迪修]已重生", "NAME": "CE"},
          {"TIME": "120", "CONTENT": "[風木東部沙漠][卡爾迪修]已重生", "NAME": "蜥蜴王"},
          {"TIME": "120", "CONTENT": "[龍之谷][一區飛龍]已重生", "NAME": "飛龍1"},
          {"TIME": "120", "CONTENT": "[龍之谷][一區飛龍]已重生", "NAME": "1"},
          {"TIME": "120", "CONTENT": "[龍之谷][三區飛龍]已重生", "NAME": "3"},
          {"TIME": "120", "CONTENT": "[龍之谷][三區飛龍]已重生", "NAME": "飛龍3"},
          {"TIME": "120", "CONTENT": "[龍之谷][二區飛龍]已重生", "NAME": "飛龍2"},
          {"TIME": "120", "CONTENT": "[龍之谷][二區飛龍]已重生", "NAME": "2"},
          {"TIME": "120", "CONTENT": "[龍之谷][四區飛龍]已重生", "NAME": "4"},
          {"TIME": "120", "CONTENT": "[龍之谷][四區飛龍]已重生", "NAME": "飛龍4"},
          {"TIME": "180", "CONTENT": "[說話之島地監第1層][獻上祭品的庫約]已重生", "NAME": "庫約"},
          {"TIME": "240", "CONTENT": "[古魯丁地監第6層][克洛林]已重生", "NAME": "克洛林"},
          {"TIME": "240", "CONTENT": "[妖魔森林][奈克偌斯]已重生", "NAME": "奈克"},
          {"TIME": "240", "CONTENT": "[妖魔森林][奈克偌斯]已重生", "NAME": "N"},
          {"TIME": "240", "CONTENT": "[妖魔森林][奈克偌斯]已重生", "NAME": "奈克偌斯"},
          {"TIME": "240", "CONTENT": "[妖魔森林][烏勒庫斯]已重生", "NAME": "W"},
          {"TIME": "240", "CONTENT": "[妖魔森林][烏勒庫斯]已重生", "NAME": "烏勒"},
          {"TIME": "240", "CONTENT": "[影子山寨][頭目哈格瑪]已重生", "NAME": "哈格瑪"},
          {"TIME": "240", "CONTENT": "[影子山寨][頭目哈格瑪]已重生", "NAME": "哈"},
          {"TIME": "240", "CONTENT": "[影子山寨][頭目哈格瑪]已重生", "NAME": "頭目"},
          {"TIME": "240", "CONTENT": "[悲哀森林][庫爾託]已重生", "NAME": "狼王"},
          {"TIME": "240", "CONTENT": "[悲哀森林][庫爾託]已重生", "NAME": "狼"},
          {"TIME": "240", "CONTENT": "[螞蟻洞窟地監第3層][巨蟻女皇]已重生", "NAME": "蟻后"},
          {"TIME": "240", "CONTENT": "[螞蟻洞窟地監第3層][巨蟻女皇]已重生", "NAME": "巨蟻女皇"},
          {"TIME": "240", "CONTENT": "[跨服][扭曲的艾奧特]已重生", "NAME": "艾奧特"},
          {"TIME": "240", "CONTENT": "[跨服][扭曲的艾奧特]已重生", "NAME": "扭曲"},
          {"TIME": "240", "CONTENT": "[跨服][扭曲的艾奧特]已重生", "NAME": "扭曲的艾奧特"},
          {"TIME": "240", "CONTENT": "[遺忘的春之庭院][審判者拉馬修]已重生", "NAME": "拉馬修"},
          {"TIME": "240", "CONTENT": "[遺忘的春之庭院][審判者拉馬修]已重生", "NAME": "審判"},
          {"TIME": "240", "CONTENT": "[遺忘的春之庭院][審判者拉馬修]已重生", "NAME": "蛇"},
          {"TIME": "240", "CONTENT": "[遺忘的春之庭院][審判者拉馬修]已重生", "NAME": "審判者"},
          {"TIME": "240", "CONTENT": "[霧月島][史前巨鱷]已重生", "NAME": "史前巨鱷"},
          {"TIME": "240", "CONTENT": "[霧月島][史前巨鱷]已重生", "NAME": "巨鱷"},
          {"TIME": "360", "CONTENT": "[古魯丁地監三四樓][四色]已重生", "NAME": "四色"},
          {"TIME": "360", "CONTENT": "[峽谷支配者][二巨]已重生", "NAME": "巨"},
          {"TIME": "360", "CONTENT": "[峽谷支配者][二巨]已重生", "NAME": "二巨"},
          {"TIME": "360", "CONTENT": "[峽谷支配者][二巨]已重生", "NAME": "吞噬岩石的戈爾森"},
          {"TIME": "120", "CONTENT": "[波若斯妖魔部落][尼羅德]已重生", "NAME": "尼羅德"}
        ]
        """
        boss_list = json.loads(raw_boss_json)
        temp_db = {}
        for item in boss_list:
            content = item["CONTENT"]
            parts = content.replace("已重生", "").split("][")
            loc = parts[0].replace("[", "") if len(parts) > 0 else "未知"
            r_name = parts[1].replace("]", "") if len(parts) > 1 else "未知"
            if content not in temp_db:
                temp_db[content] = {"real_name": r_name, "location": loc, "cd": int(item["TIME"]) * 2, "aliases": set()}
            temp_db[content]["aliases"].add(item["NAME"])
            
        for content, info in temp_db.items():
            aliases_str = ",".join(list(info["aliases"]))
            cursor.execute("INSERT INTO boss_info VALUES (?, ?, ?, ?, ?)", (content, info["real_name"], info["location"], info["cd"], aliases_str))
            cursor.execute("INSERT INTO boss_status VALUES (?, NULL, NULL)", (content,))
        conn.commit()
    conn.close()

def get_event_mode():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM global_settings WHERE key = 'event_mode'")
    mode = cursor.fetchone()[0]
    conn.close()
    return mode

def set_event_mode(mode):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE global_settings SET value = ? WHERE key = 'event_mode'", (mode,))
    conn.commit()
    conn.close()

def get_all_bosses_from_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT i.content, i.real_name, i.location, i.cd_minutes, i.aliases, s.last_kill, s.next_spawn 
        FROM boss_info i
        JOIN boss_status s ON i.content = s.content
    """, conn)
    conn.close()
    return df

def update_kill_time_in_db(content, last_kill, next_spawn):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO boss_status (content, last_kill, next_spawn) VALUES (?, ?, ?)", (content, last_kill, next_spawn))
    conn.commit()
    conn.close()

def clear_all_boss_times_in_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE boss_status SET last_kill = NULL, next_spawn = NULL")
    conn.commit()
    conn.close()

def update_boss_settings_in_db(content, new_name, new_cd, new_aliases):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE boss_info 
        SET real_name = ?, cd_minutes = ?, aliases = ?
        WHERE content = ?
    """, (new_name, new_cd, new_aliases, content))
    conn.commit()
    conn.close()

init_db()

# -------------------------------------------------------------------------
# 2. 全局活動狀態看板
# -------------------------------------------------------------------------
current_mode = get_event_mode()
if current_mode == "half":
    st.error("🚨 警告：目前全服正處於【出王時間減半】活動期間！所有重生時間自動砍半計算。")
    time_multiplier = 0.5
else:
    st.info("ℹ️ 目前狀態：正常模式（標準出王週期計算）。")
    time_multiplier = 1.0

# -------------------------------------------------------------------------
# 3. 側邊欄擊殺回報功能 (✨ 移除會引發崩潰的強制修改，改用表單快取重置法)
# -------------------------------------------------------------------------
st.sidebar.header("⚔️ 擊殺回報")
boss_df = get_all_bosses_from_db()

search_options = {}
for idx, row in boss_df.iterrows():
    aliases_list = row['aliases'].split(",")
    actual_cd = int(row['cd_minutes'] * time_multiplier)
    for alias in aliases_list:
        if alias.strip():
            search_options[f"{alias} ({row['location']})"] = {
                "content": row['content'], "real_name": row['real_name'], "cd_minutes": actual_cd
            }

menu_list = [""] + sorted(list(search_options.keys()))

# 為了在送出後能乾淨重置，我們將擊殺回報區塊包進一個沒有確認按鈕的虛擬小容器（或稱獨立控制區）
# 這裡使用獨一無二的隨機 key

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import sqlite3
import re

st.set_page_config(page_title="天堂W 盟用王表 (自動刷新版)", layout="wide")
st.title("🏰 《天堂W》王表管理系統")

DB_FILE = "boss.db"

# -------------------------------------------------------------------------
# 🛠 輔助函數：取得台灣時間 (台北時區 UTC+8)
# -------------------------------------------------------------------------
def get_tw_now():
    tw_tz = timezone(timedelta(hours=8))
    return datetime.now(tw_tz).replace(tzinfo=None)

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
          {"TIME": "240", "CONTENT": "[妖魔森林][烏勒庫斯]已重生", "NAME":

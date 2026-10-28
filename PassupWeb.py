import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

DATA_FILE = "passup_records.json"

# 页面配置
st.set_page_config(page_title="Passup Record App", page_icon="📊", layout="centered")

# 加载数据
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# 保存数据
def save_data(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

records = load_data()

st.title("📊 Daily Passup Record")

# 初始化 Session State 用于控制编辑状态
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# 查找当前是否在编辑某条记录
editing_record = None
if st.session_state.edit_id is not None:
    editing_record = next((r for r in records if r["id"] == st.session_state.edit_id), None)

# ==================== 1. 表单区域 ====================
form_title = f"✏️ Edit Record (ID: {st.session_state.edit_id})" if editing_record else "➕ Add New Passup Record"
with st.form("passup_form", clear_submit_after=False):
    st.subheader(form_title)
    
    col1, col2 = st.columns(2)
    with col1:
        default_date = datetime.strptime(editing_record["date"], "%Y-%m-%d").date() if editing_record else datetime.now().date()
        date_val = st.date_input("Date", value=default_date)
    with col2:
        terminals = ["Terminal 1", "Terminal 2", "Terminal 3", "Terminal 4"]
        default_term_idx = terminals.index(editing_record["terminal"]) if editing_record and editing_record["terminal"] in terminals else 0
        terminal_val = st.selectbox("Terminal", terminals, index=default_term_idx)

    col3, col4, col5 = st.columns(
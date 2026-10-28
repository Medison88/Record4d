import json
import os
import streamlit as st
from datetime import datetime
import pandas as pd

# 网页页面基础配置
st.set_page_config(page_title="4D 号码记录小助手", page_icon="🎲", layout="centered")

DATA_FILE = "my_4d_records.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_data(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

st.title("🎲 4D 号码记录与管理")
st.markdown("在电脑或手机浏览器上随时随地记录你的 4D 账目！")

records = load_data()

# 1. 输入表单区域
with st.form("entry_form", clear_on_submit=True):
    st.subheader("➕ 添加新记录")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        date_val = st.date_input("购买/开奖日期", value=datetime.now())
    with col2:
        num_val = st.text_input("4D号码 (4位)", max_chars=4)
    with col3:
        company_val = st.selectbox("博彩公司", ["Magnum", "Toto", "Damacai", "STC", "CashSweep", "Sabah88", "Dragon4D"])

    st.markdown("---")
    st.markdown("**玩法金额明细**")
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    with b_col1:
        big_val = st.text_input("Big 金额", value="")
    with b_col2:
        small_val = st.text_input("Small 金额", value="")
    with b_col3:
        ibox_val = st.text_input("Ibox 金额", value="")
    with b_col4:
        pm_val = st.text_input("PM 金额", value="")

    notes_val = st.text_input("备注", value="")
    
    submitted = st.form_submit_button("💾 保存记录")
    
    if submitted:
        if not num_val.isdigit() or len(num_val) != 4:
            st.error("❌ 4D 号码必须是 4 位纯数字！")
        else:
            selected_bets = []
            total_amount = 0.0
            try:
                if big_val:
                    val = float(big_val)
                    selected_bets.append(f"Big: {big_val}")
                    total_amount += val
                if small_val:
                    val = float(small_val)
                    selected_bets.append(f"Small: {small_val}")
                    total_amount += val
                if ibox_val:
                    val = float(ibox_val)
                    selected_bets.append(f"Ibox: {ibox_val}")
                    total_amount += val
                if pm_val:
                    val = float(pm_val)
                    selected_bets.append(f"PM: {pm_val}")
                    total_amount += val
            except ValueError:
                st.error("❌ 玩法金额必须是有效的数字！")
                st.stop()

            if not selected_bets:
                st.warning("⚠️ 请至少在一个玩法输入框中填入金额！")
            else:
                bet_str = " | ".join(selected_bets)
                record = {
                    "id": len(records) + 1,
                    "date": date_val.strftime("%Y-%m-%d"),
                    "number": num_val,
                    "company": company_val,
                    "bet_type": bet_str,
                    "total": total_amount,
                    "notes": notes_val if notes_val else "无"
                }
                records.append(record)
                save_data(records)
                st.success(f"🎉 号码 [{num_val}] 已成功保存，总计: {total_amount}！")

# 2. 列表展示与删除区域
st.markdown("---")
st.subheader("📋 号码记录列表")

if records:
    # 转换为 DataFrame 表格展示
    df = pd.DataFrame(records)
    # 按日期倒序排列
    df = df.sort_values(by="date", ascending=False)
    
    # 在网页中展示美观的表格
    st.dataframe(
        df[["id", "date", "number", "company", "bet_type", "total", "notes"]],
        use_container_width=True,
        hide_index=True
    )

    # 删除记录功能
    with st.form("delete_form"):
        st.markdown("### 🗑️ 删除记录")
        record_ids = [r["id"] for r in records]
        del_id = st.selectbox("选择要删除的记录 ID", record_ids)
        del_submitted = st.form_submit_button("确认删除选中记录")
        
        if del_submitted:
            records = [r for r in records if r["id"] != del_id]
            # 重新整理 ID
            for idx, r in enumerate(records, start=1):
                r["id"] = idx
            save_data(records)
            st.success(f"🗑️ 记录 ID {del_id} 已成功删除！")
            st.rerun()
else:
    st.info("📭 目前还没有任何记录，请在上方添加。")
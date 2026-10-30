from datetime import datetime
import json
import os
import gspread
import pandas as pd
import streamlit as st

# 页面配置
st.set_page_config(page_title="Passup Record App", page_icon="📊", layout="centered")

# ==================== Google Sheets 云端数据库配置 ====================
SPREADSHEET_ID = "16GTnxyRGxVD1aNRWBE3LyihraLlPbd7otGqRG_bv0is"


@st.cache_resource
def init_gspread():
  if "gcp_service_account" in st.secrets:
    creds_json = st.secrets["gcp_service_account"]
    if isinstance(creds_json, str):
      creds_dict = json.loads(creds_json)
    else:
      creds_dict = dict(creds_json)
    gc = gspread.service_account_from_dict(creds_dict)
  else:
    gc = gspread.service_account(filename="credentials.json")
  return gc.open_by_key(SPREADSHEET_ID).sheet1


try:
  sheet = init_gspread()
except Exception as e:
  st.error(f"连接 Google Sheets 失败: {e}")
  st.stop()


def load_data():
  try:
    records = sheet.get_all_records()
    for r in records:
      r["id"] = int(r.get("id", 0)) if r.get("id") else 0
      r["pay_dollar"] = float(r.get("pay_dollar", 0.0))
      r["pay_q"] = float(r.get("pay_q", 0.0))
      r["unpaid"] = float(r.get("unpaid", 0.0))
      r["cash"] = float(r.get("cash", 0.0))
      r["epay"] = float(r.get("epay", 0.0))
      r["total"] = float(r.get("total", 0.0))
    return records
  except Exception as e:
    st.error(f"读取 Google Sheets 数据失败: {e}")
    return []


def save_data(records):
  try:
    sheet.clear()
    headers = [
        "id",
        "date",
        "terminal",
        "pay_dollar",
        "pay_q",
        "unpaid",
        "cash",
        "epay",
        "total",
        "note",
    ]
    sheet.append_row(headers)
    for r in records:
      row = [
          r.get("id"),
          r.get("date"),
          r.get("terminal"),
          r.get("pay_dollar"),
          r.get("pay_q"),
          r.get("unpaid"),
          r.get("cash"),
          r.get("epay"),
          r.get("total"),
          r.get("note", "No Record"),
      ]
      sheet.append_row(row)
    return True
  except Exception as e:
    st.error(f"保存到 Google Sheets 失败: {e}")
    return False


records = load_data()

st.title("📊 Daily Passup Record")

if "edit_id" not in st.session_state:
  st.session_state.edit_id = None

editing_record = None
if st.session_state.edit_id is not None:
  editing_record = next(
      (r for r in records if r["id"] == st.session_state.edit_id), None
  )

# ==================== 初始化输入框的 Session State 默认值 ====================
if "f_pay_dollar" not in st.session_state:
  st.session_state.f_pay_dollar = (
      float(editing_record["pay_dollar"]) if editing_record else 0.0
  )
if "f_pay_q" not in st.session_state:
  st.session_state.f_pay_q = (
      float(editing_record["pay_q"]) if editing_record else 0.0
  )
if "f_unpaid" not in st.session_state:
  st.session_state.f_unpaid = (
      float(editing_record["unpaid"]) if editing_record else 0.0
  )
if "f_cash" not in st.session_state:
  st.session_state.f_cash = (
      float(editing_record["cash"]) if editing_record else 0.0
  )
if "f_epay" not in st.session_state:
  st.session_state.f_epay = (
      float(editing_record["epay"]) if editing_record else 0.0
  )
if "f_note" not in st.session_state:
  st.session_state.f_note = (
      str(editing_record["note"]) if editing_record else ""
  )

# ==================== 1. 输入区域 ====================
form_title = (
    f"✏️ Edit Record (ID: {st.session_state.edit_id})"
    if editing_record
    else "➕ Add New Passup Record"
)
st.subheader(form_title)

col1, col2 = st.columns(2)
with col1:
  default_date = (
      datetime.strptime(editing_record["date"], "%Y-%m-%d").date()
      if editing_record
      else datetime.now().date()
  )
  date_val = st.date_input("Date", value=default_date, key="f_date")

with col2:
  terminals = ["Terminal 1", "Terminal 2", "Terminal 3", "Terminal 4"]
  default_term_idx = (
      terminals.index(editing_record["terminal"])
      if editing_record and editing_record["terminal"] in terminals
      else 0
  )
  terminal_val = st.selectbox(
      "Terminal", terminals, index=default_term_idx, key="f_terminal"
  )

col3, col4, col5 = st.columns(3)
with col3:
  pay_dollar = st.number_input(
      "Payment ($)", format="%.2f", key="f_pay_dollar"
  )
with col4:
  pay_q = st.number_input("Payment (Q)", format="%.2f", key="f_pay_q")
with col5:
  unpaid = st.number_input("Unpaid Ticket", format="%.2f", key="f_unpaid")

col6, col7 = st.columns(2)
with col6:
  cash = st.number_input("Cash", format="%.2f", key="f_cash")
with col7:
  epay = st.number_input("E-Pay", format="%.2f", key="f_epay")

note = st.text_input("Note", key="f_note")

# 提交按钮
submitted = st.button("💾 Save / Update Record", type="primary")

if submitted:
  total = pay_dollar + unpaid + cash + epay
  date_str = date_val.strftime("%Y-%m-%d")

  if st.session_state.edit_id is None:
    new_record = {
        "id": len(records) + 1,
        "date": date_str,
        "terminal": terminal_val,
        "pay_dollar": pay_dollar,
        "pay_q": pay_q,
        "unpaid": unpaid,
        "cash": cash,
        "epay": epay,
        "total": total,
        "note": note.strip() or "No Record",
    }
    records.append(new_record)
    st.success("Record saved successfully to Google Sheets!")
  else:
    for r in records:
      if r["id"] == st.session_state.edit_id:
        r["date"] = date_str
        r["terminal"] = terminal_val
        r["pay_dollar"] = pay_dollar
        r["pay_q"] = pay_q
        r["unpaid"] = unpaid
        r["cash"] = cash
        r["epay"] = epay
        r["total"] = total
        r["note"] = note.strip() or "No Record"
        break
    st.success(f"Record ID {st.session_state.edit_id} updated successfully!")
    st.session_state.edit_id = None

  save_data(records)

  # 关键：保存成功后，显式将所有输入框的值清空/重置并删除缓存状态
  st.session_state.f_pay_dollar = 0.0
  st.session_state.f_pay_q = 0.0
  st.session_state.f_unpaid = 0.0
  st.session_state.f_cash = 0.0
  st.session_state.f_epay = 0.0
  st.session_state.f_note = ""

  st.rerun()

if st.session_state.edit_id is not None:
  if st.button("❌ Cancel Edit"):
    st.session_state.edit_id = None
    # 取消编辑时也重置格子
    st.session_state.f_pay_dollar = 0.0
    st.session_state.f_pay_q = 0.0
    st.session_state.f_unpaid = 0.0
    st.session_state.f_cash = 0.0
    st.session_state.f_epay = 0.0
    st.session_state.f_note = ""
    st.rerun()

st.divider()

# ==================== 2. 历史与筛选区域 ====================
st.subheader("📋 Records History & Summary")

filter_date = st.date_input(
    "Filter by Date", value=datetime.now().date(), key="filter_date"
)
filter_date_str = filter_date.strftime("%Y-%m-%d")

filtered_records = [r for r in records if r.get("date") == filter_date_str]

if filtered_records:
  df = pd.DataFrame(filtered_records)
  display_cols = [
      "id",
      "date",
      "terminal",
      "pay_dollar",
      "pay_q",
      "unpaid",
      "cash",
      "epay",
      "total",
      "note",
  ]
  df = df[[c for c in display_cols if c in df.columns]]
  st.dataframe(df, use_container_width=True, hide_index=True)

  sum_dollar = sum(r["pay_dollar"] for r in filtered_records)
  sum_q = sum(r["pay_q"] for r in filtered_records)
  sum_unpaid = sum(r["unpaid"] for r in filtered_records)
  sum_cash = sum(r["cash"] for r in filtered_records)
  sum_epay = sum(r["epay"] for r in filtered_records)
  sum_total = sum(r["total"] for r in filtered_records)

  st.markdown("### 📊 Daily Summary (Overall)")
  sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
  with sc1:
    st.markdown(f"**Pay ($)**<br>{sum_dollar:.2f}", unsafe_allow_html=True)
  with sc2:
    st.markdown(f"**Pay (Q)**<br>{sum_q:.2f}", unsafe_allow_html=True)
  with sc3:
    st.markdown(f"**Unpaid**<br>{sum_unpaid:.2f}", unsafe_allow_html=True)
  with sc4:
    st.markdown(f"**Cash**<br>{sum_cash:.2f}", unsafe_allow_html=True)
  with sc5:
    st.markdown(f"**E-Pay**<br>{sum_epay:.2f}", unsafe_allow_html=True)
  with sc6:
    st.markdown(f"**Total**<br>{sum_total:.2f}", unsafe_allow_html=True)

  st.divider()

  st.subheader("⚙️ Manage Selected Date Records")
  record_options = {
      f"ID {r['id']} | {r['terminal']} | Total: {r['total']}": r["id"]
      for r in filtered_records
  }
  selected_option = st.selectbox(
      "Select a record to Edit or Delete", options=list(record_options.keys())
  )

  if selected_option:
    target_id = record_options[selected_option]
    col_edit, col_del = st.columns(2)
    with col_edit:
      if st.button("✏️ Edit This Record"):
        st.session_state.edit_id = target_id
        # 点击编辑时，将该记录的值填入对应的 session_state 中
        target_rec = next(r for r in records if r["id"] == target_id)
        st.session_state.f_pay_dollar = float(target_rec["pay_dollar"])
        st.session_state.f_pay_q = float(target_rec["pay_q"])
        st.session_state.f_unpaid = float(target_rec["unpaid"])
        st.session_state.f_cash = float(target_rec["cash"])
        st.session_state.f_epay = float(target_rec["epay"])
        st.session_state.f_note = str(target_rec["note"])
        st.rerun()
    with col_del:
      if st.button("🗑️ Delete This Record", type="primary"):
        records = [r for r in records if r["id"] != target_id]
        for idx, r in enumerate(records, start=1):
          r["id"] = idx
        save_data(records)
        if st.session_state.edit_id == target_id:
          st.session_state.edit_id = None
        st.success("Record deleted successfully!")
        st.rerun()
else:
  st.info(f"No records found for date: {filter_date_str}")

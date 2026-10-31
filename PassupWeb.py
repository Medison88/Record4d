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
      r["cancel"] = float(r.get("cancel", 0.0))
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
        "cancel",
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
          r.get("cancel"),
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

if "form_version" not in st.session_state:
  st.session_state.form_version = 0

editing_record = None
if st.session_state.edit_id is not None:
  editing_record = next(
      (r for r in records if r["id"] == st.session_state.edit_id), None
  )

# ==================== 1. 输入表单区域 ====================
form_title = (
    f"✏️ Edit Record (ID: {st.session_state.edit_id})"
    if editing_record
    else "➕ Add New Passup Record"
)
st.subheader(form_title)

v = st.session_state.form_version

col1, col2 = st.columns(2)
with col1:
  default_date = (
      datetime.strptime(editing_record["date"], "%Y-%m-%d").date()
      if editing_record
      else datetime.now().date()
  )
  date_val = st.date_input("Date", value=default_date, key=f"f_date_{v}")

with col2:
  terminals = ["Terminal 1", "Terminal 2", "Terminal 3", "Terminal 4"]
  default_term_idx = (
      terminals.index(editing_record["terminal"])
      if editing_record and editing_record["terminal"] in terminals
      else 0
  )
  terminal_val = st.selectbox(
      "Terminal",
      terminals,
      index=default_term_idx,
      key=f"f_terminal_{v}",
  )

col3, col4, col5 = st.columns(3)
with col3:
  pay_dollar = st.number_input(
      "Payment ($)",
      value=float(editing_record["pay_dollar"]) if editing_record else 0.0,
      format="%.2f",
      key=f"f_pay_dollar_{v}",
  )
with col4:
  pay_q = st.number_input(
      "Payment (Q)",
      value=float(editing_record["pay_q"]) if editing_record else 0.0,
      format="%.2f",
      key=f"f_pay_q_{v}",
  )
with col5:
  unpaid = st.number_input(
      "Unpaid Ticket",
      value=float(editing_record["unpaid"]) if editing_record else 0.0,
      format="%.2f",
      key=f"f_unpaid_{v}",
  )

col6, col7 = st.columns(2)
with col6:
  cash = st.number_input(
      "Cash",
      value=float(editing_record["cash"]) if editing_record else 0.0,
      format="%.2f",
      key=f"f_cash_{v}",
  )
with col7:
  epay = st.number_input(
      "E-Pay",
      value=float(editing_record["epay"]) if editing_record else 0.0,
      format="%.2f",
      key=f"f_epay_{v}",
  )

cancel = st.number_input(
    "Cancel",
    value=float(editing_record["cancel"]) if editing_record else 0.0,
    min_value=0.0,
    format="%.2f",
    key=f"f_cancel_{v}",
)

# ==================== 2. Manage Selected Records 区域 (紧跟在 Note 下方) ====================
filter_date_temp = date_val.strftime("%Y-%m-%d")
current_date_records = [
    r for r in records if r.get("date") == filter_date_temp
]

if current_date_records:
  st.markdown("---")
  st.subheader("⚙️ Manage Selected Date Records")
  record_options = {
      f"ID {r['id']} | {r['terminal']} | Total: {r['total']}": r["id"]
      for r in current_date_records
  }
  selected_option = st.selectbox(
      f"Select a record for {filter_date_temp} to Edit or Delete",
      options=list(record_options.keys()),
      key=f"manage_select_{v}",
  )

  if selected_option:
    target_id = record_options[selected_option]
    col_edit, col_del = st.columns(2)
    with col_edit:
      if st.button("✏️ Edit This Record", use_container_width=True):
        st.session_state.edit_id = target_id
        st.session_state.form_version += 1
        st.rerun()
    with col_del:
      if st.button(
          "🗑️ Delete This Record", type="primary", use_container_width=True
      ):
        records = [r for r in records if r["id"] != target_id]
        for idx, r in enumerate(records, start=1):
          r["id"] = idx
        save_data(records)
        if st.session_state.edit_id == target_id:
          st.session_state.edit_id = None
        st.success("Record deleted successfully!")
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ==================== 3. Save / Update 按钮 (放在 Manage 区域下方) ====================
submitted = st.button(
    "💾 Save / Update Record", type="primary", use_container_width=True
)

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
        "cancel": cancel,
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
        r["cancel"] = cancel
        break
    st.success(f"Record ID {st.session_state.edit_id} updated successfully!")
    st.session_state.edit_id = None

  save_data(records)
  st.session_state.form_version += 1
  st.rerun()

if st.session_state.edit_id is not None:
  if st.button("❌ Cancel Edit", use_container_width=True):
    st.session_state.edit_id = None
    st.session_state.form_version += 1
    st.rerun()

st.divider()

# ==================== 4. 历史表格与汇总统计区域 ====================
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
      "cancel",
  ]
  df = df[[c for c in display_cols if c in df.columns]]
  st.dataframe(df, use_container_width=True, hide_index=True)

  sum_dollar = sum(r["pay_dollar"] for r in filtered_records)
  sum_q = sum(r["pay_q"] for r in filtered_records)
  sum_unpaid = sum(r["unpaid"] for r in filtered_records)
  sum_cash = sum(r["cash"] for r in filtered_records)
  sum_epay = sum(r["epay"] for r in filtered_records)
  sum_total = sum(r["total"] for r in filtered_records)
  sum_cancel = sum(r["cancel"] for r in filtered_records)

  st.markdown("### 📊 Daily Summary (Overall)")
  sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
  with sc1:
    st.markdown(
        f"<p style='margin:0;font-size:12px;color:gray;'>Pay"
        f" ($)</p><p style='margin:0;font-size:16px;font-weight:bold;'>{sum_dollar:.2f}</p>",
        unsafe_allow_html=True,
    )
  with sc2:
    st.markdown(
        f"<p style='margin:0;font-size:12px;color:gray;'>Pay"
        f" (Q)</p><p style='margin:0;font-size:16px;font-weight:bold;'>{sum_q:.2f}</p>",
        unsafe_allow_html=True,
    )
  with sc3:
    st.markdown(
        f"<p style='margin:0;font-size:12px;color:gray;'>Unpaid</p><p"
        f" style='margin:0;font-size:16px;font-weight:bold;'>{sum_unpaid:.2f}</p>",
        unsafe_allow_html=True,
    )
  with sc4:
    st.markdown(
        f"<p style='margin:0;font-size:12px;color:gray;'>Cash</p><p"
        f" style='margin:0;font-size:16px;font-weight:bold;'>{sum_cash:.2f}</p>",
        unsafe_allow_html=True,
    )
  with sc5:
    st.markdown(
        f"<p style='margin:0;font-size:12px;color:gray;'>E-Pay</p><p"
        f" style='margin:0;font-size:16px;font-weight:bold;'>{sum_epay:.2f}</p>",
        unsafe_allow_html=True,
    )
  with sc6:
    st.markdown(
        f"<p style='margin:0;font-size:12px;color:gray;'>Total</p><p"
        f" style='margin:0;font-size:16px;font-weight:bold;color:#007aff;'>{sum_total:.2f}</p>",
        unsafe_allow_html=True,
    )

  st.markdown("### 🏷️ Breakdown by Terminal & Grand Total")
  terminals_list = ["Terminal 1", "Terminal 2", "Terminal 3", "Terminal 4"]
  term_summary_data = []

  for t in terminals_list:
    t_records = [r for r in filtered_records if r.get("terminal") == t]
    t_dollar = sum(r["pay_dollar"] for r in t_records)
    t_q = sum(r["pay_q"] for r in t_records)
    t_unpaid = sum(r["unpaid"] for r in t_records)
    t_cash = sum(r["cash"] for r in t_records)
    t_epay = sum(r["epay"] for r in t_records)
    t_total = sum(r["total"] for r in t_records)
    t_cancel = sum(r["cancel"] for r in t_records)

    term_summary_data.append({
        "Terminal": t,
        "Pay ($)": f"{t_dollar:.2f}",
        "Pay (Q)": f"{t_q:.2f}",
        "Unpaid": f"{t_unpaid:.2f}",
        "Cash": f"{t_cash:.2f}",
        "E-Pay": f"{t_epay:.2f}",
        "Cancel": f"{t_cancel:.2f}",
        "Total": f"{t_total:.2f}",
    })

  term_summary_data.append({
      "Terminal": "Grand Total",
      "Pay ($)": f"{sum_dollar:.2f}",
      "Pay (Q)": f"{sum_q:.2f}",
      "Unpaid": f"{sum_unpaid:.2f}",
      "Cancel": f"{sum_cancel:.2f}",
      "E-Pay": f"{sum_epay:.2f}",
      "Cancel": cancel,
      "Total": f"{sum_total:.2f}",
  })

  df_term_summary = pd.DataFrame(term_summary_data)
  st.dataframe(df_term_summary, use_container_width=True, hide_index=True)
else:
  st.info(f"No records found for date: {filter_date_str}")

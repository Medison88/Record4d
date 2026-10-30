from datetime import datetime
import json
import os
import gspread
import pandas as pd
import streamlit as st

# 页面配置
st.set_page_config(page_title="Passup Record App", page_icon="📊", layout="centered")

# ==================== Google Sheets 云端数据库配置 ====================
# 使用你专属的 Google Sheets ID，避免按名称搜索失败
SPREADSHEET_ID = "16GTnxyRGxVD1aNRWBE3LyihraLlPbd7otGqRG_bv0is"


@st.cache_resource
def init_gspread():
  if "gcp_service_account" in st.secrets:
    # 从 Streamlit Secrets 读取凭证
    creds_json = st.secrets["gcp_service_account"]
    if isinstance(creds_json, str):
      creds_dict = json.loads(creds_json)
    else:
      creds_dict = dict(creds_json)
    gc = gspread.service_account_from_dict(creds_dict)
  else:
    # 本地测试时读取同目录下的 credentials.json 文件
    gc = gspread.service_account(filename="credentials.json")

  # 使用 open_by_key 通过 ID 直接连接，100% 稳定
  return gc.open_by_key(SPREADSHEET_ID).sheet1


try:
  sheet = init_gspread()
except Exception as e:
  st.error(
      f"连接 Google Sheets 失败！请检查 Streamlit Secrets 配置。"
      f" 错误信息: {e}"
  )
  st.stop()


# 加载数据函数 (从 Google Sheets 读取)
def load_data():
  try:
    records = sheet.get_all_records()
    # 确保数值类型转换正确
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


# 保存/更新/删除数据函数 (同步写回 Google Sheets)
def save_data(records):
  try:
    # 清空表格并重新写入表头和所有数据，确保 ID 排序和内容完美同步
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


# 加载当前所有记录
records = load_data()

st.title("📊 Daily Passup Record")

# 初始化 Session State 用于控制编辑状态
if "edit_id" not in st.session_state:
  st.session_state.edit_id = None

# 查找当前是否在编辑某条记录
editing_record = None
if st.session_state.edit_id is not None:
  editing_record = next(
      (r for r in records if r["id"] == st.session_state.edit_id), None
  )

# ==================== 1. 表单区域 ====================
form_title = (
    f"✏️ Edit Record (ID: {st.session_state.edit_id})"
    if editing_record
    else "➕ Add New Passup Record"
)
with st.form("passup_form", clear_on_submit=False):
  st.subheader(form_title)

  col1, col2 = st.columns(2)
  with col1:
    default_date = (
        datetime.strptime(editing_record["date"], "%Y-%m-%d").date()
        if editing_record
        else datetime.now().date()
    )
    date_val = st.date_input("Date", value=default_date)
  with col2:
    terminals = ["Terminal 1", "Terminal 2", "Terminal 3", "Terminal 4"]
    default_term_idx = (
        terminals.index(editing_record["terminal"])
        if editing_record and editing_record["terminal"] in terminals
        else 0
    )
    terminal_val = st.selectbox("Terminal", terminals, index=default_term_idx)

  col3, col4, col5 = st.columns(3)
  with col3:
    pay_dollar = st.number_input(
        "Payment ($)",
        value=float(editing_record["pay_dollar"]) if editing_record else 0.0,
        format="%.2f",
    )
  with col4:
    pay_q = st.number_input(
        "Payment (Q)",
        value=float(editing_record["pay_q"]) if editing_record else 0.0,
        format="%.2f",
    )
  with col5:
    unpaid = st.number_input(
        "Unpaid Ticket",
        value=float(editing_record["unpaid"]) if editing_record else 0.0,
        format="%.2f",
    )

  col6, col7 = st.columns(2)
  with col6:
    cash = st.number_input(
        "Cash",
        value=float(editing_record["cash"]) if editing_record else 0.0,
        format="%.2f",
    )
  with col7:
    epay = st.number_input(
        "E-Pay",
        value=float(editing_record["epay"]) if editing_record else 0.0,
        format="%.2f",
    )

  note = st.text_input(
      "Note", value=editing_record["note"] if editing_record else ""
  )

  submitted = st.form_submit_button("💾 Save / Update Record")

  if submitted:
    total = pay_dollar + unpaid + cash + epay
    date_str = date_val.strftime("%Y-%m-%d")

    if st.session_state.edit_id is None:
      # 新增
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
      # 更新
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
      st.success(
          f"Record ID {st.session_state.edit_id} updated successfully in Google"
          " Sheets!"
      )
      st.session_state.edit_id = None

    save_data(records)
    st.rerun()

if st.session_state.edit_id is not None:
  if st.button("❌ Cancel Edit"):
    st.session_state.edit_id = None
    st.rerun()

st.divider()

# ==================== 2. 筛选与历史表格区域 ====================
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

  # 3. 顶部总计栏 (Summary)
  st.markdown("### 📊 Daily Summary (Overall)")
  sum_dollar = sum(r["pay_dollar"] for r in filtered_records)
  sum_q = sum(r["pay_q"] for r in filtered_records)
  sum_unpaid = sum(r["unpaid"] for r in filtered_records)
  sum_cash = sum(r["cash"] for r in filtered_records)
  sum_epay = sum(r["epay"] for r in filtered_records)
  sum_total = sum(r["total"] for r in filtered_records)

  sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
  with sc1:
    st.markdown(
        f"<p style='margin:0;font-size:12px;color:gray;'>Pay ($)</p><p"
        f" style='margin:0;font-size:16px;font-weight:bold;'>{sum_dollar:.2f}</p>",
        unsafe_allow_html=True,
    )
  with sc2:
    st.markdown(
        f"<p style='margin:0;font-size:12px;color:gray;'>Pay (Q)</p><p"
        f" style='margin:0;font-size:16px;font-weight:bold;'>{sum_q:.2f}</p>",
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

  # 3.1 终端明细表格 + Grand Total
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

    term_summary_data.append({
        "Terminal": t,
        "Pay ($)": f"{t_dollar:.2f}",
        "Pay (Q)": f"{t_q:.2f}",
        "Unpaid": f"{t_unpaid:.2f}",
        "Cash": f"{t_cash:.2f}",
        "E-Pay": f"{t_epay:.2f}",
        "Total": f"{t_total:.2f}",
    })

  # 追加 Grand Total 行
  term_summary_data.append({
      "Terminal": "Grand Total",
      "Pay ($)": f"{sum_dollar:.2f}",
      "Pay (Q)": f"{sum_q:.2f}",
      "Unpaid": f"{sum_unpaid:.2f}",
      "Cash": f"{sum_cash:.2f}",
      "E-Pay": f"{sum_epay:.2f}",
      "Total": f"{sum_total:.2f}",
  })

  df_term_summary = pd.DataFrame(term_summary_data)
  st.dataframe(df_term_summary, use_container_width=True, hide_index=True)

  st.divider()

  # 4. 修改与删除管理操作
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
        st.rerun()
    with col_del:
      if st.button("🗑️ Delete This Record", type="primary"):
        records = [r for r in records if r["id"] != target_id]
        for idx, r in enumerate(records, start=1):
          r["id"] = idx
        save_data(records)
        if st.session_state.edit_id == target_id:
          st.session_state.edit_id = None
        st.success("Record deleted successfully from Google Sheets!")
        st.rerun()
else:
  st.info(f"No records found for date: {filter_date_str}")

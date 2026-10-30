import base64
from datetime import datetime
import json
import os
import gspread
import pandas as pd
import streamlit as st

# 页面配置
st.set_page_config(
    page_title="Ticket Purchase & 4D Analysis", page_icon="🎟️", layout="centered"
)

# ==================== Google Sheets 云端数据库配置 (Calculate_Ticket_DB) ====================
SPREADSHEET_ID = "1j9R36vCXpSNPuQ8UuQU_k5gZm9xRPcIJ7RbN1hQrLq4"


@st.cache_resource
def init_gspread():
  try:
    if "gcp_b64" in st.secrets:
      json_str = base64.b64decode(st.secrets["gcp_b64"]).decode("utf-8")
      creds_dict = json.loads(json_str)

      # 替换私钥中的字面量 \n
      if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace(
            "\\n", "\n"
        )

      with open("credentials.json", "w", encoding="utf-8") as f:
        json.dump(creds_dict, f, ensure_ascii=False)

      gc = gspread.service_account(filename="credentials.json")
      return gc.open_by_key(SPREADSHEET_ID).sheet1
    elif "gcp_service_account" in st.secrets:
      creds_json = st.secrets["gcp_service_account"]
      creds_dict = (
          json.loads(creds_json)
          if isinstance(creds_json, str)
          else dict(creds_json)
      )
      gc = gspread.service_account_from_dict(creds_dict)
      return gc.open_by_key(SPREADSHEET_ID).sheet1
    else:
      gc = gspread.service_account(filename="credentials.json")
      return gc.open_by_key(SPREADSHEET_ID).sheet1
  except Exception as e:
    st.error(f"初始化 Google Sheets 失败: {e}")
    return None


sheet = init_gspread()
if sheet is None:
  st.stop()


# ==================== 辅助函数：将 BCN 列表转为纯数字无符号文本 ====================
def get_bcn_string(r):
  """将 bcn_list 转为纯文本（空格分隔，不带方括号和引号）"""
  bcn_val = r.get("bcn_list", [""] * 9)
  if isinstance(bcn_val, list):
    return " ".join([str(b).strip() for b in bcn_val if str(b).strip()])
  return str(bcn_val).strip()


# ==================== 云端数据读写函数（兼容与处理无符号 BCN） ====================
def load_data():
  try:
    rows = sheet.get_all_values()
    records = []
    if not rows:
      return []

    for row in rows:
      if not row or not row[0]:
        continue
      try:
        rid = int(row[0])
        bcn_raw = row[5] if len(row) > 5 else ""

        # 智能解析：兼容旧的 JSON 格式及新的纯数字空格分隔格式
        bcn_list = []
        if bcn_raw.startswith("["):
          try:
            bcn_list = json.loads(bcn_raw)
          except:
            bcn_list = []
        else:
          # 按空格切分，剔除空白项
          bcn_list = [b.strip() for b in bcn_raw.split() if b.strip()]

        # 补齐至 9 个元素以便表单回填
        while len(bcn_list) < 9:
          bcn_list.append("")
        bcn_list = bcn_list[:9]

        record = {
            "id": rid,
            "date": row[1] if len(row) > 1 else "",
            "draw": row[2] if len(row) > 2 else "",
            "number": row[3] if len(row) > 3 else "",
            "prize_type": row[4] if len(row) > 4 else "",
            "bcn_list": bcn_list,
            "serial": row[6] if len(row) > 6 else "",
            "combine": row[7] if len(row) > 7 else "",
            "score": int(row[8]) if len(row) > 8 and str(row[8]).isdigit() else 0,
            "percentage": row[9] if len(row) > 9 else "0.00%",
        }
        records.append(record)
      except ValueError:
        # 跳过表头行
        continue
    return records
  except Exception as e:
    st.error(f"读取 Google Sheets 数据失败: {e}")
    return []


def save_data_all(records):
  """全量覆写（用于修改和删除）"""
  try:
    sheet.clear()
    headers = [
        "id",
        "date",
        "draw",
        "number",
        "prize_type",
        "bcn_list",
        "serial",
        "combine",
        "score",
        "percentage",
    ]
    sheet.append_row(headers)
    data_to_write = []
    for r in records:
      row = [
          r.get("id"),
          r.get("date"),
          r.get("draw"),
          r.get("number"),
          r.get("prize_type", ""),
          get_bcn_string(r),  # 无符号纯数字 BCN
          r.get("serial", ""),
          r.get("combine", ""),
          r.get("score", 0),
          r.get("percentage", "0.00%"),
      ]
      data_to_write.append(row)
    if data_to_write:
      sheet.append_rows(data_to_write)
    return True
  except Exception as e:
    st.error(f"保存到 Google Sheets 失败: {e}")
    return False


def append_single_record(r):
  """增量追加单条记录（用于新增）"""
  try:
    row = [
        r.get("id"),
        r.get("date"),
        r.get("draw"),
        r.get("number"),
        r.get("prize_type", ""),
        get_bcn_string(r),  # 无符号纯数字 BCN
        r.get("serial", ""),
        r.get("combine", ""),
        r.get("score", 0),
        r.get("percentage", "0.00%"),
    ]
    sheet.append_row(row)
    return True
  except Exception as e:
    st.error(f"追加写入 Google Sheets 失败: {e}")
    return False


records = load_data()

st.title("🎟️ Ticket Purchase & 4D Analysis")

# 初始化 Session State 控制编辑状态
if "edit_id" not in st.session_state:
  st.session_state.edit_id = None

editing_record = None
if st.session_state.edit_id is not None:
  editing_record = next(
      (r for r in records if r["id"] == st.session_state.edit_id), None
  )

# 选项卡界面
tab_input, tab_search = st.tabs(
    ["📝 Ticket Input (录入窗口)", "🔍 Search & History (搜索窗口)"]
)

# ==================== TAB 1: 录入窗口 ====================
with tab_input:
  form_title = (
      f"✏️ Edit Record (ID: {st.session_state.edit_id})"
      if editing_record
      else "➕ Ticket Purchase & Calculator"
  )
  st.subheader(form_title)

  def_date = (
      datetime.strptime(editing_record["date"], "%d/%m/%Y").date()
      if editing_record and editing_record.get("date")
      else datetime.now().date()
  )
  def_draw = editing_record["draw"] if editing_record else ""
  def_num = editing_record["number"] if editing_record else ""

  prize_options = ["First", "Second", "Third", "Special", "Consolation", " "]
  def_prize = (
      editing_record["prize_type"]
      if editing_record and editing_record.get("prize_type") in prize_options
      else prize_options[0]
  )

  def_bcns = (
      editing_record["bcn_list"]
      if editing_record and "bcn_list" in editing_record
      else [""] * 9
  )
  def_serial = editing_record.get("serial", "") if editing_record else ""

  with st.form("ticket_purchase_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
      date_val = st.date_input("Date", value=def_date)
    with col2:
      draw_val = st.text_input(
          "Draw", value=def_draw, placeholder="例如: 442/26 或 442"
      )

    number_val = st.text_input(
        "Number (4 digits)", value=def_num, placeholder="例如: 7338"
    )

    prize_type = st.selectbox(
        "Prize Type",
        options=prize_options,
        index=prize_options.index(def_prize),
    )

    st.markdown("**BCN Numbers (Multi-groups):**")
    bcn_col1, bcn_col2, bcn_col3, bcn_col4, bcn_col5 = st.columns(5)
    with bcn_col1:
      bcn1 = st.text_input("BCN 1", value=def_bcns[0] if len(def_bcns) > 0 else "")
    with bcn_col2:
      bcn2 = st.text_input("BCN 2", value=def_bcns[1] if len(def_bcns) > 1 else "")
    with bcn_col3:
      bcn3 = st.text_input("BCN 3", value=def_bcns[2] if len(def_bcns) > 2 else "")
    with bcn_col4:
      bcn4 = st.text_input("BCN 4", value=def_bcns[3] if len(def_bcns) > 3 else "")
    with bcn_col5:
      bcn5 = st.text_input("BCN 5", value=def_bcns[4] if len(def_bcns) > 4 else "")

    bcn_col6, bcn_col7, bcn_col8, bcn_col9 = st.columns(4)
    with bcn_col6:
      bcn6 = st.text_input("BCN 6", value=def_bcns[5] if len(def_bcns) > 5 else "")
    with bcn_col7:
      bcn7 = st.text_input("BCN 7", value=def_bcns[6] if len(def_bcns) > 6 else "")
    with bcn_col8:
      bcn8 = st.text_input("BCN 8", value=def_bcns[7] if len(def_bcns) > 7 else "")
    with bcn_col9:
      bcn9 = st.text_input("BCN 9", value=def_bcns[8] if len(def_bcns) > 8 else "")

    serial_val = st.text_input(
        "Serial", value=def_serial, placeholder="输入 Serial 流水号..."
    )

    btn_label = (
        "🔄 Update Record"
        if st.session_state.edit_id is not None
        else "📥 Save Record"
    )
    submitted = st.form_submit_button(btn_label)

    if submitted:
      if not date_val:
        st.error("请选择 Date 日期！")
      else:
        date_str = date_val.strftime("%d/%m/%Y")

        draw_cleaned = draw_val.split("/")[0] if "/" in draw_val else draw_val
        bcn_combined = "".join(
            [bcn1, bcn2, bcn3, bcn4, bcn5, bcn6, bcn7, bcn8, bcn9]
        )
        bcn_combined_clean = "".join(bcn_combined.split())
        combine_result = (
            f"{bcn_combined_clean}{serial_val.strip()}{draw_cleaned.strip()}"
        )

        total_len = len(combine_result)
        total_score = 0

        if number_val.strip():
          for digit in number_val.strip():
            if digit.isdigit():
              total_score += combine_result.count(digit)

        percentage = (total_score / total_len * 100) if total_len > 0 else 0.0

        if st.session_state.edit_id is None:
          # 新增记录
          new_record = {
              "id": len(records) + 1,
              "date": date_str,
              "draw": draw_val,
              "number": number_val,
              "prize_type": prize_type,
              "bcn_list": [
                  bcn1,
                  bcn2,
                  bcn3,
                  bcn4,
                  bcn5,
                  bcn6,
                  bcn7,
                  bcn8,
                  bcn9,
              ],
              "serial": serial_val,
              "combine": combine_result,
              "score": total_score,
              "percentage": f"{percentage:.2f}%",
          }
          if append_single_record(new_record):
            records.append(new_record)
            st.success(
                f"云端保存成功！得分: {total_score} | Percentage:"
                f" {percentage:.2f}%"
            )
            st.rerun()
        else:
          # 更新记录
          for r in records:
            if r["id"] == st.session_state.edit_id:
              r["date"] = date_str
              r["draw"] = draw_val
              r["number"] = number_val
              r["prize_type"] = prize_type
              r["bcn_list"] = [
                  bcn1,
                  bcn2,
                  bcn3,
                  bcn4,
                  bcn5,
                  bcn6,
                  bcn7,
                  bcn8,
                  bcn9,
              ]
              r["serial"] = serial_val
              r["combine"] = combine_result
              r["score"] = total_score
              r["percentage"] = f"{percentage:.2f}%"
              break
          if save_data_all(records):
            st.session_state.edit_id = None
            st.success(f"记录 ID {st.session_state.edit_id} 云端更新成功！")
            st.rerun()

  if st.session_state.edit_id is not None:
    if st.button("❌ Cancel Edit"):
      st.session_state.edit_id = None
      st.rerun()

  st.divider()

  # 管理区
  st.subheader("⚙️ Manage Records (Edit / Delete)")
  if records:
    record_options = {
        f"ID {r['id']} | Date: {r['date']} | Draw: {r['draw']} | Num: {r['number']} ({r.get('prize_type', '')})": (
            r["id"]
        )
        for r in records
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
          if save_data_all(records):
            if st.session_state.edit_id == target_id:
              st.session_state.edit_id = None
            st.success("云端删除成功！")
            st.rerun()
  else:
    st.write("暂无任何记录可供管理。")

# ==================== TAB 2: Search 搜索窗口 ====================
with tab_search:
  st.subheader("🔍 Search & History Window")

  col_s1, col_s2 = st.columns([2, 1])
  with col_s1:
    search_query = st.text_input(
        "Search keyword (Combine / BCN / Serial)",
        value="",
        placeholder="输入关键词搜索...",
    )
  with col_s2:
    filter_num = st.text_input(
        "Filter Number", value="", placeholder="输入4位数号码筛选..."
    )

  filtered_records = records

  if search_query.strip():
    q = search_query.strip()
    filtered_records = [
        r
        for r in filtered_records
        if q in str(r.get("combine", ""))
        or q in str(r.get("number", ""))
        or any(q in str(b) for b in r.get("bcn_list", []))
        or q in str(r.get("serial", ""))
        or q.lower() in str(r.get("prize_type", "")).lower()
    ]

  if filter_num.strip():
    fn = filter_num.strip()
    filtered_records = [
        r for r in filtered_records if fn in str(r.get("number", ""))
    ]

  if filtered_records:
    table_data = []
    for r in filtered_records:
      table_data.append({
          "ID": r["id"],
          "Date": r["date"],
          "Draw": r["draw"],
          "Number": r["number"],
          "Prize": r.get("prize_type", "-"),
          "Score": r.get("score", 0),
          "Percentage": r.get("percentage", "0.00%"),
      })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
  else:
    st.info("暂无匹配的记录。")

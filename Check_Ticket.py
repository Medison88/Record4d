from datetime import datetime
import json
import os
import pandas as pd
import streamlit as st

DATA_FILE = "ticket_records.json"

# 页面配置
st.set_page_config(
    page_title="Ticket Purchase & 4D Analysis", page_icon="🎟️", layout="centered"
)


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

st.title("🎟️ Ticket Purchase & 4D Analysis")

# 初始化 Session State 用于控制编辑状态
if "edit_id" not in st.session_state:
  st.session_state.edit_id = None

# 查找当前是否在编辑某条记录
editing_record = None
if st.session_state.edit_id is not None:
  editing_record = next(
      (r for r in records if r["id"] == st.session_state.edit_id), None
  )

# ==================== 1. 输入表单区 ====================
form_title = (
    f"✏️ Edit Record (ID: {st.session_state.edit_id})"
    if editing_record
    else "➕ Ticket Purchase & Calculator"
)
st.subheader(form_title)

# 获取默认回填值
def_date = (
    datetime.strptime(editing_record["date"], "%d/%m/%Y").date()
    if editing_record and editing_record.get("date")
    else None
)
def_draw = editing_record["draw"] if editing_record else ""
def_num = editing_record["number"] if editing_record else ""

# 奖项类型选项
prize_options = ["First", "Second", "Third", "Special", "Consolation"]
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

with st.form("ticket_form", clear_on_submit=False):
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

  # 新增的奖项下拉菜单
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

      # 1. 拼接 Combine 字符串 (参与计算与存储)
      draw_cleaned = draw_val.split("/")[0] if "/" in draw_val else draw_val
      bcn_combined = "".join(
          [bcn1, bcn2, bcn3, bcn4, bcn5, bcn6, bcn7, bcn8, bcn9]
      )
      bcn_combined_clean = "".join(bcn_combined.split())
      combine_result = (
          f"{bcn_combined_clean}{serial_val.strip()}{draw_cleaned.strip()}"
      )

      # 2. 自动计算得分与 Percentage
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
        records.append(new_record)
        msg = f"记录保存成功！得分: {total_score} | Percentage: {percentage:.2f}%"
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
        msg = f"记录 ID {st.session_state.edit_id} 更新成功！"
        st.session_state.edit_id = None

      save_data(records)
      st.success(msg)
      st.rerun()

if st.session_state.edit_id is not None:
  if st.button("❌ Cancel Edit"):
    st.session_state.edit_id = None
    st.rerun()

st.divider()

# ==================== 2. Search 搜索与历史表格区 ====================
st.subheader("🔍 Search & History")

search_query = st.text_input(
    "Search by Number, BCN or Combine string",
    value="",
    placeholder="输入号码搜索...",
)

filtered_records = records
if search_query.strip():
  q = search_query.strip()
  filtered_records = [
      r
      for r in records
      if q in str(r.get("combine", ""))
      or q in str(r.get("number", ""))
      or any(q in str(b) for b in r.get("bcn_list", []))
      or q in str(r.get("serial", ""))
      or q.lower() in str(r.get("prize_type", "")).lower()
  ]

if filtered_records:
  table_data = []
  for r in filtered_records:
    table_data.append({
        "ID": r["id"],
        "Date": r["date"],
        "Draw": r["draw"],
        "Number": r["number"],
        "Prize": r.get("prize_type", "-"),  # 可选：如果在表格中也想顺便看奖项类型，可以保留此列
        "Score": r.get("score", 0),
        "Percentage": r.get("percentage", "0.00%"),
    })

  df = pd.DataFrame(table_data)
  st.dataframe(df, use_container_width=True, hide_index=True)
else:
  st.info("暂无匹配的记录。")

# ==================== 3. 管理区（支持修改与删除） ====================
with st.expander("⚙️ Manage Records (Edit / Delete)"):
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
          save_data(records)
          if st.session_state.edit_id == target_id:
            st.session_state.edit_id = None
          st.success("删除成功！")
          st.rerun()
  else:
    st.write("暂无任何记录。")

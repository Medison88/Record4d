from datetime import datetime
import json
import os
import pandas as pd
import streamlit as st

DATA_FILE = "ticket_records.json"

# 页面配置
st.set_page_config(
    page_title="Ticket Purchase & Calculator", page_icon="🎟️", layout="centered"
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

st.title("🎟️ Ticket Purchase & Red Word Calculator")

# ==================== 1. 统一的输入表单区 ====================
with st.form("ticket_form", clear_on_submit=False):
  st.subheader("Ticket Purchase & Red Word Analysis")

  col1, col2 = st.columns(2)
  with col1:
    date_val = st.date_input("Date", value=datetime.now().date())
  with col2:
    draw_val = st.text_input("Draw", value="442/26")

  number_val = st.text_input("Number (4 digits)", value="7338")

  # 长红字串输入（用于计算 Percentage）
  default_red_word = "12926006917075326404162678098141823965621793166283"
  red_word_input = st.text_area(
      "当期的长红字串 (Red Word / Password String):",
      value=default_red_word,
      height=70,
  )

  st.markdown("**BCN Numbers (Multi-groups):**")
  bcn_col1, bcn_col2, bcn_col3, bcn_col4, bcn_col5 = st.columns(5)
  with bcn_col1:
    bcn1 = st.text_input("BCN 1", value="23335")
  with bcn_col2:
    bcn2 = st.text_input("BCN 2", value="12926")
  with bcn_col3:
    bcn3 = st.text_input("BCN 3", value="00691")
  with bcn_col4:
    bcn4 = st.text_input("BCN 4", value="70753")
  with bcn_col5:
    bcn5 = st.text_input("BCN 5", value="26404")

  bcn_col6, bcn_col7, bcn_col8, bcn_col9 = st.columns(4)
  with bcn_col6:
    bcn6 = st.text_input("BCN 6", value="16267")
  with bcn_col7:
    bcn7 = st.text_input("BCN 7", value="80981")
  with bcn_col8:
    bcn8 = st.text_input("BCN 8", value="41823")
  with bcn_col9:
    bcn9 = st.text_input("BCN 9", value="96562")

  serial_val = st.text_input("Serial", value="1793166283")

  # --- 自动计算逻辑 ---
  # 1. 计算 Combine
  draw_cleaned = draw_val.split("/")[0] if "/" in draw_val else draw_val
  bcn_combined = "".join(
      [bcn1, bcn2, bcn3, bcn4, bcn5, bcn6, bcn7, bcn8, bcn9]
  )
  bcn_combined_clean = "".join(bcn_combined.split())
  combine_result = (
      f"{bcn_combined_clean}{serial_val.strip()}{draw_cleaned.strip()}"
  )

  # 2. 实时计算红字得分与 Percentage
  clean_red = "".join(red_word_input.split())
  total_len = len(clean_red)
  total_score = 0
  digit_breakdown = []
  for digit in number_val:
    if digit.isdigit():
      count = clean_red.count(digit)
      total_score += count
      digit_breakdown.append(f"数字 [{digit}] 出现 {count} 次 (得 {count} 分)")

  percentage = (total_score / total_len * 100) if total_len > 0 else 0.0

  # 界面实时预览计算结果
  st.markdown("---")
  st.markdown(f"**🔗 Combine Result Preview:** `{combine_result}`")
  st.markdown(
      f"**📊 Calculation Result:** 总字数: `{total_len}` | 号码总得分: `{total_score}` |"
      f" 中奖占比 (Percentage): **`{percentage:.2f}%`**"
  )
  st.markdown("---")

  submitted = st.form_submit_button("📥 Save Record")

  if submitted:
    date_str = date_val.strftime("%d/%m/%Y")
    new_record = {
        "id": len(records) + 1,
        "date": date_str,
        "draw": draw_val,
        "number": number_val,
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
        "total_score": total_score,
        "percentage": f"{percentage:.2f}%",
    }
    records.append(new_record)
    save_data(records)
    st.success("Record saved successfully!")
    st.rerun()

st.divider()

# ==================== 2. Search 搜索与历史表格区 ====================
st.subheader("🔍 Search Records")

search_query = st.text_input(
    "Search by Number, BCN or Combine string",
    placeholder="Enter number to filter...",
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
  ]

if filtered_records:
  table_data = []
  for r in filtered_records:
    table_data.append({
        "ID": r["id"],
        "Date": r["date"],
        "Draw": r["draw"],
        "Number": r["number"],
        "Score": r.get("total_score", "-"),
        "Percentage": r.get("percentage", "-"),
        "BCN": r["combine"],
    })

  df = pd.DataFrame(table_data)
  st.dataframe(df, use_container_width=True, hide_index=True)
else:
  st.info("No matching records found.")

# 管理/删除记录
with st.expander("⚙️ Manage Records (Delete)"):
  if records:
    del_options = {
        f"ID {r['id']} | Date: {r['date']} | Draw: {r['draw']} | Num: {r['number']}": (
            r["id"]
        )
        for r in records
    }
    selected_to_del = st.selectbox(
        "Select record to delete", options=list(del_options.keys())
    )
    if st.button("🗑️ Delete Selected Record", type="primary"):
      target_id = del_options[selected_to_del]
      records = [r for r in records if r["id"] != target_id]
      for idx, r in enumerate(records, start=1):
        r["id"] = idx
      save_data(records)
      st.success("Deleted successfully!")
      st.rerun()
  else:
    st.write("No records available.")

from datetime import datetime
import json
import os
import pandas as pd
import streamlit as st

DATA_FILE = "ticket_records.json"

# 页面配置
st.set_page_config(
    page_title="Ticket Purchase & Search App", page_icon="🎟️", layout="centered"
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

st.title("🎟️ Ticket Purchase & Search System")

# ==================== 1. Ticket Purchase 输入区域 ====================
with st.form("ticket_form", clear_on_submit=False):
  st.subheader("Ticket Purchase")

  col1, col2 = st.columns(2)
  with col1:
    date_val = st.date_input("Date", value=datetime.now().date())
  with col2:
    draw_val = st.text_input("Draw", value="442/26")

  number_val = st.text_input("Number", value="2014")

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

  # 实时计算 Combine: BCN所有数字连起来 + Serial + Draw(仅取斜杠前的数字如442)
  draw_cleaned = draw_val.split("/")[0] if "/" in draw_val else draw_val
  bcn_combined = "".join(
      [bcn1, bcn2, bcn3, bcn4, bcn5, bcn6, bcn7, bcn8, bcn9]
  )
  # 去除空格
  bcn_combined_clean = "".join(bcn_combined.split())
  combine_result = f"{bcn_combined_clean}{serial_val.strip()}{draw_cleaned.strip()}"

  st.info(f"**Combine Result Preview:** \n`{combine_result}`")

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
    }
    records.append(new_record)
    save_data(records)
    st.success("Record saved successfully!")
    st.rerun()

st.divider()

# ==================== 2. Search 搜索与历史记录区域 ====================
st.subheader("🔍 Search")

search_query = st.text_input(
    "Search by Number, BCN or Combine string",
    placeholder="Enter number to filter...",
)

# 过滤逻辑：如果在 search 框输入了数字，则模糊匹配 Combine 或 Number 或 BCN
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
  # 整理成表格展示 (对应截图格式：ID | Date | Draw | Number | BCN(Combine))
  table_data = []
  for r in filtered_records:
    table_data.append({
        "ID": r["id"],
        "Date": r["date"],
        "Draw": r["draw"],
        "Number": r["number"],
        "BCN": r["combine"],  # 表格里的 BCN 列显示拼接好的 Combine 字符串
    })

  df = pd.DataFrame(table_data)
  st.dataframe(df, use_container_width=True, hide_index=True)
else:
  st.info("No matching records found.")

# 清除所有数据或删除单条记录的管理按钮（折叠在expander中）
with st.expander("⚙️ Manage Records (Delete / Reset)"):
  if records:
    del_options = {
        f"ID {r['id']} | Date: {r['date']} | Draw: {r['draw']}": r["id"]
        for r in records
    }
    selected_to_del = st.selectbox(
        "Select record to delete", options=list(del_options.keys())
    )
    if st.button("🗑️ Delete Selected Record", type="primary"):
      target_id = del_options[selected_to_del]
      records = [r for r in records if r["id"] != target_id]
      # 重新编号
      for idx, r in enumerate(records, start=1):
        r["id"] = idx
      save_data(records)
      st.success("Deleted successfully!")
      st.rerun()
  else:
    st.write("No records available.")

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

# ==================== 1. 输入表单区（无默认值） ====================
with st.form("ticket_form", clear_on_submit=True):
  st.subheader("Ticket Purchase & Calculator")

  col1, col2 = st.columns(2)
  with col1:
    date_val = st.date_input("Date", value=None)
  with col2:
    draw_val = st.text_input("Draw", value="", placeholder="例如: 442/26 或 442")

  number_val = st.text_input("Number (4 digits)", value="", placeholder="例如: 7338")

  st.markdown("**BCN Numbers (Multi-groups):**")
  bcn_col1, bcn_col2, bcn_col3, bcn_col4, bcn_col5 = st.columns(5)
  with bcn_col1:
    bcn1 = st.text_input("BCN 1", value="")
  with bcn_col2:
    bcn2 = st.text_input("BCN 2", value="")
  with bcn_col3:
    bcn3 = st.text_input("BCN 3", value="")
  with bcn_col4:
    bcn4 = st.text_input("BCN 4", value="")
  with bcn_col5:
    bcn5 = st.text_input("BCN 5", value="")

  bcn_col6, bcn_col7, bcn_col8, bcn_col9 = st.columns(4)
  with bcn_col6:
    bcn6 = st.text_input("BCN 6", value="")
  with bcn_col7:
    bcn7 = st.text_input("BCN 7", value="")
  with bcn_col8:
    bcn8 = st.text_input("BCN 8", value="")
  with bcn_col9:
    bcn9 = st.text_input("BCN 9", value="")

  serial_val = st.text_input("Serial", value="", placeholder="输入 Serial 流水号...")

  submitted = st.form_submit_button("📥 Save Record")

  if submitted:
    if not date_val:
      st.error("请选择 Date 日期！")
    else:
      date_str = date_val.strftime("%d/%m/%Y")

      # 1. 拼接 Combine 字符串 (所有 BCN + Serial + Draw 截取数字)
      draw_cleaned = draw_val.split("/")[0] if "/" in draw_val else draw_val
      bcn_combined = "".join(
          [bcn1, bcn2, bcn3, bcn4, bcn5, bcn6, bcn7, bcn8, bcn9]
      )
      bcn_combined_clean = "".join(bcn_combined.split())
      combine_result = (
          f"{bcn_combined_clean}{serial_val.strip()}{draw_cleaned.strip()}"
      )

      # 2. 自动计算得分与 Percentage (红字串即为 Combine 字符串)
      total_len = len(combine_result)
      total_score = 0

      if number_val.strip():
        for digit in number_val.strip():
          if digit.isdigit():
            total_score += combine_result.count(digit)

      percentage = (total_score / total_len * 100) if total_len > 0 else 0.0

      # 3. 保存记录
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
          "combine": combine_result,
          "score": total_score,
          "percentage": f"{percentage:.2f}%",
      }
      records.append(new_record)
      save_data(records)
      st.success(
          f"记录保存成功！得分: {total_score} | 真实 Percentage: {percentage:.2f}%"
      )
      st.rerun()

st.divider()

# ==================== 2. Search 搜索与历史表格区 ====================
st.subheader("🔍 Search")

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
  ]

if filtered_records:
  table_data = []
  for r in filtered_records:
    table_data.append({
        "ID": r["id"],
        "Date": r["date"],
        "Draw": r["draw"],
        "Number": r["number"],
        "Score": r.get("score", 0),  # 得分
        "Percentage": r.get("percentage", "0.00%"),  # 真实占比
        # 表格中已移除 BCN / Combine 列
    })

  df = pd.DataFrame(table_data)
  st.dataframe(df, use_container_width=True, hide_index=True)
else:
  st.info("暂无匹配的记录。")

# 删除管理
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
      st.success("删除成功！")
      st.rerun()
  else:
    st.write("暂无任何记录。")

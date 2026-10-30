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

# ==================== 1. 统一的输入表单区（无默认值） ====================
with st.form("ticket_form", clear_on_submit=True):
  st.subheader("Ticket Purchase & Red Word Analysis")

  col1, col2 = st.columns(2)
  with col1:
    date_val = st.date_input("Date", value=None)
  with col2:
    draw_val = st.text_input("Draw", value="", placeholder="例如: 442/26")

  number_val = st.text_input("Number (4 digits)", value="", placeholder="例如: 7338")

  # 长红字串输入框（无默认值）
  red_word_input = st.text_area(
      "当期的长红字串 (Red Word / Password String):",
      value="",
      height=80,
      placeholder="请在此处粘贴当期长红字串...",
  )

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

  serial_val = st.text_input("Serial", value="", placeholder="输入流水号...")

  submitted = st.form_submit_button("📥 Save Record")

  if submitted:
    if not date_val:
      st.error("请选择日期！")
    else:
      date_str = date_val.strftime("%d/%m/%Y")

      # 动态计算 Combine
      draw_cleaned = draw_val.split("/")[0] if "/" in draw_val else draw_val
      bcn_combined = "".join(
          [bcn1, bcn2, bcn3, bcn4, bcn5, bcn6, bcn7, bcn8, bcn9]
      )
      bcn_combined_clean = "".join(bcn_combined.split())
      combine_result = (
          f"{bcn_combined_clean}{serial_val.strip()}{draw_cleaned.strip()}"
      )

      # 动态计算红字得分与 Percentage
      clean_red = "".join(red_word_input.split())
      total_len = len(clean_red)
      total_score = 0
      for digit in number_val:
        if digit.isdigit():
          total_score += clean_red.count(digit)

      percentage = (total_score / total_len * 100) if total_len > 0 else 0.0

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
      st.success(
          f"保存成功！总得分: {total_score} | 中奖占比: {percentage:.2f}%"
      )
      st.rerun()

st.divider()

# ==================== 2. Search 搜索与历史表格区 ====================
st.subheader("🔍 Search Records")

search_query = st.text_input(
    "Search by Number, BCN or Combine string",
    value="",
    placeholder="输入号码或关键词进行搜索...",
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
  st.info("暂无匹配的记录。")

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
      st.success("删除成功！")
      st.rerun()
  else:
    st.write("暂无任何记录。")

import json
import os
import re
from datetime import datetime
import gspread
import pandas as pd
import streamlit as st
from google.oauth2 import service_account

# 页面配置
st.set_page_config(
    page_title="Ticket Purchase & 4D Analysis", page_icon="🎟️", layout="centered"
)

# ==================== Google Sheets 云端数据库配置 (Calculate_Ticket_DB) ====================
SPREADSHEET_ID = "1j9R36vCXpSNPuQ8UuQU_k5gZm9xRPcIJ7RbN1hQrLq4"


@st.cache_resource
def init_gspread():
  try:
    if "gcp_service_account" in st.secrets:
      creds_dict = dict(st.secrets["gcp_service_account"])
      if "private_key" in creds_dict:
        pk = str(creds_dict["private_key"])
        # 强制规范化换行符
        pk = pk.replace("\\n", "\n")
        creds_dict["private_key"] = pk

      # 【终极杀招】直接在运行目录下动态写出一个标准的 credentials.json 文件
      with open("credentials.json", "w", encoding="utf-8") as f:
        json.dump(creds_dict, f, ensure_ascii=False)

      # 直接调用 gspread 原生的文件读取方法，彻底避开内存解析坑
      gc = gspread.service_account(filename="credentials.json")
      return gc
    else:
      st.error("ERROR: 未找到 gcp_service_account 密文配置！")
      return None
  except Exception as e:
    import traceback

    st.error(f"详细初始化错误: {type(e).__name__}: {e}")
    st.code(traceback.format_exc())
    st.stop()


gc = init_gspread()
try:
  sheet_4d = gc.open_by_key(SPREADSHEET_ID).sheet1
except Exception as e:
  st.error(f"连接 Google Sheets 失败: {e}")
  st.stop()

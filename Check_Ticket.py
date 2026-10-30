import re
from datetime import datetime
import json
import os
from google.oauth2 import service_account
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
    if "gcp_service_account" in st.secrets:
      creds_dict = dict(st.secrets["gcp_service_account"])
      if "private_key" in creds_dict:
        pk = str(creds_dict["private_key"])
        # 1. 规范化转义换行符
        pk = pk.replace("\\n", "\n")

        # 2. 正则精准抓取纯净 PEM 私钥，忽略末尾任何多余的引号、等号或垃圾字符
        match = re.search(
            r"(-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----)",
            pk,
        )
        if match:
          creds_dict["private_key"] = match.group(1)
        else:
          st.error("ERROR: 私钥格式不匹配，未找到有效的 BEGIN/END 私钥标记！")
          return None
    else:
      st.error("ERROR: 未找到 gcp_service_account 密文配置！")
      return None

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=scopes
    )
    gc = gspread.authorize(credentials)
    return gc
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

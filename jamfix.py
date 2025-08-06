import streamlit as st
import gspread

try:
    gc = gspread.service_account_from_dict(st.secrets["gspread_service_account"])
    
    # GANTI DENGAN URL SPREADSHEET ANDA DI SINI
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1rStEc9ROb-L7v4P4nd1J6S0jCKloC5Wf/edit"
    
    sh = gc.open_by_url(spreadsheet_url)
    
    st.success("✅ Berhasil terhubung ke Google Sheets!")
    st.write(f"Nama Spreadsheet: {sh.title}")
    
except Exception as e:
    st.error(f"❌ Gagal terhubung ke Google Sheets: {e}")

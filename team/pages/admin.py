import streamlit as st
from sea_info.screens import admin_dashboard
if st.session_state.get('role') != 'admin':
    st.error('운영자 권한이 필요합니다.')
    st.page_link('pages/home.py', label='홈으로')
else:
    admin_dashboard()

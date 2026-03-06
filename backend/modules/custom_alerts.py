# modules/custom_alerts.py
import streamlit as st

BASE_STYLE = """
background-color: #F5E8DC;
border-radius: 6px;
padding: 12px;
margin: 10px 0;
color: #3F2A1D;
"""

def custom_success(message):
    st.markdown(f"""
    <div style="{BASE_STYLE} border-left: 5px solid #BF6B3B; font-weight: bold;">
        {message}
    </div>
    """, unsafe_allow_html=True)

def custom_info(message):
    st.markdown(f"""
    <div style="{BASE_STYLE} border-left: 5px solid #D97D4A;">
        {message}
    </div>
    """, unsafe_allow_html=True)

def custom_warning(message):
    st.markdown(f"""
    <div style="{BASE_STYLE} border-left: 5px solid #D97D4A; font-weight: bold;">
        {message}
    </div>
    """, unsafe_allow_html=True)

def custom_empty(message):
    st.markdown(f"""
    <div style="{BASE_STYLE} border-left: 5px solid #D97D4A;">
        {message}
    </div>
    """, unsafe_allow_html=True)
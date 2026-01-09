import streamlit as st

def custom_success(message):
    st.markdown(f"""
    <div style="
        background-color: #F5E8DC;
        border-left: 5px solid #BF6B3B;
        border-radius: 6px;
        padding: 12px;
        margin: 10px 0;
        color: #3F2A1D;
        font-weight: bold;
    ">
    ✅ {message}
    </div>
    """, unsafe_allow_html=True)

def custom_info(message):
    st.markdown(f"""
    <div style="
        background-color: #F5E8DC;
        border-left: 5px solid #D97D4A;
        border-radius: 6px;
        padding: 12px;
        margin: 10px 0;
        color: #3F2A1D;
    ">
    ℹ️ {message}
    </div>
    """, unsafe_allow_html=True)

def custom_warning(message):
    st.markdown(f"""
    <div style="
        background-color: #F5E8DC;
        border-left: 5px solid #D97D4A;
        border-radius: 6px;
        padding: 12px;
        margin: 10px 0;
        color: #3F2A1D;
        font-weight: bold;
    ">
    ⚠️ {message}
    </div>
    """, unsafe_allow_html=True)

def custom_empty(message):
    """Օգտագործել 'դեռ չկա' տիպի հաղորդագրությունների համար"""
    st.markdown(f"""
    <div style="
        background-color: #F5E8DC;
        border-left: 5px solid #D97D4A;
        border-radius: 6px;
        padding: 12px;
        margin: 10px 0;
        color: #3F2A1D;
    ">
    ℹ️ {message}
    </div>
    """, unsafe_allow_html=True)
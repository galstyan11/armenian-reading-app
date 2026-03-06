# app.py
import streamlit as st
import os

from modules.auth_file import show_auth_page
from modules.books_csv import load_books
from modules.ui_components import show_header, show_main_tabs
from modules.db import init_database

if "db_initialized" not in st.session_state:
    print("Performing one-time database initialization...")
    success = init_database()
    if success:
        st.session_state.db_initialized = True
        print("Database schema initialized successfully.")
    else:
        st.error("Database initialization failed — check logs.")
        st.stop()  # optional: stop app if DB setup failed

st.set_page_config(
    page_title="Կարդա ինձ հետ",
    page_icon="assets/sticker.png",
    layout="wide"
)

# Load custom CSS
try:
    with open("style.css", "r", encoding="utf-8") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("style.css file not found!")

def main():
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'link_status' not in st.session_state:
        st.session_state.link_status = {}

    books_df = load_books()

    if st.session_state.user is None:
        show_auth_page(books_df)
    else:
        show_header(st.session_state.user)
        st.markdown("---")
        show_main_tabs(books_df, st.session_state.user)

if __name__ == "__main__":
    main()
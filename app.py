import streamlit as st
import pandas as pd
from modules.auth_file import show_auth_page, get_current_user, logout
from modules.books_csv import load_books, show_all_books, show_recommendations, show_reading_plan
from modules.users_file import show_statistics, show_reminders, show_settings
from modules.creative_file import show_creative_works
from modules.utils import get_reading_time_recommendation, calculate_reading_plan

def show_main_app(books_df):
    user = st.session_state.user
    
    # Header with user info and logout
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title(f"📖 Բարի Գալուստ, {user['username']}!")
    with col3:
        if st.button("🚪 Դուրս Գալ"):
            logout()
            st.rerun()
    
    st.markdown("---")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📚 Բոլոր Գրքերը", 
        "💡 Առաջարկներ", 
        "📅 Ընթերցման Պլան",
        "📊 Իմ Վիճակագրությունը",
        "🎨 Ստեղծագործություններ",
        "⏰ Հիշեցումներ",
        "⚙️ Կարգավորումներ"
    ])
    
    with tab1:
        show_all_books(books_df, user)
    
    with tab2:
        show_recommendations(books_df, user)
    
    with tab3:
        show_reading_plan(books_df, user)
    
    with tab4:
        show_statistics(user)
    
    with tab5:
        show_creative_works(user)
    
    with tab6:
        show_reminders(user)
    
    with tab7:
        show_settings(user, books_df)

def main():
    st.set_page_config(
        page_title="📖 Ընթերցանության Հավելված", 
        page_icon="📚",
        layout="wide"
    )
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'link_status' not in st.session_state:
        st.session_state.link_status = {}
    
    # Load books data
    books_df = load_books()
    
    # Navigation
    if st.session_state.user is None:
        show_auth_page(books_df)
    else:
        show_main_app(books_df)

if __name__ == "__main__":
    main()

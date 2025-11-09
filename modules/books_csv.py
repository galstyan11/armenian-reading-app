import streamlit as st
import pandas as pd
import requests
from modules.utils import check_link_availability, calculate_reading_plan, get_reading_time_recommendation, get_advanced_recommendations
from modules.data_file import add_reading_session, add_book_comment, get_book_comments, update_reading_speed
from datetime import datetime, timedelta

@st.cache_data
def load_books():
    """Load books from GitHub CSV"""
    url = "https://raw.githubusercontent.com/galstyan11/reading-app/main/reading_app_db.csv"
    
    try:
        df = pd.read_csv(url, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        st.success(f"✅ Բեռնված է {len(df)} գիրք")
        return df
    except Exception as e:
        st.error(f"Error loading books: {e}")
        return pd.DataFrame()

def show_all_books(books_df, user):
    st.subheader("📚 Գրքերի Ամբողջական Ցանկ")
    
    if books_df.empty:
        st.error("❉ Չհաջողվեց բեռնել գրքերը")
        return
    
    # Search and filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search_title = st.text_input("🔍 Որոնել ըստ վերնագրի")
    with col2:
        search_author = st.text_input("🔍 Որոնել ըստ հեղինակի")
    with col3:
        selected_genre = st.selectbox("Ընտրել ժանր", ["Բոլորը"] + books_df['genre'].unique().tolist())
    
    # Filter books
    filtered_books = books_df.copy()
    if search_title:
        filtered_books = filtered_books[filtered_books['title'].str.contains(search_title, case=False, na=False)]
    if search_author:
        filtered_books = filtered_books[filtered_books['author'].str.contains(search_author, case=False, na=False)]
    if selected_genre != "Բոլորը":
        filtered_books = filtered_books[filtered_books['genre'] == selected_genre]
    
    # Display books
    for idx, (_, book) in enumerate(filtered_books.iterrows()):
        with st.expander(f"📗 {book['title']} - {book['author']}"):
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.write(f"**ժանր:** {book['genre']}")
                st.write(f"**Էջեր:** {book['pages']}")
                st.write(f"**Լեզու:** {book['language']}")
                
                if pd.notna(book['description']) and book['description']:
                    st.write(f"**Նկարագրություն:** {book['description']}")
                
                # PDF Link Section
                st.write("---")
                st.write("**📖 Կարդալ Գիրքը**")
                
                if pd.notna(book['link']) and book['link']:
                    # Check link status if not already checked
                    if book['id'] not in st.session_state.link_status:
                        st.session_state.link_status[book['id']] = check_link_availability(book['link'])
                    
                    link_status = st.session_state.link_status[book['id']]
                    
                    if link_status:
                        st.markdown(f"""
                        <div style='background-color: #e8f5e8; padding: 10px; border-radius: 5px; border: 1px solid #4CAF50;'>
                        <h4 style='color: #2E7D32; margin: 0;'>📚 Գիրքը Հասանելի է Առցանց</h4>
                        <a href='{book['link']}' target='_blank' style='
                            display: inline-block;
                            background-color: #4CAF50;
                            color: white;
                            padding: 10px 20px;
                            text-align: center;
                            text-decoration: none;
                            border-radius: 5px;
                            margin: 10px 0;
                            font-weight: bold;
                        '>📖 Բացել Գիրքը</a>
                        <p style='margin: 5px 0; color: #555;'>Կարդալու համար սեղմեք <<Բացել գիրքը>> </p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("❌ PDF հղումը չի աշխատում")
                        st.markdown(f"[🔗 Փորձել արտաքին հղումը]({book['link']})")
                else:
                    st.warning("⚠️ Այս գրքի համար PDF հղում չկա")
                
                # Reading session tracking
                # Updated Reading session tracking
                st.write("---")
                st.write("📖 Ընթերցման Հետևում")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    pages_read = st.number_input(
                        "Կարդացած էջեր",
                        min_value=0,
                        max_value=book['pages'],
                        value=0,
                        key=f"pages_{book['id']}_{idx}"
                    )
                
                with col2:
                    start_time = st.time_input(
                        "Ընթերցման սկիզբ",
                        value=None,
                        key=f"start_{book['id']}_{idx}"
                    )
                
                with col3:
                    end_time = st.time_input(
                        "Ընթերցման ավարտ", 
                        value=None,
                        key=f"end_{book['id']}_{idx}"
                    )
                
                # Calculate duration automatically
                duration_minutes = 0
                if start_time and end_time:
                    # Calculate time difference in minutes
                    start_dt = datetime.combine(datetime.today(), start_time)
                    end_dt = datetime.combine(datetime.today(), end_time)
                    
                    if end_dt < start_dt:
                        # If end time is next day (e.g., started at 23:00, ended at 01:00)
                        end_dt = end_dt + timedelta(days=1)
                    
                    duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
                    
                    # Display calculated duration
                    if duration_minutes > 0:
                        st.info(f"⏱️ Ընթերցման ժամանակ: **{duration_minutes} րոպե**")
                
                if st.button("💾 Պահպանել Ընթերցումը", key=f"save_{book['id']}_{idx}"):
                    if pages_read > 0 and start_time and end_time and duration_minutes > 0:
                        success = add_reading_session(
                            user['id'], 
                            book['id'], 
                            pages_read, 
                            duration_minutes, 
                            book['title']
                        )
                        if success:
                            st.success("📊 Ընթերցման տվյալները պահպանված են!")
                            
                            # Update user's reading speed automatically
                            from modules.data import update_reading_speed
                            update_reading_speed(user['id'])
                    else:
                        st.error("❌ Խնդրում եմ լրացրեք բոլոր դաշտերը ճիշտ")
            
            with col2:
                # Book metrics and info
                st.write("**📊 Գրքի Մասին**")
                
                # Reading time estimation
                total_minutes = book['pages'] // user['reading_speed']
                hours = total_minutes // 60
                minutes = total_minutes % 60
                
                if hours > 0:
                    st.metric("⏱️ Ընդհանուր Ժամանակ", f"{hours}ժ {minutes}ր")
                else:
                    st.metric("⏱️ Ընդհանուր Ժամանակ", f"{minutes} րոպե")
                
                # Daily reading plan
                daily_pages, daily_minutes = calculate_reading_plan(
                    book['pages'], user['reading_speed'], user['daily_reading_time'], 30
                )
                st.metric("📅 Օրական Պլան", f"{daily_pages} էջ")
                
                # Reading time recommendation based on genre
                recommendation = get_reading_time_recommendation(book['genre'])
                st.info(f"{recommendation['icon']} **Առաջարկվող ընթերցման ժամանակ:** {recommendation['time']}")
                
                # Additional book info
                if pd.notna(book['publication_year']):
                    st.write(f"**📅 Հրատարակման Տարի:** {int(book['publication_year'])}")
            
            # Comments Section for the book
            st.write("---")
            show_book_comments_section(book['id'], user, f"all_books_{book['id']}_{idx}")

def show_book_comments_section(book_id, user, unique_suffix=""):
    """Show comments section for a specific book"""
    st.subheader("💬 Մեկնաբանություններ")
    
    # Get existing comments
    comments = get_book_comments(book_id)
    
    # Display existing comments
    if comments:
        st.write("### 📝 Գրքի Մասին Մեկնաբանություններ")
        for comment in comments:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**👤 {comment['username']}**")
                    st.write(comment['comment_text'])
                    if comment['rating']:
                        st.write(f"⭐ Վարկանիշ: {comment['rating']}/5")
                with col2:
                    st.write(f"_{comment['created_at']}_")
                st.markdown("---")
    else:
        st.info("📝 Մեկնաբանություններ դեռ չկան։ Դուք կարող եք լինել առաջինը։")
    
    # Add new comment form
    st.write("### ✍️ Ավելացնել Նոր Մեկնաբանություն")
    with st.form(key=f"comment_form_{book_id}_{unique_suffix}"):
        new_comment = st.text_area("Ձեր մեկնաբանությունը", height=100, 
                                 placeholder="Կիսեք ձեր կարծիքը գրքի, հերոսների կամ սյուժեի վերաբերյալ...",
                                 key=f"comment_text_{book_id}_{unique_suffix}")
        rating = st.slider("Վարկանիշ", 1, 5, 3, 
                          help="1 - Շատ թույլ, 5 - Գերազանց",
                          key=f"rating_{book_id}_{unique_suffix}")
        
        submit_comment = st.form_submit_button("📤 Ուղարկել")
        
        if submit_comment and new_comment.strip():
            success = add_book_comment(user['id'], book_id, new_comment.strip(), rating, user['username'])
            if success:
                st.success("✅ Ձեր մեկնաբանությունը հաջողությամբ ավելացվել է!")
                st.rerun()
            else:
                st.error("❌ Չհաջողվեց ավելացնել մեկնաբանությունը")

def show_recommendations(books_df, user):
    st.subheader("💡 Անհատականացված Առաջարկներ")
    
    if books_df.empty:
        st.error("❉ Չհաջողվեց բեռնել գրքերը")
        return
    
    # User preferences for recommendations
    user_preferences = {
        'preferred_genres': user['preferred_genres'] if user['preferred_genres'] else [],
        'reading_speed': user['reading_speed'],
        'daily_reading_time': user['daily_reading_time'],
        'preferred_language': user.get('preferred_language', 'Հայերեն'),
        'preferred_page_range': [50, 400]
    }
    
    recommendations = get_advanced_recommendations(books_df, user_preferences)
    
    if recommendations:
        st.success(f"✅ Գտնվել է {len(recommendations)} առաջարկվող գիրք")
        
        for idx, book in enumerate(recommendations):
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"### {book['title']}")
                    st.write(f"**Հեղինակ:** {book['author']}")
                    st.write(f"**ժանր:** {book['genre']} • **Էջեր:** {book['pages']}")
                    st.write(f"**Լեզու:** {book['language']}")
                    
                    # Reading time recommendation
                    recommendation = get_reading_time_recommendation(book['genre'])
                    st.success(f"**⏰ Ընթերցման առաջարկ:** {recommendation['icon']} {recommendation['time']}")
                    st.write(f"*{recommendation['reason']}*")
                    
                    if pd.notna(book['description']) and book['description']:
                        with st.expander("📖 Նկարագրություն"):
                            st.write(book['description'])
                    
                    # PDF Link in recommendations too
                    if pd.notna(book['link']) and book['link']:
                        # Check link status if not already checked
                        if book['id'] not in st.session_state.link_status:
                            st.session_state.link_status[book['id']] = check_link_availability(book['link'])
                        
                        link_status = st.session_state.link_status[book['id']]
                        
                        if link_status:
                            st.markdown(f"""
                            <a href='{book['link']}' target='_blank' style='
                                display: inline-block;
                                background-color: #2196F3;
                                color: white;
                                padding: 8px 16px;
                                text-align: center;
                                text-decoration: none;
                                border-radius: 4px;
                                margin: 5px 0;
                                font-weight: bold;
                            '>📖 Կարդալ Այս Գիրքը</a>
                            """, unsafe_allow_html=True)
                
                with col2:
                    # Reading time estimation
                    total_minutes = book['pages'] // user['reading_speed']
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    
                    if hours > 0:
                        st.metric("⏱️ Ընդհանուր ժամանակ", f"{hours}ժ {minutes}ր")
                    else:
                        st.metric("⏱️ Ընդհանուր ժամանակ", f"{minutes} րոպե")
                    
                    daily_pages, daily_minutes = calculate_reading_plan(
                        book['pages'], user['reading_speed'], user['daily_reading_time'], 30
                    )
                    st.metric("📅 Օրական պլան", f"{daily_pages} էջ")
                
                # Comments section for recommended books too
                show_book_comments_section(book['id'], user, f"rec_{book['id']}_{idx}")
                
                st.markdown("---")
    else:
        st.info("ℹ️ Չգտնվեցին առաջարկվող գրքեր։ Ստուգեք ձեր նախընտրությունները կարգավորումներում։")

def show_reading_plan(books_df, user):
    st.subheader("📅 Ընթերցման Պլանավորում")
    
    if books_df.empty:
        st.error("❉ Չհաջողվեց բեռնել գրքերը")
        return
    
    selected_book = st.selectbox(
        "Ընտրեք գիրք պլանավորման համար",
        options=books_df['title'].tolist(),
        index=0
    )
    
    book_info = books_df[books_df['title'] == selected_book].iloc[0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Գիրք:** {book_info['title']}")
        st.write(f"**Հեղինակ:** {book_info['author']}")
        st.write(f"**Էջեր:** {book_info['pages']}")
        st.write(f"**ժանր:** {book_info['genre']}")
        
        # Reading time recommendation
        recommendation = get_reading_time_recommendation(book_info['genre'])
        st.info(f"**⏰ Ընթերցման առաջարկ:** {recommendation['icon']} {recommendation['time']}")
        st.write(f"*{recommendation['reason']}*")
        
        # PDF Link in reading plan section too
        if pd.notna(book_info['link']) and book_info['link']:
            # Check link status if not already checked
            if book_info['id'] not in st.session_state.link_status:
                st.session_state.link_status[book_info['id']] = check_link_availability(book_info['link'])
            
            link_status = st.session_state.link_status[book_info['id']]
            
            if link_status:
                st.markdown(f"""
                <a href='{book_info['link']}' target='_blank' style='
                    display: inline-block;
                    background-color: #FF9800;
                    color: white;
                    padding: 8px 16px;
                    text-align: center;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 10px 0;
                    font-weight: bold;
                '>📖 Բացել Գիրքը Պլանավորման համար</a>
                """, unsafe_allow_html=True)
    
    with col2:
        target_days = st.number_input(
            "🎯 Քանի օրում ցանկանում եք ավարտել գիրքը?",
            min_value=1,
            max_value=365,
            value=min(30, max(1, book_info['pages'] // (user['reading_speed'] * user['daily_reading_time'])))
        )
        
        if book_info['pages'] > 0:
            daily_pages, daily_minutes = calculate_reading_plan(
                book_info['pages'], user['reading_speed'], user['daily_reading_time'], target_days
            )
            
            if daily_pages > 0:
                st.success(f"**📅 Օրական պլան:** {daily_pages} էջ")
                st.success(f"**⏰ Օրական ժամանակ:** {daily_minutes} րոպե")
                
                # Progress tracking
                total_reading_time = book_info['pages'] // user['reading_speed']
                st.info(f"**Ընդհանուր ընթերցման ժամանակ:** {total_reading_time} րոպե")
                
                # Weekly plan
                st.subheader("📅 Շաբաթական Պլան")
                weekly_pages = daily_pages * 7
                st.write(f"**Շաբաթական ընթերցում:** {weekly_pages} էջ")
                st.write(f"**Շաբաթական ժամանակ:** {daily_minutes * 7} րոպե")
                
                # Check feasibility
                if daily_minutes > user['daily_reading_time']:
                    st.warning("⚠️ Օրական պլանը գերազանցում է ձեր նախընտրած ժամանակը")
                else:
                    st.success("✅ Պլանը իրագործելի է ձեր նախընտրած ժամանակում")
            else:
                st.error("❌ Չհաջողվեց հաշվարկել պլանը")
        else:
            st.warning("⚠️ Գրքի էջերի քանակը վավեր չէ")

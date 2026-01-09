# modules/books_csv.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from modules.utils import check_link_availability, calculate_reading_plan, get_reading_time_recommendation, get_advanced_recommendations
from modules.data_file import add_reading_session, add_book_comment, get_book_comments, calculate_reading_speed, update_reading_speed
from modules.custom_alerts import custom_success, custom_info, custom_warning, custom_empty


@st.cache_data
def load_books():
    """Load books from GitHub CSV"""
    url = "https://raw.githubusercontent.com/galstyan11/armenian-reading-app/refs/heads/main/reading_app_db.csv"
    try:
        df = pd.read_csv(url, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading books: {e}")
        return pd.DataFrame()


def show_book_comments_section(book_id, user, unique_suffix=""):
    st.subheader("💬 Մեկնաբանություններ")
    
    comments = get_book_comments(book_id)
    
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
                    try:
                        comment_dt = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                        st.write(f"_{comment_dt.strftime('%Y-%m-%d %H:%M')}_")
                    except:
                        st.write(f"_{comment['created_at']}_")
                st.markdown("---")
    else:
        custom_empty("📝 Մեկնաբանություններ դեռ չկան։ Դուք կարող եք լինել առաջինը։")
    
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
                custom_success("✅ Ձեր մեկնաբանությունը հաջողությամբ ավելացվել է!")
                st.rerun()
            else:
                st.error("❌ Չհաջողվեց ավելացնել մեկնաբանությունը")


def show_all_books(books_df, user):
    st.subheader("📚 Գրքերի Ամբողջական Ցանկ")
    
    if books_df.empty:
        st.error("❉ Չհաջողվեց բեռնել գրքերը")
        return
    
    # Search & filter (your existing code)
    col1, col2, col3 = st.columns(3)
    with col1:
        search_title = st.text_input("🔍 Որոնել ըստ վերնագրի")
    with col2:
        search_author = st.text_input("🔍 Որոնել ըստ հեղինակի")
    with col3:
        selected_genre = st.selectbox("Ընտրել ժանր", ["Բոլորը"] + books_df['genre'].unique().tolist())
    
    filtered_books = books_df.copy()
    if search_title:
        filtered_books = filtered_books[filtered_books['title'].str.contains(search_title, case=False, na=False)]
    if search_author:
        filtered_books = filtered_books[filtered_books['author'].str.contains(search_author, case=False, na=False)]
    if selected_genre != "Բոլորը":
        filtered_books = filtered_books[filtered_books['genre'] == selected_genre]
    
    # ────────────── PAGINATION / LOAD MORE ──────────────
    ITEMS_PER_PAGE = 5
    
    # Initialize session state for current page
    if 'book_page' not in st.session_state:
        st.session_state.book_page = 0
    
    # Calculate total pages
    total_items = len(filtered_books)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    # Get current page slice
    start_idx = st.session_state.book_page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_books = filtered_books.iloc[start_idx:end_idx]
    
    # Show books on current page
    for idx, (_, book) in enumerate(page_books.iterrows()):
        with st.expander(f"📗 {book['title']} - {book['author']}"):
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.write(f"**Ժանր:** {book['genre']}")
                st.write(f"**Էջեր:** {book['pages']}")
                st.write(f"**Լեզու:** {book['language']}")
                
                if pd.notna(book['publication_year']):
                    st.write(f"**Հրատարակման տարեթիվ:** {int(book['publication_year'])}")

                if pd.notna(book['description']) and book['description'].strip():
                    st.write(f"**Նկարագրություն:** {book['description']}")
                
                st.write("---")
                st.write("**📖 Կարդալ Գիրքը**")
                
                if pd.notna(book['link']) and book['link'].strip():
                    if book['id'] not in st.session_state.link_status:
                        st.session_state.link_status[book['id']] = check_link_availability(book['link'])
                    link_status = st.session_state.link_status[book['id']]
                    
                    if link_status:
                        st.markdown("<p style='color: #8B4513; font-size: 18px; text-align: center; font-weight: bold; margin: 20px 0;'>📚 Գիրքը հասանելի է առցանց</p>", unsafe_allow_html=True)
                        st.link_button(
                            "📖 Բացել Գիրքը",
                            book['link'],
                            use_container_width=True,
                            type="primary"
                        )
                    else:
                        st.error("❌ PDF հղումը չի աշխատում")
                        st.markdown(f"[🔗 Փորձել արտաքին հղումը]({book['link']})")
                else:
                    custom_warning("⚠️ Այս գրքի համար PDF հղում չկա")
                
                st.write("---")
                st.write("📖 Ընթերցման Հետևում")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    pages_read = st.number_input("Կարդացած էջեր", min_value=0, max_value=int(book['pages']), value=0, key=f"pages_{book['id']}_{idx}")
                with col2:
                    start_time = st.time_input("Ընթերցման սկիզբ", value=None, key=f"start_{book['id']}_{idx}")
                with col3:
                    end_time = st.time_input("Ընթերցման ավարտ", value=None, key=f"end_{book['id']}_{idx}")
                
                duration_minutes = 0
                if start_time and end_time:
                    start_dt = datetime.combine(datetime.today(), start_time)
                    end_dt = datetime.combine(datetime.today(), end_time)
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
                    if duration_minutes > 0:
                        custom_info(f"⏱️ Ընթերցման ժամանակ: **{duration_minutes} րոպե**")
                
                if st.button("💾 Պահպանել Ընթերցումը", key=f"save_{book['id']}_{idx}"):
                    if pages_read > 0 and start_time and end_time and duration_minutes > 0:
                        success = add_reading_session(user['id'], book['id'], pages_read, duration_minutes, book['title'])
                        if success:
                            custom_success("📊 Ընթերցման տվյալները պահպանված են!")
                            update_reading_speed(user['id'])
                    else:
                        st.error("❌ Խնդրում եմ լրացրեք բոլոր դաշտերը ճիշտ")
            
            with col2:
                pass  # Ջնջված է — ոչինչ չի ցուցադրվում
            pass
    
    # Load more / pagination controls
    st.markdown("---")
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    
    with col_mid:
        st.write(f"Ցուցադրվում է {start_idx + 1}–{min(end_idx, total_items)} / {total_items} գիրք")
        
        cols = st.columns(3)
        with cols[0]:
            if st.session_state.book_page > 0:
                if st.button("← Նախորդ էջ", use_container_width=True):
                    st.session_state.book_page -= 1
                    st.rerun()
        
        with cols[1]:
            st.write(f"Էջ {st.session_state.book_page + 1} / {max(1, total_pages)}")
        
        with cols[2]:
            if end_idx < total_items:
                if st.button("Հաջորդ էջ →", use_container_width=True):
                    st.session_state.book_page += 1
                    st.rerun()


def show_recommendations(books_df, user):
    st.subheader("💡 Անհատականացված Առաջարկներ")
    
    if books_df.empty:
        st.error("❉ Չհաջողվեց բեռնել գրքերը")
        return
    
    user_preferences = {
        'preferred_genres': user['preferred_genres'] if user['preferred_genres'] else [],
        'reading_speed': user['reading_speed'],
        'daily_reading_time': user['daily_reading_time'],
        'preferred_language': user.get('preferred_language', 'Հայերեն'),
        'age': user.get('age'),
    }
    
    # Safe speed handling for scoring only (no plan display)
    effective_speed = user_preferences.get('reading_speed')
    if effective_speed is None or effective_speed <= 0:
        effective_speed = 2.0  # fallback only for internal scoring
    
    recommendations = get_advanced_recommendations(books_df, user_preferences)
    
    if recommendations:
        custom_success(f"Գտնվել է {len(recommendations)} առաջարկվող գիրք")
        
        for idx, book in enumerate(recommendations):
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"### {book['title']}")
                    st.write(f"**Հեղինակ:** {book['author']}")
                    st.write(f"**Ժանր:** {book['genre']}")
                    st.write(f"**Էջեր:** {book['pages']}")
                    st.write(f"**Լեզու:** {book['language']}")
                    
                    recommendation = get_reading_time_recommendation(book['genre'])
                    custom_success(f"**⏰ Ընթերցման առաջարկ:** {recommendation['icon']} {recommendation['time']}")
                    st.write(f"*{recommendation['reason']}*")
                    
                    if pd.notna(book['link']) and book['link'].strip():
                        if book['id'] not in st.session_state.link_status:
                            st.session_state.link_status[book['id']] = check_link_availability(book['link'])
                        
                        link_status = st.session_state.link_status[book['id']]
                        
                        if link_status:
                            st.markdown("<p style='color: #8B4513; font-size: 18px; text-align: center; font-weight: bold; margin: 20px 0;'>📚 Գիրքը հասանելի է առցանց</p>", unsafe_allow_html=True)
                            st.link_button(
                                "📖 Կարդալ Այս Գիրքը",
                                book['link'],
                                use_container_width=True,
                                type="primary"
                            )
                    
                    if pd.notna(book['description']) and book['description'].strip():
                        with st.expander("📖 Նկարագրություն"):
                            st.write(book['description'])
                    
                    with st.expander("💬 Մեկնաբանություններ"):
                        show_book_comments_section(book['id'], user, f"rec_{book['id']}_{idx}")
                
                with col2:
                    # No plan/time metrics in recommendations anymore
                    st.caption("Անհատական պլանը հասանելի է «Ընթերցման Պլան» բաժնում")
                
                st.markdown("---")
    else:
        custom_info("ℹ️ Չգտնվեցին առաջարկվող գրքեր։ Ստուգեք ձեր նախընտրությունները կարգավորումներում։")


def show_reading_plan(books_df, user):
    st.subheader("📅 Ընթերցման Պլանավորում")
    
    if books_df.empty:
        st.error("❉ Չհաջողվեց բեռնել գրքերը")
        return
    
    selected_book = st.selectbox("Ընտրեք գիրք պլանավորման համար", options=books_df['title'].tolist(), index=0)
    book_info = books_df[books_df['title'] == selected_book].iloc[0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Գիրք:** {book_info['title']}")
        st.write(f"**Հեղինակ:** {book_info['author']}")
        st.write(f"**Էջեր:** {book_info['pages']}")
        st.write(f"**Ժանր:** {book_info['genre']}")
        
        recommendation = get_reading_time_recommendation(book_info['genre'])
        custom_info(f"**⏰ Ընթերցման առաջարկ:** {recommendation['icon']} {recommendation['time']}")
        st.write(f"*{recommendation['reason']}*")
        
        if pd.notna(book_info['link']) and book_info['link'].strip():
            if book_info['id'] not in st.session_state.link_status:
                st.session_state.link_status[book_info['id']] = check_link_availability(book_info['link'])
            
            link_status = st.session_state.link_status[book_info['id']]
            
            if link_status:
                st.markdown("<p style='color: #8B4513; font-size: 18px; text-align: center; font-weight: bold; margin: 20px 0;'>📚 Գիրքը հասանելի է առցանց</p>", unsafe_allow_html=True)
                st.link_button(
                    "📖 Բացել Գիրքը Պլանավորման Համար",
                    book_info['link'],
                    use_container_width=True,
                    type="primary"
                )
    
    with col2:
        pages = int(book_info['pages'])
        
        reading_speed = user.get('reading_speed')
        
        if reading_speed is None or reading_speed <= 0:
            custom_info("📝 Պլանավորումը հասանելի կլինի առաջին ընթերցումից հետո")
            st.caption("Գրանցեք Ձեր ընթերցումը՝ անհատական պլան ստանալու համար")
            return
        
        daily_time = int(user.get('daily_reading_time', 30))
        
        daily_pages_possible = reading_speed * daily_time
        suggested_days = max(1, pages // int(daily_pages_possible) if daily_pages_possible > 0 else 30)
        
        default_days = min(30, suggested_days)
        
        target_days = st.number_input(
            "🎯 Քանի օրում ցանկանում եք ավարտել գիրքը?",
            min_value=1,
            max_value=365,
            value=default_days,
            step=1
        )
        
        if pages > 0:
            daily_pages, daily_minutes = calculate_reading_plan(pages, reading_speed, daily_time, target_days)
            
            if daily_pages > 0:
                custom_success(f"**📅 Օրական պլան:** {daily_pages} էջ")
                custom_success(f"**⏰ Օրական ժամանակ:** {daily_minutes} րոպե")
                
                total_reading_time = pages / reading_speed
                custom_info(f"**Ընդհանուր ընթերցման ժամանակ:** {int(total_reading_time)} րոպե")
                
                st.subheader("📅 Շաբաթական Պլան")
                weekly_pages = daily_pages * 7
                st.write(f"**Շաբաթական ընթերցում:** {weekly_pages} էջ")
                st.write(f"**Շաբաթական ժամանակ:** {daily_minutes * 7} րոպե")
                
                if daily_minutes > daily_time:
                    custom_warning("⚠️ Օրական պլանը գերազանցում է Ձեր նախընտրած ժամանակը")
                else:
                    custom_success("✅ Պլանը իրագործելի է Ձեր նախընտրած ժամանակում")
            else:
                st.error("❌ Չհաջողվեց հաշվարկել պլանը")
        else:
            custom_warning("⚠️ Գրքի էջերի քանակը վավեր չէ")
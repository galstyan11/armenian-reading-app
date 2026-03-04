# modules/books_csv.py
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta

from modules.utils import (
    check_link_availability,
    calculate_reading_plan,
    get_reading_time_recommendation,
    get_advanced_recommendations
)
from modules.data_file import (
    add_reading_session,
    add_book_comment,
    get_book_comments,
    calculate_reading_speed,
    update_reading_speed,
    query
)

from modules.custom_alerts import (
    custom_success,
    custom_info,
    custom_warning,
    custom_empty
)

from modules.time_utils import format_armenia_datetime

# @st.cache_data(ttl=1800)  # cache 30 րոպե
def load_books():
    """Գրքերը բեռնում է MySQL books աղյուսակից"""
    try:
        rows = query(                           # ← առանց modules.db.
            """
            SELECT 
                id, title, author, type, genre, pages,
                language, publication_year, link, description
            FROM books
            ORDER BY CAST(id AS UNSIGNED)
            """, 
            fetch=True
        )
        
        if not rows:
            st.warning("Տվյալների բազայում գրքեր չկան")
            return pd.DataFrame()
            
        df = pd.DataFrame(rows)
        
        # Տիպերի կարգավորումներ (նույնը, ինչ նախկինում)
        df['id'] = df['id'].astype(str).str.strip()
        df['title'] = df['title'].astype(str).str.strip()
        df['author'] = df['author'].astype(str).str.strip().replace(['', 'None', 'nan'], None)
        df['type']   = df['type'].astype(str).str.strip().replace(['', 'None', 'nan'], None)
        df['genre']  = df['genre'].astype(str).str.strip().replace(['', 'None', 'nan'], pd.NA)
        df['language'] = df['language'].astype(str).str.strip().replace(['', 'None', 'nan'], None)
        df['link']   = df['link'].astype(str).str.strip().replace(['', 'None', 'nan'], None)
        df['description'] = df['description'].astype(str).str.strip().replace(['', 'None', 'nan'], None)
        
        for col in ['pages', 'publication_year']:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            
        return df
        
    except Exception as e:
        st.error(f"Գրքերի բեռնման սխալ տվյալների բազայից: {str(e)}")
        return pd.DataFrame()

def show_book_comments_section(book_id, user, unique_suffix=""):
    st.subheader("Մեկնաբանություններ")

    comments = get_book_comments(book_id)
    comments = sorted(comments, key=lambda c: c['created_at'], reverse=True)

    if comments:
        for comment in comments:
            with st.container():
                col1, col2 = st.columns([5, 2])   # wider left column
                with col1:
                    st.markdown(f"**{comment['username']}**")
                    st.write(comment['comment_text'])
                    if comment.get('rating'):
                        st.caption(f"Վարկանիշ: {comment['rating']}/5")
                with col2:
                    st.caption(format_armenia_datetime(comment['created_at']))
                st.markdown("---")
    else:
        custom_empty("Մեկնաբանություններ դեռ չկան։ Դուք կարող եք լինել առաջինը։")

    st.write("### Ավելացնել Նոր Մեկնաբանություն")
    with st.form(key=f"comment_form_{book_id}_{unique_suffix}", clear_on_submit=True):
        new_comment = st.text_area(
            "Ձեր մեկնաբանությունը",
            height=100,
            placeholder="Կիսեք ձեր կարծիքը գրքի, հերոսների կամ սյուժեի վերաբերյոն...",
            key=f"comment_text_{book_id}_{unique_suffix}"
        )
        
        # Rating-ը միշտ ցուցադրվում է (պարտադիր չէ)
        rating = st.slider(
            "Վարկանիշ (1–5) — ընտրովի",
            min_value=1,
            max_value=5,
            value=3,                    # default
            step=1,
            help="1 - Շատ թույլ, 5 - Գերազանց",
            key=f"rating_{book_id}_{unique_suffix}"
        )

        submit_comment = st.form_submit_button("Ուղարկել")

        if submit_comment:
            cleaned_comment = new_comment.strip()
            if not cleaned_comment:
                st.warning("Մեկնաբանությունը չի կարող դատարկ լինել")
            else:
                # rating-ը միշտ ուղարկվում է, բայց եթե օգտատերը չի փոխել default-ը՝ կարող ես համարել որպես "չի գնահատել"
                # կամ պարզապես միշտ պահպանել այն, ինչ ընտրել է
                success = add_book_comment(
                    book_id,
                    user['username'],
                    cleaned_comment,
                    rating   # միշտ ուղարկում ենք (1–5)
                )
                if success:
                    custom_success("Ձեր մեկնաբանությունը հաջողությամբ ավելացվել է!")
                    st.rerun()
                else:
                    st.error("Չհաջողվեց ավելացնել մեկնաբանությունը")
                    
def show_all_books(books_df, user):
    st.subheader("Գրքերի Ամբողջական Ցանկ")

    if books_df.empty:
        st.error("Չհաջողվեց բեռնել գրքերը")
        return

    # Search & filter
    col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1.5])

    with col1:
        search_title = st.text_input("🔍 Որոնել ըստ վերնագրի", placeholder="Մուտքագրեք վերնագիրը...")
    
    with col2:
        search_author = st.text_input("🔍 Որոնել ըստ հեղինակի", placeholder="Մուտքագրեք հեղինակի անունը...")
    
    with col3:
        genre_options = ["Բոլորը"] + sorted(books_df['genre'].dropna().unique().tolist())
        selected_genre = st.selectbox("Ժանր", options=genre_options, index=0)

    with col4:
        lang_options = ["Բոլորը"] + sorted(books_df['language'].dropna().unique().tolist())
        selected_languages = st.selectbox("Լեզու", options=lang_options, index=0)
            
    filtered_books = books_df.copy()
    
    if search_title:
        filtered_books = filtered_books[filtered_books['title'].str.contains(search_title, case=False, na=False)]
    
    if search_author:
        filtered_books = filtered_books[filtered_books['author'].str.contains(search_author, case=False, na=False)]
    
    if selected_genre != "Բոլորը":
        filtered_books = filtered_books[filtered_books['genre'] == selected_genre]
    
    if selected_languages != "Բոլորը":
        filtered_books = filtered_books[filtered_books['language'] == selected_languages]
    
    # Pagination
    ITEMS_PER_PAGE = 10
    if 'book_page' not in st.session_state:
        st.session_state.book_page = 0

    total_items = len(filtered_books)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    start_idx = st.session_state.book_page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_books = filtered_books.iloc[start_idx:end_idx]

    for idx, (_, book) in enumerate(page_books.iterrows()):
        with st.expander(f"{book['title']} - {book['author']}"):
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
                st.write("**Կարդալ Գիրքը**")

                if pd.notna(book['link']) and book['link'].strip():
                    if book['id'] not in st.session_state.get('link_status', {}):
                        if 'link_status' not in st.session_state:
                            st.session_state.link_status = {}
                        st.session_state.link_status[book['id']] = check_link_availability(book['link'])

                    link_status = st.session_state.link_status[book['id']]

                    if link_status:
                        st.markdown(
                            "<p style='color: #8B4513; font-size: 18px; text-align: center; font-weight: bold; margin: 20px 0;'>"
                            "Գիրքը հասանելի է առցանց</p>",
                            unsafe_allow_html=True
                        )
                        st.link_button(
                            "Բացել Գիրքը",
                            book['link'],
                            use_container_width=True,
                            type="primary"
                        )
                    else:
                        st.error("PDF հղումը չի աշխատում")
                        st.markdown(f"[🔗 Փորձել արտաքին հղումը]({book['link']})")
                else:
                    custom_warning("Այս գրքի համար PDF հղում չկա")

                st.write("---")
                st.write("Ընթերցման Հետևում")

                c1, c2, c3 = st.columns(3)
                with c1:
                    pages_read = st.number_input(
                        "Կարդացած էջեր",
                        min_value=0,
                        max_value=int(book['pages']) if pd.notna(book['pages']) else 0,
                        value=0,
                        key=f"pages_{book['id']}_{idx}"
                    )
                with c2:
                    start_time = st.time_input(
                        "Ընթերցման սկիզբ",
                        value=None,
                        key=f"start_{book['id']}_{idx}"
                    )
                with c3:
                    end_time = st.time_input(
                        "Ընթերցման ավարտ",
                        value=None,
                        key=f"end_{book['id']}_{idx}"
                    )

                duration_minutes = 0
                if start_time and end_time:
                    today = datetime.now(timezone.utc).date()
                    start_dt = datetime.combine(today, start_time).replace(tzinfo=timezone.utc)
                    end_dt = datetime.combine(today, end_time).replace(tzinfo=timezone.utc)
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
                    if duration_minutes > 0:
                        custom_info(f"Ընթերցման ժամանակ: {duration_minutes} րոպե")

                if st.button("Պահպանել Ընթերցումը", key=f"save_{book['id']}_{idx}"):
                    if pages_read > 0 and start_time and end_time and duration_minutes > 0:
                        success = add_reading_session(
                            user['username'],  # ← changed to username
                            book['id'],
                            pages_read,
                            duration_minutes,
                            book['title']
                        )
                        if success:
                            custom_success("Ընթերցման տվյալները պահպանված են!")
                            update_reading_speed(user['username'])
                    else:
                        st.error("Խնդրում եմ լրացրեք բոլոր դաշտերը ճիշտ")

    # Pagination controls
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
    st.subheader("Անհատականացված Առաջարկներ")

    if books_df.empty:
        st.error("Չհաջողվեց բեռնել գրքերը")
        return

    user_preferences = {
        'preferred_genres': user.get('preferred_genres', []),
        'reading_speed': user.get('reading_speed'),
        'daily_reading_time': user.get('daily_reading_time'),
        'preferred_language': user.get('preferred_language', 'Հայերեն'),
        'age': user.get('age'),
    }

    effective_speed = user_preferences.get('reading_speed')
    if effective_speed is None or effective_speed <= 0:
        effective_speed = 2.0  # fallback

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

                    rec = get_reading_time_recommendation(book['genre'])
                    custom_success(f"Ընթերցման առաջարկ: {rec['icon']} {rec['time']}")
                    st.write(f"*{rec['reason']}*")

                    if pd.notna(book['link']) and book['link'].strip():
                        if 'link_status' not in st.session_state:
                            st.session_state.link_status = {}
                        if book['id'] not in st.session_state.link_status:
                            st.session_state.link_status[book['id']] = check_link_availability(book['link'])

                        if st.session_state.link_status[book['id']]:
                            st.markdown(
                                "<p style='color: #8B4513; font-size: 18px; text-align: center; font-weight: bold; margin: 20px 0;'>"
                                "Գիրքը հասանելի է առցանց</p>",
                                unsafe_allow_html=True
                            )
                            st.link_button(
                                "Կարդալ Այս Գիրքը",
                                book['link'],
                                use_container_width=True,
                                type="primary"
                            )

                    if pd.notna(book['description']) and book['description'].strip():
                        with st.expander("Նկարագրություն"):
                            st.write(book['description'])

                    with st.expander("Մեկնաբանություններ"):
                        show_book_comments_section(book['id'], user, f"rec_{book['id']}_{idx}")

                with col2:
                    st.caption("Անհատական պլանը հասանելի է «Ընթերցման Պլան» բաժնում")

                st.markdown("---")
    else:
        custom_info("Չգտնվեցին առաջարկվող գրքեր։ Ստուգեք ձեր նախընտրությունները կարգավորումներում։")


def show_reading_plan(books_df, user):
    st.subheader("Ընթերցման Պլանավորում")

    if books_df.empty:
        st.error("Չհաջողվեց բեռնել գրքերը")
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
        st.write(f"**Ժանր:** {book_info['genre']}")

        recommendation = get_reading_time_recommendation(book_info['genre'])
        custom_info(f"Ընթերցման առաջարկ: {recommendation['icon']} {recommendation['time']}")
        st.write(f"*{recommendation['reason']}*")

        if pd.notna(book_info['link']) and book_info['link'].strip():
            if 'link_status' not in st.session_state:
                st.session_state.link_status = {}
            if book_info['id'] not in st.session_state.link_status:
                st.session_state.link_status[book_info['id']] = check_link_availability(book_info['link'])

            if st.session_state.link_status[book_info['id']]:
                st.markdown(
                    "<p style='color: #8B4513; font-size: 18px; text-align: center; font-weight: bold; margin: 20px 0;'>"
                    "Գիրքը հասանելի է առցանց</p>",
                    unsafe_allow_html=True
                )
                st.link_button(
                    "Բացել Գիրքը Պլանավորման Համար",
                    book_info['link'],
                    use_container_width=True,
                    type="primary"
                )

    with col2:
        pages = int(book_info['pages']) if pd.notna(book_info['pages']) else 0

        reading_speed = user.get('reading_speed')

        if reading_speed is None or reading_speed <= 0:
            custom_info("Ձեր ընթերցման արագությունը դեռ հաշվարկված չէ")
            st.caption("Գրանցեք առաջին ընթերցումը՝ ավելի ճշգրիտ պլան ստանալու համար")
            return

        # FIX: Convert Decimal → float (MySQL DECIMAL comes as decimal.Decimal)
        reading_speed = float(reading_speed)

        target_days = st.number_input(
            "Քանի օրում ցանկանում եք ավարտել գիրքը?",
            min_value=1,
            max_value=365,
            value=10,
            step=1
        )

        if pages > 0 and target_days > 0:
            required_daily_pages = pages / target_days
            required_daily_minutes = required_daily_pages / reading_speed

            st.markdown(f"**Օրական պլան (ձեր արագությամբ):**")
            st.markdown(f"- Էջեր՝ **{required_daily_pages:.1f}** էջ/օր")
            st.markdown(f"- Ժամանակ՝ **{required_daily_minutes:.0f}** րոպե/օր")

            if required_daily_minutes > 180:
                custom_warning("Շատ ինտենսիվ է՝ օրական կպահանջվի 3+ ժամ")
            elif required_daily_minutes > 120:
                custom_warning("Բավականին շատ է՝ օրական 2 ժամից ավելի")
            elif required_daily_minutes > 60:
                custom_info("Լավ տեմպ է՝ օրական մոտ 1 ժամ")
            elif required_daily_minutes > 30:
                custom_success("Հարմարավետ և իրագործելի է")
            else:
                custom_success("Շատ հեշտ է՝ կարճ ժամանակ կպահանջվի")

            total_hours = (pages / reading_speed) / 60
            custom_info(f"Ընդհանուր ընթերցման ժամանակ: {total_hours:.1f} ժամ")

            st.subheader("Շաբաթական պլան")
            st.write(f"Շաբաթական էջեր՝ **{required_daily_pages * 7:.1f}** էջ")
            st.write(f"Շաբաթական ժամանակ՝ **{required_daily_minutes * 7:.0f}** րոպե")

        else:
            custom_warning("Գրքի էջերի քանակը կամ օրերի թիվը անվավեր է")
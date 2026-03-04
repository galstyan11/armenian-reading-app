# modules/users_file.py
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import re

from modules.auth_file import verify_password
from modules.data_file import (
    get_user_sessions,
    add_reminder,
    get_user_reminder,
    check_reminder_time,
    calculate_reading_speed,
    get_creative_works
)
from modules.social import (
    add_friend,
    get_chat_between,
    load_friends,
    remove_friend,
    send_message,
    add_friend_request,
    get_pending_received_requests,
    accept_friend_request,
    reject_friend_request
)
from modules.utils import calculate_reading_plan
from modules.custom_alerts import custom_success, custom_info, custom_warning, custom_empty
from modules.books_csv import load_books
from modules.time_utils import ARMENIA_TZ, format_armenia_datetime, parse_iso_or_datetime
from modules.db import query  # ← for direct DB access in settings/profile


# @st.cache_data(ttl=3600)  # Cache for 1 hour
def _load_books_cached():
    return load_books()


def get_user_by_username(username: str) -> dict | None:
    """Helper: load single user from DB (used for viewed profiles)"""
    row = query("""
        SELECT 
            username, email, password_hash,
            daily_reading_time, reading_speed,
            preferred_genres, preferred_languages,
            age, profession, bio, created_at
        FROM users 
        WHERE username = %s
        LIMIT 1
    """, (username,), fetch=True, one=True)

    if not row:
        return None

    row['preferred_genres']    = json.loads(row['preferred_genres'] or '[]')
    row['preferred_languages'] = json.loads(row['preferred_languages'] or '[]')
    row['id'] = row['username']
    return row


def get_reading_insights(user_id):
    sessions = get_user_sessions(user_id)
    
    total_books = len(set(session['book_id'] for session in sessions))
    total_pages = sum(session['pages_read'] for session in sessions)
    total_minutes = sum(session['session_duration'] for session in sessions)
    total_hours = round(total_minutes / 60, 1)
    
    reading_speed = calculate_reading_speed(user_id)
    
    now_utc = datetime.now(timezone.utc)
    one_week_ago_utc = now_utc - timedelta(days=7)
    
    weekly_pages = sum(
        s['pages_read']
        for s in sessions
        if parse_iso_or_datetime(s['created_at']) > one_week_ago_utc
    )
    
    insights = []
    if total_pages > 0 and reading_speed is not None:
        if reading_speed > 3.0:
            insights.append("🚀 Դուք արագ ընթերցող եք։ Հիանալի է տեխնիկական և գիտական գրքերի համար։")
        elif reading_speed < 1.5:
            insights.append("📖 Դուք չափավոր տեմպերով եք կարդում։ Սա օպտիմալ է գրականության և բանաստեղծությունների համար։")
        else:
            insights.append("⚡ Ձեր ընթերցման տեմպը հավասարակշռված է։ Գերազանց է բոլոր ժանրերի համար։")
        
        if total_books >= 5:
            insights.append("📚 Դուք արդեն կարդացել եք բազմաթիվ գրքեր։ Շարունակեք նույն տեմպերով։")
        elif total_books == 0:
            insights.append("📝 Սկսեք ավելացնել ձեր ընթերցումները՝ ձեր վիճակագրությունը տեսնելու համար։")
        
        if weekly_pages > 50:
            insights.append("🔥 Անցած շաբաթը շատ արդյունավետ էր։ Շարունակեք պահպանել այս տեմպը։")
        elif weekly_pages < 10 and len(sessions) > 0:
            insights.append("💪 Փորձեք ավելացնել օրական ընթերցման ժամանակը։ Փոքր քայլերով էլ կարող եք մեծ արդյունքի հասնել։")
    
    return {
        'total_books': total_books,
        'total_pages': total_pages,
        'total_hours': total_hours,
        'reading_speed': reading_speed,
        'weekly_pages': weekly_pages,
        'insights': insights
    }


def show_statistics(user):
    st.subheader("Իմ Ընթերցման Վիճակագրությունը")
    
    insights_data = get_reading_insights(user['id'])
    
    sessions = get_user_sessions(user['id'])
    unique_book_ids = set(s['book_id'] for s in sessions)
    total_books_read = len(unique_book_ids)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Կարդացած Գրքեր", total_books_read)
    with col2:
        st.metric("Ընդհանուր Էջեր", insights_data['total_pages'])
    with col3:
        st.metric("Ընդհանուր Ժամանակ", f"{insights_data['total_hours']} ժամ")
    with col4:
        speed = insights_data['reading_speed']
        if speed is not None and speed > 0:
            if speed >= 2.0:
                label = "Շատ արագ ընթերցող"
            elif speed >= 1.5:
                label = "Արագ ընթերցող"
            elif speed >= 0.8:
                label = "Միջին արագությամբ ընթերցող"
            else:
                label = "Հանգիստ արագությամբ ընթերցող"
            st.metric("Իրական Արագություն", f"{speed:.1f} էջ/րոպե")
            custom_success(f"{label} — հաշվված է Ձեր ընթերցումների հիման վրա։")
        else:
            st.metric("Իրական Արագություն", "Դեռ չի հաշվվել")
            custom_info("Սկսեք ընթերցել և պահպանել Ձեր ընթերցումները՝ իրական արագությունը տեսնելու համար")


def show_reminders(user):
    st.subheader("Ընթերցման Հիշեցումներ")
    
    st.caption(
        "Այս պահին հիշեցումները պահպանվում են համակարգում, բայց դեռ չեն ուղարկվում "
        "ծանուցումներով կամ էլ. փոստով։"
    )
    
    existing_reminder = get_user_reminder(user['id'])
    
    with st.form("reminder_form", clear_on_submit=False):
        col1, col2 = st.columns([3, 4])
        
        with col1:
            default_time = existing_reminder['reminder_time'] if existing_reminder else "20:00"
            reminder_time = st.text_input(
                "Ընթերցման ժամանակ (ԺԺ:ՐՐ)",
                value=default_time,
                help="Օրինակ՝ 19:30, 21:00"
            )
        
        with col2:
            days_options = ["Երկուշաբթի", "Երեքշաբթի", "Չորեքշաբթի", 
                            "Հինգշաբթի", "Ուրբաթ", "Շաբաթ", "Կիրակի"]
            default_days = existing_reminder['days_of_week'] if existing_reminder else days_options[:5]
            selected_days = st.multiselect(
                "Օրեր",
                options=days_options,
                default=default_days,
            )
        
        submitted = st.form_submit_button("Պահպանել Հիշեցումը", type="primary")
        
        if submitted:
            if not selected_days:
                custom_warning("Խնդրում եմ ընտրել առնվազն մեկ օր")
            elif not reminder_time.strip():
                custom_warning("Խնդրում եմ մուտքագրել ժամանակը")
            else:
                try:
                    h, m = map(int, reminder_time.split(':'))
                    if not (0 <= h <= 23 and 0 <= m <= 59):
                        raise ValueError
                    normalized_time = f"{h:02d}:{m:02d}"
                except ValueError:
                    custom_warning("Նշված ձևաչափը սխալ է: (օրինակ՝ 20:00)")
                else:
                    success = add_reminder(user['id'], reminder_time.strip(), selected_days, True)
                    if success:
                        custom_success("Հիշեցման կարգավորումները պահպանվել են!")
                        st.rerun()
                    else:
                        custom_warning("Չհաջողվեց պահպանել հիշեցումը")
    
    st.subheader("Ընթացիկ Հիշեցում")
    current = get_user_reminder(user['id'])

    if not current:
        custom_info("Դեռ չունեք սահմանված հիշեցում")
        return

    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("Ժամանակ")
            st.markdown(f"{current['reminder_time']}")
        with col2:
            st.markdown("Օրեր")
            st.markdown(f"{', '.join(current['days_of_week'])}")

        st.caption(
            f"Կարգավիճակ՝ {'Ակտիվ' if current.get('is_active', True) else 'Անջատված'}"
        )

        now_yerevan = datetime.now(timezone.utc).astimezone(ARMENIA_TZ)
        today_en = now_yerevan.strftime("%A")
        
        today_map = {
            "Monday": "Երկուշաբթի", "Tuesday": "Երեքշաբթի", "Wednesday": "Չորեքշաբթի",
            "Thursday": "Հինգշաբթի", "Friday": "Ուրբաթ", "Saturday": "Շաբաթ", "Sunday": "Կիրակի"
        }
        today_arm = today_map.get(today_en, "")

        if today_arm in current['days_of_week']:
            custom_success("Այսօր ընթերցման պլանավորված օր է")
        else:
            custom_success("Այսօր ընթերցման պլան չկա")



def show_settings(user, books_df):
    st.subheader("Օգտատիրոջ Կարգավորումներ")
    
    st.write(f"**Օգտանուն:** {user['username']}")
    st.write(f"**Էլ. Փոստ:** {user['email']}")
    
    created_at_str = user.get('created_at')
    if created_at_str:
            st.write(f"**Գրանցման ամսաթիվ:** {format_armenia_datetime(parse_iso_or_datetime(created_at_str))}")
    else:
        st.write("**Գրանցման ամսաթիվ:** Անհայտ")
    
    st.subheader("Թարմացնել Նախապատվությունները")
    
    if user.get('reading_speed') is not None:
        st.write(f"**Ընթերցման Արագություն:** {user['reading_speed']:.1f} էջ/րոպե")
        st.caption("Այս արժեքն ավտոմատ հաշվվում է Ձեր ընթերցումների հիման վրա։")
    else:
        st.write("**Ընթերցման Արագություն:** Դեռ չի հաշվվել")
        custom_info("Սկսեք ընթերցել իրական արագությունը տեսնելու համար")
    
    new_daily_time = st.slider(
        "Օրական Ընթերցման Ժամանակ (րոպե)",
        15, 180,
        user.get('daily_reading_time', 30)
    )
    
    available_genres = sorted(
        books_df['genre'].dropna().astype(str).str.strip().unique().tolist()
    ) if not books_df.empty else []

    current_genres = user.get('preferred_genres', [])

    valid_defaults = [g for g in current_genres if g.strip() in available_genres]

    new_preferred_genres = st.multiselect(
        "Նախընտրելի Ժանրեր",
        options=["Բոլորը"] + available_genres if available_genres else ["Բոլորը"],
        default=valid_defaults,
        placeholder="Կարող եք ընտրել մի քանիսը",
        key="settings_genres_unique_key"
    )
    
    lang_options = ["Հայերեն", "Ռուսերեն", "Անգլերեն"]
    current_languages = user.get('preferred_languages', [])
    if not current_languages and 'preferred_language' in user:
        old = user['preferred_language']
        current_languages = [old] if isinstance(old, str) and old else []

    new_preferred_languages = st.multiselect(
        "Նախընտրելի Լեզուներ",
        options=lang_options,
        default=current_languages,
        placeholder="Ընտրեք մեկ կամ ավելի լեզուներ",
        key="settings_languages_unique_key"
    )
    
    new_age = st.number_input(
        "Տարիք",
        min_value=13,
        max_value=120,
        value=user.get('age') if user.get('age') is not None else None,
        step=1
    )
    
    profession_default = str(user.get('profession') or "")
    new_profession = st.text_input("Մասնագիտություն", value=profession_default)
    
    bio_default = str(user.get('bio') or "")
    new_bio = st.text_area("Իմ մասին", value=bio_default, height=100)
    
    if st.button("Պահպանել Կարգավորումները", type="primary"):
        try:
            query("""
                UPDATE users
                SET 
                    daily_reading_time = %s,
                    preferred_genres = %s,
                    preferred_languages = %s,
                    age = %s,
                    profession = %s,
                    bio = %s
                WHERE username = %s
            """, (
                new_daily_time,
                json.dumps(new_preferred_genres),
                json.dumps(new_preferred_languages),
                new_age if new_age else None,
                new_profession.strip() or None,
                new_bio.strip() or None,
                user['username']
            ))

            # Refresh current user in session state
            refreshed = query("""
                SELECT 
                    username, email, password_hash,
                    daily_reading_time, reading_speed,
                    preferred_genres, preferred_languages,
                    age, profession, bio, created_at
                FROM users 
                WHERE username = %s
            """, (user['username'],), fetch=True, one=True)

            if refreshed:
                refreshed['preferred_genres'] = json.loads(refreshed['preferred_genres'] or '[]')
                refreshed['preferred_languages'] = json.loads(refreshed['preferred_languages'] or '[]')
                refreshed['id'] = refreshed['username']
                st.session_state.user = refreshed

            custom_success("Կարգավորումները պահպանված են!")
            st.rerun()

        except Exception as e:
            st.error(f"Սխալ կարգավորումները պահպանելիս: {str(e)}")

    
    # Հաշվի ջնջում — վտանգավոր գոտի
    st.divider()
    st.subheader("Հաշվի ջնջում")
    st.caption("Այս գործողությունն անշրջելի է և կջնջի բոլոր տվյալները")

    with st.expander("Ջնջել իմ հաշիվը", expanded=False):

        really_sure = st.checkbox(
            "Ես գիտակցում եմ, որ չեմ կարողանա վերականգնել հաշիվս",
            key="delete_really_sure_checkbox"
        )

        if really_sure:

            password = st.text_input(
                "Վերջնական հաստատման համար մուտքագրեք Ձեր գաղտնաբառը",
                type="password",
                key="delete_account_password"
            )

            delete_enabled = really_sure and password.strip() != ""

            if st.button(
                "Ջնջել հաշիվը",
                type="primary",
                disabled=not delete_enabled,
                use_container_width=True,
                key="final_delete_account_button"
            ):
                from modules.utils import delete_account
                
                with st.spinner("Հաշիվը ջնջվում է..."):
                    success, message = delete_account(
                        username=user['username'],
                        password_input=password
                    )
                
                if success:
                    custom_success(message)
                    
                    import time
                    time.sleep(2.5)

                    # ամբողջ session-ը մաքրել
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    
                    st.session_state.logged_out = True
                    st.rerun()
                else:
                    st.error(message or "Չհաջողվեց ջնջել հաշիվը")
                    
def show_read_books_section(viewed_user):
    st.subheader("Կարդացած Գրքեր")
    user_sessions = get_user_sessions(viewed_user['id'])
    if not user_sessions:
        custom_empty("Դեռ չկան գրանցված ընթերցումներ։")
        return

    book_progress = {}
    for session in user_sessions:
        book_id = session['book_id']
        if book_id not in book_progress:
            book_progress[book_id] = {
                'title': session['book_title'],
                'pages_read': 0
            }
        book_progress[book_id]['pages_read'] += session['pages_read']

    books_df = _load_books_cached()
    read_books_list = []

    for book_id, progress in book_progress.items():

        book_row = books_df[books_df['id'] == str(book_id)]
        if not book_row.empty:
            book = book_row.iloc[0]
            total_pages = int(book['pages']) if pd.notna(book['pages']) else 0
            progress.update({
                'total_pages': total_pages,
                'author': book.get('author', 'Անհայտ'),
                'genre': book.get('genre', ''),
                'percentage': (progress['pages_read'] / total_pages * 100) if total_pages > 0 else 0
            })
            read_books_list.append(progress)

    if not read_books_list:
        custom_empty("Գրքերի մասին տեղեկություն չի գտնվել։")
        return

    read_books_list.sort(key=lambda x: x['pages_read'], reverse=True)

    for book in read_books_list:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{book['title']}** — {book['author']}")
                if book['genre']:
                    st.caption(f"Ժանր: {book['genre']}")
            with col2:
                if book['total_pages'] > 0:
                    percentage = min(100, book['percentage'])
                    st.progress(percentage / 100)
                    st.caption(f"{book['pages_read']}/{book['total_pages']} էջ ({percentage:.0f}%)")
                else:
                    st.caption(f"{book['pages_read']} էջ")
            st.markdown("")

def show_full_profile(current_user, books_df):
    viewed_username = st.session_state.get('viewed_profile', None)

    if viewed_username and viewed_username != current_user['username']:
        viewed_user = get_user_by_username(viewed_username)
        if not viewed_user:
            st.error("Օգտատերը չի գտնվել")
            return
        
        st.subheader(f"{viewed_username}-ի Պրոֆիլը")

        col1, col2 = st.columns([1, 3])
        with col1:
            initial = viewed_user['username'][0].upper()
            st.markdown(f"""
            <div style="background-color: #F5E8DC; border-radius: 50%; width: 150px; height: 150px; 
                 display: flex; align-items: center; justify-content: center; font-size: 70px; 
                 color: #BF6B3B; font-weight: bold;">
                {initial}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.write(f"**Օգտանուն:** {viewed_user['username']}")
            st.write(f"**էլ․ փոստ։** {viewed_user['email']}")
            if viewed_user.get('age'):
                st.write(f"**Տարիք:** {viewed_user['age']}")
            if viewed_user.get('profession'):
                st.write(f"**Մասնագիտություն:** {viewed_user['profession']}")
            if viewed_user.get('bio'):
                st.write(f"**{viewed_user['username']}-ի մասին:** {viewed_user['bio']}")

            created_at_str = viewed_user.get('created_at')
            reg_date = format_armenia_datetime(parse_iso_or_datetime(created_at_str)) if created_at_str else "Անհայտ"
            st.write(f"**Գրանցվել է:** {reg_date}")

        # ────────────────────────────────────────────────
        # Read books + messaging
        # ────────────────────────────────────────────────
        st.markdown("---")
        show_read_books_section(viewed_user)

        st.markdown("---")
        st.subheader(f"Հաղորդագրություն գրել {viewed_user['username']}-ին")

        if viewed_user['username'] in load_friends(current_user['username']):
            # Chat messages display
            chat_messages = get_chat_between(current_user['username'], viewed_user['username'])

            chat_container = st.container(height=300)
            with chat_container:
                if not chat_messages:
                    st.caption("Դեռ հաղորդագրություններ չկան")
                
                for msg in chat_messages:
                    sender_class = "you" if msg["sender"] == current_user['username'] else "friend"
                    label = "Դուք" if msg["sender"] == current_user['username'] else viewed_user['username']

                    created_at = msg.get('created_at')
                    date_str = (
                        format_armenia_datetime(parse_iso_or_datetime(created_at))
                        if created_at else "—"
                    )
                    # Optional: only show date if it's not today (to reduce clutter)
                    # But simplest is always show date:
                    st.markdown(
                        f"""
                        <div class="chat-message {sender_class}">
                            <small>{label} · {date_str}</small>
                            {msg['content']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # ── Message input with form (this fixes the staying text issue) ──
            with st.form(key=f"chat_form_{viewed_user['username']}", clear_on_submit=True):
                new_msg = st.text_area(
                    label="Հաղորդագրություն գրել",
                    label_visibility="collapsed",
                    height=80,
                    placeholder="Գրեք Ձեր հաղորդագրությունը այստեղ...",
                    key=f"msg_area_{viewed_user['username']}"
                )

                submitted = st.form_submit_button("Ուղարկել", type="primary")

                if submitted:
                    if not new_msg.strip():
                        st.warning("Հաղորդագրությունը դատարկ է")
                    else:
                        success, message = send_message(
                            current_user['username'],
                            viewed_user['username'],
                            new_msg.strip()
                        )
                        if success:
                            custom_success("Հաղորդագրությունը ուղարկվել է!")
                            st.rerun()  # refresh chat + clear form
                        else:
                            st.error(message)

        else:
            st.warning(f"{viewed_user['username']}-ը Ձեր ընկերների ցանկում չէ — հաղորդագրություն ուղարկել հնարավոր չէ")

        # Back button
        if st.button("Վերադառնալ իմ պրոֆիլին"):
            if 'viewed_profile' in st.session_state:
                del st.session_state.viewed_profile
            if 'active_profile_tab' in st.session_state:
                del st.session_state.active_profile_tab
            st.rerun()
        return

    # ── Own profile (no changes needed here) ─────────────────────────────
    viewed_user = current_user
    st.subheader("Իմ Պրոֆիլը")

    profile_tabs = st.tabs(["📋 Տեղեկություններ", "📊 Վիճակագրություն", "⚙️ Կարգավորումներ", "⏰ Հիշեցումներ", "👥 Ընկերներ"])

    with profile_tabs[0]:
        col1, col2 = st.columns([1, 3])
        with col1:
            initial = viewed_user['username'][0].upper()
            st.markdown(f"""
            <div style="background-color: #F5E8DC; border-radius: 50%; width: 150px; height: 150px; 
                 display: flex; align-items: center; justify-content: center; font-size: 70px; 
                 color: #BF6B3B; font-weight: bold;">
                {initial}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.write(f"**Օգտանուն:** {viewed_user['username']}")
            st.write(f"**էլ․ փոստ։** {viewed_user['email']}")
            if viewed_user.get('age'):
                st.write(f"**Տարիք:** {viewed_user['age']}")
            if viewed_user.get('profession'):
                st.write(f"**Մասնագիտություն:** {viewed_user['profession']}")
            if viewed_user.get('bio'):
                st.write(f"**Իմ մասին:** {viewed_user['bio']}")

            created_at_str = viewed_user.get('created_at')
            reg_date = format_armenia_datetime(parse_iso_or_datetime(created_at_str)) if created_at_str else "Անհայտ"
            st.write(f"**Գրանցվել է:** {reg_date}")

            st.markdown("**Ընթերցման Նախապատվություններ**")
            speed_display = f"{viewed_user['reading_speed']:.1f} էջ/րոպե" if viewed_user.get('reading_speed') is not None else "Դեռ չի հաշվվել"
            st.write(f"• Արագություն: {speed_display}")

            langs = viewed_user.get('preferred_languages', [])
            if not langs and 'preferred_language' in viewed_user:
                old_lang = viewed_user['preferred_language']
                langs = [old_lang] if old_lang and isinstance(old_lang, str) else []
            lang_text = ', '.join(langs) if langs else 'Չի նշված'
            st.write(f"• Լեզուներ: {lang_text}")

            if viewed_user.get('preferred_genres'):
                st.write(f"• Ժանրեր: {', '.join(viewed_user['preferred_genres'])}")

        st.markdown("---")
        show_read_books_section(viewed_user)
    
    with profile_tabs[1]:
        show_statistics(current_user)

    with profile_tabs[2]:
        show_settings(current_user, books_df)

    with profile_tabs[3]:
        show_reminders(current_user)

    with profile_tabs[4]:
        st.subheader("Ընկերներ")

        current_friends = load_friends(current_user['username'])

        if current_friends:
            custom_success(f"Ընկերներ՝ {len(current_friends)}")
            for friend in sorted(current_friends):
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"• {friend}", key=f"view_profile_{friend}", type="secondary"):
                        st.session_state.viewed_profile = friend
                        st.rerun()

                with col2:
                    if st.button("Հեռացնել", key=f"remove_{friend}", type="secondary"):
                        if remove_friend(current_user['username'], friend):
                            custom_success(f"{friend}-ը հեռացվել է Ձեր ընկերների ցանկից")
                            st.rerun()
                        else:
                            custom_warning("Չհաջողվեց հեռացնել")

        else:
            custom_info("Դեռ ընկերներ չունեք")

        st.markdown("---")

        st.subheader("Ստացված հրավերներ")
        pending_requests = get_pending_received_requests(current_user['username'])

        if pending_requests:
            for sender in pending_requests:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"• {sender} ուզում է ընկերանալ")
                with col2:
                    if st.button("Ընդունել", key=f"accept_{sender}", type="primary"):
                        if accept_friend_request(current_user['username'], sender):
                            custom_success(f"{sender}-ը ավելացվել է Ձեր ընկերներին")
                            st.rerun()
                        else:
                            custom_warning("Չհաջողվեց ընդունել")
                with col3:
                    if st.button("Մերժել", key=f"reject_{sender}", type="secondary"):
                        if reject_friend_request(current_user['username'], sender):
                            custom_success(f"{sender}-ի հրավերը մերժվել է")
                            st.rerun()
                        else:
                            custom_warning("Չհաջողվեց մերժել")
        else:
            custom_info("Չկան ստացված հրավերներ")

        st.markdown("---")

        st.subheader("Ավելացնել ընկեր")
        new_friend_input = st.text_input("Օգտանուն", placeholder="Մուտքագրեք օգտանունը", key="add_friend_input")

        if st.button("Ուղարկել ընկերության հայտ", type="primary"):
            new_friend = new_friend_input.strip()
            if not new_friend:
                custom_warning("Մուտքագրեք օգտանուն")
            elif new_friend == current_user['username']:
                custom_warning("Ինքներդ Ձեզ չեք կարող ավելացնել")
            else:
                viewed_friend = get_user_by_username(new_friend)
                if not viewed_friend:
                    custom_warning(f"Օգտատեր '{new_friend}' չի գտնվել")
                elif new_friend in current_friends:
                    custom_info(f"{new_friend}-ն արդեն Ձեր ընկերն է")
                elif add_friend_request(current_user['username'], new_friend):
                    custom_success(f"Հրավերն ուղարկվել է {new_friend}-ին")
                else:
                    custom_warning("Չհաջողվեց ուղարկել հրավերը (հնարավոր է արդեն ուղարկված է)")
                    
    return
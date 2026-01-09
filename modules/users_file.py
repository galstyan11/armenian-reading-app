# modules/users_file.py
import streamlit as st
import pandas as pd
from datetime import datetime as dt, timedelta
from modules.data_file import (
    get_user_sessions, add_reminder, get_user_reminder, check_reminder_time,
    calculate_reading_speed, load_users, get_creative_works
)
from modules.utils import calculate_reading_plan
from modules.custom_alerts import custom_success, custom_info, custom_warning, custom_empty
from modules.auth_file import save_users
from modules.books_csv import load_books  # Ավելացրել ենք import-ը


@st.cache_data(ttl=3600)  # Քեշ 1 ժամով
def _load_books_cached():
    return load_books()


def get_reading_insights(user_id):
    sessions = get_user_sessions(user_id)
    
    total_books = len(set(session['book_id'] for session in sessions))
    total_pages = sum(session['pages_read'] for session in sessions)
    total_minutes = sum(session['session_duration'] for session in sessions)
    total_hours = round(total_minutes / 60, 1)
    
    reading_speed = calculate_reading_speed(user_id)
    
    one_week_ago = dt.now() - timedelta(days=7)
    weekly_pages = sum(
        session['pages_read'] for session in sessions 
        if dt.fromisoformat(session['created_at'].replace('Z', '+00:00')) > one_week_ago
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
    st.subheader("📊 Իմ Ընթերցման Վիճակագրությունը")
    
    insights_data = get_reading_insights(user['id'])
    
    sessions = get_user_sessions(user['id'])
    unique_book_ids = set(session['book_id'] for session in sessions)
    total_books_read = len(unique_book_ids)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 Կարդացած Գրքեր", total_books_read)
    with col2:
        st.metric("📄 Ընդհանուր Էջեր", insights_data['total_pages'])
    with col3:
        st.metric("⏱️ Ընդհանուր Ժամանակ", f"{insights_data['total_hours']} ժամ")
    with col4:
        speed = insights_data['reading_speed']
        if speed is not None and speed > 0:
            if speed >= 2.0:
                label = "🚀 Շատ արագ ընթերցող"
            elif speed >= 1.5:
                label = "⚡ Արագ ընթերցող"
            elif speed >= 0.8:
                label = "📖 Միջին ընթերցող"
            else:
                label = "🐢 Հանգիստ տեմպ"
            st.metric("Իրական Արագություն", f"{speed:.1f} էջ/րոպե")
            st.success(f"**{label}** — հաշվված է Ձեր սեսիաներից")
        else:
            st.metric("Իրական Արագություն", "Դեռ չի հաշվվել")
            custom_info("📝 Ավելացրեք առաջին ընթերցման սեսիան՝ Ձեր իրական արագությունը տեսնելու համար")


def show_reminders(user):
    st.subheader("⏰ Ընթերցման Հիշեցումներ")
    
    custom_info("**📖 Ընթերցման հիշեցումներ** - Սահմանեք ձեր ամենօրյա ընթերցման ժամանակը, և մենք կհիշեցնենք ձեզ 5 րոպե առաջ։")
    
    existing_reminder = get_user_reminder(user['id'])
    
    with st.form("reminder_form"):
        col1, col2 = st.columns(2)
        with col1:
            default_time = existing_reminder['reminder_time'] if existing_reminder else "20:00"
            reminder_time = st.text_input("🕐 Ընթերցման ժամանակ", value=default_time, placeholder="20:00")
        with col2:
            days_options = ["Երկուշաբթի", "Երեքշաբթի", "Չորեքշաբթի", "Հինգշաբթի", "Ուրբաթ", "Շաբաթ", "Կիրակի"]
            default_days = existing_reminder['days_of_week'] if existing_reminder else days_options
            selected_days = st.multiselect("📅 Օրեր", options=days_options, default=default_days)
        
        is_active = st.checkbox("Ակտիվացնել հիշեցումները", value=existing_reminder['is_active'] if existing_reminder else True)
        
        submitted = st.form_submit_button("💾 Պահպանել Հիշեցումը")
        
        if submitted:
            if not selected_days:
                st.error("❌ Խնդրում եմ ընտրել առնվազն մեկ օր")
            elif not reminder_time:
                st.error("❌ Խնդրում եմ մուտքագրել ժամանակ")
            else:
                success = add_reminder(user['id'], reminder_time, selected_days, is_active)
                if success:
                    custom_success("✅ Հիշեցումը հաջողությամբ պահպանված է!")
                    days_str = ", ".join(selected_days)
                    custom_info(f"""
                    **📋 Ձեր հիշեցման կարգավորումները:**
                    - **⏰ Ժամանակ:** {reminder_time}
                    - **📅 Օրեր:** {days_str}
                    - **🔔 Կարգավիճակ:** {'Ակտիվ' if is_active else 'Անջատված'}
                    - **⏱️ Հիշեցում:** 5 րոպե առաջ
                    """)
                    if is_active:
                        st.balloons()
                else:
                    st.error("❌ Չհաջողվեց պահպանել հիշեցումը")
    
    st.subheader("🔔 Ընթացիկ Հիշեցում")
    current_reminder = get_user_reminder(user['id'])
    if current_reminder and current_reminder['is_active']:
        days_str = ", ".join(current_reminder['days_of_week'])
        custom_success(f"""
        **✅ Ակտիվ հիշեցում**
        - **⏰ Ժամանակ:** {current_reminder['reminder_time']}
        - **📅 Օրեր:** {days_str}
        - **⏱️ Հիշեցում:** 5 րոպե առաջ
        """)
        if check_reminder_time(user['id']):
            st.warning("**🔔 Ընթերցման Ժամանակն է!** Մոտենում է ձեր ընթերցման ժամանակը:")
            st.balloons()
    elif current_reminder and not current_reminder['is_active']:
        st.warning("**🔕 Հիշեցումները անջատված են**")
    else:
        custom_info("**Դեռ չունեք ակտիվ հիշեցումներ**")


def show_settings(user, books_df):
    st.subheader("⚙️ Օգտատիրոջ Կարգավորումներ")
    
    st.write(f"**Օգտանուն:** {user['username']}")
    st.write(f"**Էլ. Փոստ:** {user['email']}")
    
    created_at_str = user.get('created_at', None)
    if created_at_str:
        try:
            full_dt = dt.fromisoformat(created_at_str.replace('Z', '+00:00'))
            formatted_date = full_dt.strftime("%Y-%m-%d %H:%M")
            st.write(f"**Գրանցման ամսաթիվ:** {formatted_date}")
        except Exception:
            st.write(f"**Գրանցման ամսաթիվ:** {created_at_str}")
    else:
        st.write("**Գրանցման ամսաթիվ:** Անհայտ")
    
    st.subheader("🔄 Թարմացնել Նախապատվությունները")
    
    if user['reading_speed'] is not None:
        st.write(f"**Ընթերցման Արագություն:** {user['reading_speed']:.1f} էջ/րոպե")
        st.caption("Այս արժեքն ավտոմատ հաշվվում է Ձեր ընթերցումների հիման վրա։")
    else:
        st.write("**Ընթերցման Արագություն:** Դեռ չի հաշվվել")
        custom_info("📝 Սկսեք ընթերցել իրական արագությունը տեսնելու համար")
    
    new_daily_time = st.slider("Օրական Ընթերցման Ժամանակ (րոպե)", 15, 180, user['daily_reading_time'])
    
    available_genres = books_df['genre'].unique().tolist() if not books_df.empty else []
    current_genres = user['preferred_genres'] if user['preferred_genres'] else []
    new_preferred_genres = st.multiselect("Նախընտրելի Ժանրեր", available_genres, default=current_genres,
                                          placeholder="Կարող եք ընտրել մի քանիսը", key="settings_genres")
    
    current_language = user.get('preferred_language', 'Հայերեն')
    new_preferred_language = st.selectbox("Նախընտրելի Լեզու", ["Հայերեն", "Ռուսերեն", "Անգլերեն"],
                                          index=["Հայերեն", "Ռուսերեն", "Անգլերեն"].index(current_language))
    
    new_age = st.number_input("Տարիք", min_value=13, max_value=120,
                              value=user.get('age') if user.get('age') is not None else 18, step=1)
    new_profession = st.text_input("Մասնագիտություն", value=user.get('profession', ''))
    new_bio = st.text_area("Իմ մասին", value=user.get('bio', ''), height=100)
    
    if st.button("💾 Պահպանել Կարգավորումները"):
        try:
            users = load_users()
            if user['username'] in users:
                users[user['username']]['daily_reading_time'] = new_daily_time
                users[user['username']]['preferred_genres'] = new_preferred_genres
                users[user['username']]['preferred_language'] = new_preferred_language
                users[user['username']]['age'] = new_age if new_age != 18 else None
                users[user['username']]['profession'] = new_profession.strip() or None
                users[user['username']]['bio'] = new_bio.strip() or None
                
                save_users(users)
                
                st.session_state.user = users[user['username']].copy()
                st.session_state.user['username'] = user['username']
                st.session_state.user['id'] = user['username']
                
                custom_success("✅ Կարգավորումները պահպանված են!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Սխալ կարգավորումները պահպանելիս: {e}")


def show_read_books_section(viewed_user):
    """Կարդացած գրքերի բաժինը — օգտագործվում է և՛ սեփական, և՛ ուրիշի պրոֆիլում"""
    st.subheader("📚 Կարդացած Գրքեր")

    user_sessions = get_user_sessions(viewed_user['id'])
    if not user_sessions:
        custom_empty("Դեռ չկան գրանցված ընթերցումներ։")
        return

    # Հավաքել ընդհանուր կարդացած էջերը յուրաքանչյուր գրքի համար
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
        book_row = books_df[books_df['id'] == book_id]
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

    # Տեսակավորել՝ ամենաշատ կարդացածները վերևում
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
        # Ուրիշի պրոֆիլ — առանց tab-երի
        from modules.auth_file import load_users
        users = load_users()
        if viewed_username not in users:
            st.error("❌ Օգտատերը չի գտնվել")
            return
        viewed_user = users[viewed_username]
        viewed_user['id'] = viewed_username
        viewed_user['username'] = viewed_username
        st.subheader(f"👤 {viewed_username}-ի Պրոֆիլը")

        # Ավատար և տվյալներ
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
            if viewed_user.get('age'):
                st.write(f"**Տարիք:** {viewed_user['age']}")
            if viewed_user.get('profession'):
                st.write(f"**Մասնագիտություն:** {viewed_user['profession']}")
            if viewed_user.get('bio'):
                st.write(f"**{viewed_user['username']}-ի մասին:** {viewed_user['bio']}")

            created_at = viewed_user.get('created_at', 'Անհայտ')[:10] if viewed_user.get('created_at') else 'Անհայտ'
            st.write(f"**Գրանցվել է:** {created_at}")

        st.markdown("---")
        show_read_books_section(viewed_user)

        if st.button("🔙 Վերադառնալ իմ պրոֆիլին"):
            if 'viewed_profile' in st.session_state:
                del st.session_state.viewed_profile
            st.rerun()
        return

    # === ՍԵՓԱԿԱՆ ՊՐՈՖԻԼ ===
    viewed_user = current_user
    st.subheader("👤 Իմ Պրոֆիլը")

    # TAB-ԵՐԸ ՎԵՐԵՎՈՒՄ
    profile_tabs = st.tabs(["📋 Տեղեկություններ", "📊 Վիճակագրություն", "⚙️ Կարգավորումներ", "⏰ Հիշեցումներ"])

    with profile_tabs[0]:  # Տեղեկություններ
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
            if viewed_user.get('age'):
                st.write(f"**Տարիք:** {viewed_user['age']}")
            if viewed_user.get('profession'):
                st.write(f"**Մասնագիտություն:** {viewed_user['profession']}")
            if viewed_user.get('bio'):
                st.write(f"**Իմ մասին:** {viewed_user['bio']}")

            created_at = viewed_user.get('created_at', 'Անհայտ')[:10] if viewed_user.get('created_at') else 'Անհայտ'
            st.write(f"**Գրանցվել է:** {created_at}")

            st.markdown("**Ընթերցման Նախապատվություններ**")
            speed_display = f"{viewed_user['reading_speed']:.1f} էջ/րոպե" if viewed_user.get('reading_speed') is not None else "Դեռ չի հաշվվել"
            st.write(f"• Արագություն: {speed_display}")
            st.write(f"• Օրական ժամանակ: {viewed_user['daily_reading_time']} րոպե")
            st.write(f"• Լեզու: {viewed_user.get('preferred_language', 'Հայերեն')}")
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

    return
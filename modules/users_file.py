import streamlit as st
import json
import os
from datetime import datetime
from modules.data_file import get_user_sessions, add_reminder, get_user_reminder, check_reminder_time
from modules.utils import calculate_reading_plan

def show_statistics(user):
    st.subheader("📊 Իմ Ընթերցման Վիճակագրությունը")
    
    sessions = get_user_sessions(user['id'])
    
    if sessions:
        # Convert to DataFrame for easier analysis
        import pandas as pd
        sessions_df = pd.DataFrame(sessions)
        
        # Basic statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_sessions = len(sessions_df)
            st.metric("📖 Ընդհանուր Ընթերցումներ", total_sessions)
        
        with col2:
            total_pages = sessions_df['pages_read'].sum()
            st.metric("📄 Ընդհանուր Էջեր", total_pages)
        
        with col3:
            total_time = sessions_df['session_duration'].sum()
            hours = total_time // 60
            minutes = total_time % 60
            st.metric("⏱️ Ընդհանուր Ժամանակ", f"{hours}ժ {minutes}ր")
        
        with col4:
            avg_speed = total_pages / (total_time / 60) if total_time > 0 else 0
            st.metric("🚀 Միջին Արագություն", f"{avg_speed:.1f} էջ/ժամ")
        
        # Recent sessions
        st.subheader("🕒 Վերջին Ընթերցումները")
        for session in sessions[:10]:
            st.write(f"- **{session['book_title']}** - {session['pages_read']} էջ ({session['session_duration']} րոպե) - {session['created_at']}")
    
    else:
        st.info("📝 Դեռ չունեք ընթերցման տվյալներ։ Սկսեք ընթերցել և ավելացրեք ձեր առաջին ընթերցումը։")

def show_reminders(user):
    st.subheader("⏰ Ընթերցման Հիշեցումներ")
    
    st.info("""
    **📖 Ընթերցման հիշեցումներ** - Սահմանեք ձեր ամենօրյա ընթերցման ժամանակը, և մենք կհիշեցնենք ձեզ 5 րոպե առաջ։
    """)
    
    # Get existing reminder
    existing_reminder = get_user_reminder(user['id'])
    
    with st.form("reminder_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            default_time = existing_reminder['reminder_time'] if existing_reminder else "20:00"
            reminder_time = st.text_input(
                "🕐 Ընթերցման ժամանակ",
                value=default_time,
                help="Ընտրեք ժամանակ, երբ ցանկանում եք ընթերցել (օրինակ՝ 20:00)",
                placeholder="20:00"
            )
        
        with col2:
            # Days of week selection
            days_options = ["Երկուշաբթի", "Երեքշաբթի", "Չորեքշաբթի", "Հինգշաբթի", "Ուրբաթ", "Շաբաթ", "Կիրակի"]
            default_days = existing_reminder['days_of_week'] if existing_reminder else days_options
            selected_days = st.multiselect(
                "📅 Օրեր",
                options=days_options,
                default=default_days,
                help="Ընտրեք օրերը, երբ ցանկանում եք ստանալ հիշեցումներ"
            )
        
        # Active status
        is_active = st.checkbox(
            "Ակտիվացնել հիշեցումները",
            value=existing_reminder['is_active'] if existing_reminder else True,
            help="Հիշեցումները կաշխատեն միայն այն դեպքում, եթե ակտիվացված են"
        )
        
        submitted = st.form_submit_button("💾 Պահպանել Հիշեցումը")
        
        if submitted:
            if not selected_days:
                st.error("❌ Խնդրում եմ ընտրել առնվազն մեկ օր")
            elif not reminder_time:
                st.error("❌ Խնդրում եմ մուտքագրել ժամանակ")
            else:
                success = add_reminder(user['id'], reminder_time, selected_days, is_active)
                if success:
                    st.success("✅ Հիշեցումը հաջողությամբ պահպանված է!")
                    
                    # Show reminder summary
                    days_str = ", ".join(selected_days)
                    st.info(f"""
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
    
    # Current reminder status
    st.subheader("🔔 Ընթացիկ Հիշեցում")
    current_reminder = get_user_reminder(user['id'])
    
    if current_reminder and current_reminder['is_active']:
        days_str = ", ".join(current_reminder['days_of_week'])
        st.success(f"""
        **✅ Ակտիվ հիշեցում**
        - **⏰ Ժամանակ:** {current_reminder['reminder_time']}
        - **📅 Օրեր:** {days_str}
        - **⏱️ Հիշեցում:** 5 րոպե առաջ
        """)
        
        # Check if reminder should be shown now
        if check_reminder_time(user['id']):
            st.warning("""
            **🔔 Ընթերցման Ժամանակն է!**
            
            Մոտենում է ձեր ընթերցման ժամանակը: 
            Պատրաստվեք ընթերցել և վայելել ձեր ընտրված գիրքը:
            """)
            st.balloons()
    elif current_reminder and not current_reminder['is_active']:
        st.warning("""
        **🔕 Հիշեցումները անջատված են**
        
        Ձեր հիշեցումը պահպանված է, բայց այս պահին անջատված է:
        Ակտիվացրեք այն վերևի ձևում, եթե ցանկանում եք ստանալ հիշեցումներ:
        """)
    else:
        st.info("""
        **ℹ️ Դեռ չունեք ակտիվ հիշեցումներ**
        
        Սահմանեք ձեր առաջին հիշեցումը վերևի ձևում՝ 
        կանոնավոր ընթերցման սովորություն ձևավորելու համար:
        """)

def show_settings(user, books_df):
    st.subheader("⚙️ Օգտատիրոջ Կարգավորումներ")
    
    st.write(f"**Օգտանուն:** {user['username']}")
    st.write(f"**Էլ. Փոստ:** {user['email']}")
    st.write(f"**Գրանցման ամսաթիվ:** {user.get('created_at', 'Անհայտ')}")
    
    # Update preferences
    st.subheader("🔄 Թարմացնել Նախապատվությունները")
    
    new_reading_speed = st.slider(
        "Ընթերցման Արագություն (էջ/րոպե)",
        min_value=1,
        max_value=5,
        value=user['reading_speed']
    )
    
    new_daily_time = st.slider(
        "Օրական Ընթերցման Ժամանակ (րոպե)",
        min_value=15,
        max_value=180,
        value=user['daily_reading_time']
    )
    
    available_genres = books_df['genre'].unique().tolist() if not books_df.empty else []
    current_genres = user['preferred_genres'] if user['preferred_genres'] else []
    new_preferred_genres = st.multiselect(
        "Նախընտրելի Ժանրեր",
        options=available_genres,
        default=current_genres
    )
    
    # Language preference
    current_language = user.get('preferred_language', 'Հայերեն')
    new_preferred_language = st.selectbox(
        "Նախընտրելի Լեզու",
        ["Հայերեն", "Ռուսերեն", "Անգլերեն"],
        index=["Հայերեն", "Ռուսերեն", "Անգլերեն"].index(current_language) if current_language in ["Հայերեն", "Ռուսերեն", "Անգլերեն"] else 0
    )
    
    if st.button("💾 Պահպանել Կարգավորումները"):
        try:
            # Load current users
            from modules.auth_file import load_users, save_users
            users = load_users()
            
            if user['username'] in users:
                # Update user preferences
                users[user['username']]['reading_speed'] = new_reading_speed
                users[user['username']]['daily_reading_time'] = new_daily_time
                users[user['username']]['preferred_genres'] = new_preferred_genres
                users[user['username']]['preferred_language'] = new_preferred_language
                
                save_users(users)
                
                # Update session state
                st.session_state.user = users[user['username']].copy()
                st.session_state.user['username'] = user['username']
                st.session_state.user['id'] = user['username']
                
                st.success("✅ Կարգավորումները պահպանված են!")
                st.rerun()
            else:
                st.error("❌ Օգտատերը չի գտնվել")
                
        except Exception as e:
            st.error(f"❌ Սխալ կարգավորումները պահպանելիս: {e}")

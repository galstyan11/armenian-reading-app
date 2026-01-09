# modules/auth_file.py
import streamlit as st
import hashlib
import json
import os
from datetime import datetime
from modules.custom_alerts import custom_success, custom_info


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    try:
        if os.path.exists('data/users.json'):
            with open('data/users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}


def save_users(users):
    os.makedirs('data', exist_ok=True)
    with open('data/users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def create_user(username, email, password, daily_reading_time=30, preferred_genres=None,
                preferred_language='Հայերեն', age=None, profession=None, bio=None):
    users = load_users()
    
    if username in users:
        st.error("❌ Այս օգտանունն արդեն գոյություն ունի")
        return False
    
    for user_data in users.values():
        if user_data.get('email') == email:
            st.error("❌ Այս էլ․ փոստն արդեն գոյություն ունի")
            return False
    
    users[username] = {
        'email': email,
        'password': hash_password(password),
        'reading_speed': None,  # Իրական արագությունը կհաշվվի միայն սեսիաներից
        'daily_reading_time': daily_reading_time,
        'preferred_genres': preferred_genres or [],
        'preferred_language': preferred_language,
        'age': age,
        'profession': profession,
        'bio': bio,
        'created_at': datetime.now().isoformat()
    }
    
    save_users(users)
    return True


def verify_user(username, password):
    users = load_users()
    
    if username in users and users[username]['password'] == hash_password(password):
        user_data = users[username].copy()
        user_data['username'] = username
        user_data['id'] = username
        return user_data
    
    return None


def logout():
    st.session_state.user = None
    st.session_state.page = "login"


def show_auth_page(books_df):
    st.title("🔐 Մուտք Գործել կամ Գրանցվել")
    
    tab1, tab2 = st.tabs(["🚪 Մուտք Գործել", "📝 Գրանցվել"])
    
    with tab1:
        st.subheader("Մուտք Գործել")
        login_username = st.text_input("Օգտանուն", key="login_username")
        login_password = st.text_input("Գաղտնաբառ", type="password", key="login_password")
        
        if st.button("Մուտք Գործել", key="login_btn"):
            if login_username.strip() and login_password.strip():
                user = verify_user(login_username, login_password)
                if user:
                    st.session_state.user = user
                    st.session_state.page = "main"
                    custom_success(f"✅ Բարի գալուստ, {user['username']}!")
                    st.rerun()
                else:
                    st.error("❌ Սխալ օգտանուն կամ գաղտնաբառ")
            else:
                st.error("⚠️ Խնդրում եմ մուտքագրեք օգտանունը և գաղտնաբառը")
                
    with tab2:
        st.subheader("Նոր Գրանցում")
        custom_info("📝 Մուտքագրեք ձեր տվյալները նոր գրանցման համար")
        
        reg_username = st.text_input("Օգտանուն *", key="reg_username")
        reg_email = st.text_input("Էլ. Փոստ *", key="reg_email")
        reg_password = st.text_input("Գաղտնաբառ *", type="password", key="reg_password",
                                   help="Գաղտնաբառը պետք է լինի առնվազն 4 նիշ")
        reg_confirm_password = st.text_input("Հաստատել Գաղտնաբառը *", type="password", key="reg_confirm_password")
        
        reg_age = st.number_input("Տարիք", min_value=13, max_value=120, value=None, step=1, key="reg_age")
        reg_profession = st.text_input("Մասնագիտություն", key="reg_profession")
        reg_bio = st.text_area("Պատմեք ձեր մասին", height=100, key="reg_bio")
        
        st.subheader("Ընթերցման Նախապատվություններ")
        
        reg_daily_time = st.slider("Օրական Ընթերցման Ժամանակ (րոպե)", 15, 180, 30, key="reg_time")
        
        available_genres = books_df['genre'].unique().tolist() if not books_df.empty else []
        reg_preferred_genres = st.multiselect(
            "Նախընտրելի Ժանրեր",
            available_genres,
            default=[],
            placeholder="Կարող եք ընտրել մի քանիսը",
            key="reg_genres"
        )
        
        reg_preferred_language = st.selectbox(
            "Նախընտրելի Լեզու",
            ["Հայերեն", "Ռուսերեն", "Անգլերեն"],
            key="reg_language"
        )
        
        if st.button("📝 Գրանցվել", key="reg_btn", type="primary"):
            if not reg_username.strip():
                st.error("❌ Խնդրում եմ մուտքագրեք օգտանուն")
            elif not reg_email.strip():
                st.error("❌ Խնդրում եմ մուտքագրեք էլ. փոստի հասցե")
            elif not reg_password.strip():
                st.error("❌ Խնդրում եմ մուտքագրեք գաղտնաբառ")
            elif reg_password != reg_confirm_password:
                st.error("❌ Գաղտնաբառերը չեն համընկնում")
            elif len(reg_password) < 4:
                st.error("❌ Գաղտնաբառը պետք է լինի առնվազն 4 նիշ")
            else:
                success = create_user(
                    reg_username.strip(),
                    reg_email.strip(),
                    reg_password,
                    daily_reading_time=reg_daily_time,
                    preferred_genres=reg_preferred_genres,
                    preferred_language=reg_preferred_language,
                    age=reg_age if reg_age is not None else None,
                    profession=reg_profession.strip() if reg_profession.strip() else None,
                    bio=reg_bio.strip() if reg_bio.strip() else None
                )
                if success:
                    new_user = verify_user(reg_username.strip(), reg_password)
                    if new_user:
                        st.session_state.user = new_user
                        st.session_state.page = "main"
                        custom_success("✅ Գրանցումը հաջող էր! Բարի գալուստ!")
                        st.rerun()
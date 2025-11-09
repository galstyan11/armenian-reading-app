import streamlit as st
import hashlib
import json
import os
from datetime import datetime

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file"""
    try:
        if os.path.exists('data/users.json'):
            with open('data/users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_users(users):
    """Save users to JSON file"""
    os.makedirs('data', exist_ok=True)
    with open('data/users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def create_user(username, email, password, reading_speed=2, daily_reading_time=30, preferred_genres=None, preferred_language='Հայերեն'):
    """Create new user"""
    users = load_users()
    
    if username in users:
        st.error("❌ Այս օգտանունն արդեն գոյություն ունի")
        return False
    
    # Check if email already exists
    for user_data in users.values():
        if user_data.get('email') == email:
            st.error("❌ Այս էլ․ փոստն արդեն գոյություն ունի")
            return False
    
    users[username] = {
        'email': email,
        'password': hash_password(password),
        'reading_speed': reading_speed,
        'daily_reading_time': daily_reading_time,
        'preferred_genres': preferred_genres or [],
        'preferred_language': preferred_language,
        'created_at': str(datetime.now())
    }
    
    save_users(users)
    return True

def verify_user(username, password):
    """Verify user credentials"""
    users = load_users()
    
    if username in users and users[username]['password'] == hash_password(password):
        user_data = users[username].copy()
        user_data['username'] = username
        user_data['id'] = username  # Use username as ID for file-based system
        return user_data
    
    return None

def get_current_user():
    return st.session_state.get('user')

# ADD THIS MISSING FUNCTION
def logout():
    """Logout the current user"""
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
                    st.success(f"✅ Բարի գալուստ, {user['username']}!")
                    st.rerun()
                else:
                    st.error("❌ Սխալ օգտանուն կամ գաղտնաբառ")
            else:
                st.error("⚠️ Խնդրում եմ մուտքագրեք օգտանունը և գաղտնաբառը")
    
    with tab2:
        st.subheader("Նոր Գրանցում")
        
        st.info("📝 Մուտքագրեք ձեր տվյալները նոր գրանցման համար")
        
        reg_username = st.text_input("Նոր Օգտանուն *", key="reg_username")
        reg_email = st.text_input("Էլ. Փոստ *", key="reg_email")
        reg_password = st.text_input("Գաղտնաբառ *", type="password", key="reg_password", 
                                   help="Գաղտնաբառը պետք է լինի առնվազն 4 նիշ")
        reg_confirm_password = st.text_input("Հաստատել Գաղտնաբառը *", type="password", key="reg_confirm_password")
        
        st.subheader("Ընթերցման Նախապատվություններ")
        reg_reading_speed = st.slider("Ընթերցման Արագություն (էջ/րոպե)", 1, 5, 2, key="reg_speed")
        reg_daily_time = st.slider("Օրական Ընթերցման Ժամանակ (րոպե)", 15, 180, 30, key="reg_time")
        
        # Load available genres from books
        available_genres = books_df['genre'].unique().tolist() if not books_df.empty else []
        reg_preferred_genres = st.multiselect("Նախընտրելի Ժանրեր", available_genres, key="reg_genres")

        reg_preferred_language = st.selectbox(
            "Նախընտրելի Լեզու",
            ["Հայերեն", "Ռուսերեն", "Անգլերեն"],
            key="reg_language"
        )

        if st.button("📝 Գրանցվել", key="reg_btn", type="primary"):
            # Validation
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
                success = create_user(reg_username, reg_email, reg_password, reg_reading_speed, reg_daily_time, reg_preferred_genres, reg_preferred_language)
                if success:
                    # Get the newly created user
                    new_user = verify_user(reg_username, reg_password)
                    if new_user:
                        st.session_state.user = new_user
                        st.session_state.page = "main"
                        st.success("✅ Գրանցումը հաջող էր!")
                        st.rerun()
                    else:
                        st.error("❌ Չհաջողվեց բեռնել օգտատիրոջ տվյալները")

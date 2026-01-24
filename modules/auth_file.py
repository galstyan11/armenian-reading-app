# modules/auth_file.py
import streamlit as st
import hashlib
import json
import os

from modules.custom_alerts import custom_success, custom_info
from modules.time_utils import iso_now_utc


def hash_password(password: str) -> str:
    """Simple SHA-256 hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()


def load_users() -> dict:
    """Load all users from JSON file"""
    try:
        if os.path.exists('data/users.json'):
            with open('data/users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}


def save_users(users: dict):
    """Save users dictionary to JSON file"""
    os.makedirs('data', exist_ok=True)
    try:
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")


def create_user(
    username: str,
    email: str,
    password: str,
    daily_reading_time: int = 30,
    preferred_genres: list = None,
    preferred_language: str = 'Հայերեն',
    age: int = None,
    profession: str = None,
    bio: str = None
) -> bool:
    """
    Create a new user account.
    Returns True on success, False if username/email already exists.
    """
    users = load_users()

    # Check for existing username
    if username in users:
        st.error("Այս օգտանունն արդեն գոյություն ունի")
        return False

    # Check for existing email
    if any(user_data.get('email') == email for user_data in users.values()):
        st.error("Այս էլ․ փոստն արդեն գոյություն ունի")
        return False

    users[username] = {
        'email': email,
        'password': hash_password(password),
        'reading_speed': None, 
        'daily_reading_time': daily_reading_time,
        'preferred_genres': preferred_genres or [],
        'preferred_language': preferred_language,
        'age': age,
        'profession': profession,
        'bio': bio,
        'created_at': iso_now_utc(),  
    }

    save_users(users)
    return True


def verify_user(username: str, password: str) -> dict | None:
    """Verify credentials and return user data (without password) or None"""
    users = load_users()

    if username in users and users[username]['password'] == hash_password(password):
        user_data = users[username].copy()
        user_data['username'] = username
        user_data['id'] = username  # Using username as ID (consistent with your app)
        return user_data

    return None


def logout():
    """Clear session state and redirect to login"""
    st.session_state.user = None
    st.session_state.page = "login"
    st.rerun()


def show_auth_page(books_df):
    st.title("🔐 Մուտք Գործել կամ Գրանցվել")

    tab1, tab2 = st.tabs(["🚪 Մուտք Գործել", "📝 Գրանցվել"])

    with tab1:
        st.subheader("Մուտք Գործել")

        login_username = st.text_input("Օգտանուն", key="login_username")
        login_password = st.text_input("Գաղտնաբառ", type="password", key="login_password")

        if st.button("Մուտք Գործել", key="login_btn"):
            if login_username.strip() and login_password.strip():
                user = verify_user(login_username.strip(), login_password)
                if user:
                    st.session_state.user = user
                    st.session_state.page = "main"
                    custom_success(f"✅ Բարի գալուստ, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Սխալ օգտանուն կամ գաղտնաբառ")
            else:
                st.error("Խնդրում եմ մուտքագրեք օգտանունը և գաղտնաբառը")

    with tab2:
        st.subheader("Նոր Գրանցում")
        custom_info("📝 Մուտքագրեք ձեր տվյալները նոր գրանցման համար")

        reg_username = st.text_input("Օգտանուն *", key="reg_username")
        reg_email = st.text_input("Էլ. Փոստ *", key="reg_email")
        reg_password = st.text_input(
            "Գաղտնաբառ *",
            type="password",
            key="reg_password",
            help="Գաղտնաբառը պետք է լինի առնվազն 4 նիշ"
        )
        reg_confirm_password = st.text_input("Հաստատել Գաղտնաբառը *", type="password", key="reg_confirm_password")

        reg_age = st.number_input("Տարիք", min_value=13, max_value=120, value=None, step=1, key="reg_age")
        reg_profession = st.text_input("Մասնագիտություն", key="reg_profession")
        reg_bio = st.text_area("Պատմեք ձեր մասին", height=100, key="reg_bio")

        st.subheader("Ընթերցման Նախապատվություններ")

        reg_daily_time = st.slider(
            "Օրական Ընթերցման Ժամանակ (րոպե)",
            15, 180, 30,
            key="reg_time"
        )

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
                st.error("Խնդրում եմ մուտքագրեք օգտանուն")
            elif not reg_email.strip():
                st.error("Խնդրում եմ մուտքագրեք էլ. փոստի հասցե")
            elif not reg_password.strip():
                st.error("Խնդրում եմ մուտքագրեք գաղտնաբառ")
            elif reg_password != reg_confirm_password:
                st.error("Գաղտնաբառերը չեն համընկնում")
            elif len(reg_password) < 4:
                st.error("Գաղտնաբառը պետք է լինի առնվազն 4 նիշ")
            else:
                success = create_user(
                    username=reg_username.strip(),
                    email=reg_email.strip(),
                    password=reg_password,
                    daily_reading_time=reg_daily_time,
                    preferred_genres=reg_preferred_genres,
                    preferred_language=reg_preferred_language,
                    age=reg_age if reg_age is not None else None,
                    profession=reg_profession.strip() or None,
                    bio=reg_bio.strip() or None
                )
                if success:
                    new_user = verify_user(reg_username.strip(), reg_password)
                    if new_user:
                        st.session_state.user = new_user
                        st.session_state.page = "main"
                        custom_success("✅ Գրանցումը հաջող էր! Բարի գալուստ!")
                        st.rerun()
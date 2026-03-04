# modules/auth_file.py
from datetime import datetime, timezone

import streamlit as st
import hashlib
from typing import Dict, Optional, List

from modules.db import query, json_str, json_obj
from modules.custom_alerts import custom_success, custom_info



def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, stored_hash: str) -> bool:
    return hash_password(plain_password) == stored_hash

def create_user(
    username: str,
    email: str,
    password: str,
    daily_reading_time: int = 30,
    preferred_genres: Optional[List[str]] = None,
    preferred_languages: Optional[List[str]] = None,
    age: Optional[int] = None,
    profession: Optional[str] = None,
    bio: Optional[str] = None
) -> bool:
    username = username.strip()
    email = email.strip()

    if not username or not email or not password:
        st.error("Բոլոր պարտադիր դաշտերը լրացված չեն")
        return False

    # 1. Check if user/email exists
    try:
        existing = query(
            """
            SELECT username, email 
            FROM users 
            WHERE username = %s OR email = %s
            LIMIT 2
            """,
            (username, email),
            fetch=True
        )
    except Exception as e:
        st.error(f"Սխալ ստուգելիս՝ {str(e)}")
        print(f"Duplicate check error: {e}")
        return False

    if existing:
        for row in existing:
            if row['username'] == username:
                st.error("Այս օգտանունն արդեն գոյություն ունի")
                return False
            if row['email'] == email:
                st.error("Այս էլ․ փոստն արդեն գոյություն ունի")
                return False

    # Clean fields
    profession_clean = (str(profession or "")).strip() or None
    bio_clean = (str(bio or "")).strip() or None

    # 2. Try to insert
    try:
        success = query("""
            INSERT INTO users (
                username, email, password_hash, daily_reading_time,
                preferred_genres, preferred_languages,
                age, profession, bio, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username,
            email,
            hash_password(password),
            daily_reading_time,
            json_str(preferred_genres or []),
            json_str(preferred_languages or []),
            age,
            profession_clean,
            bio_clean,
            datetime.now(timezone.utc)
        ))

        if success:
            custom_success("Գրանցումը հաջող էր!")
            print(f"User created: {username}")
            return True
        else:
            st.error("Չհաջողվեց ավելացնել օգտատերը MySQL-ում")
            print("Insert returned False — check db connection / table structure")
            return False

    except Exception as insert_error:
        st.error(f"Տվյալների բազայի սխալ գրանցման ժամանակ: {str(insert_error)}")
        print(f"Insert error: {insert_error}")
        return False

def verify_user(username: str, password: str) -> Optional[Dict]:
    """
    Verify username + password.
    Returns user dict (with id = username) or None.
    """
    user = query("""
        SELECT 
            username, email, password_hash,
            daily_reading_time, reading_speed,
            preferred_genres, preferred_languages,
            age, profession, bio, created_at
        FROM users 
        WHERE username = %s
        LIMIT 1
    """, (username.strip(),), fetch=True, one=True)

    if not user:
        return None

    if user['password_hash'] != hash_password(password):
        return None

    # Convert JSON strings → python lists
    user['preferred_genres']    = json_obj(user['preferred_genres'])
    user['preferred_languages'] = json_obj(user['preferred_languages'])

    # Keep your existing convention
    user['id'] = user['username']

    return user


def load_friends(username: str) -> List[str]:
    """Return list of friend's usernames"""
    rows = query("""
        SELECT 
            CASE 
                WHEN user1 = %s THEN user2 
                ELSE user1 
            END AS friend
        FROM friendships
        WHERE user1 = %s OR user2 = %s
    """, (username, username, username), fetch=True)

    return [row['friend'] for row in rows]


def add_friend(username: str, friend_username: str) -> bool:
    """Add friend (mutual, stored sorted to avoid duplicates)"""
    if username == friend_username:
        return False

    u1, u2 = sorted([username.strip(), friend_username.strip()])

    # INSERT IGNORE prevents duplicate entries
    return bool(query("""
        INSERT IGNORE INTO friendships (user1, user2, created_at)
        VALUES (%s, %s, %s)
    """, (u1, u2, datetime.now(timezone.utc))))


def remove_friend(username: str, friend_username: str) -> bool:
    """Remove friend relationship"""
    u1, u2 = sorted([username.strip(), friend_username.strip()])

    return bool(query("""
        DELETE FROM friendships 
        WHERE user1 = %s AND user2 = %s
    """, (u1, u2)))


def logout():
    """Clear session and go back to login"""
    st.session_state.user = None
    st.session_state.page = "login"
    st.rerun()


def show_auth_page(books_df):
    """Login / Register UI — unchanged logic, just using new functions"""
    st.markdown(
        """<div style="font-size: 28px; font-weight: 400; line-height: 1.3;">
                Բարի գալուստ
            </div>
            <div style="font-size: 28px; font-weight: 400; line-height: 1.3;">
                <span style="color: #f77214; font-weight: 700;">ԿԱՐԴԱ</span>
                <span style="color: #672f1b; font-weight: 700;"> ինձ հետ</span> հավելված!
            </div>""",
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["Մուտք Գործել", "Գրանցվել"])

    with tab1:
        st.subheader("Մուտք Գործել")

        login_username = st.text_input("Օգտանուն", key="login_username")
        login_password = st.text_input("Գաղտնաբառ", type="password", key="login_password")

        if st.button("Մուտք Գործել", key="login_btn"):
            if login_username.strip() and login_password.strip():
                user = verify_user(login_username.strip(), login_password.strip())
                if user:
                    st.session_state.user = user
                    st.session_state.page = "main"
                    custom_success(f"Բարի գալուստ, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Սխալ օգտանուն կամ գաղտնաբառ")
            else:
                st.error("Խնդրում եմ մուտքագրեք օգտանունը և գաղտնաբառը")

    with tab2:
        st.subheader("Նոր Գրանցում")
        custom_info("Մուտքագրեք ձեր տվյալները նոր գրանցման համար")

        reg_username = st.text_input("Օգտանուն *", key="reg_username")
        reg_email = st.text_input("Էլ. Փոստ *", key="reg_email")
        reg_password = st.text_input("Գաղտնաբառ *", type="password", key="reg_password",
                                     help="Առնվազն 4 նիշ")
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

        reg_preferred_languages = st.multiselect(
            "Նախընտրելի Լեզուներ",
            ["Հայերեն", "Ռուսերեն", "Անգլերեն"],
            default=[],
            placeholder="Կարող եք ընտրել մեկ կամ ավելի լեզուներ",
            key="reg_languages"
        )

        if st.button("Գրանցվել", key="reg_btn", type="primary"):
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
                    preferred_languages=reg_preferred_languages,
                    age=reg_age if reg_age else None,
                    profession=reg_profession,
                    bio=reg_bio
                )
                if success:
                    new_user = verify_user(reg_username.strip(), reg_password)
                    if new_user:
                        st.session_state.user = new_user
                        st.session_state.page = "main"
                        custom_success("Գրանցումը հաջող էր! Բարի գալուստ!")
                        st.rerun()
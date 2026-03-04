# modules/data_file.py
from modules.db import query, json_str, json_obj
from modules.time_utils import ARMENIA_TZ
from typing import List, Dict, Optional, Tuple
import streamlit as st
from datetime import datetime, timezone

# ── reading_sessions ──────────────────────────────────────────────────────
def add_reading_session(
    user_id: str,
    book_id: str,
    pages_read: int,
    session_duration: int,
    book_title: str
) -> bool:
    """Save a new reading session"""
    book_id = str(book_id).strip()

    return bool(query("""
        INSERT INTO reading_sessions (
            user_id, book_id, book_title,
            pages_read, session_duration, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        book_id,
        book_title,
        pages_read,
        session_duration,
        datetime.now(timezone.utc)
    )))


def get_user_sessions(user_id: str) -> List[Dict]:
    """Get all reading sessions for a user"""
    return query("""
        SELECT 
            id, book_id, book_title, pages_read,
            session_duration, created_at
        FROM reading_sessions
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,), fetch=True)


# ── book_comments ─────────────────────────────────────────────────────────
def add_book_comment(
    book_id: str,
    username: str,
    comment_text: str,
    rating: Optional[int] = None
) -> bool:
    """Add comment to a book"""
    return bool(query("""
        INSERT INTO book_comments (
            book_id, user_id, comment_text, rating, created_at
        ) VALUES (%s, %s, %s, %s, %s)
    """, (
        book_id,
        username,
        comment_text.strip(),
        rating,
        datetime.now(timezone.utc)
    )))


def get_book_comments(book_id: str) -> List[Dict]:
    """Get all comments for a book"""
    return query("""
        SELECT 
            id, 
            user_id AS username,
            comment_text, 
            rating, 
            created_at
        FROM book_comments
        WHERE book_id = %s
        ORDER BY created_at DESC
    """, (book_id,), fetch=True)


# ── speed_calculation ─────────────────────────────────────────────────────
def calculate_reading_speed(user_id: str) -> Optional[float]:
    sessions = query("""
        SELECT pages_read, session_duration
        FROM reading_sessions
        WHERE user_id = %s
          AND session_duration > 0
    """, (user_id,), fetch=True)

    if not sessions:
        return None

    total_pages = sum(s['pages_read'] for s in sessions)
    total_minutes = sum(s['session_duration'] for s in sessions)

    if total_minutes <= 0:
        return None

    speed = total_pages / total_minutes
    return float(round(max(0.5, min(5.0, speed)), 1))


def update_reading_speed(user_id: str) -> bool:
    new_speed = calculate_reading_speed(user_id)
    if new_speed is None:
        return False

    success = query("""
        UPDATE users
        SET reading_speed = %s
        WHERE username = %s
    """, (new_speed, user_id))

    if success and st.session_state.get("user") and st.session_state.user.get("id") == user_id:
        st.session_state.user["reading_speed"] = new_speed

    return bool(success)


# ── reading_reminders ─────────────────────────────────────────────────────
def add_reminder(
    user_id: str,
    reminder_time: str,
    days_of_week: List[str],
    is_active: bool = True
) -> bool:
    now = datetime.now(timezone.utc)

    return bool(query("""
        INSERT INTO reading_reminders (
            user_id, reminder_time, days_of_week,
            is_active, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            reminder_time = VALUES(reminder_time),
            days_of_week  = VALUES(days_of_week),
            is_active     = VALUES(is_active),
            updated_at    = VALUES(updated_at)
    """, (
        user_id,
        reminder_time.strip(),
        json_str(days_of_week),
        is_active,
        now,
        now
    )))


def get_user_reminder(user_id: str) -> Optional[Dict]:
    row = query("""
        SELECT 
            reminder_time, days_of_week, is_active, created_at
        FROM reading_reminders
        WHERE user_id = %s
        LIMIT 1
    """, (user_id,), fetch=True, one=True)

    if row:
        row['days_of_week'] = json_obj(row['days_of_week'])
    return row


def check_reminder_time(user_id: str) -> bool:
    reminder = get_user_reminder(user_id)
    if not reminder or not reminder.get('is_active', True):
        return False
    
    # Use explicit Yerevan time
    now_local = datetime.now(ARMENIA_TZ)
    
    today_en = now_local.strftime("%A")
    day_map = {
        "Monday": "Երկուշաբթի",
        "Tuesday": "Երեքշաբթի",
        "Wednesday": "Չորեքշաբթի",
        "Thursday": "Հինգշաբթի",
        "Friday": "Ուրբաթ",
        "Saturday": "Շաբաթ",
        "Sunday": "Կիրակի",
    }
    today_arm = day_map.get(today_en)
    
    if today_arm not in reminder['days_of_week']:
        return False
    
    try:
        h, m = map(int, reminder['reminder_time'].split(':'))
        return now_local.hour == h and now_local.minute == m
    except:
        return False


# ── creative_works ────────────────────────────────────────────────────────
def add_creative_work(
    user_id: str,
    title: str,
    content_type: str,
    content: str,
    genre: str = "Ընդհանուր",
    description: Optional[str] = None,
    is_public: bool = True,
    username: str = ""
) -> Optional[int]:
    work_id = query("""
        INSERT INTO creative_works (
            user_id, username, title, content_type,
            content, genre, description, is_public, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        username or user_id,
        title.strip(),
        content_type,
        content.strip(),
        genre.strip(),
        description.strip() if description else None,
        is_public,
        datetime.now(timezone.utc)
    ))

    return work_id if isinstance(work_id, int) else None


def get_creative_works(
    user_id: Optional[str] = None,
    public_only: bool = False,
    viewer_id: Optional[str] = None
) -> List[Dict]:
    sql = "SELECT * FROM creative_works"
    params = []
    conditions = []

    if user_id:
        conditions.append("user_id = %s")
        params.append(user_id)

    if public_only:
        conditions.append("is_public = TRUE")

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY created_at DESC"

    works = query(sql, tuple(params), fetch=True)
    return works


def add_creative_work_comment(
    creative_work_id: int,
    username: str,
    comment_text: str
) -> bool:
    """Add comment to a creative work"""
    return bool(query("""
        INSERT INTO creative_work_comments (
            creative_work_id, user_id, comment_text, created_at
        ) VALUES (%s, %s, %s, %s)
    """, (
        creative_work_id,
        username,
        comment_text.strip(),
        datetime.now(timezone.utc)
    )))


def get_creative_work_comments(creative_work_id: int) -> List[Dict]:
    return query("""
        SELECT
            id,
            user_id AS username,
            comment_text,
            created_at
        FROM creative_work_comments
        WHERE creative_work_id = %s
        ORDER BY created_at DESC
    """, (creative_work_id,), fetch=True)


def delete_creative_work(work_id: int, user_id: str) -> Tuple[bool, str]:
    work = query(
        "SELECT id FROM creative_works WHERE id = %s AND user_id = %s LIMIT 1",
        (work_id, user_id),
        fetch=True,
        one=True
    )

    if not work:
        return False, "Միայն կարող եք ջնջել ձեր սեփական ստեղծագործությունները"

    success = query("DELETE FROM creative_works WHERE id = %s", (work_id,))

    if success:
        return True, "Ստեղծագործությունը հաջողությամբ ջնջված է"
    else:
        return False, "Ջնջման սխալ"
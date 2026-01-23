# modules/data_file.py
import json
import os
import streamlit as st
from datetime import datetime, timezone
import pytz

from modules.auth_file import load_users, save_users
from modules.time_utils import iso_now_utc, parse_iso, to_armenia, format_armenia


def ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs("data", exist_ok=True)


def load_data(filename, default=None):
    """Load data from JSON file"""
    if default is None:
        default = []

    ensure_data_dir()
    filepath = f"data/{filename}.json"

    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")

    return default


def save_data(filename, data):
    """Save data to JSON file"""
    ensure_data_dir()
    filepath = f"data/{filename}.json"

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving {filename}: {e}")


def add_reading_session(user_id, book_id, pages_read, session_duration, book_title):
    sessions = load_data("reading_sessions")

    session = {
        "id": len(sessions) + 1,
        "user_id": user_id,
        "book_id": book_id,
        "book_title": book_title,
        "pages_read": pages_read,
        "session_duration": session_duration,
        "created_at": iso_now_utc(),  # UTC ISO string
    }

    sessions.append(session)
    save_data("reading_sessions", sessions)
    return True


def get_user_sessions(user_id):
    sessions = load_data("reading_sessions")
    return [s for s in sessions if s["user_id"] == user_id]


def add_book_comment(user_id, book_id, comment_text, rating, username):
    comments = load_data("book_comments")

    comment = {
        "id": len(comments) + 1,
        "user_id": user_id,
        "username": username,
        "book_id": book_id,
        "comment_text": comment_text,
        "rating": rating,
        "created_at": iso_now_utc(),
    }

    comments.append(comment)
    save_data("book_comments", comments)
    return True


def get_book_comments(book_id):
    comments = load_data("book_comments")
    return [c for c in comments if c["book_id"] == book_id]


def add_creative_work(
    user_id,
    title,
    content_type,
    content,
    genre,
    description,
    is_public,
    username,
):
    works = load_data("creative_works")

    work = {
        "id": len(works) + 1,
        "user_id": user_id,
        "username": username,
        "title": title,
        "content_type": content_type,
        "content": content,
        "genre": genre or "Ընդհանուր",
        "description": description,
        "is_public": is_public,
        "created_at": iso_now_utc(),
    }

    works.append(work)
    save_data("creative_works", works)
    return work["id"]


def get_creative_works(user_id=None, public_only=False, viewer_id=None):
    works = load_data("creative_works")

    if user_id is not None:
        filtered = [w for w in works if w["user_id"] == user_id]
        if public_only and viewer_id is not None and user_id != viewer_id:
            filtered = [w for w in filtered if w["is_public"]]
        return filtered

    if public_only:
        return [w for w in works if w["is_public"]]

    return works


def add_creative_work_comment(creative_work_id, user_id, comment_text, username):
    comments = load_data("creative_work_comments")

    comment = {
        "id": len(comments) + 1,
        "creative_work_id": creative_work_id,
        "user_id": user_id,
        "username": username,
        "comment_text": comment_text,
        "created_at": iso_now_utc(),
    }

    comments.append(comment)
    save_data("creative_work_comments", comments)
    return True


def get_creative_work_comments(creative_work_id):
    comments = load_data("creative_work_comments")
    return [c for c in comments if c["creative_work_id"] == creative_work_id]


def add_reminder(user_id, reminder_time, days_of_week, is_active=True):
    reminders = load_data("reading_reminders")
    user_id = str(user_id)

    # Remove old reminder for this user (if exists)
    reminders = [r for r in reminders if r["user_id"] != user_id]

    reminder = {
        "id": len(reminders) + 1,
        "user_id": user_id,
        "reminder_time": reminder_time.strip(),
        "days_of_week": days_of_week,
        "is_active": is_active,
        "created_at": iso_now_utc(),
    }

    reminders.append(reminder)
    save_data("reading_reminders", reminders)
    return True


def get_user_reminder(user_id):
    reminders = load_data("reading_reminders")
    user_id = str(user_id)

    user_reminders = [r for r in reminders if r["user_id"] == user_id]
    return user_reminders[0] if user_reminders else None


def check_reminder_time(user_id):
    reminders = load_data("reading_reminders")
    user_id = str(user_id)

    reminder = next(
        (r for r in reminders if r["user_id"] == user_id and r.get("is_active", True)),
        None,
    )

    if not reminder:
        return False

    # Armenia local time
    now_local = datetime.now(timezone.utc).astimezone(pytz.timezone("Asia/Yerevan"))

    today_map = {
        "Monday": "Երկուշաբթի",
        "Tuesday": "Երեքշաբթի",
        "Wednesday": "Չորեքշաբթի",
        "Thursday": "Հինգշաբթի",
        "Friday": "Ուրբաթ",
        "Saturday": "Շաբաթ",
        "Sunday": "Կիրակի",
    }

    today_arm = today_map.get(now_local.strftime("%A"), None)
    if today_arm is None or today_arm not in reminder["days_of_week"]:
        return False

    try:
        h, m = map(int, reminder["reminder_time"].split(":"))
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return False
    except (ValueError, TypeError):
        return False

    return now_local.hour == h and now_local.minute == m


def delete_creative_work(work_id, user_id):
    try:
        works = load_data("creative_works")
        comments = load_data("creative_work_comments")

        work_to_delete = next(
            (w for w in works if w["id"] == work_id and w["user_id"] == user_id),
            None,
        )

        if not work_to_delete:
            return False, "❌ Միայն կարող եք ջնջել ձեր սեփական ստեղծագործությունները"

        works = [w for w in works if w["id"] != work_id]
        comments = [c for c in comments if c["creative_work_id"] != work_id]

        save_data("creative_works", works)
        save_data("creative_work_comments", comments)

        return True, "✅ Ստեղծագործությունը հաջողությամբ ջնջված է"

    except Exception as e:
        return False, f"❌ Ջնջման սխալ: {str(e)}"


def calculate_reading_speed(user_id):
    sessions = get_user_sessions(user_id)

    if not sessions:
        return None

    total_pages = sum(s["pages_read"] for s in sessions)
    total_minutes = sum(s["session_duration"] for s in sessions)

    if total_minutes <= 0:
        return None

    speed = total_pages / total_minutes
    return round(max(0.5, min(5.0, speed)), 1)


def update_reading_speed(user_id):
    try:
        new_speed = calculate_reading_speed(user_id)
        users = load_users()

        if user_id in users:
            users[user_id]["reading_speed"] = new_speed
            save_users(users)

            # Update session state if current user
            if (
                st.session_state.get("user")
                and st.session_state.user.get("id") == user_id
            ):
                st.session_state.user["reading_speed"] = new_speed

            return True

        return False

    except Exception as e:
        print(f"Error updating reading speed: {e}")
        return False
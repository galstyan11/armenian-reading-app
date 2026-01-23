# modules/data_file.py
import json
import os
from datetime import datetime
import streamlit as st
from modules.auth_file import load_users, save_users  # Ավելացրել ենք import-ը

def ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs('data', exist_ok=True)

def load_data(filename, default=[]):
    """Load data from JSON file"""
    ensure_data_dir()
    filepath = f'data/{filename}.json'
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return default

def save_data(filename, data):
    """Save data to JSON file"""
    ensure_data_dir()
    filepath = f'data/{filename}.json'
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

# Reading Sessions
def add_reading_session(user_id, book_id, pages_read, session_duration, book_title):
    """Add reading session"""
    sessions = load_data('reading_sessions', [])
    
    session = {
        'id': len(sessions) + 1 if sessions else 1,
        'user_id': user_id,
        'book_id': book_id,
        'book_title': book_title,
        'pages_read': pages_read,
        'session_duration': session_duration,
        'created_at': datetime.now().isoformat()
    }
    
    sessions.append(session)
    save_data('reading_sessions', sessions)
    return True

def get_user_sessions(user_id):
    """Get user's reading sessions"""
    sessions = load_data('reading_sessions', [])
    return [s for s in sessions if s['user_id'] == user_id]

# Book Comments
def add_book_comment(user_id, book_id, comment_text, rating, username):
    """Add book comment"""
    comments = load_data('book_comments', [])
    
    comment = {
        'id': len(comments) + 1 if comments else 1,
        'user_id': user_id,
        'username': username,
        'book_id': book_id,
        'comment_text': comment_text,
        'rating': rating,
        'created_at': datetime.now().isoformat()
    }
    
    comments.append(comment)
    save_data('book_comments', comments)
    return True

def get_book_comments(book_id):
    """Get comments for a book"""
    comments = load_data('book_comments', [])
    return [c for c in comments if c['book_id'] == book_id]

# Creative Works
def add_creative_work(user_id, title, content_type, content, genre, description, is_public, username):
    """Add creative work"""
    works = load_data('creative_works', [])
    
    work = {
        'id': len(works) + 1 if works else 1,
        'user_id': user_id,
        'username': username,
        'title': title,
        'content_type': content_type,
        'content': content,
        'genre': genre or "Ընդհանուր",
        'description': description,
        'is_public': is_public,
        'created_at': datetime.now().isoformat()
    }
    
    works.append(work)
    save_data('creative_works', works)
    return work['id']

def get_creative_works(user_id=None, public_only=False, viewer_id=None):
    """Get creative works with filtering"""
    works = load_data('creative_works', [])
    
    if user_id is not None:
        filtered = [w for w in works if w['user_id'] == user_id]
        if public_only and viewer_id is not None and user_id != viewer_id:
            filtered = [w for w in filtered if w['is_public']]
        return filtered
    elif public_only:
        return [w for w in works if w['is_public']]
    else:
        return works

def add_creative_work_comment(creative_work_id, user_id, comment_text, username):
    """Add comment to creative work"""
    comments = load_data('creative_work_comments', [])
    
    comment = {
        'id': len(comments) + 1 if comments else 1,
        'creative_work_id': creative_work_id,
        'user_id': user_id,
        'username': username,
        'comment_text': comment_text,
        'created_at': datetime.now().isoformat()
    }
    
    comments.append(comment)
    save_data('creative_work_comments', comments)
    return True

def get_creative_work_comments(creative_work_id):
    """Get comments for creative work"""
    comments = load_data('creative_work_comments', [])
    return [c for c in comments if c['creative_work_id'] == creative_work_id]

# Reminders
def add_reminder(user_id, reminder_time, days_of_week, is_active=True):
    """Add or update reading reminder"""
    reminders = load_data('reading_reminders', [])
    
    user_id = str(user_id)

    # Remove old reminder for this user
    reminders = [r for r in reminders if r['user_id'] != user_id]
    
    reminder = {
        'id': len(reminders) + 1 if reminders else 1,
        'user_id': user_id,
        'reminder_time': reminder_time.strip(),
        'days_of_week': days_of_week,
        'is_active': is_active,
        'created_at': datetime.now().isoformat()
    }
    
    reminders.append(reminder)
    save_data('reading_reminders', reminders)
    
    return True

def get_user_reminder(user_id):
    """Get user's current reminder"""
    user_id = str(user_id)
    reminders = load_data('reading_reminders', [])
    user_reminders = [r for r in reminders if r['user_id'] == user_id]
    return user_reminders[0] if user_reminders else None

def check_reminder_time(user_id):

    reminders = load_data('reading_reminders', [])
    user_id = str(user_id)

    reminder = next(
        (r for r in reminders if r['user_id'] == user_id and r.get('is_active', True)),
        None
    )

    if not reminder:
        return False

    now = datetime.now()

    today_map = {
        "Monday": "Երկուշաբթի",
        "Tuesday": "Երեքշաբթի",
        "Wednesday": "Չորեքշաբթի",
        "Thursday": "Հինգշաբթի",
        "Friday": "Ուրբաթ",
        "Saturday": "Շաբաթ",
        "Sunday": "Կիրակի"
    }

    today_arm = today_map.get(now.strftime("%A"))
    if today_arm not in reminder['days_of_week']:
        return False

    try:
        h, m = map(int, reminder['reminder_time'].split(":"))
    except ValueError:
        return False

    return now.hour == h and now.minute == m


def delete_creative_work(work_id, user_id):
    """Delete creative work if owned by user"""
    try:
        works = load_data('creative_works', [])
        comments = load_data('creative_work_comments', [])
        
        work_to_delete = next((w for w in works if w['id'] == work_id and w['user_id'] == user_id), None)
        
        if not work_to_delete:
            return False, "❌ Միայն կարող եք ջնջել ձեր սեփական ստեղծագործությունները"
        
        works = [w for w in works if w['id'] != work_id]
        save_data('creative_works', works)
        
        comments = [c for c in comments if c['creative_work_id'] != work_id]
        save_data('creative_work_comments', comments)
        
        return True, "✅ Ստեղծագործությունը հաջողությամբ ջնջված է"
    except Exception as e:
        return False, f"❌ Ջնջման սխալ: {str(e)}"

def calculate_reading_speed(user_id):
    """Calculate reading speed from sessions (pages per minute)"""
    sessions = get_user_sessions(user_id)
    
    if not sessions:
        return None
    
    total_pages = sum(s['pages_read'] for s in sessions)
    total_minutes = sum(s['session_duration'] for s in sessions)
    
    if total_minutes <= 0:
        return None

    
    speed = total_pages / total_minutes
    return round(max(0.5, min(5.0, speed)), 1)

def update_reading_speed(user_id):
    """Update user's reading speed in users.json and session"""
    try:
        new_speed = calculate_reading_speed(user_id)
        users = load_users()
        
        if user_id in users:
            users[user_id]['reading_speed'] = new_speed
            save_users(users)
            
            if st.session_state.get('user') and st.session_state.user['id'] == user_id:
                st.session_state.user['reading_speed'] = new_speed
                
            return True
        return False
    except Exception as e:
        print(f"Error updating reading speed: {e}")
        return False
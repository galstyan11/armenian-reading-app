import json
import os
from datetime import datetime

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
    except:
        pass
    return default

def save_data(filename, data):
    """Save data to JSON file"""
    ensure_data_dir()
    filepath = f'data/{filename}.json'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Reading Sessions
def add_reading_session(user_id, book_id, pages_read, session_duration, book_title):
    """Add reading session"""
    sessions = load_data('reading_sessions', [])
    
    session = {
        'id': len(sessions) + 1,
        'user_id': user_id,
        'book_id': book_id,
        'book_title': book_title,
        'pages_read': pages_read,
        'session_duration': session_duration,
        'created_at': str(datetime.now())
    }
    
    sessions.append(session)
    save_data('reading_sessions', sessions)
    return True

def get_user_sessions(user_id):
    """Get user's reading sessions"""
    sessions = load_data('reading_sessions', [])
    user_sessions = [s for s in sessions if s['user_id'] == user_id]
    return user_sessions

# Book Comments
def add_book_comment(user_id, book_id, comment_text, rating, username):
    """Add book comment"""
    comments = load_data('book_comments', [])
    
    comment = {
        'id': len(comments) + 1,
        'user_id': user_id,
        'username': username,
        'book_id': book_id,
        'comment_text': comment_text,
        'rating': rating,
        'created_at': str(datetime.now())
    }
    
    comments.append(comment)
    save_data('book_comments', comments)
    return True

def get_book_comments(book_id):
    """Get comments for a book"""
    comments = load_data('book_comments', [])
    book_comments = [c for c in comments if c['book_id'] == book_id]
    return book_comments

# Creative Works
def add_creative_work(user_id, title, content_type, content, genre, description, is_public, username):
    """Add creative work"""
    works = load_data('creative_works', [])
    
    work = {
        'id': len(works) + 1,
        'user_id': user_id,
        'username': username,
        'title': title,
        'content_type': content_type,
        'content': content,
        'genre': genre,
        'description': description,
        'is_public': is_public,
        'created_at': str(datetime.now())
    }
    
    works.append(work)
    save_data('creative_works', works)
    return work['id']

def get_creative_works(user_id=None, public_only=True):
    """Get creative works"""
    works = load_data('creative_works', [])
    
    if user_id:
        return [w for w in works if w['user_id'] == user_id]
    elif public_only:
        return [w for w in works if w['is_public']]
    else:
        return works

def add_creative_work_comment(creative_work_id, user_id, comment_text, username):
    """Add comment to creative work"""
    comments = load_data('creative_work_comments', [])
    
    comment = {
        'id': len(comments) + 1,
        'creative_work_id': creative_work_id,
        'user_id': user_id,
        'username': username,
        'comment_text': comment_text,
        'created_at': str(datetime.now())
    }
    
    comments.append(comment)
    save_data('creative_work_comments', comments)
    return True

def get_creative_work_comments(creative_work_id):
    """Get comments for creative work"""
    comments = load_data('creative_work_comments', [])
    work_comments = [c for c in comments if c['creative_work_id'] == creative_work_id]
    return work_comments

# Reminders
def add_reminder(user_id, reminder_time, days_of_week, is_active=True):
    """Add reading reminder"""
    reminders = load_data('reading_reminders', [])
    
    # Remove existing reminders for this user
    reminders = [r for r in reminders if r['user_id'] != user_id]
    
    reminder = {
        'id': len(reminders) + 1,
        'user_id': user_id,
        'reminder_time': reminder_time,
        'days_of_week': days_of_week,
        'is_active': is_active,
        'created_at': str(datetime.now())
    }
    
    reminders.append(reminder)
    save_data('reading_reminders', reminders)
    return True

def get_user_reminder(user_id):
    """Get user's reminder"""
    reminders = load_data('reading_reminders', [])
    user_reminders = [r for r in reminders if r['user_id'] == user_id]
    return user_reminders[0] if user_reminders else None

def check_reminder_time(user_id):
    """Check if it's reminder time (simplified version)"""
    # This is a simplified version - in a real app you'd check current time
    # For now, we'll just return False to avoid constant notifications
    return False

def delete_creative_work(work_id, user_id):
    """Delete a creative work (only if user owns it)"""
    try:
        works = load_data('creative_works', [])
        comments = load_data('creative_work_comments', [])
        
        # Find the work and verify ownership
        work_to_delete = None
        for work in works:
            if work['id'] == work_id and work['user_id'] == user_id:
                work_to_delete = work
                break
        
        if not work_to_delete:
            return False, "❌ Միայն կարող եք ջնջել ձեր սեփական ստեղծագործությունները"
        
        # Remove the work
        works = [work for work in works if work['id'] != work_id]
        save_data('creative_works', works)
        
        # Remove associated comments
        comments = [comment for comment in comments if comment['creative_work_id'] != work_id]
        save_data('creative_work_comments', comments)
        
        return True, "✅ Ստեղծագործությունը հաջողությամբ ջնջված է"
    except Exception as e:
        return False, f"❌ Ջնջման սխալ: {str(e)}"

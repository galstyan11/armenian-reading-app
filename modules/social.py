# modules/social.py
from datetime import datetime, timezone
from typing import List, Dict, Tuple

from modules.db import query

# FRIENDS & FRIEND REQUESTS (already MySQL)

def load_friends(username: str) -> List[str]:
    rows = query("""
        SELECT 
            CASE 
                WHEN user1 = %s THEN user2 
                ELSE user1 
            END AS friend
        FROM friendships
        WHERE user1 = %s OR user2 = %s
    """, (username, username, username), fetch=True)

    return [r['friend'] for r in rows] if rows else []


def add_friend(username: str, friend_username: str) -> bool:
    if username == friend_username:
        return False

    u1, u2 = sorted([username, friend_username])
    return bool(query("""
        INSERT IGNORE INTO friendships (user1, user2, created_at)
        VALUES (%s, %s,%s)
    """, (u1, u2, datetime.now(timezone.utc))))


def remove_friend(username: str, friend_username: str) -> bool:
    u1, u2 = sorted([username, friend_username])
    return bool(query("""
        DELETE FROM friendships 
        WHERE user1 = %s AND user2 = %s
    """, (u1, u2)))


def add_friend_request(sender: str, receiver: str) -> bool:
    return bool(query("""
        INSERT IGNORE INTO friend_requests 
            (sender, receiver, status, created_at)
        VALUES (%s, %s, 'pending', %s)
    """, (sender, receiver, datetime.now(timezone.utc))))

def get_pending_received_requests(username: str) -> List[str]:
    rows = query("""
        SELECT sender 
        FROM friend_requests 
        WHERE receiver = %s AND status = 'pending'
    """, (username,), fetch=True)
    return [r['sender'] for r in rows]


def accept_friend_request(receiver: str, sender: str) -> bool:
    # Delete request
    q1 = query("""
        DELETE FROM friend_requests 
        WHERE sender = %s AND receiver = %s AND status = 'pending'
    """, (sender, receiver))

    # Add mutual friendship
    q2 = add_friend(receiver, sender)

    return q1 and q2


def reject_friend_request(receiver: str, sender: str) -> bool:
    return bool(query("""
        DELETE FROM friend_requests 
        WHERE sender = %s AND receiver = %s AND status = 'pending'
    """, (sender, receiver)))


# PRIVATE MESSAGES (now MySQL)

def send_message(sender: str, receiver: str, content: str) -> Tuple[bool, str]:
    if receiver not in load_friends(sender):
        return False, "Դուք ընկերներ չեք — հաղորդագրություն ուղարկել հնարավոր չէ"

    if not content.strip():
        return False, "Հաղորդագրությունը դատարկ է"

    success = query("""
        INSERT INTO messages 
            (sender, receiver, content, created_at, is_read)
        VALUES (%s, %s, %s, %s, FALSE)
    """, (sender, receiver, content.strip(), datetime.now(timezone.utc)))

    if success:
        return True, "Հաղորդագրությունը ուղարկվել է"
    return False, "Չհաջողվեց ուղարկել հաղորդագրությունը"


def get_messages_for_user(username: str) -> List[Dict]:
    return query("""
        SELECT sender, receiver, content, created_at, is_read
        FROM messages
        WHERE sender = %s OR receiver = %s
        ORDER BY created_at DESC
    """, (username, username), fetch=True)


def get_chat_between(u1: str, u2: str) -> List[Dict]:
    return query("""
        SELECT sender, receiver, content, created_at, is_read
        FROM messages
        WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
        ORDER BY created_at ASC
    """, (u1, u2, u2, u1), fetch=True)


# POEMS (now MySQL - add table if not exists)

def share_poem(author: str, title: str, content: str) -> bool:
    return bool(query("""
        INSERT INTO poems 
            (author, title, content, created_at)
        VALUES (%s, %s, %s, %s)
    """, (author, title or "Անվերնագիր", content.strip(), datetime.now(timezone.utc))))


def like_poem(poem_id: int, liker: str) -> bool:
    # Simple version: insert into likes table (recommended)
    return bool(query("""
        INSERT IGNORE INTO poem_likes 
            (poem_id, username, created_at)
        VALUES (%s, %s, %s)
    """, (poem_id, liker, datetime.now(timezone.utc))))


def get_all_poems() -> List[Dict]:
    return query("""
        SELECT id, author, title, content, created_at
        FROM poems
        ORDER BY created_at DESC
    """, fetch=True)
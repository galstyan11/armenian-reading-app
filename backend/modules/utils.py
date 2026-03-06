# modules/utils.py
import requests
from typing import Dict, List, Tuple, Any
import pandas as pd
from collections import defaultdict
import itertools

from modules.auth_file import hash_password

def check_link_availability(url: str) -> bool:
    """Ստուգել հղումի հասանելիությունը (ավելի հուսալի մեթոդ)"""
    if not url or not url.strip():
        return False
    
    try:
        # Նախ փորձել HEAD request
        response = requests.head(
            url,
            timeout=8,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ReadingApp/1.0)"}
        )
        if response.status_code == 200:
            return True

        # Եթե HEAD-ը չի աշխատում, փորձել GET՝ stream-ով
        response = requests.get(
            url,
            timeout=10,
            stream=True,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ReadingApp/1.0)"}
        )
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            if 'pdf' in content_type or response.headers.get('Content-Length'):
                return True
        return False

    except requests.RequestException:
        return False
    except Exception:
        return False


def calculate_reading_plan(
    pages: int,
    reading_speed: float,
    daily_time: int,
    target_days: int
) -> Tuple[int, int]:
    
    if pages <= 0 or reading_speed <= 0 or target_days <= 0 or daily_time <= 0:
        return 0, 0

    daily_pages_float = pages / target_days
    daily_minutes_float = daily_pages_float / reading_speed

    daily_pages = round(daily_pages_float)
    daily_minutes = round(daily_minutes_float)

    daily_pages = max(1, daily_pages)
    daily_minutes = max(1, daily_minutes)

    return daily_pages, daily_minutes


def get_reading_time_recommendation(genre: str) -> Dict[str, str]:
    """Ստանալ ընթերցման ժամանակի առաջարկ ըստ ժանրի"""
    genre_recommendations = {
        'Բանաստեղծություններ': {
            'time': 'ճանապարհին կամ ավտոբուսում',
            'icon': '🚌',
            'reason': 'Բանաստեղծությունները կարճ են և հեշտ է կարդալ դրանք ճանապարհորդության ընթացքում'
        },
        'Դրամա': {
            'time': 'երեկոյան',
            'icon': '🌙',
            'reason': 'Դրամատիկ գրքերը հարուստ են զգացմունքներով և հարմար են երեկոյան հանգստի ժամանակ'
        },
        'Մոտիվացիոն': {
            'time': 'առավոտյան',
            'icon': '☀️',
            'reason': 'Մոտիվացիոն գրքերը կօգնեն ձեզ դրական տրամադրվածությամբ սկսել օրը'
        },
        'Գիտական': {
            'time': 'առավոտյան',
            'icon': '🔬',
            'reason': 'Գիտական գրքերը պահանջում են կենտրոնացում, ինչը ավելի հեշտ է թարմ ու պայծառ առավոտյան'
        },
        'Սիրավեպ': {
            'time': 'երեկոյան',
            'icon': '❤️',
            'reason': 'Սիրային վեպերը հարմար են հանգստանալու և ռոմանտիկ տրամադրվածության համար'
        },
        'Գիտաֆանտաստիկա': {
            'time': 'երեկոյան',
            'icon': '🚀',
            'reason': 'Ֆանտաստիկան հարմար է երեկոյան, երբ կարող եք ամբողջությամբ ընկղմվել երևակայության աշխարհ'
        },
        'Դետեկտիվ': {
            'time': 'երեկոյան',
            'icon': '🕵️',
            'reason': 'Դետեկտիվ գրքերը հարմար են երեկոյան, երբ կարող եք կենտրոնանալ առեղծվածների վրա'
        },
        'Պատմական': {
            'time': 'ցերեկը',
            'icon': '🏛️',
            'reason': 'Պատմական գրքերը հարմար են ցերեկը, երբ ուղեղն ավելի ակտիվ է'
        }
    }
    
    return genre_recommendations.get(genre.strip() if genre else '', {
        'time': 'ցանկացած ժամանակ',
        'icon': '📚',
        'reason': 'Այս գիրքը հարմար է ընթերցման ցանկացած ժամանակ'
    })


from typing import Dict, Any, List

def get_advanced_recommendations(books_df, user_preferences: Dict[str, Any]) -> List[Any]:
    if books_df.empty:
        return []

    # Reading speed (only for feasibility) — unchanged
    real_speed = user_preferences.get("reading_speed")
    effective_speed = real_speed if real_speed is not None and real_speed > 0 else 1.0

    # Preferences — unchanged
    preferred_genres = user_preferences.get("preferred_genres", [])
    preferred_languages = user_preferences.get("preferred_languages", [])
    daily_time = int(user_preferences.get("daily_reading_time", 30))
    age = user_preferences.get("age")  # optional

    # Normalize preferred_languages ALWAYS to a set — unchanged
    if isinstance(preferred_languages, str):
        preferred_languages = [l.strip() for l in preferred_languages.split(",")]

    preferred_languages = set(preferred_languages)

    # Step 1: Calculate score for every book    
    scored_books = []

    for _, book_row in books_df.iterrows():
        score = 0.0
        book = book_row.to_dict()         
        book_genre = book.get("genre")

        # 1. Genre
        if book_genre in preferred_genres:
            score += 50

        # 2. Language
        book_lang = str(book.get("language", "")).strip()
        if book_lang in preferred_languages:
            score += 25

        # 3. age
        if age is not None:
            if age < 18 and book_genre in [
                "Ֆանտաստիկա", "Ավանդապատում", "Մոտիվացիոն", "Սիրավեպ"
            ]:
                score += 10
            elif age > 40 and book_genre in [
                "Պատմական", "Դասական", "Գիտական", "Կենսագրություն", "Փիլիսոփայություն"
            ]:
                score += 10

        # 4. Feasibility
        pages = int(book.get("pages", 0))
        if pages > 0 and real_speed is not None and real_speed > 0:
            total_minutes = pages / effective_speed
            required_days = (
                total_minutes / daily_time if daily_time > 0 else float("inf")
            )

            if required_days <= 30:
                score += 15
            elif required_days <= 60:
                score += 10

        # We collect more candidates than before (lower threshold)
        if score > 10:   # lowered a bit so we have enough books per genre
            scored_books.append((score, book, book_genre))

    # Step 2: Group books by genre
    genre_groups = defaultdict(list)

    for score, book, genre in scored_books:
        if genre:  # skip books without genre
            genre_groups[genre].append((score, book))

    # Sort each genre group by score descending
    for g in genre_groups:
        genre_groups[g].sort(key=lambda x: x[0], reverse=True)

    # Step 3: Round-robin selection to cover all preferred genres
    selected = []
    preferred_genres_set = set(preferred_genres)

    if not preferred_genres_set:
        # No genres selected → fall back to classic top-5 by score
        scored_books.sort(key=lambda x: x[0], reverse=True)
        return [b for _, b, _ in scored_books[:5]]

    # Only consider genres that actually have books
    active_genres = [g for g in preferred_genres_set if g in genre_groups]

    if not active_genres:
        # None of the preferred genres exist in data → classic top-5
        scored_books.sort(key=lambda x: x[0], reverse=True)
        return [b for _, b, _ in scored_books[:5]]

    pointers = {g: 0 for g in active_genres}

    # Cycle through the preferred genres
    for genre in itertools.cycle(active_genres):
        if len(selected) >= 5:
            break

        ptr = pointers[genre]
        group = genre_groups[genre]

        if ptr < len(group):
            selected.append(group[ptr][1])  # take the book
            pointers[genre] += 1
        else:
            # This genre is finished — remove it from rotation
            active_genres = [g for g in active_genres if g != genre]
            if not active_genres:
                break

    # If we still need more books → fill with the highest scoring remaining ones
    if len(selected) < 5:
        remaining = []
        for g in genre_groups:
            for score, book in genre_groups[g][pointers.get(g, 0):]:
                remaining.append((score, book))
        remaining.sort(key=lambda x: x[0], reverse=True)
        for _, book in remaining:
            if len(selected) < 5:
                selected.append(book)
            else:
                break

    return selected[:5]

def delete_account(username: str, password_input: str) -> tuple[bool, str]:
    from modules.db import query

    # Check password first
    user = query(
        "SELECT password_hash FROM users WHERE username = %s",
        (username,),
        fetch=True,
        one=True
    )

    if not user:
        return False, "Օգտատերը չի գտնվել"

    if user['password_hash'] != hash_password(password_input):
        return False, "Սխալ գաղտնաբառ"

    # Delete user (this will cascade to friendships, etc. depending on your schema)
    success = query(
        "DELETE FROM users WHERE username = %s",
        (username,)
    )

    if success:
        return True, "Հաշիվը հաջողությամբ ջնջվել է"
    else:
        return False, "Չհաջողվեց ջնջել հաշիվը"
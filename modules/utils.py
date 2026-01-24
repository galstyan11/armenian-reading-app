# modules/utils.py
import requests
from typing import Dict, List, Tuple, Any


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
    """
    Հաշվարկել ընթերցման պլանը
    Վերադարձնում է (օրական էջեր, օրական պահանջվող րոպեներ)
    """
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


def get_advanced_recommendations(books_df, user_preferences: Dict[str, Any]) -> List[Any]:
    """
    Ստանալ անհատականացված առաջարկներ՝ հիմնված միայն ժանրի, լեզվի և (ըստ ցանկության) տարիքի վրա
    """
    if books_df.empty:
        return []

    recommendations = []

    # Իրական արագություն կամ fallback միայն feasibility-ի համար
    real_speed = user_preferences.get('reading_speed')
    effective_speed = real_speed if real_speed is not None and real_speed > 0 else 1.0

    preferred_genres = user_preferences.get('preferred_genres', [])
    preferred_language = user_preferences.get('preferred_language', 'Հայերեն')
    daily_time = int(user_preferences.get('daily_reading_time', 30))
    age = user_preferences.get('age')  # Optional

    for _, book in books_df.iterrows():
        score = 0.0

        # 1. Ժանր (ամենակարևորը)
        if book.get('genre') in preferred_genres:
            score += 50  # ← ամենաբարձր քաշը

        # 2. Լեզու
        book_lang = str(book.get('language', '')).strip()
        if book_lang == preferred_language:
            score += 25

        # 3. Տարիքային փափուկ բոնուս (ոչ պարտադիր)
        if age is not None:
            genre = book.get('genre', '')
            if age < 18 and genre in ['Ֆանտաստիկա', 'Ավանդապատում', 'Մոտիվացիոն', 'Սիրավեպ']:
                score += 10
            elif age > 40 and genre in ['Պատմական', 'Դասական', 'Գիտական', 'Կենսագրություն', 'Փիլիսոփայություն']:
                score += 8

        # 4. Իրագործելիություն (միայն եթե ունենք իրական արագություն)
        pages = int(book.get('pages', 0))
        if pages > 0 and real_speed is not None and real_speed > 0:
            total_minutes = pages / effective_speed
            required_days = total_minutes / daily_time if daily_time > 0 else float('inf')
            if required_days <= 30:
                score += 15
            elif required_days <= 60:
                score += 10

        if score > 20:  # Նվազագույն շեմ՝ անիմաստ գրքեր չցուցադրելու համար
            recommendations.append((score, book))

    # Տեսակավորել և վերադարձնել լավագույն 5-ը
    recommendations.sort(key=lambda x: x[0], reverse=True)
    return [book for score, book in recommendations[:5]]
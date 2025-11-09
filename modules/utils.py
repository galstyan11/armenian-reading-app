import requests

def check_link_availability(url):
    """Ստուգել հղումի հասանելիությունը"""
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def calculate_reading_plan(pages, reading_speed, daily_time, target_days):
    """Calculate reading plan"""
    if pages <= 0 or reading_speed <= 0 or target_days <= 0:
        return 0, 0
    daily_pages = pages // target_days
    daily_minutes = daily_pages // reading_speed
    return daily_pages, daily_minutes

def get_reading_time_recommendation(genre):
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
            'reason': 'Պատմական գրքերը հարմար են ցերեկը, երբ ուղեղը ավելի ակտիվ է'
        }
    }
    
    return genre_recommendations.get(genre, {
        'time': 'ցանկացած ժամանակ',
        'icon': '📚',
        'reason': 'Այս գիրքը հարմար է ընթերցման ցանկացած ժամանակ'
    })

def get_advanced_recommendations(books_df, user_preferences):
    """Get advanced book recommendations"""
    if books_df.empty:
        return books_df
    
    recommendations = []
    
    for _, book in books_df.iterrows():
        score = 0
        
        # Genre match (40%)
        preferred_genres = user_preferences.get('preferred_genres', [])
        if book['genre'] in preferred_genres:
            score += 40
        
        # Page count suitability (20%)
        preferred_pages = user_preferences.get('preferred_page_range', [100, 300])
        if preferred_pages[0] <= book['pages'] <= preferred_pages[1]:
            score += 20
        
        # Language preference (15%)
        if book['language'] == user_preferences.get('preferred_language', 'Հայերեն'):
            score += 15
        
        # Reading time feasibility (25%)
        reading_speed = user_preferences.get('reading_speed', 2)
        daily_time = user_preferences.get('daily_reading_time', 30)
        estimated_time = book['pages'] / reading_speed
        
        if estimated_time <= daily_time * 7:  # 1 week
            score += 25
        
        recommendations.append((book, score))
    
    # Sort by score and return top recommendations
    recommendations.sort(key=lambda x: x[1], reverse=True)
    return [book for book, score in recommendations[:5]]

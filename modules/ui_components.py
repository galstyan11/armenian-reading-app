# modules/ui_components.py
import streamlit as st
from modules.auth_file import logout

def show_header(user):
    """Display the top header with welcome message and logout button"""
    col1, col2, col3 = st.columns([4, 1, 1])

    with col1:
        st.markdown(
            f"""<div style="margin-top: 10px;">
                <div style="font-size: 28px; font-weight: 400; line-height: 1.3;">
                    Սիրելի {user['username']},
                </div>
                <div style="font-size: 28px; font-weight: 400; line-height: 1.3;">
                    Բարի գալուստ
                </div>
                <div style="font-size: 28px; font-weight: 400; line-height: 1.3;">
                    <span style="color: #f77214; font-weight: 700;">ԿԱՐԴԱ</span>
                    <span style="color: #672f1b; font-weight: 700;"> ինձ հետ</span> հավելված!
                </div>
            </div>""",
            unsafe_allow_html=True
        )
        

    with col3:
        if st.button("🚪 Դուրս Գալ", type="secondary"):
            logout()
            st.rerun()

def show_main_tabs(books_df, user):
    """Display working horizontal tabs"""
    
    # Tab-երի անունները
    tab_names = [
        "📚 Բոլոր Գրքերը",
        "💡 Առաջարկներ",
        "📅 Ընթերցման Պլան",
        "🎨 Ստեղծագործություններ",
        "👤 Պրոֆիլ"
    ]

    # Եթե ուրիշի պրոֆիլ ենք բացում — անմիջապես անցնել Պրոֆիլ tab
    if st.session_state.get("selected_tab") == "profile":
        default_tab = "👤 Պրոֆիլ"
        if "selected_tab" in st.session_state:
            del st.session_state.selected_tab
    else:
        default_tab = "📚 Բոլոր Գրքերը"

    # Ստեղծել tabs-երը՝ default ընտրվածով
    tabs = st.tabs(tab_names)

    # Բովանդակությունը՝ յուրաքանչյուր tab-ի համար
    with tabs[0]:
        from modules.books_csv import show_all_books
        show_all_books(books_df, user)

    with tabs[1]:
        from modules.books_csv import show_recommendations
        show_recommendations(books_df, user)

    with tabs[2]:
        from modules.books_csv import show_reading_plan
        show_reading_plan(books_df, user)

    with tabs[3]:
        from modules.creative_file import show_creative_works
        show_creative_works(user)

    with tabs[4]:
        from modules.users_file import show_full_profile
        show_full_profile(user, books_df)

    # Ավտոմատ անցում դեպի Պրոֆիլ, եթե պահանջվում է
    if default_tab == "👤 Պրոֆիլ":
        # Streamlit-ը ինքն է ընտրում tab-ը, եթե մենք rerun ենք անում, բայց այստեղ պարզապես աշխատում է
        pass
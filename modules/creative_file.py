# modules/creative_file.py
import streamlit as st
from modules.data_file import (
    add_creative_work,
    get_creative_works,
    add_creative_work_comment,
    get_creative_work_comments,
    delete_creative_work
)
from modules.custom_alerts import custom_success, custom_info, custom_empty, custom_warning
from modules.time_utils import parse_iso, format_armenia


def show_creative_works(user):
    st.subheader("Քո Ստեղծագործությունները")

    tab1, tab2, tab3 = st.tabs([
        "Նոր Ստեղծագործություն",
        "Իմ Ստեղծագործությունները",
        "Համայնքի Ստեղծագործությունները"
    ])

    # ── Tab 1: Create new work ────────────────────────────────────────
    with tab1:
        st.write("###Հրապարակել Նոր Ստեղծագործություն")

        with st.form("creative_work_form", clear_on_submit=True):
            work_title = st.text_input("Վերնագիր *", placeholder="Ձեր ստեղծագործության վերնագիրը...")
            content_type = st.selectbox("Տեսակ *", [
                "Պոեմ", "Պատմվածք", "Վեպ", "Էսսե", "Հոդված", "Բանաստեղծություն", "Այլ"
            ])
            genre = st.text_input("Ժանր", placeholder="Օրինակ՝ Սիրային, Թրիլեր, Կենսագրական...")
            description = st.text_area("Կարճ Նկարագրություն",
                                      placeholder="Ստեղծագործության համառոտ նկարագրություն...",
                                      height=80)
            content = st.text_area("Բովանդակություն *",
                                   placeholder="Մուտքագրեք ձեր ստեղծագործության տեքստն այստեղ...",
                                   height=200)
            is_public = st.checkbox("🌍 Հասանելի է բոլորին", value=True,
                                    help="Եթե նշված է, ձեր ստեղծագործությունը տեսանելի կլինի բոլոր օգտատերերին")

            submitted = st.form_submit_button("Հրապարակել Ստեղծագործությունը")

            if submitted:
                if not work_title.strip() or not content.strip():
                    st.error("Վերնագիրը և բովանդակությունը պարտադիր են")
                else:
                    work_id = add_creative_work(
                        user['id'],
                        work_title.strip(),
                        content_type,
                        content.strip(),
                        genre.strip() or "Ընդհանուր",
                        description.strip() or None,
                        is_public,
                        user['username']
                    )
                    if work_id:
                        custom_success("Ձեր ստեղծագործությունը հաջողությամբ հրապարակված է!")
                    else:
                        st.error("Չհաջողվեց հրապարակել ստեղծագործությունը")

    # ── Tab 2: My works ───────────────────────────────────────────────
    with tab2:
        st.write("### Իմ Ստեղծագործությունները")

        my_works = get_creative_works(user_id=user['id'])
        my_works = sorted(my_works, key=lambda w: w['created_at'], reverse=True)

        if my_works:
            for idx, work in enumerate(my_works):
                with st.expander(f" {work['title']} ({work['content_type']})"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**Տեսակ:** {work['content_type']}")
                        if work.get('genre'):
                            st.write(f"**Ժանր:** {work['genre']}")
                        if work.get('description'):
                            st.write(f"**Նկարագրություն:** {work['description']}")

                        st.write("---")
                        st.write("**Բովանդակություն:**")
                        st.write(work['content'])

                    with col2:
                        st.write("**Հրապարակված է:**")
                        st.write(format_armenia(parse_iso(work['created_at'])))

                        st.write(f"**Տեսանելիություն:** {'Հասարակական' if work['is_public'] else 'Մասնավոր'}")

                        # Delete controls
                        st.write("---")
                        st.write("**Կառավարում**")

                        delete_key = f"delete_confirm_{work['id']}_{idx}"
                        if delete_key not in st.session_state:
                            st.session_state[delete_key] = False

                        if not st.session_state[delete_key]:
                            if st.button("🗑️ Ջնջել Ստեղծագործությունը", key=f"delete_btn_{work['id']}_{idx}"):
                                st.session_state[delete_key] = True
                                st.rerun()
                        else:
                            custom_warning("Դուք պատրաստվում եք ջնջել այս ստեղծագործությունը:")
                            st.write(f"**{work['title']}**")
                            st.error("Այս գործողությունը հնարավոր չէ հետարկել!")

                            col_confirm, col_cancel = st.columns(2)
                            with col_confirm:
                                if st.button("Այո, Ջնջել", key=f"confirm_delete_{work['id']}_{idx}", type="primary"):
                                    success, message = delete_creative_work(work['id'], user['id'])
                                    if success:
                                        custom_success(message)
                                    else:
                                        st.error(message)
                                    if delete_key in st.session_state:
                                        del st.session_state[delete_key]
                                    st.rerun()

                            with col_cancel:
                                if st.button("Չեղարկել", key=f"cancel_delete_{work['id']}_{idx}"):
                                    if delete_key in st.session_state:
                                        del st.session_state[delete_key]
                                    st.rerun()

                    st.write("---")
                    show_creative_work_comments_section(work['id'], user, f"my_work_{work['id']}_{idx}")
        else:
            custom_empty("Դեռ չունեք հրապարակված ստեղծագործություններ։ Սկսեք գրել ձեր առաջին աշխատանքը։")

    # ── Tab 3: Community works ────────────────────────────────────────
    with tab3:
        st.write("### Համայնքի Ստեղծագործություններ")

        community_works = get_creative_works(public_only=True)
        community_works = sorted(community_works, key=lambda w: w['created_at'], reverse=True)

        if community_works:
            for idx, work in enumerate(community_works):
                if work['user_id'] == user['id']:
                    continue

                with st.expander(f"{work['title']} - {work['username']} ({work['content_type']})"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**Հեղինակ:** {work['username']}")
                        if st.button(f"Տեսնել {work['username']}-ի պրոֆիլը", key=f"profile_view_{work['id']}_{idx}"):
                            st.session_state.viewed_profile = work['username']
                            st.session_state.active_profile_tab = 4  # 4 = "Պրոֆիլ" tab index
                            st.rerun()

                        st.write(f"**Տեսակ:** {work['content_type']}")
                        if work.get('genre'):
                            st.write(f"**Ժանր:** {work['genre']}")
                        if work.get('description'):
                            st.write(f"**Նկարագրություն:** {work['description']}")

                        st.write("---")
                        st.write("**Բովանդակություն:**")
                        st.write(work['content'])

                    with col2:
                        st.write("**Հրապարակված է:**")
                        st.write(format_armenia(parse_iso(work['created_at'])))

                    st.write("---")
                    show_creative_work_comments_section(work['id'], user, f"community_{work['id']}_{idx}")
        else:
            custom_empty("Դեռ չկան համայնքի ստեղծագործություններ։ Դուք կարող եք լինել առաջինը։")


def show_creative_work_comments_section(creative_work_id, user, unique_suffix=""):
    st.write("#### Մեկնաբանություններ")

    comments = get_creative_work_comments(creative_work_id)
    comments = sorted(comments, key=lambda c: c['created_at'], reverse=True)

    if comments:
        for comment in comments:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"** {comment['username']}**")
                    if st.button(f" Տեսնել {comment['username']}-ի պրոֆիլը",
                                 key=f"comment_profile_{comment['id']}_{unique_suffix}"):
                        st.session_state.viewed_profile = comment['username']
                        st.session_state.active_profile_tab = 4  # Switch to profile tab
                        st.rerun()
                    st.write(comment['comment_text'])
                with col2:
                    st.write(f"_{format_armenia(parse_iso(comment['created_at']))}_")
                st.markdown("---")
    else:
        custom_empty(" Դեռ չկան մեկնաբանություններ։ Դուք կարող եք լինել առաջինը։")

    with st.form(key=f"creative_comment_form_{creative_work_id}_{unique_suffix}"):
        new_comment = st.text_area(
            "Ձեր մեկնաբանությունը",
            height=80,
            placeholder="Կիսվեք ձեր կարծիքով ստեղծագործության մասին...",
            key=f"creative_comment_text_{creative_work_id}_{unique_suffix}"
        )

        submit_comment = st.form_submit_button(" Ուղարկել Մեկնաբանություն")

        if submit_comment and new_comment.strip():
            success = add_creative_work_comment(
                creative_work_id,
                user['id'],
                new_comment.strip(),
                user['username']
            )
            if success:
                custom_success("Ձեր մեկնաբանությունը հաջողությամբ ավելացվել է!")
                st.rerun()
            else:
                st.error("Չհաջողվեց ավելացնել մեկնաբանությունը")
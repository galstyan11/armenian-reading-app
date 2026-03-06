# modules/creative_file.py
import pytz
import streamlit as st
from modules.data_file import (
    add_creative_work,
    get_creative_works,
    add_creative_work_comment,
    get_creative_work_comments,
    delete_creative_work,
    query,
    json_obj
)
from modules.custom_alerts import custom_success, custom_info, custom_empty, custom_warning
from modules.time_utils import format_armenia_datetime


def show_creative_works(user):
    st.subheader("Քո Ստեղծագործությունները")

    # Refresh trigger — incremented after like, comment, publish, delete
    if 'creative_refresh' not in st.session_state:
        st.session_state.creative_refresh = 0

    tab1, tab2, tab3 = st.tabs([
        "Նոր Ստեղծագործություն",
        "Իմ Ստեղծագործությունները",
        "Համայնքի Ստեղծագործությունները"
    ])

    # ── Tab 1: Create new work ────────────────────────────────────────
    with tab1:
        st.write("### Հրապարակել Նոր Ստեղծագործություն")

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
                        user['username'],
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
                        st.session_state.creative_refresh += 1
                        st.rerun()
                    else:
                        st.error("Չհաջողվեց հրապարակել ստեղծագործությունը")

    # ── Tab 2: My works ───────────────────────────────────────────────
    with tab2:
        st.write("### Իմ Ստեղծագործությունները")

        my_works = get_creative_works(user_id=user['username'])
        my_works = sorted(my_works, key=lambda w: w['created_at'], reverse=True)

        if my_works:
            for idx, work in enumerate(my_works):
                likes_list = json_obj(work.get('likes', []))
                likes_count = len(likes_list)

                expander_label = f"{work['title']} ({work['content_type']})"
                if likes_count > 0:
                    expander_label += f" ❤️ {likes_count}"

                with st.expander(expander_label):
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
                        st.write("**Հրապարակման ամսաթիվ:**")
                        st.write(format_armenia_datetime(work['created_at']))
                        st.write(f"**Տեսանելիություն:** {'Հասարակական' if work['is_public'] else 'Մասնավոր'}")
                       
                    st.write("---")

                    if likes_list:
                        with st.expander(f"❤️ Հավանել են {likes_count} մարդ"):
                            for liker in sorted(likes_list):
                                if st.button(f"• {liker}", key=f"liker_my_{work['id']}_{liker}_{idx}", type="tertiary"):
                                    st.session_state.viewed_profile = liker
                                    st.rerun()
                    else:
                        st.caption("Այս աշխատանքը դեռ չի հավանվել որևէ մեկի կողմից")

                    st.write("---")
                    show_creative_work_comments_section(work['id'], user, f"my_{work['id']}_{idx}")

                    st.write("---")
                    st.write("**Կառավարում**")

                    delete_key = f"delete_confirm_{work['id']}_{idx}"
                    if delete_key not in st.session_state:
                        st.session_state[delete_key] = False

                    if not st.session_state[delete_key]:
                        if st.button("🗑️ Ջնջել", key=f"delete_btn_{work['id']}_{idx}"):
                            st.session_state[delete_key] = True
                            st.rerun()
                    else:
                        custom_warning(f"Ջնջե՞լ **{work['title']}**-ը?")
                        st.error("Այս գործողությունն անշրջելի է!")

                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("Այո, ջնջել", key=f"confirm_delete_{work['id']}_{idx}", type="primary"):
                                success, message = delete_creative_work(work['id'], user['username'])
                                if success:
                                    custom_success(message)
                                    st.session_state.creative_refresh += 1
                                    st.rerun()
                                else:
                                    st.error(message)
                                if delete_key in st.session_state:
                                    del st.session_state[delete_key]

                        with col_cancel:
                            if st.button("Չեղարկել", key=f"cancel_delete_{work['id']}_{idx}"):
                                if delete_key in st.session_state:
                                    del st.session_state[delete_key]
                                st.rerun()

        else:
            custom_empty("Դեռ չունեք հրապարակված ստեղծագործություններ։ Սկսեք գրել ձեր առաջին աշխատանքը։")

    # ── Tab 3: Community works ────────────────────────────────────────
    with tab3:
        st.write("### Համայնքի Ստեղծագործություններ")

        community_works = get_creative_works(public_only=True)
        community_works = sorted(community_works, key=lambda w: w['created_at'], reverse=True)

        if community_works:
            for idx, work in enumerate(community_works):
                if work['user_id'] == user['username']:
                    continue

                likes_list = json_obj(work.get('likes', []))
                likes_count = len(likes_list)
                has_liked = user['username'] in likes_list

                expander_label = f"{work['title']} - {work['username']} ({work['content_type']})"
                if likes_count > 0:
                    expander_label += f" ❤️ {likes_count}"

                with st.expander(expander_label):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.write(f"**Հեղինակ:** {work['username']}")
                        if st.button(f"Տեսնել {work['username']}-ի պրոֆիլը", key=f"profile_view_{work['id']}_{idx}"):
                            st.session_state.viewed_profile = work['username']
                            st.session_state.active_profile_tab = 4
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
                        st.write("**Հրապարակման ամսաթիվ:**")
                        st.write(format_armenia_datetime(work['created_at']))        

                        # Like / Unlike button
                        btn_label = f"❤️ {likes_count} հավանում" if not has_liked else f"✓ {likes_count} հավանում"
                        btn_type = "primary" if has_liked else "secondary"  # or "tertiary" for liked

                        if st.button(
                            btn_label,
                            key=f"like_comm_{work['id']}_{idx}",
                            type=btn_type,
                            use_container_width=True
                        ):
                            if has_liked:
                                # Unlike (remove like)
                                success = query("""
                                    UPDATE creative_works
                                    SET 
                                        likes = JSON_REMOVE(
                                            likes,
                                            JSON_UNQUOTE(
                                                JSON_SEARCH(likes, 'one', %s)
                                            )
                                        ),
                                        likes_count = GREATEST(likes_count - 1, 0)
                                    WHERE id = %s
                                    AND JSON_CONTAINS(likes, JSON_QUOTE(%s))
                                """, (user['username'], work['id'], user['username']))

                                if success:
                                    custom_success("Հավանումը հանվեց")
                                    st.session_state.creative_refresh += 1
                                    st.rerun()
                                else:
                                    custom_warning("Չհաջողվեց հանել հավանումը")
                            else:
                                # Like (add like)
                                success = query("""
                                    UPDATE creative_works
                                    SET 
                                        likes = JSON_ARRAY_APPEND(
                                            COALESCE(likes, JSON_ARRAY()),
                                            '$',
                                            %s
                                        ),
                                        likes_count = likes_count + 1
                                    WHERE id = %s
                                    AND NOT JSON_CONTAINS(
                                        COALESCE(likes, JSON_ARRAY()),
                                        JSON_QUOTE(%s)
                                    )
                                """, (user['username'], work['id'], user['username']))

                                if success:
                                    custom_success("Հավանեցիք!")
                                    st.session_state.creative_refresh += 1
                                    st.rerun()
                                else:
                                    custom_warning("Չհաջողվեց հավանել — հավանաբար արդեն հավանել եք կամ սխալ կա")
                    
                    st.write("---")

                    if likes_list:
                        with st.expander(f"❤️ Հավանումներ՝ {likes_count}"):
                            for liker in sorted(likes_list):
                                if st.button(f"• {liker}", key=f"liker_comm_{work['id']}_{liker}_{idx}", type="tertiary"):
                                    st.session_state.viewed_profile = liker
                                    st.rerun()
                    else:
                        st.caption("Այս աշխատանքը դեռ չի հավանվել")

                    st.write("---")
                    show_creative_work_comments_section(work['id'], user, f"comm_{work['id']}_{idx}")

        else:
            custom_empty("Դեռ չկան համայնքի ստեղծագործություններ։ Դուք կարող եք լինել առաջինը։")


def show_creative_work_comments_section(creative_work_id, user, unique_suffix=""):
    st.write("#### Մեկնաբանություններ")

    comments = get_creative_work_comments(creative_work_id)
    comments = sorted(comments, key=lambda c: c['created_at'], reverse=True)

    if comments:
        for comment in comments:
            with st.container():
                col1, col2 = st.columns([5, 2])
                with col1:
                    st.markdown(f"**{comment['username']}**")
                    st.write(comment['comment_text'])
                with col2:
                    st.caption(format_armenia_datetime(comment['created_at']))
                
                if st.button(
                    f"Տեսնել {comment['username']}-ի պրոֆիլը",
                    key=f"comment_profile_{comment['id']}_{unique_suffix}"
                ):
                    st.session_state.viewed_profile = comment['username']
                    st.session_state.active_profile_tab = 4
                    st.rerun()
    else:
        custom_empty("Դեռ չկան մեկնաբանություններ։ Դուք կարող եք լինել առաջինը։")

    with st.form(key=f"creative_comment_form_{creative_work_id}_{unique_suffix}", clear_on_submit=True):
        new_comment = st.text_area(
            "Ձեր մեկնաբանությունը",
            height=80,
            placeholder="Կիսվեք ձեր կարծիքով ստեղծագործության մասին...",
            key=f"creative_comment_text_{creative_work_id}_{unique_suffix}"
        )

        submit_comment = st.form_submit_button("Ուղարկել Մեկնաբանություն")

        if submit_comment:
            cleaned = new_comment.strip()
            if not cleaned:
                st.warning("Մեկնաբանությունը չի կարող դատարկ լինել")
            else:
                success = add_creative_work_comment(
                    creative_work_id,
                    user['username'],
                    cleaned
                )
                if success:
                    custom_success("Ձեր մեկնաբանությունը հաջողությամբ ավելացվել է!")
                    st.session_state.creative_refresh += 1
                    st.rerun()
                else:
                    st.error("Չհաջողվեց ավելացնել մեկնաբանությունը")
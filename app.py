import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Library Management System", page_icon="📚", layout="wide")


# =====================================================
# HELPERS
# =====================================================

def call_api(method, path, **kwargs):
    """Call the FastAPI backend. Returns JSON on success, None on error (and shows the error)."""
    try:
        resp = requests.request(method, f"{API_URL}{path}", timeout=10, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the backend. Is FastAPI running? "
                 "Start it with: uvicorn main:app --reload")
        return None
    except requests.exceptions.Timeout:
        st.error("The backend took too long to respond.")
        return None

    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", "Something went wrong")
        except ValueError:
            detail = resp.text
        if isinstance(detail, list):  # validation errors (422)
            detail = "; ".join(f"{'.'.join(str(x) for x in e['loc'][1:])}: {e['msg']}" for e in detail)
        st.error(f"Error: {detail}")
        return None

    return resp.json()


def flash(message):
    """Save a success message to show after the page reloads."""
    st.session_state["flash"] = message


def show_flash():
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))


# =====================================================
# PAGES
# =====================================================

def dashboard_page():
    st.header("📊 Dashboard")
    stats = call_api("GET", "/stats")
    if stats is None:
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Books", stats["total_books"])
    c2.metric("Total Members", stats["total_members"])
    c3.metric("Books Borrowed", stats["books_borrowed"])
    c4.metric("Overdue Books", stats["overdue_books"])

    if stats["overdue_books"] > 0:
        st.warning(f"{stats['overdue_books']} book(s) are overdue. Check the Overdue page.")


# ---------------------- BOOKS ----------------------

def books_page():
    st.header("📖 Books")
    show_flash()
    tab_view, tab_add, tab_edit = st.tabs(["View / Search", "Add Book", "Edit / Delete"])

    # ---- View ----
    with tab_view:
        col1, col2 = st.columns(2)
        search = col1.text_input("Search by title or author")
        category = col2.text_input("Filter by category")

        params = {}
        if search:
            params["search"] = search
        if category:
            params["category"] = category

        books = call_api("GET", "/books", params=params)
        if books:
            st.dataframe(books, hide_index=True)
            st.caption(f"{len(books)} book(s) found")
        elif books is not None:
            st.info("No books found.")

    # ---- Add ----
    with tab_add:
        with st.form("add_book_form", clear_on_submit=True):
            title = st.text_input("Title *")
            author = st.text_input("Author *")
            isbn = st.text_input("ISBN * (at least 5 characters)")
            category = st.text_input("Category")
            copies = st.number_input("Total copies", min_value=1, value=1, step=1)
            submitted = st.form_submit_button("Add Book")

        if submitted:
            if not title or not author or not isbn:
                st.error("Title, author and ISBN are required.")
            else:
                result = call_api("POST", "/books", json={
                    "title": title, "author": author, "isbn": isbn,
                    "category": category or None, "total_copies": int(copies),
                })
                if result:
                    flash(f"Book '{result['title']}' added!")
                    st.rerun()

    # ---- Edit / Delete ----
    with tab_edit:
        books = call_api("GET", "/books")
        if not books:
            st.info("No books to edit yet.")
        else:
            options = {f"#{b['id']} - {b['title']} by {b['author']}": b for b in books}
            choice = st.selectbox("Select a book", list(options.keys()), key="edit_book_select")
            book = options[choice]

            st.subheader("Edit")
            with st.form(f"edit_book_form_{book['id']}"):
                new_title = st.text_input("Title", value=book["title"])
                new_author = st.text_input("Author", value=book["author"])
                new_category = st.text_input("Category", value=book["category"] or "")
                new_copies = st.number_input("Total copies", min_value=1,
                                             value=book["total_copies"], step=1)
                st.caption(f"ISBN: {book['isbn']} (cannot be changed) | "
                           f"Available now: {book['available_copies']}")
                save = st.form_submit_button("Save Changes")

            if save:
                result = call_api("PUT", f"/books/{book['id']}", json={
                    "title": new_title, "author": new_author,
                    "category": new_category or None, "total_copies": int(new_copies),
                })
                if result:
                    flash("Book updated!")
                    st.rerun()

            st.subheader("Delete")
            sure = st.checkbox("I am sure I want to delete this book", key=f"del_book_ok_{book['id']}")
            if st.button("Delete Book", type="primary", disabled=not sure):
                result = call_api("DELETE", f"/books/{book['id']}")
                if result:
                    flash(result["message"])
                    st.rerun()


# ---------------------- MEMBERS ----------------------

def members_page():
    st.header("👥 Members")
    show_flash()
    tab_view, tab_add, tab_edit = st.tabs(["View / Search", "Add Member", "Edit / Delete"])

    # ---- View ----
    with tab_view:
        search = st.text_input("Search by name or email")
        params = {"search": search} if search else {}
        members = call_api("GET", "/members", params=params)
        if members:
            st.dataframe(members, hide_index=True)
            st.caption(f"{len(members)} member(s) found")
        elif members is not None:
            st.info("No members found.")

        st.divider()
        st.subheader("Borrow history of a member")
        all_members = call_api("GET", "/members")
        if all_members:
            opts = {f"#{m['id']} - {m['name']}": m["id"] for m in all_members}
            pick = st.selectbox("Select member", list(opts.keys()), key="history_member")
            history = call_api("GET", f"/members/{opts[pick]}/borrows")
            if history:
                st.dataframe(history, hide_index=True)
            elif history is not None:
                st.info("This member has not borrowed any books yet.")

    # ---- Add ----
    with tab_add:
        with st.form("add_member_form", clear_on_submit=True):
            name = st.text_input("Name *")
            email = st.text_input("Email *")
            phone = st.text_input("Phone")
            submitted = st.form_submit_button("Add Member")

        if submitted:
            if not name or not email:
                st.error("Name and email are required.")
            else:
                result = call_api("POST", "/members", json={
                    "name": name, "email": email, "phone": phone or None,
                })
                if result:
                    flash(f"Member '{result['name']}' added!")
                    st.rerun()

    # ---- Edit / Delete ----
    with tab_edit:
        members = call_api("GET", "/members")
        if not members:
            st.info("No members to edit yet.")
        else:
            options = {f"#{m['id']} - {m['name']} ({m['email']})": m for m in members}
            choice = st.selectbox("Select a member", list(options.keys()), key="edit_member_select")
            member = options[choice]

            st.subheader("Edit")
            with st.form(f"edit_member_form_{member['id']}"):
                new_name = st.text_input("Name", value=member["name"])
                new_email = st.text_input("Email", value=member["email"])
                new_phone = st.text_input("Phone", value=member["phone"] or "")
                new_active = st.checkbox("Active", value=member["is_active"])
                save = st.form_submit_button("Save Changes")

            if save:
                result = call_api("PUT", f"/members/{member['id']}", json={
                    "name": new_name, "email": new_email,
                    "phone": new_phone or None, "is_active": new_active,
                })
                if result:
                    flash("Member updated!")
                    st.rerun()

            st.subheader("Delete")
            sure = st.checkbox("I am sure I want to delete this member",
                               key=f"del_member_ok_{member['id']}")
            if st.button("Delete Member", type="primary", disabled=not sure):
                result = call_api("DELETE", f"/members/{member['id']}")
                if result:
                    flash(result["message"])
                    st.rerun()


# ---------------------- BORROW / RETURN ----------------------

def borrow_return_page():
    st.header("🔄 Borrow & Return")
    show_flash()
    tab_borrow, tab_return, tab_all = st.tabs(["Borrow a Book", "Return a Book", "All Records"])

    books = call_api("GET", "/books") or []
    members = call_api("GET", "/members") or []
    book_names = {b["id"]: b["title"] for b in books}
    member_names = {m["id"]: m["name"] for m in members}

    # ---- Borrow ----
    with tab_borrow:
        available = [b for b in books if b["available_copies"] > 0]
        active_members = [m for m in members if m["is_active"]]

        if not available:
            st.info("No books are available right now.")
        elif not active_members:
            st.info("No active members. Add a member first.")
        else:
            book_opts = {f"#{b['id']} - {b['title']} ({b['available_copies']} available)": b["id"]
                         for b in available}
            member_opts = {f"#{m['id']} - {m['name']}": m["id"] for m in active_members}

            with st.form("borrow_form"):
                book_pick = st.selectbox("Book", list(book_opts.keys()))
                member_pick = st.selectbox("Member", list(member_opts.keys()))
                days = st.slider("Borrow for (days)", min_value=1, max_value=60, value=14)
                submitted = st.form_submit_button("Borrow")

            if submitted:
                result = call_api("POST", "/borrow", json={
                    "book_id": book_opts[book_pick],
                    "member_id": member_opts[member_pick],
                    "days": days,
                })
                if result:
                    flash(f"Book issued! Due date: {result['due_date']}")
                    st.rerun()

    # ---- Return ----
    with tab_return:
        active = call_api("GET", "/borrows", params={"status": "borrowed"})
        if not active:
            if active is not None:
                st.info("No books are currently borrowed.")
        else:
            header = st.columns([1, 3, 2, 2, 2])
            for col, text in zip(header, ["ID", "Book", "Member", "Due date", ""]):
                col.markdown(f"**{text}**")

            for record in active:
                cols = st.columns([1, 3, 2, 2, 2])
                cols[0].write(record["id"])
                cols[1].write(book_names.get(record["book_id"], f"Book #{record['book_id']}"))
                cols[2].write(member_names.get(record["member_id"], f"Member #{record['member_id']}"))
                cols[3].write(record["due_date"])
                if cols[4].button("Return", key=f"return_{record['id']}"):
                    result = call_api("POST", f"/return/{record['id']}")
                    if result:
                        msg = "Book returned!"
                        if result["fine_amount"] > 0:
                            msg += f" Late fine: ₹{result['fine_amount']:.0f}"
                        flash(msg)
                        st.rerun()

    # ---- All records ----
    with tab_all:
        status = st.selectbox("Filter by status", ["all", "borrowed", "returned"])
        params = {} if status == "all" else {"status": status}
        records = call_api("GET", "/borrows", params=params)
        if records:
            rows = [{
                "Record ID": r["id"],
                "Book": book_names.get(r["book_id"], r["book_id"]),
                "Member": member_names.get(r["member_id"], r["member_id"]),
                "Borrowed on": r["borrow_date"],
                "Due date": r["due_date"],
                "Returned on": r["return_date"],
                "Fine (₹)": r["fine_amount"],
                "Status": r["status"],
            } for r in records]
            st.dataframe(rows, hide_index=True)
        elif records is not None:
            st.info("No records found.")


# ---------------------- OVERDUE ----------------------

def overdue_page():
    st.header("⚠️ Overdue Books")
    overdue = call_api("GET", "/borrows/overdue")
    if overdue is None:
        return
    if not overdue:
        st.success("No overdue books. 🎉")
        return

    from datetime import date
    books = call_api("GET", "/books") or []
    members = call_api("GET", "/members") or []
    book_names = {b["id"]: b["title"] for b in books}
    member_names = {m["id"]: m["name"] for m in members}

    rows = []
    for r in overdue:
        days_late = (date.today() - date.fromisoformat(r["due_date"])).days
        rows.append({
            "Record ID": r["id"],
            "Book": book_names.get(r["book_id"], r["book_id"]),
            "Member": member_names.get(r["member_id"], r["member_id"]),
            "Due date": r["due_date"],
            "Days late": days_late,
            "Fine so far (₹)": days_late * 5,  # same as FINE_PER_DAY in the backend
        })
    st.dataframe(rows, hide_index=True)
    st.caption(f"{len(rows)} overdue book(s)")


# =====================================================
# NAVIGATION
# =====================================================

st.sidebar.title("📚 Library")
page = st.sidebar.radio(
    "Go to",
    ["Dashboard", "Books", "Members", "Borrow & Return", "Overdue"],
)

if page == "Dashboard":
    dashboard_page()
elif page == "Books":
    books_page()
elif page == "Members":
    members_page()
elif page == "Borrow & Return":
    borrow_return_page()
else:
    overdue_page()

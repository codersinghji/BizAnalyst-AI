
import streamlit as st
import pandas as pd

from database.db_manager import DatabaseManager

def get_user_value(user, key, default=None):
    """Read a value from either a dictionary or an object."""
    if isinstance(user, dict):
        return user.get(key, default)

    if hasattr(user, "to_dict"):
        data = user.to_dict()
        if isinstance(data, dict):
            return data.get(key, default)

    return getattr(user, key, default)

def show_admin_panel():

    # ==========================================
    # ADMIN ACCESS CHECK
    # ==========================================

    current_user = st.session_state.get("user", {})
    current_role = str(
        get_user_value(current_user, "role", "Analyst")
    ).strip().lower()

    if current_role != "admin":
        st.error("Access denied. Only administrators can access this page.")
        return

    # ==========================================
    # DASHBOARD HEADER
    # ==========================================

    st.title("🛡️ Admin Dashboard")
    st.caption("Manage BizAnalyst-AI users and accounts.")

    st.success("Administrator access verified.")

    # ==========================================
    # DATABASE CONNECTION
    # ==========================================

    try:
        db = DatabaseManager()
        users = db.get_all_users() or []

    except Exception as error:
        st.error(f"Unable to load users: {error}")
        return

    # ==========================================
    # CONVERT USERS INTO DATAFRAME
    # ==========================================

    user_data = []

    for user in users:

        user_data.append({
            "id": get_user_value(user, "id"),
            "name": get_user_value(user, "name", "Unknown"),
            "email": get_user_value(user, "email", "Not available"),
            "role": get_user_value(user, "role", "Analyst"),
            "is_active": get_user_value(user, "is_active", True),
            "created_at": get_user_value(user, "created_at", "Not available")
        })

    df = pd.DataFrame(
        user_data,
        columns=[
            "id",
            "name",
            "email",
            "role",
            "is_active",
            "created_at"
        ]
    )

    # ==========================================
    # USER STATISTICS
    # ==========================================

    total_users = len(df)

    if total_users > 0:
        total_admins = int(
            (df["role"].astype(str).str.lower() == "admin").sum()
        )

        total_analysts = int(
            (df["role"].astype(str).str.lower() == "analyst").sum()
        )

        active_users = int(
            df["is_active"].apply(
                lambda value: str(value).lower() in ["true", "1", "yes"]
            ).sum()
        )
    else:
        total_admins = 0
        total_analysts = 0
        active_users = 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Users", total_users)
    col2.metric("Administrators", total_admins)
    col3.metric("Analysts", total_analysts)
    col4.metric("Active Users", active_users)

    st.divider()

    # ==========================================
    # REGISTERED USERS
    # ==========================================

    st.subheader("👥 Registered Users")

    if df.empty:
        st.info("No registered users found.")
    else:
        display_df = df.copy()

        display_df["is_active"] = display_df["is_active"].apply(
            lambda value: (
                "Active"
                if str(value).lower() in ["true", "1", "yes"]
                else "Disabled"
            )
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # ==========================================
    # ROLE MANAGEMENT
    # ==========================================

    st.subheader("🔄 Change User Role")

    admin_id = get_user_value(current_user, "id")

    eligible_users = [
        user for user in users
        if get_user_value(user, "id") != admin_id
    ]

    if eligible_users:

        selected_user = st.selectbox(
            "Select user",
            eligible_users,
            format_func=lambda user: (
                f"{get_user_value(user, 'name', 'Unknown')} "
                f"({get_user_value(user, 'email', 'No email')})"
            ),
            key="admin_role_user"
        )

        selected_role = get_user_value(
            selected_user, "role", "Analyst"
        )

        new_role = st.selectbox(
            "Select new role",
            ["Analyst", "Admin"],
            index=0 if selected_role == "Analyst" else 1,
            key="admin_new_role"
        )

        if st.button("Update Role", key="update_user_role"):

            try:
                selected_id = get_user_value(selected_user, "id")

                if db.update_user_role(selected_id, new_role):
                    st.success("User role updated successfully!")
                    st.rerun()
                else:
                    st.error("Unable to update user role.")

            except Exception as error:
                st.error(f"Role update failed: {error}")

    else:
        st.info("No other users available for role management.")

    st.divider()

    # ==========================================
    # ACCOUNT STATUS MANAGEMENT
    # ==========================================

    st.subheader("⚙️ Account Status")

    if eligible_users:

        selected_status_user = st.selectbox(
            "Select account",
            eligible_users,
            format_func=lambda user: (
                f"{get_user_value(user, 'name', 'Unknown')} "
                f"({get_user_value(user, 'email', 'No email')})"
            ),
            key="admin_status_user"
        )

        current_status = get_user_value(
            selected_status_user, "is_active", True
        )

        is_currently_active = (
            str(current_status).lower() in ["true", "1", "yes"]
        )

        new_status = st.selectbox(
            "Account status",
            ["Active", "Disabled"],
            index=0 if is_currently_active else 1,
            key="admin_account_status"
        )

        if st.button(
            "Update Account Status",
            key="update_account_status"
        ):

            try:
                selected_id = get_user_value(
                    selected_status_user, "id"
                )

                if db.update_user_status(
                    selected_id,
                    new_status == "Active"
                ):
                    st.success("Account status updated successfully!")
                    st.rerun()
                else:
                    st.error("Unable to update account status.")

            except Exception as error:
                st.error(f"Account update failed: {error}")

    else:
        st.info("No other accounts available.")
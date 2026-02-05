import streamlit as st

# ======================== KONFIGURASI LOGIN ========================
# 🔐 Untuk keamanan, ambil dari Streamlit Secrets jika tersedia
if "users" in st.secrets:
    USERS = st.secrets["users"]
else:
    USERS = {
        # "fod": {"password": "fod123", "role": "fod"},
        "user": {"password": "user123", "role": "pengguna"},
    }

# ======================== FUNGSI LOGIN ========================
def login():
    """
    Menampilkan halaman login dengan tampilan profesional dan autentikasi sederhana.
    """
    # 🌅 Background halaman login
    page_bg = """
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    div[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.9);
    }
    </style>
    """
    st.markdown(page_bg, unsafe_allow_html=True)

    # Beri jarak agar form tampil di tengah
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

    # Judul login
    st.markdown(
        "<h2 style='text-align: center; font-size: 40px; color: white;'>🔐 LOGIN</h2>",
        unsafe_allow_html=True
    )

    # === Form Login ===
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info(
            "👥 **Panduan Login:**\n"
            "- **User umum** → username: `user`, password: `user123`\n"
            "- **FOD** → username: `fod`, password: `fod123`\n\n"
            "🛈 Gunakan kredensial sesuai peran Anda."
        )

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if username in USERS and password == USERS[username]["password"]:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = USERS[username]["role"]

                st.success(f"✅ Login berhasil sebagai **{username.upper()}** ({st.session_state['role'].upper()})")
                st.toast("Berhasil login!", icon="✅")

                # Gunakan rerun aman
                st.rerun()
            else:
                st.error("❌ Username atau password salah. Coba lagi.")


# ======================== FUNGSI LOGOUT ========================
def logout():
    """
    Logout user: hapus session state dan rerun aplikasi.
    """
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.toast("Anda telah logout.", icon="👋")
        st.rerun()

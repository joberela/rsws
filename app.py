import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, date

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="Stock Reagen Lab", layout="wide")

TIPE_LIST = ["RS", "WS", "BPFI"]

# ========================
# 🎨 UI PROFESSIONAL
# ========================
st.markdown("""
<style>
/* Background utama (tidak terlalu gelap) */
body {
    background-color: #f9fafb;
    color: #111827;
}

/* Container */
.block-container {
    padding-top: 1.5rem;
}

/* Judul */
h1, h2, h3 {
    color: #dc2626; /* merah utama */
    font-weight: 700;
}

/* CARD (putih bersih) */
.card {
    background: #ffffff;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 12px;
    border-left: 6px solid #dc2626; /* aksen merah */
}

/* Metric */
.metric {
    font-size: 26px;
    font-weight: bold;
    color: #111827;
}

/* Button */
.stButton>button {
    background: #dc2626;
    color: white;
    font-weight: 600;
    border-radius: 8px;
    border: none;
}

.stButton>button:hover {
    background: #b91c1c;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}

/* Input */
input, textarea {
    background-color: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #d1d5db !important;
}

/* Table */
table {
    background-color: white;
    color: #111827;
    border-collapse: collapse;
}

th {
    background-color: #dc2626;
    color: white;
}

td {
    border-bottom: 1px solid #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# ========================
# DB CONNECTION
# ========================
def get_conn():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        dbname=st.secrets["postgres"]["database"],  # ⬅️ ambil dari 'database'
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"],
        sslmode="require"
    )

# ========================
# SESSION LOGIN
# ========================
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.role = None
    st.session_state.username = None

# ========================
# LOGIN
# ========================
def login_page():
    st.title("🔐 Login Sistem Reagen")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT username, role 
        FROM users 
        WHERE username=%s AND password=%s
        """, (username, password))

        user = cur.fetchone()
        conn.close()

        if user:
            st.session_state.login = True
            st.session_state.username = user[0]
            st.session_state.role = user[1]
            st.rerun()
        else:
            st.error("❌ Login gagal")

def logout_button():
    if st.button("🚪 Logout"):
        st.session_state.login = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

# ========================
# CHECK LOGIN
# ========================
if not st.session_state.login:
    login_page()
    st.stop()

# ========================
# HEADER
# ========================
st.markdown(f"""
<div class="card">
    <h2>🧪 SMART LAB MANAGEMENT SYSTEM</h2>
    <p>Realtime Monitoring Reagen • Audit Friendly</p>
    <p>👤 {st.session_state.username} ({st.session_state.role})</p>
</div>
""", unsafe_allow_html=True)

# ========================
# KPI (TAMBAHAN UI SAJA)
# ========================
conn = get_conn()
df_all = pd.read_sql("SELECT * FROM stock", conn)
conn.close()

col1, col2, col3 = st.columns(3)

col1.markdown(f'<div class="card"><div class="metric">{len(df_all)}</div>Total</div>', unsafe_allow_html=True)
col2.markdown(f'<div class="card"><div class="metric">{len(df_all[df_all["status"]=="Aktif"])}</div>Aktif</div>', unsafe_allow_html=True)
col3.markdown(f'<div class="card"><div class="metric">{len(df_all[df_all["status"]=="Habis"])}</div>Habis</div>', unsafe_allow_html=True)

# ========================
# MENU
# ========================
if st.session_state.role == "superadmin":
    menu = st.radio("", ["Input", "Penggunaan", "Stock", "Histori", "Admin", "User", "Report"], horizontal=True)
else:
    menu = st.radio("", ["Penggunaan", "Stock", "Histori"], horizontal=True)

logout_button()
st.divider()

# ========================
# INPUT STOCK
# ========================
if menu == "Input":

    st.title("📥 Input Stock")

    col1, col2 = st.columns(2)

    with col1:
        kode = st.text_input("Kode")
        nama = st.text_input("Nama")
        tipe = st.selectbox("Tipe", TIPE_LIST)
        tanggal_datang = st.date_input("Tanggal Datang")

    with col2:
        batch = st.text_input("Batch")
        jumlah = st.number_input("Jumlah", min_value=0.0)
        tanggal_expired = st.date_input("Expired")

    if st.button("Simpan"):
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO stock 
        (kode_stock, nama, tipe, batch, jumlah_awal, jumlah_sisa, status, tanggal_datang, tanggal_expired, tanggal_input)
        VALUES (%s,%s,%s,%s,%s,%s,'Non-Aktif',%s,%s,%s)
        """, (
            kode, nama, tipe, batch,
            jumlah, jumlah,
            tanggal_datang,
            tanggal_expired,
            datetime.now()
        ))

        conn.commit()
        conn.close()

        st.success("OK")

# ========================
# PENGGUNAAN
# ========================
elif menu == "Penggunaan":

    st.title("⚗️ Penggunaan Reagen")

    conn = get_conn()

    df = pd.read_sql("""
    SELECT * FROM stock 
    WHERE status='Aktif'
    ORDER BY tanggal_input ASC
    """, conn)

    conn.close()

    if df.empty:
        st.warning("Tidak ada stock aktif")
        st.stop()

    # ========================
    # FORMAT EXPIRY
    # ========================
    df["tanggal_expired"] = pd.to_datetime(df["tanggal_expired"], errors='coerce')

    # ========================
    # TABEL STOK (ADA SISA JELAS)
    # ========================
    st.subheader("📦 Stok Tersedia")

    st.dataframe(
        df[[
            "nama",
            "kode_stock",
            "tipe",
            "jumlah_sisa",
            "tanggal_expired"
        ]].rename(columns={
            "jumlah_sisa": "Sisa Stok"
        }),
        use_container_width=True
    )

    # ========================
    # LABEL SELECT (SISA DITAMPILKAN JELAS)
    # ========================
    df["label"] = (
        df["nama"] + " | " +
        df["kode_stock"] + " | " +
        df["tipe"] + " | SISA: " +
        df["jumlah_sisa"].astype(str)
    )

    selected = st.selectbox("Pilih Reagen", df["label"])

    stock = df[df["label"] == selected].iloc[0]

    # ========================
    # INFO REAL TIME
    # ========================
    st.info(f"""
    📌 Detail Stock:
    - Nama: {stock['nama']}
    - Kode: {stock['kode_stock']}
    - Tipe: {stock['tipe']}
    - 🔢 Sisa: {stock['jumlah_sisa']}
    - 📅 Expired: {stock['tanggal_expired'].date() if pd.notna(stock['tanggal_expired']) else '-'}
    """)

    jumlah = st.number_input("Jumlah Pakai", min_value=0.0)
    ket = st.text_input("Keterangan")

    st.info(f"👤 User: {st.session_state.username}")

    # ========================
    # ACTION
    # ========================
    if st.button("Gunakan"):

        if pd.notna(stock["tanggal_expired"]) and stock["tanggal_expired"] < pd.to_datetime(date.today()):
            st.error("❌ Stock expired")
        else:
            sisa = float(stock["jumlah_sisa"]) - jumlah

            if sisa < 0:
                st.error(f"❌ Stok tidak cukup (Sisa hanya {stock['jumlah_sisa']})")
            else:
                conn = get_conn()
                cur = conn.cursor()

                cur.execute("""
                INSERT INTO usage_log 
                (stock_id, jumlah, keterangan, waktu, sisa_setelah, user_pengguna)
                VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    int(stock["id"]),
                    jumlah,
                    ket,
                    datetime.now(),
                    sisa,
                    st.session_state.username
                ))

                cur.execute("""
                UPDATE stock 
                SET jumlah_sisa=%s, status=%s 
                WHERE id=%s
                """, (
                    sisa,
                    "Habis" if sisa == 0 else "Aktif",
                    int(stock["id"])
                ))

                conn.commit()
                conn.close()

                st.success(f"✅ Berhasil digunakan. Sisa sekarang: {sisa}")

# ========================
# STOCK VIEW
# ========================
elif menu == "Stock":

    st.title("📊 Stock")

    conn = get_conn()

    df = pd.read_sql("SELECT * FROM stock ORDER BY tanggal_input DESC", conn)

    conn.close()

    st.dataframe(df)

# ========================
# HISTORI
# ========================
elif menu == "Histori":

    st.title("📜 Histori Penggunaan Reagen")

    conn = get_conn()

    df = pd.read_sql("""
    SELECT 
        s.nama, 
        s.kode_stock, 
        s.tipe,
        u.jumlah, 
        u.sisa_setelah, 
        u.keterangan, 
        u.waktu,
        u.user_pengguna
    FROM usage_log u
    JOIN stock s ON u.stock_id = s.id
    ORDER BY u.waktu DESC
    """, conn)

    conn.close()

    # ========================
    # 🔍 FILTER SECTION
    # ========================
    st.subheader("🔍 Filter Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        nama_list = ["Semua"] + sorted(df["nama"].dropna().unique().tolist())
        filter_nama = st.selectbox("Nama Reagen", nama_list)

    with col2:
        tipe_list = ["Semua"] + sorted(df["tipe"].dropna().unique().tolist())
        filter_tipe = st.selectbox("Tipe", tipe_list)

    with col3:
        kode_list = ["Semua"] + sorted(df["kode_stock"].dropna().unique().tolist())
        filter_kode = st.selectbox("Kode Stock", kode_list)

    # ========================
    # APPLY FILTER
    # ========================
    df_filter = df.copy()

    if filter_nama != "Semua":
        df_filter = df_filter[df_filter["nama"] == filter_nama]

    if filter_tipe != "Semua":
        df_filter = df_filter[df_filter["tipe"] == filter_tipe]

    if filter_kode != "Semua":
        df_filter = df_filter[df_filter["kode_stock"] == filter_kode]

    # ========================
    # RESULT
    # ========================
    st.subheader("📊 Hasil Histori")

    st.dataframe(df_filter, use_container_width=True)

    st.info(f"Total data: {len(df_filter)}")

# ========================
# ADMIN (TIDAK DIHAPUS)
# ========================
elif menu == "Admin":

    st.title("⚙️ Admin Stock Control")

    conn = get_conn()
    df = pd.read_sql("SELECT * FROM stock ORDER BY tanggal_input DESC", conn)

    df["tanggal_expired"] = pd.to_datetime(df["tanggal_expired"], errors='coerce')
    df["tanggal_datang"] = pd.to_datetime(df["tanggal_datang"], errors='coerce')

    today = pd.to_datetime(date.today())
    df["sisa_hari"] = (df["tanggal_expired"] - today).dt.days

    # ========================
    # WARNING EXPIRED
    # ========================
    warning_df = df[(df["sisa_hari"] <= 30) & (df["sisa_hari"] >= 0)]
    expired_df = df[df["sisa_hari"] < 0]

    if not warning_df.empty:
        st.error("🚨 EXPIRY WARNING (≤30 hari)")
        st.dataframe(warning_df[["nama","kode_stock","tipe","tanggal_expired","sisa_hari","jumlah_sisa"]])

    if not expired_df.empty:
        st.error("❌ EXPIRED STOCK")
        st.dataframe(expired_df[["nama","kode_stock","tipe","tanggal_expired","jumlah_sisa"]])

    st.divider()

    # ========================
    # 📊 SPLIT TABLE STOCK
    # ========================
    st.subheader("📊 Ketersediaan Stock")

    aktif = df[df["status"] == "Aktif"]
    nonaktif = df[df["status"] == "Non-Aktif"]
    habis = df[df["status"] == "Habis"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🟢 Aktif")
        st.dataframe(aktif[
            ["nama","kode_stock","tipe","tanggal_datang","tanggal_expired","jumlah_sisa"]
        ], use_container_width=True)

    with col2:
        st.markdown("### 🟡 Non-Aktif")
        st.dataframe(nonaktif[
            ["nama","kode_stock","tipe","tanggal_datang","tanggal_expired","jumlah_sisa"]
        ], use_container_width=True)

    with col3:
        st.markdown("### 🔴 Habis")
        st.dataframe(habis[
            ["nama","kode_stock","tipe","tanggal_datang","tanggal_expired","jumlah_sisa"]
        ], use_container_width=True)

    st.divider()

    # ========================
    # UPDATE STATUS
    # ========================
    st.subheader("🔧 Update Status Stock")

    df["label"] = df["nama"] + " | " + df["kode_stock"]

    selected = st.selectbox("Pilih Stock", df["label"])
    stock = df[df["label"] == selected].iloc[0]

    status_baru = st.selectbox("Set Status Baru", ["Aktif", "Non-Aktif", "Habis"])

    if st.button("Update Status"):

        cur = conn.cursor()

        if status_baru == "Habis":
            cur.execute("""
            UPDATE stock 
            SET status='Habis', jumlah_sisa=0 
            WHERE id=%s
            """, (int(stock["id"]),))
        else:
            cur.execute("""
            UPDATE stock 
            SET status=%s 
            WHERE id=%s
            """, (status_baru, int(stock["id"])))

        conn.commit()
        conn.close()

        st.success("✅ Status stock berhasil diupdate")
        

        # ========================
        # ✏️ EDIT STOCK (FIX MUNCUL)
        # ========================
        st.divider()
        st.subheader("✏️ Edit Jumlah & Expired")

        # pastikan df masih ada
        df_edit = df.copy()

        df_edit["label_edit"] = df_edit["nama"] + " | " + df_edit["kode_stock"]

        selected_edit = st.selectbox("Pilih Stock untuk Edit", df_edit["label_edit"], key="edit_select")

        stock_edit = df_edit[df_edit["label_edit"] == selected_edit].iloc[0]

        col1, col2 = st.columns(2)

        with col1:
            new_jumlah = st.number_input(
                "Jumlah Sisa Baru",
                value=float(stock_edit["jumlah_sisa"]),
                min_value=0.0,
                key="edit_jumlah"
            )

        with col2:
            default_date = stock_edit["tanggal_expired"]
            if pd.isna(default_date):
                default_date = date.today()
            else:
                default_date = default_date.date()

            new_expired = st.date_input(
                "Tanggal Expired Baru",
                value=default_date,
                key="edit_expired"
            )

        # preview sisa hari otomatis
        preview_sisa_hari = (pd.to_datetime(new_expired) - pd.to_datetime(date.today())).days
        st.info(f"📅 Sisa Hari Otomatis: {preview_sisa_hari} hari")

        # tombol update
        if st.button("💾 Update Data Stock", key="btn_update_stock"):

            conn2 = get_conn()
            cur2 = conn2.cursor()

            cur2.execute("""
            UPDATE stock
            SET jumlah_sisa=%s,
                tanggal_expired=%s
            WHERE id=%s
            """, (
                new_jumlah,
                new_expired,
                int(stock_edit["id"])
            ))

            conn2.commit()
            conn2.close()

            st.success("✅ Data berhasil diperbarui")
            st.rerun()


# ========================
# 👥 USER MANAGEMENT (NEW TAB)
# ========================
elif menu == "User":

    st.title("👥 User Management")

    conn = get_conn()

    df_user = pd.read_sql("SELECT id, username, role FROM users ORDER BY id ASC", conn)

    st.subheader("📋 Data User")
    st.dataframe(df_user, use_container_width=True)

    st.divider()

    st.subheader("➕ Tambah User")

    new_user = st.text_input("Username Baru")
    new_pass = st.text_input("Password Baru", type="password")
    new_role = st.selectbox("Role", ["staff", "superadmin"])

    if st.button("Tambah User"):
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO users (username, password, role)
        VALUES (%s,%s,%s)
        """, (new_user, new_pass, new_role))

        conn.commit()
        st.success("User ditambah")

    st.divider()

    st.subheader("✏️ Edit User")

    user_select = st.selectbox("Pilih User", df_user["username"])
    user_data = df_user[df_user["username"] == user_select].iloc[0]

    edit_pass = st.text_input("Password Baru")
    edit_role = st.selectbox("Role Baru", ["staff", "superadmin"])

    if st.button("Update User"):
        cur = conn.cursor()

        cur.execute("""
        UPDATE users 
        SET password=%s, role=%s 
        WHERE id=%s
        """, (edit_pass, edit_role, int(user_data["id"])))

        conn.commit()
        st.success("User diupdate")

# ========================
# REPORT
# ========================
elif menu == "Report":

    st.title("📥 Report")

    conn = get_conn()

    df_stock = pd.read_sql("SELECT * FROM stock", conn)
    df_usage = pd.read_sql("SELECT * FROM usage_log", conn)

    conn.close()

    file = "report.xlsx"

    with pd.ExcelWriter(file) as writer:
        df_stock.to_excel(writer, sheet_name="Stock", index=False)
        df_usage.to_excel(writer, sheet_name="Usage", index=False)

    with open(file, "rb") as f:
        st.download_button("Download", f, file_name=file)

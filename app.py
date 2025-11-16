import streamlit as st
import pandas as pd
from datetime import date
import os
from io import BytesIO
import json


# ========================
# SISTEM LOGIN SEDERHANA
# ========================


USER_FILE = "users.json"


# --- Load data user ---
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}


# --- Simpan user ---
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)


# ----------------------------
# HALAMAN LOGIN / REGISTER
# ----------------------------
def login_page():
    st.title("🔐 Login Kartu Persediaan")


    tab_login, tab_register, tab_forgot = st.tabs(["Login", "Register", "Lupa Password"])
    users = load_users()


# ------------ LOGIN ------------
    with tab_login:
        st.subheader("Masuk ke Akun Anda")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        login_btn = st.button("Login")


        if login_btn:
            if email in users and users[email]["password"] == password:
                st.session_state["login"] = True
                st.session_state["user"] = email
                st.success("Login berhasil!")
                st.rerun()
            else:
                st.error("Email atau password salah!")


# ------------ REGISTER ------------
    with tab_register:
        st.subheader("Buat Akun Baru")
        reg_email = st.text_input("Email Baru")
        reg_pass = st.text_input("Password Baru", type="password")
        reg_btn = st.button("Register")


        if reg_btn:
            if reg_email in users:
                st.warning("Email sudah terdaftar!")
            else:
                users[reg_email] = {"password": reg_pass}
                save_users(users)
                st.success("Akun berhasil dibuat! Silakan login.")


# ------------ LUPA PASSWORD ------------
    with tab_forgot:
        st.subheader("Reset Password")
        forgot_email = st.text_input("Masukkan Email Terdaftar")
        new_pass = st.text_input("Password Baru", type="password")
        reset_btn = st.button("Reset Password")


        if reset_btn:
            if forgot_email in users:
                users[forgot_email]["password"] = new_pass
                save_users(users)
                st.success("Password berhasil direset. Silakan login kembali.")
            else:
                st.error("Email tidak ditemukan!")
# =============================
# HALAMAN UTAMA PERSEDIAAN
# =============================

def main_app():
    st.set_page_config("Kartu Persediaan Multi Barang", layout="centered")
    st.title("📦 Kartu Persediaan Multi Barang")

    DATA_FOLDER = "data_persediaan"

    # Load data persediaan dari file
    def load_data():
        data = {}
        saldo = {}
        if os.path.exists(DATA_FOLDER):
            for file in os.listdir(DATA_FOLDER):
                if file.endswith(".csv"):
                    nama = file.replace(".csv", "")
                    df = pd.read_csv(os.path.join(DATA_FOLDER, file))
                    data[nama] = df
                    if len(df) > 0:
                        saldo_qty = df.iloc[-1]["Saldo (Qty)"]
                        saldo_nilai = df.iloc[-1]["Saldo (Nilai)"]
                    else:
                        saldo_qty = 0
                        saldo_nilai = 0
                    saldo[nama] = {"qty": saldo_qty, "nilai": saldo_nilai}
        return data, saldo

    def save_data():
        os.makedirs(DATA_FOLDER, exist_ok=True)
        for nama, df in st.session_state["persediaan"].items():
            df.to_csv(os.path.join(DATA_FOLDER, f"{nama}.csv"), index=False)

    if "persediaan" not in st.session_state:
        data, saldo = load_data()
        st.session_state["persediaan"] = data
        st.session_state["saldo"] = saldo

    st.sidebar.header(f"👤 Login sebagai: {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    # Input nama barang baru
    nama_barang = st.sidebar.text_input("Nama Barang Baru")
    if st.sidebar.button("Tambah Barang") and nama_barang:
        if nama_barang not in st.session_state["persediaan"]:
            st.session_state["persediaan"][nama_barang] = pd.DataFrame(columns=[
                "Tanggal", "Keterangan", "Masuk (Qty)", "Harga Beli",
                "Keluar (Qty)", "Harga Jual", "Saldo (Qty)", "Saldo (Nilai)"
            ])
            st.session_state["saldo"][nama_barang] = {"qty": 0, "nilai": 0}
            st.success(f"Barang '{nama_barang}' berhasil ditambahkan!")
        else:
            st.warning(f"Barang '{nama_barang}' sudah ada.")

    # Pilih barang
    if st.session_state["persediaan"]:
        pilihan_barang = st.sidebar.selectbox("Pilih Barang", list(st.session_state["persediaan"].keys()))
    else:
        st.info("Tambahkan barang terlebih dahulu.")
        return

    # Input transaksi
    st.subheader(f"Input Transaksi untuk Barang: {pilihan_barang}")
    jenis = st.selectbox("Jenis Transaksi", ["Pembelian", "Penjualan"])
    tanggal = st.date_input("Tanggal", date.today())
    keterangan = st.text_input("Keterangan", f"Transaksi {jenis}")
    qty = st.number_input("Jumlah Barang (Qty)", min_value=1, step=1)

    harga = st.number_input(
        "Harga Beli per Unit" if jenis == "Pembelian" else "Harga Jual per Unit",
        min_value=0.0,
        step=100.0,
    )

    if st.button("Simpan Transaksi"):
        df = st.session_state["persediaan"][pilihan_barang]
        saldo = st.session_state["saldo"][pilihan_barang]

        if jenis == "Pembelian":
            total_beli = qty * harga
            saldo["qty"] += qty
            saldo["nilai"] += total_beli

            new_row = {
                "Tanggal": tanggal,
                "Keterangan": keterangan,
                "Masuk (Qty)": qty,
                "Harga Beli": harga,
                "Keluar (Qty)": 0,
                "Harga Jual": 0,
                "Saldo (Qty)": saldo["qty"],
                "Saldo (Nilai)": saldo["nilai"],
            }
        else:
            if qty > saldo["qty"]:
                st.warning("⚠️ Stok tidak cukup!")
                return
            hpp_per_unit = saldo["nilai"] / saldo["qty"] if saldo["qty"] > 0 else 0
            saldo["qty"] -= qty
            saldo["nilai"] -= hpp_per_unit * qty

            new_row = {
                "Tanggal": tanggal,
                "Keterangan": keterangan,
                "Masuk (Qty)": 0,
                "Harga Beli": 0,
                "Keluar (Qty)": qty,
                "Harga Jual": harga,
                "Saldo (Qty)": saldo["qty"],
                "Saldo (Nilai)": saldo["nilai"],
            }

        st.session_state["persediaan"][pilihan_barang] = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state["saldo"][pilihan_barang] = saldo
        save_data()
        st.success("Transaksi berhasil disimpan!")

    # Tampilkan kartu persediaan
    st.subheader(f"📘 Kartu Persediaan: {pilihan_barang}")
    df_barang = st.session_state["persediaan"][pilihan_barang]
    st.dataframe(df_barang, use_container_width=True)

    saldo = st.session_state["saldo"][pilihan_barang]
    st.subheader("📊 Ringkasan Akhir")
    st.metric("Total Stok (Qty)", saldo["qty"])
    st.metric("Total Nilai Persediaan (Rp)", f"{saldo['nilai']:,}")

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_barang.to_excel(writer, index=False, sheet_name=pilihan_barang)

    st.download_button(
        label="📥 Download Kartu Persediaan",
        data=buffer.getvalue(),
        file_name=f"Kartu_Persediaan_{pilihan_barang}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# =============================
# MULAI APLIKASI
# =============================

if "login" not in st.session_state:
    st.session_state["login"] = False

if st.session_state["login"]:
    main_app()
else:
    login_page()

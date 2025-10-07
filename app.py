import streamlit as st
import pandas as pd
from datetime import date
import os
from io import BytesIO


st.set_page_config("Kartu Persediaan - Average Method", layout="centered")
st.title("📊 Kartu Persediaan (Metode Average)")

# --- Folder Data ---
DATA_FOLDER = "data_persediaan_average"

def load_data():
    data = {}
    if os.path.exists(DATA_FOLDER):
        for file in os.listdir(DATA_FOLDER):
            if file.endswith(".csv"):
                nama = file.replace(".csv", "")
                data[nama] = pd.read_csv(os.path.join(DATA_FOLDER, file))
    return data

def save_data():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    for nama, df in st.session_state["persediaan"].items():
        df.to_csv(os.path.join(DATA_FOLDER, f"{nama}.csv"), index=False)

# --- Inisialisasi ---
if "persediaan" not in st.session_state:
    st.session_state["persediaan"] = load_data()

st.subheader("📦 Input Saldo Awal Persediaan")

barang_saldo = st.selectbox("Pilih Barang untuk Saldo Awal", list(st.session_state["persediaan"].keys()))

jumlah_awal = st.number_input("Jumlah Awal", min_value=0, step=1, key="jumlah_awal")
harga_awal = st.number_input("Harga per Unit", min_value=0.0, step=100.0, key="harga_awal")

if st.button("Simpan Saldo Awal"):
    df_barang = st.session_state["persediaan"][barang_saldo]

    # Cek apakah sudah ada saldo awal sebelumnya
    if not any(df_barang["Description"] == "Saldo Awal"):
        data_baru = pd.DataFrame({
            "Tanggal": [pd.Timestamp.now().strftime("%Y-%m-%d")],
            "Doc No": [""],
            "Description": ["Saldo Awal"],
            "Purchase Qty": [jumlah_awal],
            "Purchase Price": [harga_awal],
            "Purchase Amount": [jumlah_awal * harga_awal],
            "Sales Qty": [0],
            "Sales Price": [0],
            "Sales Amount": [0],
            "Balance Qty": [jumlah_awal],
            "Balance Price": [harga_awal],
            "Balance Amount": [jumlah_awal * harga_awal],
        })
        st.session_state["persediaan"][barang_saldo] = pd.concat([data_baru, df_barang], ignore_index=True)
        save_data()
        st.success(f"✅ Saldo awal untuk {barang_saldo} berhasil disimpan!")
        st.rerun()
    else:
        st.warning("⚠️ Saldo awal sudah pernah dimasukkan untuk barang ini.")    

# --- Input Barang ---
st.sidebar.header("⚙️ Barang")
nama_barang = st.sidebar.text_input("Nama Barang Baru", "")
if st.sidebar.button("Tambah Barang") and nama_barang:
    if nama_barang not in st.session_state["persediaan"]:
        st.session_state["persediaan"][nama_barang] = pd.DataFrame(columns=[
            "Tanggal", "Doc No", "Description",
            "Purchase Qty", "Purchase Price", "Purchase Amount",
            "Sales Qty", "Sales Price", "Sales Amount",
            "Balance Qty", "Balance Price", "Balance Amount"
        ])
        st.success(f"Barang '{nama_barang}' berhasil ditambahkan!")
    else:
        st.warning(f"Barang '{nama_barang}' sudah ada.")

# --- Pilih Barang ---
if not st.session_state["persediaan"]:
    st.info("Tambahkan barang terlebih dahulu.")
    st.stop()

pilihan_barang = st.sidebar.selectbox("Pilih Barang", list(st.session_state["persediaan"].keys()))
df = st.session_state["persediaan"][pilihan_barang]

# --- Input Transaksi ---
st.subheader(f"Transaksi untuk {pilihan_barang}")
tanggal = st.date_input("Tanggal", date.today())
doc_no = st.text_input("Doc No (Nomor Bukti)", "")
desc = st.text_input("Keterangan / Deskripsi", "")
jenis = st.selectbox("Jenis Transaksi", ["Pembelian", "Penjualan"])
qty = st.number_input("Jumlah Barang", min_value=1, key="jumlah_transaksi")
harga = st.number_input("Harga per Unit", min_value=0.0, step=100.0, key="harga_transaksi")

# Hitung saldo lama
if len(df) > 0:
    saldo_qty = df.iloc[-1]["Balance Qty"]
    saldo_nilai = df.iloc[-1]["Balance Amount"]
    saldo_harga = df.iloc[-1]["Balance Price"]
else:
    saldo_qty = 0
    saldo_nilai = 0
    saldo_harga = 0

# --- Simpan Transaksi ---
if st.button("💾 Simpan Transaksi"):
    if jenis == "Pembelian":
        # Hitung saldo baru dengan metode average
        total_beli = qty * harga
        new_qty = saldo_qty + qty
        new_total = saldo_nilai + total_beli
        avg_price = new_total / new_qty if new_qty != 0 else 0

        new_row = {
            "Tanggal": tanggal,
            "Doc No": doc_no,
            "Description": desc,
            "Purchase Qty": qty,
            "Purchase Price": harga,
            "Purchase Amount": total_beli,
            "Sales Qty": 0,
            "Sales Price": 0,
            "Sales Amount": 0,
            "Balance Qty": new_qty,
            "Balance Price": avg_price,
            "Balance Amount": new_total,
        }       

    else:  # Penjualan
        if qty > saldo_qty:
            st.warning("⚠️ Stok tidak cukup!")
            st.stop()
        total_jual = qty * harga
        hpp = qty * saldo_harga
        new_qty = saldo_qty - qty
        new_total = saldo_nilai - hpp

        new_row = {
            "Tanggal": tanggal,
            "Doc No": doc_no,
            "Description": desc,
            "Purchase Qty": 0,
            "Purchase Price": 0,
            "Purchase Amount": 0,
            "Sales Qty": qty,
            "Sales Price": harga,
            "Sales Amount": total_jual,
            "Balance Qty": new_qty,
            "Balance Price": saldo_harga,
            "Balance Amount": new_total,
        }

    st.session_state["persediaan"][pilihan_barang] = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data()
    st.success("✅ Transaksi berhasil disimpan!")

# --- Tampilkan Data ---
st.subheader(f"📘 Kartu Persediaan - {pilihan_barang}")
st.dataframe(st.session_state["persediaan"][pilihan_barang], use_container_width=True)

# --- Unduh Excel ---
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    st.session_state["persediaan"][pilihan_barang].to_excel(writer, index=False, sheet_name="Kartu Persediaan")

st.download_button(
    "📥 Download Excel",
    data=buffer.getvalue(),
    file_name=f"Kartu_Persediaan_{pilihan_barang}_Average.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- FITUR HAPUS TRANSAKSI ---
st.subheader("🗑️ Hapus Transaksi")

df_barang = st.session_state["persediaan"][pilihan_barang]

if len(df_barang) > 0:
    # Menampilkan daftar transaksi dengan nomor baris
    df_barang_display = df_barang.copy()
    df_barang_display["Index"] = df_barang_display.index
    st.dataframe(df_barang_display, use_container_width=True)

    # Pilih transaksi yang mau dihapus
    index_hapus = st.number_input(
        "Masukkan nomor index transaksi yang ingin dihapus",
        min_value=0,
        max_value=len(df_barang) - 1,
        step=1
    )

    if st.button("Hapus Transaksi"):
        st.session_state["persediaan"][pilihan_barang] = df_barang.drop(index=index_hapus).reset_index(drop=True)
        save_data()
        st.success(f"✅ Transaksi ke-{index_hapus} berhasil dihapus!")
        st.rerun()
else:
    st.info("Belum ada transaksi untuk dihapus.")
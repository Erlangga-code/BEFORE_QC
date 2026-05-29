import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONEKSI DATABASE
conn = sqlite3.connect("qc_data.db", check_same_thread=False)
cursor = conn.cursor()

def buat_tabel():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaksi_qc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tanggal TEXT,
        nama_part TEXT,
        qty INTEGER,
        keterangan TEXT,
        area TEXT
    )
    """)
    conn.commit()

buat_tabel()

# Daftar part lengkap
LIST_PART = [
    "Casing Cap", "Bolt Rear", "Reinf 2PK-F4766-00", 
    "Boss Footrest 5BP", "REINF - BDJ-F4766", 
    "PLATE BOLT - KW2504", "BRACKET SEAT L - BDJ-F4718", "INSERT BRACKET STOPPER"
]

# PENGATURAN HALAMAN (Layout diatur tetap 'wide', namun responsif via elemen html)
st.set_page_config(page_title="QC Input Real-Time", layout="wide")

# CSS Tambahan agar Form dan Tabel muat sempurna saat dibuka di layar HP yang kecil
st.markdown("""
    <style>
    /* Mengatur padding utama agar lebih ramah layar HP */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    /* Memastikan tabel horizontal bisa di-scroll dengan mulus di HP */
    .stDataFrame {
        width: 100% !important;
        overflow-x: auto !important;
    }
    /* Memperbesar tombol di HP agar mudah ditekan jari */
    div.stButton > button:first-child {
        width: 100% !important;
        height: 3rem !important;
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 BEFORE CEK QC")

# Tab dibuat besar agar mudah berpindah di layar sentuh HP
tab1, tab2 = st.tabs(["📝 INPUT LAPANGAN", "🖥️ MONITORING & REKAP"])

# ==========================================
# TAB 1: FORM INPUT LAPANGAN (RESPONSIF)
# ==========================================
with tab1:
    st.subheader("Form Operator Lapangan")
    
    with st.form(key="form_qc", clear_on_submit=True):
        input_tgl = st.date_input("Tanggal", datetime.now())
        input_part = st.selectbox("Nama Part", LIST_PART)
        input_qty = st.number_input("Quantity (Qty) Baru Masuk", min_value=1, step=1, value=1)
        input_ket = st.text_input("Keterangan (Catatan)", placeholder="Ketik catatan di sini...")
        
        input_area = st.selectbox(
            "Area Posisi Barang", 
            ["QC PRODUKSI", "WAREHOUSE", "QC PRODUKSI & WAREHOUSE"]
        )
        
        submit_button = st.form_submit_button(label="🚀 Simpan Data")
        
        if submit_button:
            keterangan_capslock = input_ket.upper().strip()
            
            cursor.execute("""
                INSERT INTO transaksi_qc (tanggal, nama_part, qty, keterangan, area)
                VALUES (?, ?, ?, ?, ?)
            """, (input_tgl.strftime("%Y-%m-%d"), input_part, input_qty, keterangan_capslock, input_area))
            conn.commit()
            st.success(f"Berhasil Tersimpan!")

# ==========================================
# TAB 2: MONITORING & REKAP
# ==========================================
with tab2:
    st.subheader("Tabel Rekap (Kondisi Real-Time)")
    
    df = pd.read_sql_query("SELECT id, tanggal, nama_part, qty, keterangan, area FROM transaksi_qc ORDER BY id ASC", conn)
    
    if not df.empty:
        df['tanggal_dt'] = pd.to_datetime(df['tanggal'])
        df['tanggal_format'] = df['tanggal_dt'].dt.strftime('%d-%b-%y')
        
        df_pivot = df.pivot_table(
            index='nama_part', 
            columns='tanggal_format', 
            values='qty', 
            aggfunc='sum'
        ).reset_index()
        
        def tentukan_status_area(nama_barang):
            areas_terpakai = df[df['nama_part'] == nama_barang]['area'].unique()
            if "QC PRODUKSI & WAREHOUSE" in areas_terpakai or ("QC PRODUKSI" in areas_terpakai and "WAREHOUSE" in areas_terpakai):
                return "QC PRODUKSI & WAREHOUSE"
            elif "QC PRODUKSI" in areas_terpakai:
                return "QC PRODUKSI"
            elif "WAREHOUSE" in areas_terpakai:
                return "WAREHOUSE"
            return "QC PRODUKSI"
            
        df_terakhir = df.groupby('nama_part').last().reset_index()
        def ambil_keterangan_terbaru(nama_barang):
            ket = df_terakhir[df_terakhir['nama_part'] == nama_barang]['keterangan'].values[0]
            if pd.isna(ket) or str(ket).strip() == "":
                return "-"
            return str(ket)

        df_pivot['area'] = df_pivot['nama_part'].apply(tentukan_status_area)
        df_pivot['keterangan'] = df_pivot['nama_part'].apply(ambil_keterangan_terbaru)
        
        df_master = pd.DataFrame(LIST_PART, columns=['nama_part'])
        df_final = pd.merge(df_master, df_pivot, on='nama_part', how='left')
        
        df_final['area'] = df_final['area'].fillna("QC PRODUKSI")
        df_final['keterangan'] = df_final['keterangan'].fillna("-")
        
        semua_tanggal = [col for col in df_final.columns if col not in ['nama_part', 'area', 'keterangan']]
        tanggal_diurutkan = sorted(semua_tanggal, key=lambda x: datetime.strptime(x, '%d-%b-%y'))
        
        kolom_tanggal_5_hari = tanggal_diurutkan[-5:]
        
        susunan_kolom = ['nama_part'] + kolom_tanggal_5_hari + ['keterangan', 'area']
        df_tampilan = df_final[susunan_kolom]
        
        filter_angka = st.checkbox("🔍 Hanya Tampilkan Data Berangka (Siap Share WA)", value=False)
        if filter_angka:
            kondisi = df_tampilan[kolom_tanggal_5_hari].notna().any(axis=1)
            df_tampilan = df_tampilan[kondisi]
            
        df_tampilan = df_tampilan.fillna("-")
        
        for tgl in kolom_tanggal_5_hari:
            df_tampilan[tgl] = df_tampilan[tgl].apply(lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) else x)
        
        def beri_style_kondisi(row):
            gaya_merah = "color: #FF4B4B; font-weight: bold; font-style: italic;"
            gaya_hijau = "color: #00D26A; font-weight: bold; font-style: italic;"
            gaya_kuning = "color: #FFCC00; font-weight: bold; font-style: italic;"
            
            styles = [""] * len(row)
            idx_part = row.index.get_loc('nama_part')
            idx_area = row.index.get_loc('area')
            
            if row['area'] == "QC PRODUKSI & WAREHOUSE":
                gaya_pilihan = gaya_kuning
            elif row['area'] == "QC PRODUKSI":
                gaya_pilihan = gaya_merah
            elif row['area'] == "WAREHOUSE":
                gaya_pilihan = gaya_hijau
            else:
                gaya_pilihan = ""
                
            styles[idx_part] = gaya_pilihan
            styles[idx_area] = gaya_pilihan
            return styles

        df_styled = df_tampilan.style.apply(beri_style_kondisi, axis=1)
        
        # Ditampilkan menggunakan container lebar otomatis agar pas di layar kecil
        st.dataframe(df_styled, use_container_width=True, hide_index=True)
        
        # AREA RESET
        st.markdown("---")
        if st.button("🗑️ Kosongkan Seluruh Tabel Monitoring"):
            cursor.execute("DROP TABLE IF EXISTS transaksi_qc")
            conn.commit()
            buat_tabel()
            st.success("Tabel dibersihkan!")
            st.rerun()
            
    else:
        st.info("Belum ada data transaksi. Silakan isi form terlebih dahulu.")
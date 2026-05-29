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

st.set_page_config(page_title="QC Input Real-Time", layout="wide")

# Script capture layar menggunakan html2canvas yang diarahkan ke id "tabel-rekap"
st.markdown("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    function gasScreenshot() {
        var element = document.getElementById('tabel-rekap');
        if(element) {
            html2canvas(element, {
                backgroundColor: '#111111',
                scale: 2, // Biar hasil gambar tajam tidak pecah
                logging: false
            }).then(function(canvas) {
                var link = document.createElement('a');
                link.download = 'REKAP_BEFORE_CEK_QC.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            });
        } else {
            alert('Gagal mengambil data tabel, silahkan coba lagi.');
        }
    }
    </script>
    <style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
    /* Style Tabel HTML biar mirip Excel Premium */
    .table-responsive {
        width: 100%;
        overflow-x: auto;
        background-color: #111111;
        padding: 10px;
        border-radius: 8px;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        color: white;
        font-family: sans-serif;
        font-size: 14px;
        min-width: 800px;
    }
    .custom-table th {
        background-color: #1E1E1E;
        color: #FFCC00;
        font-weight: bold;
        text-align: center;
        padding: 12px 8px;
        border: 1px solid #333;
        text-transform: uppercase;
    }
    .custom-table td {
        padding: 10px 8px;
        border: 1px solid #333;
        text-align: center;
    }
    /* Warna Status Text */
    .text-merah { color: #FF4B4B !important; font-weight: bold; font-style: italic; }
    .text-hijau { color: #00D26A !important; font-weight: bold; font-style: italic; }
    .text-kuning { color: #FFCC00 !important; font-weight: bold; font-style: italic; }
    
    /* Tombol SS Besar */
    .btn-ss {
        background-color: #075E54 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        padding: 12px;
        width: 100%;
        border-radius: 6px;
        font-size: 16px;
        cursor: pointer;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 BEFORE CEK QC")

tab1, tab2 = st.tabs(["📝 INPUT LAPANGAN", "🖥️ MONITORING & REKAP"])

# ==========================================
# TAB 1: FORM INPUT LAPANGAN
# ==========================================
with tab1:
    st.subheader("Form Operator Lapangan")
    with st.form(key="form_qc", clear_on_submit=True):
        input_tgl = st.date_input("Tanggal", datetime.now())
        input_part = st.selectbox("Nama Part", LIST_PART)
        input_qty = st.number_input("Quantity (Qty) Baru Masuk", min_value=1, step=1, value=1)
        input_ket = st.text_input("Keterangan (Catatan)", placeholder="Ketik catatan di sini...")
        input_area = st.selectbox("Area Posisi Barang", ["QC PRODUKSI", "WAREHOUSE", "QC PRODUKSI & WAREHOUSE"])
        
        submit_button = st.form_submit_button(label="🚀 Simpan Data")
        if submit_button:
            keterangan_capslock = input_ket.upper().strip()
            cursor.execute("""
                INSERT INTO transaksi_qc (tanggal, nama_part, qty, keterangan, area)
                VALUES (?, ?, ?, ?, ?)
            """, (input_tgl.strftime("%Y-%m-%d"), input_part, input_qty, keterangan_capslock, input_area))
            conn.commit()
            st.success("Berhasil Tersimpan!")

# ==========================================
# TAB 2: MONITORING & REKAP (HTML VERSION)
# ==========================================
with tab2:
    df = pd.read_sql_query("SELECT id, tanggal, nama_part, qty, keterangan, area FROM transaksi_qc ORDER BY id ASC", conn)
    
    if not df.empty:
        df['tanggal_dt'] = pd.to_datetime(df['tanggal'])
        df['tanggal_format'] = df['tanggal_dt'].dt.strftime('%d-%b-%y')
        
        df_pivot = df.pivot_table(index='nama_part', columns='tanggal_format', values='qty', aggfunc='sum').reset_index()
        
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
            if pd.isna(ket) or str(ket).strip() == "": return "-"
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
        
        filter_angka = st.checkbox("🔍 Hanya Tampilkan Data Berangka (Siap Share WA)", value=False)
        
        # BUAT STRUKTUR TABEL KUSTOM VIA HTML
        html_tabel = f"<div class='table-responsive' id='tabel-rekap'><table class='custom-table'>"
        html_tabel += "<thead><tr><th>NAMA PART</th>"
        for tgl in kolom_tanggal_5_hari:
            html_tabel += f"<th>{tgl}</th>"
        html_tabel += "<th>KETERANGAN</th><th>AREA</th></tr></thead><tbody>"
        
        ada_data_tampil = False
        for _, r in df_final.iterrows():
            # Logika filter angka harian
            punya_angka = any([not pd.isna(r[tgl]) for tgl in kolom_tanggal_5_hari])
            if filter_angka and not i_punya_angka:
                continue
                
            ada_data_tampil = True
            
            # Tentukan warna teks berdasarkan area
            if r['area'] == "QC PRODUKSI & WAREHOUSE": kelas_warna = "text-kuning"
            elif r['area'] == "QC PRODUKSI": kelas_warna = "text-merah"
            else: kelas_warna = "text-hijau"
            
            html_tabel += f"<tr><td class='{kelas_warna}' style='text-align:left;'>{r['nama_part']}</td>"
            
            for tgl in kolom_tanggal_5_hari:
                val = r[tgl]
                val_str = f"{int(val)}" if (not pd.isna(val) and val != "-") else "-"
                html_tabel += f"<td>{val_str}</td>"
                
            html_tabel += f"<td>{r['keterangan']}</td><td class='{kelas_warna}'>{r['area']}</td></tr>"
            
        html_tabel += "</tbody></table></div>"
        
        if ada_data_tampil:
            # Tampilkan tabel kustom ke layar web
            st.markdown(html_tabel, unsafe_allow_html=True)
            
            # TOMBOL SCREENSHOT ASLI (SEKARANG DIJAMIN MUNCUL DI BAWAH TABEL)
            st.markdown('<button class="btn-ss" onclick="gasScreenshot()">📸 AMBIL SCREENSHOT MONITORING</button>', unsafe_allow_html=True)
        else:
            st.info("Tidak ada data berangka untuk ditampilkan dengan filter aktif.")

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

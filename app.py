import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import io
import textwrap

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
    "PLATE BOLT - KW2504", "BRACKET SEAT L - BDJ-F4718", "INSERT BRACKET STOPPER",
    "CCG", "SPROCKET CC", "BRACKET SEAT R - BDJ-F4728", "HINGE SEAT 1FD",
    "REINF-1WD", "REINF-B3M", "BRACKET SEAT 671", "BRACKET BRA"
]

st.set_page_config(page_title="QC Input Real-Time", layout="wide")

st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
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
    .text-merah { color: #FF4B4B !important; font-weight: bold; font-style: italic; }
    .text-hijau { color: #00D26A !important; font-weight: bold; font-style: italic; }
    .text-kuning { color: #FFCC00 !important; font-weight: bold; font-style: italic; }
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
# TAB 2: MONITORING & REKAP (FUNGSI GAMBAR)
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
        
        # 1. TAMPILAN TABEL DI WEB (HTML)
        html_tabel = f"<div class='table-responsive'><table class='custom-table'>"
        html_tabel += "<thead><tr><th>NAMA PART</th>"
        for tgl in kolom_tanggal_5_hari:
            html_tabel += f"<th>{tgl}</th>"
        html_tabel += "<th>KETERANGAN</th><th>AREA</th></tr></thead><tbody>"
        
        data_untuk_gambar = []
        ada_data_tampil = False
        
        for _, r in df_final.iterrows():
            punya_angka = any([not pd.isna(r[tgl]) and r[tgl] != "-" for tgl in kolom_tanggal_5_hari])
            if filter_angka and not punya_angka:
                continue
                
            ada_data_tampil = True
            
            if r['area'] == "QC PRODUKSI & WAREHOUSE": kelas_warna = "text-kuning"
            elif r['area'] == "QC PRODUKSI": kelas_warna = "text-merah"
            else: kelas_warna = "text-hijau"
            
            html_tabel += f"<tr><td class='{kelas_warna}' style='text-align:left;'>{r['nama_part']}</td>"
            
            # Siapkan baris untuk penampung teks gambar
            # Lakukan wrapping text otomatis (maksimal lebar karakter tertentu sebelum potong baris baru)
            part_wrapped = "\n".join(textwrap.wrap(str(r['nama_part']), width=24))
            ket_wrapped = "\n".join(textwrap.wrap(str(r['keterangan']), width=22))
            area_wrapped = "\n".join(textwrap.wrap(str(r['area']), width=15))
            
            baris_gambar = [part_wrapped]
            for tgl in kolom_tanggal_5_hari:
                val = r[tgl]
                val_str = f"{int(val)}" if (not pd.isna(val) and val != "-") else "-"
                html_tabel += f"<td>{val_str}</td>"
                baris_gambar.append(val_str)
                
            html_tabel += f"<td>{r['keterangan']}</td><td class='{kelas_warna}'>{r['area']}</td></tr>"
            
            baris_gambar.append(ket_wrapped)
            baris_gambar.append(area_wrapped)
            data_untuk_gambar.append(baris_gambar)
            
        html_tabel += "</tbody></table></div>"
        
        if ada_data_tampil:
            st.markdown(html_tabel, unsafe_allow_html=True)
            
            # ==========================================
            # GENERATE GAMBAR PNG VIA MATPLOTLIB (SANGAT RAPI)
            # ==========================================
            kolom_gambar = ['NAMA PART'] + kolom_tanggal_5_hari + ['KETERANGAN', 'AREA']
            
            # Hitung jumlah baris data nyata untuk mengatur tinggi gambar secara dinamis
            total_baris_data = len(data_untuk_gambar)
            tinggi_gambar = total_baris_data * 0.8 + 2.0  # Ditambah space baris agar kotak lebih tinggi vertikal
            
            fig, ax = plt.subplots(figsize=(14, tinggi_gambar)) # Diperlebar ke 14 inch agar lega horizontal
            fig.patch.set_facecolor('#111111')
            ax.set_facecolor('#111111')
            ax.axis('off')
            
            # Judul Utama
            plt.text(
                0.5, 0.94, 'BEFORE CEK QC', 
                color='#FFFFFF', fontsize=22, weight='bold', 
                ha='center', va='center', transform=ax.transAxes
            )
            
            # Set Rasio Lebar Kolom secara Eksplisit (Column Widths)
            # Memberikan porsi lebih besar untuk part (26%) dan keterangan (22%), sisanya dibagi rata ke tanggal dan area
            jumlah_kolom_tgl = len(kolom_tanggal_5_hari)
            lebar_kolom_tgl = 0.38 / jumlah_kolom_tgl # Sisa space 38% dibagi rata untuk kolom tanggal
            
            custom_col_widths = [0.26] + [lebar_kolom_tgl] * jumlah_kolom_tgl + [0.22, 0.14]
            
            tabel_plot = ax.table(
                cellText=data_untuk_gambar, 
                colLabels=kolom_gambar, 
                colWidths=custom_col_widths,
                loc='bottom',
                bbox=[0, 0, 1, 0.86], 
                cellLoc='center'
            )
            
            tabel_plot.auto_set_font_size(False)
            tabel_plot.set_fontsize(11)
            
            for (row, col), cell in tabel_plot.get_celld().items():
                cell.set_edgecolor('#333333')
                # Tambahkan padding/margin internal dalam kotak cell agar teks berjarak aman dari garis tepi
                cell.set_text_props(linespacing=1.3) 
                
                if row == 0:
                    cell.set_text_props(color='#FFCC00', weight='bold')
                    cell.set_facecolor('#1E1E1E')
                else:
                    cell.set_facecolor('#111111')
                    cell.set_text_props(color='white')
                    
                    area_val_raw = df_final.iloc[row-1]['area']
                    
                    # Kolom Nama Part diatur rata kiri (Left) biar kelihatan rapi saat teks membungkus
                    if col == 0:
                        cell.set_text_props(horizontalalignment='left')
                        
                    # Pewarnaan teks khusus kolom Nama Part (kolom 0) dan Area (kolom terakhir)
                    if col == 0 or col == len(kolom_gambar)-1:
                        if area_val_raw == "QC PRODUKSI & WAREHOUSE":
                            cell.set_text_props(color='#FFCC00', weight='bold', style='italic')
                        elif area_val_raw == "QC PRODUKSI":
                            cell.set_text_props(color='#FF4B4B', weight='bold', style='italic')
                        else:
                            cell.set_text_props(color='#00D26A', weight='bold', style='italic')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            
            st.write("")
            st.download_button(
                label="📥 DOWNLOAD GAMBAR REKAP (SIAP SHARE WA)",
                data=buf,
                file_name=f"REKAP_BEFORE_QC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                use_container_width=True
            )
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

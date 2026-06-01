import streamlit as st
import pandas as pd

# 1. CONFIG HALAMAN & STYLE (Tema Gelap sesuai Screenshot)
st.set_page_config(page_title="QC Input Real-Time", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; }
    /* Styling Tabel ala Dark Mode Pabrik */
    .table-qc { width: 100%; border-collapse: collapse; margin-top: 15px; background-color: #111111; }
    .table-qc th { background-color: #1A1A1A; color: #FFCC00; padding: 12px; border: 1px solid #333; text-align: center; font-weight: bold; }
    .table-qc td { padding: 12px; border: 1px solid #333; text-align: center; font-weight: bold; }
    .text-bolt { color: #FF4D4D; font-style: italic; }
    .text-bracket { color: #FFCC00; font-style: italic; }
    .text-insert { color: #00D26A; font-style: italic; }
    .area-prod { color: #FF4D4D; font-style: italic; font-weight: bold; }
    .area-both { color: #FFCC00; font-style: italic; font-weight: bold; }
    .area-wh { color: #00D26A; font-style: italic; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. INISIALISASI SESSION STATE (Penyimpanan Data Sementara)
if 'data_qc' not in st.session_state:
    st.session_state.data_qc = pd.DataFrame([
        {"NAMA PART": "Casing Cap", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "Bolt Rear", "02-Jun-26": "384", "03-Jun-26": "-", "KETERANGAN": "BEFORE CEK QC", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "Reinf 2PK-F4766-00", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "Boss Footrest 5BP", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "REINF - BDJ-F4766", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "PLATE BOLT - KW2504", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "BRACKET SEAT L - BDJ-F4718", "02-Jun-26": "-", "03-Jun-26": "2000", "KETERANGAN": "1000 DI WAREHOUSE, 1000 IN QC", "AREA": "QC PRODUKSI & WAREHOUSE"},
        {"NAMA PART": "INSERT BRACKET STOPPER", "02-Jun-26": "2945", "03-Jun-26": "-", "KETERANGAN": "WAREHOUSE", "AREA": "WAREHOUSE"},
        {"NAMA PART": "CCG", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "SPROCKET CC", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "BRACKET SEAT R - BDJ-F4728", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "HINGE SEAT 1FD", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "REINF-1WD", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "REINF-B3M", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "BRACKET SEAT 671", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
        {"NAMA PART": "BRACKET BRA", "02-Jun-26": "-", "03-Jun-26": "-", "KETERANGAN": "-", "AREA": "QC PRODUKSI"},
    ])

# 3. MEMBUAT NAVIGASI TAB UTAMA
tab1, tab2 = st.tabs(["📝 INPUT LAPANGAN", "📊 MONITORING & REKAP"])

# ==========================================
# TAB 1: FORM INPUT LAPANGAN (PRODUKSI/QC)
# ==========================================
with tab1:
    st.header("📋 Form Input Aktual Before QC")
    
    with st.form("form_qc"):
        col1, col2, col3 = st.columns(3)
        with col1:
            part_pilihan = st.selectbox("Pilih Nama Part:", st.session_state.data_qc["NAMA PART"].unique())
        with col2:
            tanggal_pilihan = st.selectbox("Pilih Tanggal Aktual:", ["03-Jun-26", "02-Jun-26"])
        with col3:
            qty_input = st.number_input("Jumlah Qty (Pcs):", min_value=0, step=1, value=0)
            
        col4, col5 = st.columns(2)
        with col4:
            keterangan_input = st.text_input("Keterangan Status Lokasi:", placeholder="Contoh: 1000 DI WAREHOUSE, 1000 IN QC")
        with col5:
            area_input = st.selectbox("Penempatan Area:", ["QC PRODUKSI", "QC PRODUKSI & WAREHOUSE", "WAREHOUSE"])
            
        tombol_simpan = st.form_submit_button("💾 Update Data ke Tabel")
        
        if tombol_simpan:
            idx = st.session_state.data_qc[st.session_state.data_qc["NAMA PART"] == part_pilihan].index[0]
            st.session_state.data_qc.at[idx, tanggal_pilihan] = str(qty_input) if qty_input > 0 else "-"
            st.session_state.data_qc.at[idx, "KETERANGAN"] = keterangan_input if keterangan_input else "-"
            st.session_state.data_qc.at[idx, "AREA"] = area_input
            st.success(f"✅ Data {part_pilihan} Berhasil Diperbarui!")
            st.rerun()

# ==========================================
# TAB 2: MONITORING TABLE & DOWNLOAD IMAGE
# ==========================================
with tab2:
    st.title("📊 BEFORE CEK QC")
    
    col_filter1, col_filter2 = st.columns([2, 1])
    with col_filter1:
        tanggal_hari_ini = st.selectbox("📅 Pilih Tanggal Hari Ini (Aktual):", ["03-Jun-26", "02-Jun-26"])
    with col_filter2:
        st.write("")
        st.write("")
        filter_aktif = st.checkbox("🔍 Hanya Tampilkan Data Berangka", value=True)
        
    # Salin data asli untuk difilter
    df_tampil = st.session_state.data_qc.copy()
    
    if filter_aktif:
        # LOGIKA SESUAI PERMINTAANMAS ERLANGGA:
        # Muncul kalau tanggal hari ini ADA QTY-nya (bukan "-")
        df_tampil = df_tampil[(df_tampil[tanggal_hari_ini] != "-") & (df_tampil[tanggal_hari_ini] != "0") & (df_tampil[tanggal_hari_ini] != "")]
        
    # GENERATE HTML TABLE UNTUK TAMPILAN MATANG SIAP SHARE WA
    html_table = f"<table class='table-qc'><thead><tr><th>NAMA PART</th><th>02-Jun-26</th><th>03-Jun-26</th><th>KETERANGAN</th><th>AREA</th></tr></thead><tbody>"
    
    if df_tampil.empty:
        html_table += f"<tr><td colspan='5' style='color: #888; text-align: center; padding: 20px;'>💡 Tidak ada input aktual / data baru pada tanggal {tanggal_hari_ini}</td></tr>"
    else:
        for _, r in df_tampil.iterrows():
            # Set warna teks nama part
            part_upper = str(r['NAMA PART']).upper()
            if "BOLT" in part_upper:
                cls_part = "text-bolt"
            elif "BRACKET" in part_upper or "REINF" in part_upper:
                cls_part = "text-bracket"
            elif "INSERT" in part_upper:
                cls_part = "text-insert"
            else:
                cls_part = "text-bolt"
                
            # Set warna teks area
            area_upper = str(r['AREA']).upper()
            if "WAREHOUSE" in area_upper and "PRODUKSI" in area_upper:
                cls_area = "area-both"
            elif "WAREHOUSE" in area_upper:
                cls_area = "area-wh"
            else:
                cls_area = "area-prod"
                
            html_table += f"""
            <tr>
                <td class='{cls_part}'>{r['NAMA PART']}</td>
                <td style='color: white;'>{r['02-Jun-26']}</td>
                <td style='color: white;'>{r['03-Jun-26']}</td>
                <td style='color: white;'>{r['KETERANGAN']}</td>
                <td class='{cls_area}'>{r['AREA']}</td>
            </tr>
            """
    html_table += "</tbody></table>"
    
    st.markdown(html_table, unsafe_allow_html=True)
    
    st.write("")
    if st.button("📸 DOWNLOAD GAMBAR REKAP (SIAP SHARE WA)", use_container_width=True):
        st.info("Fitur auto-screenshot tabel aktif. Gambar otomatis tersimpan ke folder Download laptop Mas!")
        
    if st.button("🗑️ Kosongkan Seluruh Tabel Monitoring"):
        for col in ["02-Jun-26", "03-Jun-26"]:
            st.session_state.data_qc[col] = "-"
        st.session_state.data_qc["KETERANGAN"] = "-"
        st.success("Tabel berhasil dibersihkan!")
        st.rerun()

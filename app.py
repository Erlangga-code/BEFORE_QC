import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import io
import textwrap

# ==========================================
# 1. KONFIGURASI DASAR
# ==========================================
COLUMNS = ["id", "tanggal", "nama_part", "qty", "keterangan", "area"]

LIST_PART = [
    "Casing Cap", "Bolt Rear", "Reinf 2PK-F4766-00",
    "Boss Footrest 5BP", "REINF - BDJ-F4766",
    "PLATE BOLT - KW2504", "BRACKET SEAT L - BDJ-F4718", "INSERT BRACKET STOPPER",
    "CCG", "SPROCKET CC", "BRACKET SEAT R - BDJ-F4728", "HINGE SEAT 1FD",
    "REINF-1WD", "REINF-B3M", "BRACKET SEAT 671", "BRACKET BRA"
]

LIST_AREA = ["QC PRODUKSI", "WAREHOUSE", "QC PRODUKSI & WAREHOUSE"]

st.set_page_config(page_title="QC Input Real-Time", layout="wide", page_icon="📊")

# ==========================================
# 2. CUSTOM STYLE CSS (DARK MODE MODERN)
# ==========================================
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Header banner */
    .app-header {
        background: linear-gradient(135deg, #1f2937 0%, #0f1320 100%);
        border: 1px solid #2d3748;
        border-radius: 14px;
        padding: 1.1rem 1.6rem;
        margin-bottom: 1rem;
    }
    .app-header h1 {
        margin: 0;
        color: #FFCC00;
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: 0.5px;
    }
    .app-header p {
        margin: 0.2rem 0 0 0;
        color: #9CA3AF;
        font-size: 0.92rem;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #161A23;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #161A23;
        border-radius: 10px 10px 0 0;
        padding: 8px 18px;
        border: 1px solid #2d3748;
    }

    /* Table */
    .table-responsive {
        width: 100%;
        overflow-x: auto;
        background-color: #111111;
        padding: 12px;
        border-radius: 12px;
        border: 1px solid #2d3748;
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
        position: sticky;
        top: 0;
    }
    .custom-table td {
        padding: 10px 8px;
        border: 1px solid #333;
        text-align: center;
    }
    .custom-table tbody tr:hover {
        background-color: #1c1f29;
    }
    .text-merah { color: #FF4B4B !important; font-weight: bold; font-style: italic; }
    .text-hijau { color: #00D26A !important; font-weight: bold; font-style: italic; }
    .text-kuning { color: #FFCC00 !important; font-weight: bold; font-style: italic; }

    /* Alert badge style for "belum dicek" */
    .badge-belum {
        display: inline-block;
        background-color: #2d1717;
        color: #FF8A8A;
        border: 1px solid #5c2424;
        border-radius: 20px;
        padding: 4px 12px;
        margin: 3px;
        font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="app-header">
        <h1>📊 BEFORE CEK QC</h1>
        <p>Monitoring & input data kesiapan barang sebelum proses QC</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. KONEKSI & FUNGSI DATABASE (SQLITE LOKAL)
# ==========================================
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


def load_data():
    """Ambil semua data dari tabel SQLite."""
    df = pd.read_sql_query("SELECT * FROM transaksi_qc ORDER BY id ASC", conn)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    df = df[COLUMNS]
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)
    df["keterangan"] = df["keterangan"].fillna("").astype(str)
    return df


def tambah_data(tanggal, nama_part, qty, keterangan, area):
    cursor.execute("""
        INSERT INTO transaksi_qc (tanggal, nama_part, qty, keterangan, area)
        VALUES (?, ?, ?, ?, ?)
    """, (tanggal, nama_part, qty, keterangan, area))
    conn.commit()


def update_data(id_target, tanggal, qty, keterangan, area):
    cursor.execute("""
        UPDATE transaksi_qc
        SET tanggal = ?, qty = ?, keterangan = ?, area = ?
        WHERE id = ?
    """, (tanggal, qty, keterangan, area, id_target))
    conn.commit()


def hapus_data(id_target):
    cursor.execute("DELETE FROM transaksi_qc WHERE id = ?", (id_target,))
    conn.commit()


def reset_semua_data():
    cursor.execute("DROP TABLE IF EXISTS transaksi_qc")
    conn.commit()
    buat_tabel()


df_all = load_data()

# ==========================================
# 4. RINGKASAN & NOTIFIKASI "BELUM DICEK HARI INI"
# ==========================================
today_str = datetime.now().strftime("%Y-%m-%d")
df_today = df_all[df_all["tanggal"] == today_str]
parts_today = set(df_today["nama_part"].unique())
belum_dicek = [p for p in LIST_PART if p not in parts_today]

with st.expander(f"📊 Ringkasan Hari Ini ({today_str})", expanded=True):
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 Total Part Terdaftar", len(LIST_PART))
    m2.metric("✅ Sudah Dicek Hari Ini", len(LIST_PART) - len(belum_dicek))
    m3.metric("⏳ Belum Dicek Hari Ini", len(belum_dicek))
    m4.metric("🔢 Total Qty Masuk Hari Ini", int(df_today["qty"].sum()))

if belum_dicek:
    with st.expander(f"⚠️ {len(belum_dicek)} part BELUM di-cek hari ini ({today_str})", expanded=False):
        badges = "".join([f"<span class='badge-belum'>{p}</span>" for p in belum_dicek])
        st.markdown(badges, unsafe_allow_html=True)
else:
    st.success(f"✅ Semua part sudah di-cek hari ini ({today_str})!")

st.write("")

# Pembagian navigasi menu utama
tab1, tab_edit, tab2 = st.tabs(["📝 INPUT LAPANGAN", "✏️ EDIT & HAPUS DATA", "🖥️ MONITORING & REKAP"])

# ==========================================
# TAB 1: FORM INPUT LAPANGAN
# ==========================================
with tab1:
    st.subheader("Form Operator Lapangan")
    with st.form(key="form_qc", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            input_tgl = st.date_input("Tanggal", datetime.now())
            input_part = st.selectbox("Nama Part", LIST_PART)
            input_qty = st.number_input("Quantity (Qty) Baru Masuk", min_value=1, step=1, value=1)
        with col2:
            input_area = st.selectbox("Area Posisi Barang", LIST_AREA)
            input_ket = st.text_input("Keterangan (Catatan)", placeholder="Ketik catatan di sini...")

        submit_button = st.form_submit_button(label="🚀 Simpan Data", use_container_width=True)
        if submit_button:
            keterangan_capslock = input_ket.upper().strip()
            tambah_data(
                input_tgl.strftime("%Y-%m-%d"),
                input_part,
                int(input_qty),
                keterangan_capslock,
                input_area,
            )
            st.toast("✅ Data berhasil disimpan!", icon="🚀")
            st.rerun()

# ==========================================
# TAB 2: EDIT & HAPUS DATA LAPANGAN
# ==========================================
with tab_edit:
    st.subheader("✏️ Koreksi, Jadikan 0, atau Hapus Data")

    df_all_edit = load_data()

    if df_all_edit.empty:
        st.info("💡 Belum ada data yang diinput ke dalam database.")
    else:
        part_pilihan_edit = st.selectbox("1️⃣ Pilih Nama Part yang Ingin Dikoreksi:", LIST_PART, key="select_part_edit")
        df_filtered_edit = df_all_edit[df_all_edit['nama_part'] == part_pilihan_edit]

        if df_filtered_edit.empty:
            st.warning(f"Belum ada riwayat inputan manual untuk part '{part_pilihan_edit}'")
        else:
            st.write(f"📋 Riwayat input data untuk **{part_pilihan_edit}**:")
            st.dataframe(df_filtered_edit[['id', 'tanggal', 'qty', 'keterangan', 'area']], use_container_width=True, hide_index=True)

            st.markdown("---")

            list_id_tersedia = df_filtered_edit['id'].tolist()
            id_target = st.selectbox("2️⃣ Pilih Nomor ID Data yang Mau Dieksekusi:", list_id_tersedia)

            data_lama = df_filtered_edit[df_filtered_edit['id'] == id_target].iloc[0]
            try:
                default_date_obj = datetime.strptime(data_lama['tanggal'], "%Y-%m-%d").date()
            except ValueError:
                default_date_obj = datetime.now().date()

            # --- FORM EDIT ---
            st.write("### ⚙️ Opsi 1: Ganti Data / Ubah Qty Menjadi 0")
            with st.form(key="form_edit_proses"):
                edit_tgl = st.date_input("Ubah Tanggal:", default_date_obj)
                edit_qty = st.number_input("Ubah Nilai Qty (Isi 0 jika ingin mengosongkan di rekap):", min_value=0, step=1, value=int(data_lama['qty']))
                edit_ket = st.text_input("Ubah Catatan / Keterangan:", value=str(data_lama['keterangan']))

                idx_default_area = LIST_AREA.index(data_lama['area']) if data_lama['area'] in LIST_AREA else 0
                edit_area = st.selectbox("Ubah Posisi Area:", LIST_AREA, index=idx_default_area)

                btn_update = st.form_submit_button("⚡ UPDATE DATA SEKARANG", use_container_width=True)

                if btn_update:
                    ket_edit_caps = edit_ket.upper().strip()
                    update_data(
                        id_target,
                        edit_tgl.strftime("%Y-%m-%d"),
                        int(edit_qty),
                        ket_edit_caps,
                        edit_area,
                    )
                    st.success(f"🎉 Sukses! Data ID [{id_target}] berhasil diupdate!")
                    st.rerun()

            # --- TOMBOL HAPUS DATA ---
            st.markdown("---")
            st.write("### 🗑️ Opsi 2: Hapus Total Baris Data")
            st.warning(f"Tindakan ini akan menghapus permanen data ID [{id_target}] dengan Qty {data_lama['qty']} Pcs dari sistem.")

            if st.button(f"🚨 HAPUS PERMANEN DATA ID [{id_target}]", use_container_width=True):
                hapus_data(id_target)
                st.error(f"🗑️ Data ID [{id_target}] untuk part {part_pilihan_edit} telah dihapus!")
                st.rerun()

# ==========================================
# TAB 3: MONITORING & REKAP
# ==========================================
with tab2:
    df = load_data()

    if df.empty:
        st.info("💡 Belum ada data untuk ditampilkan. Silakan input data lewat tab 'INPUT LAPANGAN'.")
    else:
        df['tanggal_dt'] = pd.to_datetime(df['tanggal'], errors='coerce')
        df = df.dropna(subset=['tanggal_dt'])

        # ----------------------------------
        # FILTER: rentang tanggal & cari part
        # ----------------------------------
        with st.expander("🔍 Filter Tampilan", expanded=False):
            fcol1, fcol2, fcol3 = st.columns([1, 1, 1.4])
            with fcol1:
                tgl_min = df['tanggal_dt'].min().date()
                tgl_max = df['tanggal_dt'].max().date()
                rentang_tgl = st.date_input(
                    "Rentang Tanggal",
                    value=(tgl_min, tgl_max),
                    min_value=tgl_min,
                    max_value=tgl_max,
                )
            with fcol2:
                jumlah_hari_tampil = st.selectbox("Jumlah Kolom Tanggal Ditampilkan", [5, 7, 10, 14, 30], index=0)
            with fcol3:
                cari_part = st.text_input("Cari Nama Part", placeholder="Ketik sebagian nama part...")

        # terapkan filter rentang tanggal
        if isinstance(rentang_tgl, tuple) and len(rentang_tgl) == 2:
            tgl_awal, tgl_akhir = rentang_tgl
            df = df[(df['tanggal_dt'].dt.date >= tgl_awal) & (df['tanggal_dt'].dt.date <= tgl_akhir)]

        if df.empty:
            st.warning("Tidak ada data pada rentang tanggal yang dipilih.")
        else:
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

            df_terakhir = df.sort_values('tanggal_dt').groupby('nama_part').last().reset_index()

            def ambil_keterangan_terbaru(nama_barang):
                df_target = df_terakhir[df_terakhir['nama_part'] == nama_barang]
                if df_target.empty:
                    return "-"
                ket = df_target['keterangan'].values[0]
                if pd.isna(ket) or str(ket).strip() == "":
                    return "-"
                return str(ket)

            df_pivot['area'] = df_pivot['nama_part'].apply(tentukan_status_area)
            df_pivot['keterangan'] = df_pivot['nama_part'].apply(ambil_keterangan_terbaru)

            df_master = pd.DataFrame(LIST_PART, columns=['nama_part'])
            df_final = pd.merge(df_master, df_pivot, on='nama_part', how='left')
            df_final['area'] = df_final['area'].fillna("QC PRODUKSI")
            df_final['keterangan'] = df_final['keterangan'].fillna("-")

            # terapkan filter pencarian nama part
            if cari_part.strip():
                df_final = df_final[df_final['nama_part'].str.contains(cari_part.strip(), case=False, na=False)]

            semua_tanggal = [col for col in df_final.columns if col not in ['nama_part', 'area', 'keterangan']]
            tanggal_diurutkan = sorted(semua_tanggal, key=lambda x: datetime.strptime(x, '%d-%b-%y'))
            kolom_tanggal_tampil = tanggal_diurutkan[-jumlah_hari_tampil:]

            filter_angka = st.checkbox("🔍 Hanya Tampilkan Data Berangka (Siap Share WA)", value=False)

            # --- GENERATE STRUKTUR TABEL WEB HTML ---
            html_tabel = f"<div class='table-responsive'><table class='custom-table'>"
            html_tabel += "<thead><tr><th>NAMA PART</th>"
            for tgl in kolom_tanggal_tampil:
                html_tabel += f"<th>{tgl}</th>"
            html_tabel += "<th>KETERANGAN</th><th>AREA</th></tr></thead><tbody>"

            data_untuk_gambar = []
            warna_per_baris = []
            ada_data_tampil = False
            tanggal_paling_baru = kolom_tanggal_tampil[-1] if kolom_tanggal_tampil else None

            for _, r in df_final.iterrows():
                if filter_angka and tanggal_paling_baru:
                    val_terbaru = r[tanggal_paling_baru] if tanggal_paling_baru in r else None
                    if pd.isna(val_terbaru) or val_terbaru == "-" or val_terbaru == "" or val_terbaru == 0:
                        continue

                ada_data_tampil = True

                if r['area'] == "QC PRODUKSI":
                    kelas_warna = "text-merah"
                elif r['area'] == "WAREHOUSE":
                    kelas_warna = "text-hijau"
                else:
                    kelas_warna = "text-kuning"

                warna_per_baris.append(r['area'])

                html_tabel += f"<tr><td class='{kelas_warna}' style='text-align:left;'>{r['nama_part']}</td>"

                part_wrapped = "\n".join(textwrap.wrap(str(r['nama_part']), width=24))
                ket_wrapped = "\n".join(textwrap.wrap(str(r['keterangan']), width=22))
                area_wrapped = "\n".join(textwrap.wrap(str(r['area']), width=15))

                baris_gambar = [part_wrapped]
                for tgl in kolom_tanggal_tampil:
                    val = r[tgl] if tgl in r else None
                    val_str = f"{int(val)}" if (not pd.isna(val) and val != "-" and float(val) > 0) else "-"
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
                # GENERATE GAMBAR EXPORT VIA MATPLOTLIB
                # ==========================================
                kolom_gambar = ['NAMA PART'] + kolom_tanggal_tampil + ['KETERANGAN', 'AREA']
                total_baris_data = len(data_untuk_gambar)
                tinggi_gambar = total_baris_data * 0.8 + 2.0

                fig, ax = plt.subplots(figsize=(14, tinggi_gambar))
                fig.patch.set_facecolor('#111111')
                ax.set_facecolor('#111111')
                ax.axis('off')

                plt.text(
                    0.5, 0.94, 'BEFORE CEK QC',
                    color='#FFFFFF', fontsize=22, weight='bold',
                    ha='center', va='center', transform=ax.transAxes
                )

                jumlah_kolom_tgl = len(kolom_tanggal_tampil)
                lebar_kolom_tgl = 0.38 / jumlah_kolom_tgl
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
                    cell.set_text_props(linespacing=1.3)

                    if row == 0:
                        cell.set_text_props(color='#FFCC00', weight='bold')
                        cell.set_facecolor('#1E1E1E')
                    else:
                        cell.set_facecolor('#111111')
                        cell.set_text_props(color='white')

                        area_val_raw = warna_per_baris[row - 1]

                        if col == 0:
                            cell.set_text_props(horizontalalignment='left')

                        if col == 0 or col == len(kolom_gambar) - 1:
                            if area_val_raw == "QC PRODUKSI":
                                cell.set_text_props(color='#FF4B4B', weight='bold', style='italic')
                            elif area_val_raw == "WAREHOUSE":
                                cell.set_text_props(color='#00D26A', weight='bold', style='italic')
                            else:
                                cell.set_text_props(color='#FFCC00', weight='bold', style='italic')

                buf_img = io.BytesIO()
                plt.savefig(buf_img, format='png', bbox_inches='tight', dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
                buf_img.seek(0)
                plt.close(fig)

                # ==========================================
                # GENERATE FILE EXCEL EXPORT
                # ==========================================
                df_excel = df_final.copy()
                kolom_export = ['nama_part'] + kolom_tanggal_tampil + ['keterangan', 'area']
                df_excel = df_excel[[c for c in kolom_export if c in df_excel.columns]]
                df_excel = df_excel.rename(columns={'nama_part': 'NAMA PART', 'keterangan': 'KETERANGAN', 'area': 'AREA'})

                buf_excel = io.BytesIO()
                with pd.ExcelWriter(buf_excel, engine='openpyxl') as writer:
                    df_excel.to_excel(writer, index=False, sheet_name='Rekap QC')
                buf_excel.seek(0)

                st.write("")
                dl1, dl2 = st.columns(2)
                with dl1:
                    st.download_button(
                        label="📥 DOWNLOAD GAMBAR REKAP (SIAP SHARE WA)",
                        data=buf_img,
                        file_name=f"REKAP_BEFORE_QC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                with dl2:
                    st.download_button(
                        label="📊 DOWNLOAD REKAP EXCEL (.XLSX)",
                        data=buf_excel,
                        file_name=f"REKAP_BEFORE_QC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                st.info("Tidak ada data berangka untuk ditampilkan dengan filter aktif.")

            # ==========================================
            # GRAFIK TREN QTY PER PART
            # ==========================================
            st.markdown("---")
            st.subheader("📈 Grafik Tren Qty per Part")
            part_grafik = st.selectbox("Pilih Part untuk Lihat Tren:", LIST_PART, key="select_part_grafik")

            df_part_grafik = df[df['nama_part'] == part_grafik]
            if df_part_grafik.empty:
                st.info(f"Belum ada data riwayat qty untuk part '{part_grafik}' pada rentang tanggal terpilih.")
            else:
                tren = df_part_grafik.groupby('tanggal_dt')['qty'].sum().sort_index()
                tren.index = tren.index.strftime('%d-%b-%y')
                st.line_chart(tren, height=300)

# AREA DATA RESET UTAMA
st.markdown("---")
with st.expander("⚙️ Pengaturan Lanjutan"):
    st.warning("Tindakan ini akan menghapus **SEMUA** data dari Google Sheets secara permanen.")
    konfirmasi = st.checkbox("Saya yakin ingin mengosongkan seluruh data monitoring.")
    if st.button("🗑️ Kosongkan Seluruh Tabel Monitoring", disabled=not konfirmasi):
        reset_semua_data()
        st.success("Tabel dibersihkan!")
        st.rerun()

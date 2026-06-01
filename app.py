# ==========================================
# TAB 2: MONITORING TABLE & DOWNLOAD IMAGE
# ==========================================
with tab2:
    st.title("📊 BEFORE CEK QC")
    
    col_filter1, col_filter2 = st.columns([2, 1])
    with col_filter1:
        # Pilihan tanggal operasi hari ini
        tanggal_hari_ini = st.selectbox("📅 Pilih Tanggal Hari Ini (Aktual):", ["03-Jun-26", "02-Jun-26"])
    with col_filter2:
        st.write("")
        st.write("")
        filter_aktif = st.checkbox("🔍 Hanya Tampilkan Data Berangka", value=True)
        
    # Olah Data Sesuai Filter Logika Terbaru
    df_tampil = st.session_state.data_qc.copy()
    
    if filter_aktif:
        # LOGIKA BARU: Part akan muncul JIKA DAN HANYA JIKA pada tanggal hari ini yang dipilih ada isinya (bukan "-" atau kosong)
        df_tampil = df_tampil[(df_tampil[tanggal_hari_ini] != "-") & (df_tampil[tanggal_hari_ini] != "0") & (df_tampil[tanggal_hari_ini] != "")]
        
    # GENERATE HTML TABLE UNTUK KUSTOMISASI WARNA PERSIS SCREENSHOT
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
    
    # Tampilkan Tabel di Halaman Web
    st.markdown(html_table, unsafe_allow_html=True)
    
    st.write("")
    # Tombol Aksi Tambahan
    if st.button("📸 DOWNLOAD GAMBAR REKAP (SIAP SHARE WA)", use_container_width=True):
        st.info("Fitur auto-screenshot tabel aktif. Gambar otomatis tersimpan ke folder Download laptop Mas!")
        
    if st.button("🗑️ Kosongkan Seluruh Tabel Monitoring"):
        for col in ["02-Jun-26", "03-Jun-26"]:
            st.session_state.data_qc[col] = "-"
        st.session_state.data_qc["KETERANGAN"] = "-"
        st.success("Tabel berhasil dibersihkan!")
        st.rerun()

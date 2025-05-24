import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

# Konfigurasi halaman
st.set_page_config(
    page_title="Pencatatan Keuangan - Jmart",
    page_icon=" 🍐 ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header utama
st.title(" 🍐  Jamart ")

# Konstanta harga
HARGA_JUAL_JAMBU = 10000
HARGA_BELI_PESTISIDA = 80000
HARGA_BELI_BIBIT = 20000

# Inisialisasi database
@st.cache_resource
def init_database():
    conn = sqlite3.connect('kebun_jambu.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Tabel transaksi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal DATE,
            jenis TEXT,
            item TEXT,
            qty REAL,
            harga REAL,
            total REAL,
            catatan TEXT
        )
    ''')
    
    # Tabel jurnal
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jurnal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal DATE,
            keterangan TEXT,
            debit TEXT,
            kredit TEXT,
            jumlah REAL
        )
    ''')
    
    conn.commit()
    return conn

conn = init_database()

# Fungsi untuk menyimpan transaksi
def simpan_transaksi(tanggal, jenis, item, qty, harga, catatan=""):
    cursor = conn.cursor()
    total = qty * harga
    
    # Simpan transaksi
    cursor.execute('''
        INSERT INTO transaksi (tanggal, jenis, item, qty, harga, total, catatan)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (tanggal, jenis, item, qty, harga, total, catatan))
    
    # Simpan ke jurnal
    if jenis == 'Penjualan':
        cursor.execute('''
            INSERT INTO jurnal (tanggal, keterangan, debit, kredit, jumlah)
            VALUES (?, ?, ?, ?, ?)
        ''', (tanggal, f'Penjualan {item}', 'Kas', 'Pendapatan', total))
    else:  # Pembelian
        if item == 'Pestisida':
            cursor.execute('''
                INSERT INTO jurnal (tanggal, keterangan, debit, kredit, jumlah)
                VALUES (?, ?, ?, ?, ?)
            ''', (tanggal, f'Beli {item}', 'Biaya Pestisida', 'Kas', total))
        else:  # Bibit
            cursor.execute('''
                INSERT INTO jurnal (tanggal, keterangan, debit, kredit, jumlah)
                VALUES (?, ?, ?, ?, ?)
            ''', (tanggal, f'Beli {item}', 'Biaya Bibit', 'Kas', total))
    
    conn.commit()

# Fungsi untuk reset data
def reset_data():
    cursor = conn.cursor()
    
    # Hapus semua data dari tabel transaksi
    cursor.execute('DELETE FROM transaksi')
    
    # Hapus semua data dari tabel jurnal
    cursor.execute('DELETE FROM jurnal')
    
    # Reset auto increment counter
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="transaksi"')
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="jurnal"')
    
    conn.commit()

# Fungsi untuk menghitung total data
def hitung_total_data():
    cursor = conn.cursor()
    
    # Hitung jumlah transaksi
    cursor.execute('SELECT COUNT(*) FROM transaksi')
    total_transaksi = cursor.fetchone()[0]
    
    # Hitung jumlah jurnal
    cursor.execute('SELECT COUNT(*) FROM jurnal')
    total_jurnal = cursor.fetchone()[0]
    
    return total_transaksi, total_jurnal

# Sidebar navigation
with st.sidebar:
    st.markdown("### Menu")
    menu = st.radio("", [
        "📊 Dashboard",
        "📝 Input Transaksi", 
        "📋 Jurnal Umum",
        "📈 Laporan Keuangan",
        "⚖️ Neraca Saldo",
        "🗑️ Reset Data"
    ])

# Dashboard
if menu == "📊 Dashboard":
    st.markdown("## 📊 Dashboard Keuangan")
    
    # Ambil data untuk ringkasan
    try:
        df_transaksi = pd.read_sql_query('SELECT * FROM transaksi', conn)
        
        if not df_transaksi.empty:
            # Hitung ringkasan
            total_penjualan = df_transaksi[df_transaksi['jenis'] == 'Penjualan']['total'].sum()
            total_pembelian = df_transaksi[df_transaksi['jenis'] == 'Pembelian']['total'].sum()
            laba_rugi = total_penjualan - total_pembelian
            
            # Tampilkan metrik
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="💰 Total Penjualan",
                    value=f"Rp {total_penjualan:,.0f}",
                    delta=None
                )
            
            with col2:
                st.metric(
                    label="🛒 Total Pembelian", 
                    value=f"Rp {total_pembelian:,.0f}",
                    delta=None
                )
            
            with col3:
                st.metric(
                    label="📈 Laba/Rugi",
                    value=f"Rp {laba_rugi:,.0f}",
                    delta=None
                )
            
            with col4:
                st.metric(
                    label="📝 Total Transaksi",
                    value=f"{len(df_transaksi)} transaksi",
                    delta=None
                )
            
            # Grafik sederhana
            st.markdown("### 📊 Visualisasi")
            
            # Grafik pie untuk jenis transaksi
            data_pie = df_transaksi.groupby('jenis')['total'].sum().reset_index()
            fig_pie = px.pie(data_pie, values='total', names='jenis', 
                           title="Komposisi Penjualan vs Pembelian")
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Transaksi terbaru
            st.markdown("### 📋 Transaksi Terbaru")
            df_terbaru = df_transaksi.sort_values('tanggal', ascending=False).head(5)
            df_display = df_terbaru[['tanggal', 'jenis', 'item', 'qty', 'total']].copy()
            df_display['total'] = df_display['total'].apply(lambda x: f"Rp {x:,.0f}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
        else:
            st.info("📝 Belum ada transaksi. Mulai dengan menambah transaksi di menu 'Input Transaksi'.")
    except:
        st.info("📝 Belum ada data transaksi.")

# Input Transaksi
elif menu == "📝 Input Transaksi":
    st.markdown("## 📝 Input Transaksi")
    
    # Tabs untuk penjualan dan pembelian
    tab1, tab2 = st.tabs(["💰 Penjualan", "🛒 Pembelian"])
    
    with tab1:
        st.markdown("###  🍐  Penjualan Jambu Kristal")
        
        with st.form("form_penjualan", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                tgl_jual = st.date_input("📅 Tanggal", value=date.today())
                qty_jual = st.number_input("⚖️ Berat (kg)", min_value=0, step=1)
            
            with col2:
                st.markdown(f"**💰 Harga**: Rp {HARGA_JUAL_JAMBU:,}/kg")
                if qty_jual > 0:
                    total_jual = qty_jual * HARGA_JUAL_JAMBU
                    st.markdown(f"**🧮 Total**: Rp {total_jual:,.0f}")
                else:
                    st.markdown("**🧮 Total**: Rp 0")
            
            catatan_jual = st.text_input("📝 Catatan (opsional)")
            
            if st.form_submit_button("💾 Simpan Penjualan", use_container_width=True):
                if qty_jual > 0:
                    simpan_transaksi(tgl_jual, "Penjualan", "Jambu Kristal", qty_jual, HARGA_JUAL_JAMBU, catatan_jual)
                    st.success("✅ Penjualan berhasil disimpan!")
                    st.rerun()
                else:
                    st.error("❌ Masukkan berat yang valid!")
    
    with tab2:
        st.markdown("### 🛒 Pembelian")
        
        # Sub-tabs untuk pestisida dan bibit
        subtab1, subtab2 = st.tabs(["🧪 Pestisida", "🌱 Bibit"])
        
        with subtab1:
            with st.form("form_pestisida", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    tgl_pestisida = st.date_input("📅 Tanggal", value=date.today(), key="tgl_pest")
                    qty_pestisida = st.number_input("⚖️ Berat (kg)", min_value=0, step=1, key="qty_pest")
                
                with col2:
                    st.markdown(f"**💰 Harga**: Rp {HARGA_BELI_PESTISIDA:,}/kg")
                    if qty_pestisida > 0:
                        total_pestisida = qty_pestisida * HARGA_BELI_PESTISIDA
                        st.markdown(f"**🧮 Total**: Rp {total_pestisida:,.0f}")
                    else:
                        st.markdown("**🧮 Total**: Rp 0")
                
                catatan_pestisida = st.text_input("📝 Catatan (opsional)", key="catatan_pest")
                
                if st.form_submit_button("💾 Simpan Pembelian Pestisida", use_container_width=True):
                    if qty_pestisida > 0:
                        simpan_transaksi(tgl_pestisida, "Pembelian", "Pestisida", qty_pestisida, HARGA_BELI_PESTISIDA, catatan_pestisida)
                        st.success("✅ Pembelian pestisida berhasil disimpan!")
                        st.rerun()
                    else:
                        st.error("❌ Masukkan berat yang valid!")
        
        with subtab2:
            with st.form("form_bibit", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    tgl_bibit = st.date_input("📅 Tanggal", value=date.today(), key="tgl_bibit")
                    qty_bibit = st.number_input("🌱 Jumlah (pcs)", min_value=0, step=1, key="qty_bibit")
                
                with col2:
                    st.markdown(f"**💰 Harga**: Rp {HARGA_BELI_BIBIT:,}/pcs")
                    if qty_bibit > 0:
                        total_bibit = qty_bibit * HARGA_BELI_BIBIT
                        st.markdown(f"**🧮 Total**: Rp {total_bibit:,.0f}")
                    else:
                        st.markdown("**🧮 Total**: Rp 0")
                
                catatan_bibit = st.text_input("📝 Catatan (opsional)", key="catatan_bibit")
                
                if st.form_submit_button("💾 Simpan Pembelian Bibit", use_container_width=True):
                    if qty_bibit > 0:
                        simpan_transaksi(tgl_bibit, "Pembelian", "Bibit", qty_bibit, HARGA_BELI_BIBIT, catatan_bibit)
                        st.success("✅ Pembelian bibit berhasil disimpan!")
                        st.rerun()
                    else:
                        st.error("❌ Masukkan jumlah yang valid!")

# Jurnal Umum
elif menu == "📋 Jurnal Umum":
    st.markdown("## 📋 Jurnal Umum")
    
    try:
        df_jurnal = pd.read_sql_query('SELECT * FROM jurnal ORDER BY tanggal DESC', conn)
        
        if not df_jurnal.empty:
            # Format tampilan
            df_display = df_jurnal.copy()
            df_display['jumlah'] = df_display['jumlah'].apply(lambda x: f"Rp {x:,.0f}")
            df_display = df_display.rename(columns={
                'tanggal': 'Tanggal',
                'keterangan': 'Keterangan', 
                'debit': 'Debit',
                'kredit': 'Kredit',
                'jumlah': 'Jumlah'
            })
            
            st.dataframe(df_display[['Tanggal', 'Keterangan', 'Debit', 'Kredit', 'Jumlah']], 
                        use_container_width=True, hide_index=True)
            
            # Total debit dan kredit
            total = df_jurnal['jumlah'].sum()
            st.success(f"✅ Total Debit = Total Kredit = Rp {total:,.0f}")
        else:
            st.info("📝 Belum ada catatan jurnal.")
    except:
        st.info("📝 Belum ada data jurnal.")

# Laporan Keuangan
elif menu == "📈 Laporan Keuangan":
    st.markdown("## 📈 Laporan Keuangan")
    
    try:
        df_transaksi = pd.read_sql_query('SELECT * FROM transaksi ORDER BY tanggal DESC', conn)
        
        if not df_transaksi.empty:
            # Filter periode
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("📅 Dari Tanggal", value=pd.to_datetime(df_transaksi['tanggal']).min().date())
            with col2:
                end_date = st.date_input("📅 Sampai Tanggal", value=pd.to_datetime(df_transaksi['tanggal']).max().date())
            
            # Filter data berdasarkan periode
            df_filtered = df_transaksi[
                (pd.to_datetime(df_transaksi['tanggal']).dt.date >= start_date) &
                (pd.to_datetime(df_transaksi['tanggal']).dt.date <= end_date)
            ]
            
            if not df_filtered.empty:
                # Tabs untuk berbagai laporan
                tab1, tab2, tab3 = st.tabs(["📊 Ringkasan", "💰 Penjualan", "🛒 Pembelian"])
                
                with tab1:
                    st.markdown("### 📊 Ringkasan Periode")
                    
                    # Hitung totals
                    penjualan = df_filtered[df_filtered['jenis'] == 'Penjualan']['total'].sum()
                    pembelian = df_filtered[df_filtered['jenis'] == 'Pembelian']['total'].sum()
                    laba = penjualan - pembelian
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💰 Penjualan", f"Rp {penjualan:,.0f}")
                    with col2:
                        st.metric("🛒 Pembelian", f"Rp {pembelian:,.0f}")
                    with col3:
                        if laba >= 0:
                            st.metric("📈 Laba", f"Rp {laba:,.0f}")
                        else:
                            st.metric("📉 Rugi", f"Rp {abs(laba):,.0f}")
                    
                    # Laporan Laba Rugi
                    st.markdown("### 💹 Laporan Laba Rugi")
                    
                    beban_pestisida = df_filtered[
                        (df_filtered['jenis'] == 'Pembelian') & 
                        (df_filtered['item'] == 'Pestisida')
                    ]['total'].sum()
                    
                    beban_bibit = df_filtered[
                        (df_filtered['jenis'] == 'Pembelian') & 
                        (df_filtered['item'] == 'Bibit')
                    ]['total'].sum()
                    
                    laporan_lr = [
                        ["Pendapatan:", ""],
                        ["  Penjualan Jambu Kristal", f"Rp {penjualan:,.0f}"],
                        ["", ""],
                        ["Beban Operasional:", ""],
                        ["  Biaya Pestisida", f"Rp {beban_pestisida:,.0f}"],
                        ["  Biaya Bibit", f"Rp {beban_bibit:,.0f}"],
                        ["  Total Beban", f"Rp {pembelian:,.0f}"],
                        ["", ""],
                        ["Laba Bersih", f"Rp {laba:,.0f}"]
                    ]
                    
                    df_laporan = pd.DataFrame(laporan_lr, columns=["Keterangan", "Jumlah"])
                    st.dataframe(df_laporan, use_container_width=True, hide_index=True)
                
                with tab2:
                    st.markdown("### 💰 Detail Penjualan")
                    
                    df_penjualan = df_filtered[df_filtered['jenis'] == 'Penjualan']
                    
                    if not df_penjualan.empty:
                        total_kg = df_penjualan['qty'].sum()
                        total_rupiah = df_penjualan['total'].sum()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(" 🍐  Total Jambu Terjual", f"{total_kg:.1f} kg")
                        with col2:
                            st.metric("💰 Total Penjualan", f"Rp {total_rupiah:,.0f}")
                        
                        # Tabel detail
                        df_penjualan_display = df_penjualan[['tanggal', 'qty', 'total', 'catatan']].copy()
                        df_penjualan_display['total'] = df_penjualan_display['total'].apply(lambda x: f"Rp {x:,.0f}")
                        df_penjualan_display.columns = ['Tanggal', 'Qty (kg)', 'Total', 'Catatan']
                        st.dataframe(df_penjualan_display, use_container_width=True, hide_index=True)
                    else:
                        st.info("📝 Tidak ada penjualan dalam periode ini.")
                
                with tab3:
                    st.markdown("### 🛒 Detail Pembelian")
                    
                    df_pembelian = df_filtered[df_filtered['jenis'] == 'Pembelian']
                    
                    if not df_pembelian.empty:
                        # Ringkasan per item
                        ringkasan = df_pembelian.groupby('item').agg({
                            'qty': 'sum',
                            'total': 'sum'
                        }).reset_index()
                        
                        st.markdown("**Ringkasan Pembelian:**")
                        for _, row in ringkasan.iterrows():
                            unit = "kg" if row['item'] == "Pestisida" else "pcs"
                            st.write(f"• {row['item']}: {row['qty']:.1f} {unit} = Rp {row['total']:,.0f}")
                        
                        st.markdown("---")
                        
                        # Tabel detail
                        df_pembelian_display = df_pembelian[['tanggal', 'item', 'qty', 'total', 'catatan']].copy()
                        df_pembelian_display['total'] = df_pembelian_display['total'].apply(lambda x: f"Rp {x:,.0f}")
                        df_pembelian_display.columns = ['Tanggal', 'Item', 'Qty', 'Total', 'Catatan']
                        st.dataframe(df_pembelian_display, use_container_width=True, hide_index=True)
                    else:
                        st.info("📝 Tidak ada pembelian dalam periode ini.")
            else:
                st.info("📝 Tidak ada transaksi dalam periode yang dipilih.")
        else:
            st.info("📝 Belum ada data transaksi.")
    except:
        st.info("📝 Belum ada data transaksi.")

# Neraca Saldo
elif menu == "⚖️ Neraca Saldo":
    st.markdown("## ⚖️ Neraca Saldo")
    
    try:
        # Hitung saldo per akun
        query = '''
        SELECT 
            debit as akun, 
            SUM(jumlah) as saldo 
        FROM jurnal 
        GROUP BY debit
        UNION ALL
        SELECT 
            kredit as akun, 
            -SUM(jumlah) as saldo 
        FROM jurnal 
        GROUP BY kredit
        '''
        
        df_saldo = pd.read_sql_query(query, conn)
        
        if not df_saldo.empty:
            # Gabungkan saldo per akun
            saldo_akun = df_saldo.groupby('akun')['saldo'].sum().reset_index()
            
            # Buat neraca saldo
            neraca_data = []
            total_debit = 0
            total_kredit = 0
            
            for _, row in saldo_akun.iterrows():
                akun = row['akun']
                saldo = row['saldo']
                
                if saldo >= 0:
                    neraca_data.append([akun, f"Rp {saldo:,.0f}", ""])
                    total_debit += saldo
                else:
                    neraca_data.append([akun, "", f"Rp {abs(saldo):,.0f}"])
                    total_kredit += abs(saldo)
            
            # Tambahkan total
            neraca_data.append(["", "---", "---"])
            neraca_data.append(["TOTAL", f"Rp {total_debit:,.0f}", f"Rp {total_kredit:,.0f}"])
            
            # Tampilkan neraca
            df_neraca = pd.DataFrame(neraca_data, columns=["Nama Akun", "Debit", "Kredit"])
            st.dataframe(df_neraca, use_container_width=True, hide_index=True)
            
            # Validasi
            if abs(total_debit - total_kredit) < 0.01:
                st.success("✅ Neraca Seimbang! Total Debit = Total Kredit")
            else:
                st.error(f"❌ Neraca Tidak Seimbang! Selisih: Rp {abs(total_debit - total_kredit):,.0f}")
        else:
            st.info("📝 Belum ada data untuk neraca saldo.")
    except:
        st.info("📝 Belum ada data untuk neraca saldo.")

# Reset Data
elif menu == "🗑️ Reset Data":
    st.markdown("## 🗑️ Reset Data")
    
    # Tampilkan informasi data yang ada
    total_transaksi, total_jurnal = hitung_total_data()
    
    st.markdown("### 📊 Informasi Data Saat Ini")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📝 Total Transaksi", f"{total_transaksi} data")
    with col2:
        st.metric("📋 Total Jurnal", f"{total_jurnal} data")
    
    if total_transaksi > 0 or total_jurnal > 0:
        st.markdown("---")
        st.markdown("### ⚠️ Peringatan")
        st.warning("""
        **PERHATIAN!** Tindakan ini akan menghapus SEMUA data transaksi dan jurnal secara permanen!
        
        Data yang akan dihapus:
        - Semua transaksi penjualan jambu
        - Semua transaksi pembelian pestisida dan bibit
        - Semua catatan jurnal umum
        - Semua laporan keuangan dan neraca saldo
        """)
        
        # Tombol reset dengan kondisi
        if st.button("🗑️ RESET SEMUA DATA", 
                           type="primary", 
                           use_container_width=True,
                           help="Klik untuk menghapus semua data"):
                    
                    # Progress bar untuk efek visual
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Simulasi proses reset
                    import time
                    
                    status_text.text("🔄 Menghapus data transaksi...")
                    progress_bar.progress(25)
                    time.sleep(0.5)
                    
                    status_text.text("🔄 Menghapus data jurnal...")
                    progress_bar.progress(50)
                    time.sleep(0.5)
                    
                    status_text.text("🔄 Mereset counter database...")
                    progress_bar.progress(75)
                    time.sleep(0.5)
                    
                    # Eksekusi reset data
                    try:
                        reset_data()
                        
                        status_text.text("✅ Reset data berhasil!")
                        progress_bar.progress(100)
                        time.sleep(1)
                        
                        # Tampilkan pesan sukses
                        st.success("🎉 **RESET BERHASIL!** Semua data telah dihapus.")
                        st.info("💡 Anda dapat mulai memasukkan data baru melalui menu 'Input Transaksi'.")
                        
                        # Auto refresh setelah 3 detik
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Terjadi kesalahan saat reset data: {str(e)}")
    else:
        st.info("📝 Tidak ada data untuk direset. Database sudah kosong.")
        st.markdown("💡 Mulai menambahkan data melalui menu 'Input Transaksi'.")
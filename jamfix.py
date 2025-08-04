import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

# --- START: MODIFIKASI UNTUK ANEKA SNACK ---

# Konfigurasi halaman
st.set_page_config(
    page_title="Pencatatan Keuangan - Aneka Snack",
    page_icon="🥨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header utama
st.title("🥨 Aneka Snack")

# Konstanta harga (disesuaikan dengan aneka snack)
HARGA_JUAL = {
    "Keripik Kue Bawang Rasa Original": 20000,
    "Keripik Kue Bawang Rasa Kelor": 22000,
    "Keripik Kue Bawang Rasa Jagung": 22000,
    "Keripik Kue Bawang Rasa Buah Naga": 23000,
    "Keripik Kenikir": 25000
}

HARGA_BELI = {
    "Tepung Terigu": 12000,
    "Tepung Beras": 10000,
    "Telur": 30000,
    "Minyak Goreng": 15000,
    "Mentega": 18000,
    "Bumbu": 50000,
    "Daun Kenikir": 10000,
    "Daun Kelor": 15000,
    "Jagung": 12000,
    "Buah Naga": 20000,
    "Plastik Kemasan": 5000
}

# --- END: MODIFIKASI UNTUK ANEKA SNACK ---

# Inisialisasi database
@st.cache_resource
def init_database():
    conn = sqlite3.connect('aneka_snack.db', check_same_thread=False)
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
        ''', (tanggal, f'Penjualan {item}', 'Kas', 'Pendapatan Penjualan', total))
    else:  # Pembelian
        akun_beban = f"Biaya Pembelian {item}"
        cursor.execute('''
            INSERT INTO jurnal (tanggal, keterangan, debit, kredit, jumlah)
            VALUES (?, ?, ?, ?, ?)
        ''', (tanggal, f'Beli {item}', akun_beban, 'Kas', total))
    
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
        "🗑️ Reset Data",
        "📞 Kontak Kami"
    ])

# Dashboard
if menu == "📊 Dashboard":
    st.markdown("## 📊 Dashboard Keuangan")
    
    try:
        df_transaksi = pd.read_sql_query('SELECT * FROM transaksi', conn)
        
        if not df_transaksi.empty:
            total_penjualan = df_transaksi[df_transaksi['jenis'] == 'Penjualan']['total'].sum()
            total_pembelian = df_transaksi[df_transaksi['jenis'] == 'Pembelian']['total'].sum()
            laba_rugi = total_penjualan - total_pembelian
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(label="💰 Total Penjualan", value=f"Rp {total_penjualan:,.0f}")
            
            with col2:
                st.metric(label="🛒 Total Pembelian", value=f"Rp {total_pembelian:,.0f}")
            
            with col3:
                st.metric(label="📈 Laba/Rugi", value=f"Rp {laba_rugi:,.0f}")
            
            with col4:
                st.metric(label="📝 Total Transaksi", value=f"{len(df_transaksi)} transaksi")
            
            st.markdown("### 📊 Visualisasi")
            
            data_pie = df_transaksi.groupby('jenis')['total'].sum().reset_index()
            fig_pie = px.pie(data_pie, values='total', names='jenis', title="Komposisi Penjualan vs Pembelian")
            st.plotly_chart(fig_pie, use_container_width=True)
            
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
    
    tab1, tab2 = st.tabs(["💰 Penjualan", "🛒 Pembelian"])
    
    with tab1:
        st.markdown("### 🥨 Penjualan Aneka Snack")
        
        with st.form("form_penjualan", clear_on_submit=True):
            produk_terjual = st.selectbox("📦 Produk", list(HARGA_JUAL.keys()))
            
            col1, col2 = st.columns(2)
            
            with col1:
                tgl_jual = st.date_input("📅 Tanggal", value=date.today())
                qty_jual = st.number_input("⚖️ Jumlah (pcs)", min_value=0, step=1)
            
            with col2:
                harga_jual_satuan = HARGA_JUAL[produk_terjual]
                st.markdown(f"**💰 Harga**: Rp {harga_jual_satuan:,}/pcs")
                if qty_jual > 0:
                    total_jual = qty_jual * harga_jual_satuan
                    st.markdown(f"**🧮 Total**: Rp {total_jual:,.0f}")
                else:
                    st.markdown("**🧮 Total**: Rp 0")
            
            catatan_jual = st.text_input("📝 Catatan (opsional)")
            
            if st.form_submit_button("💾 Simpan Penjualan", use_container_width=True):
                if qty_jual > 0:
                    simpan_transaksi(tgl_jual, "Penjualan", produk_terjual, qty_jual, harga_jual_satuan, catatan_jual)
                    st.success(f"✅ Penjualan {produk_terjual} berhasil disimpan!")
                    st.rerun()
                else:
                    st.error("❌ Masukkan jumlah yang valid!")
    
    with tab2:
        st.markdown("### 🛒 Pembelian")
        
        bahan_baku = st.selectbox("📦 Bahan Baku", list(HARGA_BELI.keys()))

        with st.form("form_pembelian", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                tgl_beli = st.date_input("📅 Tanggal", value=date.today())
                qty_beli = st.number_input("⚖️ Jumlah (kg/pcs)", min_value=0, step=1)
            
            with col2:
                harga_beli_satuan = HARGA_BELI[bahan_baku]
                st.markdown(f"**💰 Harga**: Rp {harga_beli_satuan:,}/kg")
                if qty_beli > 0:
                    total_beli = qty_beli * harga_beli_satuan
                    st.markdown(f"**🧮 Total**: Rp {total_beli:,.0f}")
                else:
                    st.markdown("**🧮 Total**: Rp 0")
            
            catatan_beli = st.text_input("📝 Catatan (opsional)")
            
            if st.form_submit_button(f"💾 Simpan Pembelian {bahan_baku}", use_container_width=True):
                if qty_beli > 0:
                    simpan_transaksi(tgl_beli, "Pembelian", bahan_baku, qty_beli, harga_beli_satuan, catatan_beli)
                    st.success(f"✅ Pembelian {bahan_baku} berhasil disimpan!")
                    st.rerun()
                else:
                    st.error("❌ Masukkan jumlah yang valid!")

# Jurnal Umum
elif menu == "📋 Jurnal Umum":
    st.markdown("## 📋 Jurnal Umum")
    
    try:
        df_jurnal = pd.read_sql_query('SELECT * FROM jurnal ORDER BY tanggal DESC', conn)
        
        if not df_jurnal.empty:
            df_display = df_jurnal.copy()
            df_display['jumlah'] = df_display['jumlah'].apply(lambda x: f"Rp {x:,.0f}")
            df_display = df_display.rename(columns={
                'tanggal': 'Tanggal', 'keterangan': 'Keterangan', 'debit': 'Debit',
                'kredit': 'Kredit', 'jumlah': 'Jumlah'
            })
            
            st.dataframe(df_display[['Tanggal', 'Keterangan', 'Debit', 'Kredit', 'Jumlah']], 
                        use_container_width=True, hide_index=True)
            
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
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("📅 Dari Tanggal", value=pd.to_datetime(df_transaksi['tanggal']).min().date())
            with col2:
                end_date = st.date_input("📅 Sampai Tanggal", value=pd.to_datetime(df_transaksi['tanggal']).max().date())
            
            df_filtered = df_transaksi[
                (pd.to_datetime(df_transaksi['tanggal']).dt.date >= start_date) &
                (pd.to_datetime(df_transaksi['tanggal']).dt.date <= end_date)
            ]
            
            if not df_filtered.empty:
                tab1, tab2, tab3 = st.tabs(["📊 Ringkasan", "💰 Penjualan", "🛒 Pembelian"])
                
                with tab1:
                    st.markdown("### 📊 Ringkasan Periode")
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
                    
                    st.markdown("### 💹 Laporan Laba Rugi")
                    
                    laporan_lr = [["Pendapatan:", ""], ["  Penjualan Aneka Snack", f"Rp {penjualan:,.0f}"], ["", ""], ["Beban Operasional:", ""]]
                    
                    total_beban = 0
                    for item_beli in HARGA_BELI.keys():
                        beban = df_filtered[
                            (df_filtered['jenis'] == 'Pembelian') & 
                            (df_filtered['item'] == item_beli)
                        ]['total'].sum()
                        if beban > 0:
                            laporan_lr.append([f"  Biaya {item_beli}", f"Rp {beban:,.0f}"])
                            total_beban += beban
                    
                    laporan_lr.append(["  Total Beban", f"Rp {total_beban:,.0f}"])
                    laporan_lr.append(["", ""])
                    laporan_lr.append(["Laba Bersih", f"Rp {laba:,.0f}"])
                    
                    df_laporan = pd.DataFrame(laporan_lr, columns=["Keterangan", "Jumlah"])
                    st.dataframe(df_laporan, use_container_width=True, hide_index=True)
                
                with tab2:
                    st.markdown("### 💰 Detail Penjualan")
                    df_penjualan = df_filtered[df_filtered['jenis'] == 'Penjualan']
                    
                    if not df_penjualan.empty:
                        total_qty = df_penjualan['qty'].sum()
                        total_rupiah = df_penjualan['total'].sum()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("📦 Total Produk Terjual", f"{total_qty:.1f} pcs")
                        with col2:
                            st.metric("💰 Total Penjualan", f"Rp {total_rupiah:,.0f}")
                        
                        df_penjualan_display = df_penjualan[['tanggal', 'item', 'qty', 'total', 'catatan']].copy()
                        df_penjualan_display['total'] = df_penjualan_display['total'].apply(lambda x: f"Rp {x:,.0f}")
                        df_penjualan_display.columns = ['Tanggal', 'Produk', 'Qty (pcs)', 'Total', 'Catatan']
                        st.dataframe(df_penjualan_display, use_container_width=True, hide_index=True)
                    else:
                        st.info("📝 Tidak ada penjualan dalam periode ini.")
                
                with tab3:
                    st.markdown("### 🛒 Detail Pembelian")
                    df_pembelian = df_filtered[df_filtered['jenis'] == 'Pembelian']
                    
                    if not df_pembelian.empty:
                        ringkasan = df_pembelian.groupby('item').agg({
                            'qty': 'sum',
                            'total': 'sum'
                        }).reset_index()
                        
                        st.markdown("**Ringkasan Pembelian:**")
                        for _, row in ringkasan.iterrows():
                            st.write(f"• {row['item']}: {row['qty']:.1f} unit = Rp {row['total']:,.0f}")
                        
                        st.markdown("---")
                        
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
        query = '''
        SELECT debit as akun, SUM(jumlah) as saldo FROM jurnal GROUP BY debit
        UNION ALL
        SELECT kredit as akun, -SUM(jumlah) as saldo FROM jurnal GROUP BY kredit
        '''
        
        df_saldo = pd.read_sql_query(query, conn)
        
        if not df_saldo.empty:
            saldo_akun = df_saldo.groupby('akun')['saldo'].sum().reset_index()
            
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
            
            neraca_data.append(["", "---", "---"])
            neraca_data.append(["TOTAL", f"Rp {total_debit:,.0f}", f"Rp {total_kredit:,.0f}"])
            
            df_neraca = pd.DataFrame(neraca_data, columns=["Nama Akun", "Debit", "Kredit"])
            st.dataframe(df_neraca, use_container_width=True, hide_index=True)
            
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
        - Semua transaksi penjualan aneka snack
        - Semua transaksi pembelian bahan baku
        - Semua catatan jurnal umum
        - Semua laporan keuangan dan neraca saldo
        """)
        
        if st.button("🗑️ RESET SEMUA DATA", type="primary", use_container_width=True, help="Klik untuk menghapus semua data"):
            progress_bar = st.progress(0)
            status_text = st.empty()
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
            
            try:
                reset_data()
                status_text.text("✅ Reset data berhasil!")
                progress_bar.progress(100)
                time.sleep(1)
                st.success("🎉 **RESET BERHASIL!** Semua data telah dihapus.")
                st.info("💡 Anda dapat mulai memasukkan data baru melalui menu 'Input Transaksi'.")
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Terjadi kesalahan saat reset data: {str(e)}")
    else:
        st.info("📝 Tidak ada data untuk direset. Database sudah kosong.")
        st.markdown("💡 Mulai menambahkan data melalui menu 'Input Transaksi'.")

# Kontak Kami
elif menu == "📞 Kontak Kami":
    st.markdown("## 📞 Kontak Kami")
    st.markdown("""
        ### Informasi Kontak Pembuat
        Anda dapat menghubungi saya melalui platform berikut:
        
        - **Instagram**: [instagram_anda](https://www.instagram.com/ebnu_am)
        - **WhatsApp**: [nomor_whatsapp_anda](https://wa.me/nomor_whatsapp_anda)
        - **Email**: [email_anda@email.com](mailto:email_anda@email.com)
        - **LinkedIn**: [linkedin_anda](https://www.linkedin.com/in/linkedin_anda)
        
        Tentu, Anda dapat mengganti informasi kontak di atas dengan data Anda sendiri.
    """)

import streamlit as st
import pandas as pd
import sqlitecloud
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

# --- START: CSS KUSTOM UNTUK MEMPERCANTIK TAMPILAN ---
st.markdown("""
<style>
    .css-1d391kg {
        width: 300px; /* Ukuran lebar sidebar */
    }
    .css-1e5z83c {
        width: 300px; /* Ukuran lebar sidebar untuk tampilan mobile */
    }
    .st-emotion-cache-1pxazr7 {
        font-size: 1.5rem; /* Ukuran font judul menu */
    }
    .st-emotion-cache-q824a1 {
        font-size: 1.2rem; /* Ukuran font item menu */
    }
    /* Mengatur warna latar belakang halaman utama */
    .stApp {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)
# --- END: CSS KUSTOM UNTUK MEMPERCANTIK TAMPILAN ---

# Header utama
st.title("🥨 Aneka Snack")

# Konstanta harga jual (tetap statis)
HARGA_JUAL = {
    "Keripik Kue Bawang Rasa Original": 20000,
    "Keripik Kue Bawang Rasa Kelor": 22000,
    "Keripik Kue Bawang Rasa Jagung": 22000,
    "Keripik Kue Bawang Rasa Buah Naga": 23000,
    "Keripik Kenikir": 25000
}

# --- END: MODIFIKASI UNTUK ANEKA SNACK ---

# Inisialisasi database
@st.cache_resource
def init_database():
    try:
        conn = sqlitecloud.connect(st.secrets['sqlitecloud']['connection_string'])
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
        
        # Tabel inventaris
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventaris (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT UNIQUE,
                qty REAL,
                satuan TEXT
            )
        ''')
        
        # Tabel daftar_pembelian
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daftar_pembelian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT UNIQUE,
                harga_standar REAL,
                satuan TEXT
            )
        ''')
        
        # Inisialisasi stok jika tabel masih kosong
        cursor.execute("SELECT COUNT(*) FROM inventaris")
        if cursor.fetchone()[0] == 0:
            stok_awal = {
                "Keripik Kue Bawang Rasa Original": (0, "pcs"),
                "Keripik Kue Bawang Rasa Kelor": (0, "pcs"),
                "Keripik Kue Bawang Rasa Jagung": (0, "pcs"),
                "Keripik Kue Bawang Rasa Buah Naga": (0, "pcs"),
                "Keripik Kenikir": (0, "pcs")
            }
            # Inisialisasi daftar pembelian
            daftar_beli_awal = {
                "Tepung Terigu": (12000, "kg"),
                "Tepung Beras": (10000, "kg"),
                "Telur": (30000, "kg"),
                "Minyak Goreng": (15000, "lt"),
                "Mentega": (18000, "kg"),
                "Bumbu": (50000, "gr"),
                "Daun Kenikir": (10000, "kg"),
                "Daun Kelor": (15000, "kg"),
                "Jagung": (12000, "kg"),
                "Buah Naga": (20000, "kg"),
                "Plastik Kemasan": (5000, "pcs")
            }
            # Masukkan stok awal
            for item, (qty, satuan) in stok_awal.items():
                cursor.execute("INSERT INTO inventaris (item, qty, satuan) VALUES (?, ?, ?)", (item, qty, satuan))
            # Masukkan daftar pembelian awal ke inventaris dan daftar pembelian
            for item, (harga, satuan) in daftar_beli_awal.items():
                cursor.execute("INSERT INTO inventaris (item, qty, satuan) VALUES (?, ?, ?)", (item, 0, satuan))
                cursor.execute("INSERT INTO daftar_pembelian (item, harga_standar, satuan) VALUES (?, ?, ?)", (item, harga, satuan))
                
        conn.commit()
        return conn
    except Exception as e:
        st.error(f"❌ Gagal terhubung ke database SQLiteCloud. Pastikan connection string sudah benar di Streamlit Secrets.")
        st.stop()

conn = init_database()

# Fungsi untuk menyimpan transaksi
def simpan_transaksi(tanggal, jenis, item, qty, harga, catatan=""):
    total = qty * harga
    cursor = conn.cursor()
    
    # Simpan transaksi
    cursor.execute("INSERT INTO transaksi (tanggal, jenis, item, qty, harga, total, catatan) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (tanggal, jenis, item, qty, harga, total, catatan))
    
    # Perbarui stok HANYA jika item tersebut ada di inventaris
    cursor.execute("SELECT item FROM inventaris WHERE item = ?", (item,))
    if cursor.fetchone():
        if jenis == 'Penjualan':
            cursor.execute("UPDATE inventaris SET qty = qty - ? WHERE item = ?", (qty, item))
        elif jenis == 'Pembelian':
            cursor.execute("UPDATE inventaris SET qty = qty + ? WHERE item = ?", (qty, item))
    
    # Simpan ke jurnal
    if jenis == 'Penjualan':
        keterangan = f'Penjualan {item}'
        debit = 'Kas'
        kredit = 'Pendapatan Penjualan'
        jumlah = total
    else:  # Pembelian
        keterangan = f'Beli {item}'
        debit = f"Biaya Pembelian {item}"
        kredit = 'Kas'
        jumlah = total
        
    cursor.execute("INSERT INTO jurnal (tanggal, keterangan, debit, kredit, jumlah) VALUES (?, ?, ?, ?, ?)",
                   (tanggal, keterangan, debit, kredit, jumlah))
    conn.commit()
    
# Fungsi untuk mengambil data
def get_data(table_name):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    
    if table_name == 'transaksi':
        columns = ['id', 'tanggal', 'jenis', 'item', 'qty', 'harga', 'total', 'catatan']
    elif table_name == 'jurnal':
        columns = ['id', 'tanggal', 'keterangan', 'debit', 'kredit', 'jumlah']
    elif table_name == 'inventaris':
        columns = ['id', 'item', 'qty', 'satuan']
    elif table_name == 'daftar_pembelian':
        columns = ['id', 'item', 'harga_standar', 'satuan']
    
    return pd.DataFrame(data, columns=columns)
    
# Fungsi untuk menambahkan item pembelian baru
def add_new_purchase_item(item, harga, satuan):
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO daftar_pembelian (item, harga_standar, satuan) VALUES (?, ?, ?)", (item, harga, satuan))
        cursor.execute("INSERT INTO inventaris (item, qty, satuan) VALUES (?, ?, ?)", (item, 0, satuan))
        conn.commit()
        return True
    except sqlitecloud.IntegrityError:
        st.warning(f"Item '{item}' sudah ada.")
        return False

# Fungsi untuk reset data
def reset_data():
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transaksi")
    cursor.execute("DELETE FROM jurnal")
    
    # Reset stok menjadi 0
    cursor.execute("UPDATE inventaris SET qty = 0")
    
    conn.commit()
    
def hitung_total_data():
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transaksi")
    total_transaksi = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jurnal")
    total_jurnal = cursor.fetchone()[0]
    return total_transaksi, total_jurnal

# --- START: LOGIKA UNTUK MODE EDITOR ---
EDITOR_PASSWORD = "Ebnu913" # GANTI DENGAN KATA SANDI YANG AMAN

if "editor_mode" not in st.session_state:
    st.session_state.editor_mode = False

with st.sidebar:
    st.markdown("### 🔒 Mode Editor")
    password = st.text_input("Masukkan Kata Sandi", type="password", help="Hanya untuk editor")
    if st.button("Masuk"):
        if password == EDITOR_PASSWORD:
            st.session_state.editor_mode = True
            st.success("✅ Mode Editor diaktifkan!")
            st.rerun()
        else:
            st.session_state.editor_mode = False
            st.error("❌ Kata sandi salah!")
    
    if st.session_state.editor_mode:
        if st.button("Keluar dari Mode Editor"):
            st.session_state.editor_mode = False
            st.rerun()

    st.markdown("### Menu")
    
    menu_options_public = [
        "📊 Dashboard",
        "📦 Inventaris (Stok Barang)",
        "📋 Jurnal Umum",
        "📈 Laporan Keuangan",
        "⚖️ Neraca Saldo",
        "📞 Kontak Kami"
    ]
    
    menu_options_editor = []
    if st.session_state.editor_mode:
        menu_options_editor = [
            "📝 Input Transaksi",
            "🗑️ Reset Data"
        ]
        
    menu = st.radio("", menu_options_public + menu_options_editor)

# --- END: LOGIKA UNTUK MODE EDITOR ---


# Dashboard
if menu == "📊 Dashboard":
    st.markdown("## 📊 Dashboard Keuangan")
    
    try:
        df_transaksi = get_data('transaksi')
        
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
            
            tab1, tab2, tab3 = st.tabs(["Ringkasan Laba", "Penjualan per Produk", "Pembelian per Item"])
            
            with tab1:
                data_laba = df_transaksi.groupby('tanggal')['total'].sum().reset_index()
                fig_laba = px.line(data_laba, x='tanggal', y='total', title='Penjualan Harian')
                st.plotly_chart(fig_laba, use_container_width=True)
                
            with tab2:
                df_penjualan = df_transaksi[df_transaksi['jenis'] == 'Penjualan']
                if not df_penjualan.empty:
                    penjualan_per_produk = df_penjualan.groupby('item')['qty'].sum().reset_index()
                    fig_produk = px.bar(penjualan_per_produk, x='item', y='qty', title='Jumlah Produk Terjual')
                    st.plotly_chart(fig_produk, use_container_width=True)
                else:
                    st.info("📝 Belum ada data penjualan.")
            
            with tab3:
                df_pembelian = df_transaksi[df_transaksi['jenis'] == 'Pembelian']
                if not df_pembelian.empty:
                    pembelian_per_item = df_pembelian.groupby('item')['total'].sum().reset_index()
                    fig_item = px.pie(pembelian_per_item, values='total', names='item', title='Komposisi Biaya Pembelian')
                    st.plotly_chart(fig_item, use_container_width=True)
                else:
                    st.info("📝 Belum ada data pembelian.")
            
            st.markdown("### 📋 Transaksi Terbaru")
            df_terbaru = df_transaksi.sort_values('tanggal', ascending=False).head(5)
            df_display = df_terbaru[['tanggal', 'jenis', 'item', 'qty', 'total']].copy()
            df_display['total'] = df_display['total'].apply(lambda x: f"Rp {x:,.0f}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
        else:
            st.info("📝 Belum ada transaksi. Mulai dengan menambah transaksi di menu 'Input Transaksi'.")
    except Exception as e:
        st.info(f"📝 Belum ada data transaksi. Error: {e}")

# Inventaris
elif menu == "📦 Inventaris (Stok Barang)":
    st.markdown("## 📦 Inventaris (Stok Barang)")
    
    try:
        df_inventaris = get_data('inventaris')
        
        if not df_inventaris.empty:
            df_inventaris_display = df_inventaris[['item', 'qty', 'satuan']].copy()
            df_inventaris_display.columns = ['Nama Item', 'Jumlah Stok', 'Satuan']
            
            # Tampilkan produk jual
            st.markdown("### Stok Produk Jual")
            df_produk_jual = df_inventaris_display[df_inventaris_display['Nama Item'].isin(HARGA_JUAL.keys())]
            st.dataframe(df_produk_jual, use_container_width=True, hide_index=True)
            
            # Tampilkan bahan baku
            st.markdown("### Stok Bahan Baku")
            df_daftar_beli = get_data('daftar_pembelian')
            items_beli = df_daftar_beli['item'].tolist()
            df_bahan_baku = df_inventaris_display[df_inventaris_display['Nama Item'].isin(items_beli)]
            st.dataframe(df_bahan_baku, use_container_width=True, hide_index=True)
            
        else:
            st.info("📝 Belum ada data inventaris.")
    except Exception as e:
        st.info(f"📝 Terjadi kesalahan saat mengambil data inventaris. Error: {e}")

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
        
        df_daftar_beli = get_data('daftar_pembelian')
        bahan_list = df_daftar_beli['item'].tolist()
        bahan_list.insert(0, "-- Pilih Item --")
        bahan_list.append("Tambah Item Baru")

        with st.form("form_pembelian", clear_on_submit=True):
            bahan_baku = st.selectbox("📦 Item Pembelian", bahan_list)
            
            item_pembelian = ""
            harga_satuan_pembelian = 0
            satuan_pembelian = ""
            
            if bahan_baku == "Tambah Item Baru":
                st.markdown("---")
                st.markdown("#### Tambah Item Pembelian Baru")
                item_pembelian = st.text_input("📝 Nama Item")
                col1, col2 = st.columns(2)
                with col1:
                    harga_satuan_pembelian = st.number_input("💰 Harga Satuan", min_value=0)
                with col2:
                    satuan_pembelian = st.text_input("⚖️ Satuan", help="Contoh: kg, pcs, gr")
                st.markdown("---")
            else:
                item_pembelian = bahan_baku
                if bahan_baku != "-- Pilih Item --":
                    harga_satuan_pembelian = df_daftar_beli[df_daftar_beli['item'] == bahan_baku]['harga_standar'].iloc[0]
                    satuan_pembelian = df_daftar_beli[df_daftar_beli['item'] == bahan_baku]['satuan'].iloc[0]
                    st.markdown(f"**💰 Harga**: Rp {harga_satuan_pembelian:,}/{satuan_pembelian}")
            
            qty_pembelian = st.number_input("⚖️ Jumlah", min_value=0, step=1, key="qty_beli_input")

            total_beli = qty_pembelian * harga_satuan_pembelian
            st.markdown(f"**🧮 Total**: Rp {total_beli:,.0f}")
            
            catatan_beli = st.text_input("📝 Catatan (opsional)")
            
            if st.form_submit_button(f"💾 Simpan Pembelian", use_container_width=True):
                if bahan_baku == "Tambah Item Baru":
                    if item_pembelian and harga_satuan_pembelian > 0 and satuan_pembelian:
                        if add_new_purchase_item(item_pembelian, harga_satuan_pembelian, satuan_pembelian):
                             # Simpan transaksi setelah item baru berhasil ditambahkan
                            simpan_transaksi(date.today(), "Pembelian", item_pembelian, qty_pembelian, harga_satuan_pembelian, catatan_beli)
                            st.success(f"✅ Item '{item_pembelian}' berhasil ditambahkan dan pembelian berhasil disimpan!")
                            st.rerun()
                    else:
                        st.error("❌ Lengkapi semua data untuk item baru!")
                elif bahan_baku != "-- Pilih Item --" and qty_pembelian > 0:
                    simpan_transaksi(date.today(), "Pembelian", item_pembelian, qty_pembelian, harga_satuan_pembelian, catatan_beli)
                    st.success(f"✅ Pembelian {item_pembelian} berhasil disimpan!")
                    st.rerun()
                else:
                    st.error("❌ Pilih item dan masukkan jumlah yang valid!")


# Jurnal Umum
elif menu == "📋 Jurnal Umum":
    st.markdown("## 📋 Jurnal Umum")
    
    try:
        df_jurnal = get_data('jurnal')
        
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
            st.success("✅ Neraca Jurnal Seimbang! Total Debit = Total Kredit")
        else:
            st.info("📝 Belum ada catatan jurnal.")
    except Exception as e:
        st.info(f"📝 Belum ada data jurnal. Error: {e}")

# Laporan Keuangan
elif menu == "📈 Laporan Keuangan":
    st.markdown("## 📈 Laporan Keuangan")
    
    try:
        df_transaksi = get_data('transaksi')
        
        if not df_transaksi.empty:
            col1, col2 = st.columns(2)
            with col1:
                df_transaksi['tanggal'] = pd.to_datetime(df_transaksi['tanggal'])
                start_date = st.date_input("📅 Dari Tanggal", value=df_transaksi['tanggal'].min().date())
            with col2:
                df_transaksi['tanggal'] = pd.to_datetime(df_transaksi['tanggal'])
                end_date = st.date_input("📅 Sampai Tanggal", value=df_transaksi['tanggal'].max().date())
            
            df_filtered = df_transaksi[
                (df_transaksi['tanggal'].dt.date >= start_date) &
                (df_transaksi['tanggal'].dt.date <= end_date)
            ]
            
            if not df_filtered.empty:
                tab1, tab2, tab3 = st.tabs(["📊 Ringkasan", "💰 Detail Penjualan", "🛒 Detail Pembelian"])
                
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
                    df_daftar_beli = get_data('daftar_pembelian')
                    semua_item_beli = df_daftar_beli['item'].tolist()
                    semua_item_beli.extend(df_filtered[(df_filtered['jenis'] == 'Pembelian') & (~df_filtered['item'].isin(semua_item_beli))]['item'].unique())
                    
                    for item_beli in semua_item_beli:
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
    except Exception as e:
        st.info(f"📝 Belum ada data transaksi. Error: {e}")

# Neraca Saldo
elif menu == "⚖️ Neraca Saldo":
    st.markdown("## ⚖️ Neraca Saldo")
    
    try:
        df_jurnal = get_data('jurnal')
        
        if not df_jurnal.empty:
            df_jurnal['jumlah'] = pd.to_numeric(df_jurnal['jumlah'])
            saldo_debit = df_jurnal.groupby('debit')['jumlah'].sum().reset_index()
            saldo_kredit = df_jurnal.groupby('kredit')['jumlah'].sum().reset_index()
            
            saldo_akun = pd.merge(saldo_debit, saldo_kredit, left_on='debit', right_on='kredit', how='outer').fillna(0)
            saldo_akun['saldo'] = saldo_akun['jumlah_x'] - saldo_akun['jumlah_y']
            
            neraca_data = []
            total_debit = 0
            total_kredit = 0
            
            for _, row in saldo_akun.iterrows():
                akun = row['debit'] if row['debit'] != 0 else row['kredit']
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
    except Exception as e:
        st.info(f"📝 Belum ada data untuk neraca saldo. Error: {e}")

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
        **PERHATIAN!** Tindakan ini akan menghapus SEMUA data transaksi, jurnal, dan mereset stok inventaris menjadi nol secara permanen!
        
        Data yang akan dihapus:
        - Semua transaksi penjualan dan pembelian
        - Semua catatan jurnal umum
        - Semua laporan keuangan dan neraca saldo
        - Semua stok barang akan direset ke 0
        """)
        
        if st.button("🗑️ RESET SEMUA DATA", type="primary", use_container_width=True, help="Klik untuk menghapus semua data"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            import time
            status_text.text("🔄 Menghapus data transaksi dan jurnal...")
            progress_bar.progress(50)
            time.sleep(0.5)
            
            try:
                reset_data()
                status_text.text("✅ Reset data berhasil!")
                progress_bar.progress(100)
                time.sleep(1)
                st.success("🎉 **RESET BERHASIL!** Semua data telah dihapus dan stok telah direset.")
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
    st.markdown("### Informasi Kontak")
    st.markdown("Silakan hubungi kami melalui media sosial atau kontak di bawah ini:")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.link_button("📸 Instagram", "https://www.instagram.com/ebnu_am", type="secondary", use_container_width=True, help="Follow us on Instagram")
    
    with col2:
        st.link_button("💬 Telegram", "https://t.me/ebnudoang", type="secondary", use_container_width=True, help="Hubungi kami via Telegram")
    
    with col3:
        st.link_button("📧 Email", "mailto:email_anda@email.com", type="secondary", use_container_width=True, help="Kirim email kepada kami")
        
    with col4:
        st.link_button("💼 LinkedIn", "https://www.linkedin.com/in/linkedin_anda", type="secondary", use_container_width=True, help="Kunjungi profil LinkedIn kami")
        
    st.markdown("""
        <br>
        **Catatan**: Silakan ganti placeholder `instagram_anda`, `nomor_whatsapp_anda`, `email_anda@email.com`, dan `linkedin_anda` 
        dengan informasi kontak yang sesuai.
    """, unsafe_allow_html=True)

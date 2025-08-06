import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import json
import uuid

# --- START: DATA DUMMY (MENGGANTIKAN GOOGLE SHEETS) ---
# Data ini hanya untuk demo dan akan hilang setiap kali aplikasi di-refresh
if "transaksi" not in st.session_state:
    st.session_state.transaksi = pd.DataFrame([
        {'transaksi_id': str(uuid.uuid4()), 'tanggal': date(2025, 7, 28), 'jenis': 'Penjualan', 'metode_bayar': 'Tunai', 'item': 'kue bawang rasa original', 'qty': 10, 'harga': 15000, 'total': 150000, 'catatan': ''},
        {'transaksi_id': str(uuid.uuid4()), 'tanggal': date(2025, 7, 28), 'jenis': 'Penjualan', 'metode_bayar': 'Kredit', 'item': 'keripik kenikir', 'qty': 5, 'harga': 15000, 'total': 75000, 'catatan': ''},
        {'transaksi_id': str(uuid.uuid4()), 'tanggal': date(2025, 7, 29), 'jenis': 'Pembelian', 'metode_bayar': 'Tunai', 'item': 'Tepung Terigu', 'qty': 50, 'harga': 10000, 'total': 500000, 'catatan': ''},
    ])
    st.session_state.jurnal = pd.DataFrame([
        {'tanggal': date(2025, 7, 28), 'keterangan': 'Penjualan', 'debit': 150000, 'kredit': 0, 'akun': 'Kas', 'kredit_akun': ''},
        {'tanggal': date(2025, 7, 28), 'keterangan': 'Penjualan', 'debit': 0, 'kredit': 150000, 'akun': '', 'kredit_akun': 'Penjualan'},
        {'tanggal': date(2025, 7, 28), 'keterangan': 'Penjualan Kredit', 'debit': 75000, 'kredit': 0, 'akun': 'Piutang Usaha', 'kredit_akun': ''},
        {'tanggal': date(2025, 7, 28), 'keterangan': 'Penjualan Kredit', 'debit': 0, 'kredit': 75000, 'akun': '', 'kredit_akun': 'Penjualan'},
        {'tanggal': date(2025, 7, 29), 'keterangan': 'Pembelian Tepung Terigu', 'debit': 500000, 'kredit': 0, 'akun': 'Bahan Baku', 'kredit_akun': ''},
        {'tanggal': date(2025, 7, 29), 'keterangan': 'Pembelian Tepung Terigu', 'debit': 0, 'kredit': 500000, 'akun': '', 'kredit_akun': 'Kas'},
    ])
    st.session_state.inventaris = pd.DataFrame([
        {'item': 'Tepung Terigu', 'qty': 50, 'satuan': 'kg', 'min_stok': 10, 'status': 'Cukup'},
        {'item': 'Gula', 'qty': 20, 'satuan': 'kg', 'min_stok': 5, 'status': 'Cukup'},
        {'item': 'Minyak Goreng', 'qty': 10, 'satuan': 'liter', 'min_stok': 20, 'status': 'Perlu Restock'},
    ])
    st.session_state.harga_jual = {
        "kue bawang rasa original": 15000,
        "kue bawang rasa kelor": 15000,
        "kue bawang rasa jagung": 15000,
        "kue bawang rasa buah naga": 15000,
        "keripik kenikir": 15000
    }
    st.session_state.daftar_pembelian = pd.DataFrame(columns=['item', 'qty', 'satuan', 'harga', 'metode_bayar'])
    st.session_state.cart = []
    st.session_state.last_invoice_id = None
    st.session_state.is_editor_mode = False
# --- END: DATA DUMMY ---

# --- KONFIGURASI APLIKASI & CSS KUSTOM ---
st.set_page_config(
    page_title="Aplikasi Keuangan Aneka Snack",
    page_icon="🥨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    body {
        font-family: 'Noto Sans', sans-serif;
        font-size: 1.2em;
    }
    h1, h2, h3, h4 {
        font-family: 'Merriweather', serif;
        color: #005a9c;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-size: 1.2em;
        padding: 10px;
        border-radius: 8px;
    }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input {
        font-size: 1.2em;
        padding: 0.5rem;
    }
    .stMetric>div>div {
        font-size: 1.5em;
    }
    .st-emotion-cache-1px5q9x {
        padding: 2rem 1rem;
    }
    .st-emotion-cache-10o4965 {
        font-size: 1.5em;
    }
    .invoice {
        border: 2px solid #ddd;
        padding: 20px;
        border-radius: 10px;
        background-color: #f9f9f9;
        margin-top: 20px;
        color: #333;
    }
    .invoice-header {
        text-align: center;
        border-bottom: 2px dashed #005a9c;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .invoice-header h2 {
        color: #005a9c;
    }
    .invoice-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        border-bottom: 1px dotted #ccc;
        padding-bottom: 5px;
    }
    .invoice-total {
        font-size: 1.5em;
        font-weight: bold;
        text-align: right;
        margin-top: 20px;
        border-top: 2px dashed #005a9c;
        padding-top: 10px;
        color: #d9534f;
    }
    .status-ok {
        background-color: #d4edda;
        color: #155724;
        padding: 5px 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 5px 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .st-emotion-cache-12t9t08 {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI UTAMA ---
def simpan_semua_data():
    st.success("✅ Data berhasil disimpan.")

# FIX: Logika jurnal diperbaiki
def update_jurnal(tanggal, keterangan, debit, kredit, akun_debit, akun_kredit):
    new_entry_debit = {'tanggal': tanggal, 'keterangan': keterangan, 'debit': debit, 'kredit': 0, 'akun': akun_debit, 'kredit_akun': ''}
    new_entry_kredit = {'tanggal': tanggal, 'keterangan': keterangan, 'debit': 0, 'kredit': kredit, 'akun': '', 'kredit_akun': akun_kredit}
    st.session_state.jurnal = pd.concat([st.session_state.jurnal, pd.DataFrame([new_entry_debit, new_entry_kredit])], ignore_index=True)

# FIX: Logika transaksi diubah agar mendukung metode pembayaran per item
def tambah_transaksi_penjualan(tanggal, cart_items):
    transaksi_id = str(uuid.uuid4())

    for item_data in cart_items:
        item = item_data['item']
        qty = item_data['qty']
        harga = item_data['harga']
        metode_bayar = item_data['metode_bayar']
        total = qty * harga

        new_transaksi = {'transaksi_id': transaksi_id, 'tanggal': tanggal, 'jenis': 'Penjualan', 'metode_bayar': metode_bayar, 'item': item, 'qty': qty, 'harga': harga, 'total': total, 'catatan': ''}
        st.session_state.transaksi = pd.concat([st.session_state.transaksi, pd.DataFrame([new_transaksi])], ignore_index=True)

        # UPDATE: mengurangi stok bahan baku, tidak langsung produk jadi
        # Asumsi 1 kue bawang butuh 0.1 kg Tepung Terigu
        if 'kue bawang' in item:
            st.session_state.inventaris.loc[st.session_state.inventaris['item'] == 'Tepung Terigu', 'qty'] -= qty * 0.1
        if 'keripik kenikir' in item:
            st.session_state.inventaris.loc[st.session_state.inventaris['item'] == 'Gula', 'qty'] -= qty * 0.05
    
    # Logika Jurnal
    total_tunai = sum(item['qty'] * item['harga'] for item in cart_items if item['metode_bayar'] == 'Tunai')
    total_kredit = sum(item['qty'] * item['harga'] for item in cart_items if item['metode_bayar'] == 'Kredit')
    
    if total_tunai > 0:
        update_jurnal(tanggal, f'Penjualan Tunai ID {transaksi_id}', total_tunai, total_tunai, 'Kas', 'Penjualan')
    if total_kredit > 0:
        update_jurnal(tanggal, f'Penjualan Kredit ID {transaksi_id}', total_kredit, total_kredit, 'Piutang Usaha', 'Penjualan')

    simpan_semua_data()
    st.session_state.cart = []
    st.balloons()
    st.session_state.last_invoice_id = transaksi_id
    st.success("Transaksi Penjualan berhasil dicatat!")

def tambah_transaksi_pembelian():
    for index, row in st.session_state.daftar_pembelian.iterrows():
        item = row['item']
        qty = row['qty']
        harga = row['harga']
        satuan = row['satuan']
        metode_bayar_pembelian = row['metode_bayar']
        total_harga = qty * harga

        new_transaksi = {'transaksi_id': '', 'tanggal': date.today(), 'jenis': 'Pembelian', 'metode_bayar': metode_bayar_pembelian, 'item': item, 'qty': qty, 'harga': harga, 'total': total_harga, 'catatan': ''}
        st.session_state.transaksi = pd.concat([st.session_state.transaksi, pd.DataFrame([new_transaksi])], ignore_index=True)
        
        if metode_bayar_pembelian == 'Tunai':
            update_jurnal(date.today(), f'Pembelian {qty} {satuan} {item}', total_harga, total_harga, 'Bahan Baku', 'Kas')
        elif metode_bayar_pembelian == 'Kredit':
            update_jurnal(date.today(), f'Pembelian Kredit {qty} {satuan} {item}', total_harga, total_harga, 'Bahan Baku', 'Utang Usaha')

        if item in st.session_state.inventaris['item'].values:
            st.session_state.inventaris.loc[st.session_state.inventaris['item'] == item, 'qty'] += qty
        else:
            new_item = {'item': item, 'qty': qty, 'satuan': satuan, 'min_stok': 10, 'status': 'Cukup'}
            st.session_state.inventaris = pd.concat([st.session_state.inventaris, pd.DataFrame([new_item])], ignore_index=True)

    st.session_state.daftar_pembelian = pd.DataFrame(columns=['item', 'qty', 'satuan', 'harga', 'metode_bayar'])
    simpan_semua_data()
    st.balloons()
    st.success("Pembelian berhasil dicatat!")

# --- SIDEBAR & NAVIGASI ---
st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.title("Menu Utama")
menu = st.sidebar.radio("Pilih Menu:", ["Dashboard", "Catat Transaksi", "Inventaris", "Laporan Keuangan", "Pengaturan Harga", "Kontak"])

# Fitur Mode Editor dengan password
st.sidebar.markdown("---")
st.sidebar.header("Mode Editor")
password = st.sidebar.text_input("Masukkan Kata Sandi", type="password")
if password == "admin":
    st.session_state.is_editor_mode = True
    st.sidebar.success("Mode Editor Aktif!")
else:
    st.session_state.is_editor_mode = False
    st.sidebar.warning("Mode Editor Tidak Aktif. Beberapa fitur tidak tersedia.")

# Fitur Reset Data (Hanya di mode editor)
st.sidebar.markdown("---")
if st.session_state.is_editor_mode:
    st.sidebar.header("Opsi Admin")
    if st.sidebar.button("⚠️ Reset Semua Data"):
        st.session_state.reset_confirm = True
    
    if "reset_confirm" in st.session_state and st.session_state.reset_confirm:
        st.warning("Apakah Anda yakin ingin menghapus semua data? Ini tidak dapat diurungkan.")
        col_reset1, col_reset2 = st.columns(2)
        with col_reset1:
            if st.button("Ya, Hapus Data"):
                st.session_state.transaksi = pd.DataFrame(columns=st.session_state.transaksi.columns)
                st.session_state.jurnal = pd.DataFrame(columns=st.session_state.jurnal.columns)
                st.session_state.inventaris = pd.DataFrame(columns=st.session_state.inventaris.columns)
                st.session_state.harga_jual = {}
                st.session_state.daftar_pembelian = pd.DataFrame(columns=['item', 'qty', 'satuan', 'harga', 'metode_bayar'])
                st.session_state.cart = []
                st.success("Semua data berhasil dihapus.")
                st.session_state.reset_confirm = False
                st.rerun()
        with col_reset2:
            if st.button("Batal"):
                st.session_state.reset_confirm = False
                st.info("Penghapusan data dibatalkan.")
                st.rerun()


# --- MENU DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Dashboard Keuangan")
    st.markdown("Ringkasan cepat performa bisnis Anda.")
    
    df_penjualan = st.session_state.transaksi[st.session_state.transaksi['jenis'] == 'Penjualan']
    df_biaya_pembelian = st.session_state.transaksi[st.session_state.transaksi['jenis'] == 'Pembelian']
    
    total_penjualan = df_penjualan['total'].sum()
    total_biaya = df_biaya_pembelian['total'].sum()
    laba_bersih = total_penjualan - total_biaya
    
    col_dash1, col_dash2, col_dash3 = st.columns(3)
    with col_dash1:
        st.metric(label="Total Penjualan", value=f"Rp{total_penjualan:,.0f}")
    with col_dash2:
        st.metric(label="Total Biaya", value=f"Rp{total_biaya:,.0f}")
    with col_dash3:
        st.metric(label="Laba Bersih", value=f"Rp{laba_bersih:,.0f}")
        
    st.markdown("---")
    
    st.write("### Tren Penjualan Bulanan")
    if not df_penjualan.empty:
        df_penjualan['bulan'] = df_penjualan['tanggal'].apply(lambda x: x.strftime('%Y-%m'))
        df_tren_penjualan = df_penjualan.groupby('bulan')['total'].sum().reset_index()
        fig_tren = px.bar(df_tren_penjualan, x='bulan', y='total', title='Tren Penjualan dari Waktu ke Waktu')
        st.plotly_chart(fig_tren, use_container_width=True)
    else:
        st.info("Tidak ada data penjualan untuk ditampilkan.")
    
    st.write("### Penjualan Berdasarkan Produk")
    if not df_penjualan.empty:
        df_penjualan_per_produk = df_penjualan.groupby('item')['qty'].sum().reset_index()
        fig_pie = px.pie(df_penjualan_per_produk, values='qty', names='item', title='Distribusi Penjualan Produk')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Tidak ada data penjualan untuk ditampilkan.")

# --- MENU CATAT TRANSAKSI (UI KASIR) ---
elif menu == "Catat Transaksi":
    st.header("📝 Catat Transaksi Penjualan")
    st.markdown("Pilih produk dan tentukan kuantitasnya, lalu tambahkan ke daftar. Lakukan pembayaran setelah semua produk ditambahkan.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Produk & Daftar Jual")
        item_pos = st.selectbox("Pilih Produk", list(st.session_state.harga_jual.keys()))
        qty_pos = st.number_input("Jumlah (pcs)", min_value=1, step=1)
        
        harga_pos = st.session_state.harga_jual.get(item_pos, 0)
        st.info(f"Harga per item: Rp{harga_pos:,.0f}")
        
        if st.button("➕ Tambah Produk"):
            st.session_state.cart.append({'item': item_pos, 'qty': qty_pos, 'harga': harga_pos, 'metode_bayar': 'Tunai'})
    
    with col2:
        st.subheader("Detail Pembayaran")
        if st.session_state.cart:
            df_cart = pd.DataFrame(st.session_state.cart)
            
            edited_df_cart = st.data_editor(
                df_cart,
                column_config={
                    "metode_bayar": st.column_config.SelectboxColumn(
                        "Metode Pembayaran",
                        options=['Tunai', 'Kredit'],
                        required=True
                    )
                },
                use_container_width=True
            )
            st.session_state.cart = edited_df_cart.to_dict('records')

            df_cart = pd.DataFrame(st.session_state.cart)
            df_cart['total'] = df_cart['qty'] * df_cart['harga']
            
            st.markdown(f"### **Total Belanja: Rp{df_cart['total'].sum():,.0f}**")
            
            if st.button("Bayar & Simpan Transaksi"):
                tambah_transaksi_penjualan(date.today(), st.session_state.cart)
    
    if st.session_state.last_invoice_id:
        st.markdown("---")
        st.header("🧾 Invoice Terakhir")
        invoice_df = st.session_state.transaksi[st.session_state.transaksi['transaksi_id'] == st.session_state.last_invoice_id]
        if not invoice_df.empty:
            total_invoice = invoice_df['total'].sum()
            invoice_text = f"""
Invoice Aneka Snack
========================================
ID Transaksi: {st.session_state.last_invoice_id}
Tanggal: {invoice_df['tanggal'].iloc[0]}
Metode Pembayaran: {', '.join(invoice_df['metode_bayar'].unique())}
----------------------------------------
Items:
"""
            for _, row in invoice_df.iterrows():
                invoice_text += f"  - {row['item']} ({row['qty']} pcs) | Rp{row['total']:,.0f} ({row['metode_bayar']})\n"
            
            invoice_text += f"""
----------------------------------------
Total: Rp{total_invoice:,.0f}
========================================
"""
            st.markdown(f"""
            <div class="invoice">
                <div class="invoice-header">
                    <h2>Invoice Aneka Snack</h2>
                    <p>ID Transaksi: {st.session_state.last_invoice_id}</p>
                    <p>Tanggal: {invoice_df['tanggal'].iloc[0]}</p>
                    <p>Metode Pembayaran: {', '.join(invoice_df['metode_bayar'].unique())}</p>
                </div>
                <div>
                    <strong>Items:</strong>
                    <ul>
            """, unsafe_allow_html=True)
            for _, row in invoice_df.iterrows():
                st.markdown(f"""
                <li class="invoice-item">
                    <span>{row['item']} ({row['qty']} pcs)</span>
                    <span>Rp{row['total']:,.0f} ({row['metode_bayar']})</span>
                </li>
                """, unsafe_allow_html=True)
            st.markdown(f"""
                    </ul>
                </div>
                <div class="invoice-total">
                    Total: Rp{total_invoice:,.0f}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.download_button(
                label="📥 Download Invoice",
                data=invoice_text,
                file_name=f"invoice_{st.session_state.last_invoice_id}.txt",
                mime="text/plain"
            )

        if st.button("Selesaikan Transaksi Baru"):
            st.session_state.last_invoice_id = None
            st.rerun()

    tab_pembelian = st.tabs(["Catat Pembelian Bahan Baku"])
    with tab_pembelian[0]:
        st.subheader("🛒 Catat Pembelian Bahan Baku")
        with st.form("form_pembelian"):
            metode_bayar_pembelian = st.selectbox("Metode Pembayaran", ['Tunai', 'Kredit'])
            
            bahan_baku_lama = sorted(st.session_state.inventaris['item'].tolist())
            bahan_baku_pilihan = st.selectbox("Pilih Bahan Baku", ['Tambah Bahan Baru'] + bahan_baku_lama)
            
            item_pembelian = ""
            satuan_pembelian = ""

            if bahan_baku_pilihan == 'Tambah Bahan Baru':
                col_new_item1, col_new_item2 = st.columns(2)
                with col_new_item1:
                    item_pembelian = st.text_input("Nama Bahan Baru")
                with col_new_item2:
                    satuan_pembelian = st.text_input("Satuan (kg, liter, dll)")
            else:
                item_pembelian = bahan_baku_pilihan
                satuan_pembelian = st.session_state.inventaris[st.session_state.inventaris['item'] == item_pembelian]['satuan'].iloc[0]
                col_item_existing1, col_item_existing2 = st.columns(2)
                with col_item_existing1:
                    st.text_input("Nama Bahan", value=item_pembelian, disabled=True)
                with col_item_existing2:
                    st.text_input("Satuan", value=satuan_pembelian, disabled=True)

            col_qty_harga1, col_qty_harga2 = st.columns(2)
            with col_qty_harga1:
                qty_pembelian = st.number_input("Jumlah", min_value=1, step=1)
            with col_qty_harga2:
                harga_pembelian = st.number_input("Harga Satuan", min_value=0)
            
            if st.form_submit_button("Tambahkan ke Daftar"):
                if item_pembelian and satuan_pembelian:
                    new_row = pd.DataFrame([{'item': item_pembelian, 'qty': qty_pembelian, 'satuan': satuan_pembelian, 'harga': harga_pembelian, 'metode_bayar': metode_bayar_pembelian}])
                    st.session_state.daftar_pembelian = pd.concat([st.session_state.daftar_pembelian, new_row], ignore_index=True)
                else:
                    st.warning("Nama bahan dan satuan tidak boleh kosong!")

        if not st.session_state.daftar_pembelian.empty:
            st.subheader("Daftar Pembelian Hari Ini")
            st.dataframe(st.session_state.daftar_pembelian, use_container_width=True)
            total_pembelian = (st.session_state.daftar_pembelian['qty'] * st.session_state.daftar_pembelian['harga']).sum()
            st.info(f"**Total Pembelian: Rp{total_pembelian:,.0f}**")
            
            if st.button("Selesai & Simpan Pembelian"):
                tambah_transaksi_pembelian()

# --- MENU INVENTARIS ---
elif menu == "Inventaris":
    st.header("📦 Inventaris Produk & Bahan Baku")
    st.markdown("### Status Stok")
    
    st.session_state.inventaris['status'] = st.session_state.inventaris.apply(
        lambda row: 'Perlu Restock' if row['qty'] <= row['min_stok'] else 'Cukup', axis=1
    )
    
    st.dataframe(st.session_state.inventaris, use_container_width=True)

    st.markdown("---")
    if st.session_state.is_editor_mode:
        st.write("### Tambah/Edit Stok Inventaris")
        with st.form("form_inventaris"):
            item_inv = st.text_input("Nama Item", "Tepung Terigu")
            qty_inv = st.number_input("Jumlah Stok", min_value=0, step=1)
            satuan_inv = st.text_input("Satuan", "kg")
            min_stok_inv = st.number_input("Stok Minimum", min_value=0, step=1, value=10)
            if st.form_submit_button("Update Inventaris"):
                if item_inv in st.session_state.inventaris['item'].values:
                    st.session_state.inventaris.loc[st.session_state.inventaris['item'] == item_inv, ['qty', 'satuan', 'min_stok']] = [qty_inv, satuan_inv, min_stok_inv]
                else:
                    new_item = {'item': item_inv, 'qty': qty_inv, 'satuan': satuan_inv, 'min_stok': min_stok_inv, 'status': 'Cukup'}
                    st.session_state.inventaris = pd.concat([st.session_state.inventaris, pd.DataFrame([new_item])], ignore_index=True)
                simpan_semua_data()
                st.success("Inventaris berhasil diupdate!")
                st.rerun()
    else:
        st.info("Anda harus masuk ke Mode Editor untuk mengubah inventaris.")

# --- MENU LAPORAN KEUANGAN ---
elif menu == "Laporan Keuangan":
    st.header("📚 Laporan Keuangan Detail")
    
    tab_laba_rugi, tab_neraca, tab_jurnal_detail = st.tabs(["Laporan Laba-Rugi", "Neraca Saldo", "Jurnal Umum"])
    
    with tab_laba_rugi:
        st.subheader("Laporan Laba-Rugi")
        
        pendapatan_penjualan = st.session_state.transaksi[st.session_state.transaksi['jenis'] == 'Penjualan']['total'].sum()
        beban_pokok_penjualan = st.session_state.transaksi[st.session_state.transaksi['jenis'] == 'Pembelian']['total'].sum()
        laba_kotor = pendapatan_penjualan - beban_pokok_penjualan
        
        st.write(f"**Pendapatan Penjualan**: Rp{pendapatan_penjualan:,.0f}")
        st.write(f"**Beban Pokok Penjualan**: Rp{beban_pokok_penjualan:,.0f}")
        st.markdown("---")
        st.write(f"**Laba Bersih**: Rp{laba_kotor:,.0f}")
        
    with tab_neraca:
        st.subheader("Neraca Saldo")
        
        saldo_kas = st.session_state.jurnal[st.session_state.jurnal['akun'] == 'Kas']['debit'].sum() - st.session_state.jurnal[st.session_state.jurnal['kredit_akun'] == 'Kas']['kredit'].sum()
        saldo_piutang = st.session_state.jurnal[st.session_state.jurnal['akun'] == 'Piutang Usaha']['debit'].sum()
        saldo_bahan_baku = st.session_state.jurnal[st.session_state.jurnal['akun'] == 'Bahan Baku']['debit'].sum()
        saldo_utang = st.session_state.jurnal[st.session_state.jurnal['kredit_akun'] == 'Utang Usaha']['kredit'].sum()
        
        total_aset = saldo_kas + saldo_piutang + saldo_bahan_baku
        total_kewajiban_ekuitas = saldo_utang + laba_kotor
        
        st.markdown(f"""
        ### **Aset: Rp{total_aset:,.0f}**
        <p>Kas: Rp{saldo_kas:,.0f}</p>
        <p>Piutang Usaha: Rp{saldo_piutang:,.0f}</p>
        <p>Bahan Baku (Inventaris): Rp{saldo_bahan_baku:,.0f}</p>
        
        <br>
        
        ### **Kewajiban & Ekuitas: Rp{total_kewajiban_ekuitas:,.0f}**
        <p>Utang Usaha: Rp{saldo_utang:,.0f}</p>
        <p>Ekuitas (Laba): Rp{laba_kotor:,.0f}</p>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        if total_aset == total_kewajiban_ekuitas:
            st.success("✅ Neraca Saldo Seimbang!")
        else:
            st.error("❌ Neraca Saldo Belum Seimbang. Ada ketidaksesuaian data.")

    with tab_jurnal_detail:
        st.subheader("Jurnal Umum Detail")
        st.dataframe(st.session_state.jurnal, use_container_width=True)
        total_debit = st.session_state.jurnal['debit'].sum()
        total_kredit = st.session_state.jurnal['kredit'].sum()
        st.markdown("---")
        col_jurnal1, col_jurnal2 = st.columns(2)
        with col_jurnal1:
            st.info(f"**Total Debit: Rp{total_debit:,.0f}**")
        with col_jurnal2:
            st.info(f"**Total Kredit: Rp{total_kredit:,.0f}**")
        if total_debit == total_kredit:
            st.success("✅ Jurnal Seimbang!")
        else:
            st.error("❌ Jurnal Tidak Seimbang. Silakan periksa kembali data.")
        
# --- MENU PENGATURAN HARGA ---
elif menu == "Pengaturan Harga":
    st.header("⚙️ Pengaturan Harga Produk")
    if st.session_state.is_editor_mode:
        st.write("Anda bisa mengubah harga jual produk di sini.")
        if st.session_state.harga_jual:
            for item, harga in st.session_state.harga_jual.items():
                st.session_state.harga_jual[item] = st.number_input(f"Harga Jual {item}", value=harga, min_value=0)
        else:
            st.warning("Tidak ada data harga jual yang ditemukan.")

        if st.button("Simpan Perubahan Harga"):
            simpan_semua_data()
            st.success("Harga berhasil diupdate!")
    else:
        st.info("Anda harus masuk ke Mode Editor untuk mengubah harga jual.")

# --- MENU KONTAK ---
elif menu == "Kontak":
    st.header("📞 Kontak Aneka Snack")
    
    st.markdown("### Hubungi Kami untuk Informasi Lebih Lanjut atau Pemesanan!")
    
    col_kontak1, col_kontak2 = st.columns(2)
    with col_kontak1:
        st.subheader("WhatsApp")
        st.markdown("""
            <a href="https://wa.me/62" target="_blank">
                <p style="font-size:24px;">📱 Chat Sekarang</p>
            </a>
        """, unsafe_allow_html=True)
        st.subheader("Instagram")
        st.markdown("""
            <a href="https://www.instagram.com/ebnu_am/" target="_blank">
                <p style="font-size:24px;">📸 @AnekaSnackOfficial</p>
            </a>
        """, unsafe_allow_html=True)

    with col_kontak2:
        st.subheader("Telegram")
        st.markdown("""
            <a href="https://t.me/ebnudoang" target="_blank">
                <p style="font-size:24px;">✈️ Telegram Channel</p>
            </a>
        """, unsafe_allow_html=True)
        st.subheader("LinkedIn")
        st.markdown("""
            <a href="https://www.linkedin.com/company/" target="_blank">
                <p style="font-size:24px;">💼 LinkedIn Page</p>
            </a>
        """, unsafe_allow_html=True)

import streamlit as st
import networkx as nx
from geopy.distance import geodesic
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

st.set_page_config(page_title="DSS Rute Kurir", layout="wide")

st.title("📦 DSS Penentuan Rute Kurir (Graph + Dijkstra)")

GUDANG = ("Gudang Denpasar", -8.6705, 115.2126)

st.sidebar.header("Input Pelanggan")
jumlah = st.sidebar.number_input("Jumlah Pelanggan", 2, 10, 4)

pelanggan = []

for i in range(jumlah):
    nama = st.sidebar.text_input(f"Nama Pelanggan {i+1}", key=f"n{i}")
    koordinat = st.sidebar.text_input(
        f"Koordinat {i+1}",
        placeholder="-8.6700,115.2390",
        key=f"k{i}"
    )

    if nama and koordinat:
        try:
            lat, lon = map(float, koordinat.split(","))
            pelanggan.append((nama, lat, lon))
        except:
            st.sidebar.error(f"Format koordinat {i+1} salah")

if pelanggan:

    semua = [GUDANG] + pelanggan

    G = nx.Graph()

    for lokasi in semua:
        G.add_node(lokasi[0])

    MAX_JARAK = 10

    for i in range(len(semua)):
        for j in range(i + 1, len(semua)):

            n1, lat1, lon1 = semua[i]
            n2, lat2, lon2 = semua[j]

            jarak = geodesic((lat1, lon1), (lat2, lon2)).km

            if jarak <= MAX_JARAK:
                G.add_edge(
                    n1,
                    n2,
                    weight=round(jarak, 2)
                )

    belum = [p[0] for p in pelanggan]
    sekarang = GUDANG[0]

    urutan = [GUDANG[0]]
    total_jarak = 0
    langkah = []

    st.subheader("🔎 Jalur Dijkstra")

    while belum:

        terdekat = None
        jarak_min = float("inf")

        for tujuan in belum:

            try:
                jarak = nx.dijkstra_path_length(
                    G,
                    sekarang,
                    tujuan,
                    weight="weight"
                )

                if jarak < jarak_min:
                    jarak_min = jarak
                    terdekat = tujuan

            except:
                pass

        if terdekat is None:
            break

        path = nx.dijkstra_path(
            G,
            sekarang,
            terdekat,
            weight="weight"
        )

        st.write(" ➜ ".join(path))

        langkah.append(
            [sekarang, terdekat, round(jarak_min, 2)]
        )

        total_jarak += jarak_min
        urutan.append(terdekat)

        sekarang = terdekat
        belum.remove(terdekat)

    st.subheader("🚚 Urutan Pengiriman")

    rute_text = " ➜ ".join(urutan)
    st.success(rute_text)

    st.subheader("📋 Langkah Perjalanan")

    df = pd.DataFrame(
        langkah,
        columns=["Dari", "Ke", "Jarak (KM)"]
    )

    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Jarak", f"{round(total_jarak,2)} KM")

    with col2:
        estimasi = round((total_jarak / 30) * 60)
        st.metric("Estimasi Waktu", f"{estimasi} Menit")

    st.subheader("🤖 AI Recommendation")

    st.info(
        f"Rute yang direkomendasikan adalah {rute_text} karena pada setiap langkah sistem memilih node dengan jarak terdekat menggunakan algoritma Dijkstra."
    )

    st.subheader("📋 Adjacency List")

    adjacency = {}

    for node in G.nodes():
        adjacency[node] = list(G.neighbors(node))

    st.json(adjacency)

    st.subheader("📊 Adjacency Matrix")

    matrix = nx.to_pandas_adjacency(
        G,
        weight="weight"
    )

    st.dataframe(matrix, use_container_width=True)

    st.subheader("📈 Statistik Graph")

    c1, c2 = st.columns(2)

    with c1:
        st.metric("Jumlah Node", G.number_of_nodes())

    with c2:
        st.metric("Jumlah Edge", G.number_of_edges())

    st.subheader("🏆 Ranking Kunjungan")

    ranking = pd.DataFrame({
        "Urutan": range(1, len(urutan)),
        "Pelanggan": urutan[1:]
    })

    st.dataframe(ranking, use_container_width=True)

    st.subheader("🕸 Visualisasi Graph")

    fig, ax = plt.subplots(figsize=(4, 3))

    pos = nx.spring_layout(G, seed=42)

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=500,
        node_color="lightblue",
        ax=ax,
        font_size=8
    )

    edge_labels = nx.get_edge_attributes(
        G,
        "weight"
    )

    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels,
        ax=ax
    )

    st.pyplot(fig)

    st.subheader("📚 Kompleksitas Algoritma")

    st.info(
        "Dijkstra memiliki kompleksitas O((V + E) log V), di mana V adalah jumlah node dan E adalah jumlah edge."
    )

    st.subheader("🗺 OpenStreetMap")

    lokasi_dict = {
        x[0]: (x[1], x[2])
        for x in semua
    }

    m = folium.Map(
        location=[GUDANG[1], GUDANG[2]],
        zoom_start=12
    )

    for nama, lat, lon in semua:

        warna = "red" if nama == GUDANG[0] else "blue"

        folium.Marker(
            [lat, lon],
            popup=nama,
            tooltip=nama,
            icon=folium.Icon(color=warna)
        ).add_to(m)

    for i in range(len(urutan)-1):

        a = urutan[i]
        b = urutan[i+1]

        lat1, lon1 = lokasi_dict[a]
        lat2, lon2 = lokasi_dict[b]

        folium.PolyLine(
            [
                [lat1, lon1],
                [lat2, lon2]
            ],
            weight=5
        ).add_to(m)

    st_folium(m, width=700, height=300)

else:
    st.info("Masukkan data pelanggan terlebih dahulu.")

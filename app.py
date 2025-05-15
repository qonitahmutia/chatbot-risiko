import streamlit as st
import openai
import pandas as pd
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Chatbot Risiko Proyek", layout="wide")
st.title("🤖 Chatbot Interaktif: Identifikasi Risiko Proyek")

# Inisialisasi chat dan hasil analisis
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": "Kamu adalah AI yang membantu identifikasi risiko proyek secara profesional dan komunikatif."}
    ]
if "last_table" not in st.session_state:
    st.session_state.last_table = None  # Menyimpan hasil DataFrame terakhir

# Tahap input proyek
if "project_set" not in st.session_state:
    project_description = st.text_area("📝 Masukkan deskripsi proyek terlebih dahulu:")

    if st.button("🔍 Analisis Awal"):
        prompt_awal = f"""
        Proyek ini: {project_description}

        Lakukan 4 hal:
        1. Identifikasi 5 risiko potensial
        2. Tentukan stakeholder terkait
        3. Beri skor dampak (1–5) dan kemungkinan (1–5)
        4. Saran mitigasi

        Jawab dalam format tabel markdown: | Risiko | Stakeholder | Dampak | Kemungkinan | Mitigasi |
        """

        st.session_state.chat_history.append({"role": "user", "content": prompt_awal})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.chat_history
        )

        reply = response["choices"][0]["message"]["content"]
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.session_state.project_set = True

        # Coba parse ke DataFrame
        try:
            if "|" in reply:
                df = pd.read_csv(io.StringIO(reply), sep="|", engine="python", skipinitialspace=True, skiprows=1)
                df = df.dropna(axis=1, how='all')
                st.session_state.last_table = df
                st.success("✅ Hasil analisis berhasil dibaca sebagai tabel.")
        except Exception as e:
            st.warning("Gagal parsing tabel dari hasil AI.")

# Input percakapan lanjutan
if st.session_state.get("project_set", False):
    st.markdown("---")
    st.subheader("💬 Lanjutkan Percakapan")
    user_input = st.text_input("Ketik balasan atau pertanyaan Anda:")

    if st.button("Kirim"):
        if user_input.strip() != "":
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.chat_history
            )

            reply = response["choices"][0]["message"]["content"]
            st.session_state.chat_history.append({"role": "assistant", "content": reply})

            # Cek apakah ada tabel baru
            if "|" in reply:
                try:
                    df = pd.read_csv(io.StringIO(reply), sep="|", engine="python", skipinitialspace=True, skiprows=1)
                    df = df.dropna(axis=1, how='all')
                    st.session_state.last_table = df
                except:
                    pass
        else:
            st.warning("Silakan isi pesan terlebih dahulu.")

# Tampilkan chat log
if len(st.session_state.chat_history) > 1:
    st.markdown("---")
    st.subheader("📜 Riwayat Percakapan")
    for msg in st.session_state.chat_history[1:]:
        speaker = "🧑‍💻 Kamu" if msg["role"] == "user" else "🤖 AI"
        st.markdown(f"**{speaker}:** {msg['content']}")

# Tampilkan dan download tabel risiko
if st.session_state.last_table is not None:
    st.markdown("---")
    st.subheader("📊 Tabel Risiko dari AI")
    st.dataframe(st.session_state.last_table)

    csv_data = st.session_state.last_table.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Download Tabel Risiko sebagai CSV",
        data=csv_data,
        file_name="hasil_analisis_risiko.csv",
        mime="text/csv"
    )

import matplotlib.pyplot as plt

# 🔥 Heatmap visualisasi risiko
st.subheader("📈 Visualisasi Matriks Risiko")

try:
    df = st.session_state.last_table.copy()

    # Pastikan kolom int
    df['Dampak'] = pd.to_numeric(df['Dampak'], errors='coerce')
    df['Kemungkinan'] = pd.to_numeric(df['Kemungkinan'], errors='coerce')
    df.dropna(subset=['Dampak', 'Kemungkinan'], inplace=True)

    fig, ax = plt.subplots(figsize=(6, 6))
    scatter = ax.scatter(
        df['Kemungkinan'],
        df['Dampak'],
        s=500,
        c=df['Dampak'] * df['Kemungkinan'],
        cmap='Reds',
        alpha=0.7,
        edgecolors='black'
    )

    for i, txt in enumerate(df['Risiko']):
        ax.annotate(txt.strip(), (df['Kemungkinan'].iloc[i], df['Dampak'].iloc[i]),
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)

    ax.set_xlabel('Kemungkinan (1-5)')
    ax.set_ylabel('Dampak (1-5)')
    ax.set_title('Matriks Risiko Proyek')
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(0.5, 5.5)
    ax.grid(True)

    st.pyplot(fig)

except Exception as e:
    st.warning("⚠️ Gagal menampilkan heatmap. Pastikan kolom 'Dampak', 'Kemungkinan', dan 'Risiko' tersedia.")


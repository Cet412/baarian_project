import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np

# Load model YOLOv8
model = YOLO(r"Streamlit\Baarian_Model.pt")

st.set_page_config(page_title="Deteksi Bahasa Isyarat BISINDO", layout="centered")
st.title("📷 Deteksi Bahasa Isyarat - BISINDO")
st.markdown("Gunakan kamera untuk mengirim satu huruf isyarat:")

# Ambil input dari kamera
img = st.camera_input("Ambil gambar dari kamera")

if img is not None:
    # Buka gambar dengan PIL
    image = Image.open(img)

    # Tampilkan gambar original
    st.image(image, caption="Gambar dari Kamera", use_container_width=True)

    # Konversi ke numpy array (RGB -> BGR)
    img_np = np.array(image)
    img_bgr = img_np[:, :, ::-1]

    # Jalankan deteksi dengan threshold rendah (biar sensitif)
    results = model.predict(img_bgr, conf=0.7, verbose=False)
    result = results[0]

    # Gambar hasil deteksi
    annotated = result.plot()

    # Tampilkan gambar hasil anotasi
    st.image(annotated, caption="Hasil Deteksi", use_container_width=True)

    # Ambil huruf terdeteksi jika ada
    if len(result.boxes) > 0:
        detected_class = result.names[int(result.boxes[0].cls.item())]
        st.success(f"Huruf terdeteksi: **{detected_class}**")
    else:
        st.warning("❌ Tidak ada huruf terdeteksi. Coba ubah posisi tangan, pencahayaan, atau ulangi gestur.")
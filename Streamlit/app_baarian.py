import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np

# Load model YOLOv8
model = YOLO(r"Streamlit\Baarian_Model.pt")

st.set_page_config(page_title="BISINDO Sign Language Detection", layout="centered")
st.title("📷 BISINDO Sign Language Detection")
st.markdown("Use the camera to send a single sign language letter:")

# Capture input from the camera
img = st.camera_input("Capture image from camera")

if img is not None:
    # Open the image with PIL
    image = Image.open(img)

    # Display the original image
    st.image(image, caption="Camera image", use_container_width=True)

    # Convert to numpy array (RGB -> BGR)
    img_np = np.array(image)
    img_bgr = img_np[:, :, ::-1]

    # Run detection with a low threshold (for sensitivity)
    results = model.predict(img_bgr, conf=0.7, verbose=False)
    result = results[0]

    # Plot detection results
    annotated = result.plot()

    # Display the annotated image
    st.image(annotated, caption="Detection result", use_container_width=True)

    # Get the detected letter if any
    if len(result.boxes) > 0:
        detected_class = result.names[int(result.boxes[0].cls.item())]
        st.success(f"Detected letter: **{detected_class}**")
    else:
        st.warning("❌ No letter detected. Try changing hand position, lighting, or repeat the gesture.")
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import easyocr
import matplotlib.pyplot as plt
import re
from PIL import Image, ImageEnhance, ImageOps

# Load models and encoders
hydration_model = joblib.load("hydration_model.pkl")
hydration_encoder = joblib.load("label_encoder.pkl")
season_model = joblib.load("season_model.pkl")
season_encoder = joblib.load("season_label_encoder.pkl")

st.set_page_config(page_title="Hydration Predictor", layout="wide")
st.title("💧 Hydration and Seasonal Context Analyzer")

reader = easyocr.Reader(['en'], gpu=False)

# Preprocessing
def preprocess_image(img):
    img = ImageOps.grayscale(img)
    img = img.resize((img.width * 2, img.height * 2))
    img = ImageEnhance.Contrast(img).enhance(2)
    return img

# Combine broken lines from OCR
def group_text_lines(lines):
    grouped = []
    current = ""
    for line in lines:
        line = line.strip()
        if line == "":
            continue
        if any(x in line.lower() for x in ["temp", "gsr", "humidity", "="]) or line.replace('.', '', 1).isdigit():
            current += " " + line
        else:
            if current:
                grouped.append(current.strip())
                current = line
            else:
                current = line
    if current:
        grouped.append(current.strip())
    return grouped

# Flexible value extraction
def extract_value(lines, keyword):
    full_text = " ".join(lines).lower().replace("=", "").replace(":", "").replace("c", "").replace("%", "")
    aliases = {
        "body temp": ["body temp", "temp", "temperature"],
        "gsr": ["gsr"],
        "env temp": ["env temp", "environment temp", "envtemperature"],
        "humidity": ["humidity"]
    }
    patterns = aliases.get(keyword.lower(), [keyword.lower()])
    for pattern in patterns:
        match = re.findall(rf"{pattern}[\s\S]{{0,10}}?([-+]?\d*\.\d+|\d+)", full_text)
        if match:
            return float(match[0])
    return None

# File uploader
uploaded_image = st.file_uploader("📷 Upload Screenshot from Serial Monitor", type=["png", "jpg", "jpeg"])

body_temp = gsr_value = env_temp = humidity = None
if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="🖼️ Uploaded Image", use_column_width=True)

    st.subheader("🛠️ Preprocessing and Extracting...")
    with st.spinner("🧠 Running OCR on preprocessed image..."):
        processed_img = preprocess_image(image)
        raw_results = reader.readtext(np.array(processed_img), detail=0)
        grouped_lines = group_text_lines(raw_results)

    st.subheader("📄 OCR Grouped Text:")
    st.code(grouped_lines)

    # Extract sensor values
    body_temp = extract_value(grouped_lines, "Body Temp")
    gsr_value = extract_value(grouped_lines, "GSR")
    env_temp = extract_value(grouped_lines, "Env Temp")
    humidity = extract_value(grouped_lines, "Humidity")

    st.subheader("🧪 Extracted Values")
    st.write(f"🔍 Body Temp: `{body_temp}`")
    st.write(f"🔍 GSR: `{gsr_value}`")
    st.write(f"🔍 Env Temp: `{env_temp}`")
    st.write(f"🔍 Humidity: `{humidity}`")

# Manual override toggle
manual_mode = st.checkbox("✏️ Manually Input Data (For Verification)")
if manual_mode or None in [body_temp, gsr_value, env_temp, humidity]:
    st.warning("🔧 Please enter values manually:")
    body_temp = st.number_input("🌡️ Enter Body Temp (°C)", value=body_temp if body_temp else 0.0)
    gsr_value = st.number_input("🖐️ Enter GSR Value", value=gsr_value if gsr_value else 0)
    env_temp = st.number_input("🌤️ Enter Environmental Temp (°C)", value=env_temp if env_temp else 0.0)
    humidity = st.number_input("💧 Enter Humidity (%)", value=humidity if humidity else 0.0)

# Predict if all values are available
if all(val not in [None, 0, 0.0] for val in [body_temp, gsr_value, env_temp, humidity]):
    hydration_pred = hydration_model.predict([[body_temp, gsr_value]])[0]
    hydration_label = hydration_encoder.inverse_transform([hydration_pred])[0]

    season_pred = season_model.predict([[env_temp, humidity]])[0]
    season_label = season_encoder.inverse_transform([season_pred])[0]

    st.header("📊 Prediction Results")
    col1, col2 = st.columns(2)
    col1.metric("Hydration Status", hydration_label)
    col2.markdown(f"<h5 style='font-size:18px;'>Seasonal Context: {season_label}</h5>", unsafe_allow_html=True)

    st.subheader("💡 Recommendations")
    if "Dehydrated Skin" in hydration_label.lower():
        st.warning("🧴 Drink plenty of water and rest.")
    else:
        st.info("Keep drinking water!")

    if "summer" in season_label.lower():
        st.warning("🌞 It's hot! Stay cool and drink extra fluids.")
    elif "winter" in season_label.lower():
        st.info("🧥 Keep warm and monitor your hydration subtly.")
    else:
        st.info("🍃 Moderate weather conditions. Stay balanced!")

    st.subheader("📈 Sensor Readings")
    fig, ax = plt.subplots()
    ax.bar(["Body Temp (°C)", "GSR", "Env Temp (°C)", "Humidity (%)"],
           [body_temp, gsr_value, env_temp, humidity], color='teal')
    ax.set_ylabel("Values")
    ax.set_title("Sensor Inputs")
    st.pyplot(fig)

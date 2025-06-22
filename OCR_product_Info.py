import streamlit as st
import easyocr
import re
import requests
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt

# OCR Reader
reader = easyocr.Reader(['en'], gpu=True)

st.set_page_config(page_title="OCR Product Finder", layout="wide")
st.markdown("""
    <h1 style="
        text-align: center;
        background: linear-gradient(to right, #FF512F, #DD2476);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Segoe UI', sans-serif;
        font-size: 3em;
        margin-bottom: 0.5em;
    ">
        🧾 OCR/Barcode Based Product Info Finder
    </h1>
""", unsafe_allow_html=True)
st.write("Upload an image of a food product label to retrieve its information.")

# Upload Image
uploaded_file = st.file_uploader("📤 Upload Product Image", type=["jpg", "jpeg", "png"])

def search_open_food_facts(query, max_products=5):
    api_url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={query}&search_simple=1&json=1"
    response = requests.get(api_url)
    try:
        data = response.json()
    except ValueError:
        return []
    products = data.get('products', [])
    return products[:max_products]

if uploaded_file:
    # Convert uploaded image to OpenCV format
    image = Image.open(uploaded_file).convert("RGB")
    img_array = np.array(image)
    results = reader.readtext(img_array)

    # Draw results on image
    for result in results:
        top_left = tuple([int(val) for val in result[0][0]])
        bottom_right = tuple([int(val) for val in result[0][2]])
        text = result[1]
        img_array = cv2.rectangle(img_array, top_left, bottom_right, (0, 255, 0), 2)
        img_array = cv2.putText(img_array, text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2, cv2.LINE_AA)

    # Show image with OCR box
    st.image(img_array, caption="📷 OCR Detected Image")

    # Extract text values
    v_list = [res[1] for res in results]
    cleaned_list = [re.sub(r'[^A-Za-z0-9]', '', val) for val in v_list]
    combined = ' '.join(cleaned_list)

    st.subheader("🔤 Combined Detected Text")
    st.code(combined)

    # Search in Open Food Facts
    with st.spinner("🔍 Searching Open Food Facts..."):
        search_results = search_open_food_facts(combined)

    if search_results:
        st.subheader("📦 Matched Products")

        cols = st.columns(2)
        for i, product in enumerate(search_results):
            with cols[i % 2]:
                with st.expander(f"Product {i+1}: {product.get('product_name', 'N/A')}"):
                    st.markdown(f"**Brand:** {product.get('brands', 'N/A')}")
                    st.markdown(f"**Categories:** {product.get('categories', 'N/A')}")
                    st.markdown(f"**Ingredients:** {product.get('ingredients_text', 'N/A')}")
                    nutriments = product.get('nutriments', {})
                    if nutriments:
                        st.markdown("**Nutrition Facts:**")
                        st.json(nutriments)
                    else:
                        st.markdown("_No nutrition data available._")
    else:
        st.warning("No matching products found.")
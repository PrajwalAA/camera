import streamlit as st
from PIL import Image, ImageFilter, ImageEnhance
import io
import datetime
import numpy as np
from cryptography.fernet import Fernet
import base64

# Streamlit page config
st.set_page_config(
    page_title="🔐 Encrypted Selfie App",
    page_icon="📷",
    layout="centered"
)

# ========== STYLE ==========
st.markdown("""
<style>
    .main { background-color: #f7f9fc; }
    .stButton button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stDownloadButton button {
        background-color: #00a8ff;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
    }
    h1 {
        color: #1a1a1a;
        text-align: center;
    }
    .encryption-box, .decryption-box {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .encryption-box { background-color: #e8f4fc; }
    .decryption-box { background-color: #f0e8fc; }
</style>
""", unsafe_allow_html=True)

# ========== FUNCTIONS ==========

# Generate encryption key
def generate_key():
    return Fernet.generate_key()

# Encrypt data
def encrypt_data(data, key):
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    return encrypted_data

# Decrypt data
def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    try:
        decrypted_data = f.decrypt(encrypted_data).decode()
        return decrypted_data
    except:
        return None

# Embed encrypted data into image
def embed_data_in_image(image, encrypted_data):
    binary_data = ''.join(format(byte, '08b') for byte in encrypted_data)
    delimiter = '1111111100000000'
    binary_data += delimiter

    img_array = np.array(image, dtype=np.uint8)
    flat_array = img_array.flatten().copy()  # ensure writable

    if len(binary_data) > flat_array.size:
        st.error("❌ Image is too small to hold encrypted data (including delimiter).")
        return None

    # Safe bit embedding using 0xFE instead of ~1
    for i, bit in enumerate(binary_data):
        if i >= len(flat_array):
            break
        flat_array[i] = (flat_array[i] & 0xFE) | int(bit)

    embedded_array = flat_array.reshape(img_array.shape)
    embedded_img = Image.fromarray(embedded_array.astype('uint8'), 'RGB')

    return embedded_img

# Extract encrypted data from image
def extract_data_from_image(image):
    if image.mode != 'RGB':
        image = image.convert('RGB')

    img_array = np.array(image, dtype=np.uint8)
    flat_array = img_array.flatten()

    binary_data = ''.join([str(pixel & 1) for pixel in flat_array])
    delimiter = '1111111100000000'
    delimiter_pos = binary_data.find(delimiter)

    if delimiter_pos == -1:
        return None

    binary_data = binary_data[:delimiter_pos]
    byte_data = bytearray()
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i+8]
        if len(byte) == 8:
            byte_data.append(int(byte, 2))

    return bytes(byte_data)

# ========== UI ==========

st.title("🔐 Encrypted Selfie App")
st.write("Take a selfie, embed secret encrypted info, and decrypt it later!")

tab1, tab2 = st.tabs(["📸 Capture & Encrypt", "🔓 Decrypt Image"])

# ---------- ENCRYPTION TAB ----------
with tab1:
    img_file = st.camera_input("Take a selfie")

    if img_file is not None:
        img = Image.open(img_file)
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Your Selfie")
            st.image(img, width="stretch")

        with col2:
            st.subheader("Filters")
            filter_option = st.selectbox(
                "Select a filter:",
                ["None", "Black & White", "Vintage", "Blur", "Sharp", "Warm", "Cool"]
            )

            if filter_option == "Black & White":
                filtered_img = img.convert("L").convert("RGB")
            elif filter_option == "Vintage":
                filtered_img = img.filter(ImageFilter.SMOOTH)
                filtered_img = ImageEnhance.Color(filtered_img).enhance(0.7)
                filtered_img = ImageEnhance.Brightness(filtered_img).enhance(0.9)
            elif filter_option == "Blur":
                filtered_img = img.filter(ImageFilter.GaussianBlur(radius=2))
            elif filter_option == "Sharp":
                filtered_img = img.filter(ImageFilter.SHARPEN)
            elif filter_option == "Warm":
                filtered_img = ImageEnhance.Color(img).enhance(1.5)
            elif filter_option == "Cool":
                filtered_img = ImageEnhance.Color(img).enhance(0.5)
            else:
                filtered_img = img.copy()

            st.image(filtered_img, width="stretch")

        st.markdown('<div class="encryption-box">', unsafe_allow_html=True)
        st.subheader("🔒 Add Encrypted Metadata")

        now = datetime.datetime.now()
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input("Date", now.date())
        with col2:
            selected_time = st.time_input("Time", now.time())

        custom_message = st.text_input("Custom Message", "This is my encrypted selfie!")

        key_option = st.radio("Encryption Key", ["Generate New Key", "Use Existing Key"])

        encryption_key = None
        if key_option == "Generate New Key":
            encryption_key = generate_key()
            st.code(encryption_key.decode(), language="text")
            st.info("💾 Save this key to decrypt later.")
        else:
            key_input = st.text_input("Enter Existing Key", type="password")
            try:
                encryption_key = key_input.encode()
                Fernet(encryption_key)
            except:
                st.error("❌ Invalid encryption key!")
                encryption_key = None

        if encryption_key:
            serialized_data = (
                f"Date: {selected_date.strftime('%Y-%m-%d')} | "
                f"Time: {selected_time.strftime('%H:%M:%S')} | "
                f"Message: {custom_message}"
            )
            encrypted_data = encrypt_data(serialized_data, encryption_key)
            encrypted_img = embed_data_in_image(filtered_img, encrypted_data)

            if encrypted_img:
                st.success("✅ Data encrypted and embedded successfully!")

                img_bytes = io.BytesIO()
                encrypted_img.save(img_bytes, format='PNG')
                st.download_button(
                    label="⬇️ Download Encrypted Selfie",
                    data=img_bytes.getvalue(),
                    file_name="encrypted_selfie.png",
                    mime="image/png"
                )

        st.markdown('</div>', unsafe_allow_html=True)

# ---------- DECRYPTION TAB ----------
with tab2:
    st.markdown('<div class="decryption-box">', unsafe_allow_html=True)
    st.subheader("🔓 Decrypt Image Metadata")

    uploaded_file = st.file_uploader("Upload encrypted image", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        encrypted_img = Image.open(uploaded_file)
        st.image(encrypted_img, caption="Uploaded Encrypted Image", width="stretch")

        key_input = st.text_input("Enter Encryption Key", type="password")

        if st.button("Decrypt"):
            if key_input:
                try:
                    encryption_key = key_input.encode()
                    Fernet(encryption_key)
                    extracted_data = extract_data_from_image(encrypted_img)

                    if extracted_data:
                        decrypted_data = decrypt_data(extracted_data, encryption_key)
                        if decrypted_data:
                            st.success("✅ Decryption Successful!")
                            st.code(decrypted_data, language="text")
                        else:
                            st.error("❌ Incorrect key or corrupted image.")
                    else:
                        st.error("⚠️ No encrypted data found in this image.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("Please enter an encryption key.")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("---")
st.markdown("<p style='text-align:center; color:#777;'>Made with ❤️ using Streamlit</p>", unsafe_allow_html=True)

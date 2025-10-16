import streamlit as st
from PIL import Image
import numpy as np
from cryptography.fernet import Fernet
import io

# -----------------------------------------------------------
# Generate or load encryption key
# -----------------------------------------------------------
@st.cache_resource
def get_key():
    return Fernet.generate_key()

fernet = Fernet(get_key())

# -----------------------------------------------------------
# Encryption / Decryption functions
# -----------------------------------------------------------
def encrypt_data(data: str) -> bytes:
    """Encrypts a text string using Fernet."""
    return fernet.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes) -> str:
    """Decrypts encrypted bytes back to string."""
    return fernet.decrypt(encrypted_data).decode()

# -----------------------------------------------------------
# Embed encrypted data into image
# -----------------------------------------------------------
def embed_data_in_image(image: Image.Image, encrypted_data: bytes):
    # Convert encrypted data to binary string + delimiter
    binary_data = ''.join(format(byte, '08b') for byte in encrypted_data)
    delimiter = '1111111100000000'
    binary_data += delimiter

    # Convert image to writable array
    img_array = np.array(image, dtype=np.uint8)
    flat_array = img_array.flatten().copy()

    # Capacity check
    if len(binary_data) > flat_array.size:
        st.error("❌ Image too small to hold encrypted data (including delimiter).")
        return None

    # Embed bits safely
    for i, bit in enumerate(binary_data):
        if i >= len(flat_array):
            break
        flat_array[i] = (flat_array[i] & ~1) | int(bit)

    # Reshape back to image
    embedded_array = flat_array.reshape(img_array.shape)
    embedded_img = Image.fromarray(embedded_array.astype('uint8'), 'RGB')
    return embedded_img

# -----------------------------------------------------------
# Extract hidden data from image
# -----------------------------------------------------------
def extract_data_from_image(image: Image.Image):
    img_array = np.array(image, dtype=np.uint8)
    flat_array = img_array.flatten()

    bits = [str(pixel & 1) for pixel in flat_array]
    binary_data = ''.join(bits)

    # Find delimiter
    delimiter = '1111111100000000'
    end_index = binary_data.find(delimiter)
    if end_index == -1:
        st.error("❌ No hidden data found or image corrupted.")
        return None

    binary_data = binary_data[:end_index]
    all_bytes = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    encrypted_bytes = bytes([int(b, 2) for b in all_bytes])
    return encrypted_bytes

# -----------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------
st.set_page_config(page_title="🔐 Encrypted Selfie App", layout="wide")
st.title("🔐 Encrypted Selfie App")
st.markdown("**Hide secret numbers or messages inside your images securely!**")

tab1, tab2 = st.tabs(["📤 Encrypt & Hide", "📥 Extract & Decrypt"])

# ----------------- Tab 1: Embed -----------------
with tab1:
    uploaded_image = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])
    secret_message = st.text_input("Enter your secret message or number:")
    if uploaded_image and secret_message:
        image = Image.open(uploaded_image).convert("RGB")
        st.image(image, caption="Original Image", width=300)

        if st.button("Encrypt & Embed"):
            encrypted_data = encrypt_data(secret_message)
            encrypted_img = embed_data_in_image(image, encrypted_data)
            if encrypted_img:
                st.success("✅ Secret embedded successfully!")
                st.image(encrypted_img, caption="Encrypted Image", width=300)

                # Download button
                buf = io.BytesIO()
                encrypted_img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                st.download_button(
                    label="⬇️ Download Encrypted Image",
                    data=byte_im,
                    file_name="encrypted_image.png",
                    mime="image/png"
                )

# ----------------- Tab 2: Extract -----------------
with tab2:
    uploaded_encrypted_image = st.file_uploader("Upload Encrypted Image", type=["png", "jpg", "jpeg"])
    if uploaded_encrypted_image:
        enc_image = Image.open(uploaded_encrypted_image).convert("RGB")
        st.image(enc_image, caption="Encrypted Image", width=300)

        if st.button("Extract & Decrypt"):
            encrypted_bytes = extract_data_from_image(enc_image)
            if encrypted_bytes:
                try:
                    secret_text = decrypt_data(encrypted_bytes)
                    st.success(f"✅ Decrypted Message: {secret_text}")
                except Exception:
                    st.error("❌ Failed to decrypt — wrong image or corrupted data.")

st.markdown("---")
st.caption("Made with ❤️ using Streamlit, PIL, and Cryptography")

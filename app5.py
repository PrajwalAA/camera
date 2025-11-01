import streamlit as st
from PIL import Image, ImageFilter, ImageEnhance
import io
import datetime
import numpy as np
from cryptography.fernet import Fernet
import base64
import hashlib
import string
import random
import streamlit.components.v1 as components

# Streamlit page config (should be at top)
st.set_page_config(
    page_title="🔐 Encrypted Selfie App",
    page_icon="📷",
    layout="centered"
)

# ========== STYLE ==========
st.markdown(
    """
<style>
    .main { background-color: #f7f9fc; }
    .stButton button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    .stDownloadButton button {
        background-color: #00a8ff;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    h1 {
        color: #1a1a1a;
        text-align: center;
        padding-bottom: 10px;
    }
    .encryption-box, .decryption-box {
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .encryption-box { border-left: 5px solid #00a8ff; background-color: #e8f4fc; }
    .decryption-box { border-left: 5px solid #ff4b4b; background-color: #f0e8fc; }
    .camera-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 15px;
    }
    .camera-controls {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }
    .camera-btn {
        padding: 8px 16px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    .camera-btn.primary {
        background-color: #00a8ff;
        color: white;
    }
    .camera-btn.secondary {
        background-color: #f0f0f0;
        color: #333;
    }
    .camera-btn:hover {
        opacity: 0.9;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ========== KEY/PASSCODE FUNCTIONS ==========

def generate_memorable_passcode():
    letters = ''.join(random.choice(string.ascii_letters) for _ in range(3))
    numbers = ''.join(random.choice(string.digits) for _ in range(3))
    passcode_list = list(letters + numbers)
    random.shuffle(passcode_list)
    return "".join(passcode_list)

def derive_fernet_key(passcode_str: str) -> bytes:
    # NOTE: for a production app use a proper KDF (PBKDF2/HKDF) with random salt stored alongside ciphertext.
    salt = b"encrypted_selfie_app_salt_v1"
    hashed = hashlib.sha256(salt + passcode_str.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(hashed)  # returns bytes
    return fernet_key

def get_passcode_and_key():
    passcode = generate_memorable_passcode()
    fernet_key = derive_fernet_key(passcode)
    return passcode, fernet_key

# ========== ENCRYPTION/DECRYPTION FUNCTIONS ==========

def encrypt_data(data: str, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes, key: bytes):
    f = Fernet(key)
    try:
        return f.decrypt(encrypted_data).decode()
    except Exception:
        return None

# ========== LSB STEGANOGRAPHY ==========

def embed_data_in_image(image: Image.Image, encrypted_data: bytes):
    if image.mode != "RGB":
        image = image.convert("RGB")

    # convert bytes to bit string
    binary_data = "".join(format(byte, "08b") for byte in encrypted_data)
    delimiter = "1111111100000000"  # 16-bit marker
    binary_data += delimiter

    img_array = np.array(image, dtype=np.uint8)
    flat_array = img_array.flatten().copy()  # flatten and ensure writable

    # capacity is number of available LSBs (one per channel byte)
    capacity_bits = flat_array.size
    if len(binary_data) > capacity_bits:
        st.error(
            f"❌ Image is too small (Capacity: {capacity_bits} bits) to hold encrypted data ({len(binary_data)} bits)."
        )
        return None

    for i, bit in enumerate(binary_data):
        # clear LSB then set to desired bit
        flat_array[i] = (flat_array[i] & 0xFE) | int(bit)

    embedded_array = flat_array.reshape(img_array.shape)
    embedded_img = Image.fromarray(embedded_array.astype("uint8"), "RGB")
    return embedded_img

def extract_data_from_image(image: Image.Image):
    if image.mode != "RGB":
        image = image.convert("RGB")

    img_array = np.array(image, dtype=np.uint8)
    flat_array = img_array.flatten()
    binary_str = "".join(str(byte & 1) for byte in flat_array)
    delimiter = "1111111100000000"
    pos = binary_str.find(delimiter)

    if pos == -1:
        return None

    binary_str = binary_str[:pos]
    byte_arr = bytearray()
    for i in range(0, len(binary_str), 8):
        byte = binary_str[i:i+8]
        if len(byte) == 8:
            byte_arr.append(int(byte, 2))

    return bytes(byte_arr)

# ========== CUSTOM CAMERA COMPONENT ==========
# Note: the JS component posts a value back to Streamlit via the standard
# 'streamlit:setComponentValue' message. components.html returns that value.
def camera_component():
    component_value = components.html(
        """
        <div class="camera-container">
            <video id="video" width="100%" autoplay playsinline></video>
            <div class="camera-controls">
                <button id="front-camera" class="camera-btn secondary">Front Camera</button>
                <button id="back-camera" class="camera-btn secondary">Back Camera</button>
                <button id="capture" class="camera-btn primary">Capture Photo</button>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
        </div>

        <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const context = canvas.getContext('2d');
        const frontCameraBtn = document.getElementById('front-camera');
        const backCameraBtn = document.getElementById('back-camera');
        const captureBtn = document.getElementById('capture');

        let currentStream = null;
        let facingMode = 'user';

        function startCamera() {
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
            }
            const constraints = { video: { facingMode: facingMode, width: { ideal: 1280 }, height: { ideal: 720 } } };
            navigator.mediaDevices.getUserMedia(constraints)
                .then(stream => {
                    currentStream = stream;
                    video.srcObject = stream;
                    if (facingMode === 'user') {
                        frontCameraBtn.classList.remove('secondary');
                        frontCameraBtn.classList.add('primary');
                        backCameraBtn.classList.remove('primary');
                        backCameraBtn.classList.add('secondary');
                    } else {
                        backCameraBtn.classList.remove('secondary');
                        backCameraBtn.classList.add('primary');
                        frontCameraBtn.classList.remove('primary');
                        frontCameraBtn.classList.add('secondary');
                    }
                })
                .catch(err => {
                    console.error("Error accessing camera: ", err);
                    alert("Could not access the camera. Please ensure you have granted camera permissions.");
                });
        }

        startCamera();

        frontCameraBtn.addEventListener('click', () => {
            facingMode = 'user';
            startCamera();
        });

        backCameraBtn.addEventListener('click', () => {
            facingMode = 'environment';
            startCamera();
        });

        captureBtn.addEventListener('click', () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const dataURL = canvas.toDataURL('image/png');
            window.parent.postMessage({ type: 'streamlit:setComponentValue', value: { image: dataURL } }, '*');
        });
        </script>
        """,
        height=520,
    )

    if component_value and isinstance(component_value, dict) and "image" in component_value:
        header, encoded = component_value["image"].split(",", 1)
        data = base64.b64decode(encoded)
        return Image.open(io.BytesIO(data))
    return None

# ========== UI ==========

st.title("🔐 Encrypted Selfie App")
st.write("Take a selfie, embed secret encrypted info, and decrypt it later using a simple 6-character passcode!")

tab1, tab2 = st.tabs(["📸 Capture & Encrypt", "🔓 Decrypt Image"])

# ---------- ENCRYPTION TAB ----------
with tab1:
    st.subheader("Capture Your Selfie")

    camera_option = st.radio("Camera Input", ["Use Custom Camera (Front/Back Switch)", "Use Default Camera"], index=0)

    img = None
    if camera_option == "Use Custom Camera (Front/Back Switch)":
        st.info("📷 Use the buttons below to switch between front and back cameras")
        img = camera_component()
        if img is None:
            st.warning("Custom camera not available in this browser/environment. Try 'Use Default Camera' instead.")
    else:
        img_file = st.camera_input("Take a selfie")
        if img_file is not None:
            img = Image.open(img_file)

    if img is not None:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Your Selfie")
            st.image(img, use_column_width=True)

        with col2:
            st.subheader("Filters")
            filter_option = st.selectbox(
                "Select a filter:",
                ["None", "Black & White", "Vintage", "Blur", "Sharp", "Warm", "Cool"],
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

            st.image(filtered_img, use_column_width=True)

        st.markdown('<div class="encryption-box">', unsafe_allow_html=True)
        st.subheader("🔒 Add Encrypted Metadata")

        now = datetime.datetime.now()
        col_date, col_time = st.columns(2)
        with col_date:
            selected_date = st.date_input("Date", now.date())
        with col_time:
            selected_time = st.time_input("Time", now.time())

        custom_message = st.text_area("Custom Secret Message", "This is my encrypted selfie! Remember this moment.", height=100)

        key_option = st.radio("Encryption Passcode", ["Generate New Passcode", "Use Existing Passcode"], index=0)

        user_passcode = None
        fernet_key = None

        if key_option == "Generate New Passcode":
            passcode, derived_key = get_passcode_and_key()
            st.code(passcode, language="text")
            st.info("🔑 **This is your 6-character passcode.** You need this exact string to decrypt later.")
            user_passcode = passcode
            fernet_key = derived_key
        else:
            passcode_input = st.text_input("Enter Existing Passcode (6 characters)", type="password", max_chars=6)
            if passcode_input and len(passcode_input) == 6:
                try:
                    user_passcode = passcode_input
                    fernet_key = derive_fernet_key(user_passcode)
                    # test key by creating Fernet object (no encryption required here)
                    _ = Fernet(fernet_key)
                except Exception:
                    st.error("❌ Invalid Passcode format!")
                    fernet_key = None
            elif passcode_input:
                st.warning("Passcode must be exactly 6 characters.")

        if fernet_key:
            serialized_data = (
                f"Date: {selected_date.strftime('%Y-%m-%d')} | "
                f"Time: {selected_time.strftime('%H:%M:%S')} | "
                f"Message: {custom_message}"
            )

            # Encrypt + embed
            encrypted_data = encrypt_data(serialized_data, fernet_key)
            encrypted_img = embed_data_in_image(filtered_img, encrypted_data)

            if encrypted_img:
                st.success("✅ Data encrypted and embedded successfully!")
                img_bytes = io.BytesIO()
                encrypted_img.save(img_bytes, format="PNG")
                st.download_button(
                    label="⬇️ Download Encrypted Selfie (.png)",
                    data=img_bytes.getvalue(),
                    file_name="encrypted_secret_selfie.png",
                    mime="image/png",
                )

        st.markdown("</div>", unsafe_allow_html=True)

# ---------- DECRYPTION TAB ----------
with tab2:
    st.markdown('<div class="decryption-box">', unsafe_allow_html=True)
    st.subheader("🔓 Decrypt Image Metadata")

    uploaded_file = st.file_uploader("Upload encrypted image (.png recommended)", type=["png", "jpg", "jpeg"])

    encrypted_img = None
    if uploaded_file is not None:
        try:
            encrypted_img = Image.open(uploaded_file)
            st.image(encrypted_img, caption="Uploaded Encrypted Image", use_column_width=True)
        except Exception as e:
            st.error(f"❌ Could not open image: {e}")
            encrypted_img = None

    if encrypted_img is not None:
        passcode_input = st.text_input("Enter 6-character Passcode", key="decryption_key_input", type="password", max_chars=6)
        if st.button("Decrypt"):
            if passcode_input and len(passcode_input) == 6:
                try:
                    decryption_fernet_key = derive_fernet_key(passcode_input)
                    extracted_data = extract_data_from_image(encrypted_img)
                    if extracted_data:
                        decrypted_data = decrypt_data(extracted_data, decryption_fernet_key)
                        if decrypted_data:
                            st.success("✅ Decryption Successful! Secret Message Revealed:")
                            st.code(decrypted_data, language="text")
                        else:
                            st.error("❌ Incorrect passcode or corrupted encrypted data.")
                    else:
                        st.error("⚠️ No encrypted data (or delimiter) found in this image.")
                except Exception as e:
                    st.error(f"❌ An internal error occurred: {e}")
            elif passcode_input:
                st.warning("Passcode must be exactly 6 characters.")
            else:
                st.warning("Please enter your 6-character passcode.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("---")
st.markdown("<p style='text-align:center; color:#777;'>Made with ❤️ using Streamlit, Fernet, and LSB Steganography</p>", unsafe_allow_html=True)

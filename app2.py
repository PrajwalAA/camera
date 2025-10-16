import streamlit as st
from PIL import Image, ImageFilter, ImageEnhance
import io
import datetime
import numpy as np
from cryptography.fernet import Fernet
import base64
import os

# Set page config
st.set_page_config(
    page_title="Encrypted Selfie App",
    page_icon="🔐",
    layout="centered"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #f0f2f6;
    }
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
    .filter-label {
        font-size: 1.2em;
        font-weight: bold;
        margin-top: 20px;
    }
    .encryption-box {
        background-color: #e8f4fc;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .decryption-box {
        background-color: #f0e8fc;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

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

# Embed encrypted data in image
def embed_data_in_image(image, encrypted_data):
    # Convert encrypted data to binary
    binary_data = ''.join(format(byte, '08b') for byte in encrypted_data)
    
    # Add a delimiter to mark the end of data
    binary_data += '1111111100000000'  # Custom delimiter
    
    # Ensure image is in RGB format
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Get image dimensions
    width, height = image.size
    
    # Check if image is large enough to hold the data
    max_data_size = width * height * 3  # 3 channels per pixel
    if len(binary_data) > max_data_size:
        st.error("Image is too small to hold the encrypted data. Please use a larger image or shorter message.")
        return None
    
    # Convert image to numpy array
    img_array = np.array(image)
    
    # Flatten the array
    flat_array = img_array.flatten()
    
    # Embed the binary data in the LSB of each pixel channel
    for i in range(len(binary_data)):
        # Clear the LSB and set it to the binary data bit
        flat_array[i] = (flat_array[i] & ~1) | int(binary_data[i])
    
    # Reshape the array back to original dimensions
    modified_array = flat_array.reshape(img_array.shape)
    
    # Convert back to PIL Image
    modified_image = Image.fromarray(modified_array)
    
    return modified_image

# Extract encrypted data from image
def extract_data_from_image(image):
    # Ensure image is in RGB format
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Convert image to numpy array
    img_array = np.array(image)
    
    # Flatten the array
    flat_array = img_array.flatten()
    
    # Extract LSBs
    binary_data = ''.join([str(pixel & 1) for pixel in flat_array])
    
    # Find the delimiter
    delimiter = '1111111100000000'
    delimiter_pos = binary_data.find(delimiter)
    
    if delimiter_pos == -1:
        return None
    
    # Extract the binary data before the delimiter
    binary_data = binary_data[:delimiter_pos]
    
    # Convert binary data to bytes
    byte_data = bytearray()
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i+8]
        if len(byte) == 8:  # Ensure we have a full byte
            byte_data.append(int(byte, 2))
    
    return bytes(byte_data)

# App title and description
st.title("🔐 Encrypted Selfie App")
st.write("Take a selfie, add encrypted metadata, and decrypt information later!")

# Tabs for different functionalities
tab1, tab2 = st.tabs(["Capture & Encrypt", "Decrypt Image"])

with tab1:
    # Camera input
    img_file = st.camera_input("Take a selfie")
    
    if img_file is not None:
        # Convert to PIL Image
        img = Image.open(img_file)
        
        # Create columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Your Selfie")
            st.image(img, use_column_width=True)
        
        with col2:
            st.subheader("Filters")
            
            # Filter options
            filter_option = st.selectbox(
                "Select a filter:",
                ["None", "Black & White", "Vintage", "Blur", "Sharp", "Warm", "Cool"]
            )
            
            # Apply selected filter
            if filter_option == "Black & White":
                filtered_img = img.convert("L")
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
            
            # Display filtered image
            st.image(filtered_img, use_column_width=True)
        
        # Encryption section
        st.markdown('<div class="encryption-box">', unsafe_allow_html=True)
        st.subheader("🔒 Add Encrypted Metadata")
        
        # Get current date and time
        now = datetime.datetime.now()
        
        # Date and time inputs
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input("Date", now.date())
        with col2:
            selected_time = st.time_input("Time", now.time())
        
        # Custom message
        custom_message = st.text_input("Custom Message", "This is my encrypted selfie!")
        
        # Generate or input encryption key
        key_option = st.radio("Encryption Key", ["Generate New Key", "Use Existing Key"])
        
        if key_option == "Generate New Key":
            encryption_key = generate_key()
            st.code(encryption_key.decode(), language="text")
            st.info("Save this key for decryption later!")
        else:
            key_input = st.text_input("Enter Encryption Key", type="password")
            try:
                encryption_key = key_input.encode()
                # Test if key is valid
                Fernet(encryption_key)
            except:
                st.error("Invalid encryption key!")
                encryption_key = None
        
        # Create serialized data
        if encryption_key:
            serialized_data = f"Date: {selected_date.strftime('%Y-%m-%d')} | Time: {selected_time.strftime('%H:%M:%S')} | Message: {custom_message}"
            
            # Encrypt the data
            encrypted_data = encrypt_data(serialized_data, encryption_key)
            
            # Embed encrypted data in image
            encrypted_img = embed_data_in_image(filtered_img, encrypted_data)
            
            if encrypted_img:
                st.success("Data encrypted and embedded successfully!")
                
                # Create download button for encrypted image
                img_byte_arr = io.BytesIO()
                encrypted_img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                
                st.download_button(
                    label="Download Encrypted Selfie",
                    data=img_byte_arr,
                    file_name="encrypted_selfie.png",
                    mime="image/png",
                    key="download_encrypted_button"
                )
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="decryption-box">', unsafe_allow_html=True)
    st.subheader("🔓 Decrypt Image Metadata")
    
    # File uploader for encrypted image
    uploaded_file = st.file_uploader("Upload an encrypted image", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        # Convert to PIL Image
        encrypted_img = Image.open(uploaded_file)
        
        # Display the encrypted image
        st.image(encrypted_img, caption="Uploaded Encrypted Image", use_column_width=True)
        
        # Input for encryption key
        key_input = st.text_input("Enter Encryption Key", type="password")
        
        if st.button("Decrypt"):
            if key_input:
                try:
                    encryption_key = key_input.encode()
                    # Test if key is valid
                    Fernet(encryption_key)
                    
                    # Extract encrypted data from image
                    extracted_data = extract_data_from_image(encrypted_img)
                    
                    if extracted_data:
                        # Decrypt the data
                        decrypted_data = decrypt_data(extracted_data, encryption_key)
                        
                        if decrypted_data:
                            st.success("Decryption successful!")
                            st.subheader("Decrypted Metadata:")
                            st.code(decrypted_data, language="text")
                        else:
                            st.error("Failed to decrypt data. Incorrect key or corrupted image.")
                    else:
                        st.error("No encrypted data found in the image.")
                except:
                    st.error("Invalid encryption key!")
            else:
                st.warning("Please enter an encryption key.")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #666;'>Made with ❤️ using Streamlit</p>", unsafe_allow_html=True)

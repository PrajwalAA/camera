import streamlit as st
from PIL import Image, ImageFilter, ImageEnhance
import io

# Set page config
st.set_page_config(
    page_title="Cool Selfie App",
    page_icon="📸",
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
</style>
""", unsafe_allow_html=True)

# App title and description
st.title("📸 Cool Selfie App")
st.write("Take a selfie, apply cool filters, and download your masterpiece!")

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
        
        # Create download button
        img_byte_arr = io.BytesIO()
        filtered_img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        st.download_button(
            label="Download Selfie",
            data=img_byte_arr,
            file_name="cool_selfie.png",
            mime="image/png",
            key="download_button"
        )
        
        # Success message
        st.success("Your selfie is ready! Click download to save it.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #666;'>Made with ❤️ using Streamlit</p>", unsafe_allow_html=True)

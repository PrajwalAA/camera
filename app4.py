import streamlit as st
from PIL import Image, ImageFilter, ImageEnhance
import io
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode

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
    /* Style for filter buttons in the live feed section */
    .stButton > button {
        width: 100%;
        padding: 8px 15px;
        border-radius: 20px;
        background-color: #e0e0e0;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #1a1a1a;
    }
    /* Active state for the buttons (using key-based CSS is hard, so this is a general style) */
    .stButton > button:hover {
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# App title and description
st.title("📸 Cool Selfie App")
st.write("Take a selfie, apply cool filters, and download your masterpiece!")

# Initialize session state for the selected live filter
if 'live_filter_type' not in st.session_state:
    st.session_state['live_filter_type'] = "None"

# Define the video transformer class for real-time filters
class VideoFilter(VideoTransformerBase):
    def __init__(self, filter_type):
        # Pass the filter type via the constructor
        self.filter_type = filter_type
    
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # Apply mirror effect (like a selfie camera)
        img = cv2.flip(img, 1)
        
        # Apply selected filter
        if self.filter_type == "Black & White":
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif self.filter_type == "Vintage":
            # Sepia effect
            sepia_kernel = np.array([[0.272, 0.534, 0.131],
                                     [0.349, 0.686, 0.168],
                                     [0.393, 0.769, 0.189]])
            img = cv2.transform(img, sepia_kernel)
            img = np.clip(img, 0, 255).astype(np.uint8)
            # Add some noise for vintage look
            noise = np.random.normal(0, 5, img.shape).astype(np.uint8) # Reduced noise
            img = cv2.add(img, noise)
        elif self.filter_type == "Blur":
            img = cv2.GaussianBlur(img, (15, 15), 0)
        elif self.filter_type == "Sharp":
            kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
            img = cv2.filter2D(img, -1, kernel)
        elif self.filter_type == "Warm":
            # Increase red and yellow tones
            img[:, :, 2] = np.clip(img[:, :, 2] * 1.2, 0, 255)  # Red channel
            img[:, :, 1] = np.clip(img[:, :, 1] * 1.1, 0, 255)  # Green channel
        elif self.filter_type == "Cool":
            # Increase blue tones
            img[:, :, 0] = np.clip(img[:, :, 0] * 1.3, 0, 255)  # Blue channel
            img[:, :, 2] = np.clip(img[:, :, 2] * 0.8, 0, 255)  # Reduce red
        elif self.filter_type == "Edge Detection":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            img = cv2.addWeighted(img, 0.7, edges, 0.3, 0)
        elif self.filter_type == "Cartoon":
            # Apply bilateral filter multiple times
            for _ in range(3):
                img = cv2.bilateralFilter(img, 9, 200, 200)
            # Create edge mask
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                             cv2.THRESH_BINARY, 9, 9)
            edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            # Combine
            img = cv2.bitwise_and(img, edges)
            
        return img

# ---
## Live Camera Feed with Real-time Filters
st.subheader("Live Camera Feed")
st.write(f"**Current Live Filter:** **{st.session_state['live_filter_type']}**")

# Function to update the session state with the new filter
def update_live_filter(filter_name):
    st.session_state['live_filter_type'] = filter_name

# Create a filter selection UI
filter_options = ["None", "Black & White", "Vintage", "Blur", "Sharp", "Warm", "Cool", "Edge Detection", "Cartoon"]

# Create filter buttons using st.columns to lay them out
cols = st.columns(3)

# Use Streamlit's on_click callback to update the session state correctly
for i, filter_name in enumerate(filter_options):
    col = cols[i % 3]
    button_style = "filter-button active" if filter_name == st.session_state['live_filter_type'] else "filter-button"
    
    col.button(
        filter_name, 
        key=f"live_filter_button_{i}", 
        on_click=update_live_filter, 
        args=(filter_name,)
    )

# Use a lambda function to dynamically create the VideoFilter instance with the current filter type
webrtc_streamer(
    key="live_filter",
    mode=WebRtcMode.SENDRECV,
    video_transformer_factory=lambda: VideoFilter(st.session_state['live_filter_type']),
    media_stream_constraints={"video": True, "audio": False},
    async_transform=True,
)

# ---
## Still Photo Editor
st.subheader("Take a Still Photo")
img_file = st.camera_input("Capture a photo")

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
            filter_options, # Reuse the list of filters
            key="still_filter_select"
        )
        
        # Apply selected filter
        if filter_option == "Black & White":
            filtered_img = img.convert("L").convert("RGB")
        elif filter_option == "Vintage":
            # Enhanced PIL Vintage effect
            filtered_img = img.copy()
            filtered_img = filtered_img.filter(ImageFilter.SMOOTH)
            filtered_img = ImageEnhance.Color(filtered_img).enhance(0.7)
            filtered_img = ImageEnhance.Brightness(filtered_img).enhance(0.9)
            
            # Sepia tone logic
            pixels = filtered_img.load()
            for i in range(filtered_img.size[0]):
                for j in range(filtered_img.size[1]):
                    r, g, b = filtered_img.getpixel((i, j))
                    tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                    tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                    tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                    pixels[i, j] = (min(255, tr), min(255, tg), min(255, tb))
        elif filter_option == "Blur":
            filtered_img = img.filter(ImageFilter.GaussianBlur(radius=2))
        elif filter_option == "Sharp":
            filtered_img = img.filter(ImageFilter.SHARPEN)
        elif filter_option == "Warm":
            # Apply color enhancement for warmth
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            cv_img[:, :, 2] = np.clip(cv_img[:, :, 2].astype(float) * 1.2, 0, 255).astype(np.uint8)
            cv_img[:, :, 1] = np.clip(cv_img[:, :, 1].astype(float) * 1.1, 0, 255).astype(np.uint8)
            filtered_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
        elif filter_option == "Cool":
            # Apply color enhancement for coolness
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            cv_img[:, :, 0] = np.clip(cv_img[:, :, 0].astype(float) * 1.3, 0, 255).astype(np.uint8)
            cv_img[:, :, 2] = np.clip(cv_img[:, :, 2].astype(float) * 0.8, 0, 255).astype(np.uint8)
            filtered_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
        elif filter_option == "Edge Detection":
            # Use OpenCV for consistency with live feed
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            # Combine
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            cv_img_edges = cv2.addWeighted(cv_img, 0.7, edges_bgr, 0.3, 0)
            filtered_img = Image.fromarray(cv2.cvtColor(cv_img_edges, cv2.COLOR_BGR2RGB))
        elif filter_option == "Cartoon":
            # Use OpenCV for consistency with live feed
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            # Apply bilateral filter
            for _ in range(3):
                cv_img = cv2.bilateralFilter(cv_img, 9, 200, 200)
            # Create edge mask
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                             cv2.THRESH_BINARY, 9, 9)
            edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            # Combine
            cv_img = cv2.bitwise_and(cv_img, edges)
            # Convert back to PIL
            filtered_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
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

# ---
## Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #666;'>Made with ❤️ using Streamlit</p>", unsafe_allow_html=True)

import streamlit as st
from huggingface_hub import InferenceClient
import io
from PIL import Image
import time

# Set page configuration
st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(to right, #6a11cb, #2575fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
    }
    .generate-btn {
        background: linear-gradient(to right, #6a11cb, #2575fc);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 0.5rem;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .generate-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .image-container {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }
    .download-btn {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 0.5rem;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .download-btn:hover {
        background-color: #45a049;
    }
    .footer {
        text-align: center;
        color: #888;
        margin-top: 3rem;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("<h1 class='main-header'>AI Image Generator</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Create stunning images from text descriptions using Stable Diffusion XL</p>", unsafe_allow_html=True)

# Sidebar with instructions
with st.sidebar:
    st.header("How to use")
    st.markdown("""
    1. Enter a detailed description of the image you want to create
    2. Click the "Generate Image" button
    3. Wait for the AI to create your image
    4. Download your image when ready
    """)
    
    st.header("Tips for better results")
    st.markdown("""
    - Be specific and detailed in your descriptions
    - Include artistic styles (e.g., "oil painting", "photorealistic")
    - Specify lighting and composition
    - Try different perspectives (e.g., "close-up", "aerial view")
    """)

# Main content area
prompt = st.text_input(
    "Describe the image you want to create:",
    placeholder="Astronaut riding a horse on Mars, photorealistic, 8k",
    max_chars=200
)

# Initialize session state for image
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None

# Generate button
if st.button("Generate Image", key="generate", help="Click to generate the image"):
    if not prompt:
        st.error("Please enter a description for the image")
    else:
        with st.spinner("Generating your image... This may take 30-60 seconds."):
            try:
                # Initialize the client
                client = InferenceClient(
                    model="stabilityai/stable-diffusion-xl-base-1.0",
                    token="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"
                )
                
                # Generate the image
                image = client.text_to_image(prompt)
                
                # Store in session state
                st.session_state.generated_image = image
                
                # Success message
                st.success("Image generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating image: {str(e)}")
                st.session_state.generated_image = None

# Display generated image
if st.session_state.generated_image is not None:
    st.markdown("<div class='image-container'>", unsafe_allow_html=True)
    st.image(st.session_state.generated_image, caption="Generated Image", use_column_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Prepare image for download
    img_byte_arr = io.BytesIO()
    st.session_state.generated_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Download button
    st.download_button(
        label="Download Image",
        data=img_byte_arr,
        file_name=f"generated_image_{int(time.time())}.png",
        mime="image/png",
        key="download",
        help="Click to download the generated image"
    )

# Footer
st.markdown("<p class='footer'>Created with Stable Diffusion XL • Powered by Hugging Face</p>", unsafe_allow_html=True)

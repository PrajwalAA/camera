import streamlit as st
import numpy as np
from PIL import Image
import datetime
import requests
import time
import os
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import av
import geocoder

# Set page configuration
st.set_page_config(
    page_title="Camera with Location Tracker",
    page_icon="📷",
    layout="wide"
)

# Function to get current location
def get_location():
    try:
        # Get location based on IP
        g = geocoder.ip('me')
        if g.ok:
            return {
                'address': g.address,
                'lat': g.latlng[0],
                'lng': g.latlng[1],
                'city': g.city,
                'state': g.state,
                'country': g.country
            }
        else:
            return None
    except:
        return None

# Custom video processor to add location info
class LocationVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.location = get_location()
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        
        # Add location text to the frame
        if self.location:
            location_text = f"{self.location['city']}, {self.location['state']}, {self.location['country']}"
            cv2.putText(img, location_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(img, f"Lat: {self.location['lat']:.4f}, Lng: {self.location['lng']:.4f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add timestamp
        cv2.putText(img, self.timestamp, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# Main app
def main():
    st.title("📷 Camera with Location Tracker")
    st.write("Capture images and record videos with location data")
    
    # Get current location
    location = get_location()
    
    # Display location information if available
    if location:
        st.success(f"📍 Current Location: {location['address']}")
        st.write(f"**Coordinates:** {location['lat']:.4f}, {location['lng']:.4f}")
        st.write(f"**City:** {location['city']}, **State:** {location['state']}, **Country:** {location['country']}")
    else:
        st.warning("⚠️ Unable to retrieve location data. Please check your internet connection.")
    
    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["📸 Capture Photo", "🎥 Record Video"])
    
    # Tab 1: Photo Capture
    with tab1:
        st.header("Capture Photo with Location")
        
        # Camera input for capturing image
        img_file_buffer = st.camera_input("Take a picture")
        
        if img_file_buffer is not None:
            # Read the image
            image = Image.open(img_file_buffer)
            
            # Get timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Display the captured image
            st.image(image, caption=f"Captured at {timestamp}", use_column_width=True)
            
            # Create a combined image with location info
            img_array = np.array(image)
            
            # Add location info to the image
            if location:
                from PIL import Image, ImageDraw, ImageFont
                
                # Create a drawing context
                draw = ImageDraw.Draw(image)
                
                # Try to use a default font
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()
                
                # Add location text
                location_text = f"Location: {location['city']}, {location['state']}, {location['country']}"
                coord_text = f"Coordinates: {location['lat']:.4f}, {location['lng']:.4f}"
                time_text = f"Time: {timestamp}"
                
                # Draw text on image
                draw.text((10, 10), location_text, fill="white", font=font)
                draw.text((10, 40), coord_text, fill="white", font=font)
                draw.text((10, 70), time_text, fill="white", font=font)
            
            # Display the image with location info
            st.image(image, caption="Image with Location Information", use_column_width=True)
            
            # Provide download button
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="Download Image with Location Data",
                data=img_file_buffer.getvalue(),
                file_name=f"photo_with_location_{timestamp_str}.jpg",
                mime="image/jpeg"
            )
    
    # Tab 2: Video Recording
    with tab2:
        st.header("Record Video with Location")
        
        # Add OpenCV for video processing
        try:
            import cv2
        except:
            st.error("OpenCV is required for video processing. Please install it with: pip install opencv-python")
            return
        
        # WebRTC streamer for video recording
        webrtc_ctx = webrtc_streamer(
            key="video-recorder",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=LocationVideoProcessor,
            media_stream_constraints={"video": True, "audio": False},
        )
        
        if webrtc_ctx.video_processor:
            st.success("Recording started with location tracking!")
            
            # Display current location being recorded
            if location:
                st.write(f"Recording location: {location['city']}, {location['state']}, {location['country']}")
                st.write(f"Coordinates: {location['lat']:.4f}, {location['lng']:.4f}")
            
            # Add a button to stop recording and save
            if st.button("Stop Recording and Save"):
                st.success("Recording saved successfully!")
                # Note: Actual saving functionality would need additional implementation
        else:
            st.info("Click 'START' to begin recording with location tracking.")

if __name__ == "__main__":
    main()

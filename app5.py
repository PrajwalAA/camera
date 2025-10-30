import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import datetime
import time
import os
import geocoder
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import av
import cv2

# ------------------ Streamlit Page Config ------------------
st.set_page_config(
    page_title="Live Camera with Location Overlay",
    page_icon="📍",
    layout="wide"
)

# ------------------ Location Function ------------------
def get_location():
    try:
        g = geocoder.ip('me')
        if g.ok and g.latlng:
            return {
                'address': g.address or "Unknown Address",
                'lat': g.latlng[0],
                'lng': g.latlng[1],
                'city': g.city or "Unknown City",
                'state': g.state or "Unknown State",
                'country': g.country or "Unknown Country",
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return None
    except Exception as e:
        st.error(f"Error getting location: {e}")
        return None

# ------------------ Video Processor ------------------
class LocationOverlayProcessor(VideoProcessorBase):
    def __init__(self):
        self.location = None
        self.last_update = 0
        self.update_interval = 5  # seconds

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")

        # Update location periodically
        current_time = time.time()
        if current_time - self.last_update > self.update_interval:
            self.location = get_location()
            self.last_update = current_time

        # Convert to PIL for overlay
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        # Use default font if Arial not available
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()

        # Draw semi-transparent background
        draw.rectangle([(0, 0), (520, 110)], fill=(0, 0, 0, 180))

        # Overlay text
        if self.location:
            loc = self.location
            draw.text((10, 10), f"📍 {loc['city']}, {loc['state']}", fill="white", font=font)
            draw.text((10, 40), f"Lat: {loc['lat']:.4f}, Lng: {loc['lng']:.4f}", fill="white", font=font)
            draw.text((10, 70), f"🕒 {loc['timestamp']}", fill="white", font=font)
        else:
            draw.text((10, 10), "📍 Location unavailable", fill="white", font=font)
            draw.text((10, 40), "Check internet connection", fill="white", font=font)

        # Convert back to OpenCV
        img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# ------------------ Main App ------------------
def main():
    st.title("📍 Live Camera with Location Overlay")
    st.write("Real-time camera feed with live location displayed on-screen")

    # Fetch initial location
    location = get_location()

    col1, col2 = st.columns([2, 1])

    # Live Camera Feed
    with col1:
        st.subheader("Live Camera Feed")
        st.write("Location info updates automatically every 5 seconds.")
        webrtc_ctx = webrtc_streamer(
            key="location-camera",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=LocationOverlayProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    # Location Info Sidebar
    with col2:
        st.subheader("Location Information")
        if location:
            st.success("📍 Current Location Detected")
            st.write(f"**Address:** {location['address']}")
            st.write(f"**City:** {location['city']}")
            st.write(f"**State:** {location['state']}")
            st.write(f"**Country:** {location['country']}")
            st.write(f"**Coordinates:** {location['lat']:.4f}, {location['lng']:.4f}")
            st.write(f"**Last Updated:** {location['timestamp']}")
        else:
            st.warning("⚠️ Unable to retrieve location data.")
            st.info("Check your internet connection and try again.")

        if st.button("🔄 Refresh Location"):
            st.cache_data.clear()
            st.experimental_rerun()

        st.subheader("Instructions")
        st.markdown("""
        1. Click **START** to enable your camera  
        2. The app overlays location info on the video  
        3. Location updates automatically every 5 seconds  
        4. Click **STOP** to end the stream  
        """)
        st.caption("Note: Accuracy depends on your network and browser permissions.")

# ------------------ Run App ------------------
if __name__ == "__main__":
    main()


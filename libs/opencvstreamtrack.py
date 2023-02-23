import cv2
from av import VideoFrame
from aiortc.mediastreams import VideoStreamTrack

# Define a class that extends VideoStreamTrack to store the video stream from OpenCV
class OpenCVStreamTrack(VideoStreamTrack):
    def __init__(self, device_index=0):
        super().__init__()        
        self._cap = cv2.VideoCapture(device_index)
    #Can handle the frame here
    async def recv(self):
        # Wait for a new frame from the camera
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame from camera")
        
        # Convert the OpenCV frame to an AV VideoFrame
        frame = VideoFrame.from_ndarray(frame, format="bgr24")
        
        # Return the VideoFrame as a dictionary
        return {"frame": frame}
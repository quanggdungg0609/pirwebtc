import cv2
from av import VideoFrame
import pyaudio
from aiortc.mediastreams import VideoStreamTrack, AudioStreamTrack

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
        return frame
    
class PyAudioStreamTrack(AudioStreamTrack):
    def __init__(self):
        super().__init__()
        self.__chunk=4096
        self.__format = pyaudio.paInt16
        self.__chanels = 2
        self.__rate= 44100
        self.__p= pyaudio.PyAudio()
import cv2
from av import VideoFrame
import pyaudio
from aiortc.mediastreams import VideoStreamTrack, AudioStreamTrack

# Define a class that extends VideoStreamTrack to store the video stream from OpenCV
class OpenCVStreamTrack(VideoStreamTrack):
    def __init__(self, device_index=0):
        super().__init__()        
        self._cap = cv2.VideoCapture(device_index)
        self._prev_frame=None

    #Can handle the frame here
    async def recv(self):
        # Wait for a new frame from the camera
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame from camera")
        
        # Convert the OpenCV frame to an AV VideoFrame
        frame = VideoFrame.from_ndarray(frame, format="bgr24")
        # Check for motion
        gray_frame= cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray_frame= cv2.GaussianBlur(gray_frame, (21, 21), 0)
        if self._prev_frame is None:
            self._prev_frame=gray_frame
        else:
            frame_delta= cv2.absdiff(self._prev_frame, gray_frame)
            thresh= cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY[1])
            contours, _ = cv2.findContours(thresh.copyt(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours)==0: 
                return None
            
            # draw bounding boxes around the contours
            for contour in contours:
                x, y, w, h= cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 2)
        self._prev_frame= gray_frame

        #Convert the openCV frame to AV VideoFrame

        frame = VideoFrame.from_ndarray(frame, format='bgr24')

        return frame
            

        # Return the VideoFrame as a dictionary
        return frame
    
class PyAudioStreamTrack(AudioStreamTrack):
    def __init__(self):
        super().__init__()
        self.__chunk=4096
        self.__format = pyaudio.paInt16
        self.__channels = 2
        self.__rate= 44100
        self.__p= pyaudio.PyAudio()
        self.__stream= self.__p.open(format= self.__format,
                                channels=self.channels,
                                rate= self.__rate,\
                                input=True,
                                frames_per_buffer=self.__chunk)

    async def recv(self):
        data= self.__stream.read(self.__chunk)
        return data
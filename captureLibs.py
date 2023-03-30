import cv2
import numpy as np
from av import VideoFrame
# import pyaudio
from aiortc import MediaStreamTrack
from aiortc.mediastreams import VideoStreamTrack, AudioStreamTrack

# Define a class that extends VideoStreamTrack to store the video stream from OpenCV
class DetectMotionTrack(MediaStreamTrack):
    kind='video'
    def __init__(self, track):
        super().__init__()        
        self.track=track
        self.static_back=None
    #Can handle the frame here
    async def recv(self):
        frame=await self.track.recv()
        np_frame=frame.to_ndarray(format="bgr24")
        np_frame = cv2.cvtColor(np_frame, cv2.COLOR_RGB2BGR)
        gray=cv2.cvtColor(np_frame,cv2.COLOR_BGR2GRAY)
        gray=cv2.GaussianBlur(gray,(5,5),0)
        if self.static_back is None:
            self.static_back=gray
            
        frameDelta = cv2.absdiff(gray,self.static_back)
        self.static_back=gray
        kernel=np.ones((5,5))
        frameDelta= cv2.dilate(frameDelta,kernel,1)
        thresh_frame= cv2.threshold(src=frameDelta, thresh=20, maxval=255, type=cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(image=thresh_frame, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
        # cv2.drawContours(image=np_frame, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)

        for contour in contours:
            if cv2.contourArea(contour) < 50:
                # too small: skip!
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(img=np_frame, pt1=(x, y), pt2=(x + w, y + h), color=(0, 255, 0), thickness=2)

        new_frame=VideoFrame.from_ndarray(np_frame, format='rgb24')
        new_frame.pts=frame.pts
        new_frame.time_base=frame.time_base
        return new_frame
            

    
# class PyAudioStreamTrack(AudioStreamTrack):
#     def __init__(self):
#         super().__init__()
#         self.__chunk=4096
#         self.__format = pyaudio.paInt16
#         self.__channels = 2
#         self.__rate= 44100
#         self.__p= pyaudio.PyAudio()
#         self.__stream= self.__p.open(format= self.__format,
#                                 channels=self.__channels,
#                                 rate= self.__rate,\
#                                 input=True,
#                                 frames_per_buffer=self.__chunk)

#     async def recv(self):
#         data= self.__stream.read(self.__chunk)
#         return data


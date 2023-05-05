import cv2
import numpy as np
from av import VideoFrame
# import pyaudio
from aiortc import MediaStreamTrack
from aiortc.mediastreams import VideoStreamTrack, AudioStreamTrack

# Define a class that extends VideoStreamTrack to store the video stream from OpenCV
class DetectMotionTrack(MediaStreamTrack):
    kind='video'
    def __init__(self,track):
        super().__init__()        
        self.track=track
        self.static_back=None
    #Can handle the frame here
    async def recv(self):
        frame=await self.track.recv()
        np_frame=frame.to_ndarray(format="bgr24")
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


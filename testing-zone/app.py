from aiortc import RTCSessionDescription, RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCIceGatherer, RTCIceCandidate
from aiortc.contrib.media import MediaRelay, MediaPlayer
import socketio
import asyncio
import logging
import json
import uuid

# from libs.opencvstreamtrack import *

logging.basicConfig(level=logging.INFO)



class PiCamRTC:
    def __init__(self, name):
        self.name=name
        self.id=str(uuid.uuid4())
        self.__peers=dict()
        self.__clients=set()
        self.__sio = socketio.AsyncClient(logger=True)
        # self.__video=OpenCVStreamTrack()
        self.__player=MediaPlayer('/dev/video0', format='v4l2', options={
            'video_size':'320x240',
            'framerate':'15'
        })
        self.__stream=MediaRelay().subscribe(self.__player.video)
        

    async def run(self):
        self.__sio.on("connect", self.__handleConnection)
        self.__sio.on("list-client",self.__handleListClient)
        
        self.__sio.on("client-connected", self.__handleClientConnect)
        self.__sio.on("client-disconnect", self.__handleClientDisconnected)

        self.__sio.on('offer', self.__handleOffer)
        try:
            #TODO: connect o nha thi su dung 192.168.0.28 o bureau thi 192.168.8.65
            await self.__sio.connect("http://192.168.0.7:3000")
            print("Connected to server")
            await self.__sio.wait()
        except Exception as e:
            print("Failed to connect to server:", e)

    async def __handleConnection(self):
        logging.info("Connected to the server")
        data={
            "id":self.id,
            "type": "camera",
            "name": self.name
        }
        await self.__sio.emit("new",data)
   
    '''
    handle events sections
    '''
    async def __handleListClient(self, data):
        for item in data:
            self.__clients.add(item)
        

    async def __handleClientConnect(self,data):
        logging.info("New client connected")
        if data not in self.__clients:
            self.__clients.add(data)
        print(self.__clients)
    
    async def __handleClientDisconnected(self, data):
        logging.info("A client has diconnected from server...")
        if data in self.__clients:
            self.__clients.remove(data)
        print(self.__clients)

                

    async def __handleOffer(self, data):
        peer=RTCPeerConnection()
        peer.addTransceiver(self.__relay.subscribe(self.__player.video),"sendonly")
        # peer.addTrack(self.__relay.subscribe(self.__player.video))
        async def on_ice_candidate(candidate):
            print(candidate)
        
        
        peer.on('icecandidate', on_ice_candidate)
        offer=RTCSessionDescription(data.get('payload').get('sdp'), data.get('payload').get('type'))
        await peer.setRemoteDescription(offer)
        answer= await peer.createAnswer()
        message={
            'target': data.get('id'),
            'payload': json.dumps({"type":answer.type, "sdp":answer.sdp})
        }
        await self.__sio.emit('answer', message)
       

pi = PiCamRTC("Camera-1")
asyncio.run(pi.run())


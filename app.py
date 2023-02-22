from aiortc import RTCSessionDescription, RTCPeerConnection
from aiortc.contrib.media import MediaRelay
import socketio
import asyncio
import logging
import json

from libs.opencvstreamtrack import *

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s')

class PiCamRTC:
    def __init__(self, name):
        self.name=name
        self.__peers=dict()
        self.__clients=set()
        self.__sio = socketio.AsyncClient(logger=True)
        # self.__video=OpenCVStreamTrack()
        # self.__relay=MediaRelay().subscribe(self.__video)


    async def run(self):
        self.__sio.on("connect", self.__handleConnection)
        self.__sio.on("list-client",self.__handleListClient)
        self.__sio.on("client-connected", self.__handleClientConnect)
        # self.__sio.on("start-negociate", self.__handleStartNegociate)
        try:
            await self.__sio.connect("http://192.168.0.7:3000")
            print("Connected to server")
            await self.__sio.wait()
        except Exception as e:
            print("Failed to connect to server:", e)

    async def __handleConnection(self):
        logging.info("Connected to the server")
        data={
            "type": "camera",
            "name": self.name
        }
        await self.__sio.emit("new",data)

    async def __handleListClient(self, data):
        for item in data:
            self.__clients.add(item)
        print(self.__clients)

    async def __handleClientConnect(self,data):
        logging.info("New client connected")
        if data not in self.__clients:
            self.__clients.add(data)
        print(self.__clients)
    #TODO: sự kiện khi có 1 client disconnect khỏi server
    # async def __handleStartNegociate(self):
    #     logging.info("Ready to negociate")
    #     peer=RTCPeerConnection()
    #     peer.addTrack(self.__relay)
    #     offer= await peer.createOffer()
    #     await peer.setLocalDescription(offer)
    #     logging.info("Peer created ready to emit offer SDP")
    #     serializeSDP=json.dumps({"type":offer.type, "sdp":offer.sdp})
    #     try:
    #         await self.__sio.emit("offer",serializeSDP)
    #     except:
    #         logging.error("Cannot emit offer SDP")
        

pi = PiCamRTC("Camera-1")
asyncio.run(pi.run())

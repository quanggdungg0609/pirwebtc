from aiortc import RTCSessionDescription, RTCPeerConnection, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay
import socketio
import asyncio
import logging
import json
import uuid

from libs.opencvstreamtrack import *

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s')

class PiCamRTC:
    def __init__(self, name):
        self.name=name
        self.id=str(uuid.uuid4())
        self.__peers=dict()
        self.__clients=set()
        self.__sio = socketio.AsyncClient(logger=True)
        self.__video=OpenCVStreamTrack()
        self.__relay=MediaRelay().subscribe(self.__video)
        logging.info(f'ID: {self.id}')

    async def run(self):
        self.__sio.on("connect", self.__handleConnection)
        # TODO: cần lắng nghe sự kiện reconnection để yêu cầu cập nhật lại danh sách client đang kết nối
        self.__sio.on("reconnect",self.__handleReconnect)
        self.__sio.on("list-client",self.__handleListClient)
        
        self.__sio.on("client-connected", self.__handleClientConnect)
        self.__sio.on("client-disconnect", self.__handleClientDisconnected)

        self.__sio.on("answer", self.__handleAnswer)
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
            "id":self.id,
            "type": "camera",
            "name": self.name
        }
        await self.__sio.emit("new",data)
    async def __handleReconnect(self):
        print("reconnect .... ")
    '''
    handle events sections
    '''
    async def __handleListClient(self, data):
        for item in data:
            self.__clients.add(item)
        
        # create peer for each clients in the list
        for client in data:
            await self.__initPeer(client)
        logging.info("Finish create peer and send offer to all clients, wait for answers...")

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

    async def __handleAnswer(self, data):
        id=data.get("id")
        logging.info(f"Receive a answer SDP {id}")
        peer=self.__peers.get(data.get("id"))
        answerSDP=RTCSessionDescription(data.get("payload").get("sdp"), data.get("payload").get("type"))
        await peer.setRemoteDescription(answerSDP)
        # TODO: kiểm tra lại peer và lấy stream từ peer

    async def __initPeer(self, client: str):
        logging.info(f"Prepare to negociate with {client}")
        #Create Peer
        config=RTCConfiguration(iceServers=[
            RTCIceServer(
                urls=["stun:stun.l.google.com:19302"],
                credential=None,
                username=None
            )
        ])
        peer=RTCPeerConnection(config)
        peer.addTrack(self.__relay)
        # create offer SDP
        offer= await peer.createOffer()
        await peer.setLocalDescription(offer)
        logging.info("Peer created ready to emit offer SDP")
        # emit offer SDP to clients
        serializeSDP=json.dumps({"type":offer.type, "sdp":offer.sdp})
        message={
            "target":client,
            "payload":serializeSDP
        }
        try:
            await self.__sio.emit("offer",message)
        except:
            logging.error("Cannot emit offer SDP")
        self.__peers.update({client:peer})

pi = PiCamRTC("Camera-1")
asyncio.run(pi.run())

import socketio
import asyncio
import uuid
import logging
import json
from aiortc import RTCSessionDescription, RTCPeerConnection, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay, MediaPlayer

logging.basicConfig(level=logging.DEBUG)

config=RTCConfiguration(iceServers=[
            RTCIceServer(
                urls=[
                      'stun:stun1.l.google.com:19302',
                      'stun:stun2.l.google.com:19302',
                    ],
        
            )
])

class PiRTC:
    def __init__(self):
        self.name='camera-1'
        self.id=str(uuid.uuid4())
        self._sio=socketio.AsyncClient(logger=True)
        self._listClient=set()
        self._player=MediaPlayer('/dev/video0', format='v4l2', options={
            'video_size':'320x240',
            'framerate':'15'
        })
        self._relay=MediaRelay()

    async def run(self):
        # add event handle for socket.io
        self._sio.on("connect",self._handleConnect)

        self._sio.on("list-client-connecetd", self._handleListClientConnected)
        self._sio.on('new-client-conneceted', self.__handleClientConnect)
        self._sio.on('client-disconnect', self.__handleClientDisconnected)

        self._sio.on('offer', self._handleOffer)
        await self._sio.connect("http://wan41.lanestel.net:3000/")
        await self._sio.wait()
    # on connection
    async def _handleConnect(self):
        message={
            "type":"camera",
            "id":self.id,
            'name':self.name
        }
        await self._sio.emit("new", message)

    # get the list of clients connected on the server first time
    async def _handleListClientConnected(self, data):
        for item in data:
            self._listClient.add(item)
        print(self._listClient)

    # handle event when a new camera connected to the server
    async def __handleClientConnect(self,data):
        logging.info("New client connected")
        if data not in self._listClient:
            self._listClient.add(data)
        print(self._listClient)
    
    # handle event when a camera disconnected
    async def __handleClientDisconnected(self, data):
        logging.info("A client has diconnected from server...")
        if data in self._listClient:
            self._listClient.remove(data)
        print(self._listClient)


    # when received a sdp offer 
    async def _handleOffer(self,data):
        if data.get('id') in self._listClient:
            offer=RTCSessionDescription(data.get('payload').get('sdp'), data.get('payload').get('type'))
            pc=RTCPeerConnection()
            pc.addTrack(self._relay.subscribe(self._player.video))
            await pc.setRemoteDescription(offer)
            answer= await pc.createAnswer()
            await pc.setLocalDescription(answer)
            message={
                'target': data.get('id'),
                'payload': json.dumps({"type":answer.type, "sdp":answer.sdp})
            }
            await self._sio.emit('answer',message)
        else:
            print("Client not exist")
        # TODO: need to be verify the video transmit
pi=PiRTC()
asyncio.run(pi.run())
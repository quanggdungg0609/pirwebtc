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
        # capture video from camera, may be change to opencv capture to handle frame for movement detection
        self._player=MediaPlayer('/dev/video0', format='v4l2', options={
            'video_size':'320x240',
            'framerate':'15'
        })
        self._relay=None
        
    def _create_local_track(self):
        if self._relay is None:
            self._relay = MediaRelay()
        return self._relay.subscribe(self._player.video)

    async def run(self):
        # add event handle for socket.io
        self._sio.on("connect",self._handleConnect)

        # handle the connection of clients
        self._sio.on("list-client-connecetd", self._handleListClientConnected)
        self._sio.on('new-client-conneceted', self._handleClientConnect)
        self._sio.on('client-disconnect', self._handleClientDisconnected)

        #handle the receive offer sdp of client
        self._sio.on('offer', self._handleOffer)

        # etablish connection with the socketio server
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
    # when we got the the list of clients connected, create a new peer and add 
    # a new track for the for each peer of earch client
    async def _handleListClientConnected(self, data):
        for item in data:
            pc=RTCPeerConnection(config)
            stream= self._create_local_track()
            pc.addTrack(stream)
            self._listClient.update({item : pc})
        print(self._listClient)

    # handle event when a new camera connected to the server
    async def _handleClientConnect(self,data):
        logging.info("New client connected")
        if not self._listClient.has_key(data):
            pc=RTCPeerConnection(config)
            stream=self._create_local_track()
            pc.addTrack(stream)
            self._listClient.update({data: pc})
        print(self._listClient.keys())
    
    # handle event when a camera disconnected
    async def _handleClientDisconnected(self, data):
        logging.info("A client has diconnected from server...")
        if self._listClient.has_key(data):
            await self._listClient.get(data).close()
            self._listClient.pop(data)
        print(self._listClient)


    # when received a sdp offer 
    async def _handleOffer(self,data):
        if self._listClient.has_key(data.get('id')):
            offer=RTCSessionDescription(data.get('payload').get('sdp'), data.get('payload').get('type'))
            #bind the sdp offer to the peer reserved for client 
            try:
                await self._listClient.get(data.get('id')).setRemoteDescription(offer)
                answer = await self._listClient.get(data.get('id')).createAnswer()
                await self._listClient.get(data.get('id')).setLocalDescription(answer)
            except Exception:
                print(Exception)
            message={
                'target':data.get('id'),
                'payload': json.dumps({"type": answer.type, "sdp": answer.sdp})
            }
            try:
                await self._sio.emit("answer",message)
            except Exception:
                print(Exception)

        
pi=PiRTC()
asyncio.run(pi.run())
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

        self._listPeer=dict()
        # capture video from camera, may be change to opencv capture to handle frame for movement detection
        self._webcam = None
        self._relay=None

        
    def _create_local_track(self):
        options = {"framerate": "20", "video_size": "320x240"}
        if self._relay is None:
            self._webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
            self._relay = MediaRelay()
        return self._relay.subscribe(self._webcam.video)

    async def run(self):
        # add event handle for socket.io
        self._sio.on("connect",self._handleConnect)

        # self._sio.on('client-disconnect', self._handleClientDisconnected)

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


    # when received a sdp offer 
    async def _handleOffer(self,data):
            #bind the sdp offer to the peer reserved for client 
            offer=RTCSessionDescription(data.get('payload').get('sdp'), data.get('payload').get('type'))
            pc=RTCPeerConnection(config)
            self._listPeer.update({data.get('id') : pc })

            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                print("Connection state is %s" % pc.connectionState)
                if pc.connectionState == "failed":
                    await pc.close()
                elif pc.connectionState == 'disconnected':
                    await pc.close()

            

            stream= self._create_local_track()
            pc.addTrack(stream)

            await pc.setRemoteDescription(offer)

            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            
            message={
                'target':data.get('id'),
                'payload': json.dumps({"type": answer.type, "sdp": answer.sdp})
            }
            await self._sio.emit("answer",message)


        
pi=PiRTC()
asyncio.run(pi.run())
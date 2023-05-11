import socketio
import asyncio
import uuid
import logging
import json
import os
import sys
from aiortc import RTCSessionDescription, RTCPeerConnection, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaRelay, MediaPlayer

# from captureLibs import DetectMotionTrack

# logging.basicConfig(level=logging.DEBUG)

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
        self.information="Raspberry PI 4B"
        self._sio=socketio.AsyncClient(logger=True)

        self._listPeer=dict()
        # capture video from camera, may be change to opencv capture to handle frame for movement detection
        self._webcam = None
        self._relay=None

        
    def _create_local_track(self):
        #best resolution for avoid the delay when capture, compress and send video throught WebRTC
        options = {"framerate": "10", "video_size": "720x480"}
        if self._relay is None:
            self._webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
            # self._webcam=DetectMotionTrack(self._webcam.video)
            self._relay = MediaRelay()
        return self._relay.subscribe(self._webcam.video)

    async def run(self):
        # add event handle for socket.io
        self._sio.on("connect",self._handleConnect)
        self._sio.on('client-disconnect', self._handleClientDisconnected)
        #handle the receive offer sdp of client
        self._sio.on('offer', self._handleOffer)
        # etablish connection with the socketio server
        try:
            await self._sio.connect("http://wan41.lanestel.net:3000/")
            await self._sio.wait()
        except Exception:
            print("Can't connect to server")

    # on connection
    async def _handleConnect(self):
        message={
            "type":"camera",
            "id":self.id,
            'name':self.name,
            'information':self.information
        }
        await self._sio.emit("new", message)

    #on client disconnect
    async def _handleClientDisconnected(self,data):
        '''
            when a client disconnect, close a peer connected to the client immediately and 
            remove the client from the list of client
        '''
        if(self._listPeer.get(data) is not None):
            await self._listPeer.get(data).close()
            if data in self._listPeer:
                self._listPeer.pop(data,None)
        

        

    # when received a sdp offer 
    async def _handleOffer(self,data):
            #bind the sdp offer to the peer reserved for client 
            offer=RTCSessionDescription(data.get('payload').get('sdp'), data.get('payload').get('type'))
            pc=RTCPeerConnection(config)
            self._listPeer.update({data.get('id') : pc })

            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                print("Connection state is %s" % pc.connectionState)
                print(list(self._listPeer.keys())[list(self._listPeer.values()).index(pc)])
                if pc.connectionState == "failed":
                    print(pc)
                    await pc.close()
            @pc.on("signalingstatechange")
            
            @pc.on("iceconnectionstatechange")
            async def on_iceconnectionstatechange():
                print("ICE connection state is %s" % pc.iceConnectionState)
                if pc.iceConnectionState=="failed":
                    print(pc)
                    await pc.close()
            
            stream= self._create_local_track()
            
            pc.addTrack(stream)
            try:
                await pc.setRemoteDescription(offer)
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
            except Exception:
                print(Exception)

            message={
                'target':data.get('id'),
                'payload': json.dumps({"type": pc.localDescription.type, "sdp": pc.localDescription.sdp})
            }
            try:
                await self._sio.emit("answer",message)
            except Exception:
                print(Exception)


    async def stop(self):
        await self._sio.disconnect()

        
pi=PiRTC()

asyncio.run(pi.run())

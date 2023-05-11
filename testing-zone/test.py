from aiortc import RTCSessionDescription, RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCIceGatherer, RTCIceCandidate
from aiortc.contrib.media import MediaRelay, MediaPlayer
import socketio
import asyncio
import uuid
import json
import logging

logging.basicConfig(level=logging.DEBUG)
name='pi-camera'
id=str(uuid.uuid4())
sio = socketio.AsyncClient(logger=True)
player=MediaPlayer('/dev/video0', format='v4l2', options={
            'video_size':'320x240',
            'framerate':'15'
})
relay=MediaRelay()
peers=dict()
clients=set()

async def main():
    sio.on("connect", handleConnection)
    sio.on("list-client", handleListClient)

    sio.on("client-connected", handleClientConnect)
    sio.on("client-disconnect", handleClientDisconnected)

    sio.on('answer',handleAnswer)

    sio.on('ice-candidate',handleIceCandidate)

    await sio.connect("http://192.168.0.7:3000")
    print("Connected to server")
    await sio.wait()

async def handleConnection():
        data={
            "id":id,
            "type": "camera",
            "name": name
        }
        await sio.emit("new",data)

async def handleListClient(data):
        print("New client connected")
        for item in data:
            clients.add(item)

async def handleClientDisconnected(data):
        print("A client has diconnected from server...")
        if data in clients:
            clients.remove(data)
        print(clients)

async def handleClientConnect(data):
    '''
    data is a id of the client connected
    '''
    print("New client connected")
    if data not in clients:
        clients.add(data)

    config=RTCConfiguration(iceServers=[
            RTCIceServer(
                urls=['stun:stun.l.google.com:19302',
                      'stun:stun1.l.google.com:19302',
                      'stun:stun2.l.google.com:19302',
                      'stun:stun3.l.google.com:19302',
                      'stun:stun4.l.google.com:19302',
                    ],
            )
    ])
    peer=RTCPeerConnection(config)
    peer.addTrack(relay.subscribe(player.video))

    @peer.on("icecandidate")
    async def on_ice_candidate(candidate):
        if candidate:
            print("Lấy ra candidate: ", candidate.candidate)
            # Xử lý candidate ở đây
    @peer.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print("ICE connection state is %s", peer.iceConnectionState)
   
        
    offer=await peer.createOffer()
    await peer.setLocalDescription(offer)
    message={
        'target':data,
        'payload':json.dumps({"type":offer.type, "sdp":offer.sdp})
    }
    await sio.emit('offer', message)
    peers.update({data: peer})

async def handle_ice_candidate(peer):
    candidates=[]
    if peer.iceGatheringState=='complete':
        print(peer.sctp)

async def handleAnswer(data):
    answer=RTCSessionDescription(sdp=data.get('payload').get('sdp'), type=data.get('payload').get('type'))
    await peers.get(data.get('id')).setRemoteDescription(answer)
    await handle_ice_candidate(peers.get(data.get('id')))

async def handleIceCandidate(data):
    ip=data.get('payload').get('ip')
    if '[' in ip:
         ip=ip.replace("[", "").replace("]", "")
    iceCandidate=RTCIceCandidate (component=data.get('payload').get('component'),
        foundation=data.get('payload').get('foundation'),
        ip=ip,
        port=data.get('payload').get('port'),
        priority=data.get('payload').get('priority'),
        protocol=data.get('payload').get('protocol'),
        type=data.get('payload').get('type'),
        relatedAddress=data.get('payload').get('relatedAddress'),
        relatedPort=data.get('payload').get('relatedPort'),
        sdpMid=data.get('payload').get('sdpMid'),
        sdpMLineIndex=data.get('payload').get('sdpMLineIndex'),
        tcpType=data.get('payload').get('tcpType'))
    await peers.get(data.get('id')).addIceCandidate(iceCandidate)
    




asyncio.run(main())
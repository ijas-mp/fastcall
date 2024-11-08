const joinRoomButton = document.getElementById('joinRoomButton');
const startButton = document.getElementById('startButton');
const hangupButton = document.getElementById('hangupButton');

let localStream;
let remoteStream;
let pc;
let ws;
let roomName;

// Event listeners
joinRoomButton.onclick = joinRoom;
startButton.onclick = startCall;
hangupButton.onclick = hangUp;

async function joinRoom() {
    roomName = document.getElementById("room").value;
    if (!roomName) {
        alert("Please enter a room name.");
        return;
    }

    ws = new WebSocket(`ws://localhost:8000/ws/${roomName}/${Math.random().toString(36).substring(2)}`);
    ws.onopen = () => console.log("Connected to WebSocket");
    ws.onmessage = handleWebSocketMessage;
    ws.onclose = () => console.log("Disconnected from WebSocket");

    joinRoomButton.disabled = true;
    startButton.disabled = false;
}

async function startCall() {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    document.getElementById('localVideo').srcObject = localStream;

    pc = createPeerConnection();

    localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    ws.send(JSON.stringify({ type: "offer", sdp: offer.sdp }));
    startButton.disabled = true;
    hangupButton.disabled = false;
}

function hangUp() {
    if (pc) pc.close();
    localStream.getTracks().forEach(track => track.stop());
    ws.send(JSON.stringify({ type: "hangup" }));
    hangupButton.disabled = true;
    startButton.disabled = false;
}

function createPeerConnection() {
    const newPc = new RTCPeerConnection();

    newPc.onicecandidate = ({ candidate }) => {
        if (candidate) {
            ws.send(JSON.stringify({
                type: "candidate",
                candidate: candidate.candidate,
                sdpMid: candidate.sdpMid,
                sdpMLineIndex: candidate.sdpMLineIndex,
            }));
        }
    };

    newPc.ontrack = event => {
        if (!remoteStream) {
            remoteStream = new MediaStream();
            document.getElementById('remoteVideo').srcObject = remoteStream;
        }
        remoteStream.addTrack(event.track);
    };

    return newPc;
}

async function handleWebSocketMessage(event) {
    const message = JSON.parse(event.data);

    switch (message.type) {
        case "offer":
            await handleOffer(message);
            break;
        case "answer":
            await handleAnswer(message);
            break;
        case "candidate":
            await handleCandidate(message);
            break;
        case "hangup":
            hangUp();
            break;
        default:
            console.warn("Unknown message type:", message.type);
    }
}

async function handleOffer(offer) {
    if (!pc) pc = createPeerConnection();

    await pc.setRemoteDescription(new RTCSessionDescription({ type: "offer", sdp: offer.sdp }));
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);

    ws.send(JSON.stringify({ type: "answer", sdp: answer.sdp }));
}

async function handleAnswer(answer) {
    await pc.setRemoteDescription(new RTCSessionDescription({ type: "answer", sdp: answer.sdp }));
}

async function handleCandidate(candidate) {
    try {
        await pc.addIceCandidate(new RTCIceCandidate({
            candidate: candidate.candidate,
            sdpMid: candidate.sdpMid,
            sdpMLineIndex: candidate.sdpMLineIndex,
        }));
    } catch (error) {
        console.error("Error adding received ICE candidate", error);
    }
}

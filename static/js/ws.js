const listeners = {};

export function onMessage(eventType, callback) {
  (listeners[eventType] ||= []).push(callback);
}

export function connectWS() {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log("ws message", msg);
    const eventType = msg.event || msg.type;
    for (const cb of listeners[eventType] || []) cb(msg);
  };
  ws.onclose = () => setTimeout(connectWS, 2000);
}

// src/utils/ws.js

const WS_BASE =
  import.meta.env.VITE_WS_URL ||
  (location.protocol === "https:" ? "wss://localhost:8000" : "ws://localhost:8000");

export default class TranscriptionSocket {
  constructor(language = "auto") {
    this.language = language;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectRetries = 5;
    this.heartbeat = null;

    // Event callbacks (set from outside)
    this.onMessage = null;
    this.onOpen = null;
    this.onClose = null;
    this.onError = null;
  }

  connect() {
    const wsURL = `${WS_BASE.replace(/\/+$/, "")}/transcribe/${encodeURIComponent(
      this.language
    )}`;

    this.ws = new WebSocket(wsURL);
    this.ws.binaryType = "arraybuffer";

    this.ws.onopen = (event) => {
      this.reconnectAttempts = 0;
      this.#startHeartbeat();

      this.onOpen && this.onOpen(event);
    };

    this.ws.onmessage = (event) => {
      try {
        const text =
          typeof event.data === "string" ? event.data : new TextDecoder().decode(event.data);
        const payload = JSON.parse(text);

        this.onMessage && this.onMessage(payload);
      } catch (err) {
        console.warn("WS: message parse failed", err);
      }
    };

    this.ws.onclose = (event) => {
      this.#stopHeartbeat();

      if (this.reconnectAttempts < this.maxReconnectRetries) {
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), 500 * this.reconnectAttempts);
      }

      this.onClose && this.onClose(event);
    };

    this.ws.onerror = (event) => {
      this.onError && this.onError(event);
    };

    return this;
  }

  sendBinary(data) {
    if (!this.#isReady()) return;
    this.ws.send(data);
  }

  sendText(obj) {
    if (!this.#isReady()) return;
    this.ws.send(JSON.stringify(obj));
  }

  close() {
    this.#stopHeartbeat();
    this.ws?.close();
    this.ws = null;
  }

  // ---------------------
  // 🔒 Private utilities
  // ---------------------

  #isReady() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  #startHeartbeat() {
    this.#stopHeartbeat(); // ensures only one timer runs

    this.heartbeat = setInterval(() => {
      if (this.#isReady()) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 8000);
  }

  #stopHeartbeat() {
    if (this.heartbeat) {
      clearInterval(this.heartbeat);
      this.heartbeat = null;
    }
  }
}

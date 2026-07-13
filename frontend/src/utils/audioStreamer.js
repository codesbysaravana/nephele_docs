export class AudioStreamer {
  constructor(webSocket) {
    this.ws = webSocket;
    this.audioContext = null;
    this.mediaStream = null;
    this.processor = null;
    this.isRecording = false;
  }

  async start() {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      
      // Use ScriptProcessorNode for raw PCM extraction (buffer size 4096)
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      
      this.processor.onaudioprocess = (e) => {
        if (!this.isRecording || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        
        const float32Data = e.inputBuffer.getChannelData(0);
        // Convert Float32 to Int16 PCM
        const int16Data = new Int16Array(float32Data.length);
        for (let i = 0; i < float32Data.length; i++) {
          let s = Math.max(-1, Math.min(1, float32Data[i]));
          int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Send raw PCM ArrayBuffer to WebSocket
        this.ws.send(int16Data.buffer);
      };

      source.connect(this.processor);
      this.processor.connect(this.audioContext.destination);
      this.isRecording = true;
      console.log("Started audio streaming (16kHz PCM)");
    } catch (err) {
      console.error("Failed to start audio streamer:", err);
      throw err;
    }
  }

  stop() {
    this.isRecording = false;
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop());
      this.mediaStream = null;
    }
    console.log("Stopped audio streaming");
  }
}

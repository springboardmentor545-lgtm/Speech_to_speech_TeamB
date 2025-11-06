class RecorderProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._bufferSize = 4096;
    this._buffer = new Int16Array(this._bufferSize);
    this._init = true;
  }

  process(inputs) {
    const input = inputs[0][0];
    // The input is a Float32Array. Convert it to Int16.
    for (let i = 0; i < input.length; i++) {
      this._buffer[i] = input[i] * 0x7FFF;
    }

    this.port.postMessage(this._buffer, [this._buffer.buffer]);
    return true;
  }
}

registerProcessor('recorder-processor', RecorderProcessor);
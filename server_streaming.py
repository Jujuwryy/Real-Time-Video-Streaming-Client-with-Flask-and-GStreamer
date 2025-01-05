from flask import Flask, jsonify
import logging
import gi
from gi.repository import Gst

# Initialize GStreamer and logging
gi.require_version('Gst', '1.0')
Gst.init(None)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for pipeline and streaming state
pipeline = None
is_streaming = False

app = Flask(__name__)

def create_pipeline():
    return Gst.parse_launch(
        "autovideosrc ! videoconvert ! x264enc tune=zerolatency ! rtph264pay name=payloader ! udpsink host=127.0.0.1 port=8079"
    )

def start_stream():
    global pipeline, is_streaming
    if is_streaming:
        return "Stream is already running."
    pipeline = create_pipeline()
    pipeline.set_state(Gst.State.PLAYING)
    is_streaming = True
    return "Stream started."

def stop_stream():
    global pipeline, is_streaming
    if not is_streaming:
        return "No stream to stop."
    pipeline.set_state(Gst.State.NULL)
    pipeline = None
    is_streaming = False
    return "Stream stopped."

@app.route('/start', methods=['POST'])
def start():
    message = start_stream()
    return jsonify({"message": message})

@app.route('/stop', methods=['POST'])
def stop():
    message = stop_stream()
    return jsonify({"message": message})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"streaming": is_streaming})

def run_server():
    app.run(host='127.0.0.1', port=8079, debug=False)

if __name__ == '__main__':
    run_server()

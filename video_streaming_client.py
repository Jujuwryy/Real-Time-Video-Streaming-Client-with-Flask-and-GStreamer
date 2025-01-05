import gi

gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GLib, Gtk
import threading
from flask import Flask, jsonify, render_template_string
import logging
import sys
import platform
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize GStreamer
Gst.init(None)

# Flask application
app = Flask(__name__)

# Global variables for the GStreamer pipeline
pipeline = None
is_streaming = False


class StreamingClient:
    """
    A client application for viewing video streams using GStreamer and GTK.

    Attributes:
        pipeline (Gst.Pipeline): The GStreamer pipeline for video playback.
        window (Gtk.Window): The main application window.
        video_area (Gtk.DrawingArea): The area where video is displayed.
        status_label (Gtk.Label): Label to display the status of the stream.
        server_url (str): URL of the Flask server managing the stream.
    """

    def __init__(self):
        """
        Initializes the StreamingClient instance with default values.
        """
        self.pipeline = None
        self.window = None
        self.video_area = None
        self.status_label = None
        self.server_url = "http://127.0.0.1:8079"

    def create_gui(self):
        """
        Creates and initializes the GTK GUI for the application.
        """
        self.window = Gtk.Window(title="Video Stream Viewer")
        self.window.connect('destroy', self.on_destroy)
        self.window.set_default_size(1100, 800)

        # Create vertical box for layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window.add(vbox)

        # Video display area
        self.video_area = Gtk.DrawingArea()
        vbox.pack_start(self.video_area, True, True, 0)

        # Control buttons
        hbox = Gtk.Box(spacing=6)
        vbox.pack_start(hbox, False, False, 0)

        self.start_button = Gtk.Button(label="Start Viewing")
        self.start_button.connect('clicked', self.on_start)
        hbox.pack_start(self.start_button, True, True, 0)

        self.stop_button = Gtk.Button(label="Stop Viewing")
        self.stop_button.connect('clicked', self.on_stop)
        self.stop_button.set_sensitive(False)
        hbox.pack_start(self.stop_button, True, True, 0)

        # Status label
        self.status_label = Gtk.Label(label="Status: Not Connected")
        vbox.pack_start(self.status_label, False, False, 0)

        self.window.show_all()

    def create_pipeline(self):
        """
        Configures the GStreamer pipeline for video playback.

        Returns:
            bool: True if the pipeline was created successfully, False otherwise.
        """
        try:
            pipeline_str = (
                "udpsrc port=8079 caps=\"application/x-rtp, media=(string)video, "
                "clock-rate=(int)90000, encoding-name=(string)H264\" ! "
                "rtph264depay ! avdec_h264 ! videoconvert ! autovideosink"
            )
            self.pipeline = Gst.parse_launch(pipeline_str)

            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect('message', self.on_message)
            logger.info("Pipeline created successfully")
            return True
        except GLib.Error as e:
            logger.error(f"Failed to create pipeline: {e}")
            self.update_status(f"Error: Failed to create pipeline - {e}")
            return False

    def initialize(self):
        """
        Initializes the pipeline and GUI.
        """
        if self.create_pipeline():
            self.create_gui()
            GLib.timeout_add(1000, self.check_server_status)

    def update_status(self, message):
        """
        Updates the status label in the GUI.

        Args:
            message (str): The message to display in the status label.
        """

        def update():
            self.status_label.set_text(message)
            return False

        GLib.idle_add(update)

    def check_server_status(self):
        """
        Checks the server status periodically and updates the GUI.

        Returns:
            bool: Always True to keep the timeout active.
        """
        try:
            response = requests.get(f"{self.server_url}/status")
            if response.status_code == 200:
                data = response.json()
                self.update_status(f"Status: {'Streaming' if data['streaming'] else 'Not Streaming'}")
        except requests.RequestException as e:
            self.update_status(f"Error: Cannot connect to server - {e}")
        return True

    def on_start(self, button):
        """
        Starts the video stream.

        Args:
            button (Gtk.Button): The button that triggered the action.
        """
        logger.info("Attempting to start stream...")
        try:
            response = requests.post(f"{self.server_url}/start")
            if response.status_code == 200:
                ret = self.pipeline.set_state(Gst.State.PLAYING)
                if ret == Gst.StateChangeReturn.FAILURE:
                    logger.error("Failed to start pipeline")
                    self.update_status("Error: Failed to start pipeline")
                    return

                self.start_button.set_sensitive(False)
                self.stop_button.set_sensitive(True)
                self.update_status("Status: Stream started")
                logger.info("Stream started successfully")
            else:
                self.update_status(f"Error: Server returned {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to connect to server: {e}")
            self.update_status(f"Error: Cannot connect to server - {e}")

    def on_stop(self, button):
        """
        Stops the video stream.

        Args:
            button (Gtk.Button): The button that triggered the action.
        """
        logger.info("Attempting to stop stream...")
        try:
            response = requests.post(f"{self.server_url}/stop")
            if response.status_code == 200:
                self.pipeline.set_state(Gst.State.NULL)
                self.start_button.set_sensitive(True)
                self.stop_button.set_sensitive(False)
                self.update_status("Status: Stream stopped")
                logger.info("Stream stopped successfully")
            else:
                self.update_status(f"Error: Server returned {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Failed to connect to server: {e}")
            self.update_status(f"Error: Cannot connect to server - {e}")

    def on_destroy(self, window):
        """
        Cleans up resources and exits the application.

        Args:
            window (Gtk.Window): The application window being closed.
        """
        logger.info("Shutting down client...")
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
        try:
            requests.post(f"{self.server_url}/stop")
        except:
            pass
        Gtk.main_quit()

    def on_message(self, bus, message):
        """
        Handles GStreamer bus messages.

        Args:
            bus (Gst.Bus): The GStreamer bus.
            message (Gst.Message): The message from the bus.
        """
        t = message.type
        if t == Gst.MessageType.ERROR:
            self.pipeline.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            logger.error(f"Pipeline error: {err}, Debug: {debug}")
            self.update_status(f"Error: {err}")
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
        elif t == Gst.MessageType.EOS:
            self.pipeline.set_state(Gst.State.NULL)
            self.update_status("Status: End of Stream")
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
        elif t == Gst.MessageType.STATE_CHANGED:
            old_state, new_state, pending_state = message.parse_state_changed()
            if message.src == self.pipeline:
                self.update_status(f"Pipeline State: {Gst.Element.state_get_name(new_state)}")


# Flask API functions (documented as needed)
def create_pipeline():
    """
    Creates the GStreamer pipeline for streaming.

    Returns:
        Gst.Pipeline: Configured GStreamer pipeline.
    """
    return Gst.parse_launch(
        "autovideosrc ! videoconvert ! x264enc tune=zerolatency ! rtph264pay name=payloader ! udpsink host=127.0.0.1 port=8079"
    )


def start_stream():
    """
    Starts the streaming pipeline.

    Returns:
        str: Message indicating the result of the operation.
    """
    global pipeline, is_streaming
    if is_streaming:
        return "Stream is already running."
    pipeline = create_pipeline()
    pipeline.set_state(Gst.State.PLAYING)
    is_streaming = True
    return "Stream started."


def stop_stream():
    """
    Stops the streaming pipeline.

    Returns:
        str: Message indicating the result of the operation.
    """
    global pipeline, is_streaming
    if not is_streaming:
        return "No stream to stop."
    pipeline.set_state(Gst.State.NULL)
    pipeline = None
    is_streaming = False
    return "Stream stopped."


@app.route('/start', methods=['POST'])
def start():
    """
    API endpoint to start the stream.
    """
    message = start_stream()
    return jsonify({"message": message})


@app.route('/stop', methods=['POST'])
def stop():
    """
    API endpoint to stop the stream.
    """
    message = stop_stream()
    return jsonify({"message": message})


@app.route('/status', methods=['GET'])
def status():
    """
    API endpoint to get the current streaming status.
    """
    return jsonify({"streaming": is_streaming})


def run_server():
    """
    Runs the Flask server in a separate thread.
    """
    app.run(host='127.0.0.1', port=8079, debug=False)


def run_gtk():
    """
    Runs the GTK main loop.
    """
    Gtk.main()


if __name__ == '__main__':
    # Flask server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    print("Server is running. Access the API at http://127.0.0.1:8079")

    # GTK client
    client = StreamingClient()
    if platform.system() == 'Darwin':  # macOS
        GLib.idle_add(client.initialize)
    else:  # Other platforms
        client.initialize()
    run_gtk()

    # Main loop for manual handling
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Shutting down...")
        if is_streaming:
            stop_stream()

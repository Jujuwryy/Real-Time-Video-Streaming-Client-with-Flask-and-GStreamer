import gi
from gi.repository import Gtk, GLib
import logging
import requests

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamingClient:
    def __init__(self):
        self.pipeline = None
        self.window = None
        self.video_area = None
        self.status_label = None
        self.server_url = "http://... . . .:xyz" #use the actual address of your local host

    def create_gui(self):
        self.window = Gtk.Window(title="Video Stream Viewer")
        self.window.connect('destroy', self.on_destroy)
        self.window.set_default_size(800, 600)

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

    def update_status(self, message):
        def update():
            self.status_label.set_text(message)
            return False

        GLib.idle_add(update)

    def check_server_status(self):
        try:
            response = requests.get(f"{self.server_url}/status")
            if response.status_code == 200:
                data = response.json()
                self.update_status(f"Status: {'Streaming' if data['streaming'] else 'Not Streaming'}")
        except requests.RequestException as e:
            self.update_status(f"Error: Cannot connect to server - {e}")
        return True

    def on_start(self, button):
        logger.info("Attempting to start stream...")
        try:
            response = requests.post(f"{self.server_url}/start")
            if response.status_code == 200:
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
        logger.info("Attempting to stop stream...")
        try:
            response = requests.post(f"{self.server_url}/stop")
            if response.status_code == 200:
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
        logger.info("Shutting down client...")
        try:
            requests.post(f"{self.server_url}/stop")
        except:
            pass
        Gtk.main_quit()


def run_gui():
    client = StreamingClient()
    client.create_gui()
    GLib.timeout_add(1000, client.check_server_status)
    Gtk.main()

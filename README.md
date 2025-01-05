# Real-Time Video Streaming Client with Flask and GStreamer

## Overview

This project implements a real-time video streaming client-server application. The client, built using GTK and GStreamer, receives a video stream and displays it in a graphical window. The server, using Flask and GStreamer, streams video over a network and controls the streaming via simple API endpoints.

## Features

- **Real-Time Video Streaming:** Using GStreamer for efficient video capture, encoding, and streaming.
- **Flask API:** Provides endpoints to control streaming (start, stop, and status) over HTTP.
- **Cross-Platform Support:** The client can run on macOS and other platforms (Linux/Windows).
- **Interactive GUI:** Built with GTK for viewing and controlling the video stream.

## Architecture

### Client (GTK + GStreamer):
- **Video Streaming Display:** 
  - The video stream is displayed using GTK's `DrawingArea` and rendered with GStreamer elements.
  
- **Control Buttons:**
  - The user can control the video stream through two buttons: `Start Viewing` and `Stop Viewing`.
  
- **Server Status Check:**
  - The client checks the server's streaming status every second and updates the GUI accordingly.

### Server (Flask + GStreamer):
- **Flask API Endpoints:**
  - `/start`: Starts the video stream.
  - `/stop`: Stops the video stream.
  - `/status`: Provides the current streaming status (running or not).

- **GStreamer Pipeline:**
  - Uses GStreamer to encode, stream, and control video playback.
  - The video is streamed using the `udpsink` element, and the server handles starting and stopping the stream based on the client’s requests.

## Installation

1. Install the necessary dependencies:
    - `GStreamer 1.0`
    - `Flask`
    - `PyGObject` for GTK
    - Other Python dependencies (see requirements.txt)

2. Clone the repository:
    ```bash
    git clone https://github.com/Jujuwryy/real-time-video-streaming.git
    cd real-time-video-streaming
    ```

3. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Use the GUI to start or stop the video stream. The Flask server will handle the streaming commands.


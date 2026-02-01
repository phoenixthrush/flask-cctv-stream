# flask-cctv-stream

A minimal Flask-based MJPEG video streaming server with fullscreen responsive client UI, camera auto-open/close logic, frame limiting, and resolution scaling.

## Quick start

```bash
pip install flask-cctv-stream
# then open http://localhost:8080/
```

## Configuration

You can configure via **CLI args** (highest priority) or **environment variables** (fallback). Defaults are shown below.

### CLI flags

```bash
--camera-index   int    Camera index (default 0)
--width          int    Frame width (default 1280)
--height         int    Frame height (default 720)
--fps            int    FPS limit (default 15)
--timeout        int    Inactivity timeout seconds (default 2)
--host           str    Bind host (default 0.0.0.0)
--port           int    Bind port (default 8080)
--log-level      str    Logging level (default INFO)
```

**Environment variables** (used when the corresponding flag is not provided)

```text
CAMERA_INDEX      FRAME_WIDTH           FRAME_HEIGHT
FPS_LIMIT         INACTIVITY_TIMEOUT
HOST              PORT                  LOG_LEVEL
```

## Running with overrides

```bash
flask-cctv-stream \
  --camera-index 0 --width 1280 --height 720 \
  --fps 15 --timeout 2 --host 0.0.0.0 --port 8080 --log-level DEBUG

# or via env vars
CAMERA_INDEX=0 FRAME_WIDTH=1280 FRAME_HEIGHT=720 \
FPS_LIMIT=15 INACTIVITY_TIMEOUT=2 PORT=8080 LOG_LEVEL=DEBUG \
flask-cctv-stream
```

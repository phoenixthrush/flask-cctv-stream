# flask-cctv-stream

A minimal Flask-based MJPEG video streaming server with fullscreen responsive client UI, camera auto-open/close logic, frame limiting, and resolution scaling.

## Quick start

```bash
pip install -r requirements.txt  # or your env setup
python -m src.flask_cctv_stream.__main__
# then open http://localhost:8080/
```

## Configuration

You can configure via **CLI args** (highest priority) or **environment variables** (fallback). Defaults are shown below.

**CLI flags**

```
--camera-index   int    Camera index (default 0)
--width          int    Frame width (default 768)
--height         int    Frame height (default 432)
--fps            int    FPS limit (default 10)
--timeout        int    Inactivity timeout seconds (default 1)
--host           str    Bind host (default 0.0.0.0)
--port           int    Bind port (default 8080)
--log-level      str    Logging level (default INFO)
```

**Environment variables** (used when the corresponding flag is not provided)

```
CAMERA_INDEX      FRAME_WIDTH      FRAME_HEIGHT
FPS_LIMIT         INACTIVITY_TIMEOUT
HOST              PORT             LOG_LEVEL
```

## Running with overrides

```bash
python -m src.flask_cctv_stream.__main__ \
  --camera-index 1 --width 1280 --height 720 \
  --fps 15 --timeout 2 --host 0.0.0.0 --port 8080 --log-level DEBUG

# or via env vars
CAMERA_INDEX=0 FRAME_WIDTH=768 FRAME_HEIGHT=432 \
FPS_LIMIT=10 INACTIVITY_TIMEOUT=1 PORT=8080 LOG_LEVEL=INFO \
python -m src.flask_cctv_stream.__main__
```

## Notes

- The built-in server is for development; use a production WSGI server for deployment.
- Close other apps that might lock the camera if you see “Camera not available”.

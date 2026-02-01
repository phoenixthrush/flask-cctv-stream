import argparse
import logging
import os
import threading
import time

import cv2
from flask import Flask, Response, render_template


class CameraManager:
    def __init__(
        self,
        camera_index=0,
        frame_width=1280,
        frame_height=720,
        fps_limit=15,
        inactivity_timeout=1,
        logger=None,
    ):
        self.cap = None
        self.cap_lock = threading.Lock()
        self.last_access = 0
        self.camera_index = camera_index
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps_limit = fps_limit
        self.inactivity_timeout = inactivity_timeout
        self.logger = logger or logging.getLogger(__name__)
        self.watchdog_thread = threading.Thread(
            target=self.camera_watchdog, daemon=True
        )
        self.watchdog_thread.start()

    def open_camera(self):
        with self.cap_lock:
            if self.cap is None or not self.cap.isOpened():
                idx = self.camera_index
                self.cap = cv2.VideoCapture(self.camera_index)
                if not self.cap.isOpened():
                    self.cap = None
                    raise RuntimeError(f"Could not start camera at index {idx}.")
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

    def close_camera(self):
        with self.cap_lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                self.logger.info("Camera closed due to inactivity.")

    def camera_watchdog(self):
        while True:
            time.sleep(1)
            if self.cap is not None:
                if time.time() - self.last_access > self.inactivity_timeout:
                    self.close_camera()

    def generate_frames(self):
        frame_interval = 1.0 / self.fps_limit
        next_frame_time = time.time()
        while True:
            try:
                with self.cap_lock:
                    if self.cap is None:
                        break
                    success, frame = self.cap.read()
                if not success:
                    break
                now = time.time()
                if now < next_frame_time:
                    time.sleep(next_frame_time - now)
                next_frame_time = time.time() + frame_interval
                self.last_access = time.time()
                ret, buffer = cv2.imencode(".jpg", frame)
                if not ret:
                    self.logger.error("Failed to encode frame as JPEG.")
                    break
                frame_bytes = buffer.tobytes()
                yield (
                    b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                    + frame_bytes
                    + b"\r\n"
                )
            except (BrokenPipeError, ConnectionResetError):
                self.logger.info("Client disconnected.")
                break
            except GeneratorExit:
                self.logger.info("Stream generator exited.")
                break
        self.close_camera()


def create_app(
    camera_index: int = 0,
    frame_width: int = 768,
    frame_height: int = 432,
    fps_limit: int = 10,
    inactivity_timeout: int = 1,
):
    app = Flask(__name__)

    camera_manager = CameraManager(
        camera_index,
        frame_width,
        frame_height,
        fps_limit,
        inactivity_timeout,
        app.logger,
    )

    @app.route("/video_feed")
    def video_feed():
        try:
            camera_manager.last_access = time.time()
            camera_manager.open_camera()
            return Response(
                camera_manager.generate_frames(),
                mimetype="multipart/x-mixed-replace; boundary=frame",
            )
        except Exception as e:
            app.logger.error(f"Camera not available: {e}")
            return Response(
                f"Camera not available: {e}", status=503, mimetype="text/plain"
            )

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


def main():
    parser = argparse.ArgumentParser(description="Flask CCTV stream server")
    parser.add_argument(
        "--camera-index",
        type=int,
        default=None,
        help="Camera index (overrides CAMERA_INDEX)",
    )
    parser.add_argument(
        "--width", type=int, default=None, help="Frame width (overrides FRAME_WIDTH)"
    )
    parser.add_argument(
        "--height", type=int, default=None, help="Frame height (overrides FRAME_HEIGHT)"
    )
    parser.add_argument(
        "--fps", type=int, default=None, help="FPS limit (overrides FPS_LIMIT)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Inactivity timeout seconds (overrides INACTIVITY_TIMEOUT)",
    )
    parser.add_argument(
        "--host", default=None, help="Host to bind (overrides HOST, default 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind (overrides PORT, default 8080)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Logging level (overrides LOG_LEVEL, default INFO)",
    )
    args = parser.parse_args()

    log_level = (args.log_level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    camera_index = (
        args.camera_index
        if args.camera_index is not None
        else int(os.environ.get("CAMERA_INDEX", 0))
    )
    frame_width = (
        args.width
        if args.width is not None
        else int(os.environ.get("FRAME_WIDTH", 768))
    )
    frame_height = (
        args.height
        if args.height is not None
        else int(os.environ.get("FRAME_HEIGHT", 432))
    )
    fps_limit = (
        args.fps if args.fps is not None else int(os.environ.get("FPS_LIMIT", 10))
    )
    inactivity_timeout = (
        args.timeout
        if args.timeout is not None
        else int(os.environ.get("INACTIVITY_TIMEOUT", 1))
    )
    host = args.host or os.environ.get("HOST", "0.0.0.0")
    port = args.port if args.port is not None else int(os.environ.get("PORT", 8080))

    app = create_app(
        camera_index=camera_index,
        frame_width=frame_width,
        frame_height=frame_height,
        fps_limit=fps_limit,
        inactivity_timeout=inactivity_timeout,
    )
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()

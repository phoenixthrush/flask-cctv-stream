from flask import Flask, Response
import cv2
import time
import threading

app = Flask(__name__)

cap = None
last_access = 0
fps_limit = 10
cap_lock = threading.Lock()


def open_camera():
    global cap
    with cap_lock:
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                cap = None
                raise RuntimeError("Could not start camera.")

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 768)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 432)


def close_camera():
    global cap
    with cap_lock:
        if cap is not None:
            cap.release()
            cap = None
            print("Camera closed due to inactivity.")


def camera_watchdog():
    global last_access
    while True:
        time.sleep(1)
        if cap is not None:
            if time.time() - last_access > 1:
                close_camera()


threading.Thread(target=camera_watchdog, daemon=True).start()


def generate_frames():
    global last_access

    open_camera()

    frame_interval = 1.0 / fps_limit
    next_frame_time = time.time()

    while True:
        try:
            with cap_lock:
                if cap is None:
                    break
                success, frame = cap.read()

            if not success:
                break

            now = time.time()
            if now < next_frame_time:
                time.sleep(next_frame_time - now)
            next_frame_time = time.time() + frame_interval

            last_access = time.time()

            ret, buffer = cv2.imencode(".jpg", frame)
            frame_bytes = buffer.tobytes()

            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )

        except (BrokenPipeError, ConnectionResetError):
            print("Client disconnected.")
            break

        except GeneratorExit:
            print("Stream generator exited.")
            break

    close_camera()


@app.route("/video_feed")
def video_feed():
    global last_access
    last_access = time.time()
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CCTV</title>
    <style>
        html,
        body {
            height: 100%;
            margin: 0;
        }

        body {
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        img.cctv {
            width: 100vw;
            height: 100vh;
            display: block;
            object-fit: contain;
            object-position: center;
            border: 0;
            user-select: none;
            -webkit-user-drag: none;
        }
    </style>
</head>

<body>
    <img class="cctv" id="stream" src="/video_feed" alt="CCTV Feed">
</body>

</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

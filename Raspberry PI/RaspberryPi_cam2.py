from picamera2 import Picamera2, Preview
import time
import requests
import threading
import cv2
from flask import Flask, request, jsonify,Response


app = Flask(name)

camera_flag = False

Flask_URL = "http://192.168.1.76:5000/upload2"
Flask_capture = "http://192.168.1.76:5000/uploads2"
camera_lock = threading.Lock()

@app.route('/start_stream')
def send_frame():
    global camera_flag
    camera_flag=True
    return jsonify({'msg':'ON'})

@app.route('/stop_stream')
def stop_frame():
    global camera_flag
    if camera_flag==True:
        camera_flag=False
    return jsonify({'msg':'OFF'})

def camera_open():
    global camera_flag
    while True:
        if camera_flag:
            with camera_lock:
                try:
                    picam2 = Picamera2()
                    config = picam2.create_video_configuration(main={"size": (1080, 720), "format": "XBGR8888"})  # ISP 호환 포맷)
                    picam2.configure(config)
                    picam2.set_controls({
                        "FrameDurationLimits" : (16666,16666)
                    })
                    picam2.start()

                    while camera_flag:
                        frame = picam2.capture_array()
                        frame = cv2.cvtColor(frame,cv2.COLORBGR2RGB)
                        ,buf = cv2.imencode('.jpg',frame)

                        files = {'image':('frame.jpg',buf.tobytes(),'image/jpeg')}
                        try:
                            requests.post(Flask_URL,files=files,timeout=1)
                        except Exception as e:
                            print("Image upload failed:",e)
                        time.sleep(0.1)
                except Exception as e:
                    print("Error debug: ",e)
                finally:
                    try:

                        picam2.stop()
                        picam2.close()
                    except Exception as e:
                        pass

def send_frames():
    while True:
        if not camera_flag:
            with camera_lock:
                picam2 = Picamera2()
                config = picam2.create_video_configuration(main={"size": (1080, 720), "format": "XBGR8888"})
                picam2.configure(config)
                picam2.set_controls({"FrameDurationLimits": (16666, 16666)})
                picam2.start()
                frame = picam2.capture_array()
                frame = cv2.cvtColor(frame,cv2.COLORBGR2RGB)
                , buf = cv2.imencode('.jpg', frame)
                files = {'image': ('frame.jpg', buf.tobytes(), 'image/jpeg')}
                try:
                    requests.post(Flask_capture, files=files, timeout=1)

                except Exception as e:
                    print("Image upload failed:", e)
                finally:
                    try:picam2.stop()
                    except: pass
                    try: picam2.close()
                    except:pass

                time.sleep(10)
if name == "main":
    threading.Thread(target=camera_open,daemon=True).start()
    threading.Thread(target=send_frames,daemon=True).start()
    app.run(host='0.0.0.0',port=5050)
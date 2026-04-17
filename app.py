import pickle
import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, render_template, Response, jsonify, request
import logging
import time
from threading import RLock

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Load the model
try:
    model_dict = pickle.load(open('./model.p', 'rb'))
    model = model_dict['model']
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.3
)

labels_dict = {
    0:'A',1:'B',2:'C',3:'D',4:'E',5:'F',6:'G',7:'H',
    8:'I',9:'J',10:'K',11:'L',12:'M',13:'N',14:'O',
    15:'P',16:'Q',17:'R',18:'S',19:'T',20:'U',
    21:'V',22:'W',23:'X',24:'Y',25:'Z'
}

current_prediction = ""
sentence_text = ""
last_prediction = ""
last_appended_prediction = ""
stable_frame_count = 0
camera_status = "starting"
camera_message = "Camera starting"
prediction_lock = RLock()
STABLE_FRAMES_REQUIRED = 15
CAMERA_INDEXES = (0, 1, 2)
CAMERA_BACKENDS = (
    ("DirectShow", cv2.CAP_DSHOW),
    ("MSMF", cv2.CAP_MSMF),
    ("Default", cv2.CAP_ANY),
)


def open_camera():
    global camera_status, camera_message

    for camera_index in CAMERA_INDEXES:
        for backend_name, backend in CAMERA_BACKENDS:
            cap = cv2.VideoCapture(camera_index, backend)
            if cap.isOpened():
                app.logger.info("Opened camera %s using %s backend.", camera_index, backend_name)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                with prediction_lock:
                    camera_status = "online"
                    camera_message = f"Camera {camera_index} active"
                return cap
            cap.release()
    with prediction_lock:
        camera_status = "offline"
        camera_message = "Camera unavailable"
    return None


def update_sentence(predicted_character):
    global current_prediction, sentence_text, last_prediction
    global last_appended_prediction, stable_frame_count

    with prediction_lock:
        current_prediction = predicted_character
        if predicted_character == last_prediction:
            stable_frame_count += 1
        else:
            last_prediction = predicted_character
            stable_frame_count = 1

        if (
            stable_frame_count >= STABLE_FRAMES_REQUIRED
            and predicted_character != last_appended_prediction
        ):
            sentence_text += predicted_character
            last_appended_prediction = predicted_character


def reset_prediction_state():
    global current_prediction, last_prediction, last_appended_prediction, stable_frame_count

    with prediction_lock:
        current_prediction = ""
        last_prediction = ""
        last_appended_prediction = ""
        stable_frame_count = 0


def predict_from_frame(frame, draw_on_frame=False):
    global current_prediction

    if model is None:
        with prediction_lock:
            current_prediction = "Model unavailable"
        return ""

    data_aux = []
    x_ = []
    y_ = []
    H, W, _ = frame.shape
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if not results.multi_hand_landmarks:
        reset_prediction_state()
        return ""

    for hand_landmarks in results.multi_hand_landmarks:
        if draw_on_frame:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

        for landmark in hand_landmarks.landmark:
            x_.append(landmark.x)
            y_.append(landmark.y)

        for landmark in hand_landmarks.landmark:
            data_aux.append(landmark.x - min(x_))
            data_aux.append(landmark.y - min(y_))

    if len(data_aux) != 42:
        reset_prediction_state()
        return ""

    prediction = model.predict([np.asarray(data_aux)])
    predicted_character = labels_dict[int(prediction[0])]
    update_sentence(predicted_character)

    if draw_on_frame and x_ and y_:
        x1 = int(min(x_) * W) - 10
        y1 = int(min(y_) * H) - 10
        x2 = int(max(x_) * W) + 10
        y2 = int(max(y_) * H) + 10
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
        cv2.putText(frame, predicted_character, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3, cv2.LINE_AA)

    return predicted_character


def camera_error_frames():
    while True:
        with prediction_lock:
            current_message = camera_message

        frame = np.full((480, 640, 3), (247, 251, 255), dtype=np.uint8)
        cv2.rectangle(frame, (36, 48), (604, 432), (15, 118, 110), 2)
        cv2.putText(frame, current_message, (72, 170),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (16, 32, 51), 2, cv2.LINE_AA)
        cv2.putText(frame, "Close other camera apps", (72, 235),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 116, 139), 2, cv2.LINE_AA)
        cv2.putText(frame, "and allow desktop camera access.", (72, 275),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 116, 139), 2, cv2.LINE_AA)

        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(1)

def gen_frames():
    global current_prediction, camera_status, camera_message
    cap = open_camera()
    if cap is None:
        app.logger.error("Could not open webcam.")
        with prediction_lock:
            current_prediction = "Camera unavailable"
        yield from camera_error_frames()
        return
    
    while True:
        data_aux = []
        x_ = []
        y_ = []

        ret, frame = cap.read()
        if not ret:
            app.logger.warning("Could not read frame from webcam.")
            with prediction_lock:
                camera_status = "offline"
                camera_message = "Camera stopped"
            break

        H, W, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame with mediapipe
        results = hands.process(frame_rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

            for hand_landmarks in results.multi_hand_landmarks:
                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y
                    x_.append(x)
                    y_.append(y)

                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y
                    data_aux.append(x - min(x_))
                    data_aux.append(y - min(y_))

            if len(x_) > 0 and len(y_) > 0:
                x1 = int(min(x_) * W) - 10
                y1 = int(min(y_) * H) - 10
                x2 = int(max(x_) * W) - 10
                y2 = int(max(y_) * H) - 10

                try:
                    if model is not None:
                        if len(data_aux) != 42:
                            current_prediction = ""
                            continue

                        prediction = model.predict([np.asarray(data_aux)])
                        predicted_character = labels_dict[int(prediction[0])]
                        update_sentence(predicted_character)

                        # Draw bounding box and text
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
                        cv2.putText(frame, predicted_character, (x1, y1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3, cv2.LINE_AA)
                except Exception as e:
                    app.logger.exception("Model prediction failed: %s", e)
                    reset_prediction_state()
        else:
            reset_prediction_state()

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
               
    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/current_prediction')
def get_prediction():
    with prediction_lock:
        return jsonify({
            "character": current_prediction,
            "sentence": sentence_text,
            "stable_frames": stable_frame_count,
            "camera_status": camera_status,
            "camera_message": camera_message
        })

@app.route('/predict_frame', methods=['POST'])
def predict_frame():
    global camera_status, camera_message

    uploaded_frame = request.files.get('frame')
    if uploaded_frame is None:
        return jsonify({"error": "No frame uploaded"}), 400

    frame_bytes = np.frombuffer(uploaded_frame.read(), np.uint8)
    frame = cv2.imdecode(frame_bytes, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "Invalid frame"}), 400

    with prediction_lock:
        camera_status = "online"
        camera_message = "Browser camera active"

    try:
        predict_from_frame(frame)
    except Exception as e:
        app.logger.exception("Browser frame prediction failed: %s", e)
        reset_prediction_state()
        return jsonify({"error": "Prediction failed"}), 500

    with prediction_lock:
        return jsonify({
            "character": current_prediction,
            "sentence": sentence_text,
            "stable_frames": stable_frame_count,
            "camera_status": camera_status,
            "camera_message": camera_message
        })

@app.route('/sentence/space', methods=['POST'])
def add_space():
    global sentence_text
    with prediction_lock:
        if sentence_text and not sentence_text.endswith(' '):
            sentence_text += ' '
        reset_prediction_state()
        return jsonify({"sentence": sentence_text})

@app.route('/sentence/backspace', methods=['POST'])
def backspace_sentence():
    global sentence_text
    with prediction_lock:
        sentence_text = sentence_text[:-1]
        reset_prediction_state()
        return jsonify({"sentence": sentence_text})

@app.route('/sentence/clear', methods=['POST'])
def clear_sentence():
    global sentence_text
    with prediction_lock:
        sentence_text = ""
        reset_prediction_state()
        return jsonify({"sentence": sentence_text})

if __name__ == '__main__':
    # Threaded=True is important for MJPEG streaming
    app.run(debug=True, threaded=True, use_reloader=False)

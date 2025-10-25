import cv2
import mediapipe as mp
import time
import socket

ESP32_IP = '192.168.4.1'
ESP32_PORT = 1234

def connect_esp32():
    while True:
        try:
            esp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            esp_socket.connect((ESP32_IP, ESP32_PORT))
            print(f"[INFO] Connected to ESP32 at {ESP32_IP}:{ESP32_PORT}")
            return esp_socket
        except Exception as e:
            print("[ERROR] Could not connect to ESP32, retrying in 3 seconds:", e)
            time.sleep(3)

esp_socket = connect_esp32()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils


def is_thumb_open(hand_landmarks, hand_label):
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]
    return thumb_tip.x > thumb_ip.x if hand_label == "Right" else thumb_tip.x < thumb_ip.x

def is_indexfinger_open(hand_landmarks, hand_label):
    index_tip = hand_landmarks.landmark[8]
    index_pip = hand_landmarks.landmark[6]
    return index_tip.x < index_pip.x if hand_label == "Right" else index_tip.x > index_pip.x

def count_extended_fingers(hand_landmarks):
    fingers = [(12, 10), (16, 14), (20, 18)]  # Index, Middle, Ring, Pinky
    return sum([hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y for tip, pip in fingers])


left_thumb_closed = False
right_thumb_closed = False
left_index_closed = False
right_index_closed = False
got_displayed = False
timer_started = False
start_time = None
last_command=None


cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    hand_count = 0
    palm_open_detected = False

    if results.multi_hand_landmarks and results.multi_handedness:
        hand_count = len(results.multi_hand_landmarks)

        for idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
            mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            hand_label = handedness.classification[0].label

            # Thumb and index logic
            thumb_open = is_thumb_open(hand_landmarks, hand_label)
            index_open = is_indexfinger_open(hand_landmarks, hand_label)

            if hand_label == "Left":
                left_thumb_closed = not thumb_open
                left_index_closed = not index_open
            elif hand_label == "Right":
                right_thumb_closed = not thumb_open
                right_index_closed = not index_open

            # Palm detection logic (≥3 fingers extended)
            extended_count = count_extended_fingers(hand_landmarks)
            if extended_count >= 3:
                palm_open_detected = True
    # ======== TIMER LOGIC ========
    if not got_displayed:
        if (hand_count == 2 and left_thumb_closed and right_thumb_closed and left_index_closed and right_index_closed):
            if not timer_started:
                start_time = time.time()
                timer_started = True
        else:
            timer_started = False
            start_time = None

    if timer_started:
        elapsed = time.time() - start_time
        remaining = 3 - int(elapsed)
        if remaining > 0:
            cv2.putText(img, f"Starting in: {remaining}", (150, 400),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
        else:
            if not got_displayed:
                go_start_time = time.time()
                got_displayed = True
            if time.time() - go_start_time < 1:
                cv2.putText(img, "Go!", (250, 400),
                            cv2.FONT_HERSHEY_COMPLEX, 1.5, (0, 255, 0), 4)
            else:
                got_displayed = True
                timer_started = False
                start_time = None

    # ======== COMMAND LOGIC ========
    if got_displayed and hand_count == 2:
        try:
            commamd=None
            if palm_open_detected:
                # print("stop")
                commamd="S"
            elif left_index_closed and left_thumb_closed and right_thumb_closed and left_thumb_closed:
                # print("straight with 10")
                commamd="F"
            elif left_thumb_closed and not right_thumb_closed and left_index_closed and right_index_closed:
                # print("turn Right with 10")
                commamd="R"
            elif right_thumb_closed and not left_thumb_closed and left_index_closed and right_index_closed:
                # print("turn Left with 10")
                commamd="L"
            elif left_thumb_closed and right_thumb_closed and right_index_closed and not left_index_closed:
                # print("speed now 30")
                commamd="I"
            elif left_thumb_closed and right_thumb_closed and not right_index_closed and left_index_closed:
                # print("speed now 20")
                commamd = "D"
            elif not left_thumb_closed and not right_thumb_closed and left_index_closed and right_index_closed:
                # print("reverse with 100")
                commamd="B"
        except Exception as e:
            print("Failed to send command:", e)
        
        if commamd and commamd != last_command:
            try:
                    esp_socket.sendall(commamd.encode())
                    print(f"[INFO] Sent command: {commamd.strip()}")
                    last_command = commamd
            except Exception as e:
                    print("[ERROR] Sending command failed:", e)
                    esp_socket.close()
                    esp_socket = connect_esp32()
                    last_command = None
    elif got_displayed and hand_count== 0:
        if last_command != "S":
            try:
                esp_socket.sendall("S".encode())
                # print("[INFO] Sent command: S (No hands detected)")
                last_command = "S"
            except Exception as e:
                # print("[ERROR] Sending stop command failed:", e)
                esp_socket.close()
                esp_socket = connect_esp32()
                last_command = None

            
    cv2.imshow("Gesture + Palm Stop Detection", img)
    

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
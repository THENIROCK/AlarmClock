from pydoc import doc
import socket
import serial
import cv2
import mediapipe
import time


class UDP:  # we'll be using UDP to communicate with the wifi enabled lamp
    def __init__(self, ip):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = (ip, 38899)

    def call(self, message):
        self.sock.sendto(bytes(message), self.addr)
        data, _ = self.sock.recvfrom(1024)
        return data


# set up light
IP = '192.168.1.234'
udp = UDP(IP)

# set up arduino communication
serialComm = serial.Serial('COM3', 9600)
serialComm.timeout = 0.1

# set up hand tracking
mp_drawing = mediapipe.solutions.drawing_utils
mp_hands = mediapipe.solutions.hands
hands = mp_hands.Hands()
cap = cv2.VideoCapture(2)

time.sleep(1)

# main loop
while True:
    serialIn = serialComm.readline().decode().strip()
    print(serialIn)

    success, img = cap.read()
    cv2.imshow("Never Sleep Alarm Clock", img)
    cv2.waitKey(1)

    if (serialIn == 'turn on light'):
        udp.call(b'{"method": "setPilot", "params":{"state": true}}')

        while True:
            success, img = cap.read()

            height, width, center = img.shape  # OpenCV screen dimensions

            if not success:
                break

            result = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

            # draw landmarks on hand
            if result.multi_hand_landmarks:
                for hand_landmark in result.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(img, hand_landmark)

                # get coordinates of hand landmarks (joints)
                for id, landmark in enumerate(hand_landmark.landmark):
                    # print(id, landmark)
                    # note that id 9 is your middle knuckle
                    # get position and label middle knuckle (id 9)
                    if id == 9:
                        x, y = int(landmark.x*width), int(landmark.y*height)
                        cv2.putText(img, str(x)+", "+str(y), (x, y),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 255), 3)
                        # move servo to avoid hand
                        if (x < 0):
                            serialComm.write(
                                ('<'+str(0)+'>\n').encode('utf-8'))
                        elif (landmark.x < 0.9 and landmark.x > 0.5):
                            serialComm.write(
                                ('<'+str(180)+'>\n').encode('utf-8'))
                        elif (landmark.x < 0.5 and landmark.x > 0.1):
                            serialComm.write(
                                ('<'+str(0)+'>\n').encode('utf-8'))
                        else:
                            serialComm.write(
                                ('<'+str(180 - int((landmark.x * 180)))+'>\n').encode('utf-8'))

            cv2.imshow("Never Sleep Alarm Clock", img)
            cv2.waitKey(1)

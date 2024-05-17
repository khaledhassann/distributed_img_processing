import numpy as np
import cv2
import socket

def imageBlur(image):
    blurred = cv2.GaussianBlur(image, (15, 15), 0)
    return blurred

def edgeDetection(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return edges


def colorInversion(image):
    inverted = cv2.bitwise_not(image)
    return inverted

def convertToGrayscale(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray

HOST = '0.0.0.0'
PORT = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSocket:
    serverSocket.bind((HOST, PORT))
    serverSocket.listen(1)
    print("Server listening on port", PORT)

    while True:
        conn, addr = serverSocket.accept()
        print('Connected by', addr)

        with conn:
            conn.settimeout(5)

            try:
                operation = conn.recv(1024).decode('utf-8')
                print(f"Command received: {operation}")

                data = b""
                while True:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    data += chunk

                nparr = np.frombuffer(data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                print("Image received and processing...")

                if operation == 'edges':
                    processed_image = edgeDetection(image)
                elif operation == 'blur':
                    processed_image = imageBlur(image)
                elif operation == 'invert':
                    processed_image = colorInversion(image)
                elif operation == 'grayscale':
                    processed_image = convertToGrayscale(image)
                else:
                    processed_image = image

                if operation == 'grayscale':
                    _, encoded_image = cv2.imencode('.jpg', processed_image)
                else:
                    _, encoded_image = cv2.imencode('.jpg', processed_image)

                processed_data = encoded_image.tobytes()
                conn.sendall(processed_data)
                print("Processed image sent back to client")
            except socket.timeout:
                print("Socket timeout: No data received from client.")
            except Exception as e:
                print("Error:", e)
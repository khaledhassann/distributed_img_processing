from flask import Flask, send_from_directory
from werkzeug.utils import secure_filename
import os
import time
import json
import base64
import cv2


def process_images(msg):
    # msg = [{image: , operation} , ... ]

    request_headers = {
    'Content-Type': 'application/json'
    }

    # Construct the JSON object
    payload_data = {}
    i = 0
    for entry in msg:
        script_dir = os.path.dirname(__file__)  # Get script's directory
        final_path = os.path.join(script_dir, 'static/images/', entry['image'])
        encoded_img = get_base64_encoded_image(final_path)
        img_payload = {'operation': entry['operation'], 'image': encoded_img}
        payload_data.update({f'image{i}': img_payload})
        i += 1

    image_payload_body={
                  "number_of_images":i,
                  "images":payload_data
                  }
    
    zip_folder_processed = process_images_remotely(image_payload_body)
    return zip_folder_processed

    # response = requests.post(url=CAMERA_FEED_URL, json=image_payload_body, headers=request_headers, auth=(USERNAME, PASSWORD))

    # return  image

def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')
    

def process_images_remotely(image_payload_body):
    num_of_images = image_payload_body['number_of_images']
    payload_data = image_payload_body['images']
    operations = []
    images = []

    for i in range(num_of_images):
        operations.append(payload_data[f'image{i}']['operation'])
        images.append(payload_data[f'image{i}']['image'])

    # for img_data in payload_data:
    #     print()
    #     # operations.append(img_data['operation'])
    #     # images.append(img_data['image'])
    
    for i in range(len(operations)):
        print(operations[i], images[i])

    return cv2.imread('connecting-ill.png', cv2.IMREAD_COLOR)




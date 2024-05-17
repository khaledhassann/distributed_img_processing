import threading
import queue
from mpi4py import MPI  # MPI for distributed computing
import io  
import os
import socket
import cv2
import numpy as np
from PIL import Image
import boto3
import time

# Constants
BUFFER_SIZE = 4096

class ImageWorker(threading.Thread):
    def __init__(self, comm, task_queue):
        super().__init__()
        self.task_queue = task_queue
        self.comm = comm

    def run(self):
        while True:
            try:
                task = self.task_queue.get()
                if task is None:  # Termination signal
                    break
                image, operation_code = task
                result = self.perform_operation(image, operation_code)
                print(f"Worker {self.comm.Get_rank()} processed the image")
                self.comm.send(result, dest=0)
            except Exception as e:
                print(f"Error in worker {self.comm.Get_rank()}: {e}")
                continue

    def perform_operation(self, image, operation_code):
        try:
            if operation_code == 1:
                return self.edgeDetection(image)
            elif operation_code == 2:
                return self.imageBlur(image)
            elif operation_code == 3:
                return self.convertToGrayscale(image)
            elif operation_code == 4:
                return self.colorInversion(image)
            else:
                raise ValueError(f"Unknown operation code: {operation_code}")
        except Exception as e:
            print(f"Error during image processing: {e}")
            return None
        
    def imageBlur(self, img, ksize=(5, 5)):
        try:
            blurred_image = cv2.GaussianBlur(img, ksize, 0)
            return Image.fromarray(blurred_image)
        except Exception as e:
            print(f"Blurring error: {e}")
            return None

    def edgeDetection(self, img, threshold1=90, threshold2=180):
        try:
            gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray_image, threshold1, threshold2)
            return Image.fromarray(edges)
        except Exception as e:
            print(f"Edge detection error: {e}")
            return None
        
    def colorInversion(self, img):
        try:
            inverted_image = cv2.bitwise_not(img)
            return Image.fromarray(inverted_image)
        except Exception as e:
            print(f"Color inversion error: {e}")
            return None

    def convertToGrayscale(self, img):
        try:
            gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return Image.fromarray(gray_image)
        except Exception as e:
            print(f"Grayscale conversion error: {e}")
            return None


def handle_client(client_socket, task_queue):
    try:
        recv_data = client_socket.recv(BUFFER_SIZE)
        file_stream = io.BytesIO(recv_data)
       
        while b'###%Image_End%' not in recv_data:
            recv_data = client_socket.recv(BUFFER_SIZE)
            file_stream.write(recv_data)
            if b"###%Image_Sent%" in recv_data:
                task_data = recv_data.split(b"###")
                if task_data[0]:
                    file_stream.write(task_data[0])
                client_socket.send(b"File received")
                operation = client_socket.recv(BUFFER_SIZE)
                image_data = np.frombuffer(file_stream.getvalue(), dtype=np.uint8)
                image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                task_queue.put((image, int(operation)))
                file_stream = io.BytesIO()
               
        task_queue.put(None)  # Signal completion
    except Exception as e:
        print(f"Client handling error: {e}")

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    hostname = MPI.Get_processor_name()
    print(f"Rank: {rank}, Hostname: {hostname}")

    try:
        if rank == 0:
            server_main(comm)
        else:
            worker_main(comm)
    except Exception as e:
        print(f"Main error: {e}")

def server_main(comm):
    task_queue = queue.Queue()
    processed_images = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 55552))
    server_socket.listen()
    print("Server is waiting for connections...")

    while True:
        try:
            client_socket, _ = server_socket.accept()
            print(f"Client {client_socket.getpeername()} connected.")
            threading.Thread(target=handle_client, args=(client_socket, task_queue)).start()
           
            num_workers = comm.Get_size()
            healthy_workers = [i for i in range(1, num_workers) if checkInstanceHealth(i)]
            if not healthy_workers:
                createNewInstance()
                num_workers = comm.Get_size()
                healthy_workers = [i for i in range(1, num_workers) if checkInstanceHealth(i)]

            while not task_queue.empty():
                for worker in healthy_workers:
                    task = task_queue.get()
                    if task is None:
                        break
                    comm.send(task, dest=worker)
                    print(f"Task sent to worker {worker}")

            for worker in healthy_workers:
                image = comm.recv(source=worker)
                processed_images.append(image)
                image.save(f'processed_image_{worker}.jpeg', format='JPEG')
                print(f"Processed image from worker {worker} saved.")

            sendProcessedImages(client_socket, processed_images)
        except Exception as e:
            print(f"Server main loop error: {e}")

def worker_main(comm):
    try:
        while True:
            task = comm.recv(source=0)
            if task is None:
                break
            processor = ImageWorker(comm, task)
            processor.start()
            processor.join()
    except Exception as e:
        print(f"Worker error: {e}")

def sendProcessedImages(client_socket, images):
    try:
        for idx, img in enumerate(images):
            with open(f'processed_image_{idx}.jpeg', 'rb') as file:
                file_data = file.read(BUFFER_SIZE)
                while file_data:
                    client_socket.send(file_data)
                    file_data = file.read(BUFFER_SIZE)
                client_socket.send(b"###%Image_Sent%")
                if client_socket.recv(BUFFER_SIZE) == b"I got the file":
                    print(f"Processed image {idx + 1} sent back to client.")
    except Exception as e:
        print(f"Error sending processed images: {e}")

def createNewInstance():
    ec2 = boto3.resource('ec2')
    instance = ec2.create_instances(
        ImageId='ami-0abcdef1234567890',  # Here we're passing our AMI ID
        InstanceType='t2.micro',  # Here we're passing our desired instance type (t2.micro as it's the free tier eligible)
        MinCount=1,
        MaxCount=1,
        KeyName='my-key-pair',  # Here we're passing our key-pair name
        SecurityGroupIds=['sg-0abcdef1234567890'],  # Here we're passing our security group ID
        SubnetId='subnet-0abcdef1234567890',  # Here we're passing our subnet ID
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'MPI-Worker'
                    },
                ]
            },
        ],
    )
    instance_id = instance[0].id
    print(f'Created EC2 instance with ID: {instance_id}')
   
    # Wait until the instance is running
    instance[0].wait_until_running()
    instance[0].reload()
    print(f'Instance {instance_id} is running')

def checkInstanceHealth(instance_id):
    ec2 = boto3.client('ec2')
    response = ec2.describe_instance_status(InstanceIds=[instance_id])
    instance_statuses = response.get('InstanceStatuses', [])
    if not instance_statuses:
        return False
    instance_status = instance_statuses[0]
    return (instance_status['InstanceState']['Name'] == 'running' and
            instance_status['InstanceStatus']['Status'] == 'ok' and
            instance_status['SystemStatus']['Status'] == 'ok')

if __name__ == "__main__":
    main()
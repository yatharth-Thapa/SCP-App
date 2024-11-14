import platform
import subprocess
import os
import sys
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import pydicom
import urllib3
import shutil
from pathlib import Path
import stat
from requests.auth import HTTPBasicAuth



requests.urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

print(platform.system())


class FileHandler(FileSystemEventHandler):
    def __init__(self, output_dir, token, client_id, branch_id, user_id):
        self.output_dir = output_dir
        self.token = token
        self.client_id = client_id
        self.branch_id = branch_id
        self.user_id = user_id

    def on_created(self, event):
        if not event.is_directory and (event.src_path.endswith(".dcm") or event.src_path.endswith(".DCM")):
            self.handle_file(event.src_path)

    def handle_file(self, file_path):
        try:
            self.set_write_access(file_path)
            

            # Process the study immediately once file is created
            self.process_study( file_path)

        except Exception as e:
            print(f"Error handling file: {file_path}, Error: {e}")

    def process_study(self, file_path):
        try:
            # study_dir = os.path.join(self.output_dir, study_instance_uid)
            # os.makedirs(study_dir, exist_ok=True)
            # logging.info(f"created directory {study_dir}")
            
            # Define new file paths
            # new_file_path = os.path.join(study_dir, os.path.basename(file_path))
            # optimize_new_file_path = os.path.join("optimized_" + os.path.basename(file_path))

            # Move the original DICOM file to the new directory
            # shutil.move(file_path, new_file_path)
            # logging.info(f"Moved dicom file to: {new_file_path}")
           

            # Ensure the file is writable
            self.set_write_access(file_path)
            # self.set_write_access(optimize_new_file_path)

            # Compress the DICOM file
            # self.compress_dicom_with_gdcm(input_dcm=file_path, output_dcm=optimize_new_file_path)

            # Send the optimized file to the PACS server
            self.send_file(file_path)
            # self.send_file(new_file_path)
            
            # Clean up the files and directories
            # if os.path.isfile(optimize_new_file_path):
            #     os.remove(optimize_new_file_path)
                
            if os.path.isfile(file_path):
                os.remove(file_path)
               

            # Check if the directory is empty before attempting to remove it
            # if not os.listdir(self.output_dir):
            #     os.rmdir(self.output_dir)
                

           
        except Exception as e:
            print(e)
            
            
    def send_file(self, file_path):
        try:
            url = 'https://dev-api.smaro.app/api/console/orthanc/upload'
            token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoic3dhbWkiLCJpZCI6MTcsImVtYWlsIjoic3dhbWlAZ21haWwuY29tIiwibW9iaWxlIjoiNzY1NDMxMjM0NSIsImlhdCI6MTcyNjIyMjczOSwiZXhwIjoxNzI2MzA5MTM5fQ.nvvtzw40qYCgWYz3rxNkG0b1e88FxmGC_u_S3BHjU0Q'

            headers = {
                'token': token,
            }

            files = {
                'file': open(file_path, 'rb')
            }

            data = {
                'client_id': self.client_id,
                'branch_id': self.branch_id
            }

            requests.post(url, headers=headers, files=files, data=data)

            
        except Exception as e:
            return False
    
    def compress_dicom_with_gdcm(self, input_dcm, output_dcm, compression_type="jpeg"):
        compression_flag = ""
        if compression_type == "jpeg":
            compression_flag = "--j2k"
        elif compression_type == "jpegls":
            compression_flag = "--jpegls"
        elif compression_type == "rle":
            compression_flag = "--rle"
        else:
            raise ValueError(f"Unsupported compression type: {compression_type}")
        
        cmd = ["gdcmconv", compression_flag, "--lossy", input_dcm, output_dcm]
        
        try:
            subprocess.run(cmd, check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to compress {input_dcm}")
            print(e)

    def set_write_access(self, folder_path):
        system = platform.system()
        if system == "Windows":
            for root, dirs, files in os.walk(folder_path):
                for dir_name in dirs:
                    os.chmod(os.path.join(root, dir_name), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                for file_name in files:
                    os.chmod(os.path.join(root, file_name), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
          
        else:
            for root, dirs, files in os.walk(folder_path):
                for dir_name in dirs:
                    os.chmod(os.path.join(root, dir_name), 0o775)
                for file_name in files:
                    os.chmod(os.path.join(root, file_name), 0o775)
            


def start_storescp(port, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    os.environ["DCMDICTPATH"] = "dcmtk/share/dcmtk-3.6.8/dicom.dic"
    command = [
        "./dcmtk/bin/storescp",
        str(port),
        "--filename-extension",
        ".dcm",
        "--output-directory",
        output_dir,
        "--max-pdu",        
        "46726",
        "+xa",
        "+B",
    ]

    storescp_process = subprocess.Popen(command)
  
    return storescp_process


def stop_storescp(storescp_process):
    storescp_process.terminate()
    storescp_process.wait()
 


def start_monitoring(output_dir, token, client_id, branch_id, user_id):
    event_handler = FileHandler(output_dir, token, client_id, branch_id, user_id)
    observer = Observer()
    observer.schedule(event_handler, path=output_dir, recursive=True)
    observer.start()


    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# Example usage
if __name__ == "__main__":
    token = sys.argv[1]
    client_id = sys.argv[2]
    branch_id = sys.argv[3]
    user_id = sys.argv[4]
    port = 11114  # Port to listen on
    output_dir = "./output/"  # Directory to store received DICOM files
    storescp_process = start_storescp(port, output_dir)
   
    start_monitoring(output_dir, token, client_id, branch_id, user_id)
    stop_storescp(storescp_process)
    

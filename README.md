# 🚗Campus vehicle logging Web application
## 📋Project Overview
  The Automatic Number Plate Recognition (ANPR) system is designed to automate the detection and recognition of vehicle license plates. This project leverages the YOLOv8 object detection model, EasyOCR for character recognition, and SORT for object tracking. It is suitable for environments like schools, colleges, and organizational campuses to monitor vehicle entry and exit activities in real time.

## ✨Key Features
  1.Vehicle and License Plate Detection: Uses YOLOv8 for robust object detection.<br>
  2.License Plate Character Recognition: EasyOCR reads and extracts license plate numbers.<br>
  3.Tracking System: SORT is used for tracking vehicles between frames.<br>
  4.Real-Time Monitoring: Displays vehicle in/out timestamps dynamically on a webpage.<br>
  5.Data Persistence: Vehicle entry/exit details are stored in a database for future reference.<br>
  6.User Authentication: Web interface includes a login page for secure access.<br>
  7.Automatic Updates: Real-time data updates with a self-refreshing webpage.
## 🛠️Technologies Used
  Frontend: HTML, CSS, JavaScript<br>
  Backend: Python (Flask)<br>
  Database: MySQL for storing vehicle data<br>
  Object Detection: YOLOv8(nano)<br>
  Character Recognition: EasyOCR<br>
  Object Tracking: SORT (Simple Online Realtime Tracking)<br>
## 🚀 How It Works
### Detection:
  1.YOLOv8 detects vehicles and license plates from video feeds.<br>
  2.Bounding boxes are interpolated for better accuracy.<br>
### Recognition:
  1.EasyOCR reads the license plate text.<br>
  2.Valid license plate numbers are stored after format validation.<br>
### Tracking:
  SORT tracks vehicles between consecutive frames to ensure accurate timestamping.
### Data Management:
  1.Entry and exit timestamps are recorded in a database.<br>
  2.Vehicle data is dynamically updated and displayed on a user-friendly webpage.<br>
  
### Web Interface:
  Admins can view vehicle entry/exit details and filter records by date or vehicle number.

## 🔧 Installation and Setup
### *** Make sure to create a folder named static in your current working dir!! ***
### Prerequisites
### Python 3.8 or later
### CUDA (for GPU acceleration, optional but recommended)
### Virtual environment tools (e.g., venv, conda)

from ultralytics import YOLO
import cv2
import numpy as np
import util
from sort import sort
from util import get_car, read_license_plate, write_csv
from datetime import datetime

results = {}

mot_tracker = sort.Sort()

# load models
coco_model = YOLO('yolov8n.pt')
license_plate_detector = YOLO(r"C:\Users\ASUS\OneDrive\Desktop\S7\anpr\model\best.pt")


import sys
video_path = sys.argv[1]  # Get the video path from command-line arguments
print(video_path)
cap = cv2.VideoCapture(video_path)

vehicles = [2, 3, 5, 6, 7]

# read frames
frame_nmr = -1
ret = True
while ret:
    frame_nmr += 1
    ret, frame = cap.read()
    if ret:
        results[frame_nmr] = {}
        # detect vehicles
        detections = coco_model(frame)[0]
        detections_ = []
        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            if int(class_id) in vehicles:
                detections_.append([x1, y1, x2, y2, score])

        # track vehicles
        track_ids = mot_tracker.update(np.asarray(detections_))

        # detect license plates
        license_plates = license_plate_detector(frame)[0]
        for license_plate in license_plates.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = license_plate

            # assign license plate to car
            xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)

            if car_id != -1:

                # crop license plate
                license_plate_crop = frame[int(y1):int(y2), int(x1): int(x2), :]

                # process license plate
                license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
                _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY_INV)

                # read license plate number
                license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop_thresh)

                if license_plate_text is not None:
                    time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    results[frame_nmr][car_id] = {'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                                                  'license_plate': {'bbox': [x1, y1, x2, y2],
                                                                    'text': license_plate_text,
                                                                    'bbox_score': score,
                                                                    'text_score': license_plate_text_score,},
                                                  'timestamp':time}

                    # Visualization: draw vehicle bounding box
                    cv2.rectangle(frame, (int(xcar1), int(ycar1)), (int(xcar2), int(ycar2)), (0, 255, 0), 2)

                    # Visualization: draw license plate bounding box
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)

                    # Visualization: put license plate text
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(frame, license_plate_text, (int(x1), int(y1) - 10), font, 0.9, (0, 0, 255), 2)

        # Display frame with annotations
        cv2.imshow('Frame', frame)

        # Exit condition
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# write results
write_csv(results, './pipeline/test.csv')
from add_missing_data import missing
missing()
from maxsort import maxplate
maxplate()
cap.release()
cv2.destroyAllWindows()

from flask import Flask, request
import cv2
import easyocr
import re
from collections import Counter
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)


numberPlate_cascade = "numberplate_haarcade.xml"
detector = cv2.CascadeClassifier(numberPlate_cascade)
reader = easyocr.Reader(['en'])

list1 = []
list2 = []


def find_most_repeated_item(lst):
    counter = Counter(lst)
    # print(counter)
    most_common = counter.most_common(1)
    # print(most_common)
    return most_common[0][0] if most_common else None

def filter_text(text):
    # Remove non-alphanumeric characters and convert to uppercase
    filtered_text = re.sub(r'[^A-Z0-9]', '', text.upper())
    return filtered_text

def read_frames(video_path):
    # Open the video file
    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        print("Error opening video file:", video_path)
        return

    # Get the frames per second (fps) of the video
    fps = video.get(cv2.CAP_PROP_FPS)

    # Initialize variables
    frame_count = 0
    current_second = -1
    frames_in_second = 0

    while True:
        # Read the next frame
        success, frame = video.read()

        # Break the loop if no more frames are available
        if not success or cv2.waitKey(1) == 27:
            break

        #current frame's timestamp in milliseconds
        current_frame_msec = video.get(cv2.CAP_PROP_POS_MSEC)

        # Calculating the current second 
        current_second = int(current_frame_msec / 1000)

        # process 8 seceond only
        if current_second > frame_count:
            frame_count = current_second
            frames_in_second = 0

        if frames_in_second < 10:
            
            img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            plates = detector.detectMultiScale(img_gray,scaleFactor=1.05, minNeighbors=7,minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)
        # continue if no plate detected
            if len(plates) == 0:
                continue
            for (x,y,w,h) in plates:

            # draw bounding box
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Crop the numberplate
                plateROI = frame[y:y+h,x:x+w]
                # cv2.imshow("Numberplate", plateROI)
                # cv2.waitKey(1)
            # preprocess image
            # plate = process(plateROI)
            # detect text

            result = reader.readtext(plateROI)
            # text=pytesseract.image_to_string(plateROI,lang='eng')
                # print("Number is : ",text)
            for detection in result:
                text = detection[1]
                filtered_text = filter_text(text)
                # print(filtered_text)
                list1.append(filtered_text)
            if len(list1) == 10:
                most_repeated = find_most_repeated_item(list1)
                if len(most_repeated) ==6 :
                    list2.append(most_repeated)
                list1.clear()


            # if len(text) == 0:
            #     continue
            # print(text)
            # print(text[0][1])
        frames_in_second += 1
        
    # Release the video object and close any open windows
    video.release()
    # cv2.destroyAllWindows()
    # for i in list2:
    #     return i
    return list2
    




@app.route('/process_video', methods=['POST'])
def process_video():
    try :
        # Access the uploaded file using the 'request' object
        video_file = request.files['file']

        save_path = 'videos/'

        # Create the save directory if it doesn't exist
        os.makedirs(save_path, exist_ok=True)

        # Generate a unique filename for the video
        filename = secure_filename(video_file.filename)
        video_path = os.path.join(save_path, filename)

        # Save the video file to the server
        video_file.save(video_path)

        # Process the video using the Haar cascade
        result = read_frames(video_path)

        result_str = '\n'.join(str(item) for item in result)

        # Return the processed string response
        return result_str

    except FileNotFoundError:
        # Handle the case where the video file is not found
        return "Video file not found.", 404

    except Exception as e:
        # Handle any other exception that may occur
        return str(e), 500


if __name__ == '__main__':
    app.run(debug=True)
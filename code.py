import cv2
import face_recognition
import sys
from tqdm import tqdm
import pickle
import pandas as pd
from datetime import datetime
import os
from threading import Thread
import sys
import time

if sys.version_info >= (3, 0):
	from queue import Queue
# otherwise, import the Queue class for Python 2.7
else:
	from Queue import Queue

class WebcamStream :
    # initialization method 
    def _init_(self, stream_id=0):
        self.stream_id = stream_id # default is 0 for main camera 
        
        # opening video capture stream 
        self.vcap      = cv2.VideoCapture(self.stream_id)
        if self.vcap.isOpened() is False :
            print("[Exiting]: Error accessing webcam stream.")
            exit(0)
        fps_input_stream = int(self.vcap.get(5)) # hardware fps
        print("FPS of input stream: {}".format(fps_input_stream))
            
        # reading a single frame from vcap stream for initializing 
        self.grabbed , self.frame = self.vcap.read()
        if self.grabbed is False :
            print('[Exiting] No more frames to read')
            exit(0)        # self.stopped is initialized to False 
        self.stopped = True        # thread instantiation  
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True # daemon threads run in background 
        
    # method to start thread 
    def start(self):
        self.stopped = False
        self.t.start()    # method passed to thread to read next available frame  
    def update(self):
        while True :
            if self.stopped is True :
                break
            self.grabbed , self.frame = self.vcap.read()
            if self.grabbed is False :
                print('[Exiting] No more frames to read')
                self.stopped = True
                break 
        self.vcap.release()    # method to return latest read frame 
    def read(self):
        return self.frame    # method to stop reading frames 
    def stop(self):
        self.stopped = True

class FileVideoStream:
    def _init_(self, path, queueSize=128):
        self.stream = cv2.VideoCapture(path)
        self.stopped = False
        self.Q = Queue(maxsize=queueSize)
    def start(self):
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self
    def update(self):
         while True:
            if self.stopped:
                return
            if not self.Q.full():
                (grabbed, frame) = self.stream.read()
                if not grabbed:
                    self.stop()
                return
            self.Q.put(frame)
    def read(self):
        return self.Q.get()
    def stop(self):
        self.stopped = True




face_detector = cv2.CascadeClassifier('haarcascade_frontalface.xml') 

 

def makeReport(filename:str,no:int)->None:
    # cap = cv2.VideoCapture("videos/"+filename)
    webcam_stream = WebcamStream(stream_id="videos/"+filename) # 0 id for main camera
    webcam_stream.start()# processing frames in input stream
    num_frames_processed = 0 
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi',fourcc, 5, (1280,720))
    df=pd.DataFrame()
    known_faces = []
    known_names=[]
    known_roll=[]
    marked_roll=[]
    marked_time=[]
    try:

        with open("embeddings.pkl","rb") as f:
            known_faces,known_names,known_roll=pickle.load(f)

    except:
            try:

                with open("D:/projects/known_faces.txt",'r') as f:
                    for line in f.readlines():
                        print("1")
                        name,rollNo,path = line.strip().split(' ')
                        print("2")
                        print(name,rollNo,path)
                        known_names.append(name)
                        known_roll.append(rollNo)
                        known_faces.append(face_recognition.face_encodings(face_recognition.load_image_file("D:/projects/images/"+path))[0])

                with open("embeddings.pkl","wb") as f:
                    pickle.dump([known_faces,known_names,known_roll],f)


            except:
                open("known_faces.txt",'a').close()

    marked = []
    s=True
    # detection = []
    print(known_names,known_roll)
    while s:
        try:
            if webcam_stream.stopped is True :
                break
            else :
                frame = webcam_stream.read()    # adding a delay for simulating video processing time 
                delay = 0.03 # delay value in seconds
                time.sleep(delay) 
                num_frames_processed += 1    # di
                frame =cv2.resize(frame,(1280,720),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
                rgb_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

                faces = face_detector.detectMultiScale(frame,scaleFactor=1.1,minNeighbors=2,minSize=(30,30),flags=cv2.CASCADE_SCALE_IMAGE)

                for(x,y,w,h) in faces:
                    face_encoding = face_recognition.face_encodings(rgb_frame,[(y,x+w,y+h,x)])[0]

                    matches = face_recognition.compare_faces(known_faces,face_encoding,tolerance=0.487)

                    if True in matches:
                        matched_index = matches.index(True)

                        if(known_names[matched_index] not in marked):
                            print("Marked Attendance: ",known_names[matched_index])
                            marked.append(known_names[matched_index])
                            marked_roll.append("7181"+known_roll[matched_index])
                            now = datetime.now()
                            dt_string = now.strftime("%H:%M:%S-%d/%m/%Y")
                            marked_time.append(dt_string)

                        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                        cv2.putText(frame,known_names[matched_index],(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),2)

                    else:
                        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                        cv2.putText(frame,"unknown",(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),2)
        except:
            pass
        b = cv2.resize(frame,(1280,720),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
        out.write(b)
        cv2.waitKey(1)
        cv2.imshow("feed",frame)

        # detection.append(faces_count)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    if(marked!=[]):
        df["Name"]=marked
        df["Roll_No"]=marked_roll
        df["Time"]=marked_time
        now = datetime.now()
        dt_string = str(now.strftime("%d/%m/%Y"))
        df.to_excel(r'report/result-'+str(no)+".xlsx", index = False)
    print(marked,marked_roll)
    webcam_stream.stop()
    out.release()

files = next(os.walk("videos/"))[-1]
for file,no in zip(files,range(1,len(files)+1)):
    makeReport(file,no)
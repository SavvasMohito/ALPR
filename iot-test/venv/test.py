import numpy as np
import cv2
from openalpr import Alpr
import sqlite3 as sq
from datetime import datetime as dt
import sys


VIDEO_SOURCE = "/home/mohito6/Videos/video.mp4"
WINDOW_NAME  = 'openalpr'
FRAME_SKIP   = 10

def main():
    alpr = Alpr('eu', "/etc/openalpr/openalpr.conf", "/usr/share/openalpr/runtime_data")
    if not alpr.is_loaded():
        print('Error loading OpenALPR')
        sys.exit(1)
    alpr.set_top_n(3)
    #alpr.set_default_region('new')

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        alpr.unload()
        sys.exit('Failed to open video file!')
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    cv2.setWindowTitle(WINDOW_NAME, 'OpenALPR video test')

    _frame_number = 0
    plates, accurs = [], []

    print("Opening Video..")
    print("Looking for Plates..\n")
    while True:
        ret_val, frame = cap.read()
        if not ret_val:
            print('VidepCapture.read() failed. Exiting...')
            break

        _frame_number += 1
        if _frame_number % FRAME_SKIP != 0:
            continue
        cv2.imshow(WINDOW_NAME, frame)

        results = alpr.recognize_ndarray(frame)

        for i, plate in enumerate(results['results']):
            best_candidate = plate['candidates'][0]
            canlen = len(best_candidate['plate'])
            if canlen >= 6 and canlen <=7 and float(best_candidate['confidence'])>87:
                print('Plate Found: {:7s} ({:.2f}%)'.format( best_candidate['plate'].upper(), best_candidate['confidence']))
                plates.append(best_candidate['plate'].upper())
                accurs.append(best_candidate['confidence'])

        if cv2.waitKey(1) == 27:
            break

    #Find correct plates in Lists
    while True:
        flag = True
        for k in range(len(plates)):
            c, j = 0, 0
            try:
                for i in plates[k]:
                    if plates[k+1].find(i) >= 0 and j == plates[k].find(i):
                        c += 1
                    j += 1
                if c>=4:
                    flag = False
                    if accurs[k] > accurs[k+1]:
                        plates.remove(plates[k+1])
                        accurs.remove(accurs[k+1])
                    else:
                        plates.remove(plates[k])
                        accurs.remove(accurs[k])
            except:
                continue
        if flag: break

    print("\nFinal Plates:")
    print(plates)
    print(accurs)


    #Send Data to DB
    conn = sq.connect("/home/mohito6/Documents/platesdb")
    c = conn.cursor()
    for k in range(len(plates)):
        c.execute("INSERT INTO events VALUES ('" + plates[k] + "', "+ "{:.2f}".format(accurs[k]) +", '" + str(dt.now()) + "')")
    conn.commit()


    #Close Connections
    conn.close()
    cv2.destroyAllWindows()
    cap.release()
    alpr.unload()


if __name__ == "__main__":
    main()
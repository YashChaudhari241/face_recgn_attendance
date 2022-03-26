import numpy as np
# import os
import cv2
import dlib
from face_align import FaceAlign
# import sys

pose_predictor = dlib.shape_predictor(
    'shape_predictor_68_face_landmarks_GTX.dat')
fa = FaceAlign(pose_predictor)
face_encoder = dlib.face_recognition_model_v1(
    'dlib_face_recognition_resnet_model_v1.dat')
# detector = dlib.get_frontal_face_detector()
modelFile = 'opencv_face_detector_uint8.pb'
configFile = 'opencv_face_detector.pbtxt'
net = cv2.dnn.readNetFromTensorflow(modelFile, configFile)


def openFromBuffer(file_buffer):
    bytes_as_np_array = np.frombuffer(file_buffer.read(), dtype=np.uint8)
    flag = 1
    # flag = 1 == cv2.IMREAD_COLOR
    # https://docs.opencv.org/4.2.0/d4/da8/group__imgcodecs.html
    frame = cv2.imdecode(bytes_as_np_array, flag)
    return frame


def getEncodings(imgArray):
    encodings = None
    for imgBuffer in imgArray:
        img = openFromBuffer(imgBuffer)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        frameHeight = img.shape[0]
        frameWidth = img.shape[1]
        blob = cv2.dnn.blobFromImage(img, 1.0, (300, 300), [104, 117,   123],
                                     False, False)
        net.setInput(blob)
        detections = np.array(net.forward())
        # maxind = detections.argmax(axis=2)

        # x1 = int(detections[0, 0, maxind, 3] * frameWidth)
        # y1 = int(detections[0, 0, maxind, 4] * frameHeight)
        # x2 = int(detections[0, 0, maxind, 5] * frameWidth)
        # y2 = int(detections[0, 0, maxind, 6] * frameHeight)
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if (i == 0 and confidence > 0.7) or (confidence > encodings[1]):
                x1 = int(detections[0, 0, i, 3] * frameWidth)
                y1 = int(detections[0, 0, i, 4] * frameHeight)
                x2 = int(detections[0, 0, i, 5] * frameWidth)
                y2 = int(detections[0, 0, i, 6] * frameHeight)
                # print(x1, file=sys.stderr)
                # print(y1, file=sys.stderr)
                # print(x2, file=sys.stderr)
                # print(y2, file=sys.stderr)
                faceAligned = fa.align(img, gray, dlib.rectangle(x1, y1, x2, y2))
                landmark = pose_predictor(faceAligned,
                                          dlib.rectangle(0, 0,
                                                         faceAligned.shape[0],
                                                         faceAligned.shape[1]))
                face_descriptor = face_encoder.compute_face_descriptor(faceAligned,
                                                                        landmark,
                                                                        num_jitters=2)
                encodings = (face_descriptor, confidence)

        # print(encodings)
        return encodings[0]

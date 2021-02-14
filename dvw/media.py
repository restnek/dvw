import cv2
import numpy as np


def resize(image, width):
    shape = np.shape(image)
    height = int(shape[0] * width / shape[1])
    return cv2.resize(image, (width, height))


def image2bin(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 127, 1, cv2.THRESH_BINARY)
    return bw.reshape(-1)


def bin2bw(binary, width):
    bw = [(255 if b else 0) for b in binary]
    return np.reshape(bw, (-1, width))


def copy_caption(input_path, output_path, codec):
    caption = cv2.VideoCapture(input_path)

    fourcc = cv2.VideoWriter_fourcc(*codec)
    fps = int(caption.get(cv2.CAP_PROP_FPS))
    width = int(caption.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(caption.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    return caption, writer


def copy_frames(source, destination):
    success, frame = source.read()
    while success:
        destination.write(frame)
        success, frame = source.read()

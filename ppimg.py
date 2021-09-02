import cv2
import numpy as np
import multiprocessing as mp
import random
import string
import sys
import json
import os
from multiprocessing import Pool
from datetime import datetime
from matplotlib import pyplot as plt
from scipy import ndimage, signal
import time

def nameFile():
    return str(int(round(time.time() * 1000))) + '.jpg'

# Leer rutas desde Node

def read_in():
    lines = sys.stdin.readlines()
    # Since our input would only be having one line, parse our JSON data from that
    return json.loads(lines[0])

def concatenar(nameFiles):
    return [*map(lambda f: os.getcwd().replace("\\", "/") + "/imgs-upload/" + f, nameFiles)]

# MÁSCARA DE ENFOQUE

def mascEnfoque(img):
    k = 5  # radio de la gaussiana
    std = 3.0  # desviacion estandar de la gaussiana
    # k y std son los parámetros que controlan la cantidad de enfoque que
    # se quieres aplicar a la imagen
    img = img.astype("float")
    kernel = sharp(k, std)
    img_filt = apply_filter(img, kernel)
    return img_filt


def gauss2d(k, std):  # gaussiana bidimensional
    rows = 2*k+1
    cols = 2*k+1
    gaussian1d = signal.gaussian(cols, std)  # gaussiana unidimensional
    kernel_gauss = np.ndarray((rows, cols), "float")  # mascara/kernel
    for i in range(0, rows):
        for j in range(0, cols):
            kernel_gauss[i, j] = gaussian1d[i]*gaussian1d[j]
    kernel_gauss = kernel_gauss/kernel_gauss.sum()  # norm. de la gaussiana
    return kernel_gauss


def conv2d(img, krnl):  # convolucion bidimensional
    rows = img.shape[0]-krnl.shape[0]+1
    cols = img.shape[1]-krnl.shape[1]+1
    output = np.ndarray((rows, cols), "float")
    kernel_reversed = np.rot90(np.rot90(krnl))
    for i in range(0, output.shape[0]):
        for j in range(0, output.shape[1]):
            img_patch = img[i:i+len(krnl), j:j+len(krnl)]
            y = max((kernel_reversed*img_patch).sum(), 0)
            z = min(y, 255)
            output[i, j] = z
    return output


def sharp(k, std):  # creación de la mascara de enfoque
    rows = 2*k+1
    cols = 2*k+1
    kernel_g = gauss2d(k, std)
    kernel = np.zeros((rows, cols), "float")
    kernel[k, k] = 2
    kernel = kernel-kernel_g
    return kernel


def apply_filter(img, kernel):  # rutina para aplicarle el filtro a la imagen
    if len(img.shape) == 2:  # blanco y negro (1 canal y transparencia)
        img_filt = conv2d(img, kernel)
    else:  # color (3 canales y transparencia)
        img_filt = []
        for channel in range(img.shape[2]):
            img_filt.append(conv2d(img[:, :, channel], kernel))
        img_filt = cv2.merge(img_filt)
    return img_filt

# BRILLO Y CONTRASTE


def automatic_brightness_and_contrast(ruta,image, clip_hist_percent=1):
    if get_lightness(image)>130:
        print('Suficiente brillo',ruta)
        return(image)
    else:
        print('Se aumentó brillo')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Calcular histograma de escala de grises
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_size = len(hist)
        # Calcular distribución acumalada desde el histograma
        accumulator = []
        accumulator.append(float(hist[0]))
        for index in range(1, hist_size):
            accumulator.append(accumulator[index - 1] + float(hist[index]))
        # Localizar puntos para recortar
        maximum = accumulator[-1]
        clip_hist_percent *= (maximum/100.0)
        clip_hist_percent /= 2.0
        # Localizar corte izquierdo
        minimum_gray = 0
        while accumulator[minimum_gray] < clip_hist_percent:
            minimum_gray += 1
        # Localizar corte derecho
        maximum_gray = hist_size - 1
        while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
            maximum_gray -= 1
        # Calcular valores de alpha y beta
        alpha = 255 / (maximum_gray - minimum_gray)
        beta = -minimum_gray * alpha
        auto_result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        return (auto_result)       

#Obtenemos nivel de brillo de la imagen
def get_lightness(src):
    hsv_image = cv2.cvtColor(src, cv2.COLOR_BGR2HSV)
    lightness = hsv_image[:,:,2].mean()    
    return  lightness

def processImage(ruta):
    image = cv2.imread(ruta)
    brillo_result = automatic_brightness_and_contrast(ruta,image)
    enfoque_result = mascEnfoque(brillo_result)
    file = nameFile()
    ruta = os.getcwd().replace("\\", "/") + '/imgs-process/' + file
    cv2.imwrite(ruta, enfoque_result)
    return file


def init(nameFiles):
    
    rutas = concatenar(nameFiles)
    with Pool(4) as p:
        ts = time.time()
        result = p.map(processImage, rutas)
        te = time.time()
        print("Procesado en:", te-ts)
        return result

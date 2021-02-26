import pyaudio
import wave
import numpy as np
import time
import matplotlib.pyplot as plt
import speech_recognition as sr
from scipy import signal
import serial
import math

ser = serial.Serial('COM6', 9600)
time.sleep(2)
ser.write(str.encode("90"))

r = sr.Recognizer()

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024
SPEAKING_THRESH = 8
WAVE_OUTPUT_FILENAME = "file.wav"

frames = [0] * 4000
frames_l = [0] * 4000
frames_r = [0] * 4000
times = [0] * 4000
audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    input_device_index=1,
                    frames_per_buffer=CHUNK)


def is_speaking(data, THRESH):
    data = np.array(data)
    data = np.frombuffer(np.array(data), np.int16) / 100

    data_rms = np.sqrt(np.mean(np.square(data)))

    if data_rms > THRESH:
        print("Speaking..")
        return 1
    else:
        return 0


def save_audio(arr):
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(arr))
    waveFile.close()


def recognize():
    with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
        # listen for the data (load audio to memory)
        audio_data = r.record(source)
        # recognize (convert from speech to text)
        try:
            text = r.recognize_google(audio_data)
        except:
            # print("?")
            return "?"

    # print(text)
    return text


def warmup():
    print("Please wait! Warming up microphone...")

    for i in range(0, int(RATE / CHUNK * 1)):
        stream.read(CHUNK)


def lag_finder(y1, y2, sr):
    corr = signal.correlate(y2, y1, mode='full', method="direct")
    lags = signal.correlation_lags(len(y2), len(y1))
    corr /= np.max(corr)
    """
    fig, (ax_orig, ax_noise, ax_corr) = plt.subplots(3, 1, figsize=(4.8, 4.8))
    ax_orig.plot(y2)
    ax_corr.plot(lags, corr)
    ax_noise.plot(y1)
    plt.show()
    """
    lag = lags[np.argmax(corr)]

    return lag, lags, corr


def rootmean(m1, m2):
    mean1 = np.mean(m1)
    mean2 = np.mean(m2)
    print(mean1 / mean2)


def plot_out(m1, m2, lags, corr):
    fig, axs = plt.subplots(3)
    axs[0].plot(m1)
    axs[1].plot(m2)
    axs[2].plot(lags, corr)
    plt.show()


def get_corresponding_mic_data(frames, start_index, stop_index):
    result = np.frombuffer(np.array(frames[start_index:stop_index]), np.int16)
    result = np.reshape(result, (int(result.shape[0] / 2), 2))
    mic_l_new, mic_r_new = result[:, 0], result[:, 1]

    size = len(mic_l_new)
    print(size)
    start = int(np.ceil(size/2)-6000)
    stop = int(np.ceil(size/2)+6000)

    mic_l_new = mic_l_new[start:stop]
    mic_r_new = mic_r_new[start:stop]

    return mic_l_new / np.max(mic_l_new), mic_r_new / np.max(mic_r_new)

def find_angle(delay,mic_D,velocity):
    print(delay)
    if delay>230/1000000 or delay<-230/1000000:
        if delay < 0:
            return -70
        else:
            return 70
    else:
        angle = math.acos(velocity*delay/mic_D)
        angle = angle * 180 / math.pi
        angle = (90-(1*angle))
        if delay<0:
            angle = math.acos(velocity * -delay / mic_D)
            angle = angle * 180 / math.pi
            angle = -(90-(1*angle))
    return angle



def speechrecognition():
    warmup()
    print("started..")
    t1 = time.time()
    start_time = t1
    stopped_time = t1

    while True:

        data = stream.read(CHUNK)

        frames.append(data)
        frames.pop(0)

        times.append(time.time())
        times.pop(0)

        if is_speaking(data, SPEAKING_THRESH):

            if (time.time() - t1) > 1:
                start_time = time.time() - 0.5
            t1 = time.time()
            # print("speaking")
        else:
            t2 = time.time()
            if (t2 - t1) > 1 and t1 > stopped_time:
                stopped_time = t2 - 0.5

                start_index = (np.abs(np.array(times) - start_time)).argmin()
                stop_index = (np.abs(np.array(times) - stopped_time)).argmin()
                save_audio(frames[start_index:stop_index])
                det = recognize()
                print(det)
                if "hello" in det:
                    mic_l, mic_r = get_corresponding_mic_data(frames, start_index, stop_index)
                    """
                    mic_l = mic_l[0:-5]
                    mic_r = mic_l[5:]
                    """

                    lag, lags, corr = lag_finder(mic_l, mic_r, 44100)
                    lag = lag * 1000000 / RATE#microseconds
                    print("lag is: ", lag, "us")
                    angle = find_angle(lag/1000000, 12.78, 37500)
                    print(angle)
                    ser.write(str.encode(str(angle*1.2)))
                    # plot_out(mic_l, mic_r, lags, corr)


speechrecognition()

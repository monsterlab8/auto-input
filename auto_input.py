import threading
import time
import sys

import PySimpleGUI as sg
import pyautogui
from pynput import keyboard

stop_flag = threading.Event()

def do_repeated_keypress(text, interval, count, delay_before):
    if delay_before > 0:
        time.sleep(delay_before)
    typed = 0
    try:
        while not stop_flag.is_set() and (count == 0 or typed < count):
            pyautogui.typewrite(text)
            typed += 1
            if stop_flag.is_set():
                break
            time.sleep(max(0.001, interval))
    except Exception as e:
        print("Error in keypress thread:", e)

def do_sequence_keypress(sequence, interval, delay_before):
    if delay_before > 0:
        time.sleep(delay_before)
    try:
        for item in sequence:
            if stop_flag.is_set():
                break
            pyautogui.typewrite(item)
            time.sleep(max(0.001, interval))
    except Exception as e:
        print("Error in sequence thread:", e)

def do_repeated_click(x, y, button, interval, count, delay_before):
    if delay_before > 0:
        time.sleep(delay_before)
    clicked = 0
    try:
        while not stop_flag.is_set() and (count == 0 or clicked < count):
            if x is None or y is None:
                pyautogui.click(button=button)
            else:
                pyautogui.click(x=x, y=y, button=button)
            clicked += 1
            if stop_flag.is_set():
                break
            time.sleep(max(0.001, interval))
    except Exception as e:
        print("Error in click thread:", e)

def start_hotkey_listener():
    def on_press(key):
        try:
            if key == keyboard.Key.esc:
                stop_flag.set()
        except:
            pass
    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()
    return listener

sg.theme('LightBlue2')

layout = [
    [sg.Frame('Mode', [
        [sg.Radio('Tekan tombol berulang (ketik teks)', "MODE", key='-MODE_KEY-', default=True)],
        [sg.Radio('Urutan teks sekali (sequence)', "MODE", key='-MODE_SEQ-')],
        [sg.Radio('Klik mouse otomatis', "MODE", key='-MODE_CLICK-')]
    ])],
    [sg.Text('Teks / Sequence (pisah dengan || untuk sequence):'), sg.Input(key='-TEXT-', size=(40,1))],
    [sg.Text('Interval (detik, mis. 0.5):'), sg.Input('1.0', key='-INTERVAL-', size=(8,1)),
     sg.Text('Count (0 = terus):'), sg.Input('0', key='-COUNT-', size=(6,1))],
    [sg.Text('Delay sebelum mulai (detik):'), sg.Input('3', key='-DELAY-', size=(6,1))],
    [sg.Frame('Klik Mode (hanya untuk mode klik)', [
        [sg.Text('Koordinat x:'), sg.Input('', key='-X-', size=(6,1)),
         sg.Text('y:'), sg.Input('', key='-Y-', size=(6,1)),
         sg.Button('Ambil Pos Mouse', key='-GETPOS-')],
        [sg.Text('Tombol:'), sg.Combo(['left','right','middle'], default_value='left', key='-BUTTON-')]
    ])],
    [sg.HorizontalSeparator()],
    [sg.Text('Hotkey global: Tekan ESC untuk menghentikan skrip')],
    [sg.Button('Start', key='-START-'), sg.Button('Stop', key='-STOP-'), sg.Button('Keluar')]
]

window = sg.Window('Auto Input & Auto Click', layout, finalize=True)
hotkey_listener = start_hotkey_listener()
worker_thread = None

def start_job(values):
    global worker_thread, stop_flag
    stop_flag.clear()

    mode_key = values['-MODE_KEY-']
    mode_seq = values['-MODE_SEQ-']
    mode_click = values['-MODE_CLICK-']

    interval = float(values['-INTERVAL-']) if values['-INTERVAL-'] else 1.0
    count = int(values['-COUNT-']) if values['-COUNT-'] else 0
    delay_before = float(values['-DELAY-']) if values['-DELAY-'] else 0.0

    if mode_key:
        text = values['-TEXT-']
        if not text:
            sg.popup_error("Masukkan teks untuk diketik.")
            return
        worker_thread = threading.Thread(target=do_repeated_keypress, args=(text, interval, count, delay_before), daemon=True)
        worker_thread.start()
    elif mode_seq:
        raw = values['-TEXT-']
        if not raw:
            sg.popup_error("Masukkan sequence (pisah item dengan ||).")
            return
        sequence = [s.strip() for s in raw.split('||') if s.strip()!='']
        worker_thread = threading.Thread(target=do_sequence_keypress, args=(sequence, interval, delay_before), daemon=True)
        worker_thread.start()
    elif mode_click:
        x_raw = values['-X-'].strip()
        y_raw = values['-Y-'].strip()
        x = int(x_raw) if x_raw != '' else None
        y = int(y_raw) if y_raw != '' else None
        button = values['-BUTTON-']
        worker_thread = threading.Thread(target=do_repeated_click, args=(x, y, button, interval, count, delay_before), daemon=True)
        worker_thread.start()
    else:
        sg.popup_error("Pilih mode.")
        return

    sg.popup_non_blocking("Job dimulai. Tekan ESC atau tombol Stop untuk menghentikan.", title="Started")

def stop_job():
    global stop_flag, worker_thread
    stop_flag.set()
    if worker_thread is not None and worker_thread.is_alive():
        worker_thread.join(timeout=1.0)

while True:
    event, values = window.read(timeout=100)
    if event == sg.WIN_CLOSED or event == 'Keluar':
        stop_flag.set()
        break
    if event == '-GETPOS-':
        x, y = pyautogui.position()
        window['-X-'].update(str(x))
        window['-Y-'].update(str(y))
    if event == '-START-':
        start_job(values)
    if event == '-STOP-':
        stop_job()

    if stop_flag.is_set():
        sg.popup_non_blocking("Stop signal diterima (ESC atau Stop). Job dihentikan.", title="Stopped")
        stop_flag.clear()

window.close()
sys.exit(0)

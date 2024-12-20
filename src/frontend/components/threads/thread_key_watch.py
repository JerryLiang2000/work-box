import time
from PyQt5.QtCore import QThread, pyqtSignal

import settings
from src.frontend.public import app_root

from pynput import keyboard, mouse


class KeyRecord:
    def __init__(self, key):
        self.key = key


class KeyWatchThread(QThread):
    press_signal = pyqtSignal(KeyRecord)
    release_signal = pyqtSignal(KeyRecord)

    start_run_signal = pyqtSignal(str)
    event_signal = pyqtSignal(list)
    update_status_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll)
        self.key_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)

        # 监听状态：1+ - 静默监听， 10 - 待录制监听, 11 - 录制中
        self._status = 1

        # 录制事件
        self._events = []

        self.update_status_signal.connect(self.update_status)

        self.sig = 0

    def update_status(self, s):
        self._status = s

    def append_event(self, event):
        self._events.append({"run_time": time.time(), "event": event})

    def clear_events(self):
        self._events = []

    def on_click(self, x, y, button, pressed):
        if self._status == 11:
            self.append_event(['click', button.name, pressed, x, y])

    def on_move(self, x, y):
        if self._status == 11:
            self.append_event(['move', x, y])

    def on_scroll(self, x, y, dx, dy):
        if self._status == 11:
            self.append_event(['scroll', x, y, dx, dy])

    def on_press(self, key):
        if self._status == 11:
            if key == keyboard.Key.esc:
                self.update_status(1)
                app_root.ui_log.info('录制结束')
                self.event_signal.emit(self._events)
            else:
                self.append_event(['press', str(key)])

        self.press_signal.emit(KeyRecord(key))

    def on_release(self, key):
        # app_root.ui_log.info('ok')
        # 录制中
        if self._status == 11:
            self.append_event(['release', str(key)])

        # 就绪 转 执行
        if self._status == 10 and key == keyboard.Key.down:
            app_root.ui_log.info('开始录制')
            self.clear_events()
            self.update_status(11)
            self.start_run_signal.emit('录制中')

        self.release_signal.emit(KeyRecord(key))

    def run(self):
        self.key_listener.start()
        self.mouse_listener.start()
        while True:
            if settings.RUN_ENV == 'Windows':
                break
            app_root.ui_log.info('校验中')
            time.sleep(2)
            app_root.ui_log.info(f'key {self.key_listener.is_alive()}')
            if not self.key_listener.is_alive():
                self.key_listener.stop()
                self.key_listener.join()
                self.key_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
                self.key_listener.start()
                continue

            app_root.ui_log.info(f'mouse {self.mouse_listener.is_alive()}')
            if not self.mouse_listener.is_alive():
                self.mouse_listener.stop()
                self.mouse_listener.join()
                self.mouse_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move,
                                                     on_scroll=self.on_scroll)
                self.mouse_listener.start()
                continue
            break
        self.sig = 1
        # app_root.ui_log.warning('success')
        # app_root.ui_log.info(f'{self.key_listener.is_alive()}, {self.mouse_listener.is_alive()}')
        self.key_listener.join()
        self.mouse_listener.join()

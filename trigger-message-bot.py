"""
My Bot

내 메시지 트리거 봇
"""
from glob import glob
from os import remove
from os.path import exists, isdir
from queue import Queue, Empty
from threading import Thread
from typing import List
from time import sleep

from dotenv import dotenv_values
from telegram.client import Telegram
from telegram.worker import BaseWorker
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer


# 귀찮아! 그냥 글로벌 설정 가즈아
class GlobalSetup:
    chat_id = 0
    tg: Telegram | None = None
    watch_path = ''


def scan_messages(directory: str) -> List[str]:
    return sorted([message_file for message_file in glob(directory + '/*.txt')])


def enqueue_message(queue: Queue, file_path: str) -> None:
    if exists(file_path):
        with open(file_path, 'r') as fp:
            message = fp.read().strip()
            if message:
                queue.put(('send_message', message), timeout=0.5)
        remove(file_path)


class TelegramHandler(FileSystemEventHandler):
    def __init__(self, queue: Queue):
        self.is_working = False
        self.queue = queue

        # Process stored files.
        for message_file in scan_messages(GlobalSetup.watch_path):
            enqueue_message(self.queue, message_file)

    def on_closed(self, event: FileSystemEvent) -> None:
        if not self.is_working:
            self.is_working = True
            enqueue_message(self.queue, event.src_path)
            self.is_working = False


class Worker(BaseWorker):
    def __init__(self, queue: Queue):
        super(Worker, self).__init__(queue)

        self._thread_1 = Thread(target=self._runner_1)
        self._thread_1.daemon = True

        self._thread_2 = Observer()
        self._thread_2.daemon = True
        self._thread_2.schedule(TelegramHandler(queue), GlobalSetup.watch_path, recursive=False)

    def run(self) -> None:
        self._thread_1.start()
        self._thread_2.start()

    def stop(self) -> None:
        self._is_enabled = False
        self._thread_2.stop()

        self._thread_1.join()
        self._thread_2.join()

    def _runner_1(self) -> None:
        chat_id = GlobalSetup.chat_id

        while self._is_enabled:
            tg = GlobalSetup.tg
            if not tg:
                sleep(1)
                continue

            try:
                tag, message = self._queue.get(timeout=0.5)
            except Empty:
                continue

            if tg and chat_id and 'send_message' == tag and isinstance(message, str):
                tg.send_message(chat_id, message)

            self._queue.task_done()

    def get_queue(self) -> Queue:
        return self._queue


def trigger_message_bot() -> None:
    config = dotenv_values('.env')

    # Required.
    api_hash = config['API_HASH'] if 'API_HASH' in config else None
    api_id = int(config['API_ID'] if 'API_ID' in config else '')
    chat_id = int(config['CHAT_ID'] if 'CHAT_ID' in config else '')
    db_enc_key = config['DB_ENC_KEY'] if 'DB_ENC_KEY' in config else None
    lib_path = config['LIB_PATH'] if 'LIB_PATH' in config else None
    phone = config['PHONE'] if 'PHONE' in config else None
    watch_path = config['WATCH_PATH'] if 'WATCH_PATH' in config else ''

    if not watch_path or not exists(watch_path) or not isdir(watch_path):
        raise Exception('Invalid path')

    # Optional.
    files_directory = config['FILES_DIRECTORY'] if 'FILES_DIRECTORY' in config else None

    # watch_path 는 반드시 tg 전에
    GlobalSetup.chat_id = chat_id
    GlobalSetup.watch_path = watch_path

    GlobalSetup.tg = Telegram(
        api_id=api_id,
        api_hash=api_hash,
        database_encryption_key=db_enc_key,
        files_directory=files_directory,
        library_path=lib_path,
        phone=phone,
        worker=Worker,
    )

    GlobalSetup.tg.login()
    GlobalSetup.tg.idle()


if __name__ == "__main__":
    trigger_message_bot()

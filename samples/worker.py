from telegram.worker import BaseWorker
from queue import Queue
from threading import Thread
from time import sleep


class Worker(BaseWorker):
    def __init__(self, queue: Queue):
        super(Worker, self).__init__(queue)
        self._thread_1 = Thread(target=self._runner_1)
        self._thread_2 = Thread(target=self._runner_2)
        self._thread_1.daemon = True
        self._thread_2.daemon = True

    def run(self) -> None:
        self._thread_1.start()
        self._thread_2.start()

    def stop(self) -> None:
        self._is_enabled = False
        self._thread_1.join()
        self._thread_2.join()

    @staticmethod
    def _runner_1() -> None:
        print('Starting runner #1')
        for x in range(0, 3):
            print('Runner #1: ' + str(x + 1))
            sleep(1)

    @staticmethod
    def _runner_2() -> None:
        print('Starting runner #2')
        for x in range(0, 3):
            print('Runner #2: ' + str(x + 1))
            sleep(1)


if __name__ == '__main__':
    worker = Worker(Queue())
    worker.run()
    print('Just wait for 5 seconds.')
    sleep(5)
    worker.stop()

from enum import Enum
from multiprocessing import Process, Queue
from threading import Thread
import uuid

import requests

class ManagerState(Enum):
    STARTING = 0
    RUNNING = 1
    OVERLOAD = -1

class FestifyManager:

    def __init__(self):
        self.state = ManagerState.STARTING
        self.active_processes = {}
        self.result_queue = Queue()
        self.start_results_worker()

    def start(self, playlist_name, base_64_image):
        if not base_64_image:
            return

        self.update_state(ManagerState.RUNNING)

        festify_process_id = str(uuid.uuid4())
        festify_process = Process(name=festify_process_id, target=Festify.create_playlist,
                                  args=(playlist_name, base_64_image, self.result_queue))
        self.active_processes[festify_process_id] = festify_process

        festify_process.start()
        return festify_process_id

    def report_results(self):
        while True:
            process_id, results, errs = self.result_queue.get()
            if errs:
                for err in errs:
                    print(err)

            data = {
                id: process_id,
                results: results
            }

            requests.post('localhost', json=data)

    def start_results_worker(self):
        Thread(target=self.report_results, daemon=True).start()

    def update_state(self, new_state):
        if not new_state or not isinstance(new_state, ManagerState) or self.state == new_state:
            raise ValueError('Invalid State')

        self.state = new_state

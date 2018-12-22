from enum import Enum
from multiprocessing import Process, Queue
from threading import Thread
import uuid

from Festify import Festify


class ManagerState(Enum):
    STARTING = 0
    RUNNING = 1
    OVERLOAD = -1


class FestifyManager:

    def __init__(self):
        self.state = ManagerState.STARTING
        self.active_processes = {}
        self.results = {}
        self.result_queue = Queue()
        self.start_results_worker()

    def start(self, playlist_id, playlist_name, base_64_image, access_token):
        if not base_64_image:
            return

        self.update_state(ManagerState.RUNNING)


        festify_process = Process(name=playlist_id, target=Festify.create_playlist,
                                  args=(
                                      playlist_id, playlist_name, base_64_image, access_token,
                                      self.result_queue))
        self.active_processes[playlist_id] = festify_process

        festify_process.start()
        return playlist_id

    def get_results(self, process_id):
        if not process_id or process_id not in self.results:
            return None

        return self.results[process_id]

    def report_results(self):
        while True:
            process_id, results, errs = self.result_queue.get()
            if errs:
                for err in errs:
                    print(err)

            self.results[process_id] = results

    def start_results_worker(self):
        Thread(target=self.report_results, daemon=True).start()

    def update_state(self, new_state):
        if not new_state or not isinstance(new_state, ManagerState) or self.state == new_state:
            return

        self.state = new_state

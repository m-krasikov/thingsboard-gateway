from storage.event_storage import EventStorage
from tb_utility.tb_utility import TBUtility
from storage.file_event_storage_files import FileEventStorageFiles, FileEventStoragePointer
import yaml
import queue


class FileEventStorage(EventStorage):
    def __init__(self, config):
        self.__queue_len = TBUtility.get_parameter(config, "max_records_count", 10)
        self.__events_per_time = TBUtility.get_parameter(config, "read_records_count", 2)
        self.__records_per_file = TBUtility.get_parameter(config, "records_per_file", 5)
        self.__no_records_sleep_interval = TBUtility.get_parameter(config, "no_records_sleep_interval", 60)
        self.__events_queue = queue.Queue(self.__queue_len)
        self.__event_pack = []

    def put(self, event):
        if not self.__events_queue.full():
            self.__events_queue.put(event)
            return True
        else:
            return False

    def get_events_queue_size(self):
        return self.__events_queue.qsize()

    def get_event_pack(self):
        if not self.__events_queue.empty() and not self.__event_pack:
            for _ in range(min(self.__events_per_time, self.__events_queue.qsize())):
                self.__event_pack.append(self.__events_queue.get())
        return self.__event_pack

    def event_pack_processing_done(self):
        self.__event_pack = []

    def write_to_storage(self, config):
        data_files = FileEventStorageFiles(config)
        path = data_files.data_folder_path
        files = data_files.init_data_files(path)
        current_position = yaml.safe_load(open(path + files['state_file']))
        pointer = FileEventStoragePointer(path, current_position['write_file'], current_position['write_line'])
        while True:
            events = self.get_event_pack()
            if events:
                for event in events:
                    if pointer.get_line() <= self.__records_per_file and (
                            not pointer.file_is_full(path, pointer.get_file(), self.__records_per_file)):
                        with open(path + pointer.get_file(), 'a') as f:
                            f.write(str(event) + '\n')
                            pointer.next_line()
                            data_files.change_state_line(path, files['state_file'], pointer.get_line())
                    else:
                        if pointer.file_is_full(path, files['data_files'][-1], self.__records_per_file):
                            new_data_file = data_files.create_new_datafile(path)
                            pointer.set_file(new_data_file)
                            files['data_files'].append(pointer.get_file())
                            data_files.change_state_file(path,files['state_file'], pointer.get_file())
                        pointer.set_file(files['data_files'][-1])
                        data_files.change_state_file(path, files['state_file'], pointer.get_file())
                        pointer.set_line(data_files.change_state_line(path, files['state_file'], 1))
                        with open(path + pointer.get_file(), 'a') as f:
                            f.write(str(event) + '\n')
            self.event_pack_processing_done()

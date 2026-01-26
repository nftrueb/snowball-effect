import os 
import json 
from platformdirs import user_data_dir

class FatalFileException(Exception): 
    def __init__(self, message=None): 
        super().__init__(message or 'Fatal exception occurred in file layer')

class FileLayer: 
    def __init__(self): 
        self.initialized = False  
        self.appname = None

    def __str__(self): 
        return f'FileLayer:\nAppname: {self.appname}\nData dir: {user_data_dir(self.appname)}'
    
    def init(self, appname: str): 
        if appname is None: 
            raise FatalFileException('No appname provided to FileLayer')
        self.appname = appname

        self.init_data_dir(appname)

        self.initialized = True 

    def init_data_dir(self, appname: str): 
        data_path = user_data_dir(appname)
        if not os.path.exists(data_path): 
            os.mkdir(data_path)
            print(f'[INFO] Created data path: {data_path}')
    
    def check_initialized(self): 
        if not self.initialized: 
            raise FatalFileException('FileLayer is not yet initialized') 
        
    def data_file_exists(self, filename: str): 
        path = os.path.join(user_data_dir(self.appname), filename)
        return os.path.exists(path)

    def load_text(self, filename: str): 
        try: 
            with open(filename, 'r', encoding='utf-8') as f: 
                return f.read()
        except Exception as ex: 
            raise FatalFileException(f'Failed to load JSON file: {filename}') from ex

    def load_bytes(self, filename: str): 
        try: 
            with open(filename, 'rb', encoding='utf-8') as f: 
                return f.read()
        except Exception as ex: 
            raise FatalFileException(f'Failed to load JSON file: {filename}') from ex

    def load_json(self, filename: str, use_data_dir=True): 
        try: 
            path = os.path.join(user_data_dir(self.appname), filename) if use_data_dir else filename 
            with open(path, 'r', encoding='utf-8') as f: 
                return json.load(f)
        except Exception as ex: 
            raise FatalFileException(f'Failed to load JSON file: {filename}') from ex
        
    def write_json(self, filename: str, data: dict, use_data_dir=True): 
        path = os.path.join(user_data_dir(self.appname), filename) if use_data_dir else filename
        json_str = json.dumps(data, indent=4, sort_keys=True)
        with open(path, 'w', encoding='utf-8') as f: 
            length = f.write(json_str)

            if length != len(json_str): 
                raise FatalFileException(f'Failed to write JSON data to file: {filename}')
            
file_layer = FileLayer()

def get_file_layer(): 
    return file_layer

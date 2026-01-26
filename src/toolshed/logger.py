import os

class Logger: 
    class Level: 
        DEBUG = 'DEBUG'
        INFO = 'INFO'
        ERROR = 'ERROR'

    def __init__(self): 
        env = os.environ
        self.root = None
        if 'PYGAME_TOOLSHED_LOGGER_ROOT' in env.keys(): 
            self.root = env.get('PYGAME_TOOLSHED_LOGGER_ROOT')
            self.debug(f'Logger initialized with root: {self.root}')

    def prefix(self, level): 
        return f'[ {level} ] '

    def debug(self, message): 
        self.log(self.Level.DEBUG, message)  

    def info(self, message): 
        self.log(self.Level.INFO, message)  

    def error(self, message, ex: Exception = None): 
        if ex is not None: 
            message += f': {ex}\n'
            frame = ex.__traceback__
            while frame is not None: 
                filename = frame.tb_frame.f_code.co_filename
                if self.root is not None and filename.startswith(self.root): 
                    filename = filename[len(self.root)+1:]
                message += f'Line: {frame.tb_lineno} -- {frame.tb_frame.f_code.co_name}() -- {filename}\n'
                frame = frame.tb_next
            message = message[:-1]
        self.log(self.Level.ERROR, message) 

    def log(self, level, input_msg): 
        prefix = self.prefix(level)
        whitespace_prefix = '\n' + ''.join([' ' for i in range(len(prefix))])
        constructed_msg = whitespace_prefix.join(input_msg.split('\n'))
        print(f'{prefix}{constructed_msg}')

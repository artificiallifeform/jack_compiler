#! python3
import sys
import os

from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine

os.system('clear')

class JackAnalyzer:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.target_check()

    def target_check(self):
        if(not os.path.exists(self.path)):
            raise Exception("Wrong path. Check it")

        if (os.path.isdir(self.path)):
            self._dir_processing()
        elif (os.path.isfile(self.path)):
            self._file_processing(self.path)

    def _dir_processing(self):
        # If target path is a dir call _file_processing for every
        # file in this folder
        for f in os.listdir(self.path):
            if (not os.path.isdir(f)):
                self._file_processing(f, self.path)

           
    def _file_processing(self,filename, filepath=None):
        # If target path is a file
        if (filename.split('.')[1] == 'jack'):
            if (filepath):
                
                # MethodMap(filepath+'\\'+filename).map_funcs()
                self.tokenizer = JackTokenizer(filepath+'\\'+filename)

                comp_engine = CompilationEngine(filepath + '\\'+filename, self.tokenizer)
                comp_engine.create_file()
            else: 
                self.tokenizer = JackTokenizer(filename)
                # MethodMap(filepath).map_funcs()
                
                comp_engine = CompilationEngine(filepath, self.tokenizer)

                
            

jackAnl = JackAnalyzer(sys.argv[1])
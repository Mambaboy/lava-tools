#coding=utf-8

import config
import os
import shutil
import subprocess
import copy
import logging
import coloredlogs
from fuzzer_afl import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("compare_test")

########################################################################
class Compare_test:
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        
    #----------------------------------------------------------------------
    def set_config(self):
        """"""
        
    
    #----------------------------------------------------------------------
    def start_all_couple(self):
        """"""
        #1. set the config to start the compare
        self.set_config()
        
        # get all the compare task 
        
        
        #2 limited time
        
    #----------------------------------------------------------------------
    def start_one_couple_in_a_thread(self):
        """"""
        #1. start the AFl with the couple binaries
        fuzzer1=Fuzzer(binary_path, work_dir, afl_count=1, library_path=None, 
                      time_limit=None, memory="8G", 
                      target_opts=None, 
                      extra_opts=None, 
                      create_dictionary=False, 
                      seeds=None, crash_mode=False, 
                      never_resume=False, qemu=True, 
                      stuck_callback=None, 
                      force_interval=None, 
                      job_dir=None, afl_engine=None, 
                      input_from='stdin', 
                      afl_input_para=None, 
                      comapre_afl=False, 
                      strategy_id='0', multi_afl=False)
        
        fuzzer1=Fuzzer(binary_path, work_dir, afl_count=1, library_path=None, 
                           time_limit=None, memory="8G", 
                          target_opts=None, 
                          extra_opts=None, 
                          create_dictionary=False, 
                          seeds=None, crash_mode=False, 
                          never_resume=False, qemu=True, 
                          stuck_callback=None, 
                          force_interval=None, 
                          job_dir=None, afl_engine=None, 
                          input_from='stdin', 
                          afl_input_para=None, 
                          comapre_afl=False, 
                          strategy_id='0', multi_afl=False)
        
        fuzzer1.start
        
        #2. start the listner for the crash time and check if the crash is the target crash
        
        #3. kill the the afl and return this thread
        
        


if __name__ == '__main__':
    coloredlogs.install()
    logger.info("start")
    
    compare_test=Compare_test()
    
    
    logger.info("successs")

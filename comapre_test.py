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
    def __init__(self,afl_upper=6):
        """Constructor"""
        self._global_config()
        
        #some init functions
        self._read_branches()
        
        #global variable
        self.afl_start_nums=0
        self.afl_start_upper=afl_upper
        
        
    #----------------------------------------------------------------------
    def _global_config(self):
        """"""
        #absolute path
        self.output_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava1-output"
        self.lava1_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/LAVA-1"
        self.branches_path=os.path.join(self.lava1_dir,"branches.txt")        
        self.targets_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava-tools/targets"

        #global variable
        self.targets=set()
        self.exclude=set()
        self.branches=set()      
    
    #----------------------------------------------------------------------
    def _read_branches(self):
        """"""
        with open(self.branches_path,"rt") as f:
            for lines in f.readlines():
                self.branches.update(["file-5.22."+lines.split("\n")[0]])     
                
    #----------------------------------------------------------------------
    def _set_targets_item(self):
        """  """
        for item in os.listdir(self.targets_dir):
            item_dir=os.path.join(self.targets_dir,item)
            binary_afl=os.path.join(item_dir,item+"-afl")
            binary_aflgo_instrument=os.path.join(item_dir+"-aflgo_instrument")
            if os.path.exists(binary_afl) and os.path.exists(binary_aflgo_instrument):
                self.targets.update([item])                       
        
    #----------------------------------------------------------------------
    def pre_for_test(self):
        """"""
        #1. set the target
        self._set_targets()  
        #2. set the fuzzing config
        self.set_fuzzing_config()
        
        
    #----------------------------------------------------------------------
    def set_fuzzing_config(self):
        """"""
        self.workspace="/tmp/compare_test"
        self.afl_count=1
        self.time_limit=4*60*60 # second
        self.seed_dir=os.path.join(os.path.dirname(self.targets_dir),"seed")
        self.afl_engine_path="/home/xiaosatianyu/workspace/git/afl/afl-fuzz"
        self.input_from="file"
    
    #----------------------------------------------------------------------
    def check_afl_engines_too_many(self):
        """
        check if could start more afl engine
        True: can not open
        False: can continue open afl
        """
        if self.afl_start_nums >self.afl_start_upper:
            return True
        else:
            return False
        
    
    #----------------------------------------------------------------------
    def start_all_targets(self):
        """"""
        #1. pre for fuzzing
        self.pre_for_test()
        #2. start the fuzzing
        for target in self.targets:
            if self.afl_start_nums >
        
        self.start_all_targets()
        
    #----------------------------------------------------------------------
    def start_one_couple_in_a_thread(self):
        """"""
        #1. start the AFl with the couple binaries
        fuzzer1=Fuzzer(binary_path, work_dir, afl_count=1, library_path=None, 
                      time_limit=None, 
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
                      )
        
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
        
#流程
#1. 初始化一个类,一个类中完成所有的对比测试
    #1.1 read from the branches 
    #1.2 set the targets
    #1.3 set the fuzzing config    
#3. 开启一个线程,该线程启动afl,进行对比测试,对比双方可以各启动多个afl,设置线程上限
#4. 当前线程坚挺crash输出,记录crash的时间差
#5. 收集到信息,保存成一定格式,用于后面画图,结束


if __name__ == '__main__':
    coloredlogs.install()
    logger.info("start")
    
    compare_test=Compare_test()
    
    
    logger.info("successs")

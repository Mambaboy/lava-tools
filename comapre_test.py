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
        self._global_config()
        
        #some init functions
        self._read_branches()
        
        #global variable
       
        
        
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
    def _set_targets(self):
        """  """
        for item in os.listdir(self.targets_dir):
            item_dir=os.path.join(self.targets_dir,item)
            binary_afl=os.path.join(item_dir,item+"-afl")
            binary_aflgo_instrument=os.path.join(item_dir,item+"-aflgo_instrument")
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
        
        self.seed_dir=os.path.join(os.path.dirname(self.targets_dir),"seed")
        self.afl_engine_path="/home/xiaosatianyu/workspace/git/afl/afl-fuzz"
        self.input_from="file"
        self.afl_input_para=["@@"]
        
        #afl start nums and counts
        self.afl_count=1  # for each number of test
        self.afl_start_nums=0
        self.afl_start_upper=6   
        
        #time limited
        self.time_limit=4*60*60 # second
    
    #----------------------------------------------------------------------
    def check_afl_engines_too_many(self):
        """
        check if could start more afl engine
        True: can not open
        False: can continue open afl
        """
        if self.afl_start_nums >self.afl_start_upper:
            return True #can not gon on openning afl 
        else:
            return False #can gon on openning afl 
        
    
    #----------------------------------------------------------------------
    def start_all_targets(self):
        """"""
        #1. pre for fuzzing
        self.pre_for_test()
        #2. start the fuzzing
        for item in self.targets:
            #2.1check resource
            while (self.check_afl_engines_too_many()):
                #wait resource for afl
                time.sleep(1)
                            
            #2.2 begin to start
            file_target_item=os.path.join(self.targets_dir,item)
            self.start_one_target(file_target_item)
            
        
    #----------------------------------------------------------------------
    def start_one_target(self,file_target_item):
        """"""
        #0. set some information
        item=os.path.basename(file_target_item)
        binary_afl_path=os.path.join(file_target_item,item+"-afl")
        binary_aflgo_instrument_path=os.path.join(file_target_item,item+"-afl_instrument")
        
        work_dir=os.path.join(self.workspace,item)
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)
        
        afl_count=self.afl_count
        time_limit=self.time_limit
        
        afl_engine=self.afl_engine_path
        
        input_from=self.input_from
        afl_input_para=self.afl_input_para
        
        seed_dir=self.seed_dir
        
        #1. start the AFl with the couple binaries
        fuzzer_afl=Fuzzer(binary_afl_path , work_dir, afl_count=1, 
                      time_limit=time_limit, 
                      seed_dir=seed_dir, crash_mode=False, 
                      qemu=False, 
                      job_dir=None, afl_engine=afl_engine, 
                      input_from=input_from, 
                      afl_input_para=afl_input_para,afl_flag="afl"
                      )
        
        fuzzer_aflgo_instrument=Fuzzer(binary_aflgo_instrument_path, work_dir, afl_count=1, 
                           time_limit=time_limit, 
                          seed_dir=seed_dir, crash_mode=False, 
                          qemu=False, 
                          job_dir=None, afl_engine=afl_engine, 
                          input_from=input_from, 
                          afl_input_para=afl_input_para,afl_flag="afl_instrument"
                          )        
        
        fuzzer_afl.start() 
        fuzzer_aflgo_instrument.start() 
        
        self.afl_start_nums+=1
        
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
    compare_test.start_all_targets()
    
    
    logger.info("successs")

#coding=utf-8

import config
import os
import shutil
import subprocess
import copy
import logging
import coloredlogs
from fuzzer_afl import *
import multiprocessing
import threading

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


    #----------------------------------------------------------------------
    def _global_config(self):
        """"""
        #absolute path
        self.output_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava1-output"
        self.lava1_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/LAVA-1"
        self.branches_path=os.path.join(self.lava1_dir,"branches.txt")        
        self.targets_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava-tools/targets"
        #check for the crash
        self.check_binary="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava-tools/targets/file-5.22-for-compare/file"
        self.plot_path="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava-tools/plot_out"

        #global variable
        self.targets=set()
        self.exclude=set()
        self.branches=set()   
        self.alfgo_test_time_upper=5*60*60 #second

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
        self.aflgo_engine_path="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/afl-fuzz"
        self.input_from="file"
        self.afl_input_para=["@@"]

        #afl start nums and counts
        self.afl_count=1  # for each number of test
        self.cpu_num=8
        self.compare_upper_nums=(self.cpu_num/(2*self.afl_count)-1) if (self.cpu_num/(2*self.afl_count)-1)!=0 else 1

        #time limited
        self.time_limit=4*60*60 # second


    #----------------------------------------------------------------------
    def start_all_targets(self):
        """"""
        #1. pre for fuzzing
        self.pre_for_test()
        #2. start the fuzzing
        self.pp=[]

        #for test
        if 0:
            for item in self.targets:
                file_target_item=os.path.join(self.targets_dir,item)
                self.start_one_compare_target(file_target_item)


        for item in self.targets:
            #2.1check resource
            while(True):
                if len(self.pp)>self.compare_upper_nums:
                    for p in self.pp:
                        if not p.is_alive():
                            p.terminate()
                            self.pp.remove(p)
                            break
                    time.sleep(0.1)
                else:
                    break

            #2.2 begin to start
            file_target_item=os.path.join(self.targets_dir,item)
            
            p = multiprocessing.Process(target=self.start_one_compare_target, args=(file_target_item,))
            p.start()
            self.pp.append(p)

        logger.info("end!!")

    #----------------------------------------------------------------------
    def check_crashes_unique_in_version(self,binary_path,crahes_path):
        """
        check if the crashes is unique in the one version
        True : unique in the version
        False: a crash in both version and basik
        """
        cmd_test= binary_path+" "+ crahes_path
        cmd_check=self.check_binary+" "+crahes_path
        ret_test=os.system(cmd_test)
        ret_check=os.system(cmd_check)	
        if ret_check==0 and ret_test!=0:
            return True
        return False


    #----------------------------------------------------------------------
    def start_one_compare_target(self,file_target_item):
        """"""
        #0. set some information
        test_start_time=time.time()
        item=os.path.basename(file_target_item) 
        logger.info("begin to test %s",item)
        work_dir=os.path.join(self.workspace,item)
        if  os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        os.makedirs(work_dir)  
        afl_count=self.afl_count
        time_limit=self.time_limit
        input_from=self.input_from
        afl_input_para=self.afl_input_para        
        seed_dir=self.seed_dir

        #1. set config for the afl engines
        binary_afl_path=os.path.join(file_target_item,item+"-afl")
        afl_engine=self.afl_engine_path
        fuzzer_afl=Fuzzer(binary_afl_path , work_dir, afl_count=afl_count, 
                          time_limit=time_limit, seed_dir=seed_dir,  afl_engine=afl_engine, 
                                  input_from=input_from, afl_input_para=afl_input_para,afl_flag="afl" )

        afl_engine=self.aflgo_engine_path
        binary_aflgo_instrument_path=os.path.join(file_target_item,item+"-aflgo_instrument")
        fuzzer_aflgo_instrument=Fuzzer(binary_aflgo_instrument_path, work_dir, afl_count=afl_count, 
                                       time_limit=time_limit, seed_dir=seed_dir, afl_engine=afl_engine, 
                                               input_from=input_from, afl_input_para=afl_input_para,afl_flag="aflgo_instrument",aflgo_time="240m" )        

        #2. start the afl engines
        afl_start_time=time.time()
        fuzzer_afl.start() 

        aflgo_start_tiem=time.time()
        fuzzer_aflgo_instrument.start() 


        #3. start the listner for the crash time and check if the crash is the target crash
        first_afl_unique_crash=None
        first_aflgo_unique_crash=None
        crashes_cached=set()
        find_afl_unique_crash_flag=False
        find_aflgo_unique_crash_flag=False
        time.sleep(2)
        while(not find_afl_unique_crash_flag or not find_aflgo_unique_crash_flag):
            #check for test time
            if time.time()-test_start_time > self.alfgo_test_time_upper:
                if not find_afl_unique_crash_flag:
                    logger.info("can not find unique crash in afl")
                if not find_aflgo_unique_crash_flag:
                    logger.info("can not find unique crash in aflgo")
                break
            #check for the afl crashes
            fuzz_afl_crashes=fuzzer_afl.crashes()   
            if not find_afl_unique_crash_flag:
                for afl_crahes_path in fuzz_afl_crashes:
                    if afl_crahes_path in crashes_cached:
                        continue
                    crashes_cached.add(afl_crahes_path)
                    if self.check_crashes_unique_in_version(binary_afl_path,afl_crahes_path):
                        first_afl_unique_crash=afl_crahes_path
                        #logger.info("a crash unique: %s\n",afl_crahes_path)
                        find_afl_unique_crash_flag=True
                        fuzzer_afl.remove_fuzzer()
                        break	
            #check for tha aflgo
            fuzz_aflgo_crashes=fuzzer_aflgo_instrument.crashes()   
            if not find_aflgo_unique_crash_flag:
                for aflgo_crahes_path in fuzz_aflgo_crashes:
                    if aflgo_crahes_path in crashes_cached:
                        continue
                    crashes_cached.add(aflgo_crahes_path)
                    if self.check_crashes_unique_in_version(binary_aflgo_instrument_path,aflgo_crahes_path):
                        first_aflgo_unique_crash=aflgo_crahes_path
                        #logger.info("a crash unique: %s\n",aflgo_crahes_path)
                        find_aflgo_unique_crash_flag=True
                        fuzzer_aflgo_instrument.remove_fuzzer()
                        break	
            time.sleep(1)
        # end the while
        #3. get some information
        if find_afl_unique_crash_flag:
            first_afl_crash_time=os.path.getctime(first_afl_unique_crash)-afl_start_time
        else:
            first_afl_crash_time="timeless"
        if find_aflgo_unique_crash_flag:
            first_aflgo_crash_time=os.path.getctime(first_aflgo_unique_crash)-aflgo_start_tiem
        else:
            first_aflgo_crash_time="timeless"

        item_plot_path=os.path.join(self.plot_path,item)
        with open(item_plot_path,"wt") as f:
            f.write(item+":\n")
            f.write("first_afl_crash_time:"+str(first_afl_crash_time)+",second\n")
            f.write("first_aflgo_crash_time:"+str(first_aflgo_crash_time)+",second\n")

        logger.info("End! test %s-------------------------------------------",item)



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
    ret=os.system("pkill -9 -f \"afl-fuzz\"")
    compare_test=Compare_test()
    compare_test.start_all_targets()


    logger.info("successs")

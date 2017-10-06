#coding=utf-8
import os
import sys
import time
import signal
import shutil
import threading
import subprocess
import copy 

import logging

l = logging.getLogger("fuzzer.fuzzer")



class InstallError(Exception):
    pass


#  http://stackoverflow.com/a/41450617
class InfiniteTimer():
    """A Timer class that does not stop, unless you want it to."""

    def __init__(self, seconds, target):
        self._should_continue = False
        self.is_running = False
        self.seconds = seconds
        self.target = target
        self.thread = None

    def _handle_target(self):
        self.is_running = True
        self.target()
        self.is_running = False
        self._start_timer()

    def _start_timer(self):
        if self._should_continue: # Code could have been running when cancel was called.
            self.thread = threading.Timer(self.seconds, self._handle_target)
            self.thread.start()

    def start(self):
        if not self._should_continue and not self.is_running:
            self._should_continue = True
            self._start_timer()
        else:
            print "Timer already started or running, please wait if you're restarting."

    def cancel(self):
        if self.thread is not None:
            self._should_continue = False # Just in case thread is running and cancel fails.
            self.thread.cancel()
        else:
            pass
            #print "Timer never started or failed to initialize."



class Fuzzer(object):
    ''' Fuzzer object, spins up a fuzzing job on a binary '''

    def __init__(
        self, binary_path, work_dir, afl_count=1, library_path=None, time_limit=None, memory="8G",
        target_opts=None, extra_opts=None, create_dictionary=False,
        seeds=None, crash_mode=False, never_resume=False, qemu=True, stuck_callback=None,
        force_interval=None, job_dir=None,
        afl_engine=None,input_from='stdin',afl_input_para=None,comapre_afl=False,strategy_id='0', multi_afl=False
    ):
        '''
        :param binary_path: path to the binary to fuzz. List or tuple for multi-CB.
        :param work_dir: the work directory which contains fuzzing jobs, our job directory will go here
        :param afl_count: number of AFL jobs total to spin up for the binary
        :param library_path: library path to use, if none is specified a default is chosen
        :param timelimit: amount of time to fuzz for, has no effect besides returning True when calling timed_out
        :param seeds: list of inputs to seed fuzzing with
        :param target_opts: extra options to pass to the target
        :param extra_opts: extra options to pass to AFL when starting up
        :param crash_mode: if set to True AFL is set to crash explorer mode, and seed will be expected to be a crashing input
        :param never_resume: never resume an old fuzzing run, even if it's possible
        :param qemu: Utilize QEMU for instrumentation of binary.
        :param memory: AFL child process memory limit (default: "8G")
        :param stuck_callback: the callback to call when afl has no pending fav's
        :param job_dir: a job directory to override the work_dir/binary_name path
        
        :param afl_engine: select the fuzzing engine
        :param input_from: indicate where is the input come from, stdin or file
        :param afl_input_para: the parameter for afl to start the program
        :param comapre_afl: start a afl not supported by driller, for compare, default is False in _start_afl_instance
        :param strategy_id : the strategy_id for sort
        :param multi_afl: shelfish_afl, afl_fast, afl run together
        '''

        self.binary_path    = binary_path
        self.work_dir       = work_dir
        self.afl_count      = afl_count  #afl的数量
        self.time_limit     = time_limit #默认没有设置fuzz结束时间 按秒计算
        self.library_path   = library_path # 库路径, 什么用?
        self.target_opts    = [ ] if target_opts is None else target_opts
        self.crash_mode     = crash_mode
        self.memory         = memory
        self.qemu           = qemu
        self.force_interval = force_interval
        #add yyy
        self.input_from     = input_from
        self.afl_input_para = afl_input_para
        self.compare_afl    = comapre_afl 
        self.strategy_id    =strategy_id
        self.afl_engine     = afl_engine
        self.fzr_start_time =time.time()  #the start time of the fuzzer
        self.multi_afl      =multi_afl

        Fuzzer._perform_env_checks() #系统环境配置

        if isinstance(binary_path,basestring): #basestring 是 str和unicode的抽象基类
            self.is_multicb = False
            self.binary_id = os.path.basename(binary_path) #程序名称
        elif isinstance(binary_path,(list,tuple)): #路径名称时list或者tuple时,是cgc,这个是怎么回事
            self.is_multicb = True
            self.binary_id = os.path.basename(binary_path[0])
        else:
            raise ValueError("Was expecting either a string or a list/tuple for binary_path! It's {} instead.".format(type(binary_path)))

        # sanity check crash mode
        if self.crash_mode:
            if seeds is None:
                raise ValueError("Seeds must be specified if using the fuzzer in crash mode")
            l.info("AFL will be started in crash mode")

        self.seeds          = ["fuzz"] if seeds is None or len(seeds) == 0 else seeds
        self.job_dir  = os.path.join(self.work_dir, self.binary_id) if not job_dir else job_dir
        if not self.multi_afl:
            if self.afl_engine==config.AFL_FAST:
                self.job_dir+="-fast"
            if self.afl_engine==config.AFL:
                self.job_dir+="-normal"
            if self.afl_engine==config.AFL_YYY:
                self.job_dir+="-yyy"
            if self.afl_engine is None:
                self.job_dir+="-shelfish"
        self.in_dir   = os.path.join(self.job_dir, "input") #afl的输入目录
        self.out_dir  = os.path.join(self.job_dir, "sync") #afl和driller配合输出目录
        self.sole_out_dir  = os.path.join(self.job_dir, "sole") #对此afl的输出目录,没有和driller对比

        # sanity check extra opts
        self.extra_opts = extra_opts
        if self.extra_opts is not None:
            if not isinstance(self.extra_opts, list):
                raise ValueError("extra_opts must be a list of command line arguments")

        # base of the fuzzer package
        self.base = Fuzzer._get_base() #指向Fuzzer目录,下级必须带有bin目录

        self.start_time       = int(time.time())
        # create_dict script #创建字典
        self.create_dict_path = os.path.join(self.base, "bin", "create_dict.py") #这是一个创建字典的脚本
        # afl dictionary
        self.dictionary       = None
        # processes spun up
        self.procs            = [ ]  #所有的afl进程对象, 控制进程
        # start the fuzzer ids at 0
        self.fuzz_id          = 0
        
        ##add by yyy---------------------------------------remove the afl cache for debug
        if os.path.isdir( os.path.join(self.job_dir,"sync")):
            for item in os.listdir(  os.path.join(self.job_dir,'sync') ) :
                if "fuzzer" in item:
                    shutil.rmtree(os.path.join(self.job_dir,'sync',item)) #删除工作目录,  aflfast的重新跑有问题
        ##end------------------------------------------
                
        # test if we're resuming an old run  #判断标准是是否存在afl的输出文件
        #self.resuming         = bool(os.listdir(self.out_dir)) if os.path.isdir(self.out_dir) else False
        self.resuming  = bool('fuzzer-master' in os.listdir(self.out_dir)) if os.path.isdir(self.out_dir) else False
        if self.resuming:
            # 避免第二次跑的时候因为queue中有crash而不跑
            os.environ['AFL_SKIP_CRASHES'] = "1"
            
        # has the fuzzer been turned on?
        self._on = False  

        if never_resume and self.resuming:
            l.info("could resume, but starting over upon request")
            shutil.rmtree(self.job_dir)
            self.resuming = False

        if self.is_multicb:  #这里针对cgc的一些改进
            # Where cgc/setup's Dockerfile checks it out
            # NOTE: 'afl/fakeforksrv' serves as 'qemu', as far as AFL is concerned
            #       Will actually invoke 'fakeforksrv/multicb-qemu'
            #       This QEMU cannot run standalone (always speaks the forkserver "protocol"),
            #       but 'fakeforksrv/run_via_fakeforksrv' allows it.
            # XXX: There is no driller/angr support, and probably will never be.
            self.afl_path = shellphish_afl.afl_bin('multi-cgc')
            self.afl_path_var = shellphish_afl.afl_path_var('multi-cgc')
            self.qemu_name = 'TODO'
        else:

            p = angr.Project(binary_path)
            # Loader 类
            self.os = p.loader.main_bin.os #查看是什么系统的文件, 通过angr的静态分析功能

            self.afl_dir          = shellphish_afl.afl_dir(self.os) #根据对应的执行程序 选择对应的afl; 一般的是选择unix

            # the path to AFL capable of calling driller
            self.afl_path         = shellphish_afl.afl_bin(self.os)# 读取aflfuzz执行程序
            
            # change the afl engine
            if  not self.afl_engine is None:
                self.afl_path=self.afl_engine
               
                
            #选择对应平台的qemu执行程序
            if self.os == 'cgc':
                self.afl_path_var = shellphish_afl.afl_path_var('cgc')
            else:
                self.afl_path_var = shellphish_afl.afl_path_var(p.arch.qemu_name) #选择对应的qemu
                # set up libraries
                self._export_library_path(p)

            # the name of the qemu port used to run these binaries
            self.qemu_name = p.arch.qemu_name

        self.qemu_dir = self.afl_path_var

        l.debug("self.start_time: %r", self.start_time)
        l.debug("self.afl_path: %s", self.afl_path)
        l.debug("self.afl_path_var: %s", self.afl_path_var)
        l.debug("self.qemu_dir: %s", self.qemu_dir)
        l.debug("self.binary_id: %s", self.binary_id)
        l.debug("self.work_dir: %s", self.work_dir)
        l.debug("self.resuming: %s", self.resuming)

        # if we're resuming an old run set the input_directory to a '-'
        if self.resuming:
            l.info("[%s] resuming old fuzzing run", self.binary_id)
            self.in_dir = "-"

        else:
            # create the work directory and input directory
            try:
                os.makedirs(self.in_dir)
            except OSError:
                l.warning("unable to create in_dir \"%s\"", self.in_dir)

            # populate the input directory
            self._initialize_seeds() #初始化复制测试用例

        # look for a dictionary
        dictionary_file = os.path.join(self.job_dir, "%s.dict" % self.binary_id)
        if os.path.isfile(dictionary_file):
            self.dictionary = dictionary_file

        # if a dictionary doesn't exist and we aren't resuming a run, create a dict
        elif not self.resuming:
            # call out to another process to create the dictionary so we can
            # limit it's memory
            if create_dictionary:
                if self._create_dict(dictionary_file):
                    self.dictionary = dictionary_file  #执行Fuzzer模块下的字典创建脚本
                    l.warning("done making dictionary")
                else:
                    # no luck creating a dictionary
                    l.warning("[%s] unable to create dictionary", self.binary_id)

        if self.force_interval is None:
            l.warning("not forced")
            self._timer = InfiniteTimer(30, self._timer_callback)
        else:
            l.warning("forced")
            self._timer = InfiniteTimer(self.force_interval, self._timer_callback)

        self._stuck_callback = stuck_callback

        # set environment variable for the AFL_PATH
        os.environ['AFL_PATH'] = self.afl_path_var  #设定afl对应的qemu到 环境变量中 所有的qemu用的都是同一个
        os.environ['AFL_SKIP_CRASHES'] = '1' #避免 queue下的crash导致afl不能运行
        
    ### EXPOSED 这个函数是外放的, 调用一个内部的函数 启动afl
    def start(self):
        '''
        start fuzzing
        '''

        # spin up the AFL workers
        self._start_afl() #启动afl, 可以多个

        # start the callback timer
        self._timer.start()

        self._on = True

    @property
    def alive(self): #
        if not self._on or not len(self.stats):
            return False

        alive_cnt = 0
        if self._on:
            for fuzzer in self.stats:
                try:
                    os.kill(int(self.stats[fuzzer]['fuzzer_pid']), 0)
                    alive_cnt += 1
                except (OSError, KeyError):
                    pass

        return bool(alive_cnt)

    def kill(self):
        for p in self.procs:
            p.terminate()
            p.wait()

        if hasattr(self, "_timer"):
            self._timer.cancel()

        self._on = False

    @property ##只读属性, 变成一个变量
    def stats(self):  #读取fuzzer_stats文件
        # collect stats into dictionary
        stats = {}
        if os.path.isdir(self.out_dir):
            for fuzzer_dir in os.listdir(self.out_dir):
                stat_path = os.path.join(self.out_dir, fuzzer_dir, "fuzzer_stats")
                if os.path.isfile(stat_path):
                    stats[fuzzer_dir] = {}

                    with open(stat_path, "rb") as f:
                        stat_blob = f.read()
                        stat_lines = stat_blob.split("\n")[:-1]
                        for stat in stat_lines:
                            key, val = stat.split(":")
                            stats[fuzzer_dir][key.strip()] = val.strip()

        return stats
    
    def found_crash(self): #返回是否发现crash,这是由谁发现的crash

        return len(self.crashes()) > 0

    def add_fuzzer(self):
        '''
        add one fuzzer
        '''

        self.procs.append(self._start_afl_instance())

    def add_extension(self, name):
        """
        Spawn the mutation extension `name`
        :param name: name of extension
        :returns: True if able to spawn extension
        """

        extension_path = os.path.join(os.path.dirname(__file__), "..", "fuzzer", "extensions", "%s.py" % name)
        rpath = os.path.realpath(extension_path)

        l.debug("Attempting to spin up extension %s", rpath)

        if os.path.exists(extension_path):
            args = [sys.executable, extension_path, self.binary_path, self.out_dir]

            outfile_leaf = "%s-%d.log" % (name, len(self.procs))
            outfile = os.path.join(self.job_dir, outfile_leaf)
            with open(outfile, "wb") as fp:
                p = subprocess.Popen(args, stderr=fp)
            self.procs.append(p)
            return True

        return False

    def add_fuzzers(self, n):
        for _ in range(n):
            self.add_fuzzer()

    def remove_fuzzer(self):
        '''
        remove one fuzzer
        '''

        try:
            f = self.procs.pop()
        except IndexError:
            l.error("no fuzzer to remove")
            raise ValueError("no fuzzer to remove")

        f.kill()

    def remove_fuzzers(self, n):
        '''
        remove multiple fuzzers
        '''

        if n > len(self.procs):
            l.error("not more than %u fuzzers to remove", n)
            raise ValueError("not more than %u fuzzers to remove" % n)

        if n == len(self.procs):
            l.warning("removing all fuzzers")

        for _ in range(n):
            self.remove_fuzzer()

    def _get_crashing_inputs(self, signals):
        """
        Retrieve the crashes discovered by AFL. Only return those crashes which
        recieved a signal within 'signals' as the kill signal.

        :param signals: list of valid kill signal numbers
        :return: a list of strings which are crashing inputs
        """

        crashes = set()
        for fuzzer in os.listdir(self.out_dir):
            crashes_dir = os.path.join(self.out_dir, fuzzer, "crashes")

            if not os.path.isdir(crashes_dir):
                # if this entry doesn't have a crashes directory, just skip it
                continue

            for crash in os.listdir(crashes_dir):
                if crash == "README.txt":
                    # skip the readme entry
                    continue

                attrs = dict(map(lambda x: (x[0], x[-1]), map(lambda y: y.split(":"), crash.split(","))))
                try:
                    if int(attrs['sig']) not in signals:
                        continue
                except Exception as e:
                    continue
                crash_path = os.path.join(crashes_dir, crash)
                with open(crash_path, 'rb') as f:
                    crashes.add(f.read())

        return list(crashes)

    def crashes(self):
        """
        Retrieve the crashes discovered by AFL. Since we are now detecting flag
        page leaks (via SIGUSR1) we will not return these leaks as crashes.
        Instead, these 'crashes' can be found with the leaks function.
        :return: a list of strings which are crashing inputs
        """

        return self._get_crashing_inputs([signal.SIGSEGV, signal.SIGILL])

    def queue(self, fuzzer='fuzzer-master'): #得到queue下的测试用例
        '''
        retrieve the current queue of inputs from a fuzzer
        :return: a list of strings which represent a fuzzer's queue
        '''

        if not fuzzer in os.listdir(self.out_dir):
            raise ValueError("fuzzer '%s' does not exist" % fuzzer)

        queue_path = os.path.join(self.out_dir, fuzzer, 'queue')
        queue_files = filter(lambda x: x != ".state", os.listdir(queue_path))

        queue_l = [ ]
        for q in queue_files:
            with open(os.path.join(queue_path, q), 'rb') as f:
                queue_l.append(f.read())

        return queue_l

    def bitmap(self, fuzzer='fuzzer-master'):
        '''
        retrieve the bitmap for the fuzzer `fuzzer`.
        :return: a string containing the contents of the bitmap.
        '''

        if not fuzzer in os.listdir(self.out_dir):
            raise ValueError("fuzzer '%s' does not exist" % fuzzer)

        bitmap_path = os.path.join(self.out_dir, fuzzer, "fuzz_bitmap")

        bdata = None
        try:
            with open(bitmap_path, "rb") as f:
                bdata = f.read()
        except IOError:
            pass

        return bdata

    def timed_out(self): 
        if self.time_limit is None:
            return False #默认是false
        return time.time() - self.start_time > self.time_limit

    def pollenate(self, testcases): #这里可能是利用新的测试用例的函数
        '''
        pollenate a fuzzing job with new testcases

        :param testcases: list of strings representing new inputs to introduce
        '''

        nectary_queue_directory = os.path.join(self.out_dir, 'pollen', 'queue')
        if not 'pollen' in os.listdir(self.out_dir):
            os.makedirs(nectary_queue_directory)

        pollen_cnt = len(os.listdir(nectary_queue_directory))

        for tcase in testcases:
            with open(os.path.join(nectary_queue_directory, "id:%06d,src:pollenation" % pollen_cnt), "w") as f:
                f.write(tcase)

            pollen_cnt += 1

    ### FUZZ PREP

    ##annotation by yyy------------------------------
    def _initialize_seeds(self):  # 将初始化的测试用例保存到input目录下
        '''
        populate the input directory with the seeds specified
        '''
 
        assert len(self.seeds) > 0, "Must specify at least one seed to start fuzzing with"
 
        l.debug("initializing seeds %r", self.seeds)
 
        template = os.path.join(self.in_dir, "seed-%d")
        for i, seed in enumerate(self.seeds):
            with open(template % i, "wb") as f:
                f.write(seed)
    ##end--------------------------------------------------------

    ### DICTIONARY CREATION
    def _create_dict(self, dict_file):

        l.warning("creating a dictionary of string references within binary \"%s\"",
                self.binary_id)

        args = [sys.executable, self.create_dict_path]
        args += self.binary_path if self.is_multicb else [self.binary_path]

        with open(dict_file, "wb") as dfp:
            p = subprocess.Popen(args, stdout=dfp)
            retcode = p.wait()

        return retcode == 0 and os.path.getsize(dict_file)

    ### AFL SPAWNERS AFL生成器

#     def _start_afl_instance(self):
# 
#         args = [self.afl_path] #aflfuzz的路径
# 
#         args += ["-i", self.in_dir]
#             
#         args += ["-o", self.out_dir] 
#         
#         if not self.afl_engine is None  and "fast" in self.afl_engine:
#             args += ["-s", self.strategy_id] #配置策略
# 
#         if self.qemu:
#             args += ["-m", self.memory]
#             args += ["-Q"]
#             
#         if self.crash_mode:
#             args += ["-C"]
# 
#         if self.fuzz_id == 0:
#             args += ["-M", "fuzzer-master"]
#             outfile = "fuzzer-master.log"
#         else:
#             args += ["-S", "fuzzer-%d" % self.fuzz_id]  #启动多个afl
#             outfile = "fuzzer-%d.log" % self.fuzz_id
# 
#         if self.dictionary is not None:
#             args += ["-x", self.dictionary]
# 
#         if self.extra_opts is not None:
#             args += self.extra_opts
# 
#         # auto-calculate timeout based on the number of binaries
#         if self.is_multicb:
#             args += ["-t", "%d+" % (1000 * len(self.binary_path))] #如果是cgc 就要加这个
# 
#         args += ["--"]
#         args += self.binary_path if self.is_multicb else [self.binary_path]
#         
#         ##add by yyy-------------------------------------
#         if self.input_from=='stdin':
#             pass
#         elif self.input_from=='file':
#             args+=self.afl_input_para
#         else:
#             l.error("the parameter to start the AFL is error")  
#         ##end-----------------------------------------------------
#         
#         args.extend(self.target_opts)
# 
#         l.debug("execing: %s > %s", ' '.join(args), outfile) #执行信息的输出
# 
#         # increment the fuzzer ID
#         self.fuzz_id += 1 #id会自增
#         
#         if self.compare_afl:
#             args_cpoy=copy.copy(args) #copy the list
#             args_cpoy[4]=self.sole_out_dir # modify the -o parameter
#         
#         time.sleep(1)
#         print args
#         #drop the output
#         with open('/dev/null', 'wb') as devnull:
#             fp = devnull
#             if self.compare_afl:
#                 #每启动一个driller的,就会启动一个对比的,对比afl的引擎数量是一致的
#                 self.procs.append(subprocess.Popen(args_cpoy, stdout=fp, close_fds=True))#添加,有助于关闭
#             
#             return subprocess.Popen(args, stdout=fp, close_fds=True) 

    def _start_afl_instance(self):
        afl_path_list=list()
        if self.multi_afl :
            afl_path_list.append(config.AFL_FAST)
            #afl_path_list.append(config.AFL_YYY)
            afl_path_list.append(config.AFL_Shellfish_unix)
            afl_path_list.append(config.AFL)
        else:
            afl_path_list.append(self.afl_path)
        
        for choose_afl in    afl_path_list: 
            #开启一个选定的afl引擎
            args = [choose_afl]  # aflfuzz的路径
            args += ["-i", self.in_dir]
            args += ["-o", self.out_dir] 
            
            if not choose_afl is None  and "fast" in choose_afl:
                args += ["-s", self.strategy_id]  # 配置策略
                
            if self.qemu:
                args += ["-m", self.memory]
                args += ["-Q"]
            if self.crash_mode:
                args += ["-C"]
            if self.fuzz_id == 0:
                args += ["-M", "fuzzer-master"]
                outfile = "fuzzer-master.log"
            else:
                args += ["-S", "fuzzer-%d" % self.fuzz_id]  # 启动多个afl
                outfile = "fuzzer-%d.log" % self.fuzz_id
            if self.dictionary is not None:
                args += ["-x", self.dictionary]
            if self.extra_opts is not None:
                args += self.extra_opts
                # auto-calculate timeout based on the number of binaries
            if self.is_multicb:
                args += ["-t", "%d+" % (1000 * len(self.binary_path))]  # 如果是cgc 就要加这个
            args += ["--"]
            args += self.binary_path if self.is_multicb else [self.binary_path]
                
            ##add by yyy-------------------------------------
            if self.input_from == 'stdin':
                pass
            elif self.input_from == 'file':
                args += self.afl_input_para
            else:
                l.error("the parameter to start the AFL is error")  
            ##end-----------------------------------------------------
                
            args.extend(self.target_opts)
            l.debug("execing: %s > %s", ' '.join(args), outfile)  # 执行信息的输出
            # increment the fuzzer ID
            self.fuzz_id += 1  # id会自增
            if self.compare_afl:
                args_cpoy = copy.copy(args)  # copy the list
                args_cpoy[4] = self.sole_out_dir  # modify the -o parameter
            time.sleep(1)
            print args
            # drop the output
            with open('/tmp/afl', 'wb') as devnull:
                fp = devnull
                if self.compare_afl:
                    # 每启动一个driller的,就会启动一个对比的,对比afl的引擎数量是一致的
                    self.procs.append(subprocess.Popen(args_cpoy, stdout=fp, close_fds=True))  # 添加,有助于关闭
                self.procs.append(subprocess.Popen(args, stdout=fp, close_fds=True))    
                
                #return subprocess.Popen(args, stdout=fp, close_fds=True)         
        

    def _start_afl(self):
        '''
        start up a number of AFL instances to begin fuzzing
        '''

        # spin up the master AFL instance
        #master = self._start_afl_instance() # the master fuzzer 启动了一个masterafl master是一个 Popen 对象
        #self.procs.append(master)
        self._start_afl_instance()

        if self.afl_count > 1: #判断是否启动多个afl
            #driller = self._start_afl_instance()
            #self.procs.append(driller)
            self._start_afl_instance()
            
            
        # only spins up an AFL instances if afl_count > 1
        for _ in range(2, self.afl_count):
            #slave = self._start_afl_instance()
            #self.procs.append(slave)
            self._start_afl_instance()

    ### UTIL

    @staticmethod
    def _perform_env_checks():
        err = ""

        # check for afl sensitive settings
        with open("/proc/sys/kernel/core_pattern") as f:
            if not "core" in f.read():
                err += "AFL Error: Pipe at the beginning of core_pattern\n"
                err += "execute 'echo core | sudo tee /proc/sys/kernel/core_pattern'\n"

        # This file is based on a driver not all systems use
        # http://unix.stackexchange.com/questions/153693/cant-use-userspace-cpufreq-governor-and-set-cpu-frequency
        # TODO: Perform similar performance check for other default drivers.
        if os.path.exists("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"):
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor") as f:
                if not "performance" in f.read():
                    err += "AFL Error: Suboptimal CPU scaling governor\n"
                    err += "execute 'cd /sys/devices/system/cpu; echo performance | sudo tee cpu*/cpufreq/scaling_governor'\n"

        # TODO: test, to be sure it doesn't mess things up
        with open("/proc/sys/kernel/sched_child_runs_first") as f:
            if not "1" in f.read():
                err += "AFL Warning: We probably want the fork() children to run first\n"
                err += "execute 'echo 1 | sudo tee /proc/sys/kernel/sched_child_runs_first'\n"

        # Spit out all errors at the same time
        if err != "":
            l.error(err)
            raise InstallError(err)


    @staticmethod
    def _get_base():
        '''
        find the directory containing bin, there should always be a directory
        containing bin below base intially
        '''
        base = os.path.dirname(__file__)

        while not "bin" in os.listdir(base) and os.path.abspath(base) != "/":
            base = os.path.join(base, "..")

        if os.path.abspath(base) == "/":  
            raise InstallError("could not find afl install directory")

        return base

    def _export_library_path(self, p):
        '''
        export the correct library path for a given architecture
        '''
        path = None

        if self.library_path is None:
            directory = None
            if p.arch.qemu_name == "aarch64":
                directory = "arm64"
            if p.arch.qemu_name == "i386":
                directory = "i386"
            if p.arch.qemu_name == "x86_64":
                directory = "x86_64"
            if p.arch.qemu_name == "mips":
                directory = "mips"
            if p.arch.qemu_name == "mipsel":
                directory = "mipsel"
            if p.arch.qemu_name == "ppc":
                directory = "powerpc"
            if p.arch.qemu_name == "arm":
                # some stuff qira uses to determine the which libs to use for arm
                with open(self.binary_path, "rb") as f: progdata = f.read(0x800)
                if "/lib/ld-linux.so.3" in progdata:
                    directory = "armel"
                elif "/lib/ld-linux-armhf.so.3" in progdata:
                    directory = "armhf"

            if directory is None:
                l.warning("architecture \"%s\" has no installed libraries", p.arch.qemu_name)
            else:
                path = os.path.join(self.afl_dir, "..", "fuzzer-libs", directory)
        else:
            path = self.library_path

        if path is not None:
            l.debug("exporting QEMU_LD_PREFIX of '%s'", path)
            os.environ['QEMU_LD_PREFIX'] = path

    def _timer_callback(self):
        if self._stuck_callback is not None:
            # check if afl has pending fav's
            if int(self.stats['fuzzer-master']['pending_favs']) == 0 or self.force_interval is not None:
                self._stuck_callback(self)

    def __del__(self):
        self.kill()


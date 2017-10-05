#coding=utf-8
#流程
#1. 编译所有的lava1程序
#2. 距离计算
#3. 根据距离进行插桩

import os
import shutil
import subprocess
import copy
import logging
import coloredlogs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("file")
#l.setLevel(logging.DEBUG)
########################################################################
class LAVA1:
    """"""

    #----------------------------------------------------------------------
    def __init__(self,compile_flag="gcc"):
        """Constructor"""
        self._global_config()
        
        #get from para
        self.compiler_flag=compile_flag
        
        #some init functions
        self._read_branches()
        
        #
        self.special=["file-5.22.1415_R_0x12345678-0x12545678"]

    #----------------------------------------------------------------------
    def _global_config(self):
        """"""
        #absolute path
        self.output_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava1-output"
        self.aflgo_clang="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/afl-clang-fast"
        self.aflgo_clang_pp="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/afl-clang-fast++"
        self.lava1_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/LAVA-1"
        self.branches_path=os.path.join(self.lava1_dir,"branches.txt")        
        self.script_getdistance="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/scripts/genDistance.sh"
        self.targets_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava-tools/targets"
        self.python_xiaosa_path="/home/xiaosatianyu/.virtualenvs/xiaosa/bin/python"
        
        #global variable
        self.all_compiler_flag=["gcc","clang","aflgo_get","aflgo_instrument"]
        self.extendion_num=3
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
    def checkout_files_all_targets(self):
        """"""
        file_source_dir=os.path.join(self.lava1_dir,"file-5.22")
        for item in self.branches:
            file_source_item_dir=os.path.join(self.lava1_dir,item)
            if os.path.exists(file_source_item_dir):
                continue
            shutil.copytree(file_source_dir, file_source_item_dir, symlinks=True)
            args = ["git","checkout",item[10:]]
            p = subprocess.Popen(args, cwd=file_source_item_dir,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)            
            ret=p.wait()
            if ret != 0:
                logger( "checkoout %s fail"%item)
                return False             
        logger.info("checkout all files successful")
    #----------------------------------------------------------------------
    def _get_configure_para_instrumented_with_distance(self):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def _get_configure_para_for_distance(self,file_source_item_dir):
        """"""
        item=os.path.basename(file_source_item_dir)
        para_str="./configure --enable-static --disable-shared " 
        prefix=file_source_item_dir+"/lava-install"
        CFLAGS="-ggdb -fvisibility=default"
        CXXFLAGS="-ggdb -fvisibility=default"
        qutation='\"'      
        #for aflgo
        CC=self.aflgo_clang
        CXX=self.aflgo_clang_pp
        target=os.path.join(self.output_dir,item,"BBtargets.txt")
        outdir=os.path.join(self.output_dir,item)
        other_flag=" -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps"       
        #add to the flags
        CFLAGS+=" -targets="+target+" -outdir="+outdir+other_flag
        CXXFLAGS+=" -targets="+target+" -outdir="+outdir+other_flag      
        #total
        para_str=para_str\
            +" --prefix="+prefix\
            +" CC="+CC\
            +" CXX="+CXX\
            +" CFLAGS="+qutation+CFLAGS+qutation\
            +" CXXFLAGS="+qutation+CXXFLAGS+qutation 
        
        return [para_str]
    #----------------------------------------------------------------------
    def _get_configure_para_with_gcc(self,file_source_item_dir):
        """"""
        para_str="./configure --enable-static --disable-shared "
        prefix=file_source_item_dir+"/lava-install"
        CC="gcc"
        CXX="g++"
        CFLAGS="-ggdb -fvisibility=default"
        CXXFLAGS="-ggdb -fvisibility=default"  
        qutation='\"' 
        #total
        para_str=para_str\
            +" --prefix="+prefix\
            +" CC="+CC\
            +" CXX="+CXX\
            +" CFLAGS="+qutation+CFLAGS+qutation\
            +" CXXFLAGS="+qutation+CXXFLAGS+qutation 
        logger.info("compiler the binary with gcc")
        return [para_str]
    #----------------------------------------------------------------------
    def _get_configure_para_with_normal_clang(self,file_source_item_dir):
        """"""
        para_str="./configure --enable-static --disable-shared " 
        prefix=file_source_item_dir+"/lava-install"
        CFLAGS="-ggdb -fvisibility=default"
        CXXFLAGS="-ggdb -fvisibility=default" 
        CC="clang"
        CXX="clang++"        
        qutation='\"' 
        #total
        para_str=para_str\
            +" --prefix="+prefix\
            +" CC="+CC\
            +" CXX="+CXX\
            +" CFLAGS="+qutation+CFLAGS+qutation\
            +" CXXFLAGS="+qutation+CXXFLAGS+qutation
        
        return [para_str]
        
    #----------------------------------------------------------------------
    def _build_file_each(self,file_source_item_dir):
        """"""
        item=os.path.basename(file_source_item_dir)
        file_target_item_path=os.path.join(self.targets_dir,item,item+"-"+self.compiler_flag)
        if self.compiler_flag=="gcc" and  os.path.exists(file_target_item_path):
            #logger.info("%s with %s has been built, do not need build again",item,self.compiler_flag)
            return True
        output_information=os.path.join(self.output_dir,item,"BBcalls.txt")
        if self.compiler_flag=="aflgo_get" and os.path.exists(output_information):
            return
        #0 build new
        pwd=file_source_item_dir
        item=os.path.basename(file_source_item_dir)
        f=open("/tmp/log","wt")
        #1.make distclean if there has a makefile
        if os.path.exists(os.path.join(pwd,"Makefile")):
            args = ["make","distclean"]
            p = subprocess.Popen(args,cwd=pwd,stdout=f, stderr=subprocess.STDOUT)            
            ret=p.wait()
            if ret < 0:
                logger.info("make distclean fail,but not return:%s"%item)
        #2. autoreconf -f -i
        args = ["autoreconf","-i","-f"]
        p = subprocess.Popen(args, cwd=pwd,stdout=f, stderr=subprocess.STDOUT)            
        ret=p.wait()
        if ret != 0:
            logger.info("autoreconf fail:%s"%item)
            return False
        #3. configure
        if  self.compiler_flag=="clang":
            args=self._get_configure_para_with_normal_clang(file_source_item_dir)
            logger.info("compiler the binary with normal clang")
        elif  self.compiler_flag=="aflgo_get":
            args=self._get_configure_para_for_distance(file_source_item_dir)
            logger.info("compiler the binary with aflgo_get")
        else:
            args=self._get_configure_para_with_gcc(file_source_item_dir)
            logger.info( "compiler the binary with aflgo")
        
        p = subprocess.Popen(args,shell=True, cwd=pwd,stdout=f, stderr=subprocess.STDOUT)            
        ret=p.wait()
        if ret != 0:
            logger.info( "configure fail:%s"%item)
            return False         
        #4. make
        args = ["make","-j8"]     
        p = subprocess.Popen(args, cwd=pwd,stdout=f, stderr=subprocess.STDOUT)            
        ret=p.wait()
        if ret != 0:
            logger.info( "make fail:%s"%item)
            return False 
        logger.info( "build %s successful"%item)
            
    #----------------------------------------------------------------------
    def pre_deal_for_aflgo_get(self,file_item_output):
        """"""
        #deal with bbnames
        BB_names_path=os.path.join(file_item_output,"BBnames.txt")
        BB_names_path_temp=os.path.join(file_item_output,"BBnames2.txt")
        args="cat "+BB_names_path+" | rev | cut -d: -f2- | rev | sort | uniq > "+BB_names_path_temp +" && mv "+BB_names_path_temp+" "+BB_names_path
        ret=os.system(args)
        if ret !=0:
            logger.error("error in dealing with bbnamess")
        
        #deal with bbcalls
        BB_calls_path=os.path.join(file_item_output,"BBcalls.txt")
        BB_calls_path_temp=os.path.join(file_item_output,"BBcalls2.txt")      
        args="cat "+BB_calls_path+ "  | sort | uniq > "+BB_calls_path_temp+" && mv "+BB_calls_path_temp+" "+BB_calls_path
        ret=os.system(args)
        if ret !=0:
            logger.error("error in dealing with bbnamess")        
        
    #----------------------------------------------------------------------
    def calculate_distance(self):
        """"""
        for item in self.special:
            file_item_output=os.path.join(self.output_dir,item)
            if not os.path.exists(file_item_output):
                continue
            self.pre_deal_for_aflgo_get(file_item_output)
            file_item__src_dir=os.path.join(self.lava1_dir,item,"src")
            args = [self.script_getdistance+" "+file_item__src_dir+" "+file_item_output+" "+"file"]
            logger.info( "calculate the distance of %s"%item)
            with open("/tmp/getdistance.log","wt") as f:
                p = subprocess.Popen(args,shell=True, stdout=f, stderr=subprocess.STDOUT)            
                ret=p.wait()
                if ret ==0:
                    logger.info( "calculate distance with aflgo sucess: %s"%item)
                else:
                    self.exclude.update([item])
                    shutil.rmtree(file_item_output)
                    logger.info( "calculate distance with aflgo fail: %s",item )
    #----------------------------------------------------------------------
    def _set_targets_item(self):
        """
        if has the BBtargets.txt, add to the targets set, and move the BBtargets.txt to the sub-output dir
        """
        if self.compiler_flag !="aflgo_get":
            self.targets=copy.deepcopy(self.branches)
            return
        for item in self.branches:
            file_target_output_item=os.path.join(self.output_dir,item)
            file_target_item_bbtargets_path=os.path.join(self.targets_dir,item,"BBtargets.txt")
            if not os.path.exists(file_target_item_bbtargets_path):
                #remove the output dir if do not have target
                if os.path.exists(file_target_output_item):
                    shutil.rmtree(file_target_output_item)           
                continue
            if  not os.path.exists(file_target_output_item):
                os.makedirs(file_target_output_item)
            shutil.copy(file_target_item_bbtargets_path, file_target_output_item)
            #add to the targets
            self.targets.update([item])

    #----------------------------------------------------------------------
    def get_all_files_crash(self):
        """""" 
        for item  in self.branches:     
            #0.check the file exist
            file_item_src_path=os.path.join(self.lava1_dir,item,"src","file")
            if not os.path.exists(file_item_src_path):
                continue
            #1. get the file
            target_item_dir=os.path.join(self.targets_dir,item)
            if not os.path.exists(target_item_dir):
                os.makedirs(target_item_dir) 
            file_target_item_binary_path=os.path.join(self.targets_dir,item,item+"-"+self.compiler_flag)
            if not os.path.exists(file_target_item_binary_path):
                shutil.copy(file_item_src_path, file_target_item_binary_path)     
            #2. get the crash
            crash_item_src_path=os.path.join(self.lava1_dir,item,"CRASH_INPUT")
            crash_target_item_path=os.path.join(self.targets_dir,item,"CRASH_INPUT")
            if not os.path.exists(crash_target_item_path):
                shutil.copy(crash_item_src_path, crash_target_item_path)            
                

    #----------------------------------------------------------------------
    def make_BBtargets(self):
        """"""
        self._extend_crash_to_target()
    
    #----------------------------------------------------------------------
    def _extend_crash_to_target(self):
        """
        extent the crash line to BBtargets 
        """
        for item in self.branches: 
            crash_line__target_item_path=os.path.join(self.targets_dir,item,"crash_line")
            target_item_bbtargets_path=os.path.join(self.targets_dir,item,"BBtargets.txt")
            if not os.path.exists(crash_line__target_item_path):
                continue
            
            # if there are some quit information in the content
            flag=True
            content=[]
            with open(crash_line__target_item_path,"rt") as f:
                for line in f.readlines():
                    #some special crash
                    if ".S" in line:
                        flag=False
                        break
                    content.append(line)
            if not flag:
                if os.path.exists(target_item_bbtargets_path):
                    os.remove(target_item_bbtargets_path)
                continue
            
            new_content= copy.deepcopy(content)
            for lines in content:
                if "\n" ==lines:
                    continue
                file_name=lines.split(":")[0]
                loc_num  =int(lines.split(":")[1])
                for j in xrange(self.extendion_num):
                    new_loc1=str(loc_num+j)
                    new_loc2=str(loc_num-j)
                    new_target1=file_name+":"+new_loc1+"\n"
                    new_target2=file_name+":"+new_loc2+"\n"
                    if not new_target1 in new_content:
                        new_content.append(new_target1)
                    if not new_target2 in new_content:
                        new_content.append(new_target2)
            new_content.sort()
            with open(target_item_bbtargets_path,"wt") as f:
                for line in new_content:
                    f.write(line)   
                    
            #move the BBtargets to the sub_output dir  
            self._move_each_BBtargets_to_outdir(target_item_bbtargets_path, item)
        logger.info( "crash_line extend to BBtargets.txt end----------------")
    
    #----------------------------------------------------------------------
    def _move_each_BBtargets_to_outdir(self,BBtarget_path,item):
        """"""
        output_item_dir=os.path.join(self.output_dir,item)
        if not os.path.exists(output_item_dir):
            os.makedirs(output_item_dir)
        shutil.copy(BBtarget_path, output_item_dir)            

    #----------------------------------------------------------------------
    def build_files_all(self,compiler_flag="gcc"):
        """
        @compiler_flag: gcc,clang,aflgo_get,aflgo_instrument
        """
        #copy all the branches
        self.checkout_files_all_targets()
        #build all the branches
        self.compiler_flag=compiler_flag
        #set the target after the compiler_flag set
        self._set_targets_item()
        for item in self.targets:
            file_target_dir=os.path.join(self.lava1_dir,item)
            flag=self._build_file_each(file_target_dir)    

    #----------------------------------------------------------------------
    def build_with_aflgo_get(self):
        """"""
        #1. make BBtarget and move the ouput dir
        self.make_BBtargets()
        #2. build all files with aflgo, but not instrument
        self.build_files_all(compiler_flag="aflgo_get")
        #3. get the output
        self.get_all_files_crash()
        self.calculate_distance()
    #----------------------------------------------------------------------
    def build_with_gcc(self):
        """"""
        self.build_files_all(compiler_flag="gcc")
        self.get_all_files_crash()
      

if __name__ == '__main__':
    coloredlogs.install()
    logger.info("start")
    lava1=LAVA1(compile_flag="gcc")
    #lava1.build_with_gcc()
    lava1.build_with_aflgo_get()
    logger.info("successs")

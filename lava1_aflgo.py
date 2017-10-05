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
        self.aflgp_flag=False
        self.targets=set()
        self.exclude=set()
        self.branches=set()
        
        self.compiler_flag=compile_flag
        self._read_branches()
        #set the target set
        self._set_targets_item()

    #----------------------------------------------------------------------
    def _global_config(self):
        """"""
        self.output_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava1-output"
        self.aflgo_clang="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/afl-clang-fast"
        self.aflgo_clang_pp="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/afl-clang-fast++"
        self.lava1_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/LAVA-1"
        self.branch_path=os.path.join(self.lava1_dir,"branches.txt")        
        self.script_getdistance="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/scripts/genDistance.sh"
        self.targets_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/yy-lava-tools/targets"
        self.python_xiaosa="/home/xiaosatianyu/.virtualenvs/xiaosa/bin/python"
        
        #global variable
        self.all_compiler_flag=["gcc","clang","aflgo_get","aflgo_instrument"]

    #----------------------------------------------------------------------
    def _read_branches(self):
        """"""
        with open(self.branch_path,"rt") as f:
            for lines in f.readlines():
                self.branches.update(["file-5.22."+lines.split("\n")[0]])
    #----------------------------------------------------------------------
    def checkout_files_all_targets(self):
        """"""
        file_source_dir=os.path.join(self.lava1_dir,"file-5.22")
        for item in self.branches:
            file_target_dir=os.path.join(self.lava1_dir,item)
            if os.path.exists(file_target_dir):
                continue
            shutil.copytree(file_source_dir, file_target_dir, symlinks=True)
            args = ["git","checkout",item[10:]]
            p = subprocess.Popen(args, cwd=file_target_dir,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)            
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
    def _get_configure_para_for_distance(self,file_target):
        """"""
        para_str="./configure --enable-static --disable-shared " 
        prefix=file_target_dir+"/lava-install"
        CFLAGS="-ggdb -fvisibility=default"
        CXXFLAGS="-ggdb -fvisibility=default"
        qutation='\"'      
        #for aflgo
        CC=self.aflgo_clang
        CXX=self.aflgo_clang_pp        
        target=os.path.join(self.output_dir,file_target,"BBtargets.txt")
        outdir=os.path.join(self.output_dir,file_target)
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
    def _get_configure_para_with_gcc(self,file_target_dir):
        """"""
        para_str="./configure --enable-static --disable-shared "
        prefix=file_target_dir+"/lava-install"
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
    def _get_configure_para_with_normal_clang(self,file_target_dir):
        """"""
        para_str="./configure --enable-static --disable-shared " 
        prefix=file_target_dir+"/lava-install"
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
    def _build_file_each(self,file_target_dir):
        """"""
        item=os.path.basename(file_target_dir)
        file_save_path=os.path.join(self.targets_dir,item,item+"-"+self.compiler_flag)
        if os.path.exists(file_save_path):
            #logger.info("%s with %s has been built, do not need build again",item,self.compiler_flag)
            return True
        #0 build new
        pwd=file_target_dir
        item=os.path.basename(file_target_dir)
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
            args=self._get_configure_para_with_normal_clang(file_target_dir)
            logger.info("compiler the binary with normal clang")
        elif  self.compiler_flag=="aflgo_get":
            args=self._get_configure_para_for_distance(file_target_dir)
            logger.info("compiler the binary with aflgo_get")
        else:
            args=self._get_configure_para_with_gcc(file_target_dir)
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
    def build_files_all(self,compiler_flag="gcc"):
        """
        @compiler_flag: gcc,clang,aflgo_get,aflgo_instrument
        """
        #copy all the branches
        self.checkout_files_all_targets()
        #build all the branches
        self.compiler_flag=compiler_flag
        for item in self.targets:
            file_target_dir=os.path.join(self.lava1_dir,item)
            flag=self._build_file_each(file_target_dir)
    
            
    #----------------------------------------------------------------------
    def calculate_distance(self):
        """"""
        for item in self.targets:
            file_target_output=os.path.join(self.output_dir,item)
            file_build_dir=os.path.join(self.lava1_dir,item,"src")
            args = [self.script_getdistance+" "+file_build_dir+" "+file_target_output+" "+item]
            logger.info( "calculate the distance of %s"%item)
            with open("/tmp/getdistance.log","wt") as f:
                p = subprocess.Popen(args,shell=True, stdout=f, stderr=subprocess.STDOUT)            
                ret=p.wait()
                if ret ==0:
                    logger.info( "calculate distance with aflgo sucess: %s"%item)
                else:
                    self.exclude.append(item)
                    shutil.rmtree(file_target_output)
                    logger.info( "calculate distance with aflgo fail: %s"%item )
    #----------------------------------------------------------------------
    def _set_targets_item(self):
        """
        if has the BBtargets.txt, add to the targets set, and move the BBtargets.txt to the sub-output dir
        """
        if self.compiler_flag !="aflgo_get":
            self.targets=copy.deepcopy(self.branches)
            return
        for item in self.branches:
            file_target_output=os.path.join(self.output_dir,item)
            file_target_source_path=os.path.join(self.targets_dir,item,"BBtargets.txt")
            if not os.path.exists(file_target_source_path):
                #remove the output dir if do not have target
                if os.path.exists(file_target_output):
                    shutil.rmtree(file_target_output)           
                continue
            if  os.path.exists(file_target_output):
                shutil.rmtree(file_target_output)
            os.makedirs(file_target_output)
            shutil.copy(file_target_source_path, file_target_output)
            #add to the targets
            self.targets.update([item])

    #----------------------------------------------------------------------
    def get_all_files_crash(self):
        """"""
                
        for item  in self.branches:     
            #0.check the file exist
            file_src_path=os.path.join(self.lava1_dir,item,"src","file")
            if not os.path.exists(file_src_path):
                continue
            #1. get the file
            sub_target_dir=os.path.join(self.targets_dir,item)
            if not os.path.exists(sub_target_dir):
                os.makedirs(sub_target_dir) 
            file_target_path=os.path.join(self.targets_dir,item,item+"-"+self.compiler_flag)
            if not os.path.exists(file_target_path):
                shutil.copy(file_src_path, file_target_path)     
            #2. get the crash
            crash_src_path=os.path.join(self.lava1_dir,item,"CRASH_INPUT")
            crash_target_path=os.path.join(self.targets_dir,item,"CRASH_INPUT")
            if not os.path.exists(crash_target_path):
                shutil.copy(crash_src_path, crash_target_path)            
                

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
            crash_line_path=os.path.join(self.targets_dir,item,"crash_line")
            BBtarget_path=os.path.join(self.targets_dir,item,"BBtargets.txt")
            if not os.path.exists(crash_line_path):
                continue
            content=[]
            with open(crash_line_path,"rt") as f:
                for line in f.readlines():
                    content.append(line)
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
            with open(BBtarget_path,"wt") as f:
                for line in new_content:
                    f.write(line)   
                    
            #move the BBtargets to the sub_output dir  
            self._move_each_BBtargets_to_outdir(BBtarget_path, item)
        logger.info( "crash_line extend to BBtargets.txt end----------------"             )
    
    #----------------------------------------------------------------------
    def _move_each_BBtargets_to_outdir(self,BBtarget_path,item):
        """"""
        sub_out_dir=os.path.join(self.output_dir,item)
        if not os.path.exists(sub_out_dir):
            os.makedirs(sub_out_dir)
        shutil.copy(BBtarget_path, sub_out_dir)            


    #----------------------------------------------------------------------
    def build_with_aflgo_get(self):
        """"""
        #1. make BBtarget and move the ouput dir
        self.make_BBtargets()
        #2. build all files with aflgo, but not instrument
        self.build_files_all(compiler_flag="aflgo_get")
        #3. get the output
        self.get_all_files_crash()
    
    #----------------------------------------------------------------------
    def build_with_gcc(self):
        """"""
        self.build_files_all(compiler_flag="gcc")
        self.get_all_files_crash()
        

if __name__ == '__main__':
    coloredlogs.install()
    logger.info("start")
    lava1=LAVA1(compile_flag="gcc")
    lava1.build_with_gcc()
    
    logger.info("successs")

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
    def __init__(self,compile_flag="gcc",recalculate=False,force_rebuild=False):
        """Constructor"""
        self._global_config()
        
        #get from para
        self.compiler_flag=compile_flag
        self.recalculate=recalculate # default not calculate the distance again
        self.force_rebuild=force_rebuild
        
        #some init functions
        self._read_branches()
        
        #self.special=["file-5.22.1415_R_0x12345678-0x12545678"]
        self.test_targets=None

    #----------------------------------------------------------------------
    def _global_config(self):
        """"""
        #absolute path
        self.output_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava1-output"
        self.lava1_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/LAVA-1"
        self.branches_path=os.path.join(self.lava1_dir,"branches.txt") 
        self.targets_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava-tools/targets"
        
        self.aflgo_clang="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/afl-clang-fast"
        self.aflgo_clang_pp="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/afl-clang-fast++"
        self.afl_clang="/home/xiaosatianyu/workspace/git/afl/afl-clang-fast"
        self.afl_clang_pp="/home/xiaosatianyu/workspace/git/afl/afl-clang-fast++"
        
        self.script_getdistance="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/scripts/genDistance.sh"
        self.python_xiaosa_path="/home/xiaosatianyu/.virtualenvs/xiaosa/bin/python"
        
        #global variable
        self.all_compiler_flag=["gcc","clang","aflgo_get","aflgo_instrument","afl"]
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
        for item in self.targets:
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
    def _get_configure_para_for_instrument(self,file_source_item_dir):
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
        distance=os.path.join(self.output_dir,item,"distance.cfg.txt")
        other_flag=" -v"  
        
        #add to the flags
        CFLAGS+=" -distance="+distance+other_flag
        CXXFLAGS+=" -distance="+distance+other_flag 
        
        #total
        para_str=para_str\
            +" --prefix="+prefix\
            +" CC="+CC\
            +" CXX="+CXX\
            +" CFLAGS="+qutation+CFLAGS+qutation\
            +" CXXFLAGS="+qutation+CXXFLAGS+qutation 
        
        return [para_str]        
       
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
        CFLAGS="-ggdb -fvisibility=default"
        CXXFLAGS="-ggdb -fvisibility=default" 
        qutation='\"' 
        #for gcc
        CC="gcc"
        CXX="g++"
        
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
        qutation='\"' 
        
        #for clang
        CC="clang"
        CXX="clang++"        
        
        #total
        para_str=para_str\
            +" --prefix="+prefix\
            +" CC="+CC\
            +" CXX="+CXX\
            +" CFLAGS="+qutation+CFLAGS+qutation\
            +" CXXFLAGS="+qutation+CXXFLAGS+qutation
        return [para_str]
    

    #----------------------------------------------------------------------
    def _get_configure_para_for_afl(self,file_source_item_dir):
        """"""
        para_str="./configure --enable-static --disable-shared " 
        prefix=file_source_item_dir+"/lava-install"
        CFLAGS="-ggdb -fvisibility=default"
        CXXFLAGS="-ggdb -fvisibility=default" 
        qutation='\"' 
        
        #for clang
        CC=self.afl_clang
        CXX=self.aflgo_clang_pp       
        
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
        
        
        #1.check if shoul build
        file_target_item_path=os.path.join(self.targets_dir,item,item+"-"+self.compiler_flag)
        if self.compiler_flag=="gcc" and  os.path.exists(file_target_item_path) and not self.force_rebuild:
            return 
        
        output_check_file=os.path.join(self.output_dir,item,"BBcalls.txt")
        if self.compiler_flag=="aflgo_get" and os.path.exists(output_check_file) and not self.force_rebuild :
            return 
        
        output_check_file=os.path.join(self.output_dir,item,"distance.cfg.txt")
        if self.compiler_flag=="aflgo_instrument" and os.path.exists(output_check_file) and not self.force_rebuild :
            return 
        
        file_target_item_path=os.path.join(self.targets_dir,item,item+"-"+self.compiler_flag)
        if self.compiler_flag=="afl" and  os.path.exists(file_target_item_path) and not self.force_rebuild:
            return         
        
        #2. remove the old information
        if self.compiler_flag=="aflgo_get":
            file_output_item=os.path.join(self.output_dir,item)
            for infos in os.listdir(file_output_item):
                infos_path=os.path.join(file_output_item,infos)
                if "BBtargets" in infos:
                    continue
                if "dot" in infos:
                    shutil.rmtree(infos_path)
                    continue
                #check if rm the distance out
                if "distance" in infos:
                    if not self.recalculate:
                        continue
                os.remove(infos_path)
                
     
        #2 build new
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
        #3. autoreconf -f -i
        args = ["autoreconf","-i","-f"]
        p = subprocess.Popen(args, cwd=pwd,stdout=f, stderr=subprocess.STDOUT)            
        ret=p.wait()
        if ret != 0:
            logger.warning("autoreconf fail:%s"%item)
            return False
        #4. configure
        if  self.compiler_flag=="clang":
            cargs=self._get_configure_para_with_normal_clang(file_source_item_dir)
            logger.info("compiler the binary with normal clang")
        elif  self.compiler_flag=="aflgo_get":
            cargs=self._get_configure_para_for_distance(file_source_item_dir)
            logger.info("compiler the binary with aflgo_get")
        elif self.compiler_flag=="aflgo_instrument":
            cargs=self._get_configure_para_for_instrument(file_source_item_dir)
            logger.info("compiler the binary with aflgo_instrument") 
        elif self.compiler_flag=="afl":
            cargs=self._get_configure_para_for_afl(file_source_item_dir)
            logger.info("compiler the binary with afl")             
        else:
            cargs=self._get_configure_para_with_gcc(file_source_item_dir)
            logger.info( "compiler the binary with gcc")
        
        p = subprocess.Popen(cargs,shell=True, cwd=pwd,stdout=f, stderr=subprocess.STDOUT)            
        ret=p.wait()
        if ret != 0:
            logger.warning( "configure fail:%s"%item)
            return False         
        #5. make       
        args = ["make","-j8"]     
        p = subprocess.Popen(args, cwd=pwd,stdout=f, stderr=subprocess.STDOUT)            
        ret=p.wait()
        if ret != 0:
            logger.warning( "make fail:%s"%item)
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
        if not self.test_targets is None:
            self.targets=self.test_targets
        for item in self.targets:
            file_item_output=os.path.join(self.output_dir,item)
            #check if should recalculate
            if not self.recalculate:
                dis_path=os.path.join(file_item_output,"distance.cfg.txt")
                if os.path.exists(dis_path) and os.path.getsize(dis_path)>0:
                    continue       
            
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
                    logger.info( "calculate with aflgo successful: %s"%item)
                else:
                    self.exclude.update([item])
                    shutil.rmtree(file_item_output)
                    logger.warning( "calculate with aflgo fail: %s",item )
    #----------------------------------------------------------------------
    def _set_targets_item(self):
        """
        if has the BBtargets.txt, add to the targets set, and move the BBtargets.txt to the sub-output dir in aflgo_get
        if has the distance.cfg.txt and not empty, add to the targets in aflgo_instrument
        """
        if not self.test_targets is None:
            self.targets=self.test_targets
            return
        
        if self.compiler_flag !="aflgo_get" and self.compiler_flag!="aflgo_instrument":
            self.targets=copy.deepcopy(self.branches)
            return
        if self.compiler_flag=="aflgo_get":
            for item in self.branches:
                file_output_item=os.path.join(self.output_dir,item)
                file_output_item_checkfile_path=os.path.join(self.targets_dir,item,"BBtargets.txt")
                if not os.path.exists(file_output_item_checkfile_path) or os.path.getsize(file_output_item_checkfile_path)==0:
                    #remove the output dir if do not have target
                    #if os.path.exists(file_target_output_item):
                        #shutil.rmtree(file_target_output_item)           
                    continue
                if  not os.path.exists(file_output_item):
                    os.makedirs(file_output_item)
                shutil.copy(file_output_item_checkfile_path, file_output_item)
                self.targets.update([item])
                
        if self.compiler_flag=="aflgo_instrument":
            for item in self.branches:
                file_output_item=os.path.join(self.output_dir,item)
                file_output_item_checkfile_path=os.path.join(self.output_dir,item,"distance.cfg.txt")
                if not os.path.exists(file_output_item_checkfile_path) or os.path.getsize(file_output_item_checkfile_path)==0:
                    #remove the output dir if do not have target
                    #if os.path.exists(file_target_output_item):
                        #shutil.rmtree(file_target_output_item)           
                    continue
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
            shutil.copy(file_item_src_path, file_target_item_binary_path)     
            #2. get the crash
            crash_item_src_path=os.path.join(self.lava1_dir,item,"CRASH_INPUT")
            crash_target_item_path=os.path.join(self.targets_dir,item,"CRASH_INPUT")
            if not os.path.exists(crash_target_item_path):
                shutil.copy(crash_item_src_path, crash_target_item_path)            
        logger.info("get %s binaries ok", self.compiler_flag)       

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
        @compiler_flag: gcc,clang,aflgo_get,aflgo_instrument,afl
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
        # get the output
        self.get_all_files_crash()

    #----------------------------------------------------------------------
    def build_with_aflgo_get(self):
        """"""
        #1. make BBtarget and move the ouput dir
        self.make_BBtargets()
        #2. build all files with aflgo, but not instrument
        self.build_files_all(compiler_flag="aflgo_get")
        #calculation
        self.calculate_distance()
    #----------------------------------------------------------------------
    def build_with_gcc(self):
        """"""
        self.build_files_all(compiler_flag="gcc")
        
    
    #----------------------------------------------------------------------
    def build_with_aflgo_instrument(self):
        """"""
        self.build_files_all(compiler_flag="aflgo_instrument")
                      
    #----------------------------------------------------------------------
    def build_with_normal_afl(self,compiler_flag="afl"):
        """"""
        self.build_files_all(compiler_flag="afl")
       
        
      

if __name__ == '__main__':
    coloredlogs.install()
    logger.info("start")
    lava1=LAVA1(force_rebuild=True,recalculate=False)
    flag=1
    
    if flag==1:
        lava1.build_with_gcc()
    elif flag==2:
        lava1.build_with_aflgo_get()
    elif flag==3: 
        lava1.build_with_aflgo_instrument()
    elif flag==4:
        lava1.build_with_normal_afl(compiler_flag="afl")
        
    logger.info("successs")

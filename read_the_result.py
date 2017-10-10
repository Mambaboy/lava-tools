import os
import json
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("readplot")

########################################################################
class One_Experiment:
    """"""
    #----------------------------------------------------------------------
    def __init__(self,plot_dir=None,compare_baseline=0):
        """Constructor"""
        self.plot_dir=plot_dir
        self.info_dict=dict()

        #global varaible
        self.afl_found_num=0
        self.afl_found_list=list()
        self.aflgo_found_num=0
        
        #from para
        self.compare_baseline=compare_baseline #second, if found the crash time belown this baseline, ignore it

        #init
        self.aflgo_found_list=list()
        self.in_afl_not_aflgo=list()
        self.in_aflgo_not_afl=list() 
        self.aflgo_faster_dict=dict() # key is the item, value is the time
        self.aflgo_slower_dict=dict()
        self.aflgo_equal_speed_dict=dict()


    #----------------------------------------------------------------------
    def get_all_plot(self):
        """
        no any deal with the data
        """
        for item in os.listdir(self.plot_dir):
            if not "file-5.22" in item:
                continue     
            item_path=os.path.join(self.plot_dir,item)
            content=[]
            with open(item_path,"rt") as f:
                for line in  f.readlines():
                    content.append(line)
            first_afl_crash_time=content[1].split(":")[1].split(",")[0].split(".")[0]
            first_aflgo_crash_time=content[2].split(":")[1].split(",")[0].split(".")[0]
            self.info_dict[item]={
                "first_afl_crash_time":first_afl_crash_time,
                "first_aflgo_crash_time":first_aflgo_crash_time
            }


    #----------------------------------------------------------------------
    def read_basic_info(self):
        """"""
        basic_info_path=os.path.join(self.plot_dir,"basic_info")
        content=[]
        with open(basic_info_path,"rt") as f:
            for lines in f.readlines():
                if lines=="\n":
                    continue
                content.append(lines.strip())

        self.info_dict["Basicinfo"]=dict()
        for infos in content:
            key=infos.split(":")[0]
            value=infos.split(":")[1]
            self.info_dict["Basicinfo"][key]=value          

    #----------------------------------------------------------------------
    def get_infomation(self):
        """"""
        self.read_basic_info()
        self.get_all_plot()

    #----------------------------------------------------------------------
    def print_crash_found_number(self):
        """"""  
        logger.info("----------------------------------------------------")
        logger.info("afl found %d crashes",self.afl_found_num)
        logger.info("aflgo found %d crashes",self.aflgo_found_num)

    #----------------------------------------------------------------------
    def print_different_crash(self):
        """
        to print the different crash between the aflgo and afl
        """   
        logger.info("----------------------------------------------------")
        if len(self.in_aflgo_not_afl):
            logger.info("aflgo found %d more than afl",len(self.in_aflgo_not_afl))
            logger.info("%s",self.in_aflgo_not_afl)
        if len(self.in_afl_not_aflgo):
            logger.info("afl found %d more than aflgo",len(self.in_afl_not_aflgo))        
            logger.info("%s",self.in_afl_not_aflgo)

    def save_info_dict(self):
        #save the json
        save_path=os.path.join(self.plot_dir,"info_dict")
        with open(save_path,"wt") as f:
            json.dump(self.info_dict,f)


    #----------------------------------------------------------------------
    def compare_and_save_result(self):
        """
        0. just get and calculation the information
        1. compare the different crashes found between in afl and aflgo, mark both afl and aflgo found a crash
        """

        for (key,value) in  self.info_dict.iteritems():
            if key =="Basicinfo":
                continue
            #basic flag
            afl_found_flag=False
            afl_found_time=0
            aflgo_found_flag=False
            aflgo_found_time=0

            if value["first_afl_crash_time"]!="timeless":
                afl_found_flag=True
                afl_found_time=int(value["first_afl_crash_time"])
                self.afl_found_num+=1
                self.afl_found_list.append(key)
            if value["first_aflgo_crash_time"]!="timeless":
                aflgo_found_flag=True
                aflgo_found_time=int(value["first_aflgo_crash_time"])
                self.aflgo_found_num+=1
                self.aflgo_found_list.append(key)

            #1.mark the different crash in afl and aflgo
            if afl_found_flag and not aflgo_found_flag:
                self.in_afl_not_aflgo.append(key)
            if aflgo_found_flag and not afl_found_flag:
                self.in_aflgo_not_afl.append(key)

            #2. compare the speed between the crash, both afl and aflgo found the crash
            if afl_found_flag and aflgo_found_flag:

                #2.1. check the baseline
                if   int(value["first_afl_crash_time"])<self.compare_baseline and int(value["first_aflgo_crash_time"]) <self.compare_baseline:
                    logger.info("%s is too easy, no need to analyse",key)
                    continue            

                afl_minus_aflgo=afl_found_time-aflgo_found_time
                #aflgo fast
                if afl_minus_aflgo>0:
                    self.aflgo_faster_dict[key]={
                        "aflgo_found_time":aflgo_found_time,
                        "afl_found_time":afl_found_time,
                        "d-value":afl_minus_aflgo   }
                #equal speed
                if afl_minus_aflgo==0:
                    self.aflgo_equal_speed_dict[key]={
                        "aflgo_found_time":aflgo_found_time,
                        "afl_found_time":afl_found_time,
                        "d-value":afl_minus_aflgo }
                #aflgo slower 
                if afl_minus_aflgo<0:
                    self.aflgo_slower_dict[key]={
                        "aflgo_found_time":aflgo_found_time,
                        "afl_found_time":afl_found_time,
                        "d-value":abs(afl_minus_aflgo) }


    #----------------------------------------------------------------------
    def print_speed_compare(self):
        """"""
        #aflgo fast
        logger.info("-------------------------------------------------------------")
        for (key,value) in self.aflgo_faster_dict.iteritems():
            logger.info("in fuzzing %s",key)
            logger.info("aflgo found crash for %d second",value['aflgo_found_time'])
            logger.info("afl found crash for %d second",value['afl_found_time'])
            logger.info("aflgo is faster than afl for %d second",value['d-value'])
            logger.info("\n")
        #the same speed  
        logger.info("-------------------------------------------------------------")
        for (key,value) in self.aflgo_equal_speed_dict.iteritems():
            logger.info("in fuzzing %s",key)
            logger.info("aflgo found crash for %d second",value['aflgo_found_time'])
            logger.info("afl found crash for %d second",value['afl_found_time'])
            logger.info("aflgo and afl are the same speed")
            logger.info("\n")
        #aflgo slow
        logger.info("-------------------------------------------------------------")
        for (key,value) in self.aflgo_slower_dict.iteritems():
            logger.info("in fuzzing %s",key)
            logger.info("aflgo found crash for %d second",value['aflgo_found_time'])
            logger.info("afl found crash for %d second",value['afl_found_time'])
            logger.info("aflgo is slower than afl for %d second",value['d-value'])
            logger.info("\n")

        logger.info("aflgo is faster than afl in %d",len(self.aflgo_faster_dict))
        logger.info("aflgo is slower than afl in %d",len(self.aflgo_slower_dict))
        logger.info("aflgo and afl are the same spped in %d",len(self.aflgo_equal_speed_dict))




if __name__ == '__main__':
    logger.info("start the read for one experiment")
    
    compare_baseline=0
    one_experiment=One_Experiment(plot_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava-tools/result/plot_out_2017-10-10"
                                  ,compare_baseline=compare_baseline)
    
    one_experiment.get_infomation()
    one_experiment.save_info_dict()
    #deal with the data
    one_experiment.compare_and_save_result()
    #print out some information
    one_experiment.print_speed_compare()
    one_experiment.print_crash_found_number()
    one_experiment.print_different_crash()



    logger.info("end-------------------------------")

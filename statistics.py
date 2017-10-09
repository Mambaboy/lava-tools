#for statistic multiple plot result

import os
import shutil
import json

########################################################################
class Statistic:
    """"""

    #----------------------------------------------------------------------
    def __init__(self,result_dir=None):
        """Constructor"""
        self.result_dir=result_dir
        self.all_resutl_list=list()
        self.all_target=list()
        
    #----------------------------------------------------------------------
    def read_all_dict(self):
        """"""
        for test in  os.listdir(self.result_dir):
            test_info_path=os.path.join(self.result_dir,test,"info_dict")
            if not os.path.exists(test_info_path):
                continue
            with open(test_info_path,"rt") as f:
                info_dict=json.load(f)
                self.all_resutl_list.append(info_dict)
        for item in self.all_resutl_list[0]:
            if "info" in item:
                continue
            self.all_target.append(str(item))
        print "a"
    

if __name__ == '__main__':
    statistic=Statistic(result_dir="/home/xiaosatianyu/infomation/git-2/lava_corpus/lava_corpus/lava-tools/result")
    statistic.read_all_dict()
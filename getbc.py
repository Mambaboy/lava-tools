from pygdbmi.gdbcontroller import GdbController
import sys
import os
import re
from pprint import pprint

def getBackTrack(target, pov, src_list):
    """
    Get back track, returns the last buggy file and line number.
    Arg1: target binary
    Arg2: argument of target binary
    Arg3: src list which is used to filter unrelated files.
    """
    try:
        gdbmi = GdbController()
        response = gdbmi.write('-file-exec-and-symbols %s' % target)
        response = gdbmi.write('run')
        response = gdbmi.write('bt')

        getLastCall(response, src_list)

    except Exception as e:
        print e

def getLastCall(response, src_list):
    for each_response in response:
        if each_response['payload'] is not None:
            res = each_response['payload']
           
            pattern = 'in (.+?) '
            re.compile(pattern)
            buggy_func = re.findall(pattern, res)
            if len(buggy_func) != 1:
                continue
            buggy_func = unicode(buggy_func[0])

            pattern = "at (.+?)\\\\n$"
            re.compile(pattern)
            buggy_src = re.findall(pattern, res)
            if len(buggy_src) != 1:
                continue

            src_file, line_num = buggy_src[0].split(':')
            if src_file not in src_list:
                continue

            print 'line %d (in function %s) in file %s raised the crash!' % (int(line_num), buggy_func, src_file)

if __name__ == '__main__':
    src_list = ['bug.c', '']
    getBackTrack('./bug', ' ', src_list)

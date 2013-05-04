#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, time

def ReadLog(filename, first_read=False, where=None):
    #Set the filename and open the file
    file = open(filename,'r')

    st_results = os.stat(filename)
    st_size = st_results[6]

    if first_read or where > st_size:
        #Find the size of the file and move to the end
        file.seek(st_size)
        where = file.tell()
        return {'line' : '', 'where' : where}
    else: pass

    file.seek(where)
    line = file.readline()
    where = file.tell()
    while not line:
        time.sleep(1)
        file.seek(where)
        line = file.readline()
        
    data = {'line' : line, 'where' : where}
    
    file.close()
    
    return data
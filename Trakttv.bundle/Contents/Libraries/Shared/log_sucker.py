#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time


class LogSucker(object):
    @staticmethod
    def read(filename, first_read=False, where=None):
        # Set the filename and open the file
        fp = open(filename, 'r')

        st_results = os.stat(filename)
        st_size = st_results[6]

        if first_read or where > st_size:
            #Find the size of the file and move to the end
            fp.seek(st_size)
            where = fp.tell()
            return {'line': '', 'where': where}
        else:
            pass

        fp.seek(where)
        line = fp.readline()
        where = fp.tell()

        while not line:
            time.sleep(1)
            fp.seek(where)
            line = fp.readline()

        data = {'line': line, 'where': where}

        fp.close()

        return data

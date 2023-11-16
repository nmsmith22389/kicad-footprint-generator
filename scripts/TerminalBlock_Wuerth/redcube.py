#!/usr/bin/env python3

import sys
import os

# load parent path of KicadModTree
print ("Sys path0: "+sys.path[0])
sys.path.append(os.path.join(sys.path[0], "..", "general"))

import StandardBox_generator

StandardBox_generator.main(sys.argv[1:])


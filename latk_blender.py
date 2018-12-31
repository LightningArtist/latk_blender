'''
The Lightning Artist Toolkit was developed with support from:
   Canada Council on the Arts
   Eyebeam Art + Technology Center
   Ontario Arts Council
   Toronto Arts Council
   
Copyright (c) 2018 Nick Fox-Gieg
http://fox-gieg.com

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''

import json
import zipfile
from io import BytesIO
from math import sqrt

# * * * * * * * * * * * * * * * * * * * * * * * * * *

class Latk(object):     
    def __init__(self, fileName=None, init=False, coords=None, color=None): # args string, Latk array, float tuple array, float tuple           
        self.layers = [] # LatkLayer
        self.frame_rate = 12

        if (fileName != None):
            self.read(fileName, True)
        elif (init == True):
            self.layers.append(LatkLayer())
            self.layers[0].frames.append(LatkFrame())
            if (coords != None): # 
                stroke = LatkStroke()
                stroke.setCoords(coords)
                if (color != None):
                    stroke.color = color
                self.layers[0].frames[0].strokes.append(stroke)            

    def getFileNameNoExt(self, s): # args string, return string
        returns = ""
        temp = s.split(".")
        if (len(temp) > 1): 
            for i in range(0, len(temp)-1):
                if (i > 0):
                    returns += "."
                returns += temp[i]
        else:
            return s
        return returns
        
    def getExtFromFileName(self, s): # args string, returns string 
        returns = ""
        temp = s.split(".")
        returns = temp[len(temp)-1]
        return returns

    def read(self, fileName, clearExisting=True, yUp=False, useScaleAndOffset=False, globalScale=(10.0, 10.0, 10.0), globalOffset=(0.0, 0.0, 0.0)): # defaults to Blender Z up
        data = None

        if (clearExisting == True):
            self.layers = []
        
        fileType = self.getExtFromFileName(fileName)
        if (fileType == "latk" or fileType == "zip"):
            imz = InMemoryZip()
            imz.readFromDisk(fileName)
            data = json.loads(imz.files[0].decode("utf-8"))        
        else:
            with open(fileName) as data_file:    
                data = json.load(data_file)
                            
        for jsonGp in data["grease_pencil"]:          
            for jsonLayer in jsonGp["layers"]:
                layer = LatkLayer(jsonLayer["name"])
                
                for jsonFrame in jsonLayer["frames"]:
                    frame = LatkFrame()
                    for jsonStroke in jsonFrame["strokes"]:                       
                        color = (1,1,1)
                        try:
                            r = jsonStroke["color"][0]
                            g = jsonStroke["color"][1]
                            b = jsonStroke["color"][2]
                            color = (r,g,b)
                        except:
                            pass
                        
                        points = []
                        for jsonPoint in jsonStroke["points"]:
                            x = float(jsonPoint["co"][0])
                            y = None
                            z = None
                            if (yUp == False):
                                y = float(jsonPoint["co"][2])
                                z = float(jsonPoint["co"][1])  
                            else:
                                y = float(jsonPoint["co"][1])
                                z = float(jsonPoint["co"][2]) 
                            #~
                            if (useScaleAndOffset == True):
                                x = (x * globalScale[0]) + globalOffset[0]
                                y = (y * globalScale[1]) + globalOffset[1]
                                z = (z * globalScale[2]) + globalOffset[2]
                            #~                                                           
                            pressure = 1.0
                            strength = 1.0
                            try:
                                pressure = jsonPoint["pressure"]
                            except:
                                pass
                            try:
                                strength = jsonPoint["strength"]
                            except:
                                pass
                            points.append(LatkPoint((x,y,z), pressure, strength))
                                                
                        stroke = LatkStroke(points, color)
                        frame.strokes.append(stroke)
                    layer.frames.append(frame)
                self.layers.append(layer)

    def write(self, fileName, yUp=True, useScaleAndOffset=False, globalScale=(0.1, 0.1, 0.1), globalOffset=(0.0, 0.0, 0.0)): # defaults to Unity, Maya Y up
        FINAL_LAYER_LIST = [] # string array

        for layer in self.layers:
            sb = [] # string array
            sbHeader = [] # string array
            sbHeader.append("\t\t\t\t\t\"frames\": [")
            sb.append("\n".join(sbHeader))

            for h, frame in enumerate(layer.frames):
                sbbHeader = [] # string array
                sbbHeader.append("\t\t\t\t\t\t{")
                sbbHeader.append("\t\t\t\t\t\t\t\"strokes\": [")
                sb.append("\n".join(sbbHeader))
                
                for i, stroke in enumerate(frame.strokes):
                    sbb = [] # string array
                    sbb.append("\t\t\t\t\t\t\t\t{")
                    color = stroke.color
                    sbb.append("\t\t\t\t\t\t\t\t\t\"color\": [" + str(color[0]) + ", " + str(color[1]) + ", " + str(color[2]) + "],")

                    if (len(stroke.points) > 0): 
                        sbb.append("\t\t\t\t\t\t\t\t\t\"points\": [")
                        for j, point in enumerate(stroke.points):
                            x = point.co[0]
                            y = None
                            z = None
                            if (yUp == True):
                                y = point.co[2]
                                z = point.co[1]
                            else:
                                y = point.co[1]
                                z = point.co[2]  
                            #~
                            if (useScaleAndOffset == True):
                                x = (x * globalScale[0]) + globalOffset[0]
                                y = (y * globalScale[1]) + globalOffset[1]
                                z = (z * globalScale[2]) + globalOffset[2]
                            #~                                           
                            if (j == len(stroke.points) - 1):
                                sbb.append("\t\t\t\t\t\t\t\t\t\t{\"co\": [" + str(x) + ", " + str(y) + ", " + str(z) + "], \"pressure\":" + str(point.pressure) + ", \"strength\":" + str(point.strength) + "}")
                                sbb.append("\t\t\t\t\t\t\t\t\t]")
                            else:
                                sbb.append("\t\t\t\t\t\t\t\t\t\t{\"co\": [" + str(x) + ", " + str(y) + ", " + str(z) + "], \"pressure\":" + str(point.pressure) + ", \"strength\":" + str(point.strength) + "},")
                    else:
                        sbb.append("\t\t\t\t\t\t\t\t\t\"points\": []")
                    
                    if (i == len(frame.strokes) - 1):
                        sbb.append("\t\t\t\t\t\t\t\t}")
                    else:
                        sbb.append("\t\t\t\t\t\t\t\t},")
                    
                    sb.append("\n".join(sbb))
                
                sbFooter = []
                if (h == len(layer.frames) - 1): 
                    sbFooter.append("\t\t\t\t\t\t\t]")
                    sbFooter.append("\t\t\t\t\t\t}")
                else:
                    sbFooter.append("\t\t\t\t\t\t\t]")
                    sbFooter.append("\t\t\t\t\t\t},")
                sb.append("\n".join(sbFooter))
            
            FINAL_LAYER_LIST.append("\n".join(sb))
        
        s = [] # string
        s.append("{")
        s.append("\t\"creator\": \"latk.py\",")
        s.append("\t\"grease_pencil\": [")
        s.append("\t\t{")
        s.append("\t\t\t\"layers\": [")

        for i, layer in enumerate(self.layers):
            s.append("\t\t\t\t{")
            if (layer.name != None and layer.name != ""): 
                s.append("\t\t\t\t\t\"name\": \"" + layer.name + "\",")
            else:
                s.append("\t\t\t\t\t\"name\": \"layer" + str(i + 1) + "\",")
                
            s.append(FINAL_LAYER_LIST[i])

            s.append("\t\t\t\t\t]")
            if (i < len(self.layers) - 1): 
                s.append("\t\t\t\t},")
            else:
                s.append("\t\t\t\t}")
                s.append("\t\t\t]") # end layers
        s.append("\t\t}")
        s.append("\t]")
        s.append("}")
        
        fileType = self.getExtFromFileName(fileName)
        if (fileType == "latk" or fileType == "zip"):
            fileNameNoExt = self.getFileNameNoExt(fileName)
            imz = InMemoryZip()
            imz.append(fileNameNoExt + ".json", "\n".join(s))
            imz.writetofile(fileName)            
        else:
            with open(fileName, "w") as f:
                f.write("\n".join(s))
                f.closed
                             
    def clean(self, cleanMinPoints = 2, cleanMinLength = 0.1):
        if (cleanMinPoints < 2):
            cleanMinPoints = 2 
        for layer in self.layers:
            for frame in layer.frames: 
                for stroke in frame.strokes:
                    # 1. Remove the stroke if it has too few points.
                    if (len(stroke.points) < cleanMinPoints): 
                        try:
                            frame.strokes.remove(stroke)
                        except:
                            pass
                    else:
                        totalLength = 0.0
                        for i in range(1, len(stroke.points)): 
                            p1 = stroke.points[i] # float tuple
                            p2 = stroke.points[i-1] # float tuple
                            # 2. Remove the point if it's a duplicate.
                            if (self.hitDetect3D(p1.co, p2.co, 0.1)): 
                                try:
                                    stroke.points.remove(stroke)
                                except:
                                    pass
                            else:
                                totalLength += self.getDistance(p1.co, p2.co)
                        # 3. Remove the stroke if its length is too small.
                        if (totalLength < cleanMinLength): 
                            try:
                                frame.strokes.remove(stroke)
                            except:
                                pass
                        else:
                            # 4. Finally, check the number of points again.
                            if (len(stroke.points) < cleanMinPoints): 
                                try:
                                    frame.strokes.remove(stroke)
                                except:
                                    pass

    def smoothStroke(self, stroke):
        points = stroke.points
        #~
        weight = 18
        scale = 1.0 / (weight + 2)
        nPointsMinusTwo = len(points) - 2
        lower = 0
        upper = 0
        center = 0
        #~
        for i in range(1, nPointsMinusTwo):
            lower = points[i-1].co
            center = points[i].co
            upper = points[i+1].co
            #~
            x = (lower[0] + weight * center[0] + upper[0]) * scale
            y = (lower[1] + weight * center[1] + upper[1]) * scale
            z = (lower[2] + weight * center[2] + upper[2]) * scale
            center = (x, y, z)
        
    def splitStroke(self, stroke): 
        points = stroke.points
        co = []
        pressure = []
        strength = []
        #~
        for i in range(1, len(points), 2):
            center = (points[i].co[0], points[i].co[1], points[i].co[2])
            lower = (points[i-1].co[0], points[i-1].co[1], points[i-1].co[2])
            x = (center[0] + lower[0]) / 2
            y = (center[1] + lower[1]) / 2
            z = (center[2] + lower[2]) / 2
            p = (x, y, z)
            #~
            co.append(lower)
            co.append(p)
            co.append(center)
            #~
            pressure.append(points[i-1].pressure)
            pressure.append((points[i-1].pressure + points[i].pressure) / 2)
            pressure.append(points[i].pressure)
            #~
            strength.append(points[i-1].strength)
            strength.append((points[i-1].strength + points[i].strength) / 2)
            strength.append(points[i].strength)
        #~
        for i in range(len(co), len(points)):
            pt = LatkPoint(co[i], pressure[i], strength[i])
            stroke.points.insert(i, pt)

    def refine(self, splitReps=2, smoothReps=10, doClean=True):
        if (doClean==True):
            self.clean()
        for layer in self.layers:
            for frame in layer.frames: 
                for stroke in frame.strokes:   
                    points = stroke.points
                    #~
                    for i in range(0, splitReps):
                        self.splitStroke(stroke)  
                        self.smoothStroke(stroke)  
                    #~
                    for i in range(0, smoothReps - splitReps):
                        self.smoothStroke(stroke)    

    def setStroke(self, stroke):
        lastLayer = self.layers[len(self.layers)-1]
        lastFrame = lastLayer.frames[len(lastLayer.frames)-1]
        lastFrame.strokes.append(stroke)

    def setPoints(self, points, color=(1.0,1.0,1.0)):
        lastLayer = self.layers[len(self.layers)-1]
        lastFrame = lastLayer.frames[len(lastLayer.frames)-1]
        stroke = LatkStroke()
        stroke.points = points
        stroke.color = color
        lastFrame.strokes.append(stroke)
    
    def setCoords(self, coords, color=(1.0,1.0,1.0)):
        lastLayer = self.layers[len(self.layers)-1]
        lastFrame = lastLayer.frames[len(lastLayer.frames)-1]
        stroke = LatkStroke()
        stroke.setCoords(coords)
        stroke.color = color
        lastFrame.strokes.append(stroke)

    def getDistance(self, v1, v2):
        return sqrt((v1[0] - v2[0])**2 + (v1[1] - v2[1])**2 + (v1[2] - v2[2])**2)

    def hitDetect3D(self, p1, p2, hitbox=0.01):
        if (self.getDistance(p1, p2) <= hitbox):
            return True
        else:
            return False
             
    def roundVal(self, a, b):
        formatter = "{0:." + str(b) + "f}"
        return formatter.format(a)

    def roundValInt(self, a):
        formatter = "{0:." + str(0) + "f}"
        return int(formatter.format(a))

    def writeTextFile(self, name="test.txt", lines=None):
        file = open(name,"w") 
        for line in lines:
            file.write(line) 
        file.close() 

    def readTextFile(self, name="text.txt"):
        file = open(name, "r") 
        return file.read() 

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

class LatkLayer(object):    
    def __init__(self, name="layer"): 
        self.frames = [] # LatkFrame
        self.name = name
        self.parent = None
    
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

class LatkFrame(object):   
    def __init__(self, frame_number=0): 
        self.strokes = [] # LatkStroke
        self.frame_number = frame_number
        self.parent_location = (0.0,0.0,0.0)
        
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

class LatkStroke(object):       
    def __init__(self, points=None, color=(1.0,1.0,1.0)): # args float tuple array, float tuple 
        self.points = []
        if (points != None):
            self.points = points
        self.color = color
        self.alpha = 1.0
        self.fill_color = color
        self.fill_alpha = 0.0

    def setCoords(self, coords):
        self.points = []
        for coord in coords:
            self.points.append(LatkPoint(coord))

    def getCoords(self):
        returns = []
        for point in self.points:
            returns.append(point.co)
        return returns

    def getPressures(self):
        returns = []
        for point in self.points:
            returns.append(point.pressure)
        return returns

    def getStrengths(self):
        returns = []
        for point in self.points:
            returns.append(point.strength)
        return returns

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

class LatkPoint(object):
    def __init__(self, co, pressure=1.0, strength=1.0): # args float tuple, float, float
        self.co = co
        self.pressure = pressure
        self.strength = strength
    
# * * * * * * * * * * * * * * * * * * * * * * * * * *

class InMemoryZip(object):

    def __init__(self):
        # Create the in-memory file-like object for working w/imz
        self.in_memory_zip = BytesIO()
        self.files = []

    def append(self, filename_in_zip, file_contents):
        # Appends a file with name filename_in_zip and contents of
        # file_contents to the in-memory zip.
        # Get a handle to the in-memory zip in append mode
        zf = zipfile.ZipFile(self.in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)

        # Write the file to the in-memory zip
        zf.writestr(filename_in_zip, file_contents)

        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in zf.filelist:
             zfile.create_system = 0         

        return self

    def readFromMemory(self):
        # Returns a string with the contents of the in-memory zip.
        self.in_memory_zip.seek(0)
        return self.in_memory_zip.read()

    def readFromDisk(self, url):
        zf = zipfile.ZipFile(url, 'r')
        for file in zf.infolist():
            self.files.append(zf.read(file.filename))

    def writetofile(self, filename):
        # Writes the in-memory zip to a file.
        f = open(filename, "wb")
        f.write(self.readFromMemory())
        f.close()

# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

'''
LIGHTNING ARTIST TOOLKIT (BLENDER)

The Lightning Artist Toolkit was developed with support from:
   Canada Council on the Arts
   Eyebeam Art + Technology Center
   Ontario Arts Council
   Toronto Arts Council
   
Copyright (c) 2018 Nick Fox-Gieg
http://fox-gieg.com

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Lightning Artist Toolkit (Blender) is free software: you can redistribute it 
and/or modify it under the terms of the GNU General Public License 
as published by the Free Software Foundation, either version 3 of 
the License, or (at your option) any later version.

The Lightning Artist Toolkit (Blender) is distributed in the hope that it will 
be useful, but WITHOUT ANY WARRANTY; without even the implied warranty 
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with the Lightning Artist Toolkit (Blender).  If not, see 
<http://www.gnu.org/licenses/>.
'''

# 1 of 10. MAIN

bl_info = {
    "name": "Lightning Artist Toolkit (Latk)", 
    "author": "Nick Fox-Gieg",
    "description": "Import and export Latk format",
    "category": "Animation"
}

import bpy
import bmesh
import bpy_extras
from bpy_extras import view3d_utils
from bpy_extras.io_utils import unpack_list
from bpy.types import Operator, AddonPreferences
from bpy.props import (BoolProperty, FloatProperty, StringProperty, IntProperty, PointerProperty, EnumProperty)
from bpy_extras.io_utils import (ImportHelper, ExportHelper)
#~
from freestyle.shaders import *
from freestyle.predicates import *
from freestyle.types import Operators, StrokeShader, StrokeVertex
from freestyle.chainingiterators import ChainSilhouetteIterator, ChainPredicateIterator
from freestyle.functions import *
#~
import math
from math import sqrt
from mathutils import *
from mathutils import Vector, Matrix
#~
import json
import xml.etree.ElementTree as etree
import base64
#~
import re
import parameter_editor
import random
import sys
import gc
import struct
import uuid
import contextlib
from collections import defaultdict
from itertools import zip_longest
from operator import itemgetter
#~
import os
import zipfile
import io
from io import BytesIO

la = Latk()

# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

# 2 of 10. TOOLS

def setObjectMode():
    bpy.ops.object.mode_set(mode='OBJECT')

def setEditMode():
    bpy.ops.object.mode_set(mode='EDIT')

def bakeAnimConstraint(target=None, bakeType="OBJECT"):
    if not target:
        target = s()
    start, end = getStartEnd()
    for obj in target:
        deselect()
        select(obj)
        setActiveObject(obj)
        bpy.ops.nla.bake(frame_start=start, frame_end=end, only_selected=True, visual_keying=True, clear_constraints=True, bake_types={bakeType.upper()})

def scatterObjects(target=None, val=10):
    if not target:
        target = s()
    for obj in target:
        x = (2 * random.random() * val) - val
        y = (2 * random.random() * val) - val
        z = (2 * random.random() * val) - val
        obj.location = (x, y, z)

def resizeToFitGp():
    least = 1
    most = 1
    #~
    gp = getActiveGp()
    for layer in gp.layers:
        if (layer.lock == False):
            for frame in layer.frames:
                if frame.frame_number < least:
                    least = frame.frame_number
                elif frame.frame_number > most:
                    most = frame.frame_number
    #~
    setStartEnd(least, most - 1)
    return getStartEnd()

def makeLoop():
    target = matchName("latk")
    origStart, origEnd = getStartEnd()
    setStartEnd(origStart-1, origEnd+1)
    start, end = getStartEnd()
    ctx = fixContext()
    #~
    for obj in target:
        fixContext("VIEW_3D")
        for i in range(start, end):
            goToFrame(i)
            if (obj.hide == False):
                bpy.ops.object.select_all(action='DESELECT')
                obj.select = True
                bpy.context.scene.objects.active = obj # last object will be the parent
                fixContext("GRAPH_EDITOR")
                bpy.ops.graph.extrapolation_type(type='MAKE_CYCLIC')
    #~
    returnContext(ctx)
    setStartEnd(origStart, origEnd - 2)

def breakUpStrokes():
    gp = getActiveGp()
    palette = getActivePalette()
    for layer in gp.layers:
        for frame in layer.frames:
            tempPoints = []
            tempColorNames = []
            for stroke in frame.strokes:
                for point in stroke.points:
                    tempPoints.append(point)
                    tempColorNames.append(stroke.colorname)
            #~
            for stroke in frame.strokes:
                frame.strokes.remove(stroke)     
            #~  
            for i, point in enumerate(tempPoints):
                stroke = frame.strokes.new(tempColorNames[i])
                stroke.draw_mode = "3DSPACE"
                stroke.points.add(1)
                coord = point.co
                createPoint(stroke, 0, (coord[0], coord[1], coord[2]), point.pressure, point.strength)

def normalizePoints(minVal=0.0, maxVal=1.0):
    gp = getActiveGp()
    allX = []
    allY = []
    allZ = []
    for layer in gp.layers:
        for frame in layer.frames:
            for stroke in frame.strokes:
                for point in stroke.points:
                    coord = point.co
                    allX.append(coord[0])
                    allY.append(coord[1])
                    allZ.append(coord[2])
    allX.sort()
    allY.sort()
    allZ.sort()
    #~
    leastValArray = [ allX[0], allY[0], allZ[0] ]
    mostValArray = [ allX[len(allX)-1], allY[len(allY)-1], allZ[len(allZ)-1] ]
    leastValArray.sort()
    mostValArray.sort()
    leastVal = leastValArray[0]
    mostVal = mostValArray[2]
    valRange = mostVal - leastVal
    #~
    xRange = (allX[len(allX)-1] - allX[0]) / valRange
    yRange = (allY[len(allY)-1] - allY[0]) / valRange
    zRange = (allZ[len(allZ)-1] - allZ[0]) / valRange
    #~
    minValX = minVal * xRange
    minValY = minVal * yRange
    minValZ = minVal * zRange
    maxValX = maxVal * xRange
    maxValY = maxVal * yRange
    maxValZ = maxVal * zRange
    #~
    for layer in gp.layers:
        for frame in layer.frames:
            for stroke in frame.strokes:
                for point in stroke.points:  
                    coord = point.co
                    x = remap(coord[0], allX[0], allX[len(allX)-1], minValX, maxValX)
                    y = remap(coord[1], allY[0], allY[len(allY)-1], minValY, maxValY)
                    z = remap(coord[2], allZ[0], allZ[len(allZ)-1], minValZ, maxValZ)
                    point.co = (x,y,z)

def scalePoints(val=0.01):
    strokes = getAllStrokes()
    for stroke in strokes:
        for point in stroke.points:
            point.co = (point.co[0] * val, point.co[1] * val, point.co[2] * val)

def loadJson(url):
    return json.load(open(url))

def gpWorldRoot(name="Empty"):
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    target = ss()
    target.name = name
    layers = getAllLayers()
    for layer in layers:
        layer.parent = target
    return target

def pressureRange(_min=0.1, _max=1.0, _mode="clamp_p"):
    gp = getActiveGp()
    if (_mode == "clamp_p"):
        for layer in gp.layers:
            for frame in layer.frames:
                for stroke in frame.strokes:
                    for point in stroke.points:
                        if (point.pressure < _min):
                            point.pressure = _min
                        elif (point.pressure > _max):
                            point.pressure = _max
    elif (_mode == "remap_p"):
        for layer in gp.layers:
            for frame in layer.frames:
                for stroke in frame.strokes:
                    for point in stroke.points:
                        point.pressure = remap(point.pressure, 0.0, 1.0, _min, _max)
    elif (_mode == "clamp_s"):
        for layer in gp.layers:
            for frame in layer.frames:
                for stroke in frame.strokes:
                    for point in stroke.points:
                        if (point.strength < _min):
                            point.strength = _min
                        elif (point.strength > _max):
                            point.strength = _max
    elif (_mode == "remap_s"):
        for layer in gp.layers:
            for frame in layer.frames:
                for stroke in frame.strokes:
                    for point in stroke.points:
                        point.strength = remap(point.strength, 0.0, 1.0, _min, _max)
    
def cameraArray(target=None, hideTarget=True, removeCameras=True, removeLayers=True): 
    if not target:
        target = ss()
    if (removeCameras == True):
        cams = matchName("Camera")
        for cam in cams:
            delete(cam)
    #~
    scene = bpy.context.scene
    render = scene.render
    render.use_multiview = True
    render.views_format = "MULTIVIEW"
    #~
    if (removeLayers == True):
        while (len(render.views) > 1): # can't delete first layer
            render.views.remove(render.views[len(render.views)-1])
        render.views[0].name = "left"
        render.views.new("right")
    render.views["left"].use = False
    render.views["right"].use = False
    #~
    coords = [(target.matrix_world * v.co) for v in target.data.vertices]
    cams = []
    for coord in coords:
        cam = createCamera()
        cam.location = coord
        cams.append(cam)
    for i, cam in enumerate(cams):
        lookAt(cam, target)
        cam.name = "Camera_" + str(i)
        renView = render.views.new(cam.name)
        renView.camera_suffix = "_" + cam.name.split("_")[1]
        scene.objects.active = cam
    parentMultiple(cams, target)
    #~
    if (hideTarget==True):
        target.hide = True
        target.hide_select = False
        target.hide_render = True

def lookAt(looker, lookee):
    deselect()
    select([looker, lookee])
    lookerPos = looker.matrix_world.to_translation()
    lookeePos = lookee.matrix_world.to_translation()
    #~
    direction = lookeePos - lookerPos
    #~
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')
    #~
    # assume we're using euler rotation
    looker.rotation_euler = rot_quat.to_euler()

'''
def centerPivot(target=None):
    if not target:
        target = ss()
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY")
'''
    
def getLayerInfo(layer):
    return layer.info.split(".")[0]

def getActiveFrameNum(layer=None):
    # assumes layer can have only one active frame
    if not layer:
        layer = getActiveLayer()
    returns = -1
    for i in range(0, len(layer.frames)):
        if (layer.frames[i] == layer.active_frame):
            returns = i
    return returns

def matchWithParent(_child, _parent, _index):
    if (_parent):
        loc, rot, scale = _parent.matrix_world.inverted().decompose()
        _child.location = loc
        #_child.rotation_quaternion = rot
        _child.scale = scale
        _child.parent = _parent
        keyTransform(_child, _index)   

def clearState():
    for ob in bpy.data.objects.values():
        try:
            ob.selected=False
        except:
            pass
    bpy.context.scene.objects.active = None

def onionSkin(layers=None, onion=False):
    if not layers:
        layers = getActiveGp().layers
    for layer in layers:
        layer.use_onion_skinning = onion

def bakeParentToChild(start=None, end=None):
    if (start==None and end==None):
        start, end = getStartEnd()
    # https://www.blender.org/api/blender_python_api_2_72_1/bpy.ops.nla.html
    bpy.ops.nla.bake(frame_start=start, frame_end=end, step=1, only_selected=True, visual_keying=True, clear_constraints=True, clear_parents=True, use_current_action=True, bake_types={'OBJECT'})    

def bakeParentToChildByName(name="latk"):
    start, end = getStartEnd()
    target = matchName(name)
    for obj in target:
        bpy.context.scene.objects.active = obj
        bakeParentToChild(start, end)

def getWorldCoords(co=None, camera=None, usePixelCoords=True, useRenderScale=True, flipV=True):
    # https://blender.stackexchange.com/questions/882/how-to-find-image-coordinates-of-the-rendered-vertex
    # Test the function using the active object (which must be a camera)
    # and the 3D cursor as the location to find.
    scene = bpy.context.scene
    if not camera:
        camera = bpy.context.object
    if not co:
        co = bpy.context.scene.cursor_location
    #~
    co_2d = bpy_extras.object_utils.world_to_camera_view(scene, camera, co)
    pixel_2d = None
    #~
    if (usePixelCoords==False):
        print("2D Coords: ", co_2d)
        return co_2d
    else:
        render_size = getSceneResolution(useRenderScale)
        if (flipV==True):
            pixel_2d = (round(co_2d.x * render_size[0]), round(render_size[1] - (co_2d.y * render_size[1])))
        else:
            pixel_2d = (round(co_2d.x * render_size[0]), round(co_2d.y * render_size[1]))
        print("Pixel Coords: ", pixel_2d)
        return pixel_2d

def getSceneResolution(useRenderScale=True):
    # https://blender.stackexchange.com/questions/882/how-to-find-image-coordinates-of-the-rendered-vertex
    scene = bpy.context.scene
    render_scale = scene.render.resolution_percentage / 100
    if (useRenderScale==True):
        return (int(scene.render.resolution_x * render_scale), int(scene.render.resolution_y * render_scale))
    else:
        return (int(scene.render.resolution_x), int(scene.render.resolution_y))

def setSceneResolution(width=1920, height=1080, scale=50):
    # https://blender.stackexchange.com/questions/9164/modify-render-settings-for-all-scenes-using-python
    for scene in bpy.data.scenes:
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = scale
        scene.render.use_border = False

def getSceneFps():
    return bpy.context.scene.render.fps

def setSceneFps(fps=12):
    for scene in bpy.data.scenes:
        scene.render.fps = fps

def deselect():
    bpy.ops.object.select_all(action='DESELECT')

def selectAll():
    bpy.ops.object.select_all(action='SELECT')

# TODO fix so you can find selected group regardless of active object
def getActiveGroup():
    obj = bpy.context.scene.objects.active
    for group in bpy.data.groups:
        for groupObj in group.objects:
            if(obj.name == groupObj.name):
                return group
    return None

def getChildren(target=None):
    if not target:
        target=s()[0]
    # https://www.blender.org/forum/viewtopic.php?t=8661
    return [ob for ob in bpy.context.scene.objects if ob.parent == target]

def groupName(name="latk", gName="myGroup"):
    deselect()
    selectName(name)
    makeGroup(gName)

def makeGroup(name="myGroup", newGroup=True):
    if (newGroup==True):
        bpy.ops.group.create(name=name)
    else:
        bpy.ops.group_link(group=name)

def deleteGroup(name="myGroup"):
    group = bpy.data.groups[name]
    for obj in group.objects:
        delete(obj)
    removeGroup(name)

def deleteGroups(name=["myGroup"]):
    for n in name:
        deleteGroup(n)

def preserveGroups(name=["myGroup"]):
    allNames = []
    for group in bpy.data.groups:
        allNames.append(group.name)
    for aN in allNames:
        doDelete = True
        for n in name:
            if (aN == n):
                doDelete = False
        if (doDelete == True):
            deleteGroup(aN)

def preserveGroupName(name="myGroup"):
    allNames = []
    for group in bpy.data.groups:
        allNames.append(group.name)
    for aN in allNames:
        doDelete = True
        for n in name:
            if re.match(r'^' + n + '', aN):
                doDelete = False
        if (doDelete == True):
            deleteGroup(aN)

def deleteGroupName(name="myGroup"):
    allNames = []
    for group in bpy.data.groups:
        allNames.append(group.name)
    for aN in allNames:
        doDelete = False
        for n in name:
            if re.match(r'^' + n + '', aN):
                doDelete = True
        if (doDelete == True):
            deleteGroup(aN)

def removeGroup(name="myGroup", allGroups=False):
    if (allGroups==False):
        group = bpy.data.groups[name]
        group.user_clear()
        bpy.data.groups.remove(group) 
        #~
    else:
        for group in bpy.data.groups:
            group.user_clear()
            bpy.data.groups.remove(group)   

def importGroup(path, name, winDir=False):
    importAppend(path, "Group", name, winDir)

def removeObj(name="myObj", allObjs=False):
    if (allObjs==False):
        obj = bpy.data.objects[name]
        obj.user_clear()
        bpy.data.objects.remove(obj) 
    else:
        for obj in bpy.data.objects:
            obj.user_clear()
            bpy.data.objects.remove(obj)  
    refresh()

def deleteDuplicateStrokes(fromAllFrames = False):
    strokes = getSelectedStrokes()
    checkPoints = []
    for i in range(0, len(strokes)):
        checkPoints.append(sumPoints(strokes[i]))
    for i in range(0, len(strokes)):
        for j in range(0, len(strokes)):
            try:
                if ( j != i and checkPoints[i] == checkPoints[j]):
                    bpy.ops.object.select_all(action='DESELECT')
                    strokes[i].select = True
                    deleteSelected()
            except:
                pass

def getEmptyStrokes(_strokes, _minPoints=0):
    returns = []
    for stroke in _strokes:
        if (len(stroke.points) <= _minPoints):
            returns.append(stroke)
    print("Found " + str(len(returns)) + " empty strokes.")
    return returns

def cleanEmptyStrokes(_strokes, _minPoints=0):
    target = getEmptyStrokes(_strokes, _minPoints)
    deleteStrokes(target)

def consolidateGroups():
    wholeNames = []
    mergeNames = []
    for group in bpy.data.groups:
        if("." in group.name):
            mergeNames.append(group.name)
        else:
            wholeNames.append(group.name)
    for sourceName in mergeNames:
        sourceGroup = bpy.data.groups[sourceName]
        destGroup = None
        for destName in wholeNames:
            if (sourceName.split(".")[0] == destName):
                destGroup = bpy.data.groups[destName]
                break
        if (destGroup==None):
            break
        else:
            for obj in sourceGroup.objects:
                try:
                    destGroup.objects.link(obj)
                except:
                    pass
            removeGroup(sourceName)
    print(mergeNames)
    print(wholeNames)


def sumPoints(stroke):
    x = 0
    y = 0
    z = 0
    for point in stroke.points:
        co = point.co
        x += co[0]
        y += co[1]
        z += co[2]
    return roundVal(x + y + z, 5)

def rename(target=None, name="Untitled"):
    if not target:
        target = ss()
    target.name = name
    return target.name

def getUniqueName(name):
    # if the name is already unique, return it
    searchNames = matchName("name")
    if (len(searchNames) == 0):
        return name
    else:
        # find the trailing digit in the name
        trailingDigit = re.sub('.*?([0-9]*)$',r'\1',name)
        
        # create default variables for newDigit and shortname
        # in case there is no trailing digit (ie: "pSphere")
        newDigit = 1
        shortname = name
        
        if(trailingDigit):
            # increment the last digit and find the shortname using the length
            # of the trailing digit as a reference for how much to trim
            newDigit = int(trailingDigit)+1
            shortname = name[:-len(trailingDigit)]
        
        # create the new name
        newName = shortname+str(newDigit)

        # recursively run through the function until a unique name is reached and returned
        return getUniqueName(newName)

def renameCurves(name="mesh", nameMesh="latk_ob_mesh", nameCurve="latk"):
    target = matchName(nameMesh)
    for i in range(0, len(target)):
        target[i].name = name + "_" + str(i)

def deleteUnparentedCurves(name="latk"):
    target = matchName(name)
    toDelete = []
    for i in range(0, len(target)):
        if (target[i].parent==None):
            toDelete.append(target[i])
    print(str(len(toDelete)) + " objects selected for deletion.")
    for i in range(0, len(toDelete)):
        delete(toDelete[i])

def currentFrame(target=None):
    if not target:
        return bpy.context.scene.frame_current
    else:
        goToFrame(target)

def getDistance(v1, v2):
    return sqrt( (v1[0] - v2[0])**2 + (v1[1] - v2[1])**2 + (v1[2] - v2[2])**2)
    
def hitDetect3D(p1, p2, hitbox=0.01):
    #if (p1[0] + hitbox >= p2[0] - hitbox and p1[0] - hitbox <= p2[0] + hitbox and p1[1] + hitbox >= p2[1] - hitbox and p1[1] - hitbox <= p2[1] + hitbox and p1[2] + hitbox >= p2[2] - hitbox and p1[2] - hitbox <= p2[2] + hitbox):
    if (getDistance(p1, p2) <= hitbox):
        return True
    else:
        return False

def parentMultiple(target, root, fixTransforms=True):
    bpy.context.scene.objects.active = root # last object will be the parent
    bpy.ops.object.select_all(action='DESELECT')
    for i in range(0, len(target)):
        target[i].select = True
    if (fixTransforms==True):
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=False) 
    else:
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

def makeParent(target=None, unParent=False, fixTransforms=True):
    if not target:
        target = s()
    if (unParent==True):
        for obj in target:
            if (obj.parent != None):
                bpy.context.scene.objects.active=obj
                if (fixTransforms==True):
                    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                else:
                    bpy.ops.object.parent_clear()
    else:
        # http://blender.stackexchange.com/questions/9200/make-object-a-a-parent-of-object-b-via-python
        for i in range(0, len(target)-1):
            target[i].select=True
        bpy.context.scene.objects.active = target[len(target)-1] # last object will be the parent
        #~
        if (fixTransforms==True):
            bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=False) 
        else:   
            bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True) 

def makeRoot():
    root = addLocator()
    target = matchName("latk")
    parentMultiple(target, root)
    return root

def keyTransform(_obj, _frame):
    _obj.keyframe_insert(data_path="location", frame=_frame) 
    _obj.keyframe_insert(data_path="rotation_euler", frame=_frame) 
    _obj.keyframe_insert(data_path="scale", frame=_frame)

def keyMatrix(_obj, _frame):
    _obj.keyframe_insert(data_path="matrix_world", frame=_frame) 

def select(target=None):
    if not target:
        target=bpy.context.selected_objects;
    print("selected " + str(target))
    return target

def delete(_obj=None):
    if not _obj:
        _obj = ss()
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[_obj.name].hide = False
    bpy.data.objects[_obj.name].select = True
    bpy.ops.object.delete()
    gc.collect()

def refresh():
    bpy.context.scene.update()

def remap(value, min1, max1, min2, max2):
    range1 = max1 - min1
    range2 = max2 - min2
    valueScaled = float(value - min1) / float(range1)
    return min2 + (valueScaled * range2)

def remapInt(value, min1, max1, min2, max2):
    return int(remap(value, min1, max1, min2, max2))

def matchName(_name):
    returns = []
    for i in range(0, len(bpy.context.scene.objects)):
        obj = bpy.context.scene.objects[i]
        if re.match(r'^' + str(_name) + '', obj.name): # curve object
            returns.append(obj)
    return returns

def selectName(_name="latk"):
    target = matchName(_name)
    deselect()
    for obj in target:
        obj.select = True

def deleteName(_name="latk"):
    target = matchName(_name)
    for obj in target:
        try:
            delete(obj)
        except:
            print("error deleting " + obj.name)

def getKeyByIndex(data, index=0):
    for i, key in enumerate(data.keys()):
        if (i == index):
            return key

def roundVal(a, b):
    formatter = "{0:." + str(b) + "f}"
    return formatter.format(a)

def roundValInt(a):
    formatter = "{0:." + str(0) + "f}"
    return int(formatter.format(a))

def frame_to_time(frame_number):
    scene = bpy.context.scene
    fps = scene.render.fps
    fps_base = scene.render.fps_base
    raw_time = (frame_number - 1) / fps
    return round(raw_time, 3)

def bakeFrames():
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end + 1
    scene = bpy.context.scene
    gp = getActiveGp()
    for layer in gp.layers:   
        for i in range(start, end):
            try:
                layer.frames.new(i)
            except:
                print ("Frame " + str(i) + " already exists.")

def getStartEnd(pad=True):
    start = bpy.context.scene.frame_start
    end = None
    if (pad==True):
        end = bpy.context.scene.frame_end + 1
    else:
        end = bpy.context.scene.frame_end
    return start, end

def setStartEnd(start, end, pad=True):
    if (pad==True):
        end += 1
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end
    return start, end

def copyFrame(source, dest, limit=None):
    scene = bpy.context.scene
    layer = getActiveLayer()  
    #.
    frameSource = layer.frames[source]
    frameDest = layer.frames[dest]
    if not limit:
        limit = len(frameSource.strokes)
    for j in range(0, limit):
        scene.frame_set(source)
        strokeSource = frameSource.strokes[j]
        scene.frame_set(dest)
        strokeDest = frameDest.strokes.new(strokeSource.color.name)
        # either of ('SCREEN', '3DSPACE', '2DSPACE', '2DIMAGE')
        strokeDest.draw_mode = '3DSPACE'
        strokeDest.points.add(len(strokeSource.points))
        for l in range(0, len(strokeSource.points)):
            strokeDest.points[l].co = strokeSource.points[l].co

def copyFramePoints(source, dest, limit=None, pointsPercentage=1):
    scene = bpy.context.scene
    layer = getActiveLayer()  
    #.
    frameSource = layer.frames[source]
    frameDest = layer.frames[dest]
    if not limit:
        limit = len(frameSource.strokes)
    for j in range(0, limit):
        scene.frame_set(source)
        strokeSource = frameSource.strokes[j]
        scene.frame_set(dest)
        strokeDest = frameDest.strokes.new(strokeSource.color.name)
        # either of ('SCREEN', '3DSPACE', '2DSPACE', '2DIMAGE')
        strokeDest.draw_mode = '3DSPACE'
        if (j>=limit-1):
            newVal = roundValInt(len(strokeSource.points) * pointsPercentage)
            strokeDest.points.add(newVal)
            for l in range(0, newVal):
                strokeDest.points[l].co = strokeSource.points[l].co
        else:
            strokeDest.points.add(len(strokeSource.points))
            for l in range(0, len(strokeSource.points)):
                strokeDest.points[l].co = strokeSource.points[l].co

def addLocator(target=None):
    if not target:
        target = ss()
    empty = bpy.data.objects.new("Empty", None)
    bpy.context.scene.objects.link(empty)
    bpy.context.scene.update()
    if (target != None):
        empty.location = target.location
    return empty

def createCamera():
    # https://blenderartists.org/forum/showthread.php?312512-how-to-add-an-empty-and-a-camera-using-python-script
   cam = bpy.data.cameras.new("Camera")
   cam_ob = bpy.data.objects.new("Camera", cam)
   bpy.context.scene.objects.link(cam_ob)
   return cam_ob

def getActiveCamera():
    # https://blender.stackexchange.com/questions/8245/find-active-camera-from-python
    cam_ob = bpy.context.scene.camera
    #~
    if cam_ob is None:
        print("no scene camera")
        return None
    elif cam_ob.type == 'CAMERA':
        print("regular scene cam")
        return cam_ob
    else:
        print("%s object as camera" % cam_ob.type)
        ob = bpy.context.object
        if ob is not None and ob.type == 'CAMERA':
            #print("Active camera object")
            return ob
        else:
            return None

def goToFrame(_index):
    origFrame = bpy.context.scene.frame_current
    bpy.context.scene.frame_current = _index
    bpy.context.scene.frame_set(_index)
    refresh()
    print("Moved from timeline frame " + str(origFrame) + " to " + str(_index))
    return bpy.context.scene.frame_current

def hideFrame(_obj, _frame, _hide):
    _obj.hide = _hide
    _obj.hide_render = _hide
    _obj.keyframe_insert(data_path="hide", frame=_frame) 
    _obj.keyframe_insert(data_path="hide_render", frame=_frame) 

def hideFrameByScale(_obj, _frame, _hide):
    showScaleVal = 1
    hideScaleVal = 0.001
    if (_hide == True):
        _obj.scale = [hideScaleVal, hideScaleVal, hideScaleVal]
    else:
        _obj.scale = [showScaleVal, showScaleVal, showScaleVal]
    #_obj.keyframe_insert(data_path="location", frame=_frame)
    #_obj.keyframe_insert(data_path="rotation_quaternion", frame=_frame)
    _obj.keyframe_insert(data_path="scale", frame=_frame)
    fcurves = _obj.animation_data.action.fcurves
    for fcurve in fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'CONSTANT'
    '''
    if (_obj.hide == True):
        _obj.hide = False
        _obj.keyframe_insert(data_path="hide", frame=_frame)
    if (_obj.hide_render == True):
        _obj.hide_render = False
        _obj.keyframe_insert(data_path="hide_render", frame=_frame)
    '''

def hideFramesByScale():
    target = matchName("latk_")
    start, end = getStartEnd()
    for i in range(start, end):
        goToFrame(i)
        for j in range(0, len(target)):
            if (target[j].hide == False):
                hideFrameByScale(target[j], i, False)
    #turn off all hide keyframes
    for i in range(start, end):
        goToFrame(i)
        for j in range(0, len(target)):
            if (target[j].hide == True):
                hideFrameByScale(target[j], i, True)
                hideFrame(target[j], i, False) 
    
def deleteAnimationPath(target=None, paths=["hide", "hide_render"]):
    if not target:
        target = ss()
    fcurves = target.animation_data.action.fcurves
    curves_to_remove = []
    for path in paths:
        for i, curve in enumerate(fcurves):
            if (curve.data_path == path):
                curves_to_remove.append(i)
    for i in range(0, len(curves_to_remove)):
        fcurves.remove(fcurves[i])


def showHide(obj, hide, keyframe=False, frame=None):
    obj.hide = hide
    obj.hide_render = hide

def showHideChildren(hide):
    target = getChildren()
    for obj in target:
        showHide(obj, hide)

def rgbToHex(color, normalized=False):
    if (normalized==True):
        return "#%02x%02x%02x" % (int(color[0] * 255.0), int(color[1] * 255.0), int(color[2] * 255.0))
    else:
        return "#%02x%02x%02x" % (int(color[0]), int(color[1]), int(color[2]))

def rgbIntToTuple(rgbint, normalized=False):
    rgbVals = [ rgbint // 256 // 256 % 256, rgbint // 256 % 256, rgbint % 256 ]
    if (normalized == True):
        for i in range(0, len(rgbVals)):
            c = float(rgbVals[i]) / 255.0
            rgbVals[i] = c;
    return (rgbVals[2], rgbVals[1], rgbVals[0])

def normRgbToHex(color):
    return rgbToHex(color, normalized=True)

def moveShot(start, end, x, y, z):
    gp = bpy.context.scene.grease_pencil
    target = (start, end)
    for g in range(target[0], target[1]+1):
        for f in range(0, len(gp.layers)):
            layer = gp.layers[f]
            currentFrame = g
            for i in range(0, len(layer.frames[currentFrame].strokes)):
                for j in range(0, len(layer.frames[currentFrame].strokes[i].points)):
                    layer.frames[currentFrame].strokes[i].points[j].co.x += x
                    layer.frames[currentFrame].strokes[i].points[j].co.y += y
                    layer.frames[currentFrame].strokes[i].points[j].co.z += z

def fixContext(ctx="VIEW_3D"):
    original_type = bpy.context.area.type
    bpy.context.area.type = ctx
    return original_type

def returnContext(original_type):
    bpy.context.area.type = original_type

def alignCamera():
    original_type = bpy.context.area.type
    print("Current context: " + original_type)
    bpy.context.area.type = "VIEW_3D"
    #~
    # strokes, points, frame
    bpy.ops.view3d.camera_to_view()
    #~
    bpy.context.area.type = original_type

# ~ ~ ~ ~ ~ ~ grease pencil ~ ~ ~ ~ ~ ~
def getActiveGp(_name="GPencil"):
    try:
        pencil = bpy.context.scene.grease_pencil
    except:
        pencil = None
    try:
        gp = bpy.data.grease_pencil[pencil.name]
    except:
        gp = bpy.data.grease_pencil.new(_name)
        bpy.context.scene.grease_pencil = gp
    #print("Active GP block is: " + gp.name)
    return gp

def forceDrawMode():
    #https://blenderartists.org/forum/showthread.php?255425-How-to-use-quot-bpy-ops-gpencil-draw()-quot
    ctx = fixContext()
    returns = bpy.ops.gpencil.draw(mode="DRAW")
    returnContext(ctx)
    return returns

def initGp():
    # https://blender.stackexchange.com/questions/48992/how-to-add-points-to-a-grease-pencil-stroke-or-make-new-one-with-python-script
    scene = bpy.context.scene
    if not scene.grease_pencil:
        a = [ a for a in bpy.context.screen.areas if a.type == 'VIEW_3D' ][0]
        override = {
            'scene'         : scene,
            'screen'        : bpy.context.screen,
            'object'        : bpy.context.object,
            'area'          : a,
            'region'        : a.regions[0],
            'window'        : bpy.context.window,
            'active_object' : bpy.context.object
        }
        bpy.ops.gpencil.data_add(override)
    return scene.grease_pencil

def getActivePalette():
    gp = getActiveGp()
    palette = gp.palettes.active
    if (palette == None):
        palette = gp.palettes.new(gp.name + "_Palette", set_active = True)
    if (len(palette.colors) < 1):
        color = palette.colors.new()
        color.color = (0,0,0)
    #print("Active palette is: " + gp.palettes.active.name)
    return palette

def getActiveColor():
    palette = getActivePalette()
    #print("Active color is: " + "\"" + palette.colors.active.name + "\" " + str(palette.colors.active.color))
    return palette.colors.active

def getActiveLayer():
    gp = getActiveGp()
    layer = gp.layers.active
    return layer

def setActiveLayer(name="Layer"):
    gp = getActiveGp()
    gp.layers.active = gp.layers[name]
    return gp.layers.active

def deleteLayer(name=None):
    gp = getActiveGp()
    if not name:
        name = gp.layers.active.info
    gp.layers.remove(gp.layers[name])

def duplicateLayer():
    ctx = fixContext()
    bpy.ops.gpencil.layer_duplicate()
    returnContext(ctx)
    return getActiveLayer()

def splitLayer(splitNum=None):
    if not splitNum:
        splitNum = getActiveFrameTimelineNum()
    layer1 = getActiveLayer()
    layer2 = duplicateLayer()
    #~
    for frame in layer1.frames:
        if (frame.frame_number>=splitNum):
            layer1.frames.remove(frame)
    for frame in layer2.frames:
        if (frame.frame_number<splitNum):
            layer2.frames.remove(frame)
    #~
    if (len(layer2.frames) > 0):
        lastNum = layer2.frames[0].frame_number
        # cap the new layers with blank frames
        blankFrame(layer1, lastNum)
        blankFrame(layer2, lastNum-1)
        return layer2
    else:
        cleanEmptyLayers()
        return None

def blankFrame(layer=None, frame=None):
    if not layer:
        layer = getActiveLayer()
    if not frame:
        frame = bpy.context.scene.frame_current
    try:
        layer.frames.new(frame)
    except:
        pass

'''
def getActiveFrameNum():
    returns = -1
    layer = getActiveLayer()
    for i, frame in enumerate(layer.frames):
        if (frame == layer.active_frame):
            returns = i
    return returns
'''

def checkForZero(v, hitRange=0.005):
    if (abs(v[0]) < hitRange and abs(v[1]) < hitRange and abs(v[2]) < hitRange):
        return True
    else:
        return False

def getActiveFrameTimelineNum():
    return getActiveLayer().frames[getActiveFrameNum()].frame_number

def checkLayersAboveFrameLimit(limit=20):
    gp = getActiveGp()
    returns = []
    print("~ ~ ~ ~")
    for layer in gp.layers:
        if (len(layer.frames) > limit + 1): # accounting for extra end cap frame
            returns.append(layer)
            print("layer " + layer.info + " is over limit " + str(limit) + " with " + str(len(layer.frames)) + " frames.")
    print(" - - - " + str(len(returns)) + " total layers over limit.")
    print("~ ~ ~ ~")
    return returns

def splitLayersAboveFrameLimit(limit=20):
    layers = checkLayersAboveFrameLimit(limit)
    #~
    if (len(layers) <= 0):
        return
    for layer in layers:
        setActiveLayer(layer.info)
        for i in range(0, int(getLayerLength()/limit)):
            currentLayer = getActiveLayer()
            print("* " + currentLayer.info + ": pass " + str(i))
            if (getLayerLength() < limit or currentLayer.lock==True):
                break
            goToFrame(currentLayer.frames[limit].frame_number)
            setActiveFrame(currentLayer.frames[limit].frame_number)
            splitLayer(currentLayer.frames[limit].frame_number)
            print("Split layer " + currentLayer.info + " with " + str(len(currentLayer.frames)) + " frames.")

def getLayerLength(name=None):
    layer = None
    if not name:
        layer = getActiveLayer()
    else:
        layer = getActiveGp().layers[name]
    return len(layer.frames)

def cleanEmptyLayers():
    gp = getActiveGp()
    for layer in gp.layers:
        if (len(layer.frames) == 0):
            gp.layers.remove(layer)

def clearLayers():
    gp = getActiveGp()
    for layer in gp.layers:
        gp.layers.remove(layer)

def clearPalette():
    palette = getActivePalette()
    for color in palette.colors:
        palette.colors.remove(color)

def clearAll():
    clearLayers()
    clearPalette()

def createColor(_color):
    frame = getActiveFrame()
    palette = getActivePalette()
    matchingColorIndex = -1
    places = 7
    for i in range(0, len(palette.colors)):
        if (roundVal(_color[0], places) == roundVal(palette.colors[i].color.r, places) and roundVal(_color[1], places) == roundVal(palette.colors[i].color.g, places) and roundVal(_color[2], places) == roundVal(palette.colors[i].color.b, places)):
            matchingColorIndex = i
    #~
    if (matchingColorIndex == -1):
        color = palette.colors.new()
        color.color = _color
    else:
        palette.colors.active = palette.colors[matchingColorIndex]
        color = palette.colors[matchingColorIndex]
    #~        
    #print("Active color is: " + "\"" + palette.colors.active.name + "\" " + str(palette.colors.active.color))
    return color

# ~ ~ ~ 
def createColorWithPalette(_color, numPlaces=7, maxColors=0):
    palette = getActivePalette()
    matchingColorIndex = -1
    places = numPlaces
    for i in range(0, len(palette.colors)):
        if (roundVal(_color[0], places) == roundVal(palette.colors[i].color.r, places) and roundVal(_color[1], places) == roundVal(palette.colors[i].color.g, places) and roundVal(_color[2], places) == roundVal(palette.colors[i].color.b, places)):
            matchingColorIndex = i
    #~
    if (matchingColorIndex == -1):
        if (maxColors<1 or len(palette.colors)<maxColors):
            color = palette.colors.new()
            color.color = _color
        else:
            distances = []
            sortedColors = []
            for color in palette.colors:
                sortedColors.append(color)
            for color in sortedColors:
                distances.append(getDistance(_color, color.color))
            sortedColors.sort(key=dict(zip(sortedColors, distances)).get)
            palette.colors.active = palette.colors[sortedColors[0].name]
    else:
        palette.colors.active = palette.colors[matchingColorIndex]
        color = palette.colors[matchingColorIndex]
    #~        
    #print("Active color is: " + "\"" + palette.colors.active.name + "\" " + str(palette.colors.active.color))
    return color
# ~ ~ ~

def matchColorToPalette(_color):
    palette = getActivePalette()
    distances = []
    sortedColors = []
    for color in palette.colors:
        sortedColors.append(color)
    for color in sortedColors:
        distances.append(getDistance(_color, color.color))
    sortedColors.sort(key=dict(zip(sortedColors, distances)).get)
    returns = palette.colors[sortedColors[0].name]
    palette.colors.active = returns
    return returns

def createAndMatchColorPalette(color, numMaxColors=16, numColPlaces=5):
    palette = getActivePalette()
    if (len(palette.colors) < numMaxColors):
        createColorWithPalette(color, numColPlaces, numMaxColors)
    else:
        matchColorToPalette(color)
    return getActiveColor()

def changeColor():
    frame = getActiveFrame()
    palette = getActivePalette()
    strokes = getSelectedStrokes()
    #~
    lineWidthBackup = []
    pointsBackup = []
    for stroke in strokes:
        lineWidthBackup.append(stroke.line_width)
        pointsBackup.append(stroke.points)
    #~
    deleteSelected()
    #~
    for i, points in enumerate(pointsBackup):
        newStroke = frame.strokes.new(getActiveColor().name)
        newStroke.draw_mode = "3DSPACE" # either of ("SCREEN", "3DSPACE", "2DSPACE", "2DIMAGE")
        newStroke.line_width = lineWidthBackup[i]
        newStroke.points.add(len(points))
        for j in range(0, len(points)):
            createPoint(newStroke, j, points[j].co)
    print(str(len(strokes)) + " changed to " + palette.colors.active.name)

def newLayer(name="NewLayer", setActive=True):
    gp = getActiveGp()
    gp.layers.new(name)
    if (setActive==True):
        gp.layers.active = gp.layers[len(gp.layers)-1]
    return gp.layers[len(gp.layers)-1]

def getStrokePoints(target=None):
    returns = []
    if not target:
        target = getSelectedStroke()
    for point in target.points:
        returns.append(point.co)
    return returns

def reprojectAllStrokes():
    strokes = getAllStrokes()
    newLayer()
    for stroke in strokes:
        points = getStrokePoints(stroke)
        try:
            drawPoints(points)
        except:
            pass

def compareTuple(t1, t2, numPlaces=5):
    if (roundVal(t1[0], numPlaces) == roundVal(t2[0], numPlaces) and roundVal(t1[1], numPlaces) == roundVal(t2[1], numPlaces) and roundVal(t1[2], numPlaces) == roundVal(t2[2], numPlaces)):
        return True
    else:
        return False

def setActiveObject(target=None):
    if not target:
        target = ss()
    bpy.context.scene.objects.active = target
    return target

def getActiveObject():
    return bpy.context.scene.objects.active

def deleteFromAllFrames():
    origStrokes = []
    frame = getActiveFrame()
    for stroke in frame.strokes:
        addToOrig = False
        for point in stroke.points:
            if (point.select):
               addToOrig = True
               break
        if (addToOrig == True):
           origStrokes.append(stroke) 
    print("Checking for " + str(len(origStrokes)) + " selected strokes.")
    #~    
    allStrokes = getAllStrokes()
    deleteList = []
    numPlaces = 5
    for allStroke in allStrokes:
        doDelete = False
        for origStroke in origStrokes:
            if (len(allStroke.points) == len(origStroke.points)):
                for i in range(0, len(allStroke.points)):
                    if (roundVal(allStroke.points[i].co.x, numPlaces) == roundVal(origStroke.points[i].co.x, numPlaces) and roundVal(allStroke.points[i].co.y, numPlaces) == roundVal(origStroke.points[i].co.y, numPlaces) and roundVal(allStroke.points[i].co.z, numPlaces) == roundVal(origStroke.points[i].co.z, numPlaces)):
                        doDelete = True
                    else:
                        doDelete = False
                        break
        if (doDelete):
            deleteList.append(allStroke)
    #~
    print(str(len(deleteList)) + " strokes listed for deletion.")
    for stroke in deleteList:
        stroke.select = True
    layer = getActiveLayer()
    start, end = getStartEnd()
    for i in range(start, end):
        goToFrame(i)    
        for j in range(0, len(layer.frames)):
            setActiveFrame(j)
            deleteSelected()

def getAllLayers():
    gp = getActiveGp()
    print("Got " + str(len(gp.layers)) + " layers.")
    return gp.layers

def getAllFrames(active=False):
    returns = []
    layers = getAllLayers()
    for layer in layers:
        if (active==False):
            for frame in layer.frames:
                returns.append(frame)
        else:
            returns.append(layer.active_frame)
    print("Got " + str(len(returns)) + " frames.")
    return returns

def getActiveFrame():
    gp = getActiveGp()
    layer = gp.layers.active
    frame = layer.active_frame
    return frame

# gp not timeline
def setActiveFrame(index):
    layer = getActiveLayer()
    if index < len(layer.frames):
        layer.active_frame = layer.frames[index]
        refresh()
        print("Moved to layer frame " + str(index))
    else:
        print("Outside of layer range")
    return layer.active_frame

def getAllStrokes(active=False):
    returns = []
    frames = getAllFrames(active)
    for frame in frames:
        for stroke in frame.strokes:
            returns.append(stroke)
    print("Got " + str(len(returns)) + " strokes.")
    return returns

def getLayerStrokes(name=None):
    gp = getActiveGp()
    if not name:
        name = gp.layers.active.info
    layer = gp.layers[name]
    strokes = []
    for frame in layer.frames:
        for stroke in frame.strokes:
            strokes.append(stroke)
    return strokes

def getFrameStrokes(num=None, name=None):
    gp = getActiveGp()
    if not name:
        name = gp.layers.active.info
    layer = gp.layers[name]
    if not num:
        num = layer.active_frame.frame_number
    strokes = []
    for frame in layer.frames:
        if (frame.frame_number == num):
            for stroke in frame.strokes:
                strokes.append(stroke)
    return strokes

def getLayerStrokesAvg(name=None):
    gp = getActiveGp()
    if not name:
        name = gp.layers.active.info
    layer = gp.layers[name]
    return float(roundVal(len(getLayerStrokes(name)) / len(layer.frames), 2))

def getAllStrokesAvg(locked=True):
    gp = getActiveGp()
    avg = 0
    for layer in gp.layers:
        if (layer.lock == False or locked == True):
            avg += getLayerStrokesAvg(layer.info)
    return float(roundVal(avg / len(gp.layers), 2))

def getSelectedStrokes(active=True):
    returns = []
    strokes = getAllStrokes(active)
    for stroke in strokes:
        if (stroke.select):
            returns.append(stroke)
        else:
            for point in stroke.points:
                if (point.select):
                    returns.append(stroke)
                    break
    if (len(returns) > 0):
        print(str(len(returns)) + " selected strokes.")
    else:
        print("No selected strokes.")
    return returns

def getSelectedStroke():
    strokes = getSelectedStrokes()
    if (len(strokes) > 0):
        print("Only returning first selected stroke.")
        return strokes[0]
    else:
        print("No selected strokes.")

def deleteSelected(target="strokes"):
    original_type = bpy.context.area.type
    print("Current context: " + original_type)
    bpy.context.area.type = "VIEW_3D"
    #~
    # strokes, points, frame
    bpy.ops.gpencil.delete(type=target.upper())
    #~
    bpy.context.area.type = original_type

# https://www.blender.org/forum/viewtopic.php?t=27834
def AssembleOverrideContextForView3dOps():
    #=== Iterates through the blender GUI's windows, screens, areas, regions to find the View3D space and its associated window.  Populate an 'oContextOverride context' that can be used with bpy.ops that require to be used from within a View3D (like most addon code that runs of View3D panels)
    # Tip: If your operator fails the log will show an "PyContext: 'xyz' not found".  To fix stuff 'xyz' into the override context and try again!
    for oWindow in bpy.context.window_manager.windows:          ###IMPROVE: Find way to avoid doing four levels of traversals at every request!!
        oScreen = oWindow.screen
        for oArea in oScreen.areas:
            if oArea.type == 'VIEW_3D':                         ###LEARN: Frequently, bpy.ops operators are called from View3d's toolbox or property panel.  By finding that window/screen/area we can fool operators in thinking they were called from the View3D!
                for oRegion in oArea.regions:
                    if oRegion.type == 'WINDOW':                ###LEARN: View3D has several 'windows' like 'HEADER' and 'WINDOW'.  Most bpy.ops require 'WINDOW'
                        #=== Now that we've (finally!) found the damn View3D stuff all that into a dictionary bpy.ops operators can accept to specify their context.  I stuffed extra info in there like selected objects, active objects, etc as most operators require them.  (If anything is missing operator will fail and log a 'PyContext: error on the log with what is missing in context override) ===
                        oContextOverride = {'window': oWindow, 'screen': oScreen, 'area': oArea, 'region': oRegion, 'scene': bpy.context.scene, 'edit_object': bpy.context.edit_object, 'active_object': bpy.context.active_object, 'selected_objects': bpy.context.selected_objects}   # Stuff the override context with very common requests by operators.  MORE COULD BE NEEDED!
                        print("-AssembleOverrideContextForView3dOps() created override context: ", oContextOverride)
                        return oContextOverride
    raise Exception("ERROR: AssembleOverrideContextForView3dOps() could not find a VIEW_3D with WINDOW region to create override context to enable View3D operators.  Operator cannot function.")

def TestView3dOperatorFromPythonScript():       # Run this from a python script and operators that would normally fail because they were not called from a View3D context will work!
    oContextOverride = AssembleOverrideContextForView3dOps()    # Get an override context suitable for bpy.ops operators that require View3D
    bpy.ops.mesh.knife_project(oContextOverride)                # An operator like this normally requires to run off the View3D context.  By overriding it with what it needs it will run from any context (like Python script, Python shell, etc)
    print("TestView3dOperatorFromPythonScript() completed succesfully.")

def addVec3(p1, p2):
    return(p1[0]+p2[0], p1[1]+p2[1], p1[2]+p2[2])

def multVec3(p1, p2):
    return(p1[0]*p2[0], p1[1]*p2[1], p1[2]*p2[2])

# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

# 3 of 10. READ / WRITE

def exportAlembic(url="test.abc"):
    bpy.ops.wm.alembic_export(filepath=url, vcolors=True, face_sets=True, renderable_only=False)

def exportForUnity(filepath=None, sketchFab=True):
    #origFilepath = ""
    #if not filepath:
        #filepath = getFilePath()
    #else:
    filepath = filepath.split(".fbx")[0] + "_"
    rootFilepath = filepath.split(getFileName())[0]
    #~
    start, end = getStartEnd()
    target = matchName("latk")
    sketchFabList = []
    sketchFabListNum = []
    for tt in range(0, len(target)):
        deselect()
        for i in range(start, end):
            deselect()
            goToFrame(i)
            if (target[tt].hide==False):
                deselect()
                target[tt].select=True
                exportName = target[tt].name
                exportName = exportName.split("latk_")[1]
                exportName = exportName.split("_mesh")[0]
                exporter(url=filepath, manualSelect=True, fileType="fbx", name=exportName, legacyFbx=True)
                sketchFabList.append(str(1.0/getSceneFps()) + " " + getFileName() + "_" + exportName + ".fbx\r") #"0.083 " + exportName + ".fbx\r")
                sketchFabListNum.append(float(exportName.split("_")[len(exportName.split("_"))-1]))
                break
    if (sketchFab==True):
        print("before sort: ")
        print(sketchFabList)
        print(sketchFabListNum)
        # this sorts entries by number instead of order in Outliner pane
        sketchFabList.sort(key=lambda x: x[0])
        ind = [i[0] for i in sorted(enumerate(sketchFabListNum),key=lambda x: x[1])]
        sketchFabList = [i[0] for i in sorted(zip(sketchFabList, ind),key=lambda x: x[1])]
        #~
        print(getFilePath() + getFileName())
        tempName = exportName.split("_")
        tempString = ""
        for i in range(0, len(tempName)-1):
            tempString += str(tempName[i])
            if (i < len(tempName)-1):
                tempString += "_"
        print("after sort: ")
        print(sketchFabList)
        #writeTextFile(filepath + getFileName() + "_" + tempString + ".sketchfab.timeframe", sketchFabList)
        writeTextFile(rootFilepath + "sketchfab.timeframe", sketchFabList)

def exporter(name="test", url=None, winDir=False, manualSelect=False, fileType="fbx", legacyFbx=False):
    if not url:
        url = getFilePath()
        if (winDir==True):
            url += "\\"
        else:
            url += "/"
    #~
    if (fileType.lower() == "alembic"):
        bpy.ops.wm.alembic_export(filepath=name + ".abc", vcolors=True, face_sets=True, renderable_only=False)
    else:
        if (manualSelect == True):
                if (fileType.lower()=="fbx"):
                    if (legacyFbx == True):
                        bpy.ops.export_scene.fbx(filepath=url + name + ".fbx", use_selection=True, version="ASCII6100") # legacy version
                    else:
                        bpy.ops.export_scene.fbx(filepath=url + name + ".fbx", use_selection=True, version="BIN7400")
                else:
                    bpy.ops.export_scene.obj(filepath=url + name + ".obj", use_selection=True)
        else:
            for j in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
                bpy.ops.object.select_all(action='DESELECT')
                goToFrame(j)
                for i in range(0, len(bpy.data.objects)):
                    if (bpy.data.objects[i].hide == False):
                        bpy.data.objects[i].select = True
                #bpy.context.scene.update()
                #~
                if (fileType=="fbx"):
                    if (legacyFbx == True):
                        bpy.ops.export_scene.fbx(filepath=url + name + "_" + str(j) + ".fbx", use_selection=True, version="ASCII6100") # legacy version
                    else:
                        bpy.ops.export_scene.fbx(filepath=url + name + "_" + str(j) + ".fbx", use_selection=True, version="BIN7400")
                else:
                    bpy.ops.export_scene.obj(filepath=url + name + "_" + str(j) + ".obj", use_selection=True)


def importAppend(blendfile, section, obj, winDir=False):
    # http://blender.stackexchange.com/questions/38060/how-to-link-append-with-a-python-script
    # blendfile = "D:/path/to/the/repository.blend"
    # section   = "\\Action\\"
    # obj    = "myaction"
    #~
    url  = blendfile + section + obj
    if (winDir==True):
        section = blendfile + "\\" + section + "\\"
    else:
        section = blendfile + "/" + section + "/"
    #~
    bpy.ops.wm.append(filepath=url, filename=obj, directory=section)

def writeTextFile(name="test.txt", lines=None):
    file = open(name,"w") 
    for line in lines:
        file.write(line) 
    file.close() 

def readTextFile(name="text.txt"):
    file = open(name, "r") 
    return file.read() 

def newFile():
    bpy.ops.wm.read_homefile()

def saveFile(name, format=True):
    if (format==True):
        name = getFilePath() + name + ".blend"
    bpy.ops.wm.save_as_mainfile(filepath=name)

def openFile(name, format=True):
    if (format==True):
        name = getFilePath() + name + ".blend"
    bpy.ops.wm.open_mainfile(filepath=name)

def getFilePath(stripFileName=True):
    name = bpy.context.blend_data.filepath
    if (stripFileName==True):
        name = name[:-len(getFileName(stripExtension=False))]
    return name

def getFileName(stripExtension=True):
    name = bpy.path.basename(bpy.context.blend_data.filepath)
    if (stripExtension==True):
        name = name[:-6]
    return name

def fromGpToLatk(bake=False, roundValues=False, numPlaces=7, useScaleAndOffset=False, globalScale=(1.0, 1.0, 1.0), globalOffset=(0.0, 0.0, 0.0)):
    print("Begin building Latk object from Grease Pencil...")
    if(bake == True):
        bakeFrames()
    gp = getActiveGp()
    pal = getActivePalette()
    #~
    la = Latk()
    la.frame_rate = getSceneFps()
    #~
    for layer in gp.layers:
        laLayer = LatkLayer()
        laLayer.name = layer.info
        if (layer.parent == True):
            laLayer.parent = layer.parent.name
        for frame in layer.frames:
            laFrame = LatkFrame()

            laFrame.frame_number = frame.frame_number
            if (layer.parent == True):
                laFrame.parent_location = layer.parent.location
            for stroke in frame.strokes:
                laStroke = LatkStroke()
                
                color = (0,0,0)
                alpha = 0.9
                fill_color = (1,1,1)
                fill_alpha = 0.0
                try:
                    col = pal.colors[stroke.colorname]
                    color = (col.color[0], col.color[1], col.color[2])
                    alpha = col.alpha 
                    fill_color = (col.fill_color[0], col.fill_color[1], col.fill_color[2])
                    fill_alpha = col.fill_alpha
                except:
                    pass
                laStroke.color = color
                laStroke.alpha = alpha
                laStroke.fill_color = fill_color
                laStroke.fill_alpha = fill_alpha
                for point in stroke.points:
                    x = point.co[0]
                    y = point.co[1]
                    z = point.co[2]
                    pressure = 1.0
                    pressure = point.pressure
                    strength = 1.0
                    strength = point.strength
                    #~
                    if (useScaleAndOffset == True):
                        x = (x * globalScale[0]) + globalOffset[0]
                        y = (y * globalScale[1]) + globalOffset[1]
                        z = (z * globalScale[2]) + globalOffset[2]
                    #~
                    if (roundValues == True):
                        x = roundVal(x, numPlaces)
                        y = roundVal(y, numPlaces)
                        z = roundVal(z, numPlaces)
                        pressure = roundVal(pressure, numPlaces)
                        strength = roundVal(strength, numPlaces)

                    laPoint = LatkPoint((x, y, z), pressure, strength)
                    laStroke.points.append(laPoint)
                laFrame.strokes.append(laStroke)
            laLayer.frames.append(laFrame)
        la.layers.append(laLayer)
    return la
    print("...end building Latk object from Grease Pencil.")           

def fromLatkToGp(la=None, resizeTimeline=True, useScaleAndOffset=False, globalScale=(1.0, 1.0, 1.0), globalOffset=(0.0, 0.0, 0.0)):
    print("Begin building Grease Pencil from Latk object...")
    clearAll()
    gp = getActiveGp()
    
    longestFrameNum = 1
    #~
    for laLayer in la.layers:
        layer = gp.layers.new(laLayer.name, set_active=True)
        #~
        for i, laFrame in enumerate(laLayer.frames):
            try:
                frame = layer.frames.new(laLayer.frames[i].frame_number) 
            except:
                frame = layer.frames.new(i) 
            if (frame.frame_number > longestFrameNum):
                longestFrameNum = frame.frame_number
            for laStroke in laFrame.strokes:
                strokeColor = (0,0,0)
                try:
                    color = laStroke.color
                    strokeColor = (color[0], color[1], color[2])
                except:
                    pass
                createColor(strokeColor)
                stroke = frame.strokes.new(getActiveColor().name)
                stroke.draw_mode = "3DSPACE" # either of ("SCREEN", "3DSPACE", "2DSPACE", "2DIMAGE")
                laPoints = laStroke.points
                stroke.points.add(len(laPoints)) # add 4 points
                for l, laPoint in enumerate(laPoints):
                    co = laPoint.co 
                    x = co[0]
                    y = co[1]
                    z = co[2]
                    pressure = 1.0
                    strength = 1.0
                    if (useScaleAndOffset == True):
                        x = (x * globalScale[0]) + globalOffset[0]
                        y = (y * globalScale[1]) + globalOffset[1]
                        z = (z * globalScale[2]) + globalOffset[2]
                    #~
                    if (laPoint.pressure != None):
                        pressure = laPoint.pressure
                    if (laPoint.strength != None):
                        strength = laPoint.strength
                    createPoint(stroke, l, (x, y, z), pressure, strength)
    #~  
    if (resizeTimeline == True):
        setStartEnd(0, longestFrameNum, pad=False)  
    print("...end building Grease Pencil from Latk object.")           

# http://blender.stackexchange.com/questions/24694/query-grease-pencil-strokes-from-python
def writeBrushStrokes(filepath=None, bake=True, roundValues=True, numPlaces=7, zipped=False, useScaleAndOffset=False, globalScale=Vector((0.1, 0.1, 0.1)), globalOffset=Vector((0, 0, 0))):
    url = filepath # compatibility with gui keywords
    #~
    if(bake == True):
        bakeFrames()
    gp = bpy.context.scene.grease_pencil
    palette = getActivePalette()
    #~
    sg = []
    sg.append("{")
    sg.append("\t\"creator\": \"blender\",")
    sg.append("\t\"grease_pencil\": [")
    sg.append("\t\t{")
    sg.append("\t\t\t\"frame_rate\": " + str(getSceneFps()) + ",")
    sg.append("\t\t\t\"layers\": [")
    #~
    sl = []
    for f, layer in enumerate(gp.layers):
        sb = []
        for h, frame in enumerate(layer.frames):
            currentFrame = h
            goToFrame(h)
            sb.append("\t\t\t\t\t\t{") # one frame
            sb.append("\t\t\t\t\t\t\t\"frame_number\": " + str(frame.frame_number) + ",")
            if (layer.parent == True):
                sb.append("\t\t\t\t\t\t\t\"parent_location\": " + "[" + str(layer.parent.location[0]) + ", " + str(layer.parent.location[1]) + ", " + str(layer.parent.location[2]) + "],")
            sb.append("\t\t\t\t\t\t\t\"strokes\": [")
            if (len(frame.strokes) > 0):
                sb.append("\t\t\t\t\t\t\t\t{") # one stroke
                for i, stroke in enumerate(frame.strokes):
                    color = (0,0,0)
                    alpha = 0.9
                    fill_color = (1,1,1)
                    fill_alpha = 0.0
                    try:
                        col = palette.colors[stroke.colorname]
                        color = col.color
                        alpha = col.alpha 
                        fill_color = col.fill_color
                        fill_alpha = col.fill_alpha
                    except:
                        pass
                    sb.append("\t\t\t\t\t\t\t\t\t\"color\": [" + str(color[0]) + ", " + str(color[1]) + ", " + str(color[2])+ "],")
                    sb.append("\t\t\t\t\t\t\t\t\t\"alpha\": " + str(alpha) + ",")
                    sb.append("\t\t\t\t\t\t\t\t\t\"fill_color\": [" + str(fill_color[0]) + ", " + str(fill_color[1]) + ", " + str(fill_color[2])+ "],")
                    sb.append("\t\t\t\t\t\t\t\t\t\"fill_alpha\": " + str(fill_alpha) + ",")
                    sb.append("\t\t\t\t\t\t\t\t\t\"points\": [")
                    for j, point in enumerate(stroke.points):
                        x = point.co.x
                        y = point.co.z
                        z = point.co.y
                        pressure = 1.0
                        pressure = point.pressure
                        strength = 1.0
                        strength = point.strength
                        #~
                        if useScaleAndOffset == True:
                            x = (x * globalScale.x) + globalOffset.x
                            y = (y * globalScale.y) + globalOffset.y
                            z = (z * globalScale.z) + globalOffset.z
                        #~
                        if roundValues == True:
                            sb.append("\t\t\t\t\t\t\t\t\t\t{\"co\": [" + roundVal(x, numPlaces) + ", " + roundVal(y, numPlaces) + ", " + roundVal(z, numPlaces) + "], \"pressure\": " + roundVal(pressure, numPlaces) + ", \"strength\": " + roundVal(strength, numPlaces))
                        else:
                            sb.append("\t\t\t\t\t\t\t\t\t\t{\"co\": [" + str(x) + ", " + str(y) + ", " + str(z) + "], \"pressure\": " + str(pressure) + ", \"strength\": " + str(strength))                  
                        #~
                        if j == len(stroke.points) - 1:
                            sb[len(sb)-1] +="}"
                            sb.append("\t\t\t\t\t\t\t\t\t]")
                            if (i == len(frame.strokes) - 1):
                                sb.append("\t\t\t\t\t\t\t\t}") # last stroke for this frame
                            else:
                                sb.append("\t\t\t\t\t\t\t\t},") # end stroke
                                sb.append("\t\t\t\t\t\t\t\t{") # begin stroke
                        else:
                            sb[len(sb)-1] += "},"
                    if i == len(frame.strokes) - 1:
                        sb.append("\t\t\t\t\t\t\t]")
            else:
                sb.append("\t\t\t\t\t\t\t]")
            if h == len(layer.frames) - 1:
                sb.append("\t\t\t\t\t\t}")
            else:
                sb.append("\t\t\t\t\t\t},")
        #~
        sf = []
        sf.append("\t\t\t\t{") 
        sf.append("\t\t\t\t\t\"name\": \"" + layer.info + "\",")
        if (layer.parent):
            sf.append("\t\t\t\t\t\"parent\": \"" + layer.parent.name + "\",")
        sf.append("\t\t\t\t\t\"frames\": [")
        sf.append("\n".join(sb))
        sf.append("\t\t\t\t\t]")
        if (f == len(gp.layers)-1):
            sf.append("\t\t\t\t}")
        else:
            sf.append("\t\t\t\t},")
        sl.append("\n".join(sf))
        #~
    sg.append("\n".join(sl))
    sg.append("\t\t\t]")
    sg.append("\t\t}")
    sg.append("\t]")
    sg.append("}")
    #~
    if (zipped == True):
        filenameRaw = os.path.split(url)[1].split(".")
        filename = ""
        for i in range(0, len(filenameRaw)-1):
            filename += filenameRaw[i]
        imz = InMemoryZip()
        imz.append(filename + ".json", "\n".join(sg))
        imz.writetofile(url)
    else:
        with open(url, "w") as f:
            f.write("\n".join(sg))
            f.closed
    print("Wrote " + url)
    #~                
    return {'FINISHED'}
    
def readBrushStrokes(filepath=None, resizeTimeline=True, useScaleAndOffset=False, globalScale=Vector((10, 10, 10)), globalOffset=Vector((0, 0, 0))):
    url = filepath # compatibility with gui keywords
    #~
    gp = getActiveGp()
    data = None
    #~
    filename = os.path.split(url)[1].split(".")
    filetype = filename[len(filename)-1].lower()
    if (filetype == "latk" or filetype == "zip"):
        imz = InMemoryZip()
        imz.readFromDisk(url)
        # https://stackoverflow.com/questions/6541767/python-urllib-error-attributeerror-bytes-object-has-no-attribute-read/6542236
        data = json.loads(imz.files[0].decode("utf-8"))        
    else:
        with open(url) as data_file:    
            data = json.load(data_file)
    #~
    longestFrameNum = 1
    for layerJson in data["grease_pencil"][0]["layers"]:
        layer = gp.layers.new(layerJson["name"], set_active=True)
        palette = getActivePalette()    
        #~
        for i, frameJson in enumerate(layerJson["frames"]):
            try:
            	frame = layer.frames.new(layerJson["frames"][i]["frame_number"]) 
            except:
            	frame = layer.frames.new(i) 
            if (frame.frame_number > longestFrameNum):
                longestFrameNum = frame.frame_number
            for strokeJson in frameJson["strokes"]:
                strokeColor = (0,0,0)
                try:
                    colorJson = strokeJson["color"]
                    strokeColor = (colorJson[0], colorJson[1], colorJson[2])
                except:
                    pass
                createColor(strokeColor)
                stroke = frame.strokes.new(getActiveColor().name)
                stroke.draw_mode = "3DSPACE" # either of ("SCREEN", "3DSPACE", "2DSPACE", "2DIMAGE")
                pointsJson = strokeJson["points"]
                stroke.points.add(len(pointsJson)) # add 4 points
                for l, pointJson in enumerate(pointsJson):
                    coJson = pointJson["co"] 
                    x = coJson[0]
                    y = coJson[2]
                    z = coJson[1]
                    pressure = 1.0
                    strength = 1.0
                    if (useScaleAndOffset == True):
                        x = (x * globalScale.x) + globalOffset.x
                        y = (y * globalScale.y) + globalOffset.y
                        z = (z * globalScale.z) + globalOffset.z
                    #~
                    if ("pressure" in pointJson):
                        pressure = pointJson["pressure"]
                    if ("strength" in pointJson):
                        strength = pointJson["strength"]
                    #stroke.points[l].co = (x, y, z)
                    createPoint(stroke, l, (x, y, z), pressure, strength)
    #~  
    if (resizeTimeline == True):
        setStartEnd(0, longestFrameNum, pad=False)              
    return {'FINISHED'}

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

def writeSvg(filepath=None):
	# Note: keep fps at 24 and above to prevent timing artifacts. 
	# Last frame in timeline must be empty.
    minLineWidth=3
    camera = getActiveCamera()
    fps = float(getSceneFps())
    start, end = getStartEnd()
    duration = float(end - start) / fps
    gp = getActiveGp()
    #url = getFilePath() + name
    url = filepath
    print(url)
    sW = getSceneResolution()[0]
    sH = getSceneResolution()[1]
    svg = []
    #~
    # HEADER
    svg.append("<?xml version=\"1.0\" encoding=\"utf-8\"?>\r");
    svg.append("<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\r")
    svg.append("<svg version=\"1.1\" id=\"Layer_1\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" x=\"0px\" y=\"0px\"\r")
    svg.append("\t" + "width=\"" + str(sW) + "px\" height=\"" + str(sH) + "px\" viewBox=\"0 0 " + str(sW) + " " + str(sH) + "\" enable-background=\"new 0 0 " + str(sW) + " " + str(sH) +"\" xml:space=\"preserve\">\r")
    #~
    # BODY
    for layer in gp.layers:
        layerInfo = layer.info.replace(" ", "_").replace(".", "_")
        svg.append("\t" + "<g id=\"" + layerInfo + "\">\r")
        for i, frame in enumerate(layer.frames):
            goToFrame(frame.frame_number)
            svg.append("\t\t" + "<g id=\"" + layerInfo + "_frame" + str(i) + "\">\r")
            palette = getActivePalette()
            for stroke in frame.strokes:
                width = stroke.line_width
                if (width == None or width < minLineWidth):
                    width = minLineWidth
                color = palette.colors[stroke.colorname]
                print("found color: " + color.name)
                cStroke = (color.color[0], color.color[1], color.color[2], color.alpha)
                cFill = (color.fill_color[0], color.fill_color[1], color.fill_color[2], color.fill_alpha)
                svg.append("\t\t\t" + svgStroke(points=stroke.points, stroke=(cStroke[0], cStroke[1], cStroke[2]), fill=(cFill[0], cFill[1], cFill[2]), strokeWidth=minLineWidth, strokeOpacity=cStroke[3], fillOpacity=cFill[3], camera=camera) + "\r")
            #~
            svg.append("\t\t\t" + svgAnimate(frame=frame.frame_number, fps=fps, duration=duration) + "\r")
            svg.append("\t\t" + "</g>\r")
        svg.append("\t" + "</g>\r")
    #~
    # FOOTER
    svg.append("</svg>\r")
    #~
    writeTextFile(url, svg)

def svgAnimate(frame=0, fps=12, duration=10, startFrame=False, endFrame=False):
    keyIn = (float(frame) / float(fps)) / float(duration)
    keyOut = keyIn + (1.0/float(fps))
    returns = "<animate attributeName=\"display\" repeatCount=\"indefinite\" dur=\"" + str(duration) + "s\" keyTimes=\"0;" + str(keyIn) + ";" + str(keyOut) + ";1\" values=\"none;inline;none;none\"/>"
    return returns

def svgStroke(points=None, stroke=(0,0,1), fill=(1,0,0), strokeWidth=2.0, strokeOpacity=1.0, fillOpacity=1.0, camera=None, closed=False):
    # https://developer.mozilla.org/en-US/docs/Web/SVG/Element/path
    returns = "<path stroke=\""+ normRgbToHex(stroke) + "\" fill=\""+ normRgbToHex(fill) + "\" stroke-width=\"" + str(strokeWidth) + "\" stroke-opacity=\"" + str(strokeOpacity) + "\" fill-opacity=\"" + str(fillOpacity) + "\" d=\""
    for i, point in enumerate(points):
        co = getWorldCoords(co=point.co, camera=camera)
        if (i == 0):
            returns += "M" + str(co[0]) + " " + str(co[1]) + " "
        elif (i > 0 and i < len(points)-1):
            returns += "L" + str(co[0]) + " " + str(co[1]) + " "
        elif (i == len(points)-1):
            if (closed==True):
                returns += "L" + str(co[0]) + " " + str(co[1]) + " z"
            else:
                returns += "L" + str(co[0]) + " " + str(co[1])
    returns += "\"/>"
    return returns

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

def writePainter(filepath=None):
    camera=getActiveCamera()
    outputFile = []
    dim = (float(getSceneResolution()[0]), float(getSceneResolution()[1]), 0.0)
    outputFile.append(painterHeader(dim))
    #~
    strokes = []
    gp = getActiveGp()
    palette = getActivePalette()
    for layer in gp.layers:
        if (layer.lock == False):
            for stroke in layer.active_frame.strokes:
                strokes.append(stroke)
    counter = 0
    for stroke in strokes:
        color = palette.colors[stroke.color.name].color
        points = []
        for point in stroke.points: 
            co = getWorldCoords(co=point.co, camera=camera)
            x = co[0] 
            y = co[1]
            prs = point.pressure
            point = (x, y, prs, counter)
            counter += 1
            points.append(point)
        outputFile.append(painterStroke(points, color))
    #~
    outputFile.append(painterFooter())
    writeTextFile(filepath, outputFile)

def painterHeader(dim=(1024,1024,1024), bgColor=(1,1,1)):
    s = "script_version_number version 10\r"
    s += "artist_name \"\"\r"
    s += "start_time date Wed, May 24, 2017 time 3:23 PM\r"
    s += "start_random 1366653360 1884255589\r"
    #s += "variant \"Painter Brushes\" \"F-X\" \"Big Wet Luscious\"\r"
    #s += "max_size_slider   14.00000\r"
    #s += "min_radius_fraction_slider    0.20599\r"
    s += "build\r"
    s += "penetration_slider 100 percent\r"
    #s += "texture \"Paper Textures\" \"<str t=17500 i=001>\"\r"
    s += "grain_inverted unchecked\r"
    s += "directional_grain unchecked\r"
    s += "scale_slider 1.00000\r"
    s += "paper_brightness_slider 0.50000\r"
    s += "paper_contrast_slider 1.00000\r"
    s += "portfolio_change \"\"\r"
    #s += "gradation \"Painter Gradients.gradients\" \"<str t=17503 i=001>\"\r"
    #s += "weaving \"Painter Weaves.weaves\" \"<str t=17504 i=001>\"\r"
    #s += "pattern_change \"Painter Patterns\" \"<str t=17001 i=001>\"\r"
    #s += "path_library_change \"Painter Selections\"\r"
    #s += "nozzle_change \"Painter Nozzles\" \"<str t=17000 i=001>\"\r"
    s += "use_brush_grid unchecked\r"
    s += "new_tool 1\r"
    s += "gradation_options type 0 order 0 angle 0.00 spirality  1.000\r"
    s += "pattern_options pattern_type 1 offset 0.594\r"
    s += "preserve_transparency unchecked\r"
    s += "wind_direction 4.712389\r"
    #s += "color red 1 green 109 blue 255\r"
    #s += "background_color red 255 green 4 blue 4\r"
    #s += "change_file \"ntitled-1\"\r"
    s += "new_3 \"Untitled-1\" width " + str(int(dim[0])) + " height " + str(int(dim[1])) + " resolution 72.00000 width_unit 1 height_unit 1 resolution_unit 1 paper_color red " + str(int(bgColor[0] * 255.0)) + " green " + str(int(bgColor[1] * 255.0)) + " blue " + str(int(bgColor[2] * 255.0)) + " movie 0 frames 1\r"
    return s

def painterFooter():
    s = "end_time date Wed, May 24, 2017 time 3:25 PM\r"
    return s

def painterStroke(points, color=(0,0,0)):
    s = "color red " + str(int(color[0]*255.0)) + " green " + str(int(color[1]*255.0)) + " blue " + str(int(color[2]*255.0)) + "\r"
    s += "stroke_start\r"
    for point in points:
        s += painterPoint(point)
    s += "stroke_end\r"
    return s

def painterPoint(point):
    x = point[0]
    y = point[1]
    time = point[3]
    s = "pnt x " + str(x) + " y " + str(y) + " time " + str(time) + " prs " + str(roundVal(point[2], 2)) + " tlt 0.00 brg 0.00 whl 1.00 rot 0.00\r"
    return s

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

def importVRDoodler(filepath=None):
    globalScale = Vector((1, 1, 1))
    globalOffset = Vector((0, 0, 0))
    useScaleAndOffset = True
    #numPlaces = 7
    #roundValues = True

    with open(filepath) as data_file: 
        data = data_file.readlines()

    vrd_strokes = []
    vrd_points = []
    for line in data:
        if str(line).startswith("l") == True:
            if (len(vrd_points) > 0):
                vrd_strokes.append(vrd_points)
                vrd_points = []
        elif str(line).startswith("v") == True:
            vrd_pointRaw = line.split()
            vrd_point = (-1 * float(vrd_pointRaw[1]), float(vrd_pointRaw[2]), float(vrd_pointRaw[3]))
            vrd_points.append(vrd_point)

    gp = getActiveGp()
    layer = gp.layers.new("VRDoodler_layer", set_active=True)
    start, end = getStartEnd()
    frame = layer.frames.new(start)
    for vrd_stroke in vrd_strokes:
        strokeColor = (0.5,0.5,0.5)
        createColor(strokeColor)
        stroke = frame.strokes.new(getActiveColor().name)
        stroke.draw_mode = "3DSPACE" # either of ("SCREEN", "3DSPACE", "2DSPACE", "2DIMAGE")
        stroke.points.add(len(vrd_stroke)) # add 4 points
        for l, vrd_point in enumerate(vrd_stroke):
            x = vrd_point[0]
            y = vrd_point[2]
            z = vrd_point[1]
            pressure = 1.0
            strength = 1.0
            if useScaleAndOffset == True:
                x = (x * globalScale.x) + globalOffset.x
                y = (y * globalScale.y) + globalOffset.y
                z = (z * globalScale.z) + globalOffset.z
            #~
            createPoint(stroke, l, (x, y, z), pressure, strength)

def importPainter(filepath=None):
    globalScale = Vector((1, 1, -1))
    globalOffset = Vector((0, 0, 0))
    useScaleAndOffset = True
    #numPlaces = 7
    #roundValues = True

    gp = getActiveGp()
    layer = gp.layers.new("Painter_layer", set_active=True)
    start, end = getStartEnd()
    frame = getActiveFrame()
    if not frame:
        frame = layer.frames.new(start)

    width = 0
    height = 0
    points = []
    pressures = []

    with open(filepath) as data_file: 
        data = data_file.readlines()

    for line in data:
        if (line.startswith("new")):
            vals = line.split(" ")
            for i, val in enumerate(vals):
                if (val == "width"):
                    width = float(vals[i+1])
                elif (val == "height"):
                    height = float(vals[i+1])
        elif (line.startswith("color")):
            r = 0
            g = 0
            b = 0
            vals = line.split(" ")
            for i, val in enumerate(vals):
                if (val == "red"):
                    r = float(vals[i+1]) / 255.0
                if (val == "green"):
                    g = float(vals[i+1]) / 255.0
                if (val == "blue"):
                    b = float(vals[i+1]) / 255.0
            createColor((r, g, b))
        elif (line.startswith("stroke_start")):
            points = []
            pressures = []
        elif (line.startswith("pnt")):
            vals = line.split(" ")
            x = 0
            y = 0
            z = 0
            pressure = 0
            for i, val in enumerate(vals):
                if (val == "x"):
                    x = float(vals[i+1]) / width
                elif (val == "y"):
                    y = float(vals[i+1]) / height
                elif (val == "prs"):
                    pressure = float(vals[i+1])
            points.append((x, y, z))
            pressures.append(pressure)
        elif (line.startswith("stroke_end")):
            stroke = frame.strokes.new(getActiveColor().name)
            stroke.draw_mode = "3DSPACE"
            stroke.points.add(len(points))

            for i in range(0, len(points)):
                point = points[i]
                x = point[0]
                y = point[2]
                z = point[1]
                pressure = pressures[i]
                strength = 1.0
                if useScaleAndOffset == True:
                    x = (x * globalScale.x) + globalOffset.x
                    y = (y * globalScale.y) + globalOffset.y
                    z = (z * globalScale.z) + globalOffset.z
                createPoint(stroke, i, (x, y, z), pressure, strength)

def importNorman(filepath=None):
    globalScale = Vector((1, 1, 1))
    globalOffset = Vector((0, 0, 0))
    useScaleAndOffset = True
    #numPlaces = 7
    #roundValues = True
    #~
    with open(filepath) as data_file: 
        data = json.load(data_file)
    #~
    frames = []    
    for i in range(0, len(data["data"])):
        strokes = []
        for j in range(0, len(data["data"][i])):
            points = []
            for k in range(0, len(data["data"][i][j])):
                points.append((data["data"][i][j][k]["x"], data["data"][i][j][k]["y"], data["data"][i][j][k]["z"]))
            strokes.append(points)
        frames.append(strokes)
    #~
    gp = getActiveGp()
    layer = gp.layers.new("Norman_layer", set_active=True)
    for i in range(0, len(frames)):
        frame = layer.frames.new(i)
        for j in range(0, len(frames[i])):
            strokeColor = (0.5,0.5,0.5)
            createColor(strokeColor)
            stroke = frame.strokes.new(getActiveColor().name)
            stroke.draw_mode = "3DSPACE" # either of ("SCREEN", "3DSPACE", "2DSPACE", "2DIMAGE")
            stroke.points.add(len(frames[i][j])) # add 4 points
            for l in range(0, len(frames[i][j])):
                x = 0.0
                y = 0.0
                z = 0.0
                pressure = 1.0
                strength = 1.0
                if useScaleAndOffset == True:
                    x = (frames[i][j][l][0] * globalScale.x) + globalOffset.x
                    y = (frames[i][j][l][2] * globalScale.y) + globalOffset.y
                    z = (frames[i][j][l][1] * globalScale.z) + globalOffset.z
                else:
                    x = frames[i][j][l][0]
                    y = frames[i][j][l][2]
                    z = frames[i][j][l][1]
                #~
                createPoint(stroke, l, (x, y, z), pressure, strength)

def gmlParser(filepath=None, splitStrokes=False, sequenceAnim=False):
    globalScale = (0.01, -0.01, 0.01)
    screenBounds = (1, 1, 1)
    up = (0, 1, 0)
    useTime = True
    minStrokeLength=3
    #~
    masterLayerList = []
    tree = etree.parse(filepath)
    root = tree.getroot()
    #~
    strokeCounter = 0
    pointCounter = 0
    gp = getActiveGp()
    fps = getSceneFps()
    start, end = getStartEnd()
    #~
    tag = root.find("tag")
    origLayerName = "GML_Tag"
    layer = newLayer(origLayerName)
    masterLayerList.append(layer)
    #~
    header = tag.find("header")
    #~
    environment = header.find("environment")
    if not environment:
        environment = tag.find("environment")
    if environment:
        upEl = environment.find("up")
        if (upEl):
            up = (float(upEl.find("x").text), float(upEl.find("y").text), float(upEl.find("z").text))
        screenBoundsEl = environment.find("screenBounds")
        if (screenBoundsEl):
            sbX = float(screenBoundsEl.find("x").text)
            sbY = float(screenBoundsEl.find("y").text)
            sbZ = 1.0
            try:
                sbZ = float(screenBoundsEl.find("z").text)
            except:
                pass
            screenBounds = (sbX, sbY, sbZ)
    globalScale = (globalScale[0] * screenBounds[0], globalScale[1] * screenBounds[1], globalScale[2] * screenBounds[2])
    #~
    drawing = tag.find("drawing")
    strokesEl = drawing.findall("stroke")
    strokeCounter += len(strokesEl)
    strokes = []
    for stroke in strokesEl:
        #~
        pts = stroke.findall("pt")
        pointCounter += len(pts)
        gmlPoints = []
        for pt in pts:
            x = float(pt.find("x").text) * globalScale[0]
            y = float(pt.find("y").text) * globalScale[1]
            z = 0.0
            try:
                z = float(pt.find("z").text) * globalScale[2]
            except:
                pass
            time = 0.0
            try:
                time = float(pt.find("time").text)
            except:
                pass
            gmlPoints.append((x,y,z,time))
        gmlPoints = sorted(gmlPoints, key=itemgetter(3)) # sort by time
        strokes.append(gmlPoints)
        #~
        if (sequenceAnim == True):
            for gmlPoint in gmlPoints:
                frameNum = int(gmlPoint[3] * float(fps))
                print(str(gmlPoint[3]))
                goToFrame(frameNum)
                try:
                    layer.frames.new(frameNum)
                except:
                    pass
            for frame in layer.frames:
                goToFrame(frame.frame_number)
                layer.active_frame = frame
                #~
                if (splitStrokes==False):
                    for stroke in strokes:
                        lastPoint = stroke[len(stroke)-1]
                        if (int(lastPoint[3] * float(fps)) <= frame.frame_number):
                            if (len(stroke) >= minStrokeLength):
                                drawPoints(stroke, frame=frame, layer=layer)
                #~
                gpPoints = []
                for gmlPoint in gmlPoints:
                    if (int(gmlPoint[3] * float(fps)) <= frame.frame_number):
                        gpPoints.append(gmlPoint)
                print("...Drawing into frame " + str(frame.frame_number) + " with " + str(len(gpPoints)) + " points.")
                if (len(gpPoints) >= minStrokeLength):
                    if (splitStrokes==True):
                        layer = newLayer(layer.info)
                        masterLayerList.append(layer)
                    drawPoints(points=gpPoints, frame=frame, layer=layer)
    # cleanup
    #~
    if (sequenceAnim == False):
        start, end = getStartEnd()
        layer = getActiveLayer()
        frame = None
        try:
            frame = layer.frames.new(start)
        except:
            frame = getActiveFrame()
        for i, stroke in enumerate(strokes):
            if (splitStrokes == True and i > 0):
                layer = newLayer(layer.info)
                masterLayerList.append(layer)
                try:
                    frame = layer.frames.new(start)
                except:
                    frame = getActiveFrame()
            drawPoints(stroke, frame=frame, layer=layer)
    #~
    if (splitStrokes==True):
        for layer in masterLayerList:
            if (len(layer.frames)<1):
                deleteLayer(layer.info)
        cleanCounter = 1
        for layer in masterLayerList:
            for gpLayer in gp.layers:
                if (layer.info==gpLayer.info):
                    gpLayer.info = origLayerName + "_" + str(cleanCounter)
                    cleanCounter += 1
                    break
    print("* * * * * * * * * * * * * * *")
    print("strokes: " + str(strokeCounter) + "   points: " + str(pointCounter))

def writeGml(filepath=None, make2d=False):
    timeCounter = 0
    timeIncrement = 0.01
    #~
    globalScale = (1, 1, 1)
    globalOffset = (0, 0, 0)
    useScaleAndOffset = True
    #numPlaces = 7
    #roundValues = True
    #~
    frame = getActiveFrame()
    strokes = frame.strokes
    allX = []
    allY = []
    allZ = []
    for stroke in strokes:
        for point in stroke.points:
            coord = point.co
            allX.append(coord[0])
            allY.append(coord[1])
            allZ.append(coord[2])
    allX.sort()
    allY.sort()
    allZ.sort()
    maxPoint = (allX[len(allX)-1], allY[len(allY)-1], allZ[len(allZ)-1])
    minPoint = (allX[0], allY[0], allZ[0])
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    sg = gmlHeader((480, 320, 18)) # Fat Tag default
    for stroke in strokes:
        coords = []
        for point in stroke.points:
            coord = point.co
            x = remap(coord[0], minPoint[0], maxPoint[0], 0, 1)
            y = remap(coord[1], minPoint[1], maxPoint[1], 0, 1)
            z = remap(coord[2], minPoint[2], maxPoint[2], 0, 1)
            coords.append((x, 1.0 - z, y))
        returnString, timeCounter = gmlStroke(coords, timeCounter, timeIncrement)
        sg += returnString
    sg += gmlFooter()
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    writeTextFile(filepath, sg)
    return {'FINISHED'}

def gmlHeader(dim=(1024,1024,1024)):
    s = "<gml spec=\"0.1b\">\r"
    s += "\t<tag>\r"
    s += "\t\t<header>\r"
    s += "\t\t\t<client>\r"
    s += "\t\t\t\t<name>Latk</name>\r"
    s += "\t\t\t</client>\r"
    s += "\t\t\t<environment>\r"
    s += "\t\t\t\t<up>\r"
    s += "\t\t\t\t\t<x>0</x>\r"
    s += "\t\t\t\t\t<y>1</y>\r"
    s += "\t\t\t\t\t<z>0</z>\r"
    s += "\t\t\t\t</up>\r"
    s += "\t\t\t\t<screenBounds>\r"
    s += "\t\t\t\t\t<x>" + str(dim[0]) + "</x>\r"
    s += "\t\t\t\t\t<y>" + str(dim[1]) + "</y>\r"
    s += "\t\t\t\t\t<z>" + str(dim[2]) + "</z>\r"
    s += "\t\t\t\t</screenBounds>\r"
    s += "\t\t\t</environment>\r"
    s += "\t\t</header>\r"
    s += "\t\t<drawing>\r"
    return s

def gmlFooter():
    s = "\t\t</drawing>\r"
    s += "\t</tag>\r"
    s += "</gml>\r"
    return s

def gmlStroke(points, timeCounter, timeIncrement):
    s = "\t\t\t<stroke>\r"
    for point in points:
        returnString, timeCounter = gmlPoint(point, timeCounter, timeIncrement)
        s += returnString
    s += "\t\t\t</stroke>\r"
    return s, timeCounter

def gmlPoint(point, timeCounter, timeIncrement):
    s = "\t\t\t\t<pt>\r"
    s += "\t\t\t\t\t<x>" + str(point[0]) + "</x>\r"
    s += "\t\t\t\t\t<y>" + str(point[1]) + "</y>\r"
    s += "\t\t\t\t\t<z>" + str(point[2]) + "</z>\r"
    s += "\t\t\t\t\t<time>" + str(timeCounter) + "</time>\r"
    s += "\t\t\t\t</pt>\r"
    timeCounter += timeIncrement
    return s, timeCounter

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

def smilParser(filepath=None):
    if not filepath:
        filepath = "C:\\Users\\nick\\Desktop\\error.svg"
    globalScale = (0.01, 0.01, 0.01)
    screenBounds = (1, 1, 1)
    up = (0, 1, 0)
    useTime = True
    minStrokeLength=3
    #~
    masterLayerList = []
    tree = etree.parse(filepath)
    root = tree.getroot()
    #~
    strokeCounter = 0
    pointCounter = 0
    gp = getActiveGp()
    fps = getSceneFps()
    start, end = getStartEnd()
    #~
    paths = getAllTags("path", tree)
    for path in paths:
        strokes = path.attrib["d"].split('M')
        for stroke in strokes:
            pointsList = []
            pointsRaw = stroke.split(" ")
            for pointRaw in pointsRaw:
                pointRaw = pointRaw.split("Q")[0]
                pointRaw = pointRaw.replace("Z", "")
                pointRaw = pointRaw.replace("L", "")
                try:
                    pointsList.append(float(pointRaw))
                except:
                    pass
            if (len(pointsList) % 2 != 0):
                pointsList.pop()
            points = []
            for i in range(0, len(pointsList), 2):
                point = (pointsList[i] * globalScale[0], pointsList[i+1] * globalScale[1], 0)
                points.append(point)
            if (len(points) > 1):
                drawPoints(points)

def getAllTags(name=None, xml=None):
    returns = []
    for node in xml.iter():
        if (node.tag.split('}')[1] == name):
            returns.append(node)
    return returns

'''
def writePointCloud(filepath=None, strokes=None):
    if not filepath:
        filepath = getFilePath()
    if not strokes:
        strokes = getSelectedStrokes()
        if not strokes:
            frame = getActiveFrame()
            strokes = frame.strokes
    lines = []
    for stroke in strokes:
        for point in stroke.points:
            x = str(point.co[0])
            y = str(point.co[1])
            z = str(point.co[2])
            lines.append(x + ", " + y + ", " + z + "\n")
    writeTextFile(name=name, lines=lines)
'''

def importAsc(filepath=None, strokeLength=1):
    globalScale = Vector((1, 1, 1))
    globalOffset = Vector((0, 0, 0))
    useScaleAndOffset = True
    #numPlaces = 7
    #roundValues = True

    with open(filepath) as data_file: 
        data = data_file.readlines()

    allPoints = []
    allPressures = []
    colors = []
    colorIs255 = False
    for line in data:
        pointRaw = line.split(",")
        point = (float(pointRaw[0]), float(pointRaw[1]), float(pointRaw[2]))
        allPoints.append(point)
        
        color = None
        pressure = 1.0
        
        if (len(pointRaw) == 4):
            pressure = float(pointRaw[3])
        elif (len(pointRaw) == 6):
            color = (float(pointRaw[3]), float(pointRaw[4]), float(pointRaw[5]))
        elif(len(pointRaw) > 6):
            pressure = float(pointRaw[3])
            color = (float(pointRaw[4]), float(pointRaw[5]), float(pointRaw[6]))

        if (colorIs255 == False and color != None and color[0] + color[1] + color[2] > 3.1):
                colorIs255 = True
        elif (colorIs255 == True):
            color = (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)

        allPressures.append(pressure)
        colors.append(color)

    gp = getActiveGp()
    layer = gp.layers.new("ASC_layer", set_active=True)
    start, end = getStartEnd()
    frame = getActiveFrame()
    if not frame:
        frame = layer.frames.new(start)

    for i in range(0, len(allPoints), strokeLength):
        color = colors[i]
        if (color != None):
            createColor(color)
        stroke = frame.strokes.new(getActiveColor().name)
        stroke.draw_mode = "3DSPACE"
        stroke.points.add(strokeLength)

        for j in range(0, strokeLength):
            x = allPoints[i+j][0]
            y = allPoints[i+j][2]
            z = allPoints[i+j][1]
            pressure = allPressures[i+j]
            strength = 1.0
            if useScaleAndOffset == True:
                x = (x * globalScale.x) + globalOffset.x
                y = (y * globalScale.y) + globalOffset.y
                z = (z * globalScale.z) + globalOffset.z
            createPoint(stroke, j, (x, y, z), pressure, strength)

def exportAsc(filepath=None):
    ascData = []
    gp = getActiveGp()
    palette = getActivePalette()
    for layer in gp.layers:
        for frame in layer.frames:
            for stroke in frame.strokes:
                color = palette.colors[stroke.colorname].color
                for point in stroke.points:
                    coord = point.co
                    x = coord[0]
                    y = coord[2]
                    z = coord[1]
                    pressure = point.pressure
                    r = color[0]
                    g = color[1]
                    b = color[2]
                    ascData.append(str(x) + "," + str(y) + "," + str(z) + "," + str(pressure) + "," + str(r) + "," + str(g) + "," + str(b)) 

    writeTextFile(filepath, "\n".join(ascData))

def importSculptrVr(filepath=None, strokeLength=1, scale=0.01, startLine=1):
    globalScale = Vector((scale, scale, scale))
    globalOffset = Vector((0, 0, 0))
    useScaleAndOffset = True
    #numPlaces = 7
    #roundValues = True

    with open(filepath) as data_file: 
        data = data_file.readlines()

    allPoints = []
    allPressures = []
    colors = []
    colorIs255 = False
    for i in range(startLine, len(data)):
        pointRaw = data[i].split(",")
        point = (float(pointRaw[0]), float(pointRaw[1]), float(pointRaw[2]))
        allPoints.append(point)
        
        color = None
        pressure = 1.0
        
        '''
        if (len(pointRaw) == 4):
            pressure = float(pointRaw[3])
        elif (len(pointRaw) == 6):
            color = (float(pointRaw[3]), float(pointRaw[4]), float(pointRaw[5]))
        elif(len(pointRaw) > 6):
            pressure = float(pointRaw[3])
        '''
        color = (float(pointRaw[4]), float(pointRaw[5]), float(pointRaw[6]))

        if (colorIs255 == False and color != None and color[0] + color[1] + color[2] > 3.1):
                colorIs255 = True
        elif (colorIs255 == True):
            color = (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)

        allPressures.append(pressure)
        colors.append(color)

    gp = getActiveGp()
    layer = gp.layers.new("ASC_layer", set_active=True)
    start, end = getStartEnd()
    frame = getActiveFrame()
    if not frame:
        frame = layer.frames.new(start)

    for i in range(0, len(allPoints), strokeLength):
        color = colors[i]
        if (color != None):
            createColor(color)
        stroke = frame.strokes.new(getActiveColor().name)
        stroke.draw_mode = "3DSPACE"
        stroke.points.add(strokeLength)

        for j in range(0, strokeLength):
            x = allPoints[i+j][0]
            y = allPoints[i+j][1]
            z = allPoints[i+j][2]
            pressure = allPressures[i+j]
            strength = 1.0
            if useScaleAndOffset == True:
                x = (x * globalScale.x) + globalOffset.x
                y = (y * globalScale.y) + globalOffset.y
                z = (z * globalScale.z) + globalOffset.z
            createPoint(stroke, j, (x, y, z), pressure, strength)

def exportSculptrVrCsv(filepath=None, strokes=None, sphereRadius=10, octreeSize=7, vol_scale=0.33, mtl_val=255, file_format="sphere"):
    file_format = file_format.lower()
    #~
    if (sphereRadius < 0.01):
        sphereRadius = 0.01
    #~
    if (octreeSize < 0):
        octreeSize = 0
    if (octreeSize > 19):
        octreeSize = 19
    if (mtl_val != 127 and mtl_val != 254 and mtl_val != 255):
        mtl_val = 255
    #~
    if not filepath:
        filepath = getFilePath()
    if not strokes:
        strokes = getSelectedStrokes()
        if not strokes:
            frame = getActiveFrame()
            strokes = frame.strokes
    #~
    csvData = []

    allX = []
    allY = []
    allZ = []
    for stroke in strokes:
        for point in stroke.points:
            coord = point.co
            allX.append(coord[0])
            allY.append(coord[1])
            allZ.append(coord[2])
    allX.sort()
    allY.sort()
    allZ.sort()

    leastValArray = [ allX[0], allY[0], allZ[0] ]
    mostValArray = [ allX[len(allX)-1], allY[len(allY)-1], allZ[len(allZ)-1] ]
    leastValArray.sort()
    mostValArray.sort()
    leastVal = leastValArray[0]
    mostVal = mostValArray[2]
    valRange = mostVal - leastVal

    xRange = (allX[len(allX)-1] - allX[0]) / valRange
    yRange = (allY[len(allY)-1] - allY[0]) / valRange
    zRange = (allZ[len(allZ)-1] - allZ[0]) / valRange

    minVal = -1500.0
    maxVal = 1500.0
    if (file_format == "legacy"):
        minVal, maxVal = getSculptrVrVolRes(0)
    elif (file_format == "single"):
        minVal, maxVal = getSculptrVrVolRes(octreeSize)

    minValX = minVal * xRange * vol_scale
    minValY = minVal * yRange * vol_scale
    minValZ = minVal * zRange * vol_scale
    maxValX = maxVal * xRange * vol_scale
    maxValY = maxVal * yRange * vol_scale
    maxValZ = maxVal * zRange * vol_scale

    for stroke in strokes:
        for point in stroke.points:
            # might do this here if we want to use variable pressure later
            #minVal, maxVal = getSculptrVrVolRes(octreeSize)

            color = stroke.color.color
            r = int(color[0] * 255)
            g = int(color[1] * 255)
            b = int(color[2] * 255)
            coord = point.co
            if (file_format == "sphere"):
                x = remap(coord[0], allX[0], allX[len(allX)-1], minValX, maxValX)
                y = remap(coord[1], allY[0], allY[len(allY)-1], minValY, maxValY)
                z = remap(coord[2], allZ[0], allZ[len(allZ)-1], minValZ, maxValZ)
                pressure = remap(point.pressure, 0.0, 1.0, sphereRadius/100.0, sphereRadius)
                if (pressure < 0.01):
                	pressure = 0.01
                csvData.append([x, y, z, pressure, r, g, b])
            else:
                x = remapInt(coord[0], allX[0], allX[len(allX)-1], int(minValX), int(maxValX))
                y = remapInt(coord[1], allY[0], allY[len(allY)-1], int(minValY), int(maxValY))
                z = remapInt(coord[2], allZ[0], allZ[len(allZ)-1], int(minValZ), int(maxValZ))
                csvData.append([x, y, z, octreeSize, r, g, b, mtl_val])

    #csvData = sorted(csvDataInt, key=lambda x: x[1])
    #csvData = sorted(csvDataInt, key=lambda x: x[2])
    finalData = []
    finalData.append("# SculptrVR: " + file_format + " #")
    if (file_format == "legacy"): # xyz rgb
        for data in csvData:
            finalData.append(str(data[0]) + "," + str(data[1]) + "," + str(data[2]) + "," + str(data[4]) + "," + str(data[5]) + "," + str(data[6]))
    elif(file_format == "single"): # xyz octree_size rgb mtl_val
        for data in csvData:
            finalData.append(str(data[0]) + "," + str(data[1]) + "," + str(data[2]) + "," + str(data[3]) + "," + str(data[4]) + "," + str(data[5]) + "," + str(data[6]) + "," + str(data[7]))
    elif(file_format == "sphere"): # xyz radius rgb
        for data in csvData:
            finalData.append(str(data[0]) + "," + str(data[1]) + "," + str(data[2]) + "," + str(data[3]) + "," + str(data[4]) + "," + str(data[5]) + "," + str(data[6]))

    writeTextFile(filepath, "\n".join(finalData))

def getSculptrVrVolRes(val):
    vol_res = 19 - val
    minVal = -pow(2, vol_res)
    maxVal = pow(2, vol_res)-1
    return minVal, maxVal

# ~ ~ ~

def tiltBrushJson_Grouper(n, iterable, fillvalue=None):
  """grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"""
  args = [iter(iterable)] * n
  return zip_longest(fillvalue=fillvalue, *args)

def tiltBrushJson_DecodeData(obj, dataType="v"):
    '''    
    VERTEX_ATTRIBUTES = [
        # Attribute name, type code
        ('v',  'f', None),
        ('n',  'f', 3),
        ('uv0','f', None),
        ('uv1','f', None),
        ('c',  'I', 1),
        ('t',  'f', 4),
    ]
    '''
    if (dataType=="v" or dataType=="n" or dataType=="t"):
        typeChar = "f"
    elif (dataType=="c"):
        typeChar = "I"

    num_verts = 1
    empty = None
    data_grouped = []
    
    data_bytes = base64.b64decode(obj)
    fmt = "<%d%c" % (len(data_bytes) / 4, typeChar)
    data_words = struct.unpack(fmt, data_bytes)
    
    if (dataType=="v" or dataType=="n"):
        num_verts = len(data_words) / 3
    elif (dataType=="t"):
        num_verts = len(data_words) / 4

    if (len(data_words) % num_verts != 0):
        return None
    else: 
        stride_words = int(len(data_words) / num_verts)
        if stride_words > 1:
            data_grouped = list(tiltBrushJson_Grouper(stride_words, data_words))
        else:
            data_grouped = list(data_words)

        if (dataType == "c"):
            for i in range(0, len(data_grouped)):
                data_grouped[i] = rgbIntToTuple(data_grouped[i][0], normalized=True)

        return(data_grouped)

def importTiltBrush(filepath=None, vertSkip=1):
    globalScale = Vector((1, 1, 1))
    globalOffset = Vector((0, 0, 0))
    useScaleAndOffset = True
    gp = getActiveGp()
    palette = getActivePalette()    

    filename = os.path.split(filepath)[1].split(".")
    filetype = filename[len(filename)-1].lower()
    if (filetype == "tilt" or filetype == "zip"): # Tilt Brush binary file with original stroke data
        t = Tilt(filepath)
        #~
        layer = gp.layers.new("TiltBrush", set_active=True)
        frame = layer.frames.new(1)
        #~
        for tstroke in t.sketch.strokes:
            strokeColor = (0,0,0)
            pointGroup = []
            try:
                strokeColor = (tstroke.brush_color[0], tstroke.brush_color[1], tstroke.brush_color[2])
            except:
                pass
            for i in range(0, len(tstroke.controlpoints), vertSkip):
                controlpoint = tstroke.controlpoints[i]
                last_controlpoint = tstroke.controlpoints[i-1]
                x = 0.0
                y = 0.0
                z = 0.0
                #~
                point = controlpoint.position
                last_point = last_controlpoint.position
                if (i==0 or point != last_point): # try to prevent duplicate points
                    pressure = 1.0
                    strength = 1.0
                    try:
                        pressure = controlpoint.extension[0]
                        # TODO strength?
                    except:
                        pass
                    #~
                    x = point[0]
                    y = point[2]
                    z = point[1]
                    if useScaleAndOffset == True:
                        x = (x * globalScale[0]) + globalOffset[0]
                        y = (y * globalScale[1]) + globalOffset[1]
                        z = (z * globalScale[2]) + globalOffset[2]
                    pointGroup.append((x, y, z, pressure, strength))
                    #~
            createColor(strokeColor)
            stroke = frame.strokes.new(getActiveColor().name)
            stroke.points.add(len(pointGroup)) # add 4 points
            stroke.draw_mode = "3DSPACE" # either of ("SCREEN", "3DSPACE", "2DSPACE", "2DIMAGE")  
            for l, point in enumerate(pointGroup):
                createPoint(stroke, l, (point[0], point[1], point[2]), point[3], point[4])
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        """Prints out some rough information about the strokes.
        Pass a tiltbrush.tilt.Sketch instance."""
        '''
        cooky, version, unused = sketch.header[0:3]
        '''
        #output += 'Cooky:0x%08x    Version:%s    Unused:%s    Extra:(%d bytes)' % (
            #cooky, version, unused, len(sketch.additional_header))
        '''
        if len(sketch.strokes):
            stroke = sketch.strokes[0]    # choose one representative one
            def extension_names(lookup):
                # lookup is a dict mapping name -> idx
                extensions = sorted(lookup.items(), key=lambda (n,i): i)
                return ', '.join(name for (name, idx) in extensions)
            #output += "Stroke Ext: %s" % extension_names(stroke.stroke_ext_lookup)
            #if len(stroke.controlpoints):
                #output += "CPoint Ext: %s" % extension_names(stroke.cp_ext_lookup)
        '''
        '''
        for (i, stroke) in enumerate(sketch.strokes):
            #output += "%3d: " % i,
            output += dump_stroke(stroke)
        '''
    else: # Tilt Brush JSON export file, not original stroke data
        pressure = 1.0
        strength = 1.0
        #~
        with open(filepath) as data_file: 
            data = json.load(data_file)
        #~
        layer = gp.layers.new("TiltBrush", set_active=True)
        frame = layer.frames.new(1)
        #~
        for strokeJson in data["strokes"]:
            strokeColor = (0,0,0)
            try:
                colorGroup = tiltBrushJson_DecodeData(strokeJson["c"], "c")
                strokeColor = (colorGroup[0][0], colorGroup[0][1], colorGroup[0][2])
            except:
                pass
            #~
            vertsFailed = False
            vertGroup = []
            pointGroup = []
            try:
                vertGroup = tiltBrushJson_DecodeData(strokeJson["v"], "v")
            except:
                vertsFailed = True

            if (vertsFailed==False and len(vertGroup) > 0):
                for j in range(0, len(vertGroup), vertSkip):
                    if (j==0 or vertGroup[j] != vertGroup[j-1]): # try to prevent duplicate points
                        vert = vertGroup[j]
                        if (vert[0] == 0 and vert[1] == 0 and vert[2] == 0):
                            pass
                        else:
                            try:
                                x = -vert[0]
                                y = vert[2]
                                z = vert[1]
                                if (useScaleAndOffset == True):
                                    x = (x * globalScale.x) + globalOffset.x
                                    y = (y * globalScale.y) + globalOffset.y
                                    z = (z * globalScale.z) + globalOffset.z
                                pointGroup.append((x, y, z, pressure, strength))
                            except:
                                pass

            if (vertsFailed==False):
                createColor(strokeColor)
                stroke = frame.strokes.new(getActiveColor().name)
                stroke.points.add(len(pointGroup)) # add 4 points
                stroke.draw_mode = "3DSPACE" # either of ("SCREEN", "3DSPACE", "2DSPACE", "2DIMAGE")  
                for l, point in enumerate(pointGroup):
                    createPoint(stroke, l, (point[0], point[1], point[2]), point[3], point[4])
           
    return {'FINISHED'}

# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

# 4 of 10. MATERIALS / RENDERING

def cleanUvs(target=None, limit=1):
    if not target:
        target = s()
    for obj in target:
        try:
            uvs = obj.data.uv_textures
            while (len(uvs) > limit):
                uvs.remove(uvs[len(uvs)-1])
        except:
            pass

def createMaterial(target=None, name="NewMaterial", unique=True):
    if not target:
        target = s()
    if (unique == False):
        mat = bpy.data.materials.new(name=name)
    for obj in target:
        try:
            if (len(obj.data.materials) < 1):
                if (unique==True):
                    mat = bpy.data.materials.new(name=name)
                obj.data.materials.append(mat)
        except:
            pass

def deleteMaterial(target=None):
    if not target:
        target = s()
    for obj in target:
        try:
            setActiveObject(obj)
            bpy.ops.object.material_slot_remove()
        except:
               pass

# http://blender.stackexchange.com/questions/17738/how-to-uv-unwrap-object-with-python
def planarUvProject():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    override = {'area': area, 'region': region, 'edit_object': bpy.context.edit_object}
                    bpy.ops.uv.smart_project(override)
                    
def colorVertexCyclesMat(obj, vertName="Cd"):
    # http://blender.stackexchange.com/questions/6084/use-python-to-add-multiple-colors-to-a-nurbs-curve
    # http://blender.stackexchange.com/questions/5668/add-nodes-to-material-with-python
    # this will fail if you don't have Cycles Render enabled
    mesh = obj.data 
    #~    
    obj.active_material = bpy.data.materials.new('material')
    obj.active_material.use_vertex_color_paint = True
    #~
    obj.active_material.use_nodes = True
    nodes = obj.active_material.node_tree.nodes
    material_output = nodes.get('Diffuse BSDF')
    nodeAttr = nodes.new("ShaderNodeAttribute")
    nodeAttr.attribute_name = vertName
    obj.active_material.node_tree.links.new(material_output.inputs[0], nodeAttr.outputs[0])

def colorVertexAlt(obj, vert, color=[1,0,0]):
    mesh = obj.data 
    scn = bpy.context.scene
    # check if our mesh already has Vertex Colors, and if not add some... (first we need to make sure it's the active object)
    scn.objects.active = obj
    obj.select = True
    if len(mesh.vertex_colors) == 0:
        bpy.ops.mesh.vertex_color_add()
    i=0
    for poly in mesh.polygons:
        for vert_side in poly.loop_indices:
            global_vert_num = poly.vertices[vert_side-min(poly.loop_indices)] 
            if vert == global_vert_num:
                mesh.vertex_colors[0].data[i].color = color
            i += 1

def getVertexColor(mesh=None, vert=0):
    if not mesh:
        mesh = ss().data
    if (len(mesh.vertex_colors)) == 0:
        return None
    i=0
    for poly in mesh.polygons:
        for vert_side in poly.loop_indices:
            if (vert == poly.vertices[vert_side-min(poly.loop_indices)]):
                return mesh.vertex_colors[0].data[i].color
            i += 1   
    return None 

def colorVertices(obj, color=(1,0,0), makeMaterial=False, colorName="rgba"):
    # start in object mode
    mesh = obj.data
    #~
    if not mesh.vertex_colors:
        mesh.vertex_colors.new(colorName) 
    #~
    color_layer = mesh.vertex_colors.active  
    #~
    i = 0
    for poly in mesh.polygons:
        for idx in poly.loop_indices:
            try:
                color_layer.data[i].color = (color[0], color[1], color[2], 1) # future-proofing 2.79a
            except:
                color_layer.data[i].color = color # 2.79 and earlier
            i += 1
    #~
    if (makeMaterial==True):
        colorVertexCyclesMat(obj)

def togglePoints(strokes=None):
    layer = getActiveLayer()
    if not strokes:
        strokes = getSelectedStrokes()
        if not strokes:
            strokes = getAllStrokes()
    #~
    for stroke in strokes:
        stroke.color.use_volumetric_strokes = True
    layer.line_change = 1

def createMtlPalette(numPlaces=5, numReps = 1):
    palette = None
    removeUnusedMtl()
    for h in range(0, numReps):
        palette = []
        # 1-3. Creating palette of all materials
        for mtl in bpy.data.materials:
            foundNewMtl = True
            for palMtl in palette:
                if (compareTuple(getDiffuseColor(mtl), getDiffuseColor(palMtl), numPlaces=numPlaces)==True):
                    foundNewMtl = False
                    break
            if (foundNewMtl==True):
                palette.append(mtl)
        for i, mtl in enumerate(palette):
            mtl.name = "Palette_" + str(i+1)
        # 2-3. Matching palette colors for all objects
        for obj in bpy.context.scene.objects:
            try:
                for i, mtl in enumerate(obj.data.materials):
                    for palMtl in palette:
                        if (compareTuple(getDiffuseColor(mtl), getDiffuseColor(palMtl), numPlaces=numPlaces)==True):
                            obj.data.materials[i] = palMtl
            except:
                pass
        # 3-3. Removing unused materials
        removeUnusedMtl()
    #~
    print ("Created palette of " + str(len(palette)) + " materials.")
    return palette

def removeUnusedMtl():
    # http://blender.stackexchange.com/questions/5300/how-can-i-remove-all-unused-materials-from-a-file/35637#35637
    for mtl in bpy.data.materials:
        if not mtl.users:
            bpy.data.materials.remove(mtl)

# https://blender.stackexchange.com/questions/5668/add-nodes-to-material-with-python
def texAllMtl(filePath="D://Asset Collections//Images//Element maps 2K//Plaster_maps//plaster_wall_distressed_04_normal.jpg", strength=1.0, colorData=False):
    for mtl in bpy.data.materials:
        mtl.use_nodes = True
        nodes = mtl.node_tree.nodes
        links = mtl.node_tree.links
        #~
        shaderNode = nodes["Diffuse BSDF"]
        texNode = None
        mapNode = None
        try:
            texNode = nodes["Image Texture"]
        except:
            texNode = nodes.new("ShaderNodeTexImage")
        try:
            mapNode = nodes["Normal Map"]
        except:
            mapNode = nodes.new("ShaderNodeNormalMap")
        #~
        links.new(texNode.outputs[0], mapNode.inputs[1])
        links.new(mapNode.outputs[0], shaderNode.inputs[2])
        #~
        texNode.image = bpy.data.images.load(filePath)
        if (colorData==True):
            texNode.color_space = "COLOR"
        else:
            texNode.color_space = "NONE"
        mapNode.inputs[0].default_value = strength
        #~
        mapNode.location = [shaderNode.location.x - 250, shaderNode.location.y]
        texNode.location = [mapNode.location.x - 250, shaderNode.location.y]

# TODO handle multiple materials on one mesh
def searchMtl(color=None, name="latk"):
    returns = []
    if not color:
        color = getActiveColor().color
    curves = matchName(name)
    for curve in curves:
        if (compareTuple(curve.data.materials[0].diffuse_color, color)):
            returns.append(curve)
    return returns

# TODO handle multiple materials on one mesh
def changeMtl(color=(1,1,0), searchColor=None, name="latk"):
    if not searchColor:
        searchColor = getActiveColor().color       
    curves = searchMtl(color=searchColor, name=name)
    print("changed: " + str(curves))
    for curve in curves:
        curve.data.materials[0].diffuse_color = color

def consolidateMtl():
    palette = getActivePalette()
    for color in palette.colors:
        matchMat = None
        for obj in bpy.context.scene.objects:
            try:
                for i, mat in enumerate(obj.data.materials):
                    if (compareTuple((color.color[0],color.color[1],color.color[2]), getDiffuseColor(mat)) == True):
                        if (matchMat == None):
                            matchMat = mat
                        else:
                            obj.data.materials[i] = matchMat
            except:
                pass

# old version, can't handle multiple materials on one mesh
def consolidateMtlAlt(name="latk"):
    palette = getActivePalette()
    for color in palette.colors:
        curves = searchMtl(color=color.color, name=name)
        for i in range(1, len(curves)):
            curves[i].data.materials[0] = curves[0].data.materials[0]

def getActiveMtl():
    return bpy.context.scene.objects.active.data.materials[bpy.context.scene.objects.active.active_material_index]

def getMtlColor(node="diffuse", mtl=None):
    if not mtl:
        mtl = getActiveMtl()
    try:
        if (node.lower() == "emission"):
            color = mtl.node_tree.nodes["Emission"].inputs["Color"].default_value
            return (color[0], color[1], color[2])
        elif (node.lower() == "principled"):
            color = mtl.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
            return (color[0], color[1], color[2])
        elif (node.lower() == "gltf"):
            color = mtl.node_tree.nodes["Group"].inputs["BaseColor"].default_value
            return (color[0], color[1], color[2])
        else:
            color = mtl.node_tree.nodes["Diffuse BSDF"].inputs["Color"].default_value
            return (color[0], color[1], color[2])
    except:
        return None

# assumes that we're starting with diffuse shader, the default
def setMtlShader(shader="diffuse", mtl=None):
    # https://blender.stackexchange.com/questions/23436/control-cycles-material-nodes-and-material-properties-in-python
    if not mtl:
        mtl = getActiveMtl()
    col = getUnknownColor(mtl)
    if not col:
        return None
    #~
    # https://blender.stackexchange.com/questions/33189/python-script-attribute-error-while-using-node-editor
    # clear all nodes to start clean
    mtl.use_nodes = True
    nodes = mtl.node_tree.nodes
    for node in nodes:
        nodes.remove(node)
    #~
    destNode = None
    #~
    # https://docs.blender.org/api/blender_python_api_2_78_0/bpy.types.html
    # create emission node
    if (shader.lower()=="emission"):
        destNode = nodes.new(type="ShaderNodeEmission")
        destNode.inputs[0].default_value = (col[0], col[1], col[2], 1) # RGBA
        #destNode.inputs[1].default_value = 5.0 # strength
    elif (shader.lower()=="principled"):
        destNode = nodes.new(type="ShaderNodeBsdfPrincipled")
        destNode.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1) # RGBA
        destNode.inputs["Subsurface Color"].default_value = (col[0], col[1], col[2], 1) # RGBA
    elif (shader.lower()=="gltf"):
        group = bpy.data.node_groups["glTF Metallic Roughness"]
        destNode = mtl.node_tree.nodes.new("ShaderNodeGroup")
        destNode.node_tree = group
        destNode.inputs["BaseColor"].default_value = (col[0], col[1], col[2], 1) # RGBA
        destNode.inputs["BaseColorFactor"].default_value = (col[0], col[1], col[2], 1) # RGBA
        destNode.inputs["MetallicRoughness"].default_value = (col[0], col[1], col[2], 1) # RGBA
        destNode.inputs["MetallicFactor"].default_value = 0.5
        destNode.inputs["RoughnessFactor"].default_value = 0.5
    else:
        destNode = nodes.new(type="ShaderNodeBsdfDiffuse")
        destNode.inputs[0].default_value = (col[0], col[1], col[2], 1) # RGBA
    #~
    destNode.location = 0,0
    #~
    # create output node
    node_output = nodes.new(type="ShaderNodeOutputMaterial")   
    node_output.location = 400,0
    #~
    # link nodes
    links = mtl.node_tree.links
    link = links.new(destNode.outputs[0], node_output.inputs[0])
    #~
    return mtl

def setAllMtlShader(shader="principled"):
    for mtl in bpy.data.materials:
        setMtlShader(shader, mtl)

def getDiffuseColor(mtl=None):
    if not mtl:
        mtl = getActiveMtl()
    col = getMtlColor("diffuse", mtl)
    if (col==None):
        col = mtl.diffuse_color
    return col

def getEmissionColor(mtl=None):
    if not mtl:
        mtl = getActiveMtl()
    return getMtlColor("emission", mtl)

def getPrincipledColor(mtl=None):
    if not mtl:
        mtl = getActiveMtl()
    return getMtlColor("principled", mtl)

def getGltfColor(mtl=None):
    if not mtl:
        mtl = getActiveMtl()
    return getMtlColor("gltf", mtl)

def getUnknownColor(mtl=None):
    if not mtl:
        mtl = getActiveMtl()
    col = None
    if (col == None):
        col = getEmissionColor(mtl)
    if (col == None):
        col = getPrincipledColor(mtl)
    if (col == None):
        col = getGltfColor(mtl)
    if (col == None):
        col = getDiffuseColor(mtl)
    return col

def getColorExplorer(target=None, vert=0, images=None):
    if not target:
        target = ss()
    mesh = target.data
    col = None
    try:
        uv_first = mesh.uv_layers.active.data[vert].uv
        pixelRaw = getPixelFromUvArray(images[target.active_material.node_tree.nodes["Image Texture"].image.name], uv_first[0], uv_first[1])                
        col = (pixelRaw[0], pixelRaw[1], pixelRaw[2])  
    except:
        pass
    if (col == None):
        col = getVertexColor(mesh, vert)
    if (col == None):
        try:
            col = getUnknownColor(mesh.materials[0])
        except:
            pass
    if (col == None):
        col = getActiveColor().color
    return col


# is this obsolete now that all materials are linked by color value?
def makeEmissionMtl():
    mtl = getActiveMtl()
    color = getEmissionColor()
    for obj in bpy.context.scene.objects:
        try:
            for j in range(0, len(obj.data.materials)):
                destColor = getDiffuseColor(obj.data.materials[j])
                if (compareTuple(destColor, color) == True):
                    obj.data.materials[j] = mtl
        except:
            pass

#~ ~ ~ ~ ~ ~ ~ ~
# pixel / uv methods
#~ ~ ~ ~ ~ ~ ~ ~

# http://blender.stackexchange.com/questions/49341/how-to-get-the-uv-corresponding-to-a-vertex-via-the-python-api
# https://blenderartists.org/forum/archive/index.php/t-195230.html
# https://developer.blender.org/T28211
# http://blenderscripting.blogspot.ca/2012/08/adjusting-image-pixels-walkthrough.html
# https://www.blender.org/forum/viewtopic.php?t=25804
# https://docs.blender.org/api/blender_python_api_2_63_2/bmesh.html
# http://blender.stackexchange.com/questions/1311/how-can-i-get-vertex-positions-from-a-mesh

# TODO is this for bmesh only?
def uv_from_vert_first(uv_layer, v):
    for l in v.link_loops:
        uv_data = l[uv_layer]
        return uv_data.uv
    return None


def uv_from_vert_average(uv_layer, v):
    uv_average = Vector((0.0, 0.0))
    total = 0.0
    for loop in v.link_loops:
        uv_average += loop[uv_layer].uv
        total += 1.0
    #~
    if total != 0.0:
        return uv_average * (1.0 / total)
    else:
        return None

# Example using the functions above
'''
def testUvs():
    obj = bpy.context.scene.objects.active #edit_object
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me) #from_edit_mesh(me)
    #~
    images = getUvImages()
    #~
    uv_layer = bm.loops.layers.uv.active
    #~
    for v in bm.verts:
        uv_first = uv_from_vert_first(uv_layer, v)
        uv_average = uv_from_vert_average(uv_layer, v)
        print("Vertex: %r, uv_first=%r, uv_average=%r" % (v, uv_first, uv_average))
        #~
        pixel = getPixelFromUvArray(images[obj.active_material.texture_slots[0].texture.image.name], uv_first[0], uv_first[1])
        print("Pixel: " + str(pixel))
'''

def getUvImages():
    obj = bpy.context.scene.objects.active
    uv_images = {}
    #~
    #for uv_tex in obdata.uv_textures.active.data:
    for tex in obj.active_material.texture_slots:
        try:
            uv_tex = tex.texture
            if (uv_tex.image and
                uv_tex.image.name not in uv_images and
                uv_tex.image.pixels):

                uv_images[uv_tex.image.name] = (
                    uv_tex.image.size[0],
                    uv_tex.image.size[1],
                    uv_tex.image.pixels[:]
                    # Accessing pixels directly is far too slow.
                    # Copied to new array for massive performance-gain.
                )
        except:
            pass
    if (len(uv_images) < 1):
        try:
            uv_tex = obj.active_material.node_tree.nodes["Image Texture"]
            if (uv_tex.image and
                uv_tex.image.name not in uv_images and
                uv_tex.image.pixels):

                uv_images[uv_tex.image.name] = (
                    uv_tex.image.size[0],
                    uv_tex.image.size[1],
                    uv_tex.image.pixels[:]
                    # Accessing pixels directly is far too slow.
                    # Copied to new array for massive performance-gain.
                )
        except:
            pass
    #~
    return uv_images

def getPixelFromImage(img, xPos, yPos):
    imgWidth = int(img.size[0])
    r = img.pixels[4 * (xPos + imgWidth * yPos) + 0]
    g = img.pixels[4 * (xPos + imgWidth * yPos) + 1]
    b = img.pixels[4 * (xPos + imgWidth * yPos) + 2]
    a = img.pixels[4 * (xPos + imgWidth * yPos) + 3]
    return [r, g, b, a]

def getPixelFromUv(img, u, v):
    imgWidth = int(img.size[0])
    imgHeight = int(img.size[1])
    pixel_x = int(u * imgWidth)
    pixel_y = int(v * imgHeight)
    return getPixelFromImage(img, pixel_x, pixel_y)

# *** these methods are much faster but don't work in all contexts
def getPixelFromImageArray(img, xPos, yPos):
    imgWidth = int(img[0]) #img.size[0]
    #r = img.pixels[4 * (xPos + imgWidth * yPos) + 0]
    r = img[2][4 * (xPos + imgWidth * yPos) + 0]
    g = img[2][4 * (xPos + imgWidth * yPos) + 1]
    b = img[2][4 * (xPos + imgWidth * yPos) + 2]
    a = img[2][4 * (xPos + imgWidth * yPos) + 3]
    return [r, g, b, a]

def getPixelFromUvArray(img, u, v):
    imgWidth = int(img[0]) #img.size[0]
    imgHeight = int(img[1]) #img.size[1]
    pixel_x = int(u * imgWidth)
    pixel_y = int(v * imgHeight)
    return getPixelFromImageArray(img, pixel_x, pixel_y)

# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

# 5 of 10. MESHES / GEOMETRY

def simpleClean(target=None):
    if not target:
        target = s()
    for obj in target:
        setObjectMode()
        setActiveObject(obj)
        setEditMode()
        bpy.ops.mesh.face_make_planar()
        bpy.ops.mesh.tris_convert_to_quads()
        bpy.ops.mesh.delete_loose()

def getVerts(target=None, useWorldSpace=True, useColors=True, useBmesh=False, useModifiers=True):
    if not target:
        target = bpy.context.scene.objects.active
    mesh = None
    if (useModifiers==True):
        mesh = target.to_mesh(scene=bpy.context.scene, apply_modifiers=True, settings='PREVIEW')
    else:
        mesh = target.data
    mat = target.matrix_world
    #~
    if (useBmesh==True):
        bm = bmesh.new()
        bm.from_mesh(mesh)
        return bm.verts
    else:
        verts = []
        #~
        for face in mesh.polygons:
            for idx in face.vertices:
                pointsFace = []
                pointsFace.append(mesh.vertices[idx].co)
            point = Vector((0,0,0))
            for vert in pointsFace:
                point += vert
            point /= len(pointsFace)
            if (useWorldSpace == True):
                point = mat * point
            verts.append((point.x, point.z, point.y))
        #~
        if (useColors==True):
            colors = []
            try:
                for i in range(0, len(mesh.vertex_colors[0].data), int(len(mesh.vertex_colors[0].data) / len(verts))):
                    colors.append(mesh.vertex_colors[0].data[i].color)
                return verts, colors
            except:
                return verts, None
        else:
            return verts

def countVerts(target=None):
    if not target:
        target = bpy.context.scene.objects.active
    return len(getVerts(target)[0])

# TODO decimate does not work, context error
def bakeAllCurvesToMesh(_decimate=0.1):
    start, end = getStartEnd()
    target = matchName("latk_")
    for obj in target:
        applyModifiers(obj)   

def joinObjects(target=None, center=False):
    if not target:
        target = s()
    #~
    bpy.ops.object.select_all(action='DESELECT') 
    target[0].select = True
    bpy.context.scene.objects.active = target[0]
    for i in range(1, len(target)):
        target[i].select = True
    #~
    bpy.ops.object.join()
    #~
    for i in range(1, len(target)):
        try:
            scn.objects.unlink(target[i])
        except:
            pass
    #~
    gc.collect()
    if (center==True):
        centerOrigin(target[0])
    return target[0]

'''
161013
Tried an all-baking approach but it didn't seem to work. 
Going back to parenting with baking for single objects, less elegant but seems to be OK
'''
# https://gist.github.com/pcote/1307658
# http://blender.stackexchange.com/questions/7578/extruding-multiple-curves-at-once
# http://blender.stackexchange.com/questions/24694/query-grease-pencil-strokes-from-python
# https://wiki.blender.org/index.php/Dev:Py/Scripts/Cookbook/Code_snippets/Materials_and_textures
# http://blender.stackexchange.com/questions/58676/add-modifier-to-selected-and-another-to-active-object
# http://blenderscripting.blogspot.ca/2011/05/blender-25-python-bezier-from-list-of.html
# http://blender.stackexchange.com/questions/6750/poly-bezier-curve-from-a-list-of-coordinates
# http://blender.stackexchange.com/questions/7047/apply-transforms-to-linked-objects

def assembleMesh(export=False, createPalette=True):
    origFileName = getFileName()
    masterUrlList = []
    masterGroupList = []
    #~
    gp = getActiveGp()
    palette = getActivePalette()
    #~
    for b, layer in enumerate(gp.layers):
        url = origFileName + "_layer_" + layer.info
        masterGroupList.append(getLayerInfo(layer))
        masterUrlList.append(url)
    #~
    readyToSave = True
    for i in range(0, len(masterUrlList)):
        if (export==True):
            dn()
        #~
        try:
            importGroup(getFilePath() + masterUrlList[i] + ".blend", masterGroupList[i], winDir=True)
            print("Imported group " + masterGroupList[i] + ", " + str(i+1) + " of " + str(len(masterGroupList)))
        except:
            readyToSave = False
            print("Error importing group " + masterGroupList[i] + ", " + str(i+1) + " of " + str(len(masterGroupList)))
    #~
    if (createPalette==True):
        createMtlPalette()
    #~
    consolidateGroups()
    #~
    if (readyToSave==True):
        if (export==True):
            exportForUnity()
            print(origFileName + " FBXs exported.")
        else:
            saveFile(origFileName + "_ASSEMBLY")
            print(origFileName + "_ASSEMBLY.blend" + " saved.")
    else:
        if (export==True):
            exportForUnity()
            print(origFileName + " FBXs exported but some groups were missing.")
        else:
            saveFile(origFileName + "_ASSEMBLY")
            print(origFileName + "_ASSEMBLY.blend" + " was saved but some groups were missing.")

def gpMesh(_thickness=0.1, _resolution=1, _bevelResolution=0, _bakeMesh=True, _decimate = 0.1, _curveType="nurbs", _useColors=True, _saveLayers=False, _singleFrame=False, _vertexColors=True, _vertexColorName="rgba", _animateFrames=True, _remesh="none", _consolidateMtl=True, _caps=True, _joinMesh=True, _uvStroke=True, _uvFill=True, _usePressure=True, _la=None):
    if (_joinMesh==True or _remesh != "none"):
        _bakeMesh=True
    #~
    if (_saveLayers==True):
        dn()
    #~    
    origFileName = getFileName()
    masterUrlList = []
    masterGroupList = []
    masterParentList = []
    #~
    totalStrokes = str(len(getAllStrokes()))
    totalCounter = 0
    start, end = getStartEnd()
    #~
    gp = getActiveGp()
    palette = getActivePalette()
    #~
    capsObj = None
    if (_caps==True):
        if (_curveType=="nurbs"):
            bpy.ops.curve.primitive_nurbs_circle_add(radius=_thickness)
        else:
            bpy.ops.curve.primitive_bezier_circle_add(radius=_thickness)
        capsObj = ss()
        capsObj.name="caps_ob"
        capsObj.data.resolution_u = _bevelResolution
    #~
    if not _la:
        _la = fromGpToLatk()
    #~
    for b, layer in enumerate(gp.layers):
        url = origFileName + "_layer_" + layer.info
        if (layer.lock==False):
            rangeStart = 0
            rangeEnd = len(layer.frames)
            if (_singleFrame==True):
                rangeStart = getActiveFrameNum(layer)
                rangeEnd = rangeStart + 1
            for c in range(rangeStart, rangeEnd):
                print("\n" + "*** gp layer " + str(b+1) + " of " + str(len(gp.layers)) + " | gp frame " + str(c+1) + " of " + str(rangeEnd) + " ***")
                frameList = []
                for stroke in _la.layers[b].frames[c].strokes:
                    origParent = None
                    if (layer.parent):
                        origParent = layer.parent
                        layer.parent = None
                        masterParentList.append(origParent.name)
                    else:
                        masterParentList.append(None)
                    #~
                    coords = stroke.getCoords()
                    pressures = stroke.getPressures()
                    #~
                    latk_ob = makeCurve(name="latk_" + getLayerInfo(layer) + "_" + str(_la.layers[b].frames[c].frame_number), coords=coords, pressures=pressures, curveType=_curveType, resolution=_resolution, thickness=_thickness, bevelResolution=_bevelResolution, parent=layer.parent, capsObj=capsObj, useUvs=_uvStroke, usePressure=_usePressure)
                    #centerOrigin(latk_ob)
                    strokeColor = (0.5,0.5,0.5)
                    if (_useColors==True):
                        strokeColor = stroke.color #palette.colors[stroke.colorname].color
                    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
                    mat = None
                    if (_consolidateMtl==False):
                       mat = bpy.data.materials.new("new_mtl")
                       mat.diffuse_color = strokeColor
                    else:
                        for oldMat in bpy.data.materials:
                            if (compareTuple(strokeColor, oldMat.diffuse_color) == True):
                                mat = oldMat
                                break
                        if (mat == None):
                            mat = bpy.data.materials.new("share_mtl")
                            mat.diffuse_color = strokeColor  
                    latk_ob.data.materials.append(mat)
                    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
                    #~   
                    bpy.context.scene.objects.active = latk_ob
                    #~
                    if (_bakeMesh==True): #or _remesh==True):
                        bpy.ops.object.modifier_add(type='DECIMATE')
                        bpy.context.object.modifiers["Decimate"].ratio = _decimate     
                        meshObj = applyModifiers(latk_ob)
                        #~
                        if (_remesh != "none"):
                            meshObj = remesher(meshObj, mode=_remesh)
                        #~
                        # + + + + + + +
                        if (stroke.fill_alpha > 0.001):
                            fill_ob = createFill(stroke.points, useUvs=_uvFill)
                            joinObjects([meshObj, fill_ob])
                        # + + + + + + +
                        #~
                        if (_vertexColors==True):
                            colorVertices(meshObj, strokeColor, colorName = _vertexColorName) 
                        #~ 
                        frameList.append(meshObj) 
                    else:
                        frameList.append(latk_ob)    
                    # * * * * * * * * * * * * * *
                    if (origParent != None):
                        makeParent([frameList[len(frameList)-1], origParent])
                        layer.parent = origParent
                    # * * * * * * * * * * * * * *
                    bpy.ops.object.select_all(action='DESELECT')
                #~
                for i in range(0, len(frameList)):
                    totalCounter += 1
                    print(frameList[i].name + " | " + str(totalCounter) + " of " + totalStrokes + " total")
                    if (_animateFrames==True):
                        hideFrame(frameList[i], start, True)
                        #~
                        for j in range(start, end):
                            if (j == layer.frames[c].frame_number):
                                hideFrame(frameList[i], j, False)
                                keyTransform(frameList[i], j)
                            elif (c < len(layer.frames)-1 and j > layer.frames[c].frame_number and j < layer.frames[c+1].frame_number):
                                hideFrame(frameList[i], j, False)
                            elif (c != len(layer.frames)-1):
                                hideFrame(frameList[i], j, True)
                #~
                if (_joinMesh==True): 
                    target = matchName("latk_" + getLayerInfo(layer))
                    for i in range(start, end):
                        strokesToJoin = []
                        if (i == layer.frames[c].frame_number):
                            goToFrame(i)
                            for j in range(0, len(target)):
                                if (target[j].hide==False):
                                    strokesToJoin.append(target[j])
                        if (len(strokesToJoin) > 1):
                            print("~ ~ ~ ~ ~ ~ ~ ~ ~")
                            print("* joining " + str(len(strokesToJoin))  + " strokes")
                            joinObjects(strokesToJoin)
                            print("~ ~ ~ ~ ~ ~ ~ ~ ~")
            #~
            '''
            # TODO bug changes location for layers of only one frame
            deselect()
            target = matchName("latk_" + getLayerInfo(layer))
            for tt in range(0, len(target)):
                target[tt].select = True            
            centerOrigin(target[tt])
            '''
            #~
            if (_saveLayers==True):
                deselect()
                target = matchName("latk_" + getLayerInfo(layer))
                for tt in range(0, len(target)):
                    target[tt].select = True
                print("* baking")
                # * * * * *
                bakeParentToChildByName("latk_" + getLayerInfo(layer))
                # * * * * *
                print("~ ~ ~ ~ ~ ~ ~ ~ ~")
                #~
                makeGroup(getLayerInfo(layer))
                #~
                masterGroupList.append(getLayerInfo(layer))
                #~
                print("saving to " + url)
                saveFile(url)
                #~
                masterUrlList.append(url)
                #~
                gpMeshCleanup(getLayerInfo(layer))
    #~
    if (_caps==True):
        try:
            delete(capsObj)
        except:
            pass
    #~
    if (_saveLayers==True):
        openFile(origFileName)
        for i in range(0, len(masterUrlList)):
            importGroup(getFilePath() + masterUrlList[i] + ".blend", masterGroupList[i], winDir=True)
        #~
        if (_consolidateMtl==True):
            createMtlPalette()
        #~
        consolidateGroups()
        #~
        saveFile(origFileName + "_ASSEMBLY")

'''
def gpMeshOrig(_thickness=0.1, _resolution=1, _bevelResolution=0, _bakeMesh=True, _decimate = 0.1, _curveType="nurbs", _useColors=True, _saveLayers=False, _singleFrame=False, _vertexColors=True, _vertexColorName="rgba", _animateFrames=True, _remesh="none", _consolidateMtl=True, _caps=True, _joinMesh=True, _uvStroke=True, _uvFill=True, _usePressure=True):
    if (_joinMesh==True or _remesh != "none"):
        _bakeMesh=True
    #~
    if (_saveLayers==True):
        dn()
    #~    
    origFileName = getFileName()
    masterUrlList = []
    masterGroupList = []
    masterParentList = []
    #~
    totalStrokes = str(len(getAllStrokes()))
    totalCounter = 0
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end + 1
    #~
    gp = getActiveGp()
    palette = getActivePalette()
    #~
    capsObj = None
    if (_caps==True):
        if (_curveType=="nurbs"):
            bpy.ops.curve.primitive_nurbs_circle_add(radius=_thickness)
        else:
            bpy.ops.curve.primitive_bezier_circle_add(radius=_thickness)
        capsObj = ss()
        capsObj.name="caps_ob"
        capsObj.data.resolution_u = _bevelResolution
    #~
    for b, layer in enumerate(gp.layers):
        url = origFileName + "_layer_" + layer.info
        if (layer.lock==False):
            rangeStart = 0
            rangeEnd = len(layer.frames)
            if (_singleFrame==True):
                rangeStart = getActiveFrameNum(layer)
                rangeEnd = rangeStart + 1
            for c in range(rangeStart, rangeEnd):
                print("\n" + "*** gp layer " + str(b+1) + " of " + str(len(gp.layers)) + " | gp frame " + str(c+1) + " of " + str(rangeEnd) + " ***")
                frameList = []
                for stroke in layer.frames[c].strokes:
                    origParent = None
                    if (layer.parent):
                        origParent = layer.parent
                        layer.parent = None
                        masterParentList.append(origParent.name)
                    else:
                        masterParentList.append(None)
                    #~
                    stroke_points = stroke.points
                    coords = [ (point.co.x, point.co.y, point.co.z) for point in stroke_points ]
                    pressures = [ point.pressure for point in stroke_points ]
                    #~
                    latk_ob = makeCurve(name="latk_" + getLayerInfo(layer) + "_" + str(layer.frames[c].frame_number), coords=coords, pressures=pressures, curveType=_curveType, resolution=_resolution, thickness=_thickness, bevelResolution=_bevelResolution, parent=layer.parent, capsObj=capsObj, useUvs=_uvStroke, usePressure=_usePressure)
                    #centerOrigin(latk_ob)
                    strokeColor = (0.5,0.5,0.5)
                    if (_useColors==True):
                        strokeColor = palette.colors[stroke.colorname].color
                    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
                    mat = None
                    if (_consolidateMtl==False):
                       mat = bpy.data.materials.new("new_mtl")
                       mat.diffuse_color = strokeColor
                    else:
                        for oldMat in bpy.data.materials:
                            if (compareTuple(strokeColor, oldMat.diffuse_color) == True):
                                mat = oldMat
                                break
                        if (mat == None):
                            mat = bpy.data.materials.new("share_mtl")
                            mat.diffuse_color = strokeColor  
                    latk_ob.data.materials.append(mat)
                    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ 
                    #~   
                    bpy.context.scene.objects.active = latk_ob
                    #~
                    if (_bakeMesh==True): #or _remesh==True):
                        bpy.ops.object.modifier_add(type='DECIMATE')
                        bpy.context.object.modifiers["Decimate"].ratio = _decimate     
                        meshObj = applyModifiers(latk_ob)
                        #~
                        if (_remesh != "none"):
                            meshObj = remesher(meshObj, mode=_remesh)
                        #~
                        # + + + + + + +
                        if (palette.colors[stroke.colorname].fill_alpha > 0.001):
                            fill_ob = createFill(stroke.points, useUvs=_uvFill)
                            joinObjects([meshObj, fill_ob])
                        # + + + + + + +
                        #~
                        if (_vertexColors==True):
                            colorVertices(meshObj, strokeColor, colorName = _vertexColorName) 
                        #~ 
                        frameList.append(meshObj) 
                    else:
                        frameList.append(latk_ob)    
                    # * * * * * * * * * * * * * *
                    if (origParent != None):
                        makeParent([frameList[len(frameList)-1], origParent])
                        layer.parent = origParent
                    # * * * * * * * * * * * * * *
                    bpy.ops.object.select_all(action='DESELECT')
                #~
                for i in range(0, len(frameList)):
                    totalCounter += 1
                    print(frameList[i].name + " | " + str(totalCounter) + " of " + totalStrokes + " total")
                    if (_animateFrames==True):
                        hideFrame(frameList[i], start, True)
                        #~
                        for j in range(start, end):
                            if (j == layer.frames[c].frame_number):
                                hideFrame(frameList[i], j, False)
                                keyTransform(frameList[i], j)
                            elif (c < len(layer.frames)-1 and j > layer.frames[c].frame_number and j < layer.frames[c+1].frame_number):
                                hideFrame(frameList[i], j, False)
                            elif (c != len(layer.frames)-1):
                                hideFrame(frameList[i], j, True)
                #~
                if (_joinMesh==True): 
                    target = matchName("latk_" + getLayerInfo(layer))
                    for i in range(start, end):
                        strokesToJoin = []
                        if (i == layer.frames[c].frame_number):
                            goToFrame(i)
                            for j in range(0, len(target)):
                                if (target[j].hide==False):
                                    strokesToJoin.append(target[j])
                        if (len(strokesToJoin) > 1):
                            print("~ ~ ~ ~ ~ ~ ~ ~ ~")
                            print("* joining " + str(len(strokesToJoin))  + " strokes")
                            joinObjects(strokesToJoin)
                            print("~ ~ ~ ~ ~ ~ ~ ~ ~")
            #~
            if (_saveLayers==True):
                deselect()
                target = matchName("latk_" + getLayerInfo(layer))
                for tt in range(0, len(target)):
                    target[tt].select = True
                print("* baking")
                # * * * * *
                bakeParentToChildByName("latk_" + getLayerInfo(layer))
                # * * * * *
                print("~ ~ ~ ~ ~ ~ ~ ~ ~")
                #~
                makeGroup(getLayerInfo(layer))
                #~
                masterGroupList.append(getLayerInfo(layer))
                #~
                print("saving to " + url)
                saveFile(url)
                #~
                masterUrlList.append(url)
                #~
                gpMeshCleanup(getLayerInfo(layer))
    #~
    if (_caps==True):
        try:
            delete(capsObj)
        except:
            pass
    #~
    if (_saveLayers==True):
        openFile(origFileName)
        for i in range(0, len(masterUrlList)):
            importGroup(getFilePath() + masterUrlList[i] + ".blend", masterGroupList[i], winDir=True)
        #~
        if (_consolidateMtl==True):
            createMtlPalette()
        #~
        consolidateGroups()
        #~
        saveFile(origFileName + "_ASSEMBLY")
'''

def gpMeshQ(val = 0.1):
    gpMesh(_decimate=val, _saveLayers=True)

def applySolidify(target=None, _extrude=1):
    if not target:
        target = s()
    for obj in target:
        setActiveObject(obj)
        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers["Solidify"].thickness = _extrude * 2
        bpy.context.object.modifiers["Solidify"].offset = 0

def applySubdiv(target=None, _subd=1):
    if (_subd > 0):
        if not target:
            target = s()
        for obj in target:
            setActiveObject(obj)
            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.context.object.modifiers["Subsurf"].levels = _subd
            bpy.context.object.modifiers["Subsurf"].render_levels = _subd
            try:
                bpy.context.object.modifiers["Subsurf"].use_opensubdiv = 1 # GPU if supported
            except:
                pass

def gpMeshCleanup(target):
    gc.collect()
    removeGroup(target, allGroups=True)
    dn()

def decimateAndBake(target=None, _decimate=0.1):
    if not target:
        target = s()
    for obj in target:
        if (obj.type == "CURVE"):
            setActiveObject(obj)
            bpy.ops.object.modifier_add(type='DECIMATE')
            bpy.context.object.modifiers["Decimate"].ratio = _decimate     
            meshObj = applyModifiers(obj)

def remesher(obj, bake=True, mode="blocks", octree=6, threshold=0.0001, smoothShade=False, removeDisconnected=False):
        bpy.context.scene.objects.active = obj
        bpy.ops.object.modifier_add(type="REMESH")
        bpy.context.object.modifiers["Remesh"].mode = mode.upper() #sharp, smooth, blocks
        bpy.context.object.modifiers["Remesh"].octree_depth = octree
        bpy.context.object.modifiers["Remesh"].use_smooth_shade = int(smoothShade)
        bpy.context.object.modifiers["Remesh"].use_remove_disconnected = int(removeDisconnected)
        bpy.context.object.modifiers["Remesh"].threshold = threshold
        if (bake==True):
            return applyModifiers(obj)     
        else:
            return obj

# context error
def decimator(target=None, ratio=0.1, bake=True):
    if not target:
        target = ss()
    bpy.context.scene.objects.active = target
    bpy.ops.object.modifier_add(type='DECIMATE')
    bpy.context.object.modifiers["Decimate"].ratio = ratio     
    if (bake == True):
        return applyModifiers(target)
    else:
        return target

# https://blender.stackexchange.com/questions/45004/how-to-make-boolean-modifiers-with-python
def booleanMod(target=None, op="union"):
    if not target:
        target=s()
    for i in range(1, len(target)):
            bpy.context.scene.objects.active = target[i]
            bpy.ops.object.modifier_add(type="BOOLEAN")
            bpy.context.object.modifiers["Boolean"].operation = op.upper()
            bpy.context.object.modifiers["Boolean"].object = target[i-1]
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            delete(target[i-1])
    lastObj = target[len(target)-1]
    lastObj.select = True
    return lastObj

def subsurfMod(target=None):
    if not target:
        target=s()
    returns = []
    for obj in target:
        bpy.context.scene.objects.active = obj
        bpy.ops.object.modifier_add(type="SUBSURF")
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Subsurf")
        returns.append(obj)
    return returns

def smoothMod(target=None):
    if not target:
        target=s()
    returns = []
    for obj in target:
        bpy.context.scene.objects.active = obj
        bpy.ops.object.modifier_add(type="SMOOTH")
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Smooth")
        returns.append(obj)
    return returns

def decimateMod(target=None, _decimate=0.1):
    if not target:
        target = s()
    returns = []
    for obj in target:
        bpy.context.scene.objects.active = obj
        bpy.ops.object.modifier_add(type='DECIMATE')
        bpy.context.object.modifiers["Decimate"].ratio = _decimate     
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")
        returns.append(obj)
    return returns

def polyCube(pos=(0,0,0), scale=(1,1,1), rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add()
    cube = s()[0]
    cube.location = pos
    cube.scale=scale
    cube.rotation_euler=rot
    return cube

def applyModifiers(obj):
    mesh = obj.to_mesh(scene = bpy.context.scene, apply_modifiers=True, settings = 'PREVIEW')
    meshObj = bpy.data.objects.new(obj.name + "_mesh", mesh)
    bpy.context.scene.objects.link(meshObj)
    bpy.context.scene.objects.active = meshObj
    meshObj.matrix_world = obj.matrix_world
    delete(obj)
    return meshObj

def getGeometryCenter(obj):
    sumWCoord = [0,0,0]
    numbVert = 0
    if obj.type == 'MESH':
        for vert in obj.data.vertices:
            wmtx = obj.matrix_world
            worldCoord = vert.co * wmtx
            sumWCoord[0] += worldCoord[0]
            sumWCoord[1] += worldCoord[1]
            sumWCoord[2] += worldCoord[2]
            numbVert += 1
        sumWCoord[0] = sumWCoord[0]/numbVert
        sumWCoord[1] = sumWCoord[1]/numbVert
        sumWCoord[2] = sumWCoord[2]/numbVert
    return sumWCoord

def getActiveCurvePoints():
    target = s()[0]
    if (target.data.splines[0].type=="BEZIER"):
        return target.data.splines.active.bezier_points
    else:
        return target.data.splines.active.points      

def curveToStroke(target=None):
    if not target:
        target = s()[0]
    for spline in target.data.splines:
        points = []
        splinePoints = None
        if (spline.type=="BEZIER"):
            splinePoints = spline.bezier_points
        else:
            splinePoints = spline.points
        for point in splinePoints:
            points.append((point.co[0], point.co[2], point.co[1]))
        try:
            drawPoints(points)
        except:
            pass

def centerOriginAlt(obj):
    oldLoc = obj.location
    newLoc = getGeometryCenter(obj)
    for vert in obj.data.vertices:
        vert.co[0] -= newLoc[0] - oldLoc[0]
        vert.co[1] -= newLoc[1] - oldLoc[1]
        vert.co[2] -= newLoc[2] - oldLoc[2]
    obj.location = newLoc

def centerOrigin(target=None):
    if not target:
        target = ss()
    deselect()
    target.select = True
    setActiveObject(target)
    bpy.ops.object.origin_set(type = 'ORIGIN_GEOMETRY')
    deselect()

def setOrigin(target, point):
    bpy.context.scene.objects.active = target
    bpy.context.scene.cursor_location = point
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    #bpy.context.scene.update()

def writeOnMesh(step=1, name="latk"):
    target = matchName(name)
    for i in range (0, len(target), step):
        if (i > len(target)-1):
            i = len(target)-1
        for j in range(i, (i+1)*step):
            if (j > len(target)-1):
                j = len(target)-1
            hideFrame(target[j], 0, True)
            hideFrame(target[j], len(target)-j, False)

def meshToGp(obj=None, strokeLength=1, strokeGaps=10.0, shuffleOdds=1.0, spreadPoints=0.1):
    if not obj:
        obj = ss()
    mesh = obj.data
    mat = obj.matrix_world
    #~
    gp = getActiveGp()
    layer = getActiveLayer()
    if not layer:
        layer = gp.layers.new(name="meshToGp")
    frame = getActiveFrame()
    if not frame or frame.frame_number != currentFrame():
        frame = layer.frames.new(currentFrame())
    #~
    images = None
    try:
        images = getUvImages()
    except:
        pass
    #~
    allPoints, allColors = getVerts(target=obj, useWorldSpace=True, useColors=True, useBmesh=False)
    #~
    pointSeqsToAdd = []
    colorsToAdd = []
    for i in range(0, len(allPoints), strokeLength):
        color = None
        if not images:
            try:
                color = allColors[i]
            except:
                color = getColorExplorer(obj, i)
        else:
            try:
                color = getColorExplorer(obj, i, images)
            except:
                color = getColorExplorer(obj, i)
        colorsToAdd.append(color)
        #~
        pointSeq = []
        for j in range(0, strokeLength):
            #point = allPoints[i]
            try:
                point = allPoints[i+j]
                if (len(pointSeq) == 0 or getDistance(pointSeq[len(pointSeq)-1], point) < strokeGaps):
                    pointSeq.append(point)
            except:
                break
        if (len(pointSeq) > 0): 
            pointSeqsToAdd.append(pointSeq)
    for i, pointSeq in enumerate(pointSeqsToAdd):
        color = colorsToAdd[i]
        createColor(color)
        stroke = frame.strokes.new(getActiveColor().name)
        stroke.draw_mode = "3DSPACE"
        stroke.points.add(len(pointSeq))

        if (random.random() < shuffleOdds):
            random.shuffle(pointSeq)

        for j, point in enumerate(pointSeq):    
            x = point[0] + (random.random() * 2.0 * spreadPoints) - spreadPoints
            y = point[2] + (random.random() * 2.0 * spreadPoints) - spreadPoints
            z = point[1] + (random.random() * 2.0 * spreadPoints) - spreadPoints
            pressure = 1.0
            strength = 1.0
            createPoint(stroke, j, (x, y, z), pressure, strength)
    '''
    points = []
    allPointsCounter = 0
    for i in range(1, len(allPoints)):
        if (len(points) < 2 or getDistance(allPoints[allPointsCounter], allPoints[i]) < vertexHitbox):
            points.append(allPoints[i])
        else:
            #col = createAndMatchColorPalette(getColorExplorer(obj, i), 16, 2)
            col = getColorExplorer(obj, i)
            try:
                drawPoints(points=points, color=col)
                allPointsCounter = i
                points = []
            except:
                points.append(allPoints[i])
    '''

def makeCurve(coords, pressures=None, resolution=2, thickness=0.1, bevelResolution=1, curveType="bezier", parent=None, capsObj=None, name="latk_ob", useUvs=True, usePressure=True):
    # http://blender.stackexchange.com/questions/12201/bezier-spline-with-python-adds-unwanted-point
    # http://blender.stackexchange.com/questions/6750/poly-bezier-curve-from-a-list-of-coordinates
    # create the curve datablock
    # https://svn.blender.org/svnroot/bf-extensions/trunk/py/scripts/addons/curve_simplify.py
    '''
    options = [
        0,    # smooth mode
        0,    # output mode
        0,    # k_thresh
        5,    # pointsNr
        0.0,  # error
        5,    # degreeOut
        0.0]  # dis_error
    if (simplify==True):
        coordsToVec = []
        for coord in coords:
            coordsToVec.append(Vector(coord))
        coordsToVec = simplypoly(coordsToVec, options)
        print(coordsToVec)
        #coords = []
        #for vec in coordsToVec:
            #coords.append((vec.x, vec.y, vec.z))
    '''
    #~
    # adding an extra point to the beginning helps with smoothing
    try:
    	coords.insert(0, coords[0])
    	pressures.insert(0, pressures[0])
    except:
    	pass

    curveData = bpy.data.curves.new('latk', type='CURVE')
    curveData.dimensions = '3D'
    curveData.fill_mode = 'FULL'
    curveData.resolution_u = resolution
    curveData.bevel_depth = thickness
    curveData.bevel_resolution = bevelResolution
    #~
    if (capsObj != None):
        curveData.bevel_object = capsObj
        curveData.use_fill_caps = True
    #~
    # map coords to spline
    curveType=curveType.upper()
    polyline = curveData.splines.new(curveType)
    #~
    if (curveType=="NURBS"):
        polyline.points.add(len(coords))#-1)
        for i, coord in enumerate(coords):
            x,y,z = coord
            polyline.points[i].co = (x, y, z, 1) 
            if (pressures != None and usePressure==True):
                polyline.points[i].radius = pressures[i]   
    elif (curveType=="BEZIER"):
        polyline.bezier_points.add(len(coords))#-1)
        #polyline.bezier_points.foreach_set("co", unpack_list(coords))
        for i, coord in enumerate(coords):
            polyline.bezier_points[i].co = coord   
            if (pressures != None and usePressure==True):
                polyline.bezier_points[i].radius = pressures[i]  
            polyline.bezier_points[i].handle_left = polyline.bezier_points[i].handle_right = polyline.bezier_points[i].co
    #~
    # create object
    latk_ob = bpy.data.objects.new(name, curveData)
    #~
    # attach to scene and validate context
    scn = bpy.context.scene
    scn.objects.link(latk_ob)
    scn.objects.active = latk_ob
    latk_ob.select = True
    if (useUvs==True):
        latk_ob.data.use_uv_as_generated = True
    return latk_ob

def createMesh(name, origin, verts, faces):
    bpy.ops.object.add(
        type='MESH', 
        enter_editmode=False,
        location=origin)
    ob = bpy.context.object
    ob.name = name
    ob.show_name = True
    me = ob.data
    me.name = name +'Mesh'
    #~
    # Create mesh from given verts, faces.
    me.from_pydata(verts, [], faces)
    # Update mesh with new data
    me.update()    
    # Set object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob

# crashes        
def makeGpCurve(_type="PATH"):
    original_type = bpy.context.area.type
    print("Current context: " + original_type)
    bpy.context.area.type = "VIEW_3D"
    #~
    # strokes, points, frame
    bpy.ops.gpencil.convert(type=_type)
    #~
    #bpy.context.area.type = "CONSOLE"
    bpy.context.area.type = original_type

def cubesToVerts(target=None, cubeScale=0.25, posScale=0.01):
    if not target:
        target = ss()
    verts = target.data.vertices
    mat = target.matrix_world
    for vert in verts:
        bpy.ops.mesh.primitive_cube_add()
        cube = ss()
        cube.scale = (cubeScale * target.scale[0],cubeScale * target.scale[1],cubeScale * target.scale[2])
        cube.rotation_euler = target.rotation_euler
        cube.location = mat * vert.co

def randomMetaballs():
    # http://blenderscripting.blogspot.com/2012/09/tripping-metaballs-python.html
    scene = bpy.context.scene
    #~
    # add metaball object
    mball = bpy.data.metaballs.new("MetaBall")
    obj = bpy.data.objects.new("MetaBallObject", mball)
    scene.objects.link(obj)
    #~
    mball.resolution = 0.2   # View resolution
    mball.render_resolution = 0.02
    #~
    for i in range(20):
        coordinate = tuple(random.uniform(-4,4) for i in range(3))
        element = mball.elements.new()
        element.co = coordinate
        element.radius = 2.0

def createFill(inputVerts, useUvs=False):
    verts = []
    #~
    # Create mesh 
    me = bpy.data.meshes.new("myMesh") 
    #~
    # Create object
    ob = bpy.data.objects.new("myObject", me) 
    #~
    #ob.location = origin
    ob.show_name = True
    #~
    # Link object to scene
    bpy.context.scene.objects.link(ob)
    #~
    # Get a BMesh representation
    bm = bmesh.new() # create an empty BMesh
    bm.from_mesh(me) # fill it in from a Mesh
    #~
    # Hot to create vertices
    for i in range(0, len(inputVerts)):
        vert = bm.verts.new((inputVerts[i].co[0], inputVerts[i].co[1], inputVerts[i].co[2]))
        verts.append(vert)
    '''
    vertex1 = bm.verts.new( (0.0, 0.0, 3.0) )
    vertex2 = bm.verts.new( (2.0, 0.0, 3.0) )
    vertex3 = bm.verts.new( (2.0, 2.0, 3.0) )
    vertex4 = bm.verts.new( (0.0, 2.0, 3.0) )
    '''
    #~
    # Initialize the index values of this sequence.
    bm.verts.index_update()
    #~
    # How to create edges 
    '''
    bm.edges.new( (vertex1, vertex2) )
    bm.edges.new( (vertex2, vertex3) )
    bm.edges.new( (vertex3, vertex4) )
    bm.edges.new( (vertex4, vertex1) )
    '''
    #~
    # How to create a face
    # it's not necessary to create the edges before, I made it only to show how create 
    # edges too
    '''
    bm.faces.new( (vertex1, vertex2, vertex3, vertex4) )
    '''
    if (len(verts) > 2):
        bm.faces.new(verts)
    #~
    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    #~
    if (useUvs==True):
        ob.select = True
        bpy.context.scene.objects.active = ob
        planarUvProject()
    #~
    return ob

def getAlembicCurves(obj=None):
    if not obj:
        obj = ss()
    name = obj.name
    start, end = getStartEnd()
    for i in range(start, end):
        goToFrame(i)
        blankFrame()
        obj = bpy.context.scene.objects[obj.name] # make sure obj is still accessible
        splines = obj.data.splines
        for spline in splines:
            points = []
            for point in spline.points:
                points.append(point.co)
            drawPoints(points)

# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

# 6 of 10. DRAWING

# note that unlike createStroke, this creates a stroke from raw coordinates
def drawPoints(points=None, color=None, frame=None, layer=None):
    if (len(points) > 0):
        if not color:
            color = getActiveColor()
        else:
            color = createColor(color)
        if not layer:
            layer = getActiveLayer()
            if not layer:
                gp = getActiveGp()
                layer = gp.layers.new("GP_Layer")
                gp.layers.active = layer
        if not frame:
            frame = getActiveFrame()
            if not frame:
                try:
                    frame = layer.frames.new(currentFrame())
                except:
                    pass
        stroke = frame.strokes.new(color.name)
        stroke.draw_mode = "3DSPACE"
        stroke.points.add(len(points))
        for i, point in enumerate(points):
            pressure = 1.0
            strength = 1.0
            if (len(point) > 3):
                pressure = point[3]
            if (len(point) > 4):
                strength = point[4]
            createPoint(stroke, i, (point[0], point[2], point[1]), pressure, strength)
        return stroke
    else:
        return None

def createPoint(_stroke, _index, _point, pressure=1, strength=1):
    _stroke.points[_index].co = _point
    _stroke.points[_index].select = True
    _stroke.points[_index].pressure = pressure
    _stroke.points[_index].strength = strength

def addPoint(_stroke, _point, pressure=1, strength=1):
    _stroke.points.add(1)
    createPoint(_stroke, len(_stroke.points)-1, _point, pressure, strength)

def closeStroke(_stroke):
    addPoint(_stroke, _stroke.points[0].co)

def createStrokes(strokes, palette=None):
    if (palette == None):
        palette = getActivePalette()
    frame = getActiveFrame()
    if (frame == None):
        frame = getActiveLayer().frames.new(bpy.context.scene.frame_current)
    #~
    for strokeSource in strokes:
        strokeColor = (0,0,0)
        try:
            strokeColor = createColor(strokeSource.color.color)
        except:
            pass
        strokeDest = frame.strokes.new(getActiveColor().name)        
        strokeDest.draw_mode = '3DSPACE'
        strokeDest.points.add(len(strokeSource.points))
        for l in range(0, len(strokeSource.points)):
            strokeDest.points[l].co = strokeSource.points[l].co 
            strokeDest.points[l].pressure = 1
            strokeDest.points[l].strength = 1

def createStroke(points, color=(0,0,0), frame=None, palette=None):
    if (palette == None):
        palette = getActivePalette()
    if (frame == None):
        frame = getActiveFrame()
    #~
    strokeColor = createColor(color)
    stroke = frame.strokes.new(getActiveColor().name)        
    stroke.draw_mode = '3DSPACE'
    stroke.points.add(len(points))
    for l in range(0, len(points)):
        stroke.points[l].co = points[l].co 
        stroke.points[l].pressure = 1
        stroke.points[l].strength = 1

def deleteStroke(_stroke):
    bpy.ops.object.select_all(action='DESELECT')
    _stroke.select = True
    deleteSelected()

def deleteStrokes(_strokes):
    bpy.ops.object.select_all(action='DESELECT')
    for stroke in _strokes:
        stroke.select = True
    deleteSelected()

def selectStrokePoint(_stroke, _index):
    for i, point in enumerate(_stroke.points):
        if (i==_index):
            point.select=True
        else:
            point.select=False
    return _stroke.points[_index]

def selectLastStrokePoint(_stroke):
    return selectStrokePoint(_stroke, len(_stroke.points)-1)

def distributeStrokesAlt(step=1):
    palette = getActivePalette()
    strokes = getAllStrokes()
    layer = getActiveLayer()
    strokesToBuild = []
    counter = 1
    for i in range(0, len(strokes)):
        goToFrame(i+1)
        try:
            layer.frames.new(bpy.context.scene.frame_current)
        except:
            pass
        layer.active_frame = layer.frames[i+1]
        copyFrame(0, i+1, counter)
        counter += step
        if (counter > len(strokes)-1):
            counter = len(strokes)-1

def distributeStrokes(pointStep=10, step=1, minPointStep=2):
    start, end = getStartEnd()
    palette = getActivePalette()
    strokes = getAllStrokes()
    layer = getActiveLayer()
    strokeCounter = 0
    extraFrameCounter = 0
    #~
    for i in range(0, len(strokes)):
        goToFrame(i+1+extraFrameCounter)
        try:
            layer.frames.new(bpy.context.scene.frame_current)
        except:
            pass
        layer.active_frame = layer.frames[bpy.context.scene.frame_current]
        #~
        if (pointStep < minPointStep):
            try:
                copyFrame(0, i+1+extraFrameCounter, strokeCounter+1)
            except:
                pass
        else:
            try:
                copyFrame(0, i+1+extraFrameCounter, strokeCounter)
            except:
                pass
        #~
        if (pointStep >= minPointStep):
            pointsCounter = 0
            stroke = strokes[strokeCounter]
            points = stroke.points
            subFrames = roundValInt(len(points)/pointStep)
            for j in range(0, subFrames):
                extraFrameCounter += 1
                outLoc = i+1+extraFrameCounter
                goToFrame(outLoc)
                try:
                    layer.frames.new(bpy.context.scene.frame_current)
                except:
                    pass
                layer.active_frame = layer.frames[bpy.context.scene.frame_current]
                #~
                for l in range(0, strokeCounter):
                    try:
                        createStroke(layer.frames[0].strokes[l].points, layer.frames[0].strokes[l].color.color, layer.frames[outLoc])#newStroke.color.color)
                    except:
                        pass
                newStroke = layer.frames[0].strokes[strokeCounter]
                newPoints = []
                for l in range(0, len(newStroke.points)):
                    if (l < j * pointStep):
                        newPoints.append(newStroke.points[l])  
                #~       
                try:                                  
                    createStroke(newPoints, newStroke.color.color, layer.frames[outLoc])
                except:
                    pass
        #~
        strokeCounter += step
        if (strokeCounter > len(strokes)-1):
            strokeCounter = len(strokes)-1
    #~
    lastLoc = len(strokes)+1+extraFrameCounter
    goToFrame(lastLoc)
    try:
        layer.frames.new(bpy.context.scene.frame_current)
    except:
        pass
    layer.active_frame = layer.frames[bpy.context.scene.frame_current]
    try:
        copyFrame(0, lastLoc)
    except:
        pass

#ds = distributeStrokes

def writeOnStrokes(pointStep=10, step=1):
    gp = getActiveGp()
    for i in range(0, len(gp.layers)):
        gp.layers.active_index = i
        distributeStrokes(pointStep=pointStep, step=step)

def makeLine(p1, p2):
    return drawPoints([p1, p2])

def makeGrid(gridRows=10, gridColumns=10, cell=0.1, zPos=0):
    strokes = []
    #~
    xMax = gridRows * cell;
    yMax = gridColumns * cell;
    xHalf = xMax / 2;
    yHalf = yMax / 2;
    #~
    for x in range(0, gridRows+1):
        xPos = x * cell;
        strokes.append(makeLine((-xHalf, xPos - xHalf, zPos), (xHalf, xPos - xHalf, zPos)))
    #~
    for y in range(0, gridColumns+1):
        yPos = y * cell;
        strokes.append(makeLine((yPos - yHalf, -yHalf, zPos), (yPos - yHalf, yHalf, zPos)))
    #~
    return strokes


def makeCube(pos=(0,0,0), size=1):
    strokes = []
    s = size / 2
    #~
    p1 = addVec3((-s, -s, s), pos)
    p2 = addVec3((-s, s, s), pos)
    p3 = addVec3((s, -s, s), pos)
    p4 = addVec3((s, s, s), pos)
    p5 = addVec3((-s, -s, -s), pos)
    p6 = addVec3((-s, s, -s), pos)
    p7 = addVec3((s, -s, -s), pos)
    p8 = addVec3((s, s, -s), pos)
    #~
    strokes.append(makeLine(p1, p2))
    strokes.append(makeLine(p2, p4))
    strokes.append(makeLine(p3, p1))
    strokes.append(makeLine(p4, p3))
    #~
    strokes.append(makeLine(p5, p6))
    strokes.append(makeLine(p6, p8))
    strokes.append(makeLine(p7, p5))
    strokes.append(makeLine(p8, p7))
    #~
    strokes.append(makeLine(p1, p5))
    strokes.append(makeLine(p2, p6))
    strokes.append(makeLine(p3, p7))
    strokes.append(makeLine(p4, p8))
    #~
    return strokes

def makeSquare(pos=(0,0,0), size=1):
    strokes = []
    s = size / 2
    p1 = addVec3((-s, -s, 0), pos)
    p2 = addVec3((-s, s, 0), pos)
    p3 = addVec3((s, -s, 0), pos)
    p4 = addVec3((s, s, 0), pos)
    strokes.append(makeLine(p1, p2))
    strokes.append(makeLine(p1, p3))
    strokes.append(makeLine(p4, p2))
    strokes.append(makeLine(p4, p3))
    #~
    return strokes

def makeCircle(pos=(0,0,0), size=1, resolution=10, vertical=True):
    points = []
    x = 0
    y = 0
    angle = 0.0
    step = 1.0/resolution
    #~
    while (angle < 2 * math.pi):
        x = (size/2.0) * math.cos(angle)
        y = (size/2.0) * math.sin(angle)
        if (vertical==True):
            points.append(addVec3((x, y, 0), pos))
        else:
            points.append(addVec3((x, 0, y), pos))
        angle += step
    #~
    return drawPoints(points)

def makeSphere(pos=(0,0,0), size=1, resolution=10, lat=10, lon=10):
    points = []
    for i in range(0, lat):
        for j in range(0, lon):
            points.append(multVec3(addVec3(getLatLon(i, j), pos), (size,size,size)))
    drawPoints(points)

def getLatLon(lat, lon):
    eulat = (math.pi / 2.0) - lat
    slat = math.sin(eulat)
    x = math.cos(lon) * slat
    y = math.sin(lon) * slat
    z = math.cos(eulat)
    return (x, y, z)

def makeStarBurst(pos=(0,0,0), size=1, reps=20):
    s = size/2.0
    strokes = []
    for i in range(0, reps):
        lat = random.uniform(0, 90)
        lon = random.uniform(0, 180)
        p2 = multVec3(getLatLon(lat, lon), (s, s, s))
        strokes.append(drawPoints([pos, p2]))
    return strokes

def makeTriangle(pos=(0,0,0), size=1):
    s = size/2.0
    p1 = (pos[0], pos[1] + s, pos[2])
    p2 = (pos[0] - s, pos[1] - s, pos[2])
    p3 = (pos[0] + s, pos[1] - s, pos[2])
    return drawPoints([p1, p2, p3, p1])

def makePyramid(pos=(0,0,0), size=1):
    strokes = []
    s = size/2.0
    p1 = (pos[0], pos[1] + s, pos[2])
    p2 = (pos[0] - s, pos[1] - s, pos[2] + s)
    p3 = (pos[0] + s, pos[1] - s, pos[2] + s)
    #~
    strokes.append(drawPoints([p1, p2, p3, p1]))
    #~
    p4 = (pos[0], pos[1] + s, pos[2])
    p5 = (pos[0] - s, pos[1] - s, pos[2] - s)
    p6 = (pos[0] + s, pos[1] - s, pos[2] - s)
    #~
    strokes.append(drawPoints([p4, p5, p6, p4]))
    #~
    strokes.append(drawPoints([p2, p5]))
    strokes.append(drawPoints([p3, p6]))
    #~
    return strokes

def smoothStroke(stroke=None):
    if not stroke:
        stroke = getSelectedStroke()
    points = stroke.points
    #~
    weight = 18
    scale = 1.0 / (weight + 2)
    nPointsMinusTwo = len(points) - 2
    lower = 0
    upper = 0
    center = 0
    #~
    for i in range(1, nPointsMinusTwo):
        lower = points[i-1].co
        center = points[i].co
        upper = points[i+1].co
        #~
        center.x = (lower.x + weight * center.x + upper.x) * scale
        center.y = (lower.y + weight * center.y + upper.y) * scale
    
def splitStroke(stroke=None):
    if not stroke:
        stroke = getSelectedStroke()    
    points = stroke.points
    co = []
    pressure = []
    strength = []
    #~
    for i in range(1, len(points), 2):
        center = (points[i].co.x, points[i].co.y, points[i].co.z)
        lower = (points[i-1].co.x, points[i-1].co.y, points[i-1].co.z)
        x = (center[0] + lower[0]) / 2
        y = (center[1] + lower[1]) / 2
        z = (center[2] + lower[2]) / 2
        p = (x, y, z)
        #~
        co.append(lower)
        co.append(p)
        co.append(center)
        #~
        pressure.append(points[i-1].pressure)
        pressure.append((points[i-1].pressure + points[i].pressure) / 2)
        pressure.append(points[i].pressure)
        #~
        strength.append(points[i-1].strength)
        strength.append((points[i-1].strength + points[i].strength) / 2)
        strength.append(points[i].strength)
    #~
    points.add(len(co) - len(points))
    for i in range(0, len(points)):
        createPoint(stroke, i, co[i], pressure[i], strength[i])

def refine(stroke=None, splitReps=2, smoothReps=10):
    if not stroke:
        stroke = getSelectedStroke()    
    points = stroke.points
    #~
    for i in range(0, splitReps):
        splitStroke(stroke)  
        smoothStroke(stroke)  
    #~
    for i in range(0, smoothReps - splitReps):
        smoothStroke(stroke)    


# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

# 7 of 10. FREESTYLE

# based on freestyle_to_gpencil by Folkert de Vries
# https://github.com/folkertdev/freestyle-gpencil-exporter

# a tuple containing all strokes from the current render. should get replaced by freestyle.context at some point
def get_strokes():
    return tuple(map(Operators().get_stroke_from_index, range(Operators().get_strokes_size())))

# get the exact scene dimensions
def render_height(scene):
    return int(scene.render.resolution_y * scene.render.resolution_percentage / 100)

def render_width(scene):
    return int(scene.render.resolution_x * scene.render.resolution_percentage / 100)

def render_dimensions(scene):
    return render_width(scene), render_height(scene)

def render_visible_strokes():
    """Renders the scene, selects visible strokes and returns them as a tuple"""
    if (bpy.context.scene.freestyle_gpencil_export.visible_only == True):
        upred = QuantitativeInvisibilityUP1D(0) # visible lines only
    else:
        upred = TrueUP1D() # all lines
    Operators.select(upred)
    Operators.bidirectional_chain(ChainSilhouetteIterator(), NotUP1D(upred))
    Operators.create(TrueUP1D(), [])
    return get_strokes()

def render_external_contour():
    """Renders the scene, selects visible strokes of the Contour nature and returns them as a tuple"""
    upred = AndUP1D(QuantitativeInvisibilityUP1D(0), ContourUP1D())
    Operators.select(upred)
    # chain when the same shape and visible
    bpred = SameShapeIdBP1D()
    Operators.bidirectional_chain(ChainPredicateIterator(upred, bpred), NotUP1D(upred))
    Operators.create(TrueUP1D(), [])
    return get_strokes()


def create_gpencil_layer(scene, name, color, alpha, fill_color, fill_alpha):
    """Creates a new GPencil layer (if needed) to store the Freestyle result"""
    gp = bpy.data.grease_pencil.get("FreestyleGPencil", False) or bpy.data.grease_pencil.new(name="FreestyleGPencil")
    scene.grease_pencil = gp
    layer = gp.layers.get(name, False)
    if not layer:
        print("making new GPencil layer")
        layer = gp.layers.new(name=name, set_active=True)
        # set defaults
        '''
        layer.fill_color = fill_color
        layer.fill_alpha = fill_alpha
        layer.alpha = alpha 
        layer.color = color
        '''
    elif scene.freestyle_gpencil_export.use_overwrite:
        # empty the current strokes from the gp layer
        layer.clear()

    # can this be done more neatly? layer.frames.get(..., ...) doesn't seem to work
    frame = frame_from_frame_number(layer, scene.frame_current) or layer.frames.new(scene.frame_current)
    return layer, frame 

def frame_from_frame_number(layer, current_frame):
    """Get a reference to the current frame if it exists, else False"""
    return next((frame for frame in layer.frames if frame.frame_number == current_frame), False)

def freestyle_to_gpencil_strokes(strokes, frame, pressure=1, draw_mode="3DSPACE", blenderRender=False):
    scene = bpy.context.scene
    if (scene.freestyle_gpencil_export.doClearPalette == True):
        clearPalette()
    """Actually creates the GPencil structure from a collection of strokes"""
    mat = scene.camera.matrix_local.copy()
    #~ 
    obj = scene.objects.active #bpy.context.edit_object
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me) #from_edit_mesh(me)
    #~
    # this speeds things up considerably
    images = getUvImages()
    #~
    uv_layer = bm.loops.layers.uv.active
    #~
    #~ 
    strokeCounter = 0;
    
    firstRun = True
    allPoints = []
    strokesToRemove = []
    allPointsCounter = 1
    lastActiveColor = None

    for fstroke in strokes:
        # *** fstroke contains coordinates of original vertices ***
        #~
        sampleVertRaw = (0,0,0)
        sampleVert = (0,0,0)
        #~
        fstrokeCounter = 0
        for svert in fstroke:
            fstrokeCounter += 1
        for i, svert in enumerate(fstroke):
            if (i == int(fstrokeCounter/2)):
            #if (i == fstrokeCounter-1):
                sampleVertRaw = mat * svert.point_3d
                break
        '''
        for svert in fstroke:
            sampleVertRaw = mat * svert.point_3d
            break
        '''
        sampleVert = (sampleVertRaw[0], sampleVertRaw[1], sampleVertRaw[2])
        #~
        pixel = (1,0,1)
        lastPixel = getActiveColor().color
        # TODO better hit detection method needed
        # possibly sort original verts by distance?
        # http://stackoverflow.com/questions/6618515/sorting-list-based-on-values-from-another-list
        # X.sort(key=dict(zip(X, Y)).get)
        distances = []
        sortedVerts = bm.verts
        for v in bm.verts:
            distances.append(getDistance(obj.matrix_world * v.co, sampleVert))
        sortedVerts.sort(key=dict(zip(sortedVerts, distances)).get)
        #~ ~ ~ ~ ~ ~ ~ ~ ~ 
        if (scene.freestyle_gpencil_export.use_connecting == True):
            if (firstRun == True):
                for svert in sortedVerts:
                    allPoints.append(svert)
                firstRun = False

            if (lastActiveColor != None):
                points = []
                for i in range(allPointsCounter, len(allPoints)):
                    if (getDistance(allPoints[i].co, allPoints[i-1].co) < scene.freestyle_gpencil_export.vertexHitbox):
                        points.append(allPoints[i-1])
                    else:
                        allPointsCounter = i
                        break
                if (scene.freestyle_gpencil_export.use_fill):
                    lastActiveColor.fill_color = lastActiveColor.color
                    lastActiveColor.fill_alpha = 0.9
                gpstroke = frame.strokes.new(lastActiveColor.name)
                gpstroke.draw_mode = "3DSPACE"
                gpstroke.points.add(count=len(points))  
                for i in range(0, len(points)):
                    gpstroke.points[i].co = obj.matrix_world * points[i].co
                    gpstroke.points[i].select = True
                    gpstroke.points[i].strength = 1
                    gpstroke.points[i].pressure = pressure
        #~ ~ ~ ~ ~ ~ ~ ~ ~
        targetVert = None
        for v in sortedVerts:
            targetVert = v
            break
        #~
            #if (compareTuple(obj.matrix_world * v.co, obj.matrix_world * v.co, numPlaces=1) == True):
            #if (hitDetect3D(obj.matrix_world * v.co, sampleVert, hitbox=bpy.context.scene.freestyle_gpencil_export.vertexHitbox) == True):
            #if (getDistance(obj.matrix_world * v.co, sampleVert) <= 0.5):
        try:
            uv_first = uv_from_vert_first(uv_layer, targetVert)
            #uv_average = uv_from_vert_average(uv_layer, v)
            #print("Vertex: %r, uv_first=%r, uv_average=%r" % (v, uv_first, uv_average))
            #~
            pixelRaw = None
            if (blenderRender == True):
                pixelRaw = getPixelFromUvArray(images[obj.active_material.texture_slots[0].texture.image.name], uv_first[0], uv_first[1])
            else:
                pixelRaw = getPixelFromUvArray(images[obj.active_material.node_tree.nodes["Image Texture"].image.name], uv_first[0], uv_first[1])                
            #pixelRaw = getPixelFromUv(obj.active_material.texture_slots[0].texture.image, uv_first[0], uv_first[1])
            #pixelRaw = getPixelFromUv(obj.active_material.texture_slots[0].texture.image, uv_average[0], uv_average[1])
            pixel = (pixelRaw[0], pixelRaw[1], pixelRaw[2])
            #break
            #print("Pixel: " + str(pixel))    
        except:
            pixel = lastPixel   
        #~ 
        lastActiveColor = createAndMatchColorPalette(pixel, scene.freestyle_gpencil_export.numMaxColors, scene.freestyle_gpencil_export.numColPlaces)
        #~
        if (scene.freestyle_gpencil_export.use_fill):
            lastActiveColor.fill_color = lastActiveColor.color
            lastActiveColor.fill_alpha = 0.9
        gpstroke = frame.strokes.new(lastActiveColor.name)
        # enum in ('SCREEN', '3DSPACE', '2DSPACE', '2DIMAGE')
        gpstroke.draw_mode = "3DSPACE"
        gpstroke.points.add(count=len(fstroke))

        #if draw_mode == '3DSPACE':
        for svert, point in zip(fstroke, gpstroke.points):
            # svert.attribute.color = (1, 0, 0) # confirms that this callback runs earlier than the shading
            point.co = mat * svert.point_3d
            point.select = True
            point.strength = 1
            point.pressure = pressure
        '''
        elif draw_mode == 'SCREEN':
            width, height = render_dimensions(bpy.context.scene)
            for svert, point in zip(fstroke, gpstroke.points):
                x, y = svert.point
                point.co = Vector((abs(x / width), abs(y / height), 0.0)) * 100
                point.select = True
                point.strength = 1
                point.pressure = 1
        else:
            raise NotImplementedError()
        '''

def freestyle_to_fill(scene):
    default = dict(color=(0, 0, 0), alpha=1, fill_color=(0, 1, 0), fill_alpha=1)
    layer, frame = create_gpencil_layer(scene, "freestyle fill", **default)
    # render the external contour 
    strokes = render_external_contour()
    freestyle_to_gpencil_strokes(strokes, frame, draw_mode="3DSPACE")#scene.freestyle_gpencil_export.draw_mode)

def freestyle_to_strokes(scene):
    default = dict(color=(0, 0, 0), alpha=1, fill_color=(0, 1, 0), fill_alpha=0)
    layer, frame = create_gpencil_layer(scene, "freestyle stroke", **default)
    # render the normal strokes 
    #strokes = render_visible_strokes()
    strokes = get_strokes()
    freestyle_to_gpencil_strokes(strokes, frame, draw_mode="3DSPACE")#scene.freestyle_gpencil_export.draw_mode)

def export_stroke(scene, _, x):
    # create stroke layer
    freestyle_to_strokes(scene)

def export_fill(scene, layer, lineset):
    # Doesn't work for 3D due to concave edges
    return

    #if not scene.freestyle_gpencil_export.use_freestyle_gpencil_export:
    #    return 

    #if scene.freestyle_gpencil_export.use_fill:
    #    # create the fill layer
    #    freestyle_to_fill(scene)
    #    # delete these strokes
    #    Operators.reset(delete_strokes=True)

# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

# 8 of 10. SHORTCUTS

def up():
    makeParent(unParent=True)

def ss():
	returns = select()
	if (len(returns) > 0):
	    return returns[0]
	else:
		return None

def dn():
    deleteName(_name="latk_ob")
    deleteName(_name="caps_ob")

def k():
	target = ss()
	for obj in target:
		keyTransform(obj, currentFrame())

rb = readBrushStrokes
wb = writeBrushStrokes
c = changeColor
a = alignCamera
s = select
d = delete
j = joinObjects
df = deleteFromAllFrames
spl = splitLayer
cplf = checkLayersAboveFrameLimit

splf = splitLayersAboveFrameLimit

getVertices = getVerts
gotoFrame = goToFrame

# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

# 10 of 10. UI

class LightningArtistToolkitPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    extraFormats_TiltBrush = bpy.props.BoolProperty(
        name = 'Tilt Brush',
        description = "Tilt Brush import",
        default = True
    )

    extraFormats_GML = bpy.props.BoolProperty(
        name = 'GML',
        description = "Graffiti Markup Language import/export",
        default = False
    )

    extraFormats_ASC = bpy.props.BoolProperty(
        name = 'ASC Point Cloud',
        description = "ASC point cloud import/export",
        default = False
    )

    extraFormats_Painter = bpy.props.BoolProperty(
        name = 'Corel Painter',
        description = "Corel Painter script import/export",
        default = False
    )

    extraFormats_SVG = bpy.props.BoolProperty(
        name = 'SVG SMIL',
        description = "SVG SMIL export (experimental)",
        default = False
    )

    extraFormats_Norman = bpy.props.BoolProperty(
        name = 'NormanVR',
        description = "NormanVR import (experimental)",
        default = False
    )

    extraFormats_VRDoodler = bpy.props.BoolProperty(
        name = 'VRDoodler',
        description = "VRDoodler import",
        default = False
    )

    extraFormats_FBXSequence = bpy.props.BoolProperty(
        name = 'FBX Sequence',
        description = "FBX Sequence export",
        default = False
    )

    extraFormats_SculptrVR = bpy.props.BoolProperty(
        name = 'SculptrVR CSV',
        description = "SculptrVR CSV import/export",
        default = True
    )

    def draw(self, context):
        layout = self.layout
        layout.label("Add menu items to import:")
        layout.prop(self, "extraFormats_TiltBrush")
        layout.prop(self, "extraFormats_SculptrVR")
        layout.prop(self, "extraFormats_ASC")
        layout.prop(self, "extraFormats_GML")
        layout.prop(self, "extraFormats_Painter")
        layout.prop(self, "extraFormats_Norman")
        layout.prop(self, "extraFormats_VRDoodler")
        #~
        layout.label("Add menu items to export:")
        layout.prop(self, "extraFormats_SculptrVR")
        layout.prop(self, "extraFormats_ASC")
        layout.prop(self, "extraFormats_GML")
        layout.prop(self, "extraFormats_Painter")
        layout.prop(self, "extraFormats_SVG")
        layout.prop(self, "extraFormats_FBXSequence")


class ImportLatk(bpy.types.Operator, ImportHelper):
    """Load a Latk File"""
    resizeTimeline = BoolProperty(name="Resize Timeline", description="Set in and out points", default=True)
    useScaleAndOffset = BoolProperty(name="Use Scale and Offset", description="Compensate scale for Blender viewport", default=True)

    bl_idname = "import_scene.latk"
    bl_label = "Import Latk"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".json"
    filter_glob = StringProperty(
            default="*.latk;*.json",
            options={'HIDDEN'},
            )

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "resizeTimeline", "useScaleAndOffset"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        keywords["resizeTimeline"] = self.resizeTimeline
        keywords["useScaleAndOffset"] = self.useScaleAndOffset
        la.readBrushStrokes(**keywords)
        return {'FINISHED'}


class ImportTiltBrush(bpy.types.Operator, ImportHelper):
    """Load a Tilt Brush File"""
    bl_idname = "import_scene.tbjson"
    bl_label = "Import Tilt Brush"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".json"
    filter_glob = StringProperty(
            default="*.tilt;*.json",
            options={'HIDDEN'},
            )

    vertSkip = IntProperty(name="Read Vertices", description="Read every n vertices", default=1)

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        keywords["vertSkip"] = self.vertSkip
        la.importTiltBrush(**keywords)
        return {'FINISHED'} 


class ImportNorman(bpy.types.Operator, ImportHelper):
    """Load a Norman File"""
    bl_idname = "import_scene.norman"
    bl_label = "Import Norman"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".json"
    filter_glob = StringProperty(
            default="*.json",
            options={'HIDDEN'},
            )

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        la.importNorman(**keywords)
        return {'FINISHED'} 


class ImportVRDoodler(bpy.types.Operator, ImportHelper):
    """Load a VRDoodler File"""
    bl_idname = "import_scene.vrdoodler"
    bl_label = "Import VRDoodler"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".obj"
    filter_glob = StringProperty(
            default="*.obj",
            options={'HIDDEN'},
            )

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        la.importVRDoodler(**keywords)
        return {'FINISHED'} 


class ImportASC(bpy.types.Operator, ImportHelper):
    """Load an ASC point cloud"""
    bl_idname = "import_scene.asc"
    bl_label = "Import ASC point cloud"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".asc"
    filter_glob = StringProperty(
            default="*.asc;*.xyz",
            options={'HIDDEN'},
            )

    strokeLength = IntProperty(name="Points per Stroke", description="Group every n points into strokes", default=1)

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        keywords["strokeLength"] = self.strokeLength
        la.importAsc(**keywords)
        return {'FINISHED'} 


class ImportSculptrVR(bpy.types.Operator, ImportHelper):
    """Load an ASC point cloud"""
    bl_idname = "import_scene.sculptrvr"
    bl_label = "Import SculptrVR CSV"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".csv"
    filter_glob = StringProperty(
            default="*.csv",
            options={'HIDDEN'},
            )

    strokeLength = IntProperty(name="Points per Stroke", description="Group every n points into strokes", default=1)

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        keywords["strokeLength"] = self.strokeLength
        la.importSculptrVr(**keywords)
        return {'FINISHED'} 


class ImportPainter(bpy.types.Operator, ImportHelper):
    """Load a Painter script"""
    bl_idname = "import_scene.painter"
    bl_label = "Import Painter"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".txt"
    filter_glob = StringProperty(
            default="*.txt",
            options={'HIDDEN'},
            )

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        la.importPainter(**keywords)
        return {'FINISHED'} 


class ImportGml(bpy.types.Operator, ImportHelper):
    """Load a GML File"""
    bl_idname = "import_scene.gml"
    bl_label = "Import Gml"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".gml"
    filter_glob = StringProperty(
            default="*.gml",
            options={'HIDDEN'},
            )

    sequenceAnim = BoolProperty(name="Sequence in Time", description="Create a new frame for each stroke", default=False)
    splitStrokes = BoolProperty(name="Split Strokes", description="Split animated strokes to layers", default=False)
                
    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "splitStrokes", "sequenceAnim"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        keywords["splitStrokes"] = self.splitStrokes
        keywords["sequenceAnim"] = self.sequenceAnim
        #~
        la.gmlParser(**keywords)
        return {'FINISHED'} 


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~


class ExportLatkJson(bpy.types.Operator, ExportHelper): # TODO combine into one class
    """Save a Latk Json File"""

    bake = BoolProperty(name="Bake Frames", description="Bake Keyframes to All Frames", default=False)
    roundValues = BoolProperty(name="Limit Precision", description="Round Values to Reduce Filesize", default=False)    
    numPlaces = IntProperty(name="Number Places", description="Number of Decimal Places", default=7)
    useScaleAndOffset = BoolProperty(name="Use Scale and Offset", description="Compensate scale for Blender viewport", default=True)

    bl_idname = "export_scene.latkjson"
    bl_label = 'Export Latk Json'
    bl_options = {'PRESET'}

    filename_ext = ".json"

    filter_glob = StringProperty(
            default="*.json",
            options={'HIDDEN'},
            )

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "check_existing", "bake", "roundValues", "numPlaces", "useScaleAndOffset"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        keywords["bake"] = self.bake
        keywords["roundValues"] = self.roundValues
        keywords["numPlaces"] = self.numPlaces
        keywords["useScaleAndOffset"] = self.useScaleAndOffset
        #~
        la.writeBrushStrokes(**keywords, zipped=False)
        return {'FINISHED'}

class ExportLatk(bpy.types.Operator, ExportHelper):  # TODO combine into one class
    """Save a Latk File"""

    bake = BoolProperty(name="Bake Frames", description="Bake Keyframes to All Frames", default=False)
    roundValues = BoolProperty(name="Limit Precision", description="Round Values to Reduce Filesize", default=False)    
    numPlaces = IntProperty(name="Number Places", description="Number of Decimal Places", default=7)
    useScaleAndOffset = BoolProperty(name="Use Scale and Offset", description="Compensate scale for Blender viewport", default=True)

    bl_idname = "export_scene.latk"
    bl_label = 'Export Latk'
    bl_options = {'PRESET'}

    filename_ext = ".latk"

    filter_glob = StringProperty(
            default="*.latk",
            options={'HIDDEN'},
            )

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "check_existing", "bake", "roundValues", "numPlaces", "useScaleAndOffset"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        keywords["bake"] = self.bake
        keywords["roundValues"] = self.roundValues
        keywords["numPlaces"] = self.numPlaces
        keywords["useScaleAndOffset"] = self.useScaleAndOffset
        #~
        la.writeBrushStrokes(**keywords, zipped=True)
        return {'FINISHED'}


class ExportGml(bpy.types.Operator, ExportHelper):
    """Save a GML File"""

    bl_idname = "export_scene.gml"
    bl_label = 'Export Gml'
    bl_options = {'PRESET'}

    filename_ext = ".gml"
    filter_glob = StringProperty(
            default="*.gml",
            options={'HIDDEN'},
            )

    make2d = BoolProperty(name="Make 2D", description="Project Coordinates to Camera View", default=False)

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "check_existing"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        keywords["make2d"] = self.make2d
        #~
        la.writeGml(**keywords)
        return {'FINISHED'} 


class ExportFbxSequence(bpy.types.Operator, ExportHelper):
    """Save an FBX Sequence"""

    bl_idname = "export_scene.fbx_sequence"
    bl_label = 'Export FBX Sequence'
    bl_options = {'PRESET'}

    filename_ext = ".fbx"
    filter_glob = StringProperty(
            default="*.fbx",
            options={'HIDDEN'},
            )

    sketchFab = BoolProperty(name="Sketchfab List", description="Generate list for Sketchfab animation", default=True)

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "check_existing"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        keywords["sketchFab"] = self.sketchFab
        #~
        la.exportForUnity(**keywords)
        return {'FINISHED'} 


class ExportSculptrVR(bpy.types.Operator, ExportHelper):
    """Save a SculptrVR CSV"""

    bl_idname = "export_scene.sculptrvr"
    bl_label = 'Export SculptrVR CSV'
    bl_options = {'PRESET'}

    filename_ext = ".csv"
    filter_glob = StringProperty(
            default="*.csv",
            options={'HIDDEN'},
            )

    sphereRadius = FloatProperty(name="Sphere Radius", description="Sphere Radius (min 0.01)", default=10)
    octreeSize = IntProperty(name="Octree Size", description="Octree Size (0-19)", default=7)
    vol_scale = FloatProperty(name="Volume Scale", description="Volume Scale (0-1)", default=0.33)
    mtl_val = IntProperty(name="Material", description="Material Value (127, 254, or 255)", default=255)
    file_format = EnumProperty(
        name="File Format",
        items=(
            ("SPHERE", "Sphere per Voxel", "Recommended", 0),
            ("SINGLE", "Single Voxel", "Single voxel at octree size", 1),
            ("LEGACY", "Legacy Format", "Probably too small to see", 2),
        ),
        default="SPHERE"
    )


    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "check_existing"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        keywords["sphereRadius"] = self.sphereRadius
        keywords["octreeSize"] = self.octreeSize
        keywords["vol_scale"] = self.vol_scale
        keywords["mtl_val"] = self.mtl_val
        keywords["file_format"] = self.file_format
        #~
        la.exportSculptrVrCsv(**keywords)
        return {'FINISHED'} 


class ExportASC(bpy.types.Operator, ExportHelper):
    """Save an ASC point cloud"""

    bl_idname = "export_scene.asc"
    bl_label = 'Export ASC'
    bl_options = {'PRESET'}

    filename_ext = ".asc"
    filter_glob = StringProperty(
            default="*.asc",
            options={'HIDDEN'},
            )

    def execute(self, context):
        import latk_blender as la
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "check_existing"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        la.exportAsc(**keywords)
        return {'FINISHED'} 


class ExportSvg(bpy.types.Operator, ExportHelper):
    """Save an SVG SMIL File"""

    bl_idname = "export_scene.svg"
    bl_label = 'Export Svg'
    bl_options = {'PRESET'}

    filename_ext = ".svg"
    filter_glob = StringProperty(
            default="*.svg",
            options={'HIDDEN'},
            )

    def execute(self, context):
        import latk_blender as la
        #keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "check_existing", "bake"))
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "check_existing"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        la.writeSvg(**keywords)
        return {'FINISHED'} 


class ExportPainter(bpy.types.Operator, ExportHelper):
    """Save a Painter script"""

    bl_idname = "export_scene.painter"
    bl_label = 'Export Painter'
    bl_options = {'PRESET'}

    filename_ext = ".txt"
    filter_glob = StringProperty(
            default="*.txt",
            options={'HIDDEN'},
            )

    def execute(self, context):
        import latk_blender as la
        #keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "check_existing", "bake"))
        keywords = self.as_keywords(ignore=("axis_forward", "axis_up", "filter_glob", "split_mode", "check_existing"))
        if bpy.data.is_saved and context.user_preferences.filepaths.use_relative_paths:
            import os
        #~
        la.writePainter(**keywords)
        return {'FINISHED'} 


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~


class FreestyleGPencil(bpy.types.PropertyGroup):
    """Properties for the Freestyle to Grease Pencil exporter"""
    bl_idname = "RENDER_PT_gpencil_export"

    use_freestyle_gpencil_export = BoolProperty(
        name="Grease Pencil Export",
        description="Export Freestyle edges to Grease Pencil"
    )

    use_fill = BoolProperty(
        name="Fill",
        description="Fill the contour with the object's material color",
        default=False
    )

    use_connecting = BoolProperty(
        name="Connecting Strokes",
        description="Connect all vertices with strokes",
        default=False
    )

    visible_only = BoolProperty(
        name="Visible Only",
        description="Only render visible lines",
        default=True
    )

    use_overwrite = BoolProperty(
        name="Overwrite",
        description="Remove the GPencil strokes from previous renders before a new render",
        default=False
    )

    vertexHitbox = FloatProperty(
        name="Vertex Hitbox",
        description="How close a GP stroke needs to be to a vertex",
        default=1.5
    )

    numColPlaces = IntProperty(
        name="Color Places",
        description="How many decimal places used to find matching colors",
        default=5,
    )

    numMaxColors = IntProperty(
        name="Max Colors",
        description="How many colors are in the Grease Pencil palette",
        default=16
    )

    doClearPalette = BoolProperty(
        name="Clear Palette",
        description="Delete palette before beginning a new render",
        default=False
    )

class FreestyleGPencil_Panel(bpy.types.Panel):
    """Creates a Panel in the render context of the properties editor"""
    bl_idname = "RENDER_PT_FreestyleGPencilPanel"
    bl_space_type = 'PROPERTIES'
    bl_label = "Latk Freestyle"
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw_header(self, context):
        self.layout.prop(context.scene.freestyle_gpencil_export, "use_freestyle_gpencil_export", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        gp = scene.freestyle_gpencil_export
        freestyle = scene.render.layers.active.freestyle_settings

        layout.active = (gp.use_freestyle_gpencil_export and freestyle.mode != 'SCRIPT')

        row = layout.row()
        row.prop(gp, "numColPlaces")
        row.prop(gp, "numMaxColors")

        row = layout.row()
        #row.prop(svg, "split_at_invisible")
        row.prop(gp, "use_fill")
        row.prop(gp, "use_overwrite")
        row.prop(gp, "doClearPalette")

        row = layout.row()
        row.prop(gp, "visible_only")
        row.prop(gp, "use_connecting")
        row.prop(gp, "vertexHitbox")


# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~


class LatkProperties(bpy.types.PropertyGroup):
    """Properties for Latk"""
    bl_idname = "GREASE_PENCIL_PT_LatkProperties"

    bakeMesh = BoolProperty(
        name="Auto Bake",
        description="Off: major speedup if you're staying in Blender. On: slow but keeps everything exportable",
        default=False
    )

    minRemapPressure = FloatProperty(
        name="Min",
        description="Minimum Remap Pressure",
        default=0.1
    )

    maxRemapPressure = FloatProperty(
        name="Max",
        description="Maximum Remap Pressure",
        default=1.0
    )

    remapPressureMode = EnumProperty(
        name="Remap Mode",
        items=(
            ("CLAMP_P", "Clamp Pressure", "Clamp pressure values below min or above max", 0),
            ("REMAP_P", "Remap Pressure", "Remap pressure values from 0-1 to min-max", 1),
            ("CLAMP_S", "Clamp Strength", "Clamp strength values below min or above max", 2),
            ("REMAP_S", "Remap Strength", "Remap strength values from 0-1 to min-max", 3)
        ),
        default="REMAP_P"
    )

    saveLayers = BoolProperty(
        name="Save Layers",
        description="Save every layer to its own file",
        default=False
    )

    thickness = FloatProperty(
        name="Thickness",
        description="Tube mesh thickness",
        default=0.1
    )

    resolution = IntProperty(
        name="Resolution",
        description="Tube mesh resolution",
        default=1
    )

    bevelResolution = IntProperty(
        name="Bevel Resolution",
        description="Tube mesh bevel resolution",
        default=0
    )

    decimate = FloatProperty(
        name="Decimate",
        description="Decimate mesh",
        default=0.1
    )

    strokeLength = IntProperty(
        name="Length",
        description="Group every n points into strokes",
        default=2
    )

    strokeGaps = FloatProperty(
        name="Gaps",
        description="Skip points greater than this distance away",
        default=10.0
    )

    shuffleOdds = FloatProperty(
        name="Odds",
        description="Odds of shuffling the points in a stroke",
        default=1.0
    )

    spreadPoints = FloatProperty(
        name="Spread",
        description="Distance to randomize points",
        default=0.1
    )

    numSplitFrames = IntProperty(
        name="Split Frames",
        description="Split layers if they have more than this many frames",
        default=20
    )

    writeStrokeSteps = IntProperty(
        name="Steps",
        description="Write-on steps",
        default=1
    )

    writeStrokePoints = IntProperty(
        name="Points",
        description="Write-on points per step",
        default=10
    )

    vertexColorName = StringProperty(
        name="Vertex Color",
        description="Vertex color name for export",
        default="rgba"
    )

    remesh_mode = EnumProperty(
        name="Remesh Mode",
        items=(
            ("NONE", "No Remesh", "No remeshing curves", 0),
            ("SHARP", "Sharp", "Sharp remesh", 1),
            ("SMOOTH", "Smooth", "Smooth remesh", 2),
            ("BLOCKS", "Blocks", "Blocks remesh", 3)
        ),
        default="NONE"
    )

    material_set_mode = EnumProperty( 
        name="Affect",
        items=(
            ("ALL", "All", "All materials", 0),
            ("SELECTED", "Selected", "Selected materials", 1)
        ),
        default="ALL"
    )

    material_shader_mode = EnumProperty(
        name="Type",
        items=(
            ("DIFFUSE", "Diffuse", "Diffuse shader", 0),
            ("PRINCIPLED", "Principled", "Principled shader", 1),
            ("GLTF", "glTF", "glTF MR shader", 2),
            #("EMISSION", "Emission", "Emission shader", 3)
        ),
        default="PRINCIPLED"
    )

# https://docs.blender.org/api/blender_python_api_2_78_release/bpy.types.Panel.html
class LatkProperties_Panel(bpy.types.Panel):
    """Creates a Panel in the 3D View context"""
    bl_idname = "GREASE_PENCIL_PT_LatkPropertiesPanel"
    bl_space_type = 'VIEW_3D'
    bl_label = "Lightning Artist Toolkit"
    bl_region_type = 'UI'
    bl_context = "object"

    #def draw_header(self, context):
        #self.layout.prop(context.scene.freestyle_gpencil_export, "enable_latk", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        latk = scene.latk_settings

        row = layout.row()
        row.operator("latk_button.gpmesh_singleframe")
     
        row = layout.row()
        row.prop(latk, "thickness")
        row.prop(latk, "resolution")

        row = layout.row()
        row.prop(latk, "bevelResolution")
        row.prop(latk, "decimate")

        row = layout.row()
        row.operator("latk_button.gpmesh")
        row.operator("latk_button.dn")

        row = layout.row()
        row.prop(latk, "bakeMesh")
        row.prop(latk, "saveLayers")
        row.prop(latk, "vertexColorName")
        
        row = layout.row()
        row.prop(latk, "remesh_mode", expand=True)

        # ~ ~ ~ 

        row = layout.row()
        row.operator("latk_button.booleanmod") 
        row.operator("latk_button.booleanmodminus") 
        row.operator("latk_button.simpleclean")

        row = layout.row()
        row.operator("latk_button.smoothmod") 
        row.operator("latk_button.subsurfmod") 
        row.operator("latk_button.decimatemod") 

        row = layout.row()
        row.operator("latk_button.bakeall")
        row.operator("latk_button.bakeanim")
        row.operator("latk_button.scopetimeline") 

        row = layout.row()
        row.operator("latk_button.hidetrue") 
        row.operator("latk_button.hidescale")
        row.operator("latk_button.makeroot") 
        row.operator("latk_button.makeloop") 

        row = layout.row()
        row.prop(latk, "strokeLength")
        row.prop(latk, "strokeGaps")
        row.prop(latk, "shuffleOdds")
        row.prop(latk, "spreadPoints")
        #row.prop(latk, "fast_colors")
        row.operator("latk_button.strokesfrommesh")

        # ~ ~ ~ 

        row = layout.row()
        row.prop(latk, "material_set_mode")
        row.prop(latk, "material_shader_mode")
        row.operator("latk_button.mtlshader")

        row = layout.row()
        row.prop(latk, "minRemapPressure")
        row.prop(latk, "maxRemapPressure")
        row.prop(latk, "remapPressureMode")
        row.operator("latk_button.remappressure")

        # ~ ~ ~ 

        row = layout.row()
        row.prop(latk, "writeStrokeSteps")
        row.prop(latk, "writeStrokePoints")
        row.operator("latk_button.writeonstrokes")
        row.operator("latk_button.pointstoggle")

        row = layout.row()
        row.prop(latk, "numSplitFrames")
        row.operator("latk_button.splf")

# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
# ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

class Latk_Button_SimpleClean(bpy.types.Operator):
    """Loop all latk keyframes"""
    bl_idname = "latk_button.simpleclean"
    bl_label = "Clean"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        simpleClean()
        return {'FINISHED'}

class Latk_Button_ScopeTimeline(bpy.types.Operator):
    """Loop all latk keyframes"""
    bl_idname = "latk_button.scopetimeline"
    bl_label = "Scope"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        resizeToFitGp()
        return {'FINISHED'}

class Latk_Button_MakeLoop(bpy.types.Operator):
    """Loop all latk keyframes"""
    bl_idname = "latk_button.makeloop"
    bl_label = "Loop"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        makeLoop()
        return {'FINISHED'}

class Latk_Button_MakeRoot(bpy.types.Operator):
    """Parent all latk objects to locator"""
    bl_idname = "latk_button.makeroot"
    bl_label = "Root"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        makeRoot()
        return {'FINISHED'}

class Latk_Button_HideScale(bpy.types.Operator):
    """Replace hide keyframes on latk objects with scale keyframes"""
    bl_idname = "latk_button.hidescale"
    bl_label = "Hide Scale"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        hideFramesByScale()
        return {'FINISHED'}

class Latk_Button_BooleanMod(bpy.types.Operator):
    """Boolean union and bake"""
    bl_idname = "latk_button.booleanmod"
    bl_label = "Bool+"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        booleanMod(op="union")
        return {'FINISHED'}

class Latk_Button_BooleanModMinus(bpy.types.Operator):
    """Boolean difference and bake"""
    bl_idname = "latk_button.booleanmodminus"
    bl_label = "Bool-"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        booleanMod(op="difference")
        return {'FINISHED'}

class Latk_Button_SubsurfMod(bpy.types.Operator):
    """Subdivide one level and bake"""
    bl_idname = "latk_button.subsurfmod"
    bl_label = "Subd"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        subsurfMod()
        return {'FINISHED'}

class Latk_Button_SmoothMod(bpy.types.Operator):
    """Smooth using defaults and bake"""
    bl_idname = "latk_button.smoothmod"
    bl_label = "Smooth"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        smoothMod()
        return {'FINISHED'}

class Latk_Button_DecimateMod(bpy.types.Operator):
    """Smooth using defaults and bake"""
    bl_idname = "latk_button.decimatemod"
    bl_label = "Decimate"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        latk_settings = bpy.context.scene.latk_settings
        decimateMod(_decimate=latk_settings.decimate)
        return {'FINISHED'}

class Latk_Button_HideTrue(bpy.types.Operator):
    """Hide or show selected"""
    bl_idname = "latk_button.hidetrue"
    bl_label = "Hide"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        target = s()
        for obj in target:
            hideFrame(obj, currentFrame(), True)
        return {'FINISHED'}

'''
class Latk_Button_HideFalse(bpy.types.Operator):
    """Show selected"""
    bl_idname = "latk_button.hidefalse"
    bl_label = "Show"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        target = s()
        for obj in target:
            hideFrame(obj,currentFrame(), False)
        return {'FINISHED'}
'''

class Latk_Button_Gpmesh(bpy.types.Operator):
    """Mesh all GP strokes. Takes a while.."""
    bl_idname = "latk_button.gpmesh"
    bl_label = "MESH ALL"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        latk_settings = bpy.context.scene.latk_settings
        gpMesh(_thickness=latk_settings.thickness, _remesh=latk_settings.remesh_mode.lower(), _resolution=latk_settings.resolution, _bevelResolution=latk_settings.bevelResolution, _decimate=latk_settings.decimate, _bakeMesh=latk_settings.bakeMesh, _joinMesh=latk_settings.bakeMesh, _saveLayers=False, _vertexColorName=latk_settings.vertexColorName)
        return {'FINISHED'}

class Latk_Button_RemapPressure(bpy.types.Operator):
    """Remap pressure or strength for all strokes"""
    bl_idname = "latk_button.remappressure"
    bl_label = "Pressure"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        latk_settings = bpy.context.scene.latk_settings
        pressureRange(latk_settings.minRemapPressure, latk_settings.maxRemapPressure, latk_settings.remapPressureMode.lower())
        return {'FINISHED'}

class Latk_Button_WriteOnStrokes(bpy.types.Operator):
    """Create a sequence of write-on GP strokes"""
    bl_idname = "latk_button.writeonstrokes"
    bl_label = "Write-On"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        latk_settings = bpy.context.scene.latk_settings
        writeOnStrokes(step=latk_settings.writeStrokeSteps, pointStep=latk_settings.writeStrokePoints)
        return {'FINISHED'}

class Latk_Button_StrokesFromMesh(bpy.types.Operator):
    """Generate GP strokes from a mesh"""
    bl_idname = "latk_button.strokesfrommesh"
    bl_label = "Strokes from Mesh"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        latk_settings = bpy.context.scene.latk_settings
        meshToGp(strokeLength=latk_settings.strokeLength, strokeGaps=latk_settings.strokeGaps, shuffleOdds=latk_settings.shuffleOdds, spreadPoints=latk_settings.spreadPoints)
        return {'FINISHED'}

class Latk_Button_PointsToggle(bpy.types.Operator):
    """Toggle points mode on"""
    bl_idname = "latk_button.pointstoggle"
    bl_label = "Points"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        latk_settings = bpy.context.scene.latk_settings
        togglePoints()
        return {'FINISHED'}

'''
class Latk_Button_BakeSelected(bpy.types.Operator):
    """Bake selected curves to exportable meshes"""
    bl_idname = "latk_button.bakeselected"
    bl_label = "Curve Bake"
    bl_options = {'UNDO'}
    
    def execute(self, context):goo
        latk_settings = bpy.context.scene.latk_settings
        decimateAndBake(_decimate=latk_settings.decimate)
        return {'FINISHED'}
'''

class Latk_Button_BakeAllCurves(bpy.types.Operator):
    """Bake curves to exportable meshes"""
    bl_idname = "latk_button.bakeall"
    bl_label = "Curves Bake"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        latk_settings = bpy.context.scene.latk_settings
        target = s()
        if (len(target) < 1): # all
            bakeAllCurvesToMesh(_decimate=latk_settings.decimate)
        else: # selected
            decimateAndBake(_decimate=latk_settings.decimate)
        return {'FINISHED'}

class Latk_Button_BakeAnim(bpy.types.Operator):
    """Bake keyframes with constraints"""
    bl_idname = "latk_button.bakeanim"
    bl_label = "Anim Bake"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        target = s()
        if (len(target) < 1): # all
            target = bpy.data.objects
        toBake = []
        for obj in target:
            if (len(obj.constraints) > 0):
                toBake.append(obj)
        if (len(toBake) > 0):
            bakeAnimConstraint(target=toBake)
        return {'FINISHED'}

class Latk_Button_Gpmesh_SingleFrame(bpy.types.Operator):
    """Mesh a single frame. Great for fast previews"""
    bl_idname = "latk_button.gpmesh_singleframe"
    bl_label = "Mesh Frame"
    bl_options = {'UNDO'}

    def execute(self, context):
        latk_settings = bpy.context.scene.latk_settings
        gpMesh(_singleFrame=True, _animateFrames=False, _thickness=latk_settings.thickness, _remesh=latk_settings.remesh_mode.lower(), _resolution=latk_settings.resolution, _bevelResolution=latk_settings.bevelResolution, _decimate=latk_settings.decimate, _bakeMesh=latk_settings.bakeMesh, _joinMesh=latk_settings.bakeMesh, _saveLayers=False, _vertexColorName=latk_settings.vertexColorName)
        return {'FINISHED'}

class Latk_Button_Dn(bpy.types.Operator):
    """Delete all Latk-generated curves and meshes"""
    bl_idname = "latk_button.dn"
    bl_label = "Delete All"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        deleteName("latk")
        return {'FINISHED'}

class Latk_Button_Splf(bpy.types.Operator):
    """Split GP stroke layers. Layers with fewer frames mesh faster"""
    bl_idname = "latk_button.splf"
    bl_label = "Split Layers"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        latk_settings = bpy.context.scene.latk_settings
        splitLayersAboveFrameLimit(latk_settings.numSplitFrames)
        return {'FINISHED'}

class Latk_Button_MtlShader(bpy.types.Operator):
    """Transfer parameters between Principled and Diffuse (default) shaders"""
    bl_idname = "latk_button.mtlshader"
    bl_label = "Shader"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        latk_settings = bpy.context.scene.latk_settings
        if (latk_settings.material_set_mode.lower() == "all"):
            setAllMtlShader(latk_settings.material_shader_mode.lower())
        elif (latk_settings.material_set_mode.lower() == "selected"):
            setMtlShader(latk_settings.material_shader_mode.lower())
        return {'FINISHED'}

# ~ ~ ~ 

def menu_func_import(self, context):
    self.layout.operator(ImportLatk.bl_idname, text="Latk Animation (.latk, .json)")
    #~
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_TiltBrush == True):
        self.layout.operator(ImportTiltBrush.bl_idname, text="Latk - Tilt Brush (.tilt, .json)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_SculptrVR == True):
        self.layout.operator(ImportSculptrVR.bl_idname, text="Latk - SculptrVR (.csv)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_ASC == True):
        self.layout.operator(ImportASC.bl_idname, text="Latk - ASC (.asc, .xyz)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_GML == True):
        self.layout.operator(ImportGml.bl_idname, text="Latk - GML (.gml)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_Painter == True):
        self.layout.operator(ImportPainter.bl_idname, text="Latk - Corel Painter (.txt)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_Norman == True):
        self.layout.operator(ImportNorman.bl_idname, text="Latk - NormanVR (.json)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_VRDoodler == True):
        self.layout.operator(ImportVRDoodler.bl_idname, text="Latk - VRDoodler (.obj)")

def menu_func_export(self, context):
    self.layout.operator(ExportLatk.bl_idname, text="Latk Animation (.latk)")
    self.layout.operator(ExportLatkJson.bl_idname, text="Latk Animation (.json)")
    #~
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_SculptrVR == True):
        self.layout.operator(ExportSculptrVR.bl_idname, text="Latk - SculptrVR (.csv)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_ASC == True):
        self.layout.operator(ExportASC.bl_idname, text="Latk - ASC (.asc)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_GML == True):
        self.layout.operator(ExportGml.bl_idname, text="Latk - GML (.gml)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_Painter == True):
        self.layout.operator(ExportPainter.bl_idname, text="Latk - Corel Painter (.txt)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_SVG == True):
        self.layout.operator(ExportSvg.bl_idname, text="Latk - SVG SMIL (.svg)")
    if (bpy.context.user_preferences.addons[__name__].preferences.extraFormats_FBXSequence == True):
        self.layout.operator(ExportFbxSequence.bl_idname, text="Latk - FBX Sequence (.fbx)")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.latk_settings = PointerProperty(type=LatkProperties)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

    bpy.types.Scene.freestyle_gpencil_export = PointerProperty(type=FreestyleGPencil)
    
    parameter_editor.callbacks_lineset_pre.append(export_fill)
    parameter_editor.callbacks_lineset_post.append(export_stroke)

def unregister():
    bpy.utils.unregister_module(__name__)

    del bpy.types.Scene.latk_settings
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

    del bpy.types.Scene.freestyle_gpencil_export
    
    parameter_editor.callbacks_lineset_pre.remove(export_fill)
    parameter_editor.callbacks_lineset_post.remove(export_stroke)

if __name__ == "__main__":
    register()

# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

# 9 of 10. TILT BRUSH binary reader -- use of Blender Python API stops here.

# Copyright 2016 Google Inc. All Rights Reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#         http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Reads and writes .tilt files. The main export is 'class Tilt'."""

'''
import os
import math
import json
import uuid
import struct
import contextlib
from collections import defaultdict
import io

__all__ = ('Tilt', 'Sketch', 'Stroke', 'ControlPoint',
                     'BadTilt', 'BadMetadata', 'MissingKey')
'''

# Format characters are as for struct.pack/unpack, with the addition of
# '@' which is a 4-byte-length-prefixed data blob.
STROKE_EXTENSION_BITS = {
    0x1: ('flags', 'I'),
    0x2: ('scale', 'f'),
    'unknown': lambda bit: ('stroke_ext_%d' % math.log(bit, 2),
                                                    'I' if (bit & 0xffff) else '@')
}

STROKE_EXTENSION_BY_NAME = dict(
    (info[0], (bit, info[1]))
    for (bit, info) in STROKE_EXTENSION_BITS.items()
    if bit != 'unknown'
)

CONTROLPOINT_EXTENSION_BITS = {
    0x1: ('pressure', 'f'),
    0x2: ('timestamp', 'I'),
    'unknown': lambda bit: ('cp_ext_%d' % math.log(bit, 2), 'I')
}

#
# Internal utils
#

class memoized_property(object):
    """Modeled after @property, but runs the getter exactly once"""
    def __init__(self, fget):
        self.fget = fget
        self.name = fget.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return None
        value = self.fget(instance)
        # Since this isn't a data descriptor (no __set__ method),
        # instance attributes take precedence over the descriptor.
        setattr(instance, self.name, value)
        return value

class binfile(object):
    # Helper for parsing
    def __init__(self, inf):
        self.inf = inf

    def read(self, n):
        return self.inf.read(n)

    def write(self, data):
        return self.inf.write(data)

    def read_length_prefixed(self):
        n, = self.unpack("<I")
        return self.inf.read(n)

    def write_length_prefixed(self, data):
        self.pack("<I", len(data))
        self.inf.write(data)

    def unpack(self, fmt):
        n = struct.calcsize(fmt)
        data = self.inf.read(n)
        return struct.unpack(fmt, data)

    def pack(self, fmt, *args):
        data = struct.pack(fmt, *args)
        return self.inf.write(data)

class BadTilt(Exception): pass
class BadMetadata(BadTilt): pass
class MissingKey(BadMetadata): pass

def validate_metadata(dct):
    def lookup(xxx_todo_changeme, key):
        (path, parent) = xxx_todo_changeme
        child_path = '%s.%s' % (path, key)
        if key not in parent:
            raise MissingKey('Missing %s' % child_path)
        return (child_path, parent[key])
    def check_string(xxx_todo_changeme1):
        (path, val) = xxx_todo_changeme1
        if not isinstance(val, str):
            raise BadMetadata('Not string: %s' % path)
    def check_float(xxx_todo_changeme2):
        (path, val) = xxx_todo_changeme2
        if not isinstance(val, (float, int)):
            raise BadMetadata('Not number: %s' % path)
    def check_array(xxx_todo_changeme3, desired_len=None, typecheck=None):
        (path, val) = xxx_todo_changeme3
        if not isinstance(val, (list, tuple)):
            raise BadMetadata('Not array: %s' % path)
        if desired_len and len(val) != desired_len:
            raise BadMetadata('Not length %d: %s' % (desired_len, path))
        if typecheck is not None:
            for i, child_val in enumerate(val):
                child_path = '%s[%s]' % (path, i)
                typecheck((child_path, child_val))
    def check_guid(xxx_todo_changeme4):
        (path, val) = xxx_todo_changeme4
        try:
            uuid.UUID(val)
        except Exception as e:
            raise BadMetadata('Not UUID: %s %s' % (path, e))
    def check_xform(pathval):
        check_array(lookup(pathval, 'position'), 3, check_float)
        check_array(lookup(pathval, 'orientation'), 4, check_float)

    root = ('metadata', dct)
    try: check_xform(lookup(root, 'ThumbnailCameraTransformInRoomSpace'))
    except MissingKey: pass
    try: check_xform(lookup(root, 'SceneTransformInRoomSpace'))
    except MissingKey: pass
    try: check_xform(lookup(root, 'CanvasTransformInSceneSpace'))
    except MissingKey: pass
    check_array(lookup(root, 'BrushIndex'), None, check_guid)
    check_guid(lookup(root, 'EnvironmentPreset'))
    if 'Authors' in dct:
        check_array(lookup(root, 'Authors'), None, check_string)

#
# External
#

class Tilt(object):
    """Class representing a .tilt file. Attributes:
        .sketch         A tilt.Sketch instance. NOTE: this is read lazily.
        .metadata     A dictionary of data.

    To modify the sketch, see XXX.
    To modify the metadata, see mutable_metadata()."""
    @staticmethod
    @contextlib.contextmanager
    def as_directory(tilt_file):
        """Temporarily convert *tilt_file* to directory format."""
        if os.path.isdir(tilt_file):
            yield Tilt(tilt_file)
        else:
            import tiltbrush.unpack as unpack
            compressed = unpack.convert_zip_to_dir(tilt_file)
            try:
                yield Tilt(tilt_file)
            finally:
                unpack.convert_dir_to_zip(tilt_file, compressed)

    @staticmethod
    def iter(directory):
        for r,ds,fs in os.walk(directory):
            for f in ds+fs:
                if f.endswith('.tilt'):
                    try:
                        yield Tilt(os.path.join(r,f))
                    except BadTilt:
                        pass

    def __init__(self, filename):
        self.filename = filename
        self._sketch = None                    # lazily-loaded
        '''
        with self.subfile_reader('metadata.json') as inf:
            self.metadata = json.load(inf)
            try:
                validate_metadata(self.metadata)
            except BadMetadata as e:
                print('WARNING: %s' % e)
        '''

    def write_sketch(self):
        if False:
            # Recreate BrushIndex. Not tested and not strictly necessary, so not enabled
            old_index_to_brush = list(self.metadata['BrushIndex'])
            old_brushes = set( old_index_to_brush )
            new_brushes = set( old_index_to_brush[s.brush_idx] for s in self.sketch.strokes )
            if old_brushes != new_brushes:
                new_index_to_brush = sorted(new_brushes)
                brush_to_new_index = dict( (b, i) for (i, b) in enumerate(new_index_to_brush) )
                old_index_to_new_index = list(map(brush_to_new_index.get, old_index_to_brush))
                for stroke in self.sketch.strokes:
                    stroke.brush_idx = brush_to_new_index[old_index_to_brush[stroke.brush_idx]]
                with self.mutable_metadata() as dct:
                    dct['BrushIndex'] = new_index_to_brush

        self.sketch.write(self)

    @contextlib.contextmanager
    def subfile_reader(self, subfile):
        if os.path.isdir(self.filename):
            with file(os.path.join(self.filename, subfile), 'rb') as inf:
                yield inf
        else:
            from zipfile import ZipFile
            with ZipFile(self.filename, 'r') as inzip:
                with inzip.open(subfile) as inf:
                    yield inf

    @contextlib.contextmanager
    def subfile_writer(self, subfile):
        # Kind of a large hammer, but it works
        if os.path.isdir(self.filename):
            with file(os.path.join(self.filename, subfile), 'wb') as outf:
                yield outf
        else:
            with Tilt.as_directory(self.filename) as tilt2:
                with tilt2.subfile_writer(subfile) as outf:
                    yield outf

    @contextlib.contextmanager
    def mutable_metadata(self):
        """Return a mutable copy of the metadata.
        When the context manager exits, the updated metadata will
        validated and written to disk."""
        import copy
        mutable_dct = copy.deepcopy(self.metadata)
        yield mutable_dct
        validate_metadata(mutable_dct)
        if self.metadata != mutable_dct:
            # Copy into self.metadata, preserving topmost reference
            for k in list(self.metadata.keys()):
                del self.metadata[k]
            for k,v in mutable_dct.items():
                self.metadata[k] = copy.deepcopy(v)
                
            new_contents = json.dumps(
                mutable_dct, ensure_ascii=True, allow_nan=False,
                indent=2, sort_keys=True, separators=(',', ': '))
            with self.subfile_writer('metadata.json') as outf:
                outf.write(new_contents)

    @memoized_property
    def sketch(self):
        # Would be slightly more consistent semantics to do the data read
        # in __init__, and parse it here; but this is probably good enough.
        return Sketch(self)

def _make_ext_reader(ext_bits, ext_mask):
    """Helper for Stroke and ControlPoint parsing.
    Returns:
    - function reader(file) -> list<extension values>
    - function writer(file, values)
    - dict mapping extension_name -> extension_index
    """
    infos = []
    while ext_mask:
        bit = ext_mask & ~(ext_mask-1)
        ext_mask = ext_mask ^ bit
        try: info = ext_bits[bit]
        except KeyError: info = ext_bits['unknown'](bit)
        infos.append(info)

    if len(infos) == 0:
        return (lambda f: [], lambda f,vs: None, {})

    fmt = '<' + ''.join(info[1] for info in infos)
    names = [info[0] for info in infos]
    if '@' in fmt:
        # struct.unpack isn't general enough to do the job
        print(fmt, names, infos)
        fmts = ['<'+info[1] for info in infos]
        def reader(f, fmts=fmts):
            values = [None] * len(fmts)
            for i,fmt in enumerate(fmts):
                if fmt == '<@':
                    nbytes, = struct.unpack('<I', f.read(4))
                    values[i] = f.read(nbytes)
                else:
                    values[i], = struct.unpack(fmt, f.read(4))
    else:
        def reader(f, fmt=fmt, nbytes=len(infos)*4):
            values = list(struct.unpack(fmt, f.read(nbytes)))
            return values

    def writer(f, values, fmt=fmt):
        return f.write(struct.pack(fmt, *values))

    lookup = dict( (name,i) for (i,name) in enumerate(names) )
    return reader, writer, lookup

def _make_stroke_ext_reader(ext_mask, memo={}):
    try:
        ret = memo[ext_mask]
    except KeyError:
        ret = memo[ext_mask] = _make_ext_reader(STROKE_EXTENSION_BITS, ext_mask)
    return ret

def _make_cp_ext_reader(ext_mask, memo={}):
    try:
        ret = memo[ext_mask]
    except KeyError:
        ret = memo[ext_mask] = _make_ext_reader(CONTROLPOINT_EXTENSION_BITS, ext_mask)
    return ret

class Sketch(object):
    """Stroke data from a .tilt file. Attributes:
        .strokes        List of tilt.Stroke instances
        .filename     Filename if loaded from file, but usually None
        .header         Opaque header data"""
    def __init__(self, source):
        """source is either a file name, a file-like instance, or a Tilt instance."""
        if isinstance(source, Tilt):
            with source.subfile_reader('data.sketch') as inf:
                self.filename = None
                self._parse(binfile(inf))
        elif hasattr(source, 'read'):
            self.filename = None
            self._parse(binfile(source))
        else:
            self.filename = source
            with file(source, 'rb') as inf:
                self._parse(binfile(inf))

    def write(self, destination):
        """destination is either a file name, a file-like instance, or a Tilt instance."""
        tmpf = io.StringIO()
        self._write(binfile(tmpf))
        data = tmpf.getvalue()

        if isinstance(destination, Tilt):
            with destination.subfile_writer('data.sketch') as outf:
                outf.write(data)
        elif hasattr(destination, 'write'):
            destination.write(data)
        else:
            with file(destination, 'wb') as outf:
                outf.write(data)

    def _parse(self, b):
        # b is a binfile instance
        # mutates self
        self.header = list(b.unpack("<3I"))
        self.additional_header = b.read_length_prefixed()
        (num_strokes, ) = b.unpack("<i")
        assert 0 <= num_strokes < 300000, num_strokes
        self.strokes = [Stroke.from_file(b) for i in range(num_strokes)]

    def _write(self, b):
        # b is a binfile instance.
        b.pack("<3I", *self.header)
        b.write_length_prefixed(self.additional_header)
        b.pack("<i", len(self.strokes))
        for stroke in self.strokes:
            stroke._write(b)

class Stroke(object):
    """Data for a single stroke from a .tilt file. Attributes:
        .brush_idx            Index into Tilt.metadata['BrushIndex']; tells you the brush GUID
        .brush_color        RGBA color, as 4 floats in the range [0, 1]
        .brush_size         Brush size, in decimeters, as a float. Multiply by
                                        get_stroke_extension('scale') to get a true size.
        .controlpoints    List of tilt.ControlPoint instances.

        .flags                    Wrapper around get/set_stroke_extension('flags')
        .scale                    Wrapper around get/set_stroke_extension('scale')

    Also see has_stroke_extension(), get_stroke_extension()."""
    @classmethod
    def from_file(cls, b):
        inst = cls()
        inst._parse(b)
        return inst

    def clone(self):
        """Returns a deep copy of the stroke."""
        inst = self.shallow_clone()
        inst.controlpoints = list(map(ControlPoint.clone, inst.controlpoints))
        return inst

    def __getattr__(self, name):
        if name in STROKE_EXTENSION_BY_NAME:
            try:
                return self.get_stroke_extension(name)
            except LookupError:
                raise AttributeError("%s (extension attribute)" % name)
        return super(Stroke, self).__getattr__(name)

    def __setattr__(self, name, value):
        if name in STROKE_EXTENSION_BY_NAME:
            return self.set_stroke_extension(name, value)
        return super(Stroke, self).__setattr__(name, value)

    def __delattr__(self, name):
        if name in STROKE_EXTENSION_BY_NAME:
            try:
                self.delete_stroke_extension(name)
                return
            except LookupError:
                raise AttributeError("%s (extension attribute)" % name)
        return super(Stroke, self).__delattr__(name)

    def shallow_clone(self):
        """Clone everything but the control points themselves."""
        inst = self.__class__()
        for attr in ('brush_idx', 'brush_color', 'brush_size', 'stroke_mask', 'cp_mask',
                                 'stroke_ext_writer', 'stroke_ext_lookup', 'cp_ext_writer', 'cp_ext_lookup'):
            setattr(inst, attr, getattr(self, attr))
        inst.extension = list(self.extension)
        inst.controlpoints = list(self.controlpoints)
        return inst

    def _parse(self, b):
        # b is a binfile instance
        (self.brush_idx, ) = b.unpack("<i")
        self.brush_color = b.unpack("<4f")
        (self.brush_size, self.stroke_mask, self.cp_mask) = b.unpack("<fII")
        stroke_ext_reader, self.stroke_ext_writer, self.stroke_ext_lookup = \
                _make_stroke_ext_reader(self.stroke_mask)
        self.extension = stroke_ext_reader(b)

        cp_ext_reader, self.cp_ext_writer, self.cp_ext_lookup = \
                _make_cp_ext_reader(self.cp_mask)
        
        (num_cp, ) = b.unpack("<i")
        assert num_cp < 10000, num_cp

        # Read the raw data up front, but parse it lazily
        bytes_per_cp = 4 * (3 + 4 + len(self.cp_ext_lookup))
        self._controlpoints = (cp_ext_reader, num_cp, b.inf.read(num_cp * bytes_per_cp))

    @memoized_property
    def controlpoints(self):
        (cp_ext_reader, num_cp, raw_data) = self.__dict__.pop('_controlpoints')
        b = binfile(io.BytesIO(raw_data))
        return [ControlPoint.from_file(b, cp_ext_reader) for i in range(num_cp)]

    def has_stroke_extension(self, name):
        """Returns true if this stroke has the requested extension data.
        
        The current stroke extensions are:
            scale         Non-negative float. The size of the player when making this stroke.
                                Multiply this by the brush size to get a true stroke size."""
        return name in self.stroke_ext_lookup

    def get_stroke_extension(self, name):
        """Returns the requested extension stroke data.
        Raises LookupError if it doesn't exist."""
        idx = self.stroke_ext_lookup[name]
        return self.extension[idx]

    def set_stroke_extension(self, name, value):
        """Sets stroke extension data.
        This method can be used to add extension data."""
        idx = self.stroke_ext_lookup.get(name, None)
        if idx is not None:
            self.extension[idx] = value
        else:
            # Convert from idx->value to name->value
            name_to_value = dict( (name, self.extension[idx])
                                                        for (name, idx) in self.stroke_ext_lookup.items() )
            name_to_value[name] = value

            bit, exttype = STROKE_EXTENSION_BY_NAME[name]
            self.stroke_mask |= bit
            _, self.stroke_ext_writer, self.stroke_ext_lookup = \
                    _make_stroke_ext_reader(self.stroke_mask)
            
            # Convert back to idx->value
            self.extension = [None] * len(self.stroke_ext_lookup)
            for (name, idx) in self.stroke_ext_lookup.items():
                self.extension[idx] = name_to_value[name]
                                                                                                                    
    def delete_stroke_extension(self, name):
        """Remove stroke extension data.
        Raises LookupError if it doesn't exist."""
        idx = self.stroke_ext_lookup[name]

        # Convert from idx->value to name->value
        name_to_value = dict( (name, self.extension[idx])
                                                    for (name, idx) in self.stroke_ext_lookup.items() )
        del name_to_value[name]

        bit, exttype = STROKE_EXTENSION_BY_NAME[name]
        self.stroke_mask &= ~bit
        _, self.stroke_ext_writer, self.stroke_ext_lookup = \
                _make_stroke_ext_reader(self.stroke_mask)

        # Convert back to idx->value
        self.extension = [None] * len(self.stroke_ext_lookup)
        for (name, idx) in self.stroke_ext_lookup.items():
            self.extension[idx] = name_to_value[name]

    def has_cp_extension(self, name):
        """Returns true if control points in this stroke have the requested extension data.
        All control points in a stroke are guaranteed to use the same set of extensions.

        The current control point extensions are:
            timestamp                 In seconds
            pressure                    From 0 to 1"""
        return name in self.cp_ext_lookup

    def get_cp_extension(self, cp, name):
        """Returns the requested extension data, or raises LookupError if it doesn't exist."""
        idx = self.cp_ext_lookup[name]
        return cp.extension[idx]

    def _write(self, b):
        b.pack("<i", self.brush_idx)
        b.pack("<4f", *self.brush_color)
        b.pack("<fII", self.brush_size, self.stroke_mask, self.cp_mask)
        self.stroke_ext_writer(b, self.extension)
        b.pack("<i", len(self.controlpoints))
        for cp in self.controlpoints:
            cp._write(b, self.cp_ext_writer)

class ControlPoint(object):
    """Data for a single control point from a stroke. Attributes:
        .position        Position as 3 floats. Units are decimeters.
        .orientation Orientation of controller as a quaternion (x, y, z, w)."""
    @classmethod
    def from_file(cls, b, cp_ext_reader):
        # b is a binfile instance
        # reader reads controlpoint extension data from the binfile
        inst = cls()
        inst.position = list(b.unpack("<3f"))
        inst.orientation = list(b.unpack("<4f"))
        inst.extension = cp_ext_reader(b)
        return inst

    def clone(self):
        inst = self.__class__()
        for attr in ('position', 'orientation', 'extension'):
            setattr(inst, attr, list(getattr(self, attr)))
        return inst

    def _write(self, b, cp_ext_writer):
        p = self.position; o = self.orientation
        b.pack("<7f", p[0], p[1], p[2], o[0], o[1], o[2], o[3])
        cp_ext_writer(b, self.extension)

# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * *

# END

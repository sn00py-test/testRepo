#-----------------------------------------------------------------------------
# Name:        railwayAgent.py
#
# Purpose:     This module is the agents module to init different items in the 
#              railway system map. All the items on the Map are agent objects, each 
#              agent's update() function is a self-driven function to update the 
#              item's state.
# 
# Author:      Yuancheng Liu
#
# Version:     v0.1.2
# Created:     2023/05/26
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import math
import random
from random import randint
import railwayPWSimuGlobal as gv

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class AgentTarget(object):
    """ Create a agent target to generate all the elements in the metro system, 
        all the other 'things' in the system will be inheritance from this module.
    """
    def __init__(self, parent, tgtID, pos, tType):
        self.parent = parent
        self.id = tgtID
        self.pos = pos      # target init position on the map.
        self.tType = tType  # 2 letter agent types.<railwayGlobal.py>

#--AgentTarget-----------------------------------------------------------------
# Define all the get() functions here:

    def getID(self):
        return self.id

    def getPos(self):
        return self.pos

    def getType(self):
        return self.tType

#--AgentTarget-----------------------------------------------------------------
    def checkNear(self, posX, posY, threshold):
        """ Check whether a point is near the selected point with the 
            input threshold value (unit: pixel).
        """
        dist = math.sqrt((self.pos[0] - posX)**2 + (self.pos[1] - posY)**2)
        return dist <= threshold

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class agentEnv(AgentTarget):
    """ The environment Item shown on the map such as building, IOT, camera."""
    def __init__(self, parent, tgtID, pos, wxBitMap, size ,tType=gv.ENV_TYPE):
        super().__init__(parent, tgtID, pos, tType)
        # build Icon: https://www.freepik.com/premium-vector/isometric-modern-supermarket-buildings-set_10094282.htm
        self.bitmap = wxBitMap
        self.size = size
        self.color = None   
        self.linkList = None

#-----------------------------------------------------------------------------
# Define all the get() functions here:
    def getColor(self):
        return self.color
    
    def getLink(self):
        return self.linkList 

    def getSize(self):
        return self.size

    def getWxBitmap(self):
        return self.bitmap
    
#-----------------------------------------------------------------------------
# Define all the set() functions here:

    def setColor(self, color):
        self.color = color

    def setLinkList(self, linkList):
        self.linkList = linkList

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class AgentJunction(AgentTarget):
    """ The temporary test junction agent to check the train collision. Currently 
        the junction only support two tracks. YC: will implement multiple trasks (> 3)
        junctions. 
        The input parameter parent needs to be a <MapMgr> obj.
    """
    def __init__(self, parent, tgtID, pos, TrackID1, TrackID2):
        super().__init__(parent, tgtID, pos, gv.JUNCTION_TYPE)
        self.trackid1 = TrackID1
        self.trackid2 = TrackID2
        self.detectState = {
            self.trackid1 : None,
            self.trackid2 : None,
        }
        self.signalList = None

    def _checkTrainEnter(self, trainArea, threshold=15):
        """ Check whether a train has enter the junction."""
        u,d,l,r = trainArea
        x, y = self.getPos()
        if (l-threshold <= x <= r+threshold) and (u-threshold <= y <= d+threshold):
            return True
        return False

#-----------------------------------------------------------------------------
# Define all the get() functions here:
    def getCollition(self):
        if None in self.detectState.values(): return False
        return True

    def getCollitionState(self):
        return self.detectState

#-----------------------------------------------------------------------------
# Define all the set() functions here:

    def setSignalList(self, signalList):
        self.signalList = signalList

#-----------------------------------------------------------------------------
    def handleDeadLock(self):
        """ Check whether there are 2 trains triggered the junction's signal at the 
            same time.
            YC: current this function is not used as we set the train priority. But 
            we may use this function in the future. 
        """
        noDeadLock = False
        if self.signalList:
            for i, signal in enumerate(self.signalList):
                if not signal.getState():
                    noDeadLock = True
                break
            if noDeadLock == False:
                self.signalList[1].startManualOverrideOnDeadlock()

#-----------------------------------------------------------------------------
    def updateState(self):
        """ Update the current station of a junction """
        if self.parent:
            for trackid in self.detectState.keys():
                self.detectState[trackid] = None
                for i, train in enumerate(self.parent.getTrains(trackID=trackid)):
                    if self._checkTrainEnter(train.getTrainArea()):
                        self.detectState[trackid] = i
                        break

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class AgentSensors(AgentTarget):
    """ The sensors set to show the sensors detection state."""
    def __init__(self, parent, idx, pos):
        AgentTarget.__init__(self, parent, idx, pos, gv.SENSOR_TYPE)
        self.sensorsCount = len(self.pos)
        self.stateList = [0]*self.sensorsCount # elements state: 1-triggered, 0-not triggered.

#-----------------------------------------------------------------------------
# Define all the get() functions here:

    def getActiveIndex(self):
        """ Return a list of all the actived sensors' index."""
        idxList = []
        for i, val in enumerate(self.pos):
            if val: idxList.append(i)
        return idxList

    def getSensorCount(self):
        return self.sensorsCount

    def getSensorState(self, idx):
        return self.stateList[idx]

    def getSensorsState(self):
        return self.stateList

#-----------------------------------------------------------------------------
# Define all the set() functions here:

    def setSensorState(self, idx, state):
        """ Set one sensor's state with an index in the sensor list.
            Args:
                idx (int): sensor index.
                state (int): 0/1
        """
        if idx >= self.sensorsCount: return False
        self.stateList[idx] = state
        return True

#-----------------------------------------------------------------------------
    def updateActive(self, trainList):
        """ Update the sensor triggered state based on the input trains position.
            Args:
                trainList (list(<AgentTrain>)): a list of AgentTrain obj.
        """
        for i in range(self.sensorsCount):
            self.stateList[i] = 0
            x, y = self.pos[i]
            for trainObj in trainList:
                (u, d, l, r) = trainObj.getTrainArea()
                if l <= x <= r and u <= y <= d: 
                    self.stateList[i] = 1
                    break
        
#-----------------------------------------------------------------------------
class AgentStation(AgentTarget):
    """ One train station obj. TODO: this agent is just for testing as it can only 
        sense/check on pos on one line. Will add sense multiple point on different 
        tracks later.
    """
    def __init__(self, parent, tgtID, pos, layout=gv.LAY_H, signalLayout=gv.LAY_U):
        super().__init__(parent, tgtID, pos, gv.STATION_TYPE)
        self.dockCount = gv.gDockTime if gv.gDockTime else random.randint(3, 10)
        # defines the dock time by refresh cycle (capped at 20)
        self.emptyCount = gv.gMinTrainDist # defines how long the station has been empty for by refresh cycle 
        self.trainList = []
        self.dockState = False
        self.signalState = False # Train signal to make next train waiting outise the station when some train is docking.
        self.layout = layout
        self.labelPos = (-25, -28) # default delta label location on the map
        self.signalPos = self._getSingalPos(signalLayout)

    def _getSingalPos(self, layout):
        x, y = self.getPos()
        if layout == gv.LAY_U:
            return(x, y-40)
        elif layout == gv.LAY_D:
            return(x, y+40)
        elif layout == gv.LAY_L:
            return(x-40, y)
        elif layout == gv.LAY_R:
            return(x+40, y)
        gv.gDebugPrint("_getSingalPos(): The input layout is no valid: %s" %str(layout), logType=gv.LOG_WARN)
        return None    
    
    def _checkNearSignal(self, pos, threshold = 20):
        if self.signalPos is None: 
            return False
        dist = math.sqrt((self.signalPos[0] - pos[0])**2 + (self.signalPos[1] - pos[1])**2)
        return dist <= threshold

#-----------------------------------------------------------------------------
# Define all the get() functions here:

    def getDockState(self):
        return self.dockState
    
    def getSignalState(self):
        return self.signalState

    def getEmptyCount(self):
        return self.emptyCount    

    def getLayout(self):
        return self.layout

    def getLabelPos(self):
        return self.labelPos
    
    def getSignalPos(self):
        return self.signalPos

#-----------------------------------------------------------------------------
# Define all the set() functions here:

    def setCheckTrains(self, TrainList):
        """ Set the trains may dock in the station.
            Args:
                TrainList (list(<AgentTrain>)):  list of AgentTrain obj.
        """
        self.trainList = TrainList

    def setDockState(self, dockState):
        self.dockState = dockState

    def setSignalState(self, signalState):
        self.signalState = signalState

    def setlabelPos(self, pos):
        self.labelPos = pos

    def setTrainDockCount(self, dockCount):
        self.dockCount = dockCount

    def setEmptyCount(self, count):
        self.emptyCount = count

#-----------------------------------------------------------------------------
    def updateTrainsDock(self):
        if len(self.trainList) == 0: return
        for train in self.trainList:
            # Check Whether the train can dock inside the station.
            midPt = train.getTrainPos(idx=2)
            if self.checkNear(midPt[0], midPt[1], 5):
                self.dockState = True
                if gv.gTestMD: self.setSignalState(True)
                # print("Station: " + str(self.getID()) + " - " + str(self.emptyCount))
                # Code to avoid train density high, current customer don't want this function, temporary disabled.
                # if train.getDockCount() == 0: 
                #     distFromFtTrain = self.emptyCount
                #     if distFromFtTrain >= gv.gMinTrainDist:
                #         train.setDockCount(self.dockCount)
                #     else:
                #         minDockCount = gv.gMinTrainDist - distFromFtTrain
                #         train.setDockCount(max(minDockCount, self.dockCount))
                #     # Reset empty count when station is occupied
                #     self.emptyCount = 0
                if train.getDockCount() == 0: train.setDockCount(self.dockCount)
                return
            # Check whether the train need to be stopped by the station signal
            headPt = train.getTrainPos(idx=0) 
            if self._checkNearSignal(headPt):
                train.setWaiting(self.signalState) 
        self.dockState = False
        if gv.gTestMD: self.setSignalState(False)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class AgentSignal(AgentTarget):
    def __init__(self, parent, tgtID, pos, dir=gv.LAY_U, tType=gv.SINGAL_TYPE):
        """ One signal object to control whether a train can pass / be-blocked at 
            the intersection. 
        Args:
            parent (_type_): _description_
            tgtID (_type_): _description_
            pos (_type_): _description_
            dir (int, optional): _description_. Defaults to 0-up, 1-down, 2-left, 3 right.
            tType (_type_, optional): _description_. Defaults to gv.SINGAL_TYPE.
        """
        super().__init__(parent, tgtID, pos, tType)
        self.signalOn = False   # signal on (True): train stop, signal off(False): train pass  
        self.dir = dir          # signal indicator's direction on map. 0-up, 1-down, 2-left, 3-right
        self.triggerOnSenAgent = None 
        self.triggerOnIdxList = None
        self.triggerOffSenAgent = None
        self.triggerOffIdxList = None
        
#-----------------------------------------------------------------------------
# Define all the get() functions here:
    def getState(self):
        return self.signalOn

#-----------------------------------------------------------------------------
# Define all the set() functions here:

    def setTriggerOnSensors(self, sensorAgent, idxList):
        self.triggerOnSenAgent = sensorAgent
        self.triggerOnIdxList = idxList

    def setTriggerOffSensors(self, sensorAgent, idxList):
        self.triggerOffSenAgent = sensorAgent
        self.triggerOffIdxList = idxList

    def setState(self, state):
        self.signalOn = state

#-----------------------------------------------------------------------------
    def startManualOverrideOnDeadlock(self):
        """ YC: currently we will now use this function, but may be used in the
            future.
        """
        for idx in self.triggerOffIdxList:
            self.triggerOffSenAgent.setSensorState(idx, 1)
        for idx in self.triggerOnIdxList:
            self.triggerOnSenAgent.setSensorState(idx, 0)
        self.signalOn = False
    
#-----------------------------------------------------------------------------
    def updateSingalState(self):
        if self.signalOn:
            for idx in self.triggerOffIdxList:
                if self.triggerOffSenAgent.getSensorState(idx): 
                    self.signalOn = False
                    break
        else:
            for idx in self.triggerOnIdxList:
                if self.triggerOnSenAgent.getSensorState(idx):
                    self.signalOn =True
                    break

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class AgentTrain(AgentTarget):
    """ Create a train object with its init railway (track) array.

        input:  pos - The init position of the train head.
                railwayPts - list of railway points.(train will also run under 
                the list sequence.)
    """
    def __init__(self, parent, trainID, initPos, railwayPts, 
                 trainLen=5, trainSpeed=gv.gTrainDefSpeed, railwayType=gv.RAILWAY_TYPE_CYCLE):
        """ Init the train control agent object.
        Args:
            parent (_type_): parent object.
            trainID (_type_): train ID.
            pos (_type_): train initiate position. 
            railwayPts (_type_): the track path train will follow.
            trainLen (int, optional): _description_. Defaults to 5.
            railwayType (_type_, optional): _description_. Defaults to gv.RAILWAY_TYPE_CYCLE.
        """
        AgentTarget.__init__(self, parent, trainID, initPos, railwayType)
        self.railwayPts = railwayPts
        self.railwayType = railwayType
        self.trainLen = trainLen
        self.initPos = initPos
        self.dirs = [0]*5
        self.traindir = 1   # follow the railway point with increase order.
        self.trainDestList = self._getDestList(initPos)
        # Init the train head and tail points at the horizontal position.
        #self.pos = [[initPos[0] + 10*i, initPos[1]] for i in range(self.trainLen)]
        self.pos = self._buildTrainPos()
        self.trainSpeed = trainSpeed if gv.gTestMD else 0 # train speed: pixel/periodic loop
        self.dockCount = 0              # refersh cycle number of a train to stop in the station.
        self.isWaiting = False          # Train waiting at signal or out side the station.
        self.collsionFlg = False        # Flag to identify whether Train collsion happens.
        self.emgStop = False if gv.gTestMD else True   # emergency stop.

        self.rfrtSensorFlg = False # realworld detected the front train sensor state
        # real world train information dict.
        self.rwInfoDict = {
            'train_id': self.id,
            'power': 0,
            'speed': 0,
            'voltage': 0,
            'current': 0,
            'fsensor': self.rfrtSensorFlg,
        }

#-----------------------------------------------------------------------------
    def _buildTrainPos(self):
        x, y = self.initPos
        x1, y1 = self.railwayPts[self.trainDestList[0]]
        i = j = 0
        if x == x1: j = 1 if y > y1 else -1
        if y == y1: i = 1 if x > x1  else -1
        return [[x+10*i*k, y+10*j*k] for k in range(self.trainLen)]

#-----------------------------------------------------------------------------
    def _getDestList(self, initPos):
        """ Get the idx list of the target points (train destination) on the track 
            based on current train pos.
        """
        (x0, y0) = initPos
        for idx in range(len(self.railwayPts)-1):
            x1, y1 = self.railwayPts[idx]
            x2, y2 = self.railwayPts[idx+1]
            if x1 == x0 == x2 or y1 == y0 == y2: return [idx+1]*self.trainLen
        return [0]*self.trainLen
            
#-----------------------------------------------------------------------------
    def _getDirc(self, srcPt, destPt):
        """ Get the moving direction. (vector from src point to dest point)"""
        x = destPt[0] - srcPt[0]
        y = destPt[1] - srcPt[1]
        return math.pi-math.atan2(x, y) 

#-----------------------------------------------------------------------------
    def initDir(self, nextPtIdx):
        """ Init every train carriage's direction.(Currently not used)"""
        if nextPtIdx < len(self.railwayPts):
            self.trainDestList = [nextPtIdx]*len(self.pos)
            nextPt = self.railwayPts[nextPtIdx]
            for i in range(len(self.pos)):
                self.dirs[i] = self._getDirc(self.pos[i], nextPt)

#-----------------------------------------------------------------------------
    def changedir(self):
        """ Change the train running direction."""
        #print(self.trainDestList)
        self.traindir = -self.traindir
        for i in range(len(self.trainDestList)):
            element = self.trainDestList[i]
            self.trainDestList[i] = (element+self.traindir) % len(self.railwayPts)
        #print(self.trainDestList)        

#--AgentTrain------------------------------------------------------------------
    def checkNear(self, posX, posY, threshold):
        """ Overwrite the parent checknear function to check whether a point
            is near the train.
        """
        for pos in self.pos:
            dist = math.sqrt((pos[0] - posX)**2 + (pos[1] - posY)**2)
            if dist <= threshold: return True
        return False

    def checkTHsensor(self, posX, posY, threshold):
        """ Check the train head sensor detection."""
        pos = self.pos[0]
        dist = math.sqrt((pos[0] - posX)**2 + (pos[1] - posY)**2)
        return dist <= threshold

#--AgentTrain------------------------------------------------------------------
    def checkCollFt(self, frontTrain, threshold = 25):
        """ Check whether their is possible collision to the front train.
            Args:
                frontTrain (_type_): _description_
                threshold (int, optional): collision detection distance. Defaults to 20.
        """
        if self.isWaiting: return False
        ftTail = frontTrain.getTrainPos(idx=-1) # front train tail position.
        if self.checkNear(ftTail[0], ftTail[1], threshold):
            if self.trainSpeed >= 0 and self.dockCount==0:
                self.trainSpeed = 0
            self.rfrtSensorFlg = True
            return True # detected will be collision to the front train
        elif self.trainSpeed == 0 and self.dockCount <= 1:
            self.setTrainSpeed(10)
        self.rfrtSensorFlg = False
        return False

#--AgentTrain------------------------------------------------------------------
    def checkSignal(self, signalList):
        """ Check whether the train reach the signal position, if the signal is 
            on, stop the train to wait.
        """
        for singalObj in signalList:
            x, y = singalObj.getPos()
            if self.checkNear(x, y, 5) or self.checkTHsensor(x, y, 20):
                speed = 0 if singalObj.getState() else gv.gTrainDefSpeed
                self.setTrainSpeed(speed)
                break

#-----------------------------------------------------------------------------
# Define all the get() functions here:
    
    def getCollsionFlg(self):
        return self.collsionFlg

    def getDirs(self):
        return self.dirs 

    def getDockCount(self):
        return self.dockCount

    def getTrainArea(self):
        """ Get the area train covered on the map."""
        h, t = self.pos[0], self.pos[-1]
        left, right = min(h[0], t[0])-5, max(h[0], t[0])+5
        up, down = min(h[1], t[1])-5, max(h[1], t[1])+5
        return (up, down, left, right)

    def getTrainLength(self):
        return self.trainLen
    
    def getTrainPos(self, idx=None):
        if isinstance(idx, int) and idx < self.trainLen: return self.pos[idx]
        return self.pos

    def getTrainSpeed(self):
        return self.trainSpeed

    def getTrainRealInfo(self):
        """ Generate the trian's realworld information"""
        return self.rwInfoDict

    def getPowerState(self):
        return not (self.emgStop or self.collsionFlg)

    def getEmgStop(self):
        return self.emgStop

#-----------------------------------------------------------------------------
# Define all the set() functions here:

    def setCollsionFlg(self, state):
        self.collsionFlg = state
        if self.collsionFlg: self.setEmgStop(True)

    def setDockCount(self, count):
        self.dockCount = count
        self.trainSpeed =0

    def setEmgStop(self, emgStop):
        self.emgStop = emgStop
        self.trainSpeed = 0 if self.emgStop else gv.gTrainDefSpeed

    def setNextPtIdx(self, nextPtIdx):
        if nextPtIdx < len(self.railwayPts): 
            self.trainDestList = [nextPtIdx]*len(self.pos)

    def setRailWayPts(self, railwayPts):
        """ change the train's railway points list.(before train pass the fork)"""
        self.railwayPts = railwayPts

    def setTrainSpeed(self, speed):
        if self.emgStop: return
        self.trainSpeed = speed

    def setWaiting(self, waitFlg):
        if self.isWaiting == waitFlg: return
        self.isWaiting = waitFlg
        speed = 0 if waitFlg else gv.gTrainDefSpeed
        self.setTrainSpeed(speed)

#--AgentTrain------------------------------------------------------------------
    def resetTrain(self):
        """ reset the train to the init position."""
        self.trainDestList = self._getDestList(self.initPos)
        self.pos = self._buildTrainPos()
        self.emgStop = False
        self.collsionFlg = False
        self.isWaiting = False
        self.trainSpeed = gv.gTrainDefSpeed
        self.dockCount = 0
        self.rwInfoDict = {
            'train_id': self.id,
            'power': 0,
            'speed': 0,
            'voltage': 0,
            'current': 0,
            'fsensor': self.rfrtSensorFlg,
        }

#--AgentTrain------------------------------------------------------------------
    def updateTrainPos(self):
        """ Update the current train positions on the map. This function will be 
            called periodicly.
        """
        if self.emgStop or self.isWaiting: return
        # if dockCount == 1 also move the train to simulate the train start.
        if self.dockCount == 0 or self.dockCount ==1:
            # Train running on the railway:
            for i, trainPt in enumerate(self.pos):
                # The next railway point idx train going to approch.
                nextPtIdx = self.trainDestList[i]
                nextPt = self.railwayPts[nextPtIdx]
                dist = math.sqrt((trainPt[0] - nextPt[0])**2 + (trainPt[1] - nextPt[1])**2)
                if dist <= self.trainSpeed:
                    # Go to the next check point if the distance is less than 1 speed unit.
                    trainPt[0], trainPt[1] = nextPt[0], nextPt[1]
                    # Update the next train distination if the train already get its next dist.
                    nextPtIdx = self.trainDestList[i] = (nextPtIdx + self.traindir) % len(self.railwayPts)
                    nextPt = self.railwayPts[nextPtIdx]
                    #self.dirs[i] = self._getDirc(trainPt, nextPt)
                else:
                    # Move one speed unit.
                    scale = float(self.trainSpeed)/float(dist)
                    trainPt[0] += int((nextPt[0]-trainPt[0])*scale)
                    trainPt[1] += int((nextPt[1]-trainPt[1])*scale)
            if self.dockCount == 1: 
                self.dockCount -= 1
                if self.trainSpeed == 0: self.trainSpeed = gv.gTrainDefSpeed
        else:  # Train stop at the station.
            self.dockCount -= 1

#--AgentTrain------------------------------------------------------------------
    def updateRealWordInfo(self):
        """ Update the own real world information."""
        rSpeedVal = randint(0, 5) if self.trainSpeed == 0 else randint(56, 100)
        self.rwInfoDict['speed'] = rSpeedVal if self.getPowerState() else 0
        self.rwInfoDict['voltage'] = 750 - randint(0, 20) if self.getPowerState() else 0
        rCrtVal = randint(10, 30) if self.trainSpeed == 0 else randint(150, 200)
        self.rwInfoDict['current'] = rCrtVal if self.getPowerState() else 0
        self.rwInfoDict['fsensor'] = self.rfrtSensorFlg
        

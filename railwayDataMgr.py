#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        DataMgr.py
#
# Purpose:     Data manager module is used to control all the other data processing 
#              modules and store the interprocess/result data.
#
# Author:      Yuancheng Liu
#
# Created:     2023/06/07
# Version:     v_0.1.2
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import time
import json
import threading

import railwayPWSimuGlobal as gv
import Log
import udpCom

# Define all the local untility functions here:
#-----------------------------------------------------------------------------
def parseIncomeMsg(msg):
    """ parse the income message to tuple with 3 elements: request key, type and jsonString
        Args: msg (str): example: 'GET;dataType;{"user":"<username>"}'
    """
    req = msg.decode('UTF-8') if not isinstance(msg, str) else msg
    try:
        reqKey, reqType, reqJsonStr = req.split(';', 2)
        return (reqKey.strip(), reqType.strip(), reqJsonStr)
    except Exception as err:
        Log.error('parseIncomeMsg(): The income message format is incorrect.')
        Log.exception(err)
        return('','',json.dumps({}))

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class DataManager(threading.Thread):
    """ The data manager is a module running parallel with the main App UI thread 
        to handle the data-IO such as input the current sensor state to PLC and 
        accept PLC's coil out request.
    """
    def __init__(self, parent) -> None:
        threading.Thread.__init__(self)
        self.parent = parent
        self.terminate = False
        # Init a udp server to accept all the other plc module's data fetch/set request.
        self.server = udpCom.udpServer(None, gv.gUDPPort)
        self.daemon = True
        # init the local sensors data record dictionary
        self.sensorsDict = {
            'weline': None,
            'nsline': None, 
            'ccline': None,
            'mtline': None
        }
        # ccline have lowest piority: check whether other 2 line sensors are on
        self.priorityConfig = [('nsline',0), None, 
                               ('nsline', 4), None,
                               ('nsline', 2), None,
                               ('nsline', 2), None,
                               ('weline', 7, 9), None,
                               ('weline', 5, 11), None,
                               ('weline', 3, 13), None,
                               ('weline', 1, 15), None ]

        self.sensorPlcUpdateT = 0
        # init the local station data record dictionary
        self.stationsDict = {
            'weline': None,
            'nsline': None, 
            'ccline': None,
            'mtline': None
        }
        self.stationPlcUpdateT = 0
        # init the local train power state dictionary
        self.trainsDict = {
            'weline': None,
            'nsline': None, 
            'ccline': None,
            'mtline': None
        }
        self.trainPlcUpdateT= 0

        # init the remote train sensor state dictionary
        self.trainsRtuDict = {
            'weline': None,
            'nsline': None, 
            'ccline': None,
            'mtline': None
        }
        self.trainRtuUpdateT = 0

        # init the remote block sensor state dictionary
        self.blocksDict = {
            'weline': None,
            'nsline': None, 
            'ccline': None,
            'mtline': None
        }
        self.blockPlcUpdateT= 0

        gv.gDebugPrint("datamanager init finished.", logType=gv.LOG_INFO)

    #-----------------------------------------------------------------------------
    # Define all the data fetching request here:
    # the fetch function will handle the Plc components state fetch request by: convert 
    # the json string to dict, then fill the input reqDict with the data and return.
    # return json.dumps({'result': 'failed'}) if process data error.
    def fetchSensorInfo(self, reqJsonStr):
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            self.sensorPlcUpdateT = time.time() 
            self.updateSensorsData()
            junctionSenIdxDict = gv.iMapMgr.getJunctionSenIdxDict()
            for key in reqDict.keys():
                if key in self.sensorsDict.keys():
                    startIdx, endIdx = junctionSenIdxDict[key]
                    rawSensorList = self.sensorsDict[key]
                    reqDict[key] = rawSensorList[startIdx:endIdx]
            respStr = json.dumps(reqDict)
        except Exception as err:
            gv.gDebugPrint("fetchSensorInfo() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr
    
    #-----------------------------------------------------------------------------
    def fetchBlockSensInfo(self, reqJsonStr):
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            self.blockPlcUpdateT = time.time()
            self.updateSensorsData()
            blockSenIdxDict = gv.iMapMgr.getBlockSenIdxDict()
            for key in reqDict.keys():
                if key in self.sensorsDict.keys():
                    senList = blockSenIdxDict[key]
                    rawSensorList = self.sensorsDict[key]
                    reqDict[key] = [rawSensorList[idx] for idx in senList]
            respStr = json.dumps(reqDict)
        except Exception as err:
            gv.gDebugPrint("fetchSensorInfo() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr

    #-----------------------------------------------------------------------------
    def fetchStationInfo(self, reqJsonStr):
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            self.stationPlcUpdateT = time.time()
            self.updateStationsData()
            for key in reqDict.keys():
                if key in self.stationsDict.keys(): reqDict[key] = self.stationsDict[key]
            respStr = json.dumps(reqDict)
        except Exception as err:
            gv.gDebugPrint("fetchStationInfo() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr

    #-----------------------------------------------------------------------------
    def fetchTrainPwrInfo(self, reqJsonStr):
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            self.trainPlcUpdateT = time.time()
            self.updateTrainsPwrData()
            for key in reqDict.keys():
                if key in self.trainsDict.keys(): reqDict[key] = self.trainsDict[key]
            respStr = json.dumps(reqDict)
        except Exception as err:
            gv.gDebugPrint("fetchTrainPwrInfo() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr

    def fetchTrainSensInfo(self, reqJsonStr):
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            self.trainRtuUpdateT = time.time()
            self.updateTrainsSenData()
            for key in reqDict.keys():
                if key in self.trainsDict.keys(): reqDict[key] = self.trainsRtuDict[key]
            respStr = json.dumps(reqDict)
        except Exception as err:
            gv.gDebugPrint("fetchTrainSenInfo() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr

    #-----------------------------------------------------------------------------
    def getLastPlcsConnectionState(self):
        #print time.strftime("%b %d %Y %H:%M:%S", time.localtime(time.time))
        crtTime = time.time()
        sensorPlcOnline = crtTime - self.sensorPlcUpdateT < gv.gPlcTimeout
        stationPlcOnline = crtTime - self.stationPlcUpdateT < gv.gPlcTimeout
        trainPlcOnline = crtTime - self.trainPlcUpdateT < gv.gPlcTimeout
        blockPlcOnline = crtTime - self.blockPlcUpdateT < gv.gPlcTimeout
        return {
            'sensors': (time.strftime("%H:%M:%S", time.localtime(self.sensorPlcUpdateT)), sensorPlcOnline), 
            'stations': (time.strftime("%H:%M:%S", time.localtime(self.stationPlcUpdateT)), stationPlcOnline), 
            'trains': (time.strftime("%H:%M:%S", time.localtime(self.trainPlcUpdateT)), trainPlcOnline), 
            'blocks': (time.strftime("%H:%M:%S", time.localtime(self.blockPlcUpdateT)), blockPlcOnline),
        }

    def getLastRtusConnectionState(self):
        crtTime = time.time()
        trainRtuOnline = crtTime - self.trainRtuUpdateT < gv.gPlcTimeout
        return {
            'trains': (time.strftime("%H:%M:%S", time.localtime(self.trainRtuUpdateT)), trainRtuOnline), 
        }

    #-----------------------------------------------------------------------------
    def msgHandler(self, msg):
        """ Function to handle the data-fetch/control request from the monitor-hub.
            Args:
                msg (str/bytes): incoming data from PLC modules though UDP.
            Returns:
                bytes: message bytes needs to reply to the PLC.
        """
        gv.gDebugPrint("Incomming message: %s" % str(msg), logType=gv.LOG_INFO)
        if msg == b'': return None
        # request message format: 
        # data fetch: GET:<key>:<val1>:<val2>...
        # data set: POST:<key>:<val1>:<val2>...
        resp = b'REP;deny;{}'
        (reqKey, reqType, reqJsonStr) = parseIncomeMsg(msg)
        if reqKey=='GET':
            if reqType == 'login':
                resp = ';'.join(('REP', 'login', json.dumps({'state':'ready'})))
            elif reqType == 'sensors':
                respStr = self.fetchSensorInfo(reqJsonStr)
                resp =';'.join(('REP', 'sensors', respStr))
            elif reqType == 'stations':
                respStr = self.fetchStationInfo(reqJsonStr)
                resp =';'.join(('REP', 'stations', respStr))
            elif reqType == 'trainsPlc':
                respStr = self.fetchTrainPwrInfo(reqJsonStr)
                resp =';'.join(('REP', 'trainsPlc', respStr))
            elif reqType == 'trainsRtu':
                respStr = self.fetchTrainSensInfo(reqJsonStr)
                resp =';'.join(('REP', 'trainsRtu', respStr))
            elif reqType == 'blockSensors':
                respStr = self.fetchBlockSensInfo(reqJsonStr)
                resp =';'.join(('REP', 'blockSensors', respStr))

        elif reqKey=='POST':
            if reqType == 'signals':
                respStr = self.setSignals(reqJsonStr)
                resp =';'.join(('REP', 'signals', respStr))
            elif reqType == 'stations':
                respStr = self.setStationSignals(reqJsonStr)
                resp =';'.join(('REP', 'stations', respStr))
            elif reqType == 'trainsPlc':
                respStr = self.setTrainsPower(reqJsonStr)
                resp =';'.join(('REP', 'trainsPlc', respStr))
            elif reqType == 'blockSignals':
                respStr = self.setBlocks(reqJsonStr)
                resp =';'.join(('REP', 'blockSignals', respStr))
            pass
            # TODO: Handle all the control request here.
        if isinstance(resp, str): resp = resp.encode('utf-8')
        #gv.gDebugPrint('reply: %s' %str(resp), logType=gv.LOG_INFO )
        return resp

    #-----------------------------------------------------------------------------
    def run(self):
        """ Thread run() function will be called by start(). """
        time.sleep(1)
        gv.gDebugPrint("datamanager subthread started.", logType=gv.LOG_INFO)
        self.server.serverStart(handler=self.msgHandler)
        gv.gDebugPrint("DataManager running finished.", logType=gv.LOG_INFO)

    #-----------------------------------------------------------------------------
    # define all the set() function here:
    # set function will handle the Plc components state set request by: convert 
    # the json string to dict, the change the components state in map manager.

    def setSignals(self, reqJsonStr):
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            if gv.iMapMgr:
                for key, val in reqDict.items():
                    gv.iMapMgr.setSingals(key, val)
                respStr = json.dumps({'result': 'success'})
        except Exception as err:
            gv.gDebugPrint("setSignals() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr

    #-----------------------------------------------------------------------------
    def setBlocks(self, reqJsonStr):
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            if gv.iMapMgr:
                for key, val in reqDict.items():
                    gv.iMapMgr.setBlocks(key, val)
                respStr = json.dumps({'result': 'success'})

        except Exception as err:
            gv.gDebugPrint("setBlock() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr

    #-----------------------------------------------------------------------------
    def setStationSignals(self, reqJsonStr):
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            if gv.iMapMgr:
                for key, val in reqDict.items():
                    gv.iMapMgr.setStationSignal(key, val)
                respStr = json.dumps({'result': 'success'})
        except Exception as err:
            gv.gDebugPrint("setStationSignals() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr

    #-----------------------------------------------------------------------------
    def setTrainsPower(self, reqJsonStr):
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            if gv.iMapMgr:
                for key, val in reqDict.items():
                    gv.iMapMgr.setTainsPower(key, val)
                respStr = json.dumps({'result': 'success'})
        except Exception as err:
            gv.gDebugPrint("setTrainsPower() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr

    #-----------------------------------------------------------------------------
    # define() all the update function here, update function will update the local 
    # components record from the map manager.

    def updateSensorsData(self):
        if gv.iMapMgr:
            for key in self.sensorsDict.keys():
                sensorAgent = gv.iMapMgr.getSensors(trackID=key)
                self.sensorsDict[key] = sensorAgent.getSensorsState()

            # update the cc sensor piority if connect to PLC
            if not gv.gTestMD and not gv.gCollAvoid: self._updateSensorPriority()

    def _updateSensorPriority(self):
        if self.sensorsDict['ccline']:
            pryLen = len(self.priorityConfig)
            for i, val in enumerate(self.sensorsDict['ccline']):
                if i < pryLen and self.priorityConfig[i]:
                    priorityVal = self.priorityConfig[i]
                    overWriteFlg = False 
                    key, idxs = priorityVal[0], priorityVal[1:]
                    for j in idxs:
                        if j < len(self.sensorsDict[key]):
                            overWriteFlg = overWriteFlg or self.sensorsDict[key][j]
                    if val and overWriteFlg:
                        self.sensorsDict['ccline'][i] = 0

    #-----------------------------------------------------------------------------
    def updateStationsData(self):
        if gv.iMapMgr:
            for key in self.stationsDict.keys():
                self.stationsDict[key] = []
                for stationAgent in gv.iMapMgr.getStations(trackID=key):
                    state = 1 if stationAgent.getDockState() else 0
                    self.stationsDict[key].append(state)

    #-----------------------------------------------------------------------------
    def updateTrainsPwrData(self):
        if gv.iMapMgr:
            for key in self.trainsDict.keys():
                self.trainsDict[key] = []
                for train in gv.iMapMgr.getTrains(trackID=key):
                    state = 0 if train.getPowerState() == 0 else 1
                    self.trainsDict[key].append(state)

    #-----------------------------------------------------------------------------             
    def updateTrainsSenData(self):
        if gv.iMapMgr:
            for key in self.trainsRtuDict.keys():
                self.trainsRtuDict[key] = []
                for train in gv.iMapMgr.getTrains(trackID=key):
                    state = train.getTrainRealInfo()
                    reuslt = [state['fsensor'], state['speed'], state['voltage'], state['current']]
                    self.trainsRtuDict[key].append(reuslt) 

    #-----------------------------------------------------------------------------
    def stop(self):
        """ Stop the thread."""
        self.terminate = True
        if self.server: self.server.serverStop()
        endClient = udpCom.udpClient(('127.0.0.1', gv.UDP_PORT))
        endClient.disconnect()
        endClient = None

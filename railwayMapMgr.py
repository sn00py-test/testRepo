#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        railwayMgr.py
#
# Purpose:     The management module to control all the components on the map 
#              and update the components state. 
# 
# Author:      Yuancheng Liu
#
# Version:     v0.1.3
# Created:     2023/05/29
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import os
import json
import wx
from collections import OrderedDict

import railwayPWSimuGlobal as gv
import railwayAgent as agent

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class MapMgr(object):
    """ Map manager to init/control differet elements state on the map."""
    def __init__(self, parent):
        """ Init all the elements on the map. All the parameters are public to 
            other module.
        """
        self.tracks = OrderedDict()
        self.trains = OrderedDict()
        self.sensors = OrderedDict()
        self.signals = OrderedDict()
        self.stations = OrderedDict()

        self.junctionSenIdxDict = {} 
        self.blockSenIdxDict= {}
        self.junctionSigIdxDict = {}
        self.blockSigIdxDict = {}
        
        self.junctions = []
        self.envItems = [] # Currently we only have building item so use list instead of dict()

        self._initTandT()
        self._initSensors()
        self._initSignal()
        self._initStation()
        self._initEnv()
        self._initJunction()

        gv.gDebugPrint('Map display management controller inited', logType=gv.LOG_INFO)

#-----------------------------------------------------------------------------
    def _initTandT(self):
        """ This is a private Train&Tracks data init function, currently the data 
            is hardcoded. It will be replaced by loading a config file before the 
            whole program init.(load to a gv.gxx parameter)
        """
        # Init WE-Line and the trains on it.
        key = 'weline'
        self.tracks[key] = {
            'name': key,
            'color': gv.gTrackConfig[key]['color'],
            'type': gv.RAILWAY_TYPE_CYCLE,
            'points': [(50, 200), (100, 200), (100, 600), (600, 600), (600, 800),
                       (900, 800), (900, 400), (1550, 400), (1550, 450), (950, 450),
                       (950, 850), (550, 850), (550, 650), (50, 650)]
        }
        trackTrainCfg_we = [{'id': 'we01', 'head': (50, 200), 'nextPtIdx': 1, 'len': 5}, 
                            {'id': 'we02', 'head': (460, 600),'nextPtIdx': 7, 'len': 5},
                            {'id': 'we03', 'head': (1500, 400), 'nextPtIdx': 3, 'len': 5},
                            {'id': 'we04', 'head': (800, 850), 'nextPtIdx': 11, 'len': 5}]
        #if gv.gCollsionTestFlg: trackTrainCfg_we[1] = {'id': 'we02', 'head': (480, 600), 'nextPtIdx': 3, 'len': 5}
        self.trains[key] = self._getTrainsList(trackTrainCfg_we, self.tracks[key]['points'])
        # Init NS-Line and the trains on it.
        key = 'nsline'
        self.tracks[key] = {
            'name' : key,
            'color': gv.gTrackConfig[key]['color'],
            'type': gv.RAILWAY_TYPE_CYCLE,
            'points': [(300, 50), (1200, 50), (1200, 300), (800, 300), (800, 600), (700, 600), 
                       (700, 100), (400, 100), (400, 450), (300, 450)]
        }
        trackTrainCfg_ns = [{'id': 'ns01', 'head': (1000, 50), 'nextPtIdx': 1, 'len': 4},
                            {'id': 'ns02', 'head': (1100, 300), 'nextPtIdx': 3, 'len': 4},
                            {'id': 'ns03', 'head': (600, 100), 'nextPtIdx': 7, 'len': 4}]

        self.trains[key] = self._getTrainsList(trackTrainCfg_ns, self.tracks[key]['points'])
        # Init CC-Line and the trains on it.
        key = 'ccline'
        self.tracks[key] = {
            'name' : key,
            'color': gv.gTrackConfig[key]['color'],
            'type': gv.RAILWAY_TYPE_CYCLE,
            'points': [(200, 200), (1400, 200), (1400, 700), (200, 700)]
        }
        trackTrainCfg_cc = [  {'id': 'cc01', 'head': (1100, 200), 'nextPtIdx': 1, 'len': 5},
                            {'id': 'cc02', 'head': (1300, 700), 'nextPtIdx': 3, 'len': 5},
                            {'id': 'cc03', 'head': (300, 700), 'nextPtIdx': 3, 'len': 5}]
        #if gv.gCollsionTestFlg: trackTrainCfg_cc[2] = {'id': 'cc03', 'head': (700, 700), 'nextPtIdx': 3, 'len': 6}
        #if gv.gTrainDistTestFlag:
        #    trackTrainCfg_cc[0]['head'] = (510, 700)
        #    trackTrainCfg_cc[1]['head'] = (430, 700)
        #    trackTrainCfg_cc[2]['head'] = (300, 700)
        self.trains[key] = self._getTrainsList(trackTrainCfg_cc, self.tracks[key]['points'])
        # Init the maintance line 
        key = 'mtline'
        self.tracks[key] = {
            'name' : key,
            'color': gv.gTrackConfig[key]['color'],
            'type': gv.RAILWAY_TYPE_CYCLE,
            'points': [(460, 320), (640, 320), (640, 480), (460, 480)]
        }
        self.trains[key] = self._getTrainsList([], [])

#-----------------------------------------------------------------------------
    def _initSensors(self):
        """ Init all the train detection sensors on the map. """
        # Init all the WE-Line sensors
        sensorPos_we= [
            (100, 400), (170, 600), (270, 600), (600, 670), (600, 770), (900, 730),
            (900, 630), (1370, 400), (1470, 400), (1430, 450), (1330, 450), 
            (950, 670), (950, 770), (550, 730), (550, 650), (230, 650), (130, 650),
            # Add the track block sensors:
            (600, 600), (1140, 400), (950, 480), (640, 850)
            ]
        self.junctionSenIdxDict['weline'] = (0, 17)
        self.sensors['weline'] = agent.AgentSensors(self, 'we', sensorPos_we)
        # Init all the NS-line sensors
        sensorPos_ns = [
            (300, 230), (300, 130), (1200, 170), (1200, 270), (700, 230), (700, 130),
            (400, 170), (400, 270),
            # Add the track block sensors:
            (300, 340), (760, 50), (800, 400)
            ]
        self.junctionSenIdxDict['nsline'] = (0, 8)
        self.sensors['nsline'] = agent.AgentSensors(self, 'ns', sensorPos_ns)
        # Init all the CC-Line sensors.
        sensorPos_cc = [
            (270, 200), (480, 200), (670, 200), (770, 200), 
            (1170, 200), (1270, 200), (1400, 370), (1400, 500), 
            (980, 700), (830, 700), (630, 700), (460, 700),
            (200, 700), (200, 530), 
            # Add the track block sensors:
            (200, 360), (600, 200), (1080, 200),(1400, 260), (1320, 700)
            ]
        self.junctionSenIdxDict['ccline'] = (0, 14)
        self.sensors['ccline'] = agent.AgentSensors(self, 'cc', sensorPos_cc)
        # Init all the MT-Line sensors
        sensorPos_mt = [
            (640, 340), (640, 460)
            ]
        self.junctionSenIdxDict['mtline'] = (0, 2)
        self.sensors['mtline'] = agent.AgentSensors(self, 'mt', sensorPos_mt)

#-----------------------------------------------------------------------------
    def _initSignal(self):
        # Set all the signal on track weline
        trackSignalConfig_we = [
            {'id': 'we-0', 'pos':(160, 600), 'dir': gv.LAY_U, 'tiggerS': self.sensors['ccline'], 'onIdx':(12,), 'offIdx':(13,) }, 
            {'id': 'we-1', 'pos':(240, 650), 'dir': gv.LAY_U, 'tiggerS': self.sensors['ccline'], 'onIdx':(12,), 'offIdx':(13,) },
            {'id': 'we-2', 'pos':(600, 660), 'dir': gv.LAY_R, 'tiggerS': self.sensors['ccline'], 'onIdx':(10,), 'offIdx':(11,) },
            {'id': 'we-3', 'pos':(550, 740), 'dir': gv.LAY_L, 'tiggerS': self.sensors['ccline'], 'onIdx':(10,), 'offIdx':(11,) },
            {'id': 'we-4', 'pos':(900, 740), 'dir': gv.LAY_L, 'tiggerS': self.sensors['ccline'], 'onIdx':(8,), 'offIdx':(9,) },
            {'id': 'we-5', 'pos':(950, 660), 'dir': gv.LAY_R, 'tiggerS': self.sensors['ccline'], 'onIdx':(8,), 'offIdx':(9,) },
            {'id': 'we-6', 'pos':(1360, 400), 'dir': gv.LAY_U, 'tiggerS': self.sensors['ccline'], 'onIdx':(6,), 'offIdx':(7,) },
            {'id': 'we-7', 'pos':(1440, 450), 'dir': gv.LAY_U, 'tiggerS': self.sensors['ccline'], 'onIdx':(6,), 'offIdx':(7,) },
            # Add the track block control signal
            {'id': 'we-8', 'pos':(100, 340), 'dir': gv.LAY_R, 'tiggerS': self.sensors['weline'], 'onIdx':(0,), 'offIdx':(1,) },
            {'id': 'we-9', 'pos':(540, 600), 'dir': gv.LAY_U, 'tiggerS': self.sensors['weline'], 'onIdx':(17,), 'offIdx':(3,) },
            {'id': 'we-10', 'pos':(880, 800), 'dir': gv.LAY_U, 'tiggerS': self.sensors['weline'], 'onIdx':(5,), 'offIdx':(6,) },
            {'id': 'we-11', 'pos':(1080, 400), 'dir': gv.LAY_U, 'tiggerS': self.sensors['weline'], 'onIdx':(18,), 'offIdx':(7,) },
            {'id': 'we-12', 'pos':(980, 450), 'dir': gv.LAY_D, 'tiggerS': self.sensors['weline'], 'onIdx':(19,), 'offIdx':(11,) },
            {'id': 'we-13', 'pos':(700, 850), 'dir': gv.LAY_U, 'tiggerS': self.sensors['weline'], 'onIdx':(20,), 'offIdx':(13,) },

        ]
        self.blockSenIdxDict ['weline'] = (0,1,17,3,5,6,18,7,19,11,20,13)
        self.signals['weline'] = []
        for info in trackSignalConfig_we:
            signal = agent.AgentSignal(self, info['id'], info['pos'], dir=info['dir'])
            signal.setTriggerOnSensors(info['tiggerS'], info['onIdx'])
            signal.setTriggerOffSensors(info['tiggerS'], info['offIdx'])
            self.signals['weline'].append(signal)
        self.junctionSigIdxDict['weline'] = (0,1,2,3,4,5,6,7)
        self.blockSigIdxDict['weline'] = (8,9,10,11,12,13)

        # Set all the signal on track nsline
        trackSignalConfig_ns = [
            {'id': 'ns-0', 'pos':(300, 240), 'dir': gv.LAY_L, 'tiggerS': self.sensors['ccline'], 'onIdx':(0,), 'offIdx':(1,) },
            {'id': 'ns-1', 'pos':(400, 160), 'dir': gv.LAY_R, 'tiggerS': self.sensors['ccline'], 'onIdx':(0,), 'offIdx':(1,) },
            {'id': 'ns-2', 'pos':(700, 240), 'dir': gv.LAY_R, 'tiggerS': self.sensors['ccline'], 'onIdx':(2,), 'offIdx':(3,) },
            {'id': 'ns-3', 'pos':(1200, 160), 'dir': gv.LAY_R, 'tiggerS': self.sensors['ccline'], 'onIdx':(4,), 'offIdx':(5,) },
            # Add the track block control signal
            {'id': 'ns-4', 'pos':(300, 400), 'dir': gv.LAY_R, 'tiggerS': self.sensors['nsline'], 'onIdx':(8,), 'offIdx':(1,) },
            {'id': 'ns-5', 'pos':(700, 50), 'dir': gv.LAY_U, 'tiggerS': self.sensors['nsline'], 'onIdx':(9,), 'offIdx':(2,) },
            {'id': 'ns-6', 'pos':(800, 340), 'dir': gv.LAY_R, 'tiggerS': self.sensors['nsline'], 'onIdx':(10,), 'offIdx':(4,) },
        ]
        self.blockSenIdxDict['nsline'] = (8,1,9,2,10,4)
        self.signals['nsline'] = []
        for info in trackSignalConfig_ns:
            signal = agent.AgentSignal(self, info['id'], info['pos'], dir=info['dir'])
            signal.setTriggerOnSensors(info['tiggerS'], info['onIdx'])
            signal.setTriggerOffSensors(info['tiggerS'], info['offIdx'])
            self.signals['nsline'].append(signal)

        self.junctionSigIdxDict['nsline'] = (0,1,2,3)
        self.blockSigIdxDict['nsline'] =(4,5,6)

        # set all the signal on track ccline
        trackSignalConfig_cc = [
            {'id': 'cc-0', 'pos':(260, 200), 'dir': gv.LAY_U, 'tiggerS': self.sensors['nsline'], 'onIdx':(0, 6), 'offIdx':(1, 7) },
            {'id': 'cc-1', 'pos':(660, 200), 'dir': gv.LAY_U, 'tiggerS': self.sensors['nsline'], 'onIdx':(4,), 'offIdx':(5,) },
            {'id': 'cc-2', 'pos':(1160, 200), 'dir': gv.LAY_U, 'tiggerS': self.sensors['nsline'], 'onIdx':(2,), 'offIdx':(3,) },
            {'id': 'cc-3', 'pos':(1400, 360), 'dir': gv.LAY_R, 'tiggerS': self.sensors['weline'], 'onIdx':(7,9), 'offIdx':(8,10) },
            {'id': 'cc-4', 'pos':(990, 700), 'dir': gv.LAY_U, 'tiggerS': self.sensors['weline'], 'onIdx':(5,11), 'offIdx':(6,12) },
            {'id': 'cc-5', 'pos':(640, 700), 'dir': gv.LAY_U, 'tiggerS': self.sensors['weline'], 'onIdx':(3,13), 'offIdx':(4,14) },
            {'id': 'cc-6', 'pos':(210, 700), 'dir': gv.LAY_U, 'tiggerS': self.sensors['weline'], 'onIdx':(1, 15), 'offIdx':(2,16) },
            # Add the track block control signal
            {'id': 'cc-7', 'pos':(200, 420), 'dir': gv.LAY_R, 'tiggerS': self.sensors['ccline'], 'onIdx':(14,), 'offIdx':(0,) },
            {'id': 'cc-8', 'pos':(540, 200), 'dir': gv.LAY_U, 'tiggerS': self.sensors['ccline'], 'onIdx':(15,), 'offIdx':(2,) },
            {'id': 'cc-9', 'pos':(1020, 200), 'dir': gv.LAY_U, 'tiggerS': self.sensors['ccline'], 'onIdx':(16,), 'offIdx':(4,) },
            {'id': 'cc-10', 'pos':(1400, 200), 'dir': gv.LAY_U, 'tiggerS': self.sensors['ccline'], 'onIdx':(17,), 'offIdx':(6,) },
            {'id': 'cc-11', 'pos':(1380, 700), 'dir': gv.LAY_U, 'tiggerS': self.sensors['ccline'], 'onIdx':(18,), 'offIdx':(8,) },
            {'id': 'cc-12', 'pos':(265, 700), 'dir': gv.LAY_U, 'tiggerS': self.sensors['ccline'], 'onIdx':(12,), 'offIdx':(13,) },
        ]
        self.blockSenIdxDict['ccline'] = (14,0,15,2,16,4,17,6,18,8,12,13)
        self.signals['ccline'] = []
        for info in trackSignalConfig_cc:
            signal = agent.AgentSignal(self, info['id'], info['pos'], dir=info['dir'])
            signal.setTriggerOnSensors(info['tiggerS'], info['onIdx'])
            signal.setTriggerOffSensors(info['tiggerS'], info['offIdx'])
            self.signals['ccline'].append(signal)

        self.junctionSigIdxDict['ccline'] = (0,1,2,3,4,5,6)
        self.blockSigIdxDict['ccline'] = (7,8,9,10,11,12)

        # set all the singal on track mtline
        trackSignalConfig_mt = [
            {'id': 'mt-0', 'pos':(460, 400), 'dir': gv.LAY_R, 'tiggerS': self.sensors['mtline'], 'onIdx':(0,), 'offIdx':(1,) }
        ]
        self.signals['mtline'] = []
        for info in trackSignalConfig_mt:
            signal = agent.AgentSignal(self, info['id'], info['pos'], dir=info['dir'])
            signal.setTriggerOnSensors(info['tiggerS'], info['onIdx'])
            signal.setTriggerOffSensors(info['tiggerS'], info['offIdx'])
            self.signals['mtline'].append(signal)

#---------------------------------------------------------------------------
    def _initStation(self):
        """ Init the station based on the configuration file, YC: this function is used to replace the old 
            _initstation() function which did the hard code station in the code.
        """
        for key in gv.gTrackConfig.keys():
            stationCfgFile = gv.gTrackConfig[key]['stationCfg']
            stationCfgPath = os.path.join(gv.CFG_FD, stationCfgFile)
            if os.path.exists(stationCfgPath):
                with open(stationCfgPath) as json_file:
                    trackStationList = json.load(json_file)
                    self.stations[key] = []
                    for info in trackStationList:
                        layoutParm = info['layout'] if 'layout' in info.keys() else gv.LAY_H
                        signalParm = info['signalLayout'] if 'signalLayout' in info.keys() else gv.LAY_L
                        station = agent.AgentStation(self, info['id'], info['pos'], layout=layoutParm, signalLayout=signalParm)
                        station.setCheckTrains(self.trains[key])
                        if 'labelPos' in info.keys(): station.setlabelPos(info['labelPos'])
                        self.stations[key].append(station)
            else:
                gv.gDebugPrint("The station configure file is not exist, expected file path: %s" % str(stationCfgPath),
                               logType=gv.LOG_WARN)

#-----------------------------------------------------------------------------
    def _initStation_old(self):
        """ Init all the train stations. [This function is replayed by the station configure files] """
        # Init all stations on weline.
        trackStation_we = [{'id': 'Tuas_Link', 'pos': (80, 200), 'layout': gv.LAY_H},
                           {'id': 'Jurong_East', 'pos': (360, 600), 'layout': gv.LAY_H},
                           {'id': 'Outram_Park', 'pos': (750, 800), 'layout': gv.LAY_H},
                           {'id': 'City_Hall', 'pos': (900, 500), 'layout': gv.LAY_V, 'labelPos':(-70, -10)},
                           {'id': 'Paya_Lebar', 'pos': (1250, 400), 'layout': gv.LAY_H },
                           {'id': 'Changi_Airport', 'pos': (1550, 430), 'layout': gv.LAY_V, 'labelPos':(-70, -60)},
                           {'id': 'Lavender', 'pos': (1100, 450), 'layout': gv.LAY_H},
                           {'id': 'Raffles_Place', 'pos': (850, 850), 'layout': gv.LAY_H},
                           {'id': 'Clementi', 'pos': (430, 650), 'layout': gv.LAY_H},
                           {'id': 'Boon_Lay', 'pos': (50, 450), 'layout': gv.LAY_V, 'labelPos':(20, -10)}]
        self.stations['weline'] = []
        for info in trackStation_we:
            station = agent.AgentStation(self, info['id'], info['pos'], layout=info['layout'])
            station.setCheckTrains(self.trains['weline'])
            if 'labelPos' in info.keys(): station.setlabelPos(info['labelPos'])
            self.stations['weline'].append(station)
        
        # Init all stations on nsline
        trackStation_ns = [{'id': 'Jurong_East', 'pos': (360, 450)},
                           {'id': 'Woodlands', 'pos': (430, 50)},
                           {'id': 'Yishun', 'pos': (1040, 50)},
                           {'id': 'Orchard', 'pos': (980, 300)},
                           {'id': 'City_Hall', 'pos': (750, 600)},
                           {'id': 'Bishan', 'pos': (550, 100)}]
        self.stations['nsline'] = []
        for info in trackStation_ns:
            station = agent.AgentStation(self, info['id'], info['pos'])
            station.setCheckTrains(self.trains['nsline'])
            self.stations['nsline'].append(station)

        # Init all stations on ccline
        trackStation_cc = [{'id': 'Buona_Vista', 'pos': (320, 700), 'layout': gv.LAY_H},
                           {'id': 'Farrer_Road', 'pos': (200, 300), 'layout': gv.LAY_V, 'labelPos':(20, -10) },
                           {'id': 'Serangoon', 'pos': (930, 200), 'layout': gv.LAY_H},
                           {'id': 'Nicoll_Highway', 'pos': (1400, 600), 'layout': gv.LAY_V, 'labelPos':(20, -10)},
                           {'id': 'Bayfront', 'pos': (1160, 700),'layout': gv.LAY_H},
                           {'id': 'Harbourfront', 'pos': (710, 700),'layout': gv.LAY_H}]
        self.stations['ccline'] = []
        for info in trackStation_cc:
            station = agent.AgentStation(self, info['id'], info['pos'], layout=info['layout'])
            station.setCheckTrains(self.trains['ccline'])
            if 'labelPos' in info.keys(): station.setlabelPos(info['labelPos'])
            self.stations['ccline'].append(station)

#-----------------------------------------------------------------------------
    def _initJunction(self):
        juncType1 = ('nsline', 'ccline')
        juncType2 = ('weline', 'ccline')
        metroJunctions = [ 
            {'pos':(300, 200), 'tracks':juncType1, 'Idx1': (0,), 'Idx2': (0,)}, 
            {'pos':(400, 200), 'tracks':juncType1, 'Idx1': (1,), 'Idx2': (0,)},
            {'pos':(700, 200), 'tracks':juncType1, 'Idx1': (2,), 'Idx2': (1,)}, 
            {'pos':(1200, 200), 'tracks':juncType1, 'Idx1': (3,), 'Idx2': (2,)},
            {'pos':(1400, 400), 'tracks':juncType2, 'Idx1': (6,), 'Idx2': (3,)}, 
            {'pos': (1400, 450), 'tracks':juncType2, 'Idx1': (7,), 'Idx2': (3,)},
            {'pos':(950, 700), 'tracks':juncType2, 'Idx1': (5,), 'Idx2': (4,)}, 
            {'pos':(900, 700), 'tracks':juncType2, 'Idx1': (4,), 'Idx2': (4,)},
            {'pos':(600, 700), 'tracks':juncType2, 'Idx1': (2,), 'Idx2': (5,)},
            {'pos':(550, 700), 'tracks':juncType2, 'Idx1': (3,), 'Idx2': (5,)},
            {'pos':(200, 650), 'tracks':juncType2, 'Idx1': (1,), 'Idx2': (6,)}, 
            {'pos':(200, 600), 'tracks':juncType2, 'Idx1': (0,), 'Idx2': (6,)}            

        ]
        for i, info in enumerate(metroJunctions):
            track1Id = info['tracks'][0]
            track2Id = info['tracks'][1]
            #signalList = []
            junction = agent.AgentJunction(self, 'jc-%s' % str(i), info['pos'], track1Id, track2Id)
            # YC TODO : temporary disabled the junction deadlock check function as we will 
            # add the train priority check part.
            # Set the signals related to each other in each junction  
            # for j, signal in enumerate(self.signals[track1Id]):
            #     if j in info['Idx1']:
            #         signalList.append(signal)
            # for j, signal in enumerate(self.signals[track2Id]):
            #     if j in info['Idx2']:
            #         signalList.append(signal)
            # junction.setSignalList(signalList)         
            self.junctions.append(junction)

#-----------------------------------------------------------------------------
    def _initEnv(self):
        """ Init all the enviroment Items on the map such as IOT device or camera."""
        envCfg = [ {'id':'Industry Area', 'img':'factory_0.png', 'pos':(100, 90), 'size':(120, 120)},
                   {'id':'Airport', 'img':'airport.jpg', 'pos':(1500, 240), 'size':(160, 100)},
                   {'id':'JurongEast-Jem', 'img':'city_0.png', 'pos':(360, 520), 'size':(80, 80)},
                   {'id':'CityHall-01', 'img':'city_2.png', 'pos':(750, 520), 'size':(90, 80)},
                   {'id':'CityHall-02', 'img':'city_1.png', 'pos':(850, 600), 'size':(80, 60)},
                   {'id':'Hospital', 'img':'hospitalIcon.png', 'pos':(1080, 540), 'size':(120, 80)},

                   {'id':'Legend', 'img':'legend.png', 'pos':(1450, 820), 'size':(200, 150)},
                   {'id':'Track-Junction-PLCs', 'img': 'plcIcon2.png', 'pos':(50, 780), 'size':(60,50)},
                   {'id':'Track-Station-PLCs', 'img': 'plcIcon2.png', 'pos':(50, 860), 'size':(60,50)},
                   {'id':'Train-Ctrl-PLCs', 'img': 'plcIcon2.png', 'pos':(310, 780), 'size':(60,50)},
                   {'id':'Track-Block-PLCs', 'img': 'plcIcon2.png', 'pos':(310, 860), 'size':(60,50)},
                   {'id':'Train-Ctrl-RTUs', 'img': 'rtuIcon2.png', 'pos':(1100, 780), 'size':(60,50)},
                   {'id':'Date & Time', 'img': 'time.png', 'pos':(1270, 50), 'size':(30,30)}
                   ]
        for info in envCfg:
            imgPath = os.path.join(gv.IMG_FD, info['img'])
            if os.path.exists(imgPath):
                bitmap = wx.Bitmap(imgPath)
                building = agent.agentEnv(self, info['id'], info['pos'], bitmap, info['size'] )
                self.envItems.append(building)
        
        labelCfg = [
                {'id': 'West-East Line [WE]', 'img': None, 'pos': (550, 550), 'size': (180, 30),
                'color': gv.gTrackConfig['weline']['color'], 'link':((550, 550), (550, 600))},
                {'id': 'North-South [NS]', 'img': None, 'pos': (850, 100), 'size': (180, 30),
                'color': gv.gTrackConfig['nsline']['color'], 'link':((850, 100), (850, 50))},
                {'id': 'Circle Line [CC]', 'img': None, 'pos': (1260, 650), 'size': (180, 30),
                'color': gv.gTrackConfig['ccline']['color'], 'link':((1260, 650), (1260, 700))},
                {'id': 'Maintenance Line [MT]', 'img': None, 'pos': (550, 280), 'size': (190, 30),
                'color': gv.gTrackConfig['mtline']['color'], 'link':((550, 280), (550, 320))}
        ]
        for info in labelCfg:
            label = agent.agentEnv(self, info['id'], info['pos'], None, info['size'], tType=gv.LABEL_TYPE )
            if 'link' in info.keys(): label.setLinkList(info['link'])
            if 'color' in info.keys(): label.setColor(info['color'])
            self.envItems.append(label)

#-----------------------------------------------------------------------------
    def _getTrainsList(self, trainCfg, trackPts):
        """ Build the railwayAgent.TainAgent obj list based on inmput train config information.
        Args:
            trainCfg (_type_): _description_
            trackPts (_type_): _description_
        Returns:
            _type_: _description_
        """
        trainList = []
        for trainInfo in trainCfg:
            trainObj = agent.AgentTrain(self, trainInfo['id'], trainInfo['head'], trackPts, 
                                        trainLen=trainInfo['len'])
            trainList.append(trainObj)
        return trainList

#-----------------------------------------------------------------------------
    def _updateJunctionState(self):
        collsionTrainsDict = {
            'weline' : [], 
            'nsline' : [],
            'ccline' : [],
            'mtline' : [],
        }
        for junction in self.junctions:
            junction.updateState()
            #if gv.gDeadlockTestFlg:
            #    junction.handleDeadLock()
            #gv.gDebugPrint(junction.getCollitionState(), logType=gv.LOG_INFO)
            if junction.getCollition():
                colltionState = junction.getCollitionState()
                for key, val in colltionState.items():
                    collsionTrainsDict[key].append(val)
        return collsionTrainsDict

#-----------------------------------------------------------------------------
    def resetTrainsPos(self, trainDict):
        for key in trainDict.keys():
            if key in self.tracks.keys():
                self.trains[key] = self._getTrainsList(trainDict[key], self.tracks[key]['points'])
        # reInit the items
        self._initSensors()
        self._initSignal()
        self._initStation()
        self._initJunction()

#-----------------------------------------------------------------------------
# Define all the get() functions here:

    def getEnvItems(self):
        return self.envItems

    def getTracks(self, trackID=None):
        if trackID and trackID in self.tracks.keys(): return self.tracks[trackID]
        return self.tracks

    def getTrains(self, trackID=None):
        if trackID and trackID in self.trains.keys(): return self.trains[trackID]
        return self.trains

    def getStations(self, trackID=None):
        if trackID and trackID in self.stations.keys(): return self.stations[trackID]
        return self.stations

    def getSignals(self, trackID=None):
        if trackID and trackID in self.signals.keys(): return self.signals[trackID]
        return self.signals

    def getSensors(self, trackID=None):
        if trackID and trackID in self.sensors.keys(): return self.sensors[trackID]
        return self.sensors

    def getJunction(self):
        return self.junctions

    def getJunctionSenIdxDict(self):
        return self.junctionSenIdxDict

    def getBlockSenIdxDict(self):
        return self.blockSenIdxDict

#-----------------------------------------------------------------------------
# Define all the set() functions here:

    def setStationSignal(self, trackID, stationStatList):
        if trackID in self.stations.keys():
            for i, stationAgent in enumerate(self.stations[trackID]):
                if i < len(stationStatList):
                    stationAgent.setSignalState(stationStatList[i])

    def setSingals(self, trackID, signalStatList):
        if trackID in self.signals.keys():
            for i, singal in enumerate(self.signals[trackID]):
                if i < len(signalStatList):
                    singal.setState(signalStatList[i])

    def setBlocks(self, trackID, blockStatList):
        if trackID in self.blockSigIdxDict.keys():
            idxList = self.blockSigIdxDict[trackID]
            for i, singalVal in enumerate(blockStatList):
                if i < len(idxList):
                    signal = self.signals[trackID][idxList[i]]
                    signal.setState(singalVal)

    def setTainsPower(self, trackID, powerStateList):
        if trackID in self.trains.keys():
            for i, train in enumerate(self.trains[trackID]):
                if i < len(powerStateList):
                    stopflg = not powerStateList[i]
                    train.setEmgStop(stopflg)
        # change the trains avoidance config if need
        if trackID == 'config':
            gv.gDebugPrint('--> change the CA state: %s' %str(powerStateList[0]), 
                           logType=gv.LOG_INFO)
            data = powerStateList[0]
            gv.gCollAvoid = data
            gv.iMainFrame.changeCAcheckboxState(gv.gCollAvoid)

    #-----------------------------------------------------------------------------
    def updateSignalState(self, key):
        if key == 'mtline': return
        piority = {
            'weline': ('ccline',),
            'nsline': ('ccline',),
            'ccline': ('weline', 'nsline'),
            #'mtline': ('mtline',)
        }
        for lineKey in piority[key]:
            for idx, signal in enumerate(self.signals[lineKey]):
                if idx in self.junctionSigIdxDict[lineKey]:
                    signal.updateSingalState()

    #-----------------------------------------------------------------------------
    def autoCorrectSignalState(self):
        """ Correct the CC line signal if got error, if both signal are on, turn 
            off the cc line signal to make the cc line train pass 1st. This function
            actived by the 
        """
        checkPair = [
            ('nsline', (0, 1)),
            ('nsline', (2,)),
            ('nsline', (3,)),
            ('weline', (6, 7)),
            ('weline', (4, 5)),
            ('weline', (2, 3)),
            ('weline', (0, 1))
        ]
        for i, signal in enumerate(self.signals['ccline']):
            if i < len(checkPair):
                checkRst = signal.getState()
                if checkRst:
                    key, val = checkPair[i]
                    for idx in val:
                        checkRst = checkRst and self.signals[key][idx].getState()
                    # If both signal on state happens correct the CC line signal.
                    if checkRst: 
                        gv.gDebugPrint("Correct the CC line signal: %s" %str(i), logType=gv.LOG_WARN)
                        signal.setState(False)

#-----------------------------------------------------------------------------
    def periodic(self , now):
        """ Periodicly call back function. This function need to be called before the 
            railwayPanelMap's periodic().
        """
        collsionTrainsDict = self._updateJunctionState()
        # update the trains position.
        for key, val in self.trains.items():
            for i, train in enumerate(val):
                if len(val) > 1:
                    # Check train collision if more than 2 trains on the track
                    frontTrain = val[(i+1)%len(val)] 
                    # Check the collision to the front train 1st. 
                    result = train.checkCollFt(frontTrain)
                    # Handle the collision if the auto avoidance is disabled.
                    if result and (not gv.gCollAvoid):
                        train.setEmgStop(True)
                        train.setCollsionFlg(True)
                        frontTrain.setEmgStop(True)

                # if collision with the front train, ignore the signal.
                if not result: train.checkSignal(self.signals[key])        
                # stop the train if it got collision at any junction.
                if collsionTrainsDict and i in collsionTrainsDict[key]:
                    if gv.gCollAvoid:
                        if key == 'ccline': train.setTrainSpeed(0)
                    else: 
                        train.setEmgStop(True)
                train.updateRealWordInfo()
                train.updateTrainPos()               
            # update all the track's sensors state afte all the trains have moved.
            self.sensors[key].updateActive(val)
            # updaste all the signal, if test mode (not connect to PLC) call the 
            # buildin signal control logic, else the data manager will read the signal 
            # infromation from PLC then do the auto update.
            if gv.gTestMD or gv.gCollAvoid: self.updateSignalState(key)
            if gv.gJuncAvoid: self.autoCorrectSignalState()

        # update the station train's docking state
        for key, val in self.stations.items():
            for station in val:
                station.updateTrainsDock()
                if not station.getDockState():
                    station.setEmptyCount(station.getEmptyCount() + 1)



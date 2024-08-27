#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        railWayPanelMap.py
#
# Purpose:     This module is used to display the state animation of the railway 
#              system, such as trains movement, sensors detection state, station
#              docking state and singal changes ...
# 
# Author:      Yuancheng Liu
#
# Version:     v0.1.2
# Created:     2023/06/01
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import os
import time

import wx
import railwayPWSimuGlobal as gv

DEF_PNL_SIZE = (1600, 920)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PanelMap(wx.Panel):
    """ RailWay system map panel."""
    def __init__(self, parent, panelSize=DEF_PNL_SIZE):
        wx.Panel.__init__(self, parent, size=panelSize)
        self.bgColor = wx.Colour(30, 40, 62)
        self.SetBackgroundColour(self.bgColor)
        self.panelSize = panelSize
        self.bitMaps = self._loadBitMaps()
        self.toggle = False
        # Paint the map
        self.Bind(wx.EVT_PAINT, self.onPaint)
        # self.Bind(wx.EVT_LEFT_DOWN, self.onLeftClick)
        # Set the panel double buffer to void the panel flash during update.
        self.SetDoubleBuffered(True)

#-----------------------------------------------------------------------------
    def _loadBitMaps(self):
        """ Load the internal usage pictures as bitmaps."""
        imgDict = {}
        imgPath = os.path.join(gv.IMG_FD, 'alert.png')
        if os.path.exists(imgPath):
            png = wx.Image(imgPath, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            imgDict['alert'] = png
        return imgDict

#-----------------------------------------------------------------------------
# Define all the _draw() map components paint functions.
    
    def _drawEnvItems(self, dc):
        """ Draw the environment items."""
        dc.SetPen(self.dcDefPen)
        dc.SetTextForeground(wx.Colour('White'))
        for item in gv.iMapMgr.getEnvItems():
            id = item.getID()
            pos = item.getPos()
            bitmap = item.getWxBitmap()
            size = item.getSize()
            if item.getType() == gv.ENV_TYPE:
                dc.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
                dc.DrawBitmap(bitmap, pos[0]-size[0]//2, pos[1]-size[1]//2)
                dc.DrawText(str(id), pos[0]-size[0]//2, pos[1]-size[1]//2-15)
            elif item.getType() == gv.LABEL_TYPE:
                color, link = item.getColor(), item.getLink()
                if link:
                    dc.SetPen(wx.Pen(color, width=2, style=wx.PENSTYLE_SOLID))
                    dc.DrawLines(link)
                dc.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD))
                dc.SetBrush(wx.Brush(color))
                dc.DrawRectangle(pos[0]-size[0]//2, pos[1]-size[1]//2, size[0], size[1])
                dc.DrawText(str(id), pos[0]-size[0]//2+6, pos[1]-size[1]//2+6)
        # Draw the current date and time
        dc.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        dc.SetTextForeground(wx.Colour('GREEN'))
        dc.DrawText(time.strftime("%b %d %Y %H:%M:%S", time.localtime(time.time())), 1300, 40)
        
        # Draw the PLC state:
        if gv.iDataMgr:
            dc.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
            plcStateDict = gv.iDataMgr.getLastPlcsConnectionState()
            rtuStateDict = gv.iDataMgr.getLastRtusConnectionState()
            # draw sensor plc state
            timeStr, state = plcStateDict['sensors']
            textColor = wx.Colour('GREEN') if state else wx.Colour('RED')
            dc.SetTextForeground(textColor)
            connState = 'online' if state else 'offline'
            dc.DrawText('- [ PLC-00, PLC-01, PLC-02 ]', 90, 760)
            dc.DrawText('- Last Update Time: '+str(timeStr), 90, 777)
            dc.DrawText('- Connection State: '+str(connState), 90, 794)

            # draw sensor plc state
            timeStr, state = plcStateDict['stations']
            textColor = wx.Colour('GREEN') if state else wx.Colour('RED')
            dc.SetTextForeground(textColor)
            connState = 'online' if state else 'offline'
            dc.DrawText('- [ PLC-03, PLC-04, PLC-05 ]', 90, 840)
            dc.DrawText('- Last Update Time: '+str(timeStr), 90, 857)
            dc.DrawText('- Connection State: '+str(connState), 90, 874)

            # draw trains plc state
            timeStr, state = plcStateDict['trains']
            textColor = wx.Colour('GREEN') if state else wx.Colour('RED')
            dc.SetTextForeground(textColor)
            connState = 'online' if state else 'offline'
            dc.DrawText('- [ PLC-06, PLC-07 ]', 350, 760)
            dc.DrawText('- Last Update Time: '+str(timeStr), 350, 777)
            dc.DrawText('- Connection State: '+str(connState), 350, 794)

           # draw trains rtu state
            timeStr, state = rtuStateDict['trains']
            textColor = wx.Colour('GREEN') if state else wx.Colour('RED')
            dc.SetTextForeground(textColor)
            connState = 'online' if state else 'offline'
            dc.DrawText('- [ RTU-01-10 ]', 1140, 760)
            dc.DrawText('- Last Update Time: '+str(timeStr), 1140, 777)
            dc.DrawText('- Connection State: '+str(connState), 1140, 794)

        # draw the time state
        timeStr, state = plcStateDict['blocks']
        textColor = wx.Colour('GREEN') if state else wx.Colour('RED')
        dc.SetTextForeground(textColor)
        connState = 'online' if state else 'offline'
        dc.DrawText('- [ PLC-08, PLC-09 ]', 350, 840)
        dc.DrawText('- Last Update Time: '+str(timeStr), 350, 857)
        dc.DrawText('- Connection State: '+str(connState), 350, 874)

#-----------------------------------------------------------------------------
    def _drawJunction(self, dc):
        """ Draw the junction 
        """
        dc.SetPen(self.dcDefPen)
        for item in gv.iMapMgr.getJunction():
            pos = item.getPos()
            if item.getCollition() and not gv.gCollAvoid:
                if self.toggle:
                    dc.DrawBitmap(self.bitMaps['alert'], pos[0]-15, pos[1]-15)
                else:
                    dc.SetPen(wx.Pen('RED', width=1, style=wx.PENSTYLE_SOLID))
                    dc.SetBrush(wx.Brush('RED'))
                    dc.DrawRectangle(pos[0]-10, pos[1]-10, 20, 20)
            else: 
                dc.SetPen(wx.Pen('GREEN', width=1, style=wx.PENSTYLE_SOLID))
                dc.SetBrush(wx.Brush('GREEN', wx.TRANSPARENT))
                dc.DrawRectangle(pos[0]-10, pos[1]-10, 20, 20)

#-----------------------------------------------------------------------------
    def _drawRailWay(self, dc):
        """ Draw the background and the railway."""
        w, h = self.panelSize
        dc.SetBrush(wx.Brush(self.bgColor))
        dc.DrawRectangle(0, 0, w, h)
        for key, trackInfo in gv.iMapMgr.getTracks().items():
            dc.SetPen(wx.Pen(trackInfo['color'], width=4, style=wx.PENSTYLE_SOLID))
            trackPts = trackInfo['points']
            for i in range(len(trackPts)-1):
                fromPt, toPt = trackPts[i], trackPts[i+1]
                dc.DrawLine(fromPt[0], fromPt[1], toPt[0], toPt[1])
            # Connect the head and tail if the track is a circle:
            if trackInfo['type'] == gv.RAILWAY_TYPE_CYCLE: 
                fromPt, toPt = trackPts[0], trackPts[-1]
                dc.DrawLine(fromPt[0], fromPt[1], toPt[0], toPt[1])

#--PanelMap--------------------------------------------------------------------
    def _drawTrains_old(self, dc):
        """ Draw the trains on the map."""
        dc.SetPen(self.dcDefPen)
        clashPt = None
        # Draw the train1 on the map.
        # dc.SetPen(wx.Pen(wx.Colour(52, 169, 129)))
        # dirList = self.mapMgr.trainA.getDirs()
        # #bitmap = wx.Bitmap(gv.gTrainImgB)
        # gc = wx.GraphicsContext.Create(dc)
        # gc.SetBrush(wx.Brush(trainColor))
        # for i, point in enumerate( self.mapMgr.trainA.getPos()):
        #      gc.PushState()
        #      gc.Translate(point[0], point[1])
        #      gc.Rotate(dirList[i])
        #      gc.DrawRectangle(-5, -5, 10, 10)
        #      if i == 0 or i == 4:
        #          gc.DrawBitmap(wx.Bitmap(gv.gTrainImgB), -5, -5, 10, 10)
        # #     else:
        # #         gc.DrawBitmap(bitmap, -5, -5, 10, 10)
        #      gc.PopState()
        for point in self.mapMgr.trainA.getPos():
            dc.DrawRectangle(point[0]-5, point[1]-5, 10, 10)
        # Draw the train2 on the map.

#-----------------------------------------------------------------------------
    def _drawTrains(self, dc):
        """ Draw the trains on the map."""
        dc.SetPen(self.dcDefPen)
        trainDict = gv.iMapMgr.getTrains()
        for key, val in trainDict.items():
            for i, train in enumerate(val):
                trainColor = '#CE8349' if train.getTrainSpeed() == 0 else 'GREEN'
                if train.getEmgStop():
                    trainColor = 'RED'
                dc.SetBrush(wx.Brush(trainColor))
                for point in train.getPos():
                    dc.DrawRectangle(point[0]-5, point[1]-5, 10, 10)
                # draw the train ID:
                dc.SetTextForeground(wx.Colour(trainColor))
                pos = train.getTrainPos(idx=0)
                # Draw the collsion Icon if collision happens.
                if self.toggle and train.getCollsionFlg(): dc.DrawBitmap(self.bitMaps['alert'], pos[0]-20, pos[1]-20)
                #dc.DrawText(key+'-'+str(i), pos[0]+5, pos[1]+5)
                dc.DrawText(key+'-'+str(i), pos[0]+5, pos[1]+5)
                if gv.gShowTrainRWInfo:
                    trainInfo = train.getTrainRealInfo()
                    dc.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
                    dc.DrawText('- power: %s' %str('on' if train.getPowerState() else 'off'), pos[0]+5, pos[1]+15)
                    dc.DrawText('- speed: %s km/h' %str(trainInfo['speed']), pos[0]+5, pos[1]+25)
                    dc.DrawText('- voltage: %s V' %str(trainInfo['voltage']), pos[0]+5, pos[1]+35)
                    dc.DrawText('- current: %s A' %str(trainInfo['current']), pos[0]+5, pos[1]+45)
                    dc.DrawText('- fsensor: %s' %str('detected' if trainInfo['fsensor'] else 'none'), pos[0]+5, pos[1]+55)

#-----------------------------------------------------------------------------
    def _drawSensors(self, dc):
        dc.SetPen(self.dcDefPen)
        dc.SetFont(wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        dc.SetBrush(wx.Brush('GRAY'))
        for key, sensorAgent in gv.iMapMgr.getSensors().items():
            sensorId = sensorAgent.getID()
            sensorPos = sensorAgent.getPos()
            sensorState = sensorAgent.getSensorsState()
            dc.SetTextForeground(wx.Colour('White'))
            for i in range(sensorAgent.getSensorCount()):
                pos = sensorPos[i]
                dc.DrawText(sensorId+"-s"+str(i), pos[0]+3, pos[1]+5)
                state = sensorState[i]
                if state:
                    color = 'YELLOW' if self.toggle else 'BLUE'
                    dc.SetBrush(wx.Brush(color))
                    dc.DrawRectangle(pos[0]-4, pos[1]-4, 8, 8)
                    dc.SetBrush(wx.Brush('GRAY'))
                else:
                    dc.DrawRectangle(pos[0]-4, pos[1]-4, 8, 8)

#-----------------------------------------------------------------------------
    def _drawSignals(self, dc):
        dc.SetPen(self.dcDefPen)
        dc.SetFont(wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        dc.SetBrush(wx.Brush('Green'))
        for key, signals in gv.iMapMgr.getSignals().items():
            for signalAgent in signals:
                id = signalAgent.getID()
                pos = signalAgent.getPos()
                state = signalAgent.getState()
                dir = signalAgent.dir
                color = 'RED' if state else 'GREEN'
                dc.SetPen(wx.Pen(color, width=2, style=wx.PENSTYLE_SOLID))
                x, y = pos[0], pos[1]
                if dir == gv.LAY_U:
                    y -= 15 
                elif dir == gv.LAY_D:
                    y += 15
                elif dir == gv.LAY_L:
                    x -= 15
                elif dir == gv.LAY_R:
                    x += 15
                dc.DrawLine(pos[0], pos[1], x, y)
                dc.DrawText("S-"+str(id), x-10, y-25)
                dc.SetBrush(wx.Brush(color))
                dc.DrawRectangle(x-5, y-5, 10, 10)

#-----------------------------------------------------------------------------
    def _drawStation(self, dc):
        dc.SetPen(self.dcDefPen)
        dc.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        for key, stations in gv.iMapMgr.getStations().items():
            colorCode = gv.iMapMgr.getTracks(trackID=key)['color']
            dc.SetTextForeground(colorCode)
            for station in stations:
                id = station.getID()
                pos = station.getPos()
                x, y = pos[0], pos[1]
                dc.SetPen(self.dcDefPen)
                dc.SetBrush(wx.Brush(colorCode))
                (x1,y1) = station.getLabelPos()
                dc.DrawText(str(id), x+x1, y+y1)
                color = 'BLUE' if station.getDockState() else colorCode
                line =wx.PENSTYLE_SOLID if station.getDockState() else wx.PENSTYLE_LONG_DASH
                dc.SetBrush(wx.Brush(color))
                dc.DrawCircle(x, y, 8)
                dc.SetPen(wx.Pen(color, width=1, style=line))
                dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
                if station.getLayout() == gv.LAY_H:
                    dc.DrawRectangle(x-35, y-7, 70, 14)
                else: 
                    dc.DrawRectangle(x-7, y-35, 14, 70)
                # Draw station signal if some train is docking.
                if station.getSignalState():
                    dc.SetPen(self.dcDefPen)
                    dc.SetBrush(wx.Brush('RED'))
                    if station.getLayout() == gv.LAY_H:
                        dc.DrawRectangle(x-40, y-6, 8, 12)
                        dc.DrawRectangle(x+30, y-6, 8, 12)
                    else: 
                        dc.DrawRectangle(x-6, y-40, 12, 8)
                        dc.DrawRectangle(x-6, y+30, 12, 8)
                    pos = station.getSignalPos()
                    #dc.DrawCircle(pos[0], pos[1], 10)

    #--PanelMap--------------------------------------------------------------------
    def onPaint(self, event):
        """ Draw the whole panel by using the wx device context."""
        dc = wx.PaintDC(self)
        self.dcDefPen = dc.GetPen()
        # Draw all the components
        self._drawRailWay(dc)
        self._drawJunction(dc)
        self._drawTrains(dc)
        self._drawSensors(dc)
        self._drawSignals(dc)
        self._drawStation(dc)
        self._drawEnvItems(dc)

    def updateDisplay(self, updateFlag=None):
        """ Set/Update the display: if called as updateDisplay() the function will 
            update the panel, if called as updateDisplay(updateFlag=?) the function
            will set the self update flag.
        """
        self.Refresh(False)
        self.Update()
        self.toggle = not self.toggle

#--PanelMap--------------------------------------------------------------------
    def periodic(self , now):
        """ periodicly call back to do needed calcualtion/panel update"""
        # Call the onPaint to update the map display.
        self.updateDisplay()

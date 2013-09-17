#Kevin Xu
#15-112 Spring 2013 Term Project
#video found at http://www.youtube.com/watch?v=aNAGobQN3oo&feature=youtu.be
#enjoy~ this program was independently written by me alone, and 
#makes use of panda3d engine, along with Starcraft: Wings of Liberty graphics,
#and Starcraft: Brood War sound effects


import direct.directbase.DirectStart
#starts the program
import random
from panda3d.core import Point2,Point3,Vec3,Vec4
#implements a movable object, which will be the player for me
from panda3d.core import TextNode
from pandac.PandaModules import NodePath
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from math import sin, cos, pi, atan
from direct.interval.MetaInterval import Sequence
from direct.gui.OnscreenImage import OnscreenImage
from direct.interval.IntervalGlobal import *
from direct.showbase.ShowBase import ShowBase
import cPickle, sys
import time

def loadObject(tex = None,  pos = Point2(0,0), depth = 55, scale = 1, \
    transparency = True): #the depth and scale is set to the standard values
    #so I don't need to provide it every time we call load object
    item = loader.loadModel("models/plane")
    item.reparentTo(camera) #sets the perspective of the camera, orients objects
    item.setPos(Point3(pos.getX(), depth, pos.getY())) #starting spot
    item.setScale(scale)
    item.setBin("unsorted", 0) #doesn't matter in what order we draw items
    item.setDepthTest(False) #All in 1 plane, don't need to test overlaps
    if transparency: item.setTransparency(1) #All of our objects are trasnparent
    if tex: #is a texture
        tex = loader.loadTexture("textures/"+tex+".png") #Whatever picture we want
        item.setTexture(tex, 1)                           #Set the picture
    return item

class Stage(DirectObject):#DirectObject, ShowBase): #this is different from a normal object! since we want to 
    #be able to keep track of the state of key presses as opposed to 1 time events
    def __init__(self, level = 1, score = 0, timeStart = time.time(), startMus = True):
        self.level = level
        if self.level == 3:
            self.level = 1
        self.alive = True
        self.screenX = 50
        self.screenY = 30
        self.yBound = self.screenY - 2
        self.xBound = self.screenX - 2
        self.accel = 10
        self.degToRad = pi/180
        self.icy = False
        self.discs = []
        self.lasers = []
        self.enemyArmy = []
        self.constantArmy = []
        self.enemyType = []
        self.constantEnemyType = []
        self.spawningEnemy = []
        self.warping = []
        self.warpingIn = []
        if self.level == 1:
            self.bossHealth = 60
            self.bossSprite = 'mothership'
        elif self.level == 2:
            self.bossHealth = 99999
            self.bossSprite = 'leviathan'
        self.timerCount = 0
        self.lastChecked = 0
        self.hasShip = False
        self.finishedSpawning = False
        self.finishedSpawningStations = False
        self.increaseEnemy = False
        self.wallLoaded = []
        self.enemyWarping = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.score = score
        self.timeStart = timeStart
        self.transition = False
        self.extraSpawn = False
        self.playMusic(startMus)
        if self.level == 1: self.objectiveMes = "Objective: Defeat the Mothership"
        elif self.level == 2: self.objectiveMes = "Objective: Move West to Extraction area"
        self.finishDirection = False
        self.nextLevelGo = False
        self.extraWall = False
        self.turnRate = 360 #How quickly the player's icon turns, assuming degrees
        #I can use this to access any .png files and set it as my background
        #I can use this to access any .png files to use as my player icon, 
        #along with any decorations. Here the ship is the player, and flower is
        #for testing decorations
        self.makeIntro()
        self.keys = {"turnLeft" : 0, "turnRight": 0,
                 "move": 0, "shoot": 0, "recall": 0, "restart": 0, 'zoomout': 0,
                 "continue": 0, "paused": 0} #a dictionary of all the events that can be done
                 #I'll say 1 = True, 0 = False.
        self.accept("arrow_left",     self.setKey, ["turnLeft", 1]) #key is currently being held down
        self.accept("arrow_left-up",  self.setKey, ["turnLeft", 0]) #the -up means the key is released
        self.accept("arrow_right",    self.setKey, ["turnRight", 1])
        self.accept("arrow_right-up", self.setKey, ["turnRight", 0])
        self.accept("arrow_up",       self.setKey, ["move", 1])
        self.accept("arrow_up-up",    self.setKey, ["move", 0])
        self.accept("arrow_down",       self.setKey, ["move", -1])
        self.accept("arrow_down-up",       self.setKey, ["move", 0])
        self.accept('x', self.setKey, ['zoomout', 1])
        self.accept('z', self.setKey, ['zoomout', 0])
        
        self.accept("enter",         self.setKey, ["recall", 1])
        self.start = {"start":0}
        self.accept("mouse1", self.setStart, ["start", 1])
        self.gameTask = taskMgr.add(self.timerFired, "timerFired")
        self.gameTask.last = 0         #How frequently it updates

    def makeIntro(self):
            self.introScreen = loadObject("intro", scale = (150, 100, 120), depth = 200, \
                transparency = False)
            self.title = loadObject("title", scale = (40, 100, 10), depth = 200, \
                pos = Point2(0, 29))
            self.title1 = loadObject("title1", scale = (80, 100, 30), depth = 200, \
                pos = Point2(0, 45))
            self.selectBox1 = loadObject("selectbox", scale = (40,100,70), depth = 200,
                pos = Point2(-47,-10))
            self.selectBox2 = loadObject("selectbox", scale = (40,100,70), depth = 200,
                pos = Point2(-0,-10))
            self.selectBox3 = loadObject("selectbox", scale = (40,100,70), depth = 200,
                pos = Point2(47,-10))
            self.loadShip1 = loadObject("bc", scale = (35, 100, 20), depth = 200, \
                pos = Point2(-47, -1))
            self.loadShip2 = loadObject("viking2", scale = (35, 100, 30), depth = 200, \
                pos = Point2(0,-3))
            self.loadShip3 = loadObject("wraith", scale = (27, 100, 24), depth = 200, \
                pos = Point2(47, -3))
            self.line1 = OnscreenText(text = "Viking", pos = (0, 0.24), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.1)
            self.line2 = OnscreenText(text = "Battlecruiser", pos = (-1.17, 0.24), fg=(20,20,0,20),
                          align = TextNode.ALeft, scale = 0.1)
            self.line3 = OnscreenText(text = "Wraith", pos = (0.75, 0.24), fg=(20,20,0,20),
                          align = TextNode.ALeft, scale = 0.1)
            self.line4 = OnscreenText(text = "Tactical Aircraft", pos = (0, -0.31), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.07)
            self.line5 = OnscreenText(text = "Surgical Striker", pos = (0.63, -0.31), fg=(20,20,0,20),
                          align = TextNode.ALeft, scale = 0.07)
            self.line6 = OnscreenText(text = "Heavy Assaulter", pos = (-1.13, -0.31), fg=(20,20,0,20),
                          align = TextNode.ALeft, scale = 0.07)
            self.line7 = OnscreenText(text = "Health: 10", pos = (0, -0.4), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.06)
            self.line8 = OnscreenText(text = "Health: 20", pos = (-0.87, -0.4), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.06)
            self.line9 = OnscreenText(text = "Health: 10", pos = (0.75, -0.4), fg=(20,20,0,20),
                          align = TextNode.ALeft, scale = 0.06)
            self.line10 = OnscreenText(text = "Ammo: 10", pos = (0, -0.47), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.06)
            self.line11 = OnscreenText(text = "Ammo: Infinite", pos = (-.87, -0.47), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.06)
            self.line12 = OnscreenText(text = "Ammo: Infinite", pos = (0.69, -0.47), fg=(20,20,0,20),
                          align = TextNode.ALeft, scale = 0.06)
            self.line13 = OnscreenText(text = "Missiles bounce on walls", pos = (0, -0.54), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.06)
            self.line14 = OnscreenText(text = "Press Enter to recall bullets", pos = (0, -0.6), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.057)
            self.line15 = OnscreenText(text = "Medium moving speed", pos = (0, -0.66), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.057)
            self.line16 = OnscreenText(text = "Dual Laser Fire", pos = (-.87, -0.54), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.06)
            self.line17 = OnscreenText(text = "Twice as Durable", pos = (-.87, -0.6), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.057)
            self.line18 = OnscreenText(text = "Slow moving speed", pos = (-.87, -0.66), fg=(20,20,0,20),
                          align = TextNode.ACenter, scale = 0.057)
            self.line19 = OnscreenText(text = "Quick Sniper missiles", pos = (0.6, -0.54), fg=(20,20,0,20),
                          align = TextNode.ALeft, scale = 0.06)
            self.line20 = OnscreenText(text = "Automatic burst lasers", pos = (0.6, -0.6), fg=(20,20,0,20),
                          align = TextNode.ALeft, scale = 0.057)
            self.line21 = OnscreenText(text = "Quick moving speed", pos = (0.625, -0.66), fg=(20,20,0,20),
                          align = TextNode.ALeft, scale = 0.057)

    def loadDirections(self):
        if self.keys["continue"] == 1:
            self.keys["continue"] = 0
            self.finishDirection = True
        if self.level == 1:
            self.protoss1 = loadObject('mission1', scale = (144, 100, 108),depth = 200, \
            transparency = False)
            self.protoss2 = loadObject('protossbox', scale = (110,100,110), depth = 200,
                transparency = True, pos = Point2(-15, -17))
            self.protoss3 = loadObject('controls1', scale = (90, 100, 70), depth = 200,
                transparency = True, pos = Point2(-20, -10))
            self.protoss4 = loadObject('controls5', scale = (40, 100, 30), depth = 200,
                transparency = True, pos = Point2(-19, 35))
            self.protoss5 = loadObject('protoss', scale = (60,100,60), depth = 200,
                transparency = True, pos = Point2(43, -30))
        if self.level == 2:
            self.introScreen = loadObject("level2", scale = (150, 100, 120), depth = 200, \
                transparency = False)

    def altTimer(self, task):
        try: self.pauseMessage.remove()
        except: pass
        self.pauseMessage = OnscreenText("Paused",
                pos = (0, 0), fg=(20,20,0,20), align = TextNode.ACenter, scale = 0.1)
        self.accept('p', self.setKey, ['paused', 0])
        if self.keys['paused'] == 0: #unpaused
            try: self.pauseMessage.remove()
            except: pass
            self.accept('p', self.setKey, ['paused', 1])
            self.gameTask = taskMgr.add(self.timerFired, "timerFired")
            self.gameTask.last = 0
            taskMgr.remove('pausetimer')
            return Task.done
        return Task.cont

    def playMusic(self, start):
        if start == True:
            if self.level == 1:
                mySound = base.loadMusic("operationevolution.mp3")
                mySound.setVolume(0.1)
                mySound.setLoopCount(0)
                mySound.play()
            if self.level == 2:
                mySound = base.loadMusic("jetstream.mp3")
                mySound.setVolume(0.3)
                mySound.setLoopCount(0)
                mySound.play()

    def playSFX(self):
        if self.level == 1:
            if self.bossHealth == 60:
                warn = base.loadSfx("PDrPss02.wav")
                warn.setVolume(0.6)
                warn.setLoopCount(1)
                warn.play()
            if self.bossHealth == 0:
                warn = base.loadSfx("EXPLOLRG.WAV")
                warn.setVolume(0.6)
                warn.setLoopCount(1)
                warn.play()
            if self.bossHealth == 20:
                warn = base.loadSfx("PCaPss03.wav")
                warn.setVolume(0.6)
                warn.setLoopCount(1)
                warn.play()
        if self.level == 2 and self.extraWall == True:
            warn = base.loadSfx("ZBgRdy00.wav")
            warn.setVolume(0.6)
            warn.setLoopCount(1)
            warn.play()            

    def timerFired(self, task):
    #This uses the change in time as "dt" or delta, as the tutorial called it.
    #The timerfired is like any other, it loops infinitely, updating the position
    #of the ship every frame
        if self.keys['paused'] == 1:
                self.gameTaskAlt = taskMgr.add(self.altTimer, "pausetimer")
                self.gameTaskAlt.last = 0
                taskMgr.remove('timerFired')
        if self.start["start"] == 1:
            self.accept('p', self.setKey, ['paused', 1])
            if self.hasShip == False:
                self.loadShip()
            if self.hasShip == True:
                self.removeAll()
                self.accept("s",  self.setKey, ["continue", 1])
                self.loadDirections()
                if self.finishDirection == False:
                    return Task.cont
                if self.finishDirection == True:
                    self.removeDirections()
                    self.bg = loadObject("stars", scale = 400, depth = 200, \
                                 transparency = False)
                    self.drawBoundary()
                    self.start['start'] = 2
                    self.drawShip()
                    self.playSFX()
                    if self.level == 1:
                        self.boss = loadObject(self.bossSprite, scale=7, pos = Point2(-15, 0))
                    if self.level == 2:
                        self.boss = loadObject(self.bossSprite, scale=9, pos = Point2(-15, 0))
                        self.rotateEnemy(self.boss)
                    self.setVelocity(self.ship, Vec3(0,0,0)) #starts without moving 
                    self.createMonsters()
                    self.createSameMonsters()
                    self.makeWalls()
        if self.start['start'] == 2:
            self.accept("r", self.setKey, ["restart", 1])
            if self.level == 2:
                try: self.rotateEnemy(self.boss)
                except: pass
                if self.extraWall == True:
                    if time.time() > self.endSurvive:
                        self.nextLevel()
            self.accept('mouse1', self.setKey, ['paused', 0])
            self.accept('p', self.setKey, ['paused', 1])
            self.accept("space",          self.setKey, ["shoot", 1])
            try: self.showScore.remove()
            except: pass
            try: self.objective.remove()
            except: pass
            self.showScore = OnscreenText("Score: %d" % (self.score), 
                pos = (0.92, 0.9),\
                fg=(20,20,0,20), align = TextNode.ALeft, scale = 0.07)
            self.objective = OnscreenText(self.objectiveMes,
                    pos = (-1.3, 0.9), fg=(20,20,0,20), align = TextNode.ALeft, scale = 0.07)
            if self.keys["restart"] == 1:
                self.gameOver1()
            if self.alive == True:
                self.timerCount += 1 #every frame we count 1
                timeChange = task.time - task.last
                self.currentTime = time.time()
                task.last = task.time
                self.updateShip(timeChange)
                for disc in self.discs:
                    try:
                        self.updatePos(disc, timeChange)
                        if self.checkLegalDisc(disc, timeChange) == 42:
                            return
                        self.checkLaserWall(disc, self.discs, timeChange)
                    except:
                        pass
                for index in xrange(len(self.enemyArmy)):
                    self.shotTime = 0  
                    self.updateEnemy(self.enemyArmy[index], timeChange, self.enemyType[index], index) 
                for index in xrange(len(self.constantArmy)):
                    self.shotTime = 0
                    if type(self.constantArmy[index]) != int:   
                        self.updateEnemy(self.constantArmy[index], timeChange, self.armyList[index], index)
                    elif type(self.constantArmy[index]) == int:
                        self.constantArmy[index] += 1
                for laser in self.lasers:
                    self.updatePos(laser, timeChange)
                    self.checkHitShip(laser, timeChange)
                    self.checkLaserWall(laser, self.lasers, timeChange)
                if self.shipType == 'wraith2' and self.timerCount > 100 and \
                    self.timerCount % 200 == 0:
                        self.makeWraithLasers()
                if len(self.spawningEnemy) > 0:
                    for index in xrange(len(self.spawningEnemy)):
                        self.spawningEnemy[index] += 1
                if len(self.warping) > 0:
                    for index in xrange(len(self.warping)):
                        self.warping[index] += 1
                self.createMonsters()
                self.createSameMonsters()
                self.createLifeBar()
                self.centerCamera()
                if self.extraWall == False and self.ship.getPos().getX() < 10 and self.level == 2:
                    self.makeWalls()
                if self.extraWall == True:
                    self.drawCountDown()
                    self.objectiveMes = "Objective: Survive until Extraction"
                if self.bossHealth == 20 and self.extraSpawn == False:
                    for index in xrange(len(self.constantArmy)):
                        if type(self.constantArmy[index]) == int:
                            if self.constantArmy[index] < 850:
                                self.constantArmy[index] = 849
                    self.constantArmy.append(845)
                    self.constantArmy.append(845)
                    self.constantArmy.append(845)
                    self.createSameMonsters()
                    self.extraSpawn = True
                    self.objectiveMes = "The Protoss has summoned reinforcements around the map!"
                    self.playSFX()
                return Task.cont
            if self.alive == False:
                self.accept("mouse1", self.setStart, ['start', 4])
        if self.alive == False:
            if self.restartGame(self.level) == True:
                return
            elif self.restartGame(self.level) == False:
                return Task.cont
        return Task.cont

    def centerCamera(self):
        if self.keys['zoomout'] == 0:
            pos = self.ship.getPos()
            posX = pos.getX()
            posY = pos.getZ()
            base.cam.setPos(posX,-5,posY)
        elif self.keys['zoomout'] == 1:
            shipX = self.ship.getPos().getX()
            if shipX >= -20 and shipX <= 20:
                base.cam.setPos(0,-55,0)
            elif shipX < -20:
                base.cam.setPos(shipX+20, -55, 0)
            elif shipX > 20:
                base.cam.setPos(shipX-20, -55, 0)

    def loadShip(self):
        try:
            mouseX = base.mouseWatcherNode.getMouseX()
            mouseY = base.mouseWatcherNode.getMouseY()
            if mouseY >= -0.84 and mouseY <= 0.46:
                if mouseX >= -0.9375 and mouseX <= -0.377:
                    self.shipType = 'battlecruiser'
                    self.hasShip = True
                    self.maxVelocity = 10
                    self.maxVelocitySq = 10**2
                    self.bulletCount = 999
                    self.bulletSpeed = 16
                    self.shipHealth = 20
                    warn = base.loadSfx("tbardy00.wav")
                    warn.setVolume(0.5)
                    warn.setLoopCount(1)
                    warn.play()
                if mouseX >= -0.28 and mouseX <= 0.275:
                    self.shipType = 'viking'
                    self.hasShip = True
                    self.maxVelocity = 14
                    self.maxVelocitySq = 14**2
                    self.bulletCount = 10
                    self.bulletSpeed = 16
                    self.shipHealth = 10
                    warn = base.loadSfx("TGoPss00.wav")
                    warn.setVolume(0.5)
                    warn.setLoopCount(1)
                    warn.play()
                if mouseX >= 0.38 and mouseX <= 0.935:
                    self.shipType = 'wraith2'
                    self.hasShip = True
                    self.maxVelocity = 19
                    self.maxVelocitySq = 19**2
                    self.bulletCount = 999
                    self.bulletSpeed = 30
                    self.shipHealth = 10
                    warn = base.loadSfx("TPhPss01.wav")
                    warn.setVolume(0.5)
                    warn.setLoopCount(1)
                    warn.play()
        except: pass

    def drawShip(self):
        self.ship = loadObject(self.shipType, scale = 5, pos = Point2(43.12,4))

    def removeDirections(self):
        if self.level == 1:
            self.protoss1.remove()
            self.protoss2.remove()
            self.protoss3.remove()
            self.protoss4.remove()
            self.protoss5.remove()

    def removeAll(self):
        self.introScreen.remove()
        self.title.remove()
        self.title1.remove()
        self.selectBox1.remove()
        self.selectBox2.remove()
        self.selectBox3.remove()
        self.loadShip1.remove()
        self.loadShip2.remove()
        self.loadShip3.remove()
        self.line1.remove()
        self.line2.remove()
        self.line3.remove()
        self.line4.remove()
        self.line5.remove()
        self.line6.remove()
        self.line7.remove()
        self.line8.remove()
        self.line9.remove()
        self.line10.remove()
        self.line11.remove()
        self.line12.remove()
        self.line13.remove()
        self.line14.remove()
        self.line15.remove()
        self.line16.remove()
        self.line17.remove()
        self.line18.remove()
        self.line19.remove()
        self.line20.remove()
        self.line21.remove()
        if self.level == 2:
            self.introScreen.remove()

    def drawBoundary(self):
        self.upBound = loadObject('laserwall3', pos = Point2(0,self.yBound+1),
            scale = (100,2,2))
        self.lowerBound = loadObject('laserwall3', pos = Point2(0,-self.yBound-1),
            scale = (100,2,2))
        self.rightBound = loadObject('laserwall3', pos = Point2(self.xBound+1,0),
            scale = (2,2,60))
        self.leftBound = loadObject('laserwall3', pos = Point2(-self.xBound-1,0),
            scale = (2,2,60))

    def setVelocity(self, obj, val): ##########This function is taken from the Panda3d tutorial on velocity mechanisms#############
        list = [val[0],val[1],val[2]] 
        obj.setTag("velocity", cPickle.dumps(list))

    def getVelocity(self, obj):     ###########This function is also taken from the tutorial#######
        list = cPickle.loads(obj.getTag("velocity"))
        return Vec3(list[0], list[1], list[2])

    def setKey(self, key, val): 
        self.keys[key] = val #keeps track of whether a key is being held down or not in the dictionary of keys pressed

    def setStart(self,key,val):
        self.start[key] = val

    def updatePos(self, obj, timeChange):
        #makes use of the built-in getX, getY and getZ functions of panda
        if self.keys['paused'] == 0:
            velocity = self.getVelocity(obj)
            newPos = obj.getPos() + (velocity*timeChange)
            obj.setPos(newPos)

    def updateShip(self, timeChange):
        self.updateBullets()
        self.checkRecall()
        direction = self.ship.getR() #the direction of the ship
        if self.keys["turnRight"]:
            direction += timeChange * self.turnRate #uses the time multiplied by rate of turning to find out how much it turns
            self.ship.setR((direction+360) % 360) #so it can go full circles without crashing
        elif self.keys["turnLeft"]:
            direction -= timeChange * self.turnRate
            self.ship.setR((direction+360) % 360)
        speed = self.maxVelocity
        self.constantSpeed = speed #one single constant speed
        directionRad = self.degToRad * direction #sin and cos only work with radians
        yComponent = sin(directionRad)
        xComponent = cos(directionRad)
        if self.keys["move"] == 1: #moves forwards
            newVel = (Vec3(yComponent, 0, xComponent) * self.accel * timeChange) #this yields the new X and Y components of speed vector
        elif self.keys["move"] == -1: #moves backwards
            newVel = (Vec3(-yComponent, 0, -xComponent) * self.accel * timeChange)
        if self.icy == True:
            if self.keys["move"] != 0:
                newVel += self.getVelocity(self.ship) #which we add to the original speed
                if newVel.lengthSquared() > self.maxVelocitySq:
                    newVel.normalize() #uses builtin function of normalizing to find the unit vectors, to keep direction the same
                    newVel *= self.maxVelocity #multiplies by the magnitude, to find the correct vector speed
                elif newVel.lengthSquared() > self.maxVelocitySq:
                    newVel.normalize()
                    newVel *= self.maxVelocity
            else:
                newVel = self.getVelocity(self.ship)
        if self.keys["move"] == 0 and self.icy == False:
            newVel = Vec3(0,0,0)
        if self.icy == False:
            newVel.normalize()
            newVel *= speed
        self.setVelocity(self.ship, newVel)
        self.checkLegalPosition(self.ship, newVel, timeChange)
        self.updatePos(self.ship, timeChange) #update the player's ship on the board

    def updateBullets(self):
        if self.keys["shoot"] == 1:
            if self.shipType == 'viking' or self.shipType == 'wraith2':
                if self.bulletCount > 0: #this section is indentical to update ship, but with
                    self.bulletCount -= 1 #elastic collision mechanics
                    direction = self.ship.getR()
                    directionRad = self.degToRad * direction
                    yComponent = sin(directionRad)
                    xComponent = cos(directionRad)
                    bulletVel = (Vec3(yComponent, 0, xComponent))
                    bulletVel.normalize()
                    bulletVel *= self.bulletSpeed #direction of bullet found!
                    position = self.ship.getPos() + bulletVel*0.08
                    if self.shipType == 'wraith2':
                        position = self.ship.getPos() + bulletVel*0.01
                    if self.shipType == 'viking':
                        disc = loadObject('water2', scale = 0.8)
                    else:
                        disc = loadObject('ammo4', scale = 0.6)
                    disc.setPos(position)
                    self.setVelocity(disc, bulletVel)
                    self.discs.append(disc)
                    hit = base.loadSfx("BLASTCAN.WAV")
                    hit.setVolume(0.4)
                    hit.setLoopCount(1)
                    hit.play()
            if self.shipType == 'battlecruiser':
                direction = self.ship.getR()
                directionRad = self.degToRad * direction
                yComponent = sin(directionRad)
                xComponent = cos(directionRad)
                bulletVel = (Vec3(yComponent, 0, xComponent))
                bulletVel.normalize()
                bulletVel *= self.bulletSpeed #direction of bullet found!
                position = self.ship.getPos() + bulletVel*0.08
                offSet = (xComponent*0.3,0,-yComponent*0.3)
                offSet1 = (-xComponent*0.3,0,yComponent*0.3)
                position1 = position + offSet
                position2 = position + offSet1
                disc = loadObject('ammo7', scale = 0.6)
                disc.setPos(position1)
                self.setVelocity(disc, bulletVel)
                self.discs.append(disc)
                disc = loadObject('ammo7', scale = 0.6)
                disc.setPos(position2)
                self.setVelocity(disc, bulletVel)
                self.discs.append(disc)
                hit = base.loadSfx("BLASTCAN.WAV")
                hit.setVolume(0.4)
                hit.setLoopCount(1)
                hit.play()
            self.keys["shoot"] = 0

    def makeWraithLasers(self):
        direction = self.ship.getR()
        direction1 = direction + 10
        direction2 = direction - 10
        directionRad = self.degToRad * direction
        directionRad1 = self.degToRad * direction1
        directionRad2 = self.degToRad * direction2
        yComponent = sin(directionRad)
        xComponent = cos(directionRad)
        yComponent1 = sin(directionRad1)
        xComponent1 = cos(directionRad1)
        yComponent2 = sin(directionRad2)
        xComponent2 = cos(directionRad2)
        bulletVel = (Vec3(yComponent, 0, xComponent))
        bulletVel.normalize()
        bulletVel *= 16
        position = self.ship.getPos() + bulletVel*0.03
        disc = loadObject('ammo8', scale = 0.6)
        disc.setPos(position)
        self.setVelocity(disc, bulletVel)
        self.discs.append(disc)
        bulletVel = (Vec3(yComponent1, 0, xComponent1))
        bulletVel.normalize()
        bulletVel *= 16
        position = self.ship.getPos() + bulletVel*0.03
        disc = loadObject('ammo8', scale = 0.6)
        disc.setPos(position)
        self.setVelocity(disc, bulletVel)
        self.discs.append(disc)    
        bulletVel = (Vec3(yComponent2, 0, xComponent2))
        bulletVel.normalize()
        bulletVel *= 16
        position = self.ship.getPos() + bulletVel*0.03
        disc = loadObject('ammo8', scale = 0.6)
        disc.setPos(position)
        self.setVelocity(disc, bulletVel)
        self.discs.append(disc)            

    def checkRecall(self):
        if self.keys["recall"] == 1:
            discs = self.discs
            for disc in discs:
                self.returnDisc(disc)
            self.keys["recall"] = 0

    def returnDisc(self, disc):
        if self.shipType == 'viking':
            shipPos = self.ship.getPos()
            discPos = disc.getPos()
            shipX = shipPos.getX()
            shipY = shipPos.getZ()
            discX = discPos.getX()
            discY = discPos.getZ()
            deltaX = shipX - discX
            deltaY = shipY - discY
            newVel = Vec3(deltaX, 0, deltaY) #yields the direction of return path
            newVel.normalize()
            newVel *= self.bulletSpeed
            self.setVelocity(disc, newVel)
    
    def checkLegalPosition(self, ship, velocity, timeChange):
        velocity = self.getVelocity(ship)
        newPos = ship.getPos() + (velocity*timeChange)
        if newPos.getX() > self.xBound and velocity[0] > 0: #These 2 check the left and right bounds. 
        #I set the boundary width to be 1
            velocity[0] = 0
            self.setVelocity(self.ship, velocity)
            newPos = ship.getPos()
        elif newPos.getX() < -self.xBound and velocity[0] < 0: 
            velocity[0] = 0
            self.setVelocity(self.ship, velocity)
            newPos = ship.getPos()
        if newPos.getZ() > self.yBound and velocity[2] > 0: #these two check the upper and lower bounds
            velocity[2] = 0
            self.setVelocity(self.ship, velocity)
            newPos = ship.getPos()
        elif newPos.getZ() < -self.yBound and velocity[2] < 0: 
            velocity[2] = 0
            self.setVelocity(self.ship, velocity)
            newPos = ship.getPos()
        self.checkWallPos(ship, velocity, timeChange)

    def checkLegalDisc(self, disc, timeChange):
        velocity = self.getVelocity(disc)
        newPos = disc.getPos() + (velocity*timeChange)
        if self.shipType == 'viking':
            if self.discReturned(disc,timeChange) == False:
                if newPos.getX() > self.xBound and velocity[0] > 0: #These 2 check the left and right bounds. 
                    velocity[0] *= -1
                    self.setVelocity(disc, velocity)
                    newPos = disc.getPos()
                elif newPos.getX() < -self.xBound and velocity[0] < 0: 
                    velocity[0] *= -1
                    self.setVelocity(disc, velocity)
                    newPos = disc.getPos()
                if newPos.getZ() > self.yBound and velocity[2] > 0: #these two check the upper and lower bounds
                    velocity[2] *= -1
                    self.setVelocity(disc, velocity)
                    newPos = disc.getPos()
                elif newPos.getZ() < -self.yBound and velocity[2] < 0: 
                    velocity[2] *= -1
                    self.setVelocity(disc, velocity)
                    newPos = disc.getPos()
                for enemy in self.enemyArmy:
                    if self.checkEnemyHit(disc, timeChange, enemy, self.enemyArmy) == True:
                        self.createMonsters()
                        return
                if self.checkBossHit(disc, timeChange, self.boss) == True:
                    return
                for enemy in self.constantArmy:
                    if type(enemy) != int:
                        if self.checkEnemyHit(disc, timeChange, enemy, self.constantArmy) == True:
                            self.createSameMonsters()
                            return
        elif self.shipType == 'wraith2' or self.shipType == 'battlecruiser':
            if newPos.getX() > self.xBound or newPos.getX() < -self.xBound \
            or newPos.getZ() > self.yBound or newPos.getZ() < -self.yBound: #checks if its within bounds  
                self.discs.remove(disc)
                self.bulletCount += 1
                disc.remove()
                return
            #test if it hits an enemy
            for enemy in self.enemyArmy:
                if self.checkEnemyHit(disc, timeChange, enemy, self.enemyArmy) == True:
                    self.createMonsters()
                    return
            if self.checkBossHit(disc, timeChange, self.boss) == True:
                return
            for enemy in self.constantArmy:
                if type(enemy) != int:
                    if self.checkEnemyHit(disc, timeChange, enemy, self.constantArmy) == True:
                        self.createSameMonsters()
                        return

    def checkEnemyHit(self, disc, timeChange, enemy, enemyArmy): 
        margin = 1.5 #the area surrounding the ship
        discPos = disc.getPos()
        enemyPos = enemy.getPos()
        discX = discPos.getX()
        enemyX = enemyPos.getX()
        discZ = discPos.getZ()
        enemyZ = enemyPos.getZ()
        if discX > enemyX - margin and discX < enemyX + margin and \
        discZ > enemyZ - margin and discZ < enemyZ + margin:
            self.discs.remove(disc)
            self.bulletCount += 1
            disc.remove()
            if enemyArmy is self.enemyArmy: #a random enemy
                index = self.enemyArmy.index(enemy)
                self.enemyArmy.remove(enemy)
                self.enemyType.pop(index)
                enemy.remove()
                self.spawningEnemy.append(0)
                self.score += 10
                '''chance = random.randint(0,20)
                if chance == 5:
                    self.shipHealth += 2'''
            elif enemyArmy is self.constantArmy: #a stationed army
                index = self.constantArmy.index(enemy)
                self.constantArmy[index].remove()
                self.constantArmy[index] = 0
                self.score += 10
                '''chance = random.randint(0,20)
                if chance == 5:
                    self.shipHealth += 2'''
            hit1 = base.loadSfx("explo1.wav")
            hit1.setVolume(0.5)
            hit1.setLoopCount(1)
            hit1.play()
            return True
        return False

    def checkBossHit(self,disc,timeChange,enemy):
        margin = 2.6 #boss frames
        try:
            discPos = disc.getPos()
            enemyPos = enemy.getPos()
            discX = discPos.getX()
            enemyX = enemyPos.getX()
            discZ = discPos.getZ()
            enemyZ = enemyPos.getZ()
            if discX > enemyX - margin and discX < enemyX + margin and \
            discZ > enemyZ - margin and discZ < enemyZ + margin:
                self.discs.remove(disc)
                self.bulletCount += 1
                disc.remove()
                if self.bossHealth == 1:
                    self.score += 100
                    self.bossHealth -= 1
                    self.transition = True
                    self.nextLevel()
                    return 42
                elif self.bossHealth == 41:
                    self.bossHealth -= 1
                    self.score += 15
                    self.ship.remove()
                    self.ship = loadObject(self.shipType, scale = 5, pos = Point2(-12.66, -20.7))
                    self.ship.setVelocity(Point3(0,0,0))
                elif self.bossHealth == 21:
                    self.bossHealth -= 1
                    self.score += 15
                    self.ship.remove()
                    self.ship = loadObject(self.shipType, scale = 5, pos = Point2(43.12,4))
                    self.ship.setVelocity(Point3(0,0,0))
                else:
                    self.bossHealth -= 1
                    self.score += 15
                return True
        except: pass
        return False

    def checkHitShip(self, laser, timeChange):
        margin = 0.6 #the area surrounding the ship
        shipPos = self.ship.getPos()
        laserPos = laser.getPos()
        shipX = shipPos.getX()
        laserX = laserPos.getX()
        shipZ = shipPos.getZ()
        laserZ = laserPos.getZ()
        if laserX > shipX - margin and laserX < shipX + margin and \
        laserZ > shipZ - margin and laserZ < shipZ + margin:
            if self.shipHealth == 1:
                self.gameOver1(self.level)
            else:
                self.shipHealth -= 1
                self.lasers.remove(laser)
                laser.remove()
                hit = base.loadSfx("EXPLOSM.WAV")
                hit.setVolume(0.6)
                hit.setLoopCount(1)
                hit.play()
            return True
        if laserX > self.xBound or laserX < -self.xBound or \
        laserZ > self.yBound or laserZ < -self.yBound:
            self.lasers.remove(laser)
            laser.remove()
        return False

    def discReturned(self, disc, timeChange):
        margin = 0.8 #the area surrounding the ship
        discPos = disc.getPos()
        shipPos = self.ship.getPos()
        discX = discPos.getX()
        shipX = shipPos.getX()
        discZ = discPos.getZ()
        shipZ = shipPos.getZ()
        if discX > shipX - margin and discX < shipX + margin and \
        discZ > shipZ - margin and discZ < shipZ + margin:
            self.discs.remove(disc)
            self.bulletCount += 1
            disc.remove()
            return True
        return False

    def createMonsters(self):
        self.maxEnemy = 14
        if self.bossHealth < 15 and self.increaseEnemy == False:
            for time in xrange(6):
                self.spawningEnemy.append(200)
            self.increaseEnemy = True
            self.maxEnemy = 20
        elif self.bossHealth == 0:
            self.maxEnemy = 0 #boss is dead, stop making new enemies
        if self.level == 1:
            armyList = ['phoenix', 'voidray', 'sentry', 'carrier']
        if self.level == 2:
            armyList = ['corruptor', 'mutalisk', 'overlord', 'broodlord']
        if self.finishedSpawning == False:
            while len(self.spawningEnemy) < self.maxEnemy:
                count = 0
                if self.level == 1:
                    enemyPos = Point2(random.randint(-16,0), random.randint(-10,10))
                if self.level == 2:
                    enemyPos = Point2(random.randint(-37,10), random.randint(-25,25))
                for enemy1 in self.enemyArmy:
                    if enemy1.getPos() != enemyPos:
                        count += 1
                if count == len(self.enemyArmy):
                    self.spawningEnemy.append(290)
            self.finishedSpawning = True
        if self.extraWall == True:
            if (self.endSurvive-self.currentTime)%4 > -0.02 and \
            (self.endSurvive-self.currentTime)%4 < 0.02:
                self.spawningEnemy.append(290)
        if self.finishedSpawning == True:
            if len(self.spawningEnemy) > 0:
                for enemy in self.spawningEnemy:
                    if enemy == 300:
                        count = 0
                        if self.level == 1:
                            enemyPos = Point2(random.randint(-16,0), random.randint(-10,10))
                        if self.level == 2:
                            enemyPos = Point2(random.randint(-37,10), random.randint(-25,25))
                        for enemy1 in self.enemyArmy:
                            if enemy1.getPos() != enemyPos:
                                count += 1
                        if count == len(self.enemyArmy):
                            if self.level == 1:
                                warpIn = loadObject('warpin2', scale = 5.5, pos = enemyPos)
                            elif self.level == 2:
                                warpIn = loadObject('cocoon2', scale = 4.5, pos = enemyPos)
                            self.warping.append(0)
                            self.warpingIn.append(warpIn)
            if len(self.warping) > 0:
                while 25 in self.warping:
                    warpin = self.warping.index(25)
                    pos = self.warpingIn[warpin].getPos()
                    posX = pos.getX()
                    posY = pos.getZ()
                    self.warpingIn[warpin].remove()
                    self.warping[warpin] += 1
                    if self.level == 1:
                        self.warpingIn[warpin] = loadObject('warpin', \
                        scale = 4.2, pos = Point2(posX, posY))
                    elif self.level == 2:
                        self.warpingIn[warpin] = loadObject('cocoon1', \
                        scale = 4.2, pos = Point2(posX, posY))
                while 50 in self.warping:
                    warpin = self.warping.index(50)
                    enemy = armyList[random.randint(0,3)]
                    enemyPos = self.warpingIn[warpin].getPos()
                    enemyX = enemyPos.getX()
                    enemyY = enemyPos.getZ()
                    enemyPos = Point2(enemyX, enemyY)
                    if enemy == 'sentry':
                        enemyLoad = loadObject(enemy, scale = 4.5, pos = enemyPos)
                    else:
                        enemyLoad = loadObject(enemy, scale = 6.2, pos = enemyPos)
                    self.rotateEnemy(enemyLoad)
                    self.enemyArmy.append(enemyLoad)
                    self.enemyType.append(enemy)
                    self.warping.remove(self.warping[warpin])
                    self.warpingIn[warpin].remove()
                    self.warpingIn.remove(self.warpingIn[warpin])

    def createSameMonsters(self):
        if self.level == 1:
            sprite = 'warpin2'
            sprite1 = 'warpin'
        elif self.level == 2:
            sprite = 'cocoon2'
            sprite1 = 'cocoon1'
        if self.level == 1:
            self.armyList = ['carrier', 'phoenix', 'carrier', 'voidray', 'sentry', \
            'voidray', 'voidray', 'phoenix', 'phoenix', 'sentry', 'sentry', 'sentry']
            enemyPosition = [Point2(-40.95,23.05), Point2(-40.95,0), Point2(-40.95,-23.05), \
                Point2(-8.5, 24), Point2(-1.65, -16.9), Point2(20, 25), Point2(11.52, -23.28),\
                Point2(24.8, 15.2), Point2(24.8, -15.2), Point2(43.3, -23.3), \
                Point2(44.2, 13), Point2(35.2, -1.8)]
        elif self.level == 2:
            self.armyList = ['broodlord', 'corruptor', 'mutalisk', 'corruptor', 'broodlord', 'corruptor', 'overlord', \
            'corruptor', 'corruptor', 'mutalisk', 'mutalisk', 'overlord', 'overlord',\
            'corruptor', 'overlord', 'overlord','mutalisk', 'mutalisk',\
            'overlord', 'overlord', 'overlord']
            enemyPosition = [Point2(-40.95,23.05), Point2(-40.95,11.5), Point2(-40.95,0), \
                Point2(-40.95,-11.5), Point2(-40.95,-23.05), \
                Point2(-8.5, 24), Point2(-1.65, -16.9), Point2(20, 25), Point2(20, -25),\
                Point2(24.8, 13.2), Point2(24.8, -13.2), \
                Point2(20, 7), Point2(20, -7), Point2(38, 25), \
                Point2(37, 13.2), Point2(37, -13.2), Point2(35, 7), Point2(35, -7),
                Point2(43.3, -23.3), Point2(44.2, 13), Point2(35.2, -1.8)]
        if self.finishedSpawningStations == False:
            for station in xrange(len(self.armyList)-3):
                self.constantArmy.append(845)
            self.finishedSpawningStations = True
        for index in xrange(len(self.constantArmy)):
            if self.constantArmy[index] == 850:
                warpIn = loadObject(sprite, scale = 5.5, \
                    pos = enemyPosition[index])
                self.enemyWarping[index] = warpIn
            if self.constantArmy[index] == 875:
                warpIn = loadObject(sprite1, \
                        scale = 4.2, pos = enemyPosition[index])
                self.enemyWarping[index].remove()
                self.enemyWarping[index] = warpIn
            if self.constantArmy[index] == 900:
                self.enemyWarping[index].remove()
                enemyPos = enemyPosition[index]
                enemy = self.armyList[index]
                if enemy == 'sentry':
                    enemyLoad = loadObject(enemy, scale = 4.5, pos = enemyPos)
                else:
                    enemyLoad = loadObject(enemy, scale = 6.2, pos = enemyPos)
                self.rotateEnemy(enemyLoad)
                self.constantArmy[index] = enemyLoad
                self.enemyWarping[index] = 0

    def rotateEnemy(self, enemy):
        shipPos = self.ship.getPos()
        enemyPos = enemy.getPos()
        shipX = shipPos.getX()
        shipY = shipPos.getZ()
        enemyX = enemyPos.getX()
        enemyY = enemyPos.getZ()
        deltaX = shipX - enemyX
        deltaY = shipY - enemyY
        laserSpeed = Vec3(deltaX, 0, deltaY) #yields the direction of return path
        laserSpeed.normalize()
        laserSpeed *= self.bulletSpeed
        try:
            ratio = deltaY/deltaX
        except:
            ratio = deltaY
        newDirection = atan(ratio)*180.0/pi
        if (deltaY > 0) and deltaX > 0:
            enemy.setR(90-newDirection)
        elif deltaY < 0 and deltaX > 0:
            enemy.setR(90-newDirection)
        elif deltaY < 0 and deltaX < 0:
            enemy.setR(270-newDirection)
        else:
            enemy.setR(270-newDirection)
    
    def updateEnemy(self, enemy, timeChange, enemyType, index):
        self.rotateEnemy(enemy)
        laserSpeed = 10
        if (enemyType == 'sentry') or (enemyType == 'overlord'):
            delay = 200
            sprite = 'ammo2'
        if (enemyType == 'voidray') or (enemyType == 'corruptor'):
            delay = 150
            laserSpeed = 20
            sprite = 'sparkle'
        if (enemyType == 'phoenix') or (enemyType == 'mutalisk'):
            delay = 65
            sprite = 'ammo1'
        if (enemyType == 'carrier') or (enemyType == 'broodlord'):
            delay = 250
            sprite = 'ammo3'
        self.generateLasers(enemy, timeChange, enemyType, index, sprite, delay, laserSpeed)
    
    def generateLasers(self, enemy, timeChange, enemyType, index, sprite, delay, laserSpeed):
        if self.timerCount > 100 and self.timerCount % (delay+index*2) == 0 and \
            self.shotTime != self.timerCount:
                self.shotTime = self.timerCount
                shipPos = self.ship.getPos()
                enemyPos = enemy.getPos()
                shipX = shipPos.getX()
                shipY = shipPos.getZ()
                enemyX = enemyPos.getX()
                enemyY = enemyPos.getZ()
                deltaX = shipX - enemyX
                deltaY = shipY - enemyY
                newVel = Vec3(deltaX, 0, deltaY) #yields the direction of return path
                newVel.normalize()
                newVel *= laserSpeed
                position = enemy.getPos() + newVel*0.06
                laser = loadObject(sprite, scale = 0.7)
                laser.setPos(position)
                self.setVelocity(laser, newVel)
                self.lasers.append(laser)
                if enemyType == 'carrier' or enemyType == 'broodlord':
                    laser = loadObject(sprite, scale = 0.7)
                    laser.setPos(position)
                    self.setVelocity(laser,newVel+(0.5,0,-0.5))
                    self.lasers.append(laser)
                    laser = loadObject(sprite, scale = 0.7)
                    laser.setPos(position)
                    self.setVelocity(laser, newVel+(-0.5,0,0.5))
                    self.lasers.append(laser)
                if enemyType == 'sentry' or enemyType == 'overlord':
                    self.makeSplitLasers(enemy, deltaX, deltaY, sprite, \
                        laserSpeed, position)

    def makeSplitLasers(self, enemy, deltaX, deltaY, sprite, laserSpeed, position):
        otherDirs = []
        newVel = Vec3(-deltaY, 0, deltaX)
        otherDirs.append(newVel)
        newVel = Vec3(deltaY, 0, -deltaX)
        otherDirs.append(newVel)
        newVel = Vec3(-deltaX, 0, -deltaY)
        otherDirs.append(newVel)
        for newVel in otherDirs:
            laser = loadObject(sprite, scale = 0.7)
            laser.setPos(position)
            newVel.normalize()
            newVel *= laserSpeed
            self.setVelocity(laser, newVel)
            self.lasers.append(laser)

    def createLifeBar(self):
        try: self.health.remove()
        except: pass
        shipPos = self.ship.getPos()
        shipX = shipPos.getX()
        shipY = shipPos.getZ()
        sprite = str(self.shipHealth)
        if self.shipType == 'viking' or self.shipType == 'wraith2':
            if self.shipHealth >= 10:
                sprite = '10'
            if self.shipHealth >= 1:
                self.health = loadObject("healthbars/health" + sprite, scale = (3.3,1,0.9))
                self.health.setPos(Point3(shipX, 55, shipY + 1.4))
        elif self.shipType == 'battlecruiser':
            if self.shipHealth > 60:
                sprite = '10'
            elif self.shipHealth < 60:
                sprite = str(self.shipHealth/2)
            if self.shipHealth >= 1:
                self.health = loadObject("healthbars/health" + sprite, scale = (3.3,1,0.9))
                self.health.setPos(Point3(shipX, 55, shipY + 1.4))
        try: self.bossBar.remove()
        except: pass
        if self.level == 1:
            try:
                bossPos = self.boss.getPos()
                bossX = bossPos.getX()
                bossY = bossPos.getZ()
                sprite = str(self.bossHealth/6) #boss has 20 health, so this is scaled
                if self.bossHealth >= 1:
                    self.bossBar = loadObject("healthbars/health" + sprite, scale = (5.5,1,1))
                    self.bossBar.setPos(Point3(bossX, 55, bossY + 2))
            except: pass

    def checkWallPos(self, ship, velocity, timeChange):
        for walls in self.walls:
            velocity = self.getVelocity(ship)
            newPos = ship.getPos() + (velocity*timeChange)
            if self.shipType == 'battlecruiser':
                margin = 0.42
            elif self.shipType == 'wraith2' or self.shipType == 'viking':
                margin = 0.57
            if newPos.getX() >= walls[0]-margin and newPos.getX() <= walls[0]+margin \
            and newPos.getZ() > walls[2] and newPos.getZ() < walls[3] \
            and velocity[0] > 0: #These 2 check the left and right bounds. 
                velocity[0] = 0
                self.setVelocity(self.ship, velocity)
                newPos = ship.getPos()
            elif newPos.getX() >= walls[1]-margin and newPos.getX() <= walls[1]+margin \
            and newPos.getZ() > walls[2] and newPos.getZ() < walls[3] \
            and velocity[0] < 0: 
                velocity[0] = 0
                self.setVelocity(self.ship, velocity)
                newPos = ship.getPos()
            elif newPos.getZ() >= walls[2]-margin and newPos.getZ() <= walls[2]+margin\
            and newPos.getX() > walls[0] and newPos.getX() < walls[1] \
            and velocity[2] > 0: #these two check the upper and lower bounds
                velocity[2] = 0
                self.setVelocity(self.ship, velocity)
                newPos = ship.getPos()
            elif newPos.getZ() >= walls[3]-margin and newPos.getZ() <= walls[3]+margin\
            and newPos.getX() > walls[0] and newPos.getX() < walls[1] \
            and velocity[2] < 0: 
                velocity[2] = 0
                self.setVelocity(self.ship, velocity)
                newPos = ship.getPos()

    def checkLaserWall(self, disc, discs, timeChange):
        for walls in self.walls:
            try: velocity = self.getVelocity(disc)
            except: return
            newPos = disc.getPos() + (velocity*timeChange)
            if self.shipType == 'viking' and discs is self.discs:
                if newPos.getX() >= walls[0]+0.55 and newPos.getX() <= walls[0]+2 \
                and newPos.getZ() > walls[2] and newPos.getZ() < walls[3] \
                and velocity[0] > 0: #These 2 check the left and right bounds. 
                    velocity[0] *= -1
                    self.setVelocity(disc, velocity)
                    newPos = disc.getPos()
                elif newPos.getX() >= walls[1]-2 and newPos.getX() <= walls[1]-0.55 \
                and newPos.getZ() > walls[2] and newPos.getZ() < walls[3] \
                and velocity[0] < 0: 
                    velocity[0] *= -1
                    self.setVelocity(disc, velocity)
                    newPos = disc.getPos()
                elif newPos.getZ() >= walls[2]+0.55 and newPos.getZ() <= walls[2]+2 \
                and newPos.getX() > walls[0] and newPos.getX() < walls[1] \
                and velocity[2] > 0: #these two check the upper and lower bounds
                    velocity[2] *= -1
                    self.setVelocity(disc, velocity)
                    newPos = disc.getPos()
                elif newPos.getZ() >= walls[3]-2 and newPos.getZ() <= walls[3]-0.55 \
                and newPos.getX() > walls[0] and newPos.getX() < walls[1] \
                and velocity[2] < 0: 
                    velocity[2] *= -1
                    self.setVelocity(disc, velocity)
                    newPos = disc.getPos()
            else:
                if newPos.getX() > walls[0]+1 and newPos.getX() < walls[1]-1 and \
                newPos.getZ() > walls[2]+1 and newPos.getZ() < walls[3]-1:
                    disc.remove()
                    discs.remove(disc)
                    if discs is self.discs:
                        self.bulletCount += 1
                    return
 
    def makeWalls(self):
        if self.level == 1:
            self.walls = [[-42,-26,9,13],[-36,-32,3,19],[-36,-32,-19,-3],
            [-42,-26,-13,-9],[-22,6,16,20],[20,40,17,21],[20,40,-21,-17],
            [18.2,22.2,2.8,20.8], [18.2,22.2,-20.8,-2.8], [28,32,-14,14],
            [1,5,-29,-15],[-18.2,-4.2,-18.8,-14.8],[-20,-16,-29,-15],
            [37,49,6.2,10.2], [37, 49, -7.2, -3.2], [35.2,39.2,-0.9,9.9]]
        elif self.level == 2:
            self.walls = [[28.2,32.2,-29,-15],[30.2,42.2,-18.8,-14.8],[28.2,32.2,15,29],\
            [30.2,42.2,14.8,18.8],[28,32,-13,13], [12,16,-13,13],\
            [12,16,-29,-15],[14,26,-18.8,-14.8],[12,16,15,29],[14,26,14.8,18.8]]
        if self.level == 2:
            if self.ship.getPos().getX() < 9 and self.extraWall == False:
                self.walls.append([12,16,-29,29])
                self.extraWall = True
                self.startSurvive = time.time()
                self.endSurvive = time.time() + 120
                self.seconds = 60
                self.playSFX()
        for wall in self.walls:
            deltaX = wall[1] - wall[0]
            deltaY = wall[3] - wall[2]
            if deltaX > deltaY:
                yScale = 1.5
                xScale = deltaX - 2
            else:
                xScale = 1.5
                yScale = deltaY - 2
            xCenter = deltaX / 2.0 + wall[0]
            yCenter = deltaY / 2.0 + wall[2]
            self.wall = loadObject('laserwall3', scale = (xScale, 2, yScale))
            self.wall.setPos(Point3(xCenter, 55, yCenter))
            self.wallLoaded.append(self.wall)

    def drawCountDown(self):
        try: self.countDown.remove()
        except: pass
        self.countDown = OnscreenText("Time Remaining: %0.2f" % ((self.endSurvive - time.time())%120%1000),\
            pos = (0, 0.70), fg = (250,20,0,20), align = TextNode.ACenter, scale = 0.1)


    def gameOver1(self, level = 1):
        self.alive = False
        self.timeEnd = time.time()
        self.keys['restart'] = 0
        self.level = level

    def restartGame(self, level):
        if self.alive == False and self.nextLevelGo == False:
            self.accept("r", self.setKey, ["restart", 0])
            try: self.gameOverLine1.remove()
            except: pass
            try: self.gameOverLine2.remove()
            except: pass
            try: self.gameOverLine3.remove()
            except: pass
            try: self.gameOverScreen.remove()
            except: pass
            try: self.countDown.remove()
            except: pass
            self.showScore.remove()
            self.objective.remove()
            self.gameOverScreen = loadObject('gameover', scale = (40,100,35))
            self.gameOverLine1 = OnscreenText(text = \
                "Time elapsed: %d minutes and  %0.3f seconds" %\
                ((self.timeEnd - self.timeStart)/60, (self.timeEnd-self.timeStart)%60%1000),\
                pos = (0, 0.26), fg=(20,20,0,20),
                align = TextNode.ACenter, scale = 0.1)
            self.gameOverLine2 = OnscreenText('Your Score: %d' % (self.score),\
                pos = (0, 0.14), fg=(20,20,0,20), align = TextNode.ACenter, scale = 0.1)
            self.gameOverLine3 = OnscreenText('Click anywhere to continue',\
                pos = (0, 0), fg=(20,20,0,20), align = TextNode.ACenter, scale = 0.1)
            base.cam.setPos(0,5,0)
            self.accept("mouse1", self.setStart, ["start", 3])
        elif self.nextLevelGo == True:
            try: self.gameOverScreen.remove()
            except: pass
            try: self.gameOverLine3.remove()
            except: pass
            try: self.countDown.remove()
            except: pass
            self.gameOverScreen = loadObject('nextlevel', scale = (36, 100, 27))
            base.cam.setPos(0,5,0)
            self.gameOverLine3 = OnscreenText('Click anywhere to continue',\
                pos = (0, 0), fg=(20,20,0,20), align = TextNode.ACenter, scale = 0.1)
            self.accept("mouse1", self.setStart, ["start", 3])
        if self.start['start'] == 3:
            self.keys["restart"] = 0
            self.accept("space",          self.setKey, ["shoot", 0])
            self.accept("s", self.setKey, ["continue", 0])
            self.leftBound.remove()
            self.rightBound.remove()
            self.upBound.remove()
            self.lowerBound.remove()
            base.cam.setPos(0,0,0)
            self.ship.remove()
            self.bg.remove()
            if len(self.discs) > 0:
                for disc in self.discs:
                    disc.remove()
            if len(self.lasers)>  0:
                for laser in self.lasers:
                    laser.remove()
            if len(self.enemyArmy) > 0:
                for enemy in self.enemyArmy:
                    enemy.remove()
            if len(self.constantArmy) > 0:
                for enemy in self.constantArmy:
                    if type(enemy) != int:
                        enemy.remove()
            if len(self.warpingIn) > 0:
                for enemy in self.warpingIn:
                    enemy.remove()
            if len(self.wallLoaded) > 0:
                for wall in self.wallLoaded:
                    wall.remove()
            self.boss.remove()
            self.alive = True
            self.gameOverScreen.remove()
            self.gameOverLine3.remove()
            if self.nextLevelGo == False:
                self.gameOverLine1.remove()
                self.gameOverLine2.remove()
                self.gameOverLine3.remove()
            for child in camera.getChildren():
                if str(child) != 'render/camera/cam':
                    child.remove()
            if self.nextLevelGo == False:
                self.__init__(level, 0, time.time(), False)
            elif self.nextLevelGo == True:
                self.__init__(level, self.score, self.timeStart, True)
            return True
        return False

    def nextLevel(self): 
        self.level += 1
        self.nextLevelGo = True
        self.gameOver1(self.level)

Stage() #makes the world and all its objects
run()


""" CITATIONS: PANDA3D TASKS TUTORIAL FOR THE 2 VELOCITY FUNCTIONS:
http://www.panda3d.org/manual/index.php/Tasks
"""
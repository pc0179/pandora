#!/usr/bin/python

import sys
import random
import argparse
import xml.etree.ElementTree
import math

sys.path.append('/home/xrubio/workspace/pandora/pandora/pyPandora/')
sys.path.append('/home/xrubio/workspace/pandora/pandora/')

from pyPandora import Simulation, Agent, World, Point2DInt

def enum(**enums):
	""" converts a sequence of values to an C++ style enum """
	return type('Enum', (), enums)

terrainTypes = enum(ePastures=0, eFields=1)

class FrontierConfig():
	def __init__(self):
		return
	
	def deserialize(self, xmlFile):
		tree = xml.etree.ElementTree.parse(xmlFile)
		root = tree.getroot()

		self._resultsFile = str(root.find('output').get('resultsFile'))
		self._logsDir = str(root.find('output').get('logsDir'))

		self._size = Point2DInt(int(root.find('size').get('width')), int(root.find('size').get('height')))
		self._numSteps = int(root.find('numSteps').get('value'))
		self._serializeResolution = int(root.find('numSteps').get('serializeResolution'))

		# r_0 in the logistic growth model
		self._asabiyaIncrease = float(root.find('asabiya').get('increase'))
		# exponential decay of asabiya
		self._asabiyaDecay = float(root.find('asabiya').get('decay'))
		# minimal value of average asabiya of an empire
		self._minAsabiya = float(root.find('asabiya').get('min'))
		
		# parameter fixing the influence of distance from political center to asabiya
		self._distanceSensibility = float(root.find('conflict').get('distanceSensibility'))
		# the attack value must be superior to attackThreshold in order to conquer a neighbouring cell
		self._attackThreshold = float(root.find('conflict').get('attackThreshold'))

class Empire(Agent):
	""" An empire created during the simulation """
	
	def __init__(self, id):
		Agent.__init__( self, id)

		self._averageAsabiya= 0.0
		self._empireId = 0
		self._numRegions = 1

	def updateNumRegions(self):
		self._numRegions = 0
		index = Point2DInt(0,0)
		for index._x in range(0, self.getWorld()._config._size._x):
			for index._y in range(0, self.getWorld()._config._size._y):
				if self.getWorld().getValue("id", index) == self._empireId:
					self._numRegions += 1
		#print 'empire: ' + self.id + ' has: ' + str(self._numRegions) + ' regions'

	def calculateAverageAsabiya(self):
		self._averageAsabiya = 0.0

		index = Point2DInt(0,0)
		for index._x in range(0, self.getWorld()._config._size._x):
			for index._y in range(0, self.getWorld()._config._size._y):
				if self.getWorld().getValue("id", index) == self._empireId:
					self._averageAsabiya = self._averageAsabiya + float(self.getWorld().getValue("asabiya", index)/1000.0)

		self._averageAsabiya = self._averageAsabiya/self._numRegions
		#print "empire: " + self.id + " has average asabiya: " + str(self._averageAsabiya) + " containing: " + str(self._numRegions) + " regions"


	def calculateCentre(self):	
		centre = Point2DInt(0,0)

		index = Point2DInt(0,0)
		for index._x in range(0, self.getWorld()._config._size._x):
			for index._y in range(0, self.getWorld()._config._size._y):
				if self.getWorld().getValue("id", index) == self._empireId:
					centre._x = centre._x + index._x
					centre._y = centre._y + index._y

		centre._x = centre._x / self._numRegions 
		centre._y = centre._y / self._numRegions 
		self.position = centre
		#print "centre of empire: " + self.id + " is: " +str(centre._x) + '/' + str(centre._y)

	def updateState(self):
		self.updateNumRegions()

		# if it has collapsed do nothing
		if self._numRegions==0 :
			return

		self.calculateAverageAsabiya()
		self.calculateCentre()

	def registerAttributes(self):
		self.registerIntAttribute('average asabiya x100')
		self.registerIntAttribute('num regions')
	
	def serialize(self):
		self.serializeIntAttribute('average asabiya x100', int(100.0*self._averageAsabiya))
		self.serializeIntAttribute('num regions', self._numRegions)

class Frontier(World):

	def __init__(self, simulation, config ):
		World.__init__( self, simulation, 1, 1, config._resultsFile)
		self._config = config
		self._numEmpires = 1

	def createRasters(self):
		self.registerDynamicRaster("id", 1)
		self.registerDynamicRaster("asabiya", 1)
		self.registerDynamicRaster("executed", 0)
		self.registerDynamicRaster("boundary", 1)
		self.getDynamicRaster("id").setInitValues(0, 10000, 0)
		self.getDynamicRaster("asabiya").setInitValues(0, 10000, 500)
		self.getDynamicRaster("executed").setInitValues(0, 1, 0)
		self.getDynamicRaster("boundary").setInitValues(0, 1, 0)

	def createAgents(self):
		newEmpire = Empire('Empire_1')
		newEmpire._empireId = self._numEmpires
		self.addAgent(newEmpire)
		#newEmpire.setRandomPosition()
		newEmpire.position = Point2DInt(1,1)
		self._numEmpires += 1

		# first empire has a 3x3 zone
		index = Point2DInt(0,0)
		#print 'centre of empire : ' + str(newEmpire.position._x) + '/' + str(newEmpire.position._y)
		for index._x in range(newEmpire.position._x-1, newEmpire.position._x+2):
			for index._y in range(newEmpire.position._y-1, newEmpire.position._y+2):
				if self.checkPosition(index):
					self.setValue("id", index, newEmpire._empireId)
		newEmpire.updateState()

	def isEmpireBoundary(self, region):
		index = Point2DInt(region._x-1, region._y)
		if self.checkPosition(index) and self.getValue("id", index)!=self.getValue("id", region):
			return True

		index._x = region._x+1
		if self.checkPosition(index) and self.getValue("id", index)!=self.getValue("id", region):
			return True

		index._x = region._x
		index._y = region._y-1
		if self.checkPosition(index) and self.getValue("id", index)!=self.getValue("id", region):
			return True

		index._y = region._y+1
		if self.checkPosition(index) and self.getValue("id", index)!=self.getValue("id", region):
			return True
		return False

	def calculateAsabiya(self):
		index = Point2DInt(0,0)
		for index._x in range(0, self._config._size._x):
			for index._y in range(0, self._config._size._y):
				if self.isEmpireBoundary(index):
					self.setValue("boundary", index, 1)
					asabiya = float(self.getValue("asabiya", index)/1000.0)
					newAsabiya = asabiya + self._config._asabiyaIncrease*asabiya*(1.0-asabiya)
					self.setValue("asabiya", index, int(1000.0*newAsabiya))
					#print '\tcell: ' + str(index._x) + "/" + str(index._y) + ' boundary had asabiya: ' + str(asabiya) + ' now: ' + str(self.getValue("asabiya", index)/1000.0)
				else:
					self.setValue("boundary", index, 0)
					asabiya = float(self.getValue("asabiya", index)/1000.0)
					newAsabiya = asabiya - self._config._asabiyaDecay*asabiya
					# value must not be 0
					self.setValue("asabiya", index, max(1, int(1000.0*newAsabiya)))
					#print '\tcell: ' + str(index._x) + "/" + str(index._y)+ ' NOT boundary had asabiya: ' + str(asabiya) + ' now: ' + str(self.getValue("asabiya", index)/1000.0)

	def cleanEmpireRaster(self, empireId):
		index = Point2DInt(0,0)
		for index._x in range(0, self._config._size._x):
			for index._y in range(0, self._config._size._y):
				if self.getValue("id", index)==empireId:
					self.setValue("id", index, 0)


	def checkCollapse(self):
		index = Point2DInt(0,0)
		for index._x in range(0, self._config._size._x):
			for index._y in range(0, self._config._size._y):
				empireIds = self.getAgentIds(index, 'Empire')
				for empireId in empireIds:
					empire = self.getAgent(empireId)
					#print "empire: " + empireId + " has average asabiya: " + str(empire._averageAsabiya)
					"""
					TODO which option is better?
					if empire._averageAsabiya<self._config._minAsabiya:
						print "empire: " + empireId + " collapses"
						self.cleanEmpireRaster(empire._empireId)
						empire._numRegions = 0
						self.removeAgent(empire)
					"""
					if empire._numRegions==0:
						#print "empire: " + empireId + " collapses"
						self.cleanEmpireRaster(empire._empireId)
						empire._numRegions = 0
						empire.remove()

	def attack(self, attacker, defender):
	
		# out of boundaries
		if not self.checkPosition(defender):
			return

		# same empire, not attack
		if self.getValue("id", attacker)!=0 and self.getValue("id", defender)==self.getValue("id", attacker):
			return
		
		numAttackingRegions = 1
		numDefendingRegions = 1
		averageAttackingAsabiya = self.getValue("asabiya", attacker)/1000.0
		averageDefendingAsabiya = self.getValue("asabiya", defender)/1000.0
		distToAttackingCentre = 0
		distToDefendingCentre = 0

		# attacker not empire
		if self.getValue("id", attacker)!=0:
			attackingEmpire = self.getAgent("Empire_"+str(self.getValue("id", attacker)))
			numAttackingRegions = attackingEmpire._numRegions
			averageAttackingAsabiya = attackingEmpire._averageAsabiya
			distToAttackingCentre = attackingEmpire.position.distance(attacker)

		if self.getValue("id", defender)!=0:
			defendingEmpire = self.getAgent("Empire_"+str(self.getValue("id", defender)))
			numDefendingRegions = defendingEmpire._numRegions
			averageDefendingAsabiya = defendingEmpire._averageAsabiya
			distToDefendingCentre = defendingEmpire.position.distance(defender)
	
		powerAttacker = numAttackingRegions*averageAttackingAsabiya*math.exp(-distToAttackingCentre/self._config._distanceSensibility)
		powerDefender = numDefendingRegions*averageDefendingAsabiya*math.exp(-distToDefendingCentre/self._config._distanceSensibility)
		
		#print "\tattack from : " + str(attacker._x) + '/' + str(attacker._y) + ' to: ' +  str(defender._x) + '/' + str(defender._y) + " power att: " + str(powerAttacker) + " power def: " + str(powerDefender) + " diff: " + str(powerAttacker-powerDefender) + " thresh: " + str(self._config._attackThreshold)

		self.setValue("executed", attacker, 1)
		if(powerAttacker-powerDefender>self._config._attackThreshold):
			self.setValue("executed", defender, 1)
			# losing empire
			if self.getValue("id", defender)!=0:
				defendingEmpire = self.getAgent("Empire_"+str(self.getValue("id", defender)))
				defendingEmpire._numRegions -= 1
#				print "\tdefending empire: " + str(defendingEmpire._empireId) + " lost cell"

			# new empire!
			if self.getValue("id", attacker)==0:
				newEmpire = Empire("Empire_"+str(self._numEmpires))
				newEmpire._averageAsabiya = self.getValue("asabiya", attacker)/1000.0
				newEmpire._numRegions = 2
				newEmpire._empireId = self._numEmpires

				# update of cells
				self.setValue("id", attacker, newEmpire._empireId)
				self.setValue("id", defender, newEmpire._empireId)
				self.setValue("asabiya", defender, int(newEmpire._averageAsabiya*1000.0))
				self._numEmpires += 1
				
				self.addAgent(newEmpire)
				newEmpire.position = attacker
#				print "\tcreation of new empire: " + str(newEmpire._empireId)

			else:
				attackingEmpire = self.getAgent("Empire_"+str(self.getValue("id", attacker)))
				attackingEmpire._numRegions += 1

				self.setValue("id", defender, attackingEmpire._empireId)
				self.setValue("asabiya", defender, int(attackingEmpire._averageAsabiya*1000.0))
#				print "\tattacking empire: " + str(attackingEmpire._empireId) + " conquered cell"
#		else:
#			print "\tattack failed"


	def checkConflicts(self):

		index = Point2DInt(0,0)
		potentialAttackers = []
		for index._x in range(0, self._config._size._x):
			for index._y in range(0, self._config._size._y):
				if self.isEmpireBoundary(index):
					potentialAttackers.append(Point2DInt(index._x, index._y))

		# randomize conflicts
		random.shuffle(potentialAttackers)
		for attacker in potentialAttackers:
			if self.getValue("executed", attacker)==0:			
				#print 'checking attacks from empire: ' + str(self.getValue("id", attacker)) + " at position: " + str(attacker._x) + "/" + str(attacker._y)
				self.attack(attacker, Point2DInt(attacker._x-1, attacker._y))
				self.attack(attacker, Point2DInt(attacker._x+1, attacker._y))
				self.attack(attacker, Point2DInt(attacker._x, attacker._y-1))
				self.attack(attacker, Point2DInt(attacker._x, attacker._y+1))
		
		# clean executed raster
		index = Point2DInt(0,0)
		for index._x in range(0, self._config._size._x):
			for index._y in range(0, self._config._size._y):
				self.setValue("executed", index, 0)
	
	def stepEnvironment(self):
		self.calculateAsabiya()
		self.checkConflicts()
		self.checkCollapse()

		return

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-x', '--config', default='config.xml', help='config file')
	args = parser.parse_args()
	config = FrontierConfig()
	config.deserialize(args.config)

	#print('size: '+str(config._size)+' num steps:'+str(config._numSteps))
	mySimulation = Simulation(config._size, config._numSteps, config._serializeResolution)
	frontier = Frontier(mySimulation, config)
	frontier.initialize()
	frontier.run()
 
if __name__ == "__main__":
	main()


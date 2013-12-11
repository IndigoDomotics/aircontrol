#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2013, Perceptive Automation, LLC. All rights reserved.
# http://www.perceptiveautomation.com
#
# This source is freely available to use by anyone for any purpose.

import indigo
import urllib2
import xml.etree.ElementTree as ET
import re
import socket

# All known elements delivered by AirControl except 'name' which we'll specifically
# find when doing an update. We use that as a key - if it changes then we'll update
# all the other states as well. Otherwise we'll just skip the update since nothing has
# changed.
validTags = ["type", "certification", "cetification", "released", "runtime", "coverArtURL", "overview", "studio", "genre", "album", "artistName", "copyright", "trackNumber", "trackCount", "seasonName", "tagline", "category", "viewcount"]

# The list of apps that have categories available.
# There are a few others, but Apple managed to make the return XML invalid (they include
# characters that aren't appropriately encoded) so these are just the ones I quickly confirmed
appsWithCategories = ["com.apple.frontrow.appliance.movies",
					  "com.apple.frontrow.appliance.music",
					  "com.apple.frontrow.appliance.tv",
					  "com.apple.frontrow.appliance.xbmc",
					  "com.apple.frontrow.appliance.CouchSurfer",
					  "com.firecore.maintenance",
					 ]

# Static text (not markup) that's returned when nothing is playing. Totally unclear why
# it's an unformatted text message rather than XML like all other replies. Sigh.
noMediaPlaying = "There is currently no media playing"

################################################################################
def isValidHostname(hostname):
	if len(hostname) > 255 or len(hostname) < 1:
		return False
	if hostname[-1] == ".":
		hostname = hostname[:-1] # strip exactly one dot from the right, if present
	allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
	return all(allowed.match(x) for x in hostname.split("."))

################################################################################
class Plugin(indigo.PluginBase):
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = pluginPrefs.get("showDebugInfo", False)
		self.activeDevices = {}
		socket.setdefaulttimeout(3)

	########################################
	def runConcurrentThread(self):
		try:
			while True:
				for devId, dev in self.activeDevices.items():
					try:
						reply = urllib2.urlopen("http://%s/npx" % dev.address)
					except:
						self.debugLog("Device %s is not available on the network or isn't responding to the media query" % dev.name)
						dev.setErrorStateOnServer("Device unavailable")
						continue
					try:
						replyString = reply.read()
						nowplaying = ET.fromstring(replyString)
					except Exception, e:
						if replyString != noMediaPlaying:
							self.debugLog("API exception: \n%s" % str(e))
							self.debugLog("API returned this when trying to get the current media information: \n\n%s" % replyString)
						# Player isn't playing - for some reason AirControl doesn't
						# deliver a valid XML file when there's nothing playing - it just
						# replies with this text: "There is currently no media playing"
						# Silly I know...
						for state in validTags:
							# hurray for typos in XML element names!
							if state != "type" and state != "cetification":
								dev.updateStateOnServer(key=state, value="")
						dev.updateStateOnServer(key="type", value="No Media Playing")
						dev.updateStateOnServer(key="name", value="")
						dev.updateStateOnServer(key="playStatus", value="stopped")
						continue
					if nowplaying.tag != "nowplaying":
						self.debugLog("Data for device %s is not valid:\n\n%s" % (dev.name, replyString))
						dev.setErrorStateOnServer("Device data invalid")
						continue
					# We should have valid XML at this point. Get the "name" element and see if it's
					# changed. If not then we'll skip doing any state updates.
					dev.updateStateOnServer(key="playStatus", value="playing")
					nameList = nowplaying.findall('name')
					if len(nameList) != 1:
						self.debugLog("Data for device %s is not valid:\n\n%s" % (dev.name, replyString))
						dev.setErrorStateOnServer("Device data invalid")
						continue
					nameElement = nameList[0]
					if nameElement.text != dev.states["name"]:
						dev.updateStateOnServer(key='name', value=nameElement.text)
						self.debugLog("Media being played changed to: \n%s" % replyString)
						stateList = list(validTags)
						for child in nowplaying:
							self.debugLog("    tag: %s, text: %s" % (child.tag, child.text))
							if child.tag in validTags:
								stateList.remove(child.tag)
								# they have a typo in their XML element name sometimes so we have to fix it here
								if child.tag == "cetification":
									self.debugLog("cetification found, updating certification state with: %s" % child.text)
									dev.updateStateOnServer(key="certification", value=child.text)
									stateList.remove("certification")
								else:
									if child.tag == "type":
										val = child.text.lower()
									else:
										val = child.text
									dev.updateStateOnServer(key=child.tag, value=val)
						for state in stateList:
							# unbelieveable number of exceptions because of their typo...
							if state != "cetification":
								dev.updateStateOnServer(key=state, value="")
				self.sleep(3)
		except self.StopThread:
			pass	# Optionally catch the StopThread exception and do any needed cleanup.

	########################################
	def deviceStartComm(self, dev):
		self.debugLog("Starting device %s" % dev.name)
		self.activeDevices[dev.id] = dev

	########################################
	def deviceStopComm(self, dev):
		self.debugLog("Stopping device %s" % dev.name)
		if dev.id in self.activeDevices:
			del self.activeDevices[dev.id]

	########################################
	# Actions defined in MenuItems.xml:
	####################
	def wakeAtv(self):
		self.debugLog("wake menu item")
		pass

	####################
	def sleepAtv(self):
		self.debugLog("sleep menu item")
		pass

	########################################
	# Dialog methods
	########################################
	def validateDeviceConfigUi(self, valuesDict, typeId, devId):
		errorsDict = indigo.Dict()
		if "address" not in valuesDict:
			errorsDict["address"] = 'You must specify a host name or IP address.'
		else:
			if not isValidHostname(valuesDict["address"]):
				errorsDict["address"] = 'You must specify a valid host name or IP address.'
		if len(errorsDict):
			return (False, valuesDict, errorsDict)
		return (True, valuesDict)

	########################################
	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		# Since the dialog closed we want to set the debug flag - if you don't directly use
		# a plugin's properties (and for debugLog we don't) you'll want to translate it to
		# the appropriate stuff here. 
		if not userCancelled:
			self.debug = valuesDict.get("showDebugInfo", False)
			if self.debug:
				indigo.server.log("Debug logging enabled")
			else:
				indigo.server.log("Debug logging disabled")
	
	########################################
	# Plugin Actions object callbacks (pluginAction is an Indigo plugin action instance)
	######################
	def sendButtonPress(self, pluginAction):
		self.debugLog("sendButtonPress action called:\n" + str(pluginAction))
		if pluginAction.deviceId in self.activeDevices:
			dev = self.activeDevices[pluginAction.deviceId]
			key = pluginAction.props.get("keyToPress", None)
			if not key:
				self.errorLog("Send Button Press: no button selected")
				return
			try:
				reply = urllib2.urlopen("http://%s/remoteAction=%s" % (dev.address, key))
				return
			except:
				self.errorLog("Send Button Press: device %s is not available on the network" % dev.name)
				return
		self.errorLog("Send Button Press: device %i doesn't appear to be available or enabled" % pluginAction.deviceId)

	######################
	def goToApp(self, pluginAction):
		self.debugLog("goToApp action called:\n" + str(pluginAction))
		if pluginAction.deviceId in self.activeDevices:
			dev = self.activeDevices[pluginAction.deviceId]
			app = pluginAction.props.get("app", None)
			force = pluginAction.props.get("force", False)
			if not app:
				self.errorLog("Go To App: no app selected" % dev.name)
				return
			category = None
			if pluginAction.props.get("categoryAvailable", False):
				category = pluginAction.props.get("category", None)
			try:
				if force and dev.states["playStatus"] == "playing":
					reply = urllib2.urlopen("http://%s/remoteAction=1" % dev.address)
			except:
				self.debugLog("Go To App: couldn't force stop")
				return
			try:
				url = "http://%s/plugin=%s" % (dev.address, app)
				if category:
					url = "%s/%s" % (url, category)
				self.debugLog("Go To App: url: %s" % url)
				reply = urllib2.urlopen(url)
				return
			except:
				self.errorLog("Go To App: device %s is not available on the network" % dev.name)
				return
		self.errorLog("Go To App: device %i doesn't appear to be available or enabled" % pluginAction.deviceId)

	######################
	# Callback to build the list of available apps from the Apple TV
	######################
	def getAppList(self, filter="", valuesDict=None, typeId="", targetId=0):
 		self.debugLog("getAppList targetId: %i, valuesDict: %s" % (targetId, str(valuesDict)))
		itemList = []
		dev = indigo.devices[targetId]
		if not dev:
			self.errorLog("Device %i no longer exists")
		else:
			try:
				reply = urllib2.urlopen("http://%s/apl" % dev.address)
			except:
				self.errorLog("Device %s is not available on the network or isn't responding to the application list query" % dev.name)
				return itemList
			try:
				replyString = reply.read()
				applianceList = ET.fromstring(replyString)
			except Exception, e:
				self.errorLog("API exception: \n%s" % str(e))
				self.errorLog("API returned this when trying to get the app list: \n\n%s" % replyString)
				return itemList
			if applianceList.tag != "applianceList":
				self.errorLog("Appliance list for device %s is not valid:\n\n%s" % (dev.name, replyString))
				return itemList
			# We should have valid XML at this point.
			for child in applianceList:
				self.debugLog("    attributes: %s" % str(child.attrib))
				itemList.append((child.attrib["identifier"], child.attrib["name"]))
		return sorted(itemList, key=lambda appliance: appliance[1])
	
	######################
	# Callback called when the selected app changes - gives us the opportunity to show/hide the category list
	# based on whether the app has static categories.
	########################################
	def appSelected(self, valuesDict, typeId="", devId=None):
		self.debugLog("appSelected called")
		app = valuesDict.get("app", None)
		if app in appsWithCategories:
			valuesDict["categoryAvailable"] = True
		else:
			valuesDict["categoryAvailable"] = False
		return valuesDict

	######################
	# Callback to build the list of available categories for the selected app (if any)
	######################
	def getCategoryList(self, filter="", valuesDict=None, typeId="", targetId=0):
 		self.debugLog("getCategryList valuesDict: %s" % str(valuesDict))
 		theSelectedApp = valuesDict.get("app", None)
 		self.debugLog("getCategoryList: theSelectedApp: %s" % theSelectedApp)
		itemList = []
 		if theSelectedApp in appsWithCategories:
			dev = indigo.devices[targetId]
			if not dev:
				self.errorLog("Device %i no longer exists")
			else:
				try:
					reply = urllib2.urlopen("http://%s/appcat=%s" % (dev.address, theSelectedApp))
				except:
					self.errorLog("Device %s is not available on the network or isn't responding to the application category query" % dev.name)
					return itemList
				try:
					replyString = reply.read()
					categoryList = ET.fromstring(replyString)
				except Exception, e:
					self.errorLog("API exception: \n%s" % str(e))
					self.errorLog("API returned this when trying to get the app list: \n\n%s" % replyString)
					return itemList
				if categoryList.tag != "categories":
					self.errorLog("Appliance list for device %s is not valid:\n\n%s" % (dev.name, replyString))
					return itemList
				# We should have valid XML at this point.
				for child in categoryList:
					self.debugLog("    attributes: %s" % str(child.attrib))
					itemList.append((child.attrib["identifier"], child.attrib["name"]))
		return sorted(itemList)

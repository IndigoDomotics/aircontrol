#AirControl

This plugin allows you to create Apple TV devices from Apple TV's that have been jailbroken and have aTVFlash installed. Included with aTVFlash is an extra called AirControl which allows remote client applications to get information about currently playing media and control the Apple TV as if with an actual physical remote.

Jailbreaking and installing aTVFlash is solely the responsibility of the owner - see the FireCore.com website for details.

##Downloading for use

If you are a user and just want to download and install the plugin, click on the "Download Zip" button to the right and it will download the plugin and readme file to a folder in your Downloads directory called "aircontrol". Once it's downloaded just open that folder and double-click on the "AirControl.indigoPlugin" file to have the client install and enable it for you.

##Contributing

If you want to contribute, just clone the repository in your account, make your changes, and issue a pull request. Make sure that you describe the change you're making thoroughly - this will help the repository managers accept your request more quickly.

##Terms

Perceptive Automation is hosting this repository and will do minimal management. Unless a pull request has no description or upon cursory observation has some obvious issue, pull requests will be accepted without any testing by us. We may choose to delegate commit privledges to other users at some point in the future.

We (Perceptive Automation) don't guarantee anything about this plugin - that this plugin works or does what the description above states, so use at your own risk. We will attempt to answer questions about the plugin but we can't help with the jailbreaking process or installing aTVFlash.

##Plugin ID

Here's the plugin ID in case you need to programmatically restart the plugin:

**Plugin ID**: com.perceptiveautomation.opensource.aircontrol

##Technical Details

The documentation on the capabilities for AirControl are scattered around the FireCore site a bit, so I'm going to add what I find here. First, these are the states that I'm presenting:

* type (movie, tv-episode, song, music video, streaming video, live video, advertisement, video clip, yt video, podcast-episode)
* name
* certification (sometimes misspelled cetification - it's the movie or tv show rating)
* released (date it was released)
* runtime (how long it is)
* coverArtURL (a URL to the cover art for the media - can't do much with it yet but it could be cool)
* overview (a description of the media)
* studio (production studio)
* genre
* album
* artistName
* copyright (long copyright information)
* trackNumber
* trackCount
* seasonName
* tagline (a short tag for the media)
* category
* viewcount

I'm skipping the &lt;credits&gt; element because it's hierarchical and potentially repetitive (multiple case members, etc.). I believe everything else is getting passed through. The only normalization of the data that I'm currently doing is lowercasing the type since I've seen both Movie and movie used. Also, I'm dealing with the occasional misspelling of certification (cetification) in the XML. That bug really should be fixed by the FireCore guys.

There's a separate file in the repo called AirControl Examples.txt that has a bunch of &lt;nowplaying&gt; examples from the various apps (called appliances).

The [main article about the API](http://support.firecore.com/entries/21375902-3rd-Party-Control-API-AirControl-beta-) has most information though more was gleaned from the [AirControl support thread](http://forum.firecore.com/topic/8574). I'm going to repeat the control parts here to try and make it a bit more of a cohesive whole.

The control api is just a simple action=value path after the host part of a URL (it's a GET so you can do it easily in the browser). So, if our Apple TV's name is "Apple TV" then the host name (if you're on the local network) is "apple-tv.local" (you can also use the IP of course). To mimic a press of the menu button, you'd do this:

	http://apple-tv.local/remoteAction=1

The action is "remoteAction" and the menu button is represented by 1. This is the list of actions as far as I've gleaned them so far:

* remoteAction
* plugin
* wake (always use wake=1)
* sleep (always use sleep=1)
* kf (relaunches the AppleTV, always use kf=1)

We'll talk more about the first two - the last three are pretty self-explanatory. Here are the valid remoteAction values:

* Menu = 1
* Menu Hold = 2
* Arrow Up = 3
* Arrow Down = 4
* Select = 5
* Arrow Left = 6
* Arrow Right = 7
* Play/Pause = 10
* Pause = 15
* Play = 16
* Stop = 17
* Fast Forward = 18
* Rewind = 19
* Chapter Skip Forward = 20
* Chapter Skip Backwards = 21
* List/Select Hold = 22

So sending any of those remote commands is also pretty straight-forward.

The plugin action allows you to jump directly to that app - so with a single command you can jump directly to, say, the Netflix app. There is a discovery protocol for getting the available apps - you use this command:

	http://apple-tv.local/apl

and you'll get back an XML document that looks something like this:

	<applianceList>
		<appliance name="Computers" identifier="com.apple.frontrow.appliance.computers"/>
		<appliance name="Movies" identifier="com.apple.frontrow.appliance.movies"/>
		<appliance name="Music" identifier="com.apple.frontrow.appliance.music"/>
		<appliance name="Settings" identifier="com.apple.frontrow.appliance.settings"/>
		<appliance name="TV Shows" identifier="com.apple.frontrow.appliance.tv"/>
		<appliance name="Browser" identifier="com.apple.frontrow.appliance.CouchSurfer"/>
		<appliance name="XBMC" identifier="com.apple.frontrow.appliance.xbmc"/>
		<appliance name="Maintenance" identifier="com.firecore.maintenance"/>
		<appliance name="HBO GO" identifier="vega"/>
		<appliance name="Netflix" identifier="netflix"/>
		<appliance name="Qello" identifier="qello"/>
		<appliance name="Podcasts" identifier="internet-podcasts"/>
		<appliance name="Vimeo" identifier="vimeo"/>
		<appliance name="Sky News" identifier="skynews"/>
		<appliance name="MobileMe" identifier="dot-mac"/>
		<appliance name="Flickr" identifier="flickr"/>
		<appliance name="NBA" identifier="nba"/>
		<appliance name="WSJ Live" identifier="wsj"/>
		<appliance name="Trailers" identifier="movie-trailers-v2"/>
		<appliance name="Vevo" identifier="com.vevo.appletv"/>
		<appliance name="Radio" identifier="internet-radio-stations"/>
		<appliance name="Hulu Plus" identifier="hulu"/>
		<appliance name="MLS" identifier="com.mlssoccer.appletv"/>
		<appliance name="What's New" identifier="apollo"/>
		<appliance name="Disney Junior" identifier="com.disney.junior.appletv"/>
		<appliance name="Crunchyroll" identifier="crunchyroll"/>
		<appliance name="MLB.TV" identifier="flagstaff"/>
		<appliance name="Disney Channel" identifier="com.disney.channel.appletv"/>
		<appliance name="Smithsonian" identifier="com.smithsonian.appletv"/>
		<appliance name="YouTube" identifier="internet-youtube"/>
		<appliance name="NHL" identifier="NHL"/>
		<appliance name="Weather" identifier="com.weather.appletv"/>
		<appliance name="Disney XD" identifier="com.disney.xd.appletv"/>
		<appliance name="Photo Stream" identifier="photo-stream"/>
		<appliance name="ESPN" identifier="carterville"/>
	</applianceList>

You can then use the identifier specified above to jump directly to that app:

	http://apple-tv.local/plugin=com.apple.frontrow.appliance.movies

That will jump you directly to the iTunes Moves app. The built-in iTunes apps (and perhaps others) have static "categories" at the top. In movies, for instance, you have "Top Movies", "Genre", "Search", etc. You can jump directly to those categories by appending a slash then the category identifier. To get a list of category identifiers for any app, use the following command:

	http://apple-tv.local/appcat=com.apple.frontrow.appliance.movies

That returns another XML doc that has all the categories available:

	<categories>
		<category name="Wish List" identifier="wish-list"/>
		<category name="Top Movies" identifier="top-movies"/>
		<category name="Genres" identifier="genres"/>
		<category name="Search" identifier="search"/>
		<category name="Purchased" identifier="movie-purchases"/>
		<category name="Genius" identifier="F1A3D8D6-6FF5-44FA-B92B-E99EF2ADA4BE-311-00000018F769B5BD"/>
	</categories>

So, to jump directly to the Purchased category in the Movies app, you'd send the following command:

	http://apple-tv.local/plugin=com.apple.frontrow.appliance.movies/movie-purchases

That's all we've been able to glean so far. There might be more.

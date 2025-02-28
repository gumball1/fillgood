"""
    FanFilm Add-on

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from kover import autoinstall  # noqa: F401

import json
import re
import time
import threading
import sys
import xbmc

xbmc.log('Python Version: {}'.format(sys.version), 1)

"""
resolverEnabled = json.loads(xbmc.executeJSONRPC(
    f'{{"jsonrpc":"2.0", "id":1, "method":"Addons.GetAddonDetails", "params":{{"addonid":"{"script.module.resolveurl"}", "properties":["enabled"]}}}}'))[
        "result"]["addon"]["enabled"]
"""
ptwEnabled = json.loads(xbmc.executeJSONRPC(
    f'{{"jsonrpc":"2.0", "id":1, "method":"Addons.GetAddonDetails", "params":{{"addonid":"{"script.module.ptw"}", "properties":["enabled"]}}}}'))[
        "result"]["addon"]["enabled"]
#xbmc.log(f"{ptwEnabled=}", 1)

if ptwEnabled:
    from ptw.libraries import control
    from ptw.libraries import log_utils
    from ptw.libraries import cache

    import xbmcaddon
    control.setting = xbmcaddon.Addon().getSetting
    control.setSetting = xbmcaddon.Addon().setSetting


    if control.setting("autostart") == "true":
        log_utils.log("Automatic startup is ON", log_utils.LOGINFO, )
        control.infoDialog('Poczekaj na automatyczne uruchomienie', time=1, sound=False)
        control.execute("ActivateWindow(10025, plugin://plugin.video.fanfilm, return)")



    def cyclic_call(interval, func, *args, **kwargs):
        def calling():
            monitor = xbmc.Monitor()
            while True:
                monitor.waitForAbort(interval)  # sleeps for {interval} in secs or returns early if kodi aborts
                if monitor.abortRequested():  # abort was requested to Kodi (e.g. shutdown)
                    xbmc.log("[service.py] stopping cyclic_call, because abort was requested to Kodi")
                    return sys.exit()  # do cleanup logic
                func(*args, **kwargs)

        thread = threading.Thread(target=calling)
        thread.start()
        return thread


    def syncTraktLibrary():
        control.execute("RunPlugin(plugin://%s)" % "plugin.video.fanfilm/?action=tvshowsToLibrarySilent&url=traktcollection")
        control.execute("RunPlugin(plugin://%s)" % "plugin.video.fanfilm/?action=moviesToLibrarySilent&url=traktcollection")
        log_utils.log("### TRAKT LIBRARY UPDATE - NEXT ON  " + control.setting("schedTraktTime") + " HOURS ################", log_utils.LOGINFO, )


    def syncTMDBLibrary():
        control.execute("RunPlugin(plugin://%s)" % "plugin.video.fanfilm/?action=tvshowsToLibrarySilent&url=tmdbuserfavourite")
        control.execute("RunPlugin(plugin://%s)" % "plugin.video.fanfilm/?action=moviesToLibrarySilent&url=tmdbuserfavourite")
        log_utils.log("### TMDB LIBRARY UPDATE - NEXT ON  " + control.setting("schedTmdbTime") + " HOURS ################", log_utils.LOGINFO, )

            
    def syncIMdbLibrary():
        control.execute("RunPlugin(plugin://%s)" % "plugin.video.fanfilm/?action=tvshowsToLibrarySilent&url=imdbwatchlist")
        control.execute("RunPlugin(plugin://%s)" % "plugin.video.fanfilm/?action=moviesToLibrarySilent&url=imdbwatchlist")
        log_utils.log("### IMdb LIBRARY UPDATE - NEXT ON  " + control.setting("schedIMdbTime") + " HOURS ################", log_utils.LOGINFO, )


    def cacheCleanTimer():
        control.execute("RunPlugin(plugin://%s)" % "plugin.video.fanfilm/?action=clearCacheAllSilent")
        log_utils.log("### CACHE CLEAN - NEXT ON  " + control.setting("schedCleanCache") + " HOURS ################", log_utils.LOGINFO, )


    try:
        MediaVersion = control.addon("script.fanfilm.media").getAddonInfo("version")
        AddonVersion = control.addon("plugin.video.fanfilm").getAddonInfo("version")
        PTWVersion = control.addon("script.module.ptw").getAddonInfo("version")
        control.setSetting("addon.version", AddonVersion)
        control.setSetting("ptw.version", PTWVersion)
        log_utils.log("######################### FANFILM ############################", log_utils.LOGINFO, )
        log_utils.log("####### CURRENT FANFILM VERSIONS REPORT ######################", log_utils.LOGINFO, )
        log_utils.log("### FANFILM PLUGIN VERSION: %s ###" % str(AddonVersion), log_utils.LOGINFO)
        log_utils.log("### FANFILM MEDIA VERSION: %s ###" % str(MediaVersion), log_utils.LOGINFO)
        log_utils.log("### PTW VERSION: %s ###" % str(PTWVersion), log_utils.LOGINFO)
        log_utils.log("###############################################################", log_utils.LOGINFO, )
    except:
        log_utils.log("######################### FANFILM ############################", log_utils.LOGINFO, )
        log_utils.log("####### CURRENT FANFILM VERSIONS REPORT ######################", log_utils.LOGINFO, )
        log_utils.log("### ERROR GETTING FANFILM VERSIONS - NO HELP WILL BE GIVEN AS THIS IS NOT AN OFFICIAL FANFILM INSTALL. ###", log_utils.LOGINFO, )
        log_utils.log("###############################################################", log_utils.LOGINFO, )


    if control.setting("autoTraktOnStart") == "true":
        syncTraktLibrary()


    if int(control.setting("schedTraktTime")) > 0:
        log_utils.log("###############################################################", log_utils.LOGINFO, )
        log_utils.log("#################### STARTING TRAKT SCHEDULING ################", log_utils.LOGINFO, )
        log_utils.log("#################### SCHEDULED TIME FRAME " + control.setting("schedTraktTime") + " HOURS ################", log_utils.LOGINFO, )
        timeout = 3600 * int(control.setting("schedTraktTime"))
        cyclic_call(timeout, syncTraktLibrary)


    if control.setting("autoTmdbOnStart") == "true":
        syncTMDBLibrary()


    if int(control.setting("schedTmdbTime")) > 0:
        log_utils.log("###############################################################", log_utils.LOGINFO, )
        log_utils.log("#################### STARTING TMDB SCHEDULING ################", log_utils.LOGINFO, )
        log_utils.log("#################### SCHEDULED TIME FRAME " + control.setting("schedTmdbTime") + " HOURS ################", log_utils.LOGINFO, )
        timeout = 3600 * int(control.setting("schedTmdbTime"))
        cyclic_call(timeout, syncTMDBLibrary)


    if control.setting("autoIMdbOnStart") == "true":
        syncIMdbLibrary()


    if int(control.setting("schedIMdbTime")) > 0:
        log_utils.log("###############################################################", log_utils.LOGINFO, )
        log_utils.log("#################### STARTING IMdb SCHEDULING ################", log_utils.LOGINFO, )
        log_utils.log("#################### SCHEDULED TIME FRAME " + control.setting("schedIMdbTime") + " HOURS ################", log_utils.LOGINFO, )
        timeout = 3600 * int(control.setting("schedIMdbTime"))
        cyclic_call(timeout, syncIMdbLibrary)


    if control.setting("autoCleanCacheAll") == "true":
        cache.cache_clear_all()
        log_utils.log("######################### FANFILM ############################", log_utils.LOGINFO, )
        log_utils.log("######## Wyczyszczono pamięć podręczną #######################", log_utils.LOGINFO, )
        log_utils.log("###############################################################", log_utils.LOGINFO, )


    if int(control.setting("schedCleanCache")) > 0:
        log_utils.log("###############################################################", log_utils.LOGINFO, )
        log_utils.log("#################### STARTING CLEAN SCHEDULING ################", log_utils.LOGINFO, )
        log_utils.log("#################### SCHEDULED TIME FRAME " + control.setting("schedCleanCache") + " HOURS ################", log_utils.LOGINFO, )
        timeout = 3600 * int(control.setting("schedCleanCache"))
        cyclic_call(timeout, cacheCleanTimer)


    # clean downloaded database
    try:
        from ptw.libraries import downloader
        downloader.clear_db()
    except:
        pass


    # look in default.py what is going to run
    #control.execute("RunPlugin(plugin://%s)" % control.get_plugin_url({"action": "libepisodesservice"}))  # new thread

    # current thread - must be at the end of this script
    log_utils.log("start service (cyclic) for checking and updating library episodes", log_utils.LOGINFO)
    from ptw.libraries import libtools
    libtools.libepisodes().service()
    # don't put anything more here

else:
    # enable PTW module
    from checker import ResolveUrlChecker, PtwModuleChecker
    ResolveUrlChecker().setResolveUrl(enabled=True)
    PtwModuleChecker().setPtwModule(enabled=True)

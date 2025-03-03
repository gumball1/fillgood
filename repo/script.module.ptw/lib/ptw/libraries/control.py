# -*- coding: utf-8 -*-

"""
    Fanfilm Add-on

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

import os
import sys

try:
    import urllib.parse as urllib
except:
    pass

from kover import autoinstall  # noqa: F401
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

integer = 1000

lang = xbmcaddon.Addon().getLocalizedString

lang2 = xbmc.getLocalizedString

setting = xbmcaddon.Addon().getSetting

setSetting = xbmcaddon.Addon().setSetting

addon = xbmcaddon.Addon

addItem = xbmcplugin.addDirectoryItem

addItems = xbmcplugin.addDirectoryItems

item = xbmcgui.ListItem

directory = xbmcplugin.endOfDirectory

content = xbmcplugin.setContent

property = xbmcplugin.setProperty

sortMethod = xbmcplugin.addSortMethod

addonInfo = xbmcaddon.Addon().getAddonInfo

infoLabel = xbmc.getInfoLabel

condVisibility = xbmc.getCondVisibility

jsonrpc = xbmc.executeJSONRPC

window = xbmcgui.Window(10000)

dialog = xbmcgui.Dialog()

progressDialog = xbmcgui.DialogProgress()

progressDialogBG = xbmcgui.DialogProgressBG()

windowDialog = xbmcgui.WindowDialog()

button = xbmcgui.ControlButton

image = xbmcgui.ControlImage

getCurrentDialogId = xbmcgui.getCurrentWindowDialogId()
currentDialogId =    xbmcgui.getCurrentWindowDialogId

currentWindowId = xbmcgui.getCurrentWindowId()

keyboard = xbmc.Keyboard

log = xbmc.log

monitor = xbmc.Monitor()

# Modified `sleep` command that honors a user exit request  # ale jest przecież funkcja do tego o nazwie "waitForAbort()" - czas w sekundach
def sleep(time):
    monitor = xbmc.Monitor()
    monitor.waitForAbort(time/1000)
    """
    while time > 0 and not monitor.abortRequested():
        xbmc.sleep( min(50, time) )  # zawsze nie dłużej niż 50ms (może być krócej)
        time = time - 50
    """

sleep0 = xbmc.sleep  # msec

execute = xbmc.executebuiltin

skin = xbmc.getSkinDir()

player = xbmc.Player()

playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

resolve = xbmcplugin.setResolvedUrl

openFile = xbmcvfs.File

makeFile = xbmcvfs.mkdir

deleteFile = xbmcvfs.delete

deleteDir = xbmcvfs.rmdir

listDir = xbmcvfs.listdir

existsPath = xbmcvfs.exists

transPath = xbmcvfs.translatePath

skinPath = xbmcvfs.translatePath("special://skin/")

addonPath = xbmcvfs.translatePath(addonInfo("path"))

dataPath = xbmcvfs.translatePath(addonInfo("profile"))

settingsFile = os.path.join(dataPath, "settings.xml")

viewsFile = os.path.join(dataPath, "views.db")

bookmarksFile = os.path.join(dataPath, "bookmarks.db")

providercacheFile = os.path.join(dataPath, "providers.13.db")

episodesFile = os.path.join(dataPath, "episodes.json")

metacacheFile = os.path.join(dataPath, "meta.5.db")

sourcescacheFile = os.path.join(dataPath, "sources.db")

searchFile = os.path.join(dataPath, "search.1.db")

libcacheFile = os.path.join(dataPath, "library.db")

cacheFile = os.path.join(dataPath, "cache.db")

downloadsFile = os.path.join(dataPath, "downloads.db")

key = "RgUkXp2s5v8x/A?D(G+KbPeShVmYq3t6"

iv = "p2s5v8y/B?E(H+Mb"


def autoTraktSubscription(tvshowtitle, year, imdb, tmdb):
    from . import libtools

    libtools.libtvshows().add(tvshowtitle, year, imdb, tmdb)


def addonIcon():
    theme = appearance()
    art = artPath()
    if not (art is None and theme in ["-", ""]):
        return os.path.join(art, "icon.png")
    return addonInfo("icon")


def addonThumb():
    theme = appearance()
    art = artPath()
    if not (art is None and theme in ["-", ""]):
        return os.path.join(art, "poster.png")
    elif theme == "-":
        return "poster.png"
    return addonInfo("icon")


def addonPoster():
    theme = appearance()
    art = artPath()
    if not (art is None and theme in ["-", ""]):
        return os.path.join(art, "poster.png")
    return "poster.png"


def addonBanner():
    theme = appearance()
    art = artPath()
    if not (art is None and theme in ["-", ""]):
        return os.path.join(art, "banner.png")
    return "banner.png"


def addonFanart():
    theme = appearance()
    art = artPath()
    if not (art is None and theme in ["-", ""]):
        return os.path.join(art, "fanart.jpg")
    return addonInfo("fanart.jpg")


def addonLandscape():
    theme = appearance()
    art = artPath()
    if art is None and theme in ["-", ""]:
        path = "landscape.jpg"
    else:
        path = os.path.join(art, "landscape.jpg")
    return path if os.path.exists(path) else addonFanart()


def addonNext():
    theme = appearance()
    art = artPath()
    if not (art is None and theme in ["-", ""]):
        return os.path.join(art, "next.png")
    return "next.png"


def addonId():
    return addonInfo("id")


def addonName():
    return addonInfo("name")


def get_plugin_url(queries):
    try:
        query = urllib.urlencode(queries)
    except UnicodeEncodeError:
        for k in queries:
            if isinstance(queries[k], str):
                queries[k] = queries[k].encode("utf-8")
        query = urllib.urlencode(queries)
    addon_id = sys.argv[0]
    if not addon_id:
        addon_id = addonId()
    return addon_id + "?" + query


def artPath():
    theme = appearance()
    if theme in ["-", ""]:
        return
    elif condVisibility("System.HasAddon(script.fanfilm.media)"):
        path_old = os.path.join(
            xbmcaddon.Addon("script.fanfilm.media").getAddonInfo("path"),
            "resources",
            "media",
            theme,
        )
        path_new = os.path.join(
            xbmcaddon.Addon("script.fanfilm.media").getAddonInfo("path"),
            "resources",
            "media",
            #theme,  # już nie ma "Incursion"
        )
        return path_old if os.path.exists(path_old) else path_new


def appearance():
    appearance = (
        setting("appearance.1").lower()  # "Incursion"
        if condVisibility("System.HasAddon(script.fanfilm.media)")
        else setting("appearance.alt").lower()
    )
    return appearance


def artwork():
    execute("RunPlugin(plugin://script.fanfilm.media)")


def infoDialog(message, heading=addonInfo("name"), icon="", time=3000, sound=False):
    if icon == "":
        icon = addonIcon()
    elif icon == "INFO":
        icon = xbmcgui.NOTIFICATION_INFO
    elif icon == "WARNING":
        icon = xbmcgui.NOTIFICATION_WARNING
    elif icon == "ERROR":
        icon = xbmcgui.NOTIFICATION_ERROR
    dialog.notification(heading, message, icon, time, sound=sound)


def yesnoDialog(
    line1="", line2="", line3="", heading=addonInfo("name"), nolabel="", yeslabel=""
):
    return dialog.yesno(heading, line1 + "\n" + line2 + "\n" + line3, nolabel, yeslabel)


def selectDialog(list, heading=addonInfo("name")):
    return dialog.select(heading, list)


def metaFile():
    if condVisibility("System.HasAddon(script.fanfilm.metadata)"):
        return os.path.join(
            xbmcaddon.Addon("script.fanfilm.metadata").getAddonInfo("path"),
            "resources",
            "data",
            "meta.db",
        )


def apiLanguage(ret_name=None):
    langDict = {
        "Bulgarian": "bg",
        "Chinese": "zh",
        "Croatian": "hr",
        "Czech": "cs",
        "Danish": "da",
        "Dutch": "nl",
        "English": "en",
        "Finnish": "fi",
        "French": "fr",
        "German": "de",
        "Greek": "el",
        "Hebrew": "he",
        "Hungarian": "hu",
        "Italian": "it",
        "Japanese": "ja",
        "Korean": "ko",
        "Norwegian": "no",
        "Polish": "pl",
        "Portuguese": "pt",
        "Romanian": "ro",
        "Russian": "ru",
        "Serbian": "sr",
        "Slovak": "sk",
        "Slovenian": "sl",
        "Spanish": "es",
        "Swedish": "sv",
        "Thai": "th",
        "Turkish": "tr",
        "Ukrainian": "uk",
    }

    trakt = [
        "bg",
        "cs",
        "da",
        "de",
        "el",
        "en",
        "es",
        "fi",
        "fr",
        "he",
        "hr",
        "hu",
        "it",
        "ja",
        "ko",
        "nl",
        "no",
        "pl",
        "pt",
        "ro",
        "ru",
        "sk",
        "sl",
        "sr",
        "sv",
        "th",
        "tr",
        "uk",
        "zh",
    ]
    tvdb = [
        "en",
        "sv",
        "no",
        "da",
        "fi",
        "nl",
        "de",
        "it",
        "es",
        "fr",
        "pl",
        "hu",
        "el",
        "tr",
        "ru",
        "he",
        "ja",
        "pt",
        "zh",
        "cs",
        "sl",
        "hr",
        "ko",
    ]
    youtube = [
        "gv",
        "gu",
        "gd",
        "ga",
        "gn",
        "gl",
        "ty",
        "tw",
        "tt",
        "tr",
        "ts",
        "tn",
        "to",
        "tl",
        "tk",
        "th",
        "ti",
        "tg",
        "te",
        "ta",
        "de",
        "da",
        "dz",
        "dv",
        "qu",
        "zh",
        "za",
        "zu",
        "wa",
        "wo",
        "jv",
        "ja",
        "ch",
        "co",
        "ca",
        "ce",
        "cy",
        "cs",
        "cr",
        "cv",
        "cu",
        "ps",
        "pt",
        "pa",
        "pi",
        "pl",
        "mg",
        "ml",
        "mn",
        "mi",
        "mh",
        "mk",
        "mt",
        "ms",
        "mr",
        "my",
        "ve",
        "vi",
        "is",
        "iu",
        "it",
        "vo",
        "ii",
        "ik",
        "io",
        "ia",
        "ie",
        "id",
        "ig",
        "fr",
        "fy",
        "fa",
        "ff",
        "fi",
        "fj",
        "fo",
        "ss",
        "sr",
        "sq",
        "sw",
        "sv",
        "su",
        "st",
        "sk",
        "si",
        "so",
        "sn",
        "sm",
        "sl",
        "sc",
        "sa",
        "sg",
        "se",
        "sd",
        "lg",
        "lb",
        "la",
        "ln",
        "lo",
        "li",
        "lv",
        "lt",
        "lu",
        "yi",
        "yo",
        "el",
        "eo",
        "en",
        "ee",
        "eu",
        "et",
        "es",
        "ru",
        "rw",
        "rm",
        "rn",
        "ro",
        "be",
        "bg",
        "ba",
        "bm",
        "bn",
        "bo",
        "bh",
        "bi",
        "br",
        "bs",
        "om",
        "oj",
        "oc",
        "os",
        "or",
        "xh",
        "hz",
        "hy",
        "hr",
        "ht",
        "hu",
        "hi",
        "ho",
        "ha",
        "he",
        "uz",
        "ur",
        "uk",
        "ug",
        "aa",
        "ab",
        "ae",
        "af",
        "ak",
        "am",
        "an",
        "as",
        "ar",
        "av",
        "ay",
        "az",
        "nl",
        "nn",
        "no",
        "na",
        "nb",
        "nd",
        "ne",
        "ng",
        "ny",
        "nr",
        "nv",
        "ka",
        "kg",
        "kk",
        "kj",
        "ki",
        "ko",
        "kn",
        "km",
        "kl",
        "ks",
        "kr",
        "kw",
        "kv",
        "ku",
        "ky",
    ]
    tmdb = [
        "ar",
        "be",
        "bg",
        "bn",
        "ca",
        "ch",
        "cs",
        "da",
        "de",
        "el",
        "en",
        "eo",
        "es",
        "et",
        "eu",
        "fa",
        "fi",
        "fr",
        "gl",
        "he",
        "hi",
        "hu",
        "id",
        "it",
        "ja",
        "ka",
        "kk",
        "kn",
        "ko",
        "lt",
        "lv",
        "ml",
        "ms",
        "nb",
        "nl",
        "no",
        "pl",
        "pt",
        "ro",
        "ru",
        "si",
        "sk",
        "sl",
        "sr",
        "sv",
        "ta",
        "te",
        "th",
        "tl",
        "tr",
        "uk",
        "vi",
        "zh",
        "zu-ZA",
    ]

    name = None
    name = setting("api.language")
    if not name:
        name = "AUTO"

    if name[-1].isupper():
        try:
            name = xbmc.getLanguage(xbmc.ENGLISH_NAME).split(" ")[0]
        except:
            pass
    try:
        name = langDict[name]
    except KeyError:
        name = "en"
    lang = {"trakt": name} if name in trakt else {"trakt": "en"}
    lang["tvdb"] = name if name in tvdb else "en"
    lang["youtube"] = name if name in youtube else "en"
    lang["tmdb"] = name if name in tmdb else "en"

    if ret_name:
        lang["trakt"] = [i[0] for i in langDict.items() if i[1] == lang["trakt"]][0]
        lang["tvdb"] = [i[0] for i in langDict.items() if i[1] == lang["tvdb"]][0]
        lang["youtube"] = [i[0] for i in langDict.items() if i[1] == lang["youtube"]][0]
        lang["tmdb"] = [i[0] for i in langDict.items() if i[1] == lang["tmdb"]][0]
    return lang


def version():
    num = ""
    try:
        version = addon("xbmc.addon").getAddonInfo("version")
    except:
        version = "999"
    for i in version:
        if i.isdigit():
            num += i
        else:
            break
    return int(num)


def cdnImport(uri, name):
    import imp
    from ptw.libraries import client

    path = os.path.join(dataPath, "py" + name)
    path = path.decode("utf-8")

    deleteDir(os.path.join(path, ""), force=True)
    makeFile(dataPath)
    makeFile(path)

    r = client.request(uri)
    p = os.path.join(path, name + ".py")
    f = openFile(p, "w")
    f.write(r)
    f.close()
    m = imp.load_source(name, p)

    deleteDir(os.path.join(path, ""), force=True)
    return m


def openSettings(query=None, id=addonInfo("id")):
    try:
        idle()
        execute("Addon.OpenSettings(%s)" % id)
        if query is None:
            raise Exception()
        c, f = query.split(".")
        execute("SetFocus(%i)" % (int(c) + 100))
        execute("SetFocus(%i)" % (int(f) + 200))
    except:
        return


def getCurrentViewId():
    win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    return str(win.getFocusId())


def refresh():
    return execute("Container.Refresh")


def update(url, replace=None):
    if replace:
        return execute("Container.Update(%s, 'replace')" % url)
    else:
        return execute("Container.Update(%s)" % url)


def busy():
    Kodi = xbmc.getInfoLabel("System.BuildVersion")[:2]
    try:
        Kodi = int(Kodi)
        if Kodi > 17:
            if not condVisibility("Window.IsActive(busydialognocancel)") and not condVisibility("Window.IsActive(busydialog)"):
                execute("ActivateWindow(busydialognocancel)")  # Kodi 18
        else:
            if not condVisibility("Window.IsActive(busydialog)"):
                execute("ActivateWindow(busydialog)")  # Kodi 17
    except Exception:
        pass


def idle(mode=0):
    if mode != 2 and condVisibility("Window.IsActive(busydialog)"):
        execute("Dialog.Close(busydialog)")  # Kodi 17
    if mode != 1 and condVisibility("Window.IsActive(busydialognocancel)"):
        execute("Dialog.Close(busydialognocancel)")  # Kodi 18


def queueItem():
    return execute("Action(Queue)")


def metadataClean(
    metadata,
):  # Filter out non-existing/custom keys. Otherise there are tons of errors in Kodi 18 log.
    if metadata is None:
        return metadata
    allowed = [
        "genre",
        "country",
        "year",
        "episode",
        "season",
        "sortepisode",
        "sortseason",
        "episodeguide",
        "showlink",
        "top250",
        "setid",
        "tracknumber",
        "rating",
        "userrating",
        "watched",
        "playcount",
        "overlay",
        "cast",
        "castandrole",
        "director",
        "mpaa",
        "plot",
        "plotoutline",
        "title",
        "originaltitle",
        "sorttitle",
        "duration",
        "studio",
        "tagline",
        "writer",
        "tvshowtitle",
        "premiered",
        "status",
        "set",
        "setoverview",
        "tag",
        "imdbnumber",
        "code",
        "aired",
        "credits",
        "lastplayed",
        "album",
        "artist",
        "votes",
        "path",
        "trailer",
        "dateadded",
        "mediatype",
        "dbid",
    ]
    return {k: v for k, v in metadata.items() if k in allowed}


class settings:
    def getInt(id):
        try:
            n = int(setting(id))
        except:
            n = 0
        return n
    
    def getBool(id):
        return True if setting(id) == "true" else False

    def getString(id):
        return str(setting(id))

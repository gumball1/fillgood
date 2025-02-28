"""
    FanFilm Add-on
    Copyright (C) 2024 - original author MrKnow

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
from ptw.libraries import control

import xbmcaddon
control.setting = xbmcaddon.Addon().getSetting
control.setSetting = xbmcaddon.Addon().setSetting

if control.setting("additional_working_info") == "true" or (control.infoLabel('Container.FolderPath')).startswith("plugin://plugin.video.themoviedb.helper/"):
    if not control.condVisibility('Window.IsActive(notification)'):
        control.infoDialog('', time=1, sound=False)
        control.sleep(100)
        pass  # aby móc łatwo zakomentować powyższą linijkę

import sys
from kover import autoinstall  # noqa: F401
from contextlib import contextmanager
from urllib.parse import parse_qsl


#control.setSetting('appearance.1', 'Incursion')  # już niepotrzebne


FFlastpath = control.window.getProperty('FanFilm.var.lastpath')  # z pamięci
FFlastpath = eval(FFlastpath) if FFlastpath else {}  # tylko jak Kodi wczytuje folder z cachu, to ta zmienna się nie zmienia (bo plugin nie jest wywoływany)

folderpath  = control.infoLabel('Container.FolderPath')
KFolderPath = dict(parse_qsl(folderpath.split('?')[-1]))  # taki niby referer, ale nie działa prawidłowo, jak odpalamy z widgetu

currentPath = dict(parse_qsl(sys.argv[2][1:]))
#control.log(f"{currentPath=}", 1)

referer = KFolderPath if KFolderPath != currentPath else ''
# control.log(f'{referer=} ', 1)


generate_short_path = control.setting("generate_short_path") == "true"


# for debug
if False and currentPath.get("action") not in ["service", "libepisodesservice"]:

    control.log(f"\n\n________________________________________________________________ ", 1)

    control.log(f"{control.infoLabel('Container.PluginName')=}", 1)  # może się przydać (użyte w sources.py do detekcji czy ma być katalog czy okienko) (chyba puste, gdy odpalamy pozycje z biblioteki)
    control.log(f" ", 1)

    control.log(f" {FFlastpath=}", 1)
    control.log(f"{KFolderPath=}  ({folderpath.split('?')[0]})", 1)
    control.log(f"{currentPath=}", 1)
    control.log(f'    {referer=} ', 1)
    control.log(f" ", 1)

    # https://alwinesch.github.io/modules__infolabels_boolean_conditions.html
    control.log(f"{control.infoLabel('Container.FolderPath')=}", 1)
    control.log(f" {control.infoLabel('ListItem.FolderPath')=}", 1)
    control.log(f" {control.infoLabel('ListItem.Path')=}", 1)
    control.log(f'{control.infoLabel("ListItem.FileNameAndPath")=}', 1)
    control.log(f'{control.infoLabel("ListItem.FileName")=}', 1)
    control.log(f" ", 1)

    control.log(f'{control.infoLabel("Container.NumPages")=}', 1)
    control.log(f'{control.infoLabel("Container.CurrentPage")=}', 1)
    control.log(f'{control.infoLabel("Container.NumItems")=}', 1)
    control.log(f'{control.infoLabel("Container.NumAllItems")=}', 1)
    control.log(f" ", 1)
    control.log(f'{control.infoLabel("Container.CurrentItem")=}', 1)
    control.log(f'{control.infoLabel("ListItem.CurrentItem")=}', 1)
    control.log(f'{control.infoLabel("ListItem.FileNameAndPath")=}', 1)
    control.log(f"{control.infoLabel('ListItem.Label')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Label2')=}", 1)

    control.log(f" ", 1)
    control.log(f"{control.infoLabel('ListItem.Title')=}", 1)
    control.log(f"{control.infoLabel('ListItem.OriginalTitle')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(englishTitle)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.TvShowTitle')=}", 1)
    control.log(f"{control.infoLabel('Container.showtitle')=}", 1)  # nie wiem kiedy to ma działać
    control.log(f"{control.infoLabel('ListItem.Property(englishTvShowTitle)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(OriginalTvShowTitle)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.UniqueID(imdb)')=}", 1)  # od Kodi 19 ?
    control.log(f"{control.infoLabel('ListItem.UniqueID(tmdb)')=}", 1)  # od Kodi 19 ?
    control.log(f"{control.infoLabel('ListItem.UniqueID(tvdb)')=}", 1)  # od Kodi 19 ?
    control.log(f"{control.infoLabel('ListItem.Property(imdb_id)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(tmdb_id)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(tvdb_id)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(meta)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Season')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Episode')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Premiered')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Year')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(TvShowYear)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Country')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Plot')=}", 1)
    control.log(f"{control.infoLabel('ListItem.MPAA')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Duration')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Overlay')=}", 1)
    control.log(f"{control.infoLabel('ListItem.PlayCount')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(TotalSeasons)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(TotalEpisodes)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(fullpath)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(url)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Property(IsPlayable)')=}", 1)
    #control.log(f"{control.infoLabel('ListItem.IsFolder')=}", 1)  # źle, bo to jest typu bool
    control.log(f"{control.condVisibility('ListItem.IsFolder')=}", 1)  # to jest poprawne
    #control.log(f"{control.infoLabel('ListItem.Thumb')=}", 1)  #  Deprecated but still available, returns the same as ListItem.Art(thumb).
    #control.log(f"{control.infoLabel('ListItem.Icon')=}", 1)
    # control.log(f"{control.infoLabel('ListItem.ActualIcon')=}", 1)
    control.log(f"{control.infoLabel('ListItem.DBID')=}", 1)
    control.log(f"{control.infoLabel('ListItem.DBTYPE')=}", 1)
    
    control.log(f"{control.infoLabel('ListItem.Thumb')=}", 1)  # Deprecated but still available, returns the same as ListItem.Art(thumb).
    control.log(f"{control.infoLabel('ListItem.Art(thumb)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(poster)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(season.poster)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(tvshow.poster)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(banner)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(clearlogo)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(clearart)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(fanart)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(landscape)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(keyart)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(discart)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(characterart)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(dupa)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Icon')=}", 1)
    control.log(f"{control.infoLabel('ListItem.ActualIcon')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(season.banner)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(season.landscape)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(tvshow.banner)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(tvshow.clearlogo)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(tvshow.fanart)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(season.fanart)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(season.clearlogo)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(season.clearart)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(season.keyart)')=}", 1)
    control.log(f"{control.infoLabel('ListItem.Art(season.icon)')=}", 1)
    control.log(f" ", 1)

    # to coś nie działa, albo dziwnie działa
    #control.log(f"{control.window.getProperty('LatestMovie.1.Title')=}", 1)
    #control.log(f"{control.infoLabel('Window(Home).Property(LatestMovie.1.Title)')=}", 1)
    #control.log(f" ", 1)

    control.log(f"{control.infoLabel('Container.Content')=}", 1)

    control.log(f"{control.infoLabel('Window.Property(xmlfile)')=}", 1)

    control.log(f"{control.infoLabel('System.CurrentWindow')=}", 1)
    control.log(f"{control.infoLabel('System.CurrentControl')=}", 1)
    control.log(f"{control.infoLabel('System.CurrentControlID')=}", 1)

    # import xbmcgui
    # win_id = xbmcgui.getCurrentWindowId()
    win_id = control.currentWindowId
    control.log(f"{win_id=}", 1)

    # focus_panel_id = control.getCurrentViewId()
    # control.log(f"{focus_panel_id=}", 1)

    #control.log(f"{control.condVisibility('Window.IsVisible(DialogVideoInfo.xml)')=}", 1)
    #control.log(f"{control.condVisibility('Window.IsVisible(DialogBusy.xml)')=}", 1)

    control.log(f" ", 1)


params = dict(parse_qsl(sys.argv[2].replace("?", "")))

control.log(f'\n[FanFilm][default.py] początek {params=}', 0)

action = params.get("action")

name = params.get("name")
title = params.get("title")
localtitle = params.get("localtitle") or params.get("title")
year = params.get("year")
imdb = params.get("imdb")
tmdb = params.get("tmdb")
tvdb = params.get("tvdb")
tvshowtitle = params.get("tvshowtitle")
season = params.get("season")
episode = params.get("episode")
url = params.get("url")


if not action:
    control.log("[FanFilm] start default action", 1)

    resolverCheck = control.setting("resolverCheck")
    ptwCheck = control.setting("ptwCheck")

    if ptwCheck == "true":
        control.log("[FanFilm] checking PTW version", 1)
        from checker import PtwModuleChecker
        PtwModuleChecker().checkVersion()

    if resolverCheck == "true":
        control.log("[FanFilm] checking ResolveUrl version", 1)
        from checker import ResolveUrlChecker
        ResolveUrlChecker().checkVersion()

    control.log("[FanFilm] preparing Menu", 1)
    from resources.lib.indexers import navigator
    navigator.navigator().root()
    control.log("[FanFilm] Menu is ready", 1)

    control.window.clearProperty('FanFilm.var.curr_item_p')  # tylko, że to nie zawsze się wykona


elif action == "play":
    premiered = params.get("premiered")
    meta = params.get("meta")
    select = params.get("select")
    originalname = params.get("originalname", "")
    epimdb = params.get("epimdb", "")
    customTitles = params.get("customTitles")
    #mediatype = params.get("mediatype", "")  # może potem będzie zbędne (może season i episode wystarczy)


    if not params.get("title"):
        title = control.infoLabel('ListItem.Property(englishTitle)')
        title = control.infoLabel('ListItem.OriginalTitle') if not title else title

    if not params.get("localtitle"):
        localtitle = control.infoLabel('ListItem.Title')

    if not params.get("tvshowtitle"):
        tvshowtitle = control.infoLabel('ListItem.Property(englishTvShowTitle)')
        tvshowtitle = control.infoLabel('ListItem.TvShowTitle') if not tvshowtitle else tvshowtitle
        tvshowtitle = tvshowtitle if tvshowtitle else None

    if not params.get("year"):
        year = control.infoLabel('ListItem.Property(TvShowYear)')
        year = control.infoLabel('ListItem.Year') if not year else year

    if not params.get("imdb"):
        imdb = control.infoLabel('ListItem.Property(imdb_id)')  # starsze Kodi ( < 20)
        imdb = control.infoLabel('ListItem.UniqueID(imdb)') if not imdb else imdb
        imdb = imdb if imdb else None

    if not params.get("tmdb"):
        tmdb = control.infoLabel('ListItem.Property(tmdb_id)')  # starsze Kodi ( < 20)
        tmdb = control.infoLabel('ListItem.UniqueID(tmdb)') if not tmdb else tmdb
        tmdb = tmdb if tmdb else None

    if not params.get("tvdb"):
        tvdb = control.infoLabel('ListItem.Property(tvdb_id)')  # starsze Kodi ( < 20)
        tvdb = control.infoLabel('ListItem.UniqueID(tvdb)') if not tvdb else tvdb
        tvdb = tvdb if tvdb else None

    if not params.get("meta"):
        meta = control.infoLabel('ListItem.Property(meta)')
        meta = meta if meta else None

    if not params.get("season"):
        season = control.infoLabel('ListItem.Season')
        season = season if season else None

    if not params.get("episode"):
        episode = control.infoLabel('ListItem.Episode')
        episode = episode if episode else None

    if not params.get("premiered"):
        premiered = control.infoLabel('ListItem.Premiered')

    # wykrycie, czy wywołanie jest z zewnątrz
    # obcy = not control.infoLabel("ListItem.CurrentItem")  # nie sprawdził się przy refresh
    obcy = control.infoLabel("Container.NumPages")  # moze też być CurrentPage, NumItems, NumAllItems
    # startowa = True if obcy == "" else False  # może 'Container.PluginName' by wystarczył - trzeba potestować
    obcy = not int(obcy) if obcy else False
    # control.log(f'{obcy=}', 1)
    # nie sprawdza się do końca
    # próba korekty tej zmiennej
    if FFlastpath.get("action") == "playItem":  # nie wiem, czy nie trzeba też dołożyć "showItems"
        obcy = False
        # control.log(f'{obcy=}', 1)
    # ale powyjściu z wygaszacza pokazuje, że obcy, a akcja to play
    # control.log(f'{tmdb=}', 1)
    if (
        params.get("r")
        or not obcy and tmdb is None
        or tmdb is None and KFolderPath == currentPath
        or tmdb is None and FFlastpath == currentPath  # to może pomóc
        ):
        # control.log(f'z pamieci', 1)
        zmienne = control.window.getProperty('FanFilm.var.curr_item_p')  # z pamięci
        # control.log(f'{zmienne=}', 1)
        if zmienne:
            zmienne = eval(zmienne)
            globals().update(zmienne)  # opcjonalnie
    else:
        # control.log(f'do pamieci', 1)
        #zmienne = (title, localtitle, year, imdb, tvdb, tmdb, season, episode, tvshowtitle, premiered, meta, select, customTitles, originalname, epimdb)
        zmienne = {"title":title, "localtitle":localtitle, "year":year, "imdb":imdb, "tvdb":tvdb, "tmdb":tmdb,
                   "season":season, "episode":episode, "tvshowtitle":tvshowtitle, "premiered":premiered,
                   "meta":meta, "select":select, "originalname":originalname, "epimdb":epimdb}
        control.window.setProperty('FanFilm.var.curr_item_p', repr(zmienne))  # do pamięci

    # control.log(f' [ KONTROLA ] \n{title=} \n{localtitle=} \n{year=} \n{imdb=} \n{tvdb=} \n{tmdb=} \n{season=} \n{episode=} \n{tvshowtitle=} \n{premiered=} \n{meta=} \n{select=} \n{customTitles=} \n{originalname=}  \n{epimdb=}', 1)
    #control.log(f" {control.window.getProperty('imdb_id')=}", 1)

    folderpath = control.infoLabel('Container.FolderPath')
    select = control.setting("hosts.mode") if select is None else select
    # control.log(f"{select=}", 1)
    # if select == "1" and folderpath.startswith("plugin://plugin.video.themoviedb.helper/"):  # może dałoby się zrobić bardziej uniwersalnie ?
    #if select == "1" and not control.infoLabel("Container.PluginName"):  # próba uniwersalności
    if select == "1" and "plugin.video.fanfilm" not in control.infoLabel("Container.PluginName"):  # próba uniwersalności
        select = "0"
    #elif select == "0" and int(sys.argv[1]) > 0 and not folderpath.startswith("plugin://plugin.video.themoviedb.helper/"):
    #elif select == "0" and int(sys.argv[1]) > 0 and control.infoLabel("Container.PluginName") and not control.infoLabel("ListItem.FolderPath"):
    elif (select == "0" or select == "2") and int(sys.argv[1]) >= 0 and control.infoLabel("Container.PluginName") and not control.infoLabel("ListItem.FolderPath"):
        select = "1"  # pomaga wyświetlać katalogi, gdy user ustawił okienko  # tu nie, aby nie robić przekierowania (szkoda), bo warunki się zmieniają (te 2 na końcu), ale sources.py już to ustawia
        pass
        control.log(f'{control.infoLabel("Container.PluginName")=}', 0)
        control.log(f'{control.infoLabel("ListItem.FolderPath")=}', 0)
    # control.log(f"{select=}", 1)

    # if control.setting("generate_short_path") == "true" and (params.get("title") or params.get("tvshowtitle")) and select == "1" and not params.get("r"):
    if control.setting("generate_short_path") == "true" and (params.get("title") or params.get("tvshowtitle")) and select == "1" and not params.get("r") and control.infoLabel("Container.PluginName"):
        if KFolderPath.get("r"):
            control.log("aby nie powstała nieskończona pętla", 1)
            control.directory(int(sys.argv[1]), cacheToDisc=False)  # obowiązkowo
            control.log("akcja wstecz", 1)
            control.execute('Action(Back)')
            action = "nothing"
        else:
            control.window.setProperty('FanFilm.var.before_r', repr(params))  # do pamięci
            """
            import json
            try:
                meta = json.loads(meta)
            except:
                meta = {}
            for k,v in params.items():
                if k not in ["meta", "action"]:
                #if k not in zmienne:
                    meta.update({k: v})

            # są potrzebne korekty pod FF
            if (val := meta.get("localtitle")):
                meta.update({"title": val}); meta.pop('localtitle')
            if (val := meta.get("localtvshowtitle")):
                meta.update({"tvshowtitle": val}); meta.pop('localtvshowtitle')
            # jeszce potrzeba korekt na thumb i poster

            meta = json.dumps(meta)
            zmienne.update({"meta": meta})
            control.window.setProperty('FanFilm.var.curr_item_p', repr(zmienne))  # do pamięci jeszcze raz
            """
            #sign = "-" if not control.infoLabel("ListItem.FolderPath") else ""  # to nic nie dało
            # control.addItem(int(sys.argv[1]), sys.argv[0]+"?action=play&r=1", control.item(" proszę czekać ..."), True)  # opcjonalnie
            control.addItem(int(sys.argv[1]), sys.argv[0]+"?action=nothing", control.item(" proszę czekać ..."), False)  # opcjonalnie
            control.directory(int(sys.argv[1]), cacheToDisc=False)  # obowiązkowo i musi być False, bo przy True nie chce robić przekierowania, gdy wyświetla stronę z cachu
            control.log("przekierowanie (odświeżenie) z obcięciem parametrów", 0)  # tu dodatkowe polecenie jako zwłoka przed następnym
            control.sleep0(100)
            control.execute('Container.Update(' + sys.argv[0]+f"?action={action}&r=1" + ')')
            action = "nothing"
    else:
        if select == "0":
            control.busy()
            control.sleep(500)

        from ptw.libraries import sources
        if customTitles:
            if zmienne:
                zmienne.update({"customTitles": customTitles})
            sources.sources().alterSources(zmienne)
        else:
            #sources.sources().play(title, localtitle, year, imdb, tvdb, tmdb, season, episode, tvshowtitle, premiered, meta, select, originalname=originalname, epimdb=epimdb)
            if zmienne:
                #sources.sources().play(*zmienne)
                sources.sources().play(**zmienne)

        if select == "0":
            control.idle(2)
            pass


elif action == "showItems":
    if not (title := params.get("title")):    
        # title = control.infoLabel('ListItem.OriginalTitle')
        title = control.infoLabel('ListItem.Property(title)')
        if title:
            # control.log(f'do pamieci', 1)
            control.window.setProperty('FanFilm.var.title', title)  # do pamięci
        else:
            # control.log(f'z pamieci', 1)
            title = control.window.getProperty('FanFilm.var.title')  # z pamięci
    #control.log(f"{title=}", 1)
    from ptw.libraries import sources
    sources.sources().showItems(title, params.get("items"), params.get("trash"), season, episode)


elif action == "playItem":
    title = params.get("title") or control.infoLabel('ListItem.Title') or None
    source = params.get("source") or control.infoLabel('ListItem.Property(source)') or None
    meta = params.get("meta") or control.infoLabel('ListItem.Property(meta)') or None

    from ptw.libraries import sources
    sources.sources().playItem(title, source, meta, imdb, tmdb, season, episode)


elif action == "movieNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().movies()


elif action == "movieliteNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().movies(lite=True)


elif action == "mymovieNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().mymovies()


elif action == "mymovieliteNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().mymovies(lite=True)


elif action == "tvNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().tvshows()


elif action == "tvliteNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().tvshows(lite=True)


elif action == "mytvNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().mytvshows()


elif action == "downloadNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().downloads()


elif action == "libraryNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().library()


elif action == "toolNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().tools()


elif action == "searchNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().search()


elif action == "viewsNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().views()


elif action == "cacheNavigator":
    from resources.lib.indexers import navigator
    navigator.navigator().cache()


elif action == "clearCache":
    from resources.lib.indexers import navigator
    navigator.navigator().clearCache()


elif action == "clearCacheMeta":
    from resources.lib.indexers import navigator
    navigator.navigator().clearCacheMeta()


elif action == "clearCacheProviders":
    from resources.lib.indexers import navigator
    navigator.navigator().clearCacheProviders()


elif action == "clearCacheSearch":
    from resources.lib.indexers import navigator
    if navigator.navigator().clearCacheSearch(params.get("content")) is not False:
        control.refresh()


elif action == "removeFromSearchHistory":
    from resources.lib.indexers import navigator
    if navigator.navigator().removeFromSearchHistory(params.get("term"), params.get("content")) is not False:
        control.refresh()

        
elif action == "clearCacheAll":
    from resources.lib.indexers import navigator
    navigator.navigator().clearCacheAll()


elif action == "clearCacheAllSilent":
    from resources.lib.indexers import navigator
    navigator.navigator().clearCacheAllSilent()


elif action == "infoCheck":
    from resources.lib.indexers import navigator
    navigator.navigator().infoCheck("")


elif action == "downloadManager":
    from ptw.libraries import downloader
    downloader.downloadManager()
    # after close modal window
    if not control.monitor.abortRequested():
        control.sleep(500)  # because of animation
        handle = int(sys.argv[1])
        if handle > -1:
            control.directory(handle, cacheToDisc=False)
            control.log(f"akcja wstecz (po {action})", 0)
            control.execute('Action(Back)')
            action = "nothing"

elif action == "movies" or action == "moviePage":
    if not url:
        url = control.infoLabel('ListItem.Property(url)')

        if url:
            # control.log(f'do pamieci', 1)
            control.window.setProperty('FanFilm.var.url', url)  # do pamięci
        else:
            # control.log(f'z pamieci', 1)
            url = control.window.getProperty('FanFilm.var.url')  # z pamięci

        page = params.get("page")
        if page and "page" not in url:
            q_or_a = "&" if "?" in url else "?"
            url += f"{q_or_a}page={page}"
    # control.log(f'{action=} {url=}', 1)
    refresh = params.get("refresh")
    from resources.lib.indexers import movies
    movies.movies().get(url, refresh=refresh)


elif action == "movieWidget":
    from resources.lib.indexers import movies
    movies.movies().widget()


elif action == "movieSearch":
    control.window.clearProperty('FanFilm.var.name')  # wyczyszcenie
    from resources.lib.indexers import movies
    movies.movies().search()


elif action == "movieSearchnew":
    from resources.lib.indexers import movies
    movies.movies().search_new()


elif action == "movieSearchterm":
    if not params.get("name"):
        folderpath = control.infoLabel('Container.FolderPath') 
        referer = dict(parse_qsl(folderpath.split('?')[-1]))
        if referer.get("action") == "movieSearch":
            name = control.infoLabel('ListItem().Label')  # z wybranej pozycji
            control.window.setProperty('FanFilm.var.name', name)  # do pamięci
            # control.log(f'do pamieci', 1)
        else:
            name = control.window.getProperty('FanFilm.var.name')  # z pamięci
            # control.log(f'z pamieci', 1)
    from resources.lib.indexers import movies
    movies.movies().search_term(name)


elif action == "movieSearchEPG":
    if not name:
        import re
        label = control.infoLabel('ListItem().Label')
        name = re.search(r"^(.+?)(?= \[)", label)
        name = name[0] if name else label
        year = re.search(r"(?<=\[I\]\()\d{4}(?=r\.\)\[/I\])", label)
        year = year[0] if year else control.infoLabel('ListItem().Year')
        # control.log(f'{action=} {name=} {year=}', 1)
    if name and name != "..":
        from resources.lib.indexers import movies
        movies.movies().search_epg(name, year)
    else:
        # bo nie zachowałem w pamięci
        control.directory(int(sys.argv[1]), cacheToDisc=False)  # obowiązkowo
        control.execute('Action(Back)')
        action = "nothing"
        pass

elif action == "prepareItemForAddToLibrary":
    item = {}
    item.update({"fullpath": control.infoLabel('ListItem.Property(fullpath)')})
    if item.get("fullpath"):
        item.update({"label": control.infoLabel('ListItem.Label')})
        item.update({"icon": control.infoLabel('ListItem.Icon')})
        item.update({"year": control.infoLabel('ListItem.Year')})
        #from resources.lib.indexers import movies
        #movies.movies().prepareItemForAddToLibrary([item])
        items = [item]  # dla komatybilności na razie zrobiłem
        syshandle = int(sys.argv[1])
        addonFanart, addonThumb, artPath = (control.addonFanart(), control.addonThumb(), control.artPath(),)
        for i in items:
            label = i.get("label")
            url = i.get("fullpath")
            thumb = i.get("icon")
            item = control.item(label=label)  # create ListItem
            item.setArt({"icon": thumb, "thumb": thumb, "poster": thumb, "fanart": addonFanart, })
            item.setInfo(type="Video", infoLabels={'year': i.get("year")})
            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
        control.directory(syshandle, cacheToDisc=True)
    else:
        control.directory(int(sys.argv[1]), cacheToDisc=False)  # obowiązkowo
        # control.log("akcja wstecz", 1)
        control.execute('Action(Back)')
        action = "nothing"


elif action == "similar":
    if not params.get("tmdb"):
        tmdb = control.infoLabel('ListItem.Property(tmdb_id)')  # starsze Kodi ( < 20)
        tmdb = control.infoLabel('ListItem.UniqueID(tmdb)') if not tmdb else tmdb
        tmdb = tmdb if tmdb else None
    from resources.lib.indexers import movies
    movies.movies().similar(tmdb)


elif action == "moviePerson":
    from resources.lib.indexers import movies
    movies.movies().person()


elif action == "movieGenres":
    from resources.lib.indexers import movies
    movies.movies().genres()


elif action == "movieLanguages":
    from resources.lib.indexers import movies
    movies.movies().languages()


elif action == "movieCertificates":
    from resources.lib.indexers import movies
    movies.movies().certifications()


elif action == "movieYears":
    from resources.lib.indexers import movies
    movies.movies().years()


elif action == "movieYearsTop":
    from resources.lib.indexers import movies
    movies.movies().years_top()


elif action == "moviesAwards":
    from resources.lib.indexers import movies
    movies.movies().awards()


elif action == "movieCompanies":
    from resources.lib.indexers import movies
    movies.movies().companies()


elif action == "moviePersons":  # już chyba niewywoływane stąd
    #if not url:
        #control.log("BŁĄD: brak zmiennej url", 1)
    from resources.lib.indexers import movies
    movies.movies().persons(url)


elif action == "movieUserlists":
    from resources.lib.indexers import movies
    movies.movies().userlists()


elif action == "channels" or action == "movieSearchFromEPG":
    from resources.lib.indexers import channels
    channels.channels().get()


elif action == "tvshows" or action == "tvshowPage":
    if not url:
        url = control.infoLabel('ListItem.Property(url)')
        if url:
            # control.log(f'do pamieci', 1)
            control.window.setProperty('FanFilm.var.url', url)  # do pamięci
        else:
            # control.log(f'z pamieci', 1)
            url = control.window.getProperty('FanFilm.var.url')  # z pamięci
        page = params.get("page")
        if page and "page" not in url:
            q_or_a = "&" if "?" in url else "?"
            url += f"{q_or_a}page={page}"
    # control.log(f'{action=} {url=}', 1)
    refresh = params.get("refresh")
    from resources.lib.indexers import tvshows
    tvshows.tvshows().get(url, refresh=refresh)


elif action == "tvSearch":
    control.window.clearProperty('FanFilm.var.name')  # wyczyszcenie
    from resources.lib.indexers import tvshows
    tvshows.tvshows().search()


elif action == "tvSearchnew":
    from resources.lib.indexers import tvshows
    tvshows.tvshows().search_new()


elif action == "tvSearchterm":
    if not params.get("name"):
        folderpath = control.infoLabel('Container.FolderPath') 
        referer = dict(parse_qsl(folderpath.split('?')[-1]))
        if referer.get("action") == "tvSearch":
            name = control.infoLabel('ListItem().Label')  # z wybranej pozycji
            control.window.setProperty('FanFilm.var.name', name)  # do pamięci
            # control.log(f'do pamieci', 1)
        else:
            name = control.window.getProperty('FanFilm.var.name')  # z pamięci
            # control.log(f'z pamieci', 1)
    from resources.lib.indexers import tvshows
    tvshows.tvshows().search_term(name)


elif action == "tvPerson":
    from resources.lib.indexers import tvshows
    tvshows.tvshows().person()


elif action == "tvGenres":
    from resources.lib.indexers import tvshows
    tvshows.tvshows().genres()


elif action == "tvNetworks":
    from resources.lib.indexers import tvshows
    tvshows.tvshows().networks()


elif action == "tvLanguages":
    from resources.lib.indexers import tvshows
    tvshows.tvshows().languages()


elif action == "tvCertificates":
    certification_country = params.get("certification_country")
    from resources.lib.indexers import tvshows
    tvshows.tvshows().certifications(certification_country)


elif action == "tvYears":
    from resources.lib.indexers import tvshows
    tvshows.tvshows().years()


elif action == "tvYearsTop":
    from resources.lib.indexers import tvshows
    tvshows.tvshows().years_top()


elif action == "tvPersons":  # już chyba niewywoływane stąd
    #if not url:
        #control.log("BŁĄD: brak zmiennej url", 1)
    from resources.lib.indexers import tvshows
    tvshows.tvshows().persons(url)


elif action == "tvUserlists":
    from resources.lib.indexers import tvshows
    tvshows.tvshows().userlists()


elif action == "seasons":
    meta = params.get("meta")
    localtvshowtitle = params.get("localtvshowtitle")

    if not params.get("tvshowtitle"):
        tvshowtitle = control.infoLabel('ListItem.Property(englishTvShowTitle)')
        tvshowtitle = control.infoLabel('ListItem.TvShowTitle') if not tvshowtitle else tvshowtitle
        tvshowtitle = control.infoLabel('ListItem.Property(englishTitle)') if not tvshowtitle else tvshowtitle
        tvshowtitle = control.infoLabel('ListItem.OriginalTitle') if not tvshowtitle else tvshowtitle
    if not params.get("localtvshowtitle"):
        localtvshowtitle = control.infoLabel('ListItem.TvShowTitle') 
        localtvshowtitle = control.infoLabel('ListItem.Title') if not localtvshowtitle else localtvshowtitle
    if not params.get("originaltvshowtitle"):
        originaltvshowtitle = control.infoLabel('ListItem.Property(OriginalTvShowTitle)')
        originaltvshowtitle = control.infoLabel('ListItem.OriginalTitle') if not originaltvshowtitle else originaltvshowtitle
        # control.log(f'{originaltvshowtitle=}', 1)
    if not params.get("year"):
        year = control.infoLabel('ListItem.Property(TvShowYear)')
        year = control.infoLabel('ListItem.Year') if not year else year
    if not params.get("imdb"):
        imdb = control.infoLabel('ListItem.Property(imdb_id)')
        imdb = control.infoLabel('ListItem.UniqueID(imdb)') if not imdb else imdb
    if not params.get("tmdb"):
        tmdb = control.infoLabel('ListItem.Property(tmdb_id)')
        tmdb = control.infoLabel('ListItem.UniqueID(tmdb)') if not tmdb else tmdb
    if not params.get("tvdb"):
        tvdb = control.infoLabel('ListItem.Property(tvdb_id)')
        tvdb = control.infoLabel('ListItem.UniqueID(tvdb)') if not tvdb else tvdb
    if not params.get("meta"):
        meta = control.infoLabel('ListItem.Property(meta)')

    #if not tvshowtitle or not tmdb:  # czemu tylko tmdb a nie imdb ?
    if not tvshowtitle or not tmdb and not imdb:  # próba
        # control.log(f'z pamieci', 1)
        zmienne = control.window.getProperty('FanFilm.var.curr_item_s')  # z pamięci
        if zmienne:
            zmienne = eval(zmienne)
            globals().update(zmienne)  # opcjonalnie
    else:
        # control.log(f'do pamieci', 1)
        #zmienne = (tvshowtitle, year, imdb, tmdb, meta)
        zmienne = {"tvshowtitle":tvshowtitle, "year":year, "imdb":imdb, "tmdb":tmdb, "tvdb":tvdb, "meta":meta, "localtvshowtitle":localtvshowtitle, "originaltvshowtitle":originaltvshowtitle}
        control.window.setProperty('FanFilm.var.curr_item_s', repr(zmienne))  # do pamięci
    
    # control.log(f" [ KONTROLA_s ] {tvshowtitle=} {year=} {imdb=} {tmdb=} {tvdb=} {localtvshowtitle=} {originaltvshowtitle=}  {meta=}", 1)

    select = control.setting("hosts.mode")
    if control.setting("generate_short_path") == "true" and (params.get("title") or params.get("tvshowtitle")) and select == "1" and not params.get("r"):
        control.window.setProperty('FanFilm.var.before_r', repr(params))  # do pamięci
        control.addItem(int(sys.argv[1]), sys.argv[0]+"?action=nothing", control.item(" proszę czekać ..."), False)  # opcjonalnie
        control.directory(int(sys.argv[1]), cacheToDisc=False, updateListing=True)  # obowiązkowo i musi być False, bo przy True nie chce robić przekierowania, gdy wyświetla stronę z cachu
        # control.log("przekierowanie (odświeżenie) z obcięciem parametrów", 1)  # tu dodatkowe polecenie jako zwłoka przed następnym
        control.sleep0(100)
        control.execute('Container.Update(' + sys.argv[0]+f"?action={action}&r=1" + ')')
        action = "nothing"
    else:
        from resources.lib.indexers import episodes
        episodes.seasons().get(tvshowtitle, year, imdb, tmdb, tvdb, meta, localtvshowtitle=localtvshowtitle, originaltvshowtitle=originaltvshowtitle)


elif action == "episodes":
    zmienne = None
    #if not tvshowtitle or not tmdb:  # czemu tmdb a nie imdb ?
    # if not tvshowtitle or not (tmdb and imdb):  # próba, czy będzie dobrze działać
    if generate_short_path and not referer or params.get("r"):  # ryzykowniejsze, bo trafiła mi się nieskończona pętla
        # control.log(f'z pamieci (próba)', 1)
        zmienne = control.window.getProperty('FanFilm.var.curr_item_e')  # z pamięci
        if zmienne:
            zmienne = eval(zmienne)
            globals().update(zmienne)  # opcjonalnie
        else:
            # control.log(f'nieudana próba', 1)
            pass

    if not zmienne:
        # pobranie wszystkich potrzebnych zmiennych
        # jak podane w url, to priorytet nad kryjącym się w ListItem
        # season = params.get("season")  # to jest na początku tego pliku
        # episode = params.get("episode")  # j.w.
        meta = params.get("meta")
        localtvshowtitle = params.get("localtvshowtitle") or ""
        originaltvshowtitle = params.get("originaltvshowtitle") or ""

        # control.log(f'{generate_short_path=}  {referer=}', 1)
        if generate_short_path and referer:
            # control.log(f'odczytywanie z ListItemu', 1)
            if not episode:
                episode = control.infoLabel('ListItem.Episode')  # nie można tego przy odświeżaniu
                episode = episode if episode else None  # ważne jest None (choć 0 i '' też daje not episode)

            if not season:
                season = control.infoLabel('ListItem.Season')
                season = season if season else None  # ważne tu

            if not meta:
                meta = control.infoLabel('ListItem.Property(meta)')

            if not year:
                year = control.infoLabel('ListItem.Property(TvShowYear)')
                year = control.infoLabel('ListItem.Year') if not year else year

            if not imdb:
                imdb = control.infoLabel('ListItem.Property(imdb_id)')
                imdb = control.infoLabel('ListItem.UniqueID(imdb)') if not imdb else imdb

            if not tmdb:
                tmdb = control.infoLabel('ListItem.Property(tmdb_id)')
                tmdb = control.infoLabel('ListItem.UniqueID(tmdb)') if not tmdb else tmdb

            if not tvdb:
                tvdb = control.infoLabel('ListItem.Property(tvdb_id)')
                tvdb = control.infoLabel('ListItem.UniqueID(tvdb)') if not tvdb else tvdb

            if not tvshowtitle:
                tvshowtitle = control.infoLabel('ListItem.Property(englishTvShowTitle)')
                tvshowtitle = control.infoLabel('ListItem.TvShowTitle') if not tvshowtitle else tvshowtitle

            if not localtvshowtitle:
                localtvshowtitle = control.infoLabel('ListItem.TvShowTitle')
                # control.log(f'{originaltvshowtitle=}', 1)

            if not originaltvshowtitle:
                originaltvshowtitle = control.infoLabel('ListItem.Property(OriginalTvShowTitle)')
                # control.log(f'{originaltvshowtitle=}', 1)


        #zmienne = (tvshowtitle, year, imdb, tmdb, meta)
        zmienne = {"tvshowtitle":tvshowtitle, "year":year, "imdb":imdb, "tmdb":tmdb, "tvdb":tvdb, "meta":meta,
                   "season":season, "episode":episode, "localtvshowtitle":localtvshowtitle, "originaltvshowtitle":originaltvshowtitle}
        # control.log(f'do pamieci', 1)
        control.window.setProperty('FanFilm.var.curr_item_e', repr(zmienne))  # do pamięci

    # control.log(f" [ KONTROLA_e ] {tvshowtitle=} {year=} {imdb=} {tmdb=} {tvdb=} {season=} {episode=} {localtvshowtitle=} {originaltvshowtitle=}  {meta=}", 1)

    select = control.setting("hosts.mode")
    # control.log(f'{select=}', 1)

    # sprawdzenie, czy zrobić jeszcze dodatkowe przekerowanie
    # a może zrobić z tego funkcję? bo się powtarza w kilku miejscach
    # control.log(f" {sys.argv=} ", 1)
    import time
    if generate_short_path and (params.get("title") or params.get("tvshowtitle")) and select == "1" and not params.get("r"):
        if (not (r_time := control.window.getProperty('FanFilm.var.r_time')) or int(r_time) < int(time.time()) - 2):  # ma służyć przed nieskończonym przekierowaniem w niektórych sytuacjach (jak np. błąd pythona w trakcie wykonywania kodu)
            control.window.setProperty('FanFilm.var.r_time', str(int(time.time())) )  # ustawienie znacznika r
            control.log(f'będzie przekierowanie jeszcze', 1)
            control.window.setProperty('FanFilm.var.before_r', repr(params))  # do pamięci
            control.addItem(int(sys.argv[1]), sys.argv[0]+"?action=nothing", control.item(" proszę czekać ..."), False)  # opcjonalnie
            control.directory(int(sys.argv[1]), cacheToDisc=False, updateListing=True)  # obowiązkowo i musi być False, bo przy True nie chce robić przekierowania, gdy wyświetla stronę z cachu
            # control.log("przekierowanie (odświeżenie) z obcięciem parametrów", 1)  # tu dodatkowe polecenie jako zwłoka przed następnym
            control.sleep0(100)
            control.execute('Container.Update(' + sys.argv[0]+f"?action={action}&r=1" + ')')  # uruchomienie przekierowania
            action = "nothing"
        else:
            control.log(f"przekierowanie zostało zablokowane", 1)
            action = "nothing"  # nie wiem, czy dać
            pass
    else:  # można wreszcie wywołać właściwą funkcję
        from resources.lib.indexers import episodes
        episodes.episodes().get(tvshowtitle, year, imdb, tmdb, tvdb, season, episode, meta, localtvshowtitle=localtvshowtitle, originaltvshowtitle=originaltvshowtitle)
        control.window.clearProperty('FanFilm.var.r_time')  # reset (może dać na sam koniec)

elif action == "calendar":
    # control.log(f'{url=}', 1)
    if not url:
        url = control.infoLabel('ListItem.Property(url)')
        if url:
            # control.log(f'do pamieci', 1)
            control.window.setProperty('FanFilm.var.url', url)  # do pamięci
        else:
            # control.log(f'z pamieci', 1)
            url = control.window.getProperty('FanFilm.var.url')  # z pamięci
    # control.log(f'{url=}', 1)
    refresh = params.get("refresh")
    from resources.lib.indexers import episodes
    episodes.episodes().calendar(url, refresh)


elif action == "tvWidget":
    from resources.lib.indexers import episodes
    episodes.episodes().widget()


elif action == "calendars":
    from resources.lib.indexers import episodes
    episodes.episodes().calendars()


elif action == "episodeUserlists":
    from resources.lib.indexers import episodes
    episodes.episodes().userlists()


elif action == "refresh":
    from ptw.libraries import control
    control.refresh()


elif action == "queueItem":
    from ptw.libraries import control
    control.queueItem()


elif action == "openSettings":
    from ptw.libraries import control
    control.openSettings(params.get("query"))


elif action == "artwork":
    from ptw.libraries import control
    control.artwork()


elif action == "addView":
    from ptw.libraries import views
    views.addView(params.get("content"))


elif action == "moviePlaycount":
    from ptw.libraries import playcount
    playcount.movies(imdb, params.get("query"))


elif action == "episodePlaycount":
    from ptw.libraries import playcount
    playcount.episodes(imdb, tvdb, season, episode, params.get("query"))


elif action == "tvPlaycount":
    from ptw.libraries import playcount
    playcount.tvshows(name, imdb, tmdb, season, params.get("query"))


elif action == "trailer":
    # Zamknij = False  # gdzie to ma przełożenie ?
    windowedtrailer = params.get("windowedtrailer")
    # windowedtrailer = "1"  # nie wiem, co to ma dawać, bo i tak odtwarza się na całym ekranie
    windowedtrailer = int(windowedtrailer) if windowedtrailer in ("0", "1") else 0
    # control.log(f'{name=} {url=} {windowedtrailer=}', 1)
    from ptw.libraries import trailer
    trailer.trailer().play(name, url, windowedtrailer)


elif action == "traktManager":
    from ptw.libraries import trakt
    content = params.get("content")
    trakt.manager(name, imdb, tmdb, content)


elif action == "authTrakt":
    from ptw.libraries import trakt
    trakt.authTrakt()


elif action == "pairEkino":
    from resources.lib.sources.pl import ekinotv
    ekinotv.source().pair_scraper()


elif action == "smuSettings":
    try:
        import resolveurl
    except Exception:
        pass
    resolveurl.display_settings()


elif action == "download":
    # control.log(f'{action=}', 1)
    control.busy()
    control.sleep(200)
    import json
    from ptw.libraries import sources
    from ptw.libraries import downloader
    source = params.get("source")
    image = params.get("image")
    extrainfo = params.get("extrainfo", "")
    Zamknij = False  # gdzie to ma przełożenie ?
    url = sources.sources().sourcesResolve(json.loads(source)[0], True)  # jak wywołanie jest z folderu (nie z okna)
    downloader.download(name, image, url, extrainfo)
    control.idle(2)

    
elif action == "buyItemAgain":
    from ptw.libraries import sources
    sources.sources().playItem(title, params.get("source"), for_sourcesResolve={'for_resolve': {'buy_anyway': True}})


elif action == "alterSources":
    #if not url:
        #control.log("BŁĄD: brak zmiennej url", 1)
    from ptw.libraries import sources
    sources.sources().alterSources(url, params.get("meta"))


elif action == "clearSources":
    from ptw.libraries import sources
    sources.sources().clearSources()


elif action == "random":
    if not url:
        control.log("BŁĄD: brak zmiennej url", 1)
    rtype = params.get("rtype")
    if rtype == "movie":
        from resources.lib.indexers import movies
        rlist = movies.movies().get(url, create_directory=False)
        r = sys.argv[0] + "?action=play"
    elif rtype == "episode":
        from resources.lib.indexers import episodes
        rlist = episodes.episodes().get(tvshowtitle, year, imdb, tmdb, season, create_directory=False)
        r = sys.argv[0] + "?action=play"
    elif rtype == "season":
        from resources.lib.indexers import episodes
        rlist = episodes.seasons().get(tvshowtitle, year, imdb, tmdb, create_directory=False)
        r = sys.argv[0] + "?action=random&rtype=episode"
    elif rtype == "show":
        from resources.lib.indexers import tvshows
        rlist = tvshows.tvshows().get(url, create_directory=False)
        r = sys.argv[0] + "?action=random&rtype=season"

    #from ptw.libraries import control
    from urllib.parse import quote_plus
    from random import randint
    import json

    select = params.get("select")  # nie wiem czy to tu potrzebne
    meta = params.get("meta")  # to samo co wyżej
    premiered = params.get("premiered")  # to samo co wyżej
    try:
        rand = randint(1, len(rlist)) - 1
        for p in ["title", "year", "imdb", "tmdb", "season", "episode", "tvshowtitle", "premiered", "select", ]:
            if rtype == "show" and p == "tvshowtitle":
                try:
                    r += "&" + p + "=" + quote_plus(rlist[rand]["title"])
                except Exception:
                    pass
            else:
                try:
                    r += "&" + p + "=" + quote_plus(rlist[rand][p])
                except Exception:
                    pass
        try:
            r += "&meta=" + quote_plus(json.dumps(rlist[rand]))
        except Exception:
            r += "&meta=" + quote_plus("{}")
        if rtype == "movie":
            try:
                control.infoDialog(rlist[rand]["title"], control.lang(32536), time=30000, )
            except Exception:
                pass
        elif rtype == "episode":
            try:
                control.infoDialog(
                    rlist[rand]["tvshowtitle"] + " - Season " + rlist[rand]["season"] + " - " + rlist[rand][
                        "title"], control.lang(32536), time=30000, )
            except Exception:
                pass
        control.execute("RunPlugin(%s)" % r)
    except Exception:
        control.infoDialog(control.lang(32537), time=8000)


elif action == "movieToLibrary":
    from ptw.libraries import libtools
    libtools.libmovies().add(name, title, localtitle, year, imdb, tmdb)


elif action == "moviesToLibrary":
    #if not url:
        #control.log("BŁĄD: brak zmiennej url", 1)
    from ptw.libraries import libtools
    libtools.libmovies().range(url)


elif action == "moviesMultiToLibrary":
    from ptw.libraries import libtools
    libtools.libmovies().multi(params.get("select"))


elif action == "moviesToLibrarySilent":
    #if not url:
        #control.log("BŁĄD: brak zmiennej url", 1)
    from ptw.libraries import libtools
    libtools.libmovies().silent(url)


elif action == "tvshowToLibrary":
    from ptw.libraries import libtools
    meta = params.get("meta")
    localtvshowtitle = params.get("localtvshowtitle")
    libtools.libtvshows().add(tvshowtitle, year, imdb, tmdb, season, episode, meta, localtvshowtitle=localtvshowtitle)


elif action == "tvshowsToLibrary":
    #if not url:
        #control.log("BŁĄD: brak zmiennej url", 1)
    from ptw.libraries import libtools
    libtools.libtvshows().range(url)


elif action == "tvshowsToLibrarySilent":
    #if not url:
        #control.log("BŁĄD: brak zmiennej url", 1)
    from ptw.libraries import libtools
    libtools.libtvshows().silent(url)


elif action == "updateLibrary":
    from ptw.libraries import libtools
    libtools.libepisodes().update(params.get("query"))


elif action == "tmdbauthorize":
    from ptw.libraries import tmdbauth
    tmdbauth.Auth().create_session_id()


elif action == "tmdbdeauthorize":
    from ptw.libraries import tmdbauth
    tmdbauth.Auth().revoke_session_id()


elif action == "libepisodesservice":
    # przeniosłem uruchamianie do service.py
    if False:
        control.log("[FanFilm] start service (cyclic) for checking and updating library episodes (once call from service.py)", 0)
        from ptw.libraries import libtools
        libtools.libepisodes().service()


control.log(f'[FanFilm][default.py]   koniec {params=}\n', 0)
# control.log(f"============================================================", 1)

# control.log(f'[FanFilm][default.py]   {action=}', 1)
# control.log(f'[FanFilm][default.py]   {params=}', 1)
if (action != "nothing"
    # and params != KFolderPath
     and params != FFlastpath
   ):
    control.window.setProperty('FanFilm.var.lastpath', repr(params))  # do pamięci

# try to prevent infinite busydialog
handle = int(sys.argv[1])
# control.log(f"[FanFilm]  koniec  {sys.argv=}", 1)
# control.log(f"[FanFilm]  koniec  {handle=}  {action=}", 1)
if handle > -1 and action not in ['removeFromSearchHistory', 'clearCacheSearch', 'trailer', 'nothing']:

    c = 3
    while control.condVisibility('Window.IsActive(busydialog)') and c > 0:
        control.sleep0(100)
        c -= 1

    # PluginName = control.infoLabel('Container.PluginName')  # tu można pomyśleć (jak pusty, lub nie 'plugin.video.fanfilm', to oznacza, że wywoływane z innego pluginu)
    # control.log(f"[FanFilm] {PluginName=}", 1)
    # isFolder = control.condVisibility('ListItem.IsFolder')  # nie sprawdza się, bo nie zawsze potrafi odczytać prawidłową pozycję
    # control.log(f"[FanFilm] {isFolder=}", 1)
    # IsPlayable = control.infoLabel('ListItem.Property(IsPlayable)')  # na tym też do końca nie można polegać, bo Kodi czasami tego nie odczytuje prawidłowo
    # control.log(f'[FanFilm] {IsPlayable=}', 1)
    ilosc_pozycji_do_wyswietlenia = control.infoLabel("Container().NumItems")  # często pokazuje iformacje przed odświeżeniem, także nieprzydatne wówczas (a jak pokazuje, to czasami jest puste a czasami 0 - i bądź tu mądry)
    # control.log(f'[FanFilm] {ilosc_pozycji_do_wyswietlenia=}', 1)
    # control.log(f"[FanFilm] {control.currentDialogId()=}", 1)  # może być BusyDialog albo ProgressDialog (10101)

    if (
        control.condVisibility('Window.IsActive(busydialog)')  # trafiłem na ProgressDialog przy próbie tworzenia skrótu przez skórkę
        # or (not ilosc_pozycji_do_wyswietlenia or int(ilosc_pozycji_do_wyswietlenia) < 1)  # to pomogło przy próbie tworzenia skrótu przez skórkę
        or not ilosc_pozycji_do_wyswietlenia  # czy to by nie wystarczyło? (zamiast powyższej linijki)
       ):
        if action != "play":  # nie wiem, czy to dobrze !  (jeszcze ewentualnie z select można spróbować dołożyć, bo playItem się nie sprawdził, jak materiał się nie odtworzył
            control.log('[FanFilm] dodanie pustego katalogu', 1)
            updateListing = True if params.get("r") else False  # True świadczy, że po drodze było odświeżanie
            control.directory(handle, cacheToDisc=True, updateListing=updateListing)  # w Kodi 19 może pojawiś się czasami WARNING w logach (że niepotrzebnie czasami taka operacja), ale w nowszych nie widziałem
            control.sleep0(100)

        if control.currentDialogId() == 9999 and action != "playItem":  # nie pamiętam co oznacza 9999 (może brak jakiegokolwiek okna)
            if action != "play" or select == "1":  # czy zmienna "select" zawsze jest zdefiniowana?
                if not control.monitor.abortRequested():
                    control.log(f"[FanFilm] Can't display content for {sys.argv=}", 1)
                    if False:  # tymczasowo, jako wybór wariantu
                        # control.log(f"[FanFilm] Can't display content for {sys.argv=}", 1)  # wyniosłem wyżej
                        # control.log(f"------------------------------------------------------------ \n", 1)
                        control.infoDialog(f"Can't show content[CR] ERROR    for {action=}", icon="ERROR", time=2000, sound=True)
                        # control.addItem(handle, url=sys.argv[0]+"?action=nothing", listitem=control.item(label="Wystąpił jakiś błąd"), isFolder=False)
                    else:
                        # control.sleep(100)
                        if control.infoLabel('ListItem.Property(IsPlayable)') != 'true':  # nie wiem, czy to ma sens, bo chyba zawsze będzie spełnione
                            ilosc_pozycji_do_wyswietlenia = control.infoLabel("Container().NumItems")
                            # control.log(f'[FanFilm] {ilosc_pozycji_do_wyswietlenia=}', 1)
                            if ilosc_pozycji_do_wyswietlenia and int(ilosc_pozycji_do_wyswietlenia) < 1:  # dodatkowe zabezpieczenie
                                control.log(f"[FanFilm] action Back", 1)
                                control.execute('Action(Back)')
                sys.exit()  # nie wiem, czy to jest na końcu potrzebne

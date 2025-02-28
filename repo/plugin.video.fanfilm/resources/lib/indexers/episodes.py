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

import datetime
import json
import os
import re
import sys
from urllib.parse import (parse_qsl, quote, unquote_plus, quote_plus, urlsplit, urlencode, urlparse, )

import requests
import six  # Do wywalenia - wkrótce
from ptw.libraries import apis
from ptw.libraries import cache
from ptw.libraries import cleantitle
from ptw.libraries import client
from ptw.libraries import control
from ptw.libraries import log_utils
from ptw.libraries import source_utils
from ptw.libraries.log_utils import log, fflog, _is_debugging
from ptw.debug import log_exception, fflog_exc
from ptw.libraries import playcount
from ptw.libraries import trakt
from ptw.libraries import utils
from ptw.libraries import views
from xbmcplugin import addSortMethod, SORT_METHOD_UNSORTED
from resources.lib.indexers.super_info import SuperInfo

# import simplejson as json

params = dict(parse_qsl(sys.argv[2].replace("?", ""))) if len(sys.argv) > 1 else dict()

action = params.get("action")


class seasons:
    def __init__(self):
        # fflog("inicjalizacja klasy seasons")

        # fix for not always current value
        global params, action
        params = dict(parse_qsl(sys.argv[2].replace("?", ""))) if len(sys.argv) > 1 else dict()
        action = params.get("action")

        self.session = requests.Session()

        self.showunaired = control.setting("showunaired") or "true"
        # self.specials = "false"
        self.specials = control.setting('tv.specials')
        # self.trailer_source = "1"
        self.trailer_source = control.setting('trailer.source')
        #fflog(f'{self.trailer_source=}')

        self.datetime = datetime.datetime.utcnow()  # - datetime.timedelta(hours = 5)
        self.today_date = self.datetime.strftime("%Y-%m-%d")

        self.lang = control.apiLanguage()["tmdb"] or "en"
        self.tm_user = control.setting("tm.user") or apis.tmdb_API

        self.tmdb_show_link = "https://api.themoviedb.org/3/tv/%s?api_key=%s&language=%s&append_to_response=aggregate_credits,content_ratings,external_ids" % ("%s", self.tm_user, "%s")
        self.tmdb_show_lite_link = "https://api.themoviedb.org/3/tv/%s?api_key=%s&language=en" % ("%s", self.tm_user)
        self.tmdb_by_imdb = "https://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id" % ("%s", self.tm_user)
        self.search_link = "https://api.themoviedb.org/3/search/tv?api_key=%s&language=en-US&query=%s&page=1" % (self.tm_user, "%s")
        self.tm_img_link = "https://image.tmdb.org/t/p/w%s%s"

        self.list = []


    def __del__(self):
        self.session.close()


    def get(self, tvshowtitle, year, imdb, tmdb, tvdb=None, meta=None, localtvshowtitle="", originaltvshowtitle="", idx=True, create_directory=True):
        fflog(f'(seasons) {params=}', 1, 1)
        try:
            if idx:
                self.list = cache.get(self.tmdb_list, 24, tvshowtitle, year, imdb, tmdb, tvdb, meta, localtvshowtitle, originaltvshowtitle)
                #log_utils.log('idx_list_loaded ')
                #fflog(repr(self.list))
                if create_directory:
                    self.seasonDirectory(self.list)
                return self.list
            else:
                self.list = self.tmdb_list(tvshowtitle, year, imdb, tmdb, tvdb, localtvshowtitle=localtvshowtitle, originaltvshowtitle=originaltvshowtitle, lite=True)
                #log_utils.log('nonidx_list_loaded ')# + repr(self.list))
                return self.list
        except Exception:
            fflog_exc(1)
            log_utils.log("seasons_get", "indexer")


    def tmdb_list(self, tvshowtitle, year, imdb, tmdb, tvdb, meta=None, localtvshowtitle="", originaltvshowtitle="", lite=False):
        # fflog(f'{lite=}',1,1)
        try:

            if tmdb is None and not imdb == "0":
                try:
                    url = self.tmdb_by_imdb % imdb
                    # control.log(f'{url=}', 1)
                    result = self.session.get(url, timeout=10).json()
                    tmdb_result = result["tv_results"][0]
                    tmdb = tmdb_result["id"]
                    if not tmdb:
                        tmdb = "0"
                    else:
                        tmdb = str(tmdb)
                except Exception:
                    # fflog_exc(1)
                    pass

            if tmdb == "0" and tvshowtitle:
                try:
                    url = (self.search_link % (quote(tvshowtitle)) + "&first_air_date_year=" + year)
                    # control.log(f'{url=}', 1)
                    result = self.session.get(url, timeout=10).json()
                    results = result["results"]
                    show = [r for r in results if cleantitle.get(r.get("name")) == cleantitle.get(tvshowtitle)][
                        0]  # and re.findall('(\d{4})', r.get('first_air_date'))[0] == year][0]
                    tmdb = show["id"]
                    if not tmdb:
                        tmdb = "0"
                    else:
                        tmdb = str(tmdb)
                except Exception:
                    # fflog_exc(1)
                    pass

        except Exception as e:
            log_utils.log("tmdb-list0 Exception %s" % e, "indexer")
            fflog_exc(1)
            pass

        try:
            if tmdb == "0":
                raise Exception(f"{tmdb=}")

            seasons_url = self.tmdb_show_link % (tmdb, self.lang) + ",translations"
            seasons_en_url = self.tmdb_show_link % (tmdb, "en")
            seasons_lite_url = self.tmdb_show_lite_link % tmdb

            if self.lang == "en":
                url = seasons_en_url
            elif lite:
                url = seasons_lite_url
            else:
                url = seasons_url

            # control.log(f'{url=}', 1)
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            r.encoding = "utf-8"
            item = r.json()
            # log_utils.log('tmdb_item: ' + str(item))

            if imdb == "0":
                try:
                    imdb = item["external_ids"]["imdb_id"]
                    if not imdb:
                        imdb = "0"
                except Exception:
                    pass

            try:
                # if not tvdb:
                tvdb = item["external_ids"]["tvdb_id"]
                if not tvdb:
                    tvdb = "0"
                else:
                    tvdb = str(tvdb)
            except Exception:
                tvdb = "0"

            seasons = item["seasons"]

            if self.specials == "false":
                seasons = [s for s in seasons if not s["season_number"] == 0]

            # check if en version needed
            seasons_en = {}
            for s_item in seasons:
                plot = s_item["overview"]
                if not plot:
                    log_utils.fflog('potrzeba pobrania angielskich opisów do sezonów', 0)
                    # control.log(f'{seasons_en_url=}', 1)
                    r_en = self.session.get(seasons_en_url, timeout=10)
                    r_en.raise_for_status()
                    r_en.encoding = "utf-8"
                    seasons_en = r_en.json()["seasons"]
                    break

            if self.specials == "false":
                seasons_en = [s for s in seasons_en if not s["season_number"] == 0]

            try:
                studio = item["networks"][0]["name"]
            except:
                studio = ""
            if not studio:
                studio = "0"

            try:
                genres = item["genres"]
                genre = [d["name"] for d in genres]
                genre = " / ".join(genre)
            except:
                genre = ""
            if not genre:
                genre = "0"

            try:
                duration = item["episode_run_time"][0]
                duration = str(duration)
            except:
                duration = ""
            if not duration:
                duration = "0"

            try:
                m = item["content_ratings"]["results"]
                #mpaa = [d["rating"] for d in m if d["iso_3166_1"] == "US"][0]
                mpaa = [d["rating"] for d in m if d["iso_3166_1"] in ["US","PL"]][0]
            except:
                mpaa = ""
            if not mpaa:
                mpaa = "0"
            #fflog(f'{mpaa=}')

            try:
                status = item["status"]
            except:
                status = ""
            if not status:
                status = "0"

            castwiththumb = []
            try:
                c = item["aggregate_credits"]["cast"][:30]
                for person in c:
                    _icon = person["profile_path"]
                    icon = self.tm_img_link % ("185", _icon) if _icon else ""
                    castwiththumb.append(
                        {"name": person["name"], "role": person["roles"][0]["character"], "thumbnail": icon, })
            except Exception:
                pass
            if not castwiththumb:
                castwiththumb = "0"

            # opis serialu (nie sezonu) - na wypadek, gdy nie będzie opisu sezonu
            try:
                show_plot = item["overview"]
            except:
                show_plot = ""
            if not show_plot:
                show_plot = "0"
            if not self.lang == "en" and show_plot == "0":
                try:
                    translations = item["translations"]["translations"]
                    trans_item = [x["data"] for x in translations if x.get("iso_639_1") == "en"][0]
                    show_plot = trans_item["overview"]
                except:
                    pass

            unaired = ""

            try:
                poster_path = item["poster_path"]
            except:
                poster_path = ""
            if poster_path:
                show_poster = self.tm_img_link % ("500", poster_path)
            else:
                show_poster = "0"

            try:
                fanart_path = item["backdrop_path"]
            except:
                fanart_path = ""
            if fanart_path:
                show_fanart = self.tm_img_link % ("1280", fanart_path)
            else:
                show_fanart = "0"

            meta_poster = meta_fanart = None
            banner = clearlogo = clearart = keyart = landscape = characterart = "0"

            if meta:
                _meta = json.loads(unquote_plus(meta))
                #fflog(f'{_meta=}')
                meta_poster, meta_fanart, banner, clearlogo, clearart, keyart, landscape, characterart = (
                    #_meta["poster"], _meta["fanart"], _meta["banner"], _meta["clearlogo"], _meta["clearart"], _meta["landscape"],
                    _meta.get("poster"), _meta.get("fanart"), _meta.get("banner"), _meta.get("clearlogo"), _meta.get("clearart"), _meta.get("keyart"), _meta.get("landscape"), _meta.get("characterart"),
                )
            else:
                _meta = {}

        except Exception as e:
            log_utils.log("tmdb-list1 Exception: %s " % e, "indexer")
            fflog_exc(1)
            return

        count = 0
        # fflog(f'{len(seasons)=}',1,1)
        for s_item in seasons:
            try:
                # fflog(f's_item={json.dumps(s_item, indent=2)}',1,1)
                name = str(s_item["name"])
                
                season = str(s_item["season_number"])

                premiered = s_item.get("air_date", "0") or "0"

                if status == "Ended":
                    pass
                elif not premiered or premiered == "0":
                    # raise Exception()
                    # continue
                    pass
                    # brak daty może oznaczać, że nie znana jest jeszcze premiera (ale i też, że nie została wprowadzona informacja o tym)
                    unaired = "true"
                    if self.showunaired != "true":
                        continue
                elif int(re.sub("[^0-9]", "", str(premiered))) > int(re.sub("[^0-9]", "", str(self.today_date))):
                    unaired = "true"
                    if self.showunaired != "true":
                        # raise Exception()
                        continue

                plot = s_item["overview"]
                if not plot:
                    plot = seasons_en[count]["overview"]
                    if not plot:
                        # plot = show_plot
                        pass

                count += 1

                episodes = s_item.get("episode_count")

                poster_path = s_item.get("poster_path")
                if poster_path:
                    season_poster = self.tm_img_link % ("500", poster_path)
                else:
                    season_poster = None
                # fflog(f'{_meta=} {_meta.get("seasons_posters")=} {season=}')
                poster = season_poster or meta_poster or show_poster
                poster = _meta.get("seasons_posters", {}).get(season) or poster

                banner = _meta.get("seasons_banners", {}).get(season) or _meta.get("banner") or ""
                landscape = _meta.get("seasons_landscapes", {}).get(season) or _meta.get("landscape") or ""
                # fflog(f'{season=}')
                # fflog(f'{_meta.get("seasons_banners")=}')
                # fflog(f'{_meta.get("seasons_banners").get(season)=}')
                # fflog(f'{banner=}')

                # fanart = meta_fanart or show_fanart
                fanart = _meta.get("seasons_fanarts", {}).get(season) or _meta.get("fanart") or show_fanart or ""

                self.list.append({
                    "title": name, "season": season, "tvshowtitle": tvshowtitle, "year": year, "premiered": premiered,
                    "status": status, "studio": studio, "genre": genre, "duration": duration, "mpaa": mpaa,
                    "castwiththumb": castwiththumb, "plot": plot, "imdb": imdb, "tmdb": tmdb, "tvdb": tvdb,
                    "poster": poster, "fanart": fanart, "banner": banner, "clearlogo": clearlogo, "clearart": clearart,
                    "landscape": landscape, "unaired": unaired, "keyart": keyart, "characterart": characterart,
                    "localtvshowtitle": localtvshowtitle, "originaltvshowtitle": originaltvshowtitle, "episodes": episodes,
                    })

            except Exception as e:
                log_utils.log("seasons_dir Exception: %s " % e, "indexer")
                fflog_exc(1)
                pass

        try:
            cache.cache_insert("seasons" + f"_{tmdb or imdb}", repr(self.list))  # to w sumie nie jest do niczego potrzebne
        except Exception:
            fflog_exc(1)
            pass
        # fflog(f'self.list={json.dumps(self.list, indent=2)}')
        return self.list


    def seasonDirectory(self, items):
        #fflog(f'[seasonDirectory]')
        if items is None or len(items) == 0:
            return  #  ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        if control.setting("zastepcze_grafiki") == "true":
            addonPoster = control.addonPoster()
            addonFanart = control.addonFanart()
            addonBanner = control.addonBanner()
        else:
            addonPoster = addonFanart = addonBanner = ""

        settingFanart = control.setting("fanart")

        traktCredentials = trakt.getTraktCredentialsInfo()

        isOld = False
        try:
            control.item().getArt("type")
        except Exception:
            #fflog_exc(1)
            isOld = True

        try:
            indicators = playcount.getSeasonIndicators(items[0]["imdb"])
            #fflog(f'{indicators=}')
        except Exception:
            #fflog_exc(1)
            indicators = []
            pass

        # trailerAction = "tmdb_trailer" if self.trailer_source == "0" else "yt_trailer"  # to nie jest zrobione
        trailerAction = "trailer"
        watchedMenu =   (control.lang(32068) if trakt.getTraktIndicatorsInfo() == True else control.lang(32066))
        unwatchedMenu = (control.lang(32069) if trakt.getTraktIndicatorsInfo() == True else control.lang(32067))
        queueMenu = control.lang(32065)
        traktManagerMenu = control.lang(32070)
        labelMenu = control.lang(32055)
        playRandom = control.lang(32535)
        addToLibrary = control.lang(32551)
        infoMenu = control.lang(32101)
        generate_short_path = control.setting("generate_short_path") == "true"

        addSortMethod(syshandle, sortMethod=SORT_METHOD_UNSORTED, labelMask="%L", label2Mask="%Y")

        unpremiered_color = control.setting("unpremiered_color")
        if unpremiered_color == "inny":
            unpremiered_color = control.setting("unpremiered_custom_color")
        else:
            colors_map = {
                "szary": "gray",
                "czerwony": "red",
                "fioletowy": "magenta",
                "pomarańczowy": "orange",
                }
            unpremiered_color = colors_map[unpremiered_color]
        # fflog(f'{unpremiered_color=}')

        #counter = 1
        for i in items:
            try:
                # log_utils.fflog(f'{i=}')
                # fflog(f'i={json.dumps(i, indent=2)}',1,1)

                label = i.get("title")
                if not label:
                    label = "{} {}".format(labelMenu, i["season"])

                syslabel = quote_plus(label)

                systitle = quote_plus(i["tvshowtitle"])
                syslocaltitle = quote_plus(i.get("localtvshowtitle", ""))

                poster = (i["poster"] if "poster" in i and not i["poster"] == "0" else addonPoster)

                fanart = (i["fanart"] if "fanart" in i and not i["fanart"] == "0" else addonFanart)

                banner1 = i.get("banner", "")
                # banner = banner1 or fanart or addonBanner
                banner = banner1 or addonBanner

                if "landscape" in i and not i["landscape"] == "0":
                    landscape = i["landscape"]
                else:
                    landscape = fanart

                imdb, tvdb, tmdb, year, season, duration, status = (
                    i["imdb"], i["tvdb"], i["tmdb"], i["year"], i["season"], i.get("duration", "45"), i.get("status", "0")
                )

                ep_meta = {
                    "poster": poster,
                    "fanart": fanart,
                    "banner": banner,
                    "clearlogo": i.get("clearlogo", "0"),
                    "clearart": i.get("clearart", "0"),
                    "keyart": i.get("keyart", "0"),
                    "characterart": i.get("characterart", "0"),
                    "landscape": landscape,
                    "duration": duration,
                    "status": status,
                    "mpaa": i.get("mpaa", ""),
                }

                sysmeta = quote_plus(json.dumps(ep_meta))
                # log_utils.log('sysmeta: ' + str(sysmeta))

                meta = {k: v for k, v in i.items() if not v == "0"}

                meta.update({"title": i.get("title") or label})

                meta.update({"mediatype": "season"})

                meta.update({"season": season})  # potrzebne dla sezonów o numerze 0

                meta.update({"imdbnumber": imdb, "code": tmdb})

                # meta.update({"trailer": "%s?action=%s&name=%s&tmdb=%s&season=%s" % (sysaddon, trailerAction, systitle, tmdb, season)})
                meta.update({"trailer": "%s?action=trailer&name=%s&url=%s" % (sysaddon, systitle + " " + syslabel, quote_plus(meta.get("trailer") or ""))})

                if not "duration" in meta:
                    # meta.update({"duration": "45"})
                    # meta.update({"duration": "1"})
                    pass
                elif meta["duration"] == "0":
                    # meta.update({"duration": "45"})
                    # meta.update({"duration": "1"})
                    pass
                try:
                    if meta.get("duration") and meta.get("duration") != "0":
                        meta.update({"duration": str(int(meta["duration"]) * 60)})
                except Exception:
                    pass

                # try: meta.update({"genre": cleangenre.lang(meta["genre"], self.lang)})
                # except: pass

                try:
                    seasonYear = i["premiered"]
                    seasonYear = re.findall(r"(\d{4})", seasonYear)[0]
                    # seasonYear = six.ensure_str(seasonYear)
                    meta.update({"tvshowyear": i["year"]})
                    meta.update({"year": seasonYear})
                except Exception:
                    pass

                meta.update({"originalname": i.get("originaltvshowtitle", "")})

                episodes = i.get("episodes") or 0

                if True:
                    try:
                        overlay = int(playcount.getSeasonOverlay(indicators, imdb, season, episodes))
                        if overlay == 7:
                            meta.update({"playcount": 1, "overlay": 7})
                        else:
                            meta.update({"playcount": 0, "overlay": 6})
                    except Exception:
                        fflog_exc(1)
                        pass

                meta.pop("next", None)

                # bulding context menu
                cm = [(playRandom, "RunPlugin(%s?action=random&rtype=episode&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&season=%s)" % (
                                    sysaddon, quote_plus(systitle), quote_plus(year), quote_plus(imdb), quote_plus(tmdb), quote_plus(season),),), 
                      (queueMenu, "RunPlugin(%s?action=queueItem)" % sysaddon),
                     ]

                if True:
                    cm.append((watchedMenu,   "RunPlugin(%s?action=tvPlaycount&name=%s&imdb=%s&tmdb=%s&season=%s&query=7)" % (sysaddon, systitle, imdb, tmdb, season),))
                    cm.append((unwatchedMenu, "RunPlugin(%s?action=tvPlaycount&name=%s&imdb=%s&tmdb=%s&season=%s&query=6)" % (sysaddon, systitle, imdb, tmdb, season),))

                if traktCredentials:
                    cm.append((traktManagerMenu, "RunPlugin(%s?action=traktManager&name=%s&tmdb=%s&content=tvshow)" % (sysaddon, systitle, tmdb),))

                if isOld:
                    cm.append((infoMenu, "Action(Info)"))

                cm.append((addToLibrary,
                           "RunPlugin(%s?action=tvshowToLibrary&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&localtvshowtitle=%s)" % (
                           sysaddon, systitle, year, imdb, tmdb, syslocaltitle),))

                if generate_short_path:
                    cm.append(("[I]przygotuj do ulubionych[/I]", "Container.Update(%s?action=prepareItemForAddToLibrary)" % (sysaddon),))


                try:
                    if i["unaired"] == "true":
                        label = f"[COLOR {unpremiered_color}][I]%s[/I][/COLOR]" % label
                except:
                    pass


                # create ListItem
                try:
                    item = control.item(label=label, offscreen=True)  # dlaczego tak? przecież to ma być wyświetlane! chyba tego nierozumiem
                except Exception:
                    item = control.item(label=label)

                item.addContextMenuItems(cm)


                art = {}

                art.update({
                            "icon": poster, 
                            "thumb": poster, 
                            "poster": poster, 
                            "season.poster": poster,  # zależy od skórki (jak ma kod napisany
                            # "tvshow.poster": poster,  # niektóre mogą pewnie i tego wymagać
                            "banner": banner, 
                            "landscape": landscape, 
                          })

                if settingFanart == "true":
                    art.update({"fanart": fanart})
                elif not addonFanart is None:
                    art.update({"fanart": addonFanart})

                if "clearlogo" in i and not i["clearlogo"] == "0":
                    art.update({"clearlogo": i["clearlogo"]})
                    art.update({"tvshow.clearlogo": i["clearlogo"]})  # to jest ważniejsze dla skórki (tak są tam przeważnie zapisane warunki sprawdzające) - sprawdzane po kolei od góry i zatrzymanie się na którymś
                    pass

                if "clearart" in i and not i["clearart"] == "0":
                    art.update({"clearart": i["clearart"]})

                if "keyart" in i and not i["keyart"] == "0":
                    art.update({"keyart": i["keyart"]})

                """
                if "characterart" in i and not i["characterart"] == "0":
                    art.update({"characterart": i["characterart"]})
                """
                # if has("characterart"):
                if "characterart" in i and not i["characterart"] == "0":
                    characterart = i["characterart"]
                    if isinstance(characterart, list):
                        for an in range(0, len(characterart)):
                            # art[f"characterart{an+1}"] = characterart[an]
                            art.update({f"characterart{an+1}": characterart[an]})
                            # art.update({f"tvshow.characterart{an+1}": characterart[an]})
                    else:
                        # art["characterart"] = characterart
                        art.update({"characterart": characterart})
                        # art.update({"tvshow.characterart": characterart})


                item.setArt(art)


                castwiththumb = i.get("castwiththumb")
                if castwiththumb and not castwiththumb == "0":
                    item.setCast(castwiththumb)
                    pass


                # fflog(f'{control.metadataClean(meta)=}')

                item.setInfo(type="video", infoLabels=control.metadataClean(meta))


                # korekta pod standard ListItem (bo super_info.py inaczej generuje)
                item.setInfo(type="Video", infoLabels={'TvShowTitle': meta.get("localtvshowtitle") or meta.get("tvshowtitle", "")})
                item.setProperty("englishTvShowTitle", meta.get("englishtvshowtitle") or meta.get("tvshowtitle", ""))
                #item.setProperty("OriginalTvShowTitle", meta.get("originaltvshowtitle") or meta.get("tvshowtitle", ""))
                item.setProperty("OriginalTvShowTitle", meta.get("originaltvshowtitle") or "")
                item.setProperty("TvShowYear", meta.get("tvshowyear") or meta.get("year", ""))


                if generate_short_path:
                    # fflog(f'{imdb=} {tmdb=} {tvdb=}')
                    try:
                        vtag = item.getVideoInfoTag()
                        vtag.setUniqueIDs({
                            'imdb': imdb,
                            'tmdb' : tmdb,
                            'tvdb' : tvdb,
                        })
                    except Exception:
                        fflog_exc(1)
                        item.setProperty("imdb_id", imdb)
                        item.setProperty("tmdb_id", tmdb)
                        item.setProperty("tmdb_id", tvdb)

                    item.setProperty("meta", json.dumps(ep_meta))


                url = "%s?action=episodes&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&meta=%s&season=%s" % (sysaddon, systitle, year, imdb, tmdb, tvdb, sysmeta, season)
                if generate_short_path:
                    item.setProperty("fullpath", url)
                    url = "{}?action=episodes&item={}".format(sysaddon, i["season"])


                # video_streaminfo = {"codec": "h264"}; item.addStreamInfo("video", video_streaminfo)  # czy to konieczne?


                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)

                #counter += 1
            except Exception:
                log_utils.log("season-dir Exception", "indexer")
                fflog_exc(1)
                pass

        # ciekawe do czego to służy
        try:
            # control.property(syshandle, "showplot", items[0]["plot"])  # ale to powoduje, że każdy sezon ma ten sam opis
            pass
        except Exception:
            fflog_exc(1)
            pass

        params = dict(parse_qsl(sys.argv[2][1:]))
        updateListing = True if params.get("r") else False  # True świadczy, że po drodze było odświeżanie

        control.content(syshandle, "seasons")
        control.directory(syshandle, cacheToDisc=True, updateListing=updateListing)
        views.setView("seasons")



class episodes:
    def __init__(self):
        # fflog("inicjalizacja klasy episodes")

        # fix for not always current value
        global params, action
        params = dict(parse_qsl(sys.argv[2].replace("?", ""))) if len(sys.argv) > 1 else dict()
        action = params.get("action")

        self.session = requests.Session()

        self.list = []

        self.trakt_link = "https://api.trakt.tv"
        self.tvmaze_link = "https://api.tvmaze.com"

        self.datetime = datetime.datetime.utcnow()  # - datetime.timedelta(hours = 5)
        self.systime = self.datetime.strftime("%Y%m%d%H%M%S%f")
        self.today_date = self.datetime.strftime("%Y-%m-%d")

        self.tm_user = control.setting("tm.user") or apis.tmdb_API
        self.trakt_user = control.setting("trakt.user").strip()
        self.showunaired = control.setting("showunaired") or "true"
        # self.specials = "false"
        self.specials =  control.setting('tv.specials')
        self.lang = control.apiLanguage()["tmdb"] or "en"
        # self.hq_artwork = "false"
        self.fanartTV_artwork = control.setting("fanartTV_artwork")
        self.items_per_page = str(control.setting("items.per.page")) or "20"
        # self.trailer_source = "1"
        self.trailer_source = control.setting('trailer.source')

        # tmdb
        self.tmdb_season_link = ("https://api.themoviedb.org/3/tv/%s/season/%s?api_key=%s&language=%s&append_to_response=aggregate_credits" % (
                    "%s", "%s", self.tm_user, "%s"))
        self.tmdb_season_lite_link = "https://api.themoviedb.org/3/tv/%s/season/%s?api_key=%s&language=en" % ("%s", "%s", self.tm_user)
        self.tmdb_episode_link = ("https://api.themoviedb.org/3/tv/%s/season/%s/episode/%s?api_key=%s&language=%s&append_to_response=credits" % (
                    "%s", "%s", "%s", self.tm_user, self.lang))
        self.tmdb_episode_link_en = ("https://api.themoviedb.org/3/tv/%s/season/%s/episode/%s?api_key=%s&language=en" % (
                    "%s", "%s", "%s", self.tm_user))
        self.tmdb_by_imdb = "https://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id" % ("%s", self.tm_user)
        self.tm_img_link = "https://image.tmdb.org/t/p/w%s%s"
        self.search_link = "https://api.themoviedb.org/3/search/tv?api_key=%s&language=en-US&query=%s&page=1" % (self.tm_user, "%s")
        self.tmdb_show_lite_link = "https://api.themoviedb.org/3/tv/%s?api_key=%s&language=en" % ("%s", self.tm_user)

        # obrazki z fanartTV
        self.fanart_tv_art_link = "http://webservice.fanart.tv/v3/tv/%s"
        self.fanart_tv_user = control.setting("fanart.tv.user") or apis.fanarttv_client_key  # user musi swój podać (bo na domyślnym z FF nie działa)
        self.fanart_tv_API_key = control.setting("fanart.tv.dev") or apis.fanarttv_API_key
        self.fanart_tv_headers = {"api-key": self.fanart_tv_API_key, "client-key": self.fanart_tv_user, }

        # tv maze
        self.added_link = "https://api.tvmaze.com/schedule"
        self.calendar_link = "https://api.tvmaze.com/schedule?date=%s"

        # trakt
        # https://api.trakt.tv/calendars/all/shows/date[30]/31 #use this for new episodes?
        # self.mycalendar_link = "https://api.trakt.tv/calendars/my/shows/date[29]/60/"
        self.mycalendar_link = "https://api.trakt.tv/calendars/my/shows/date[30]/31/"  # go back 30 and show all shows aired until tomorrow
        self.trakthistory_link = "https://api.trakt.tv/users/me/history/shows?limit=%s" % self.items_per_page
        self.progress_link = "https://api.trakt.tv/users/me/watched/shows"
        self.hiddenprogress_link = "https://api.trakt.tv/users/hidden/progress_watched?limit=1000&type=show"
        self.onDeck_link = "https://api.trakt.tv/sync/playback/episodes?limit=%s" % self.items_per_page
        self.traktlists_link = "https://api.trakt.tv/users/me/lists"
        self.traktlikedlists_link = "https://api.trakt.tv/users/likes/lists?limit=1000000"
        self.traktlist_link = "https://api.trakt.tv/users/%s/lists/%s/items"


    def __del__(self):
        self.session.close()


    def get(self, tvshowtitle, year, imdb, tmdb, tvdb=None, season=None, episode=None, meta=None, localtvshowtitle="", originaltvshowtitle="", idx=True, create_directory=True,):
        fflog(f'(episodes) {params=}', 1, 1)
        # fflog(f'{season=} {episode=}')
        try:
            if idx:
                if season is None or episode is None:
                    # fflog(f'tu 1')
                    self.list = cache.get(self.tmdb_list, 1, tvshowtitle, year, imdb, tmdb, tvdb, season, meta, localtvshowtitle, originaltvshowtitle)
                    # fflog(f'{len(self.list)=}')
                # elif episode == None:
                # self.list = cache.get(self.tmdb_list, 1, tvshowtitle, year, imdb, tmdb, fanart, duration, status, season)
                # pass
                else:
                    fflog(f'tu 2')  # kiedy to jest wykorzystywane ?
                    self.list = cache.get(self.tmdb_list, 1, tvshowtitle, year, imdb, tmdb, tvdb, season, meta, localtvshowtitle, originaltvshowtitle)
                    # fflog(f'{len(self.list)=}')
                    num = [x for x, y in enumerate(self.list) if y["season"] == str(season) and y["episode"] == str(episode)][-1]
                    # fflog(f'{num=}')
                    self.list = [y for x, y in enumerate(self.list) if x >= num]
                    # fflog(f'{len(self.list)=}')
                if create_directory:
                    # fflog(f'tu 3')
                    self.episodeDirectory(self.list)
                return self.list
            else:
                # fflog(f'tu 4')
                self.list = self.tmdb_list(tvshowtitle, year, imdb, tmdb, tvdb, season, meta, localtvshowtitle=localtvshowtitle, originaltvshowtitle=originaltvshowtitle, lite=True)
                return self.list
        except Exception:
            log_utils.log("episodes_get Exception", "indexer")
            fflog_exc(1)
            pass


    def calendar(self, url, refresh=None):
        # debug
        if not "http" in url: 
            fflog(f'{params=}', fn=True)
            pass
        else:
            if not _is_debugging():
                fflog(f'params={({**params, "url": "*"})}', 1, 1)
                pass
            else:
                fflog(f'params={({**params, "url": url})}', 0)

        force_tvshow_title: bool = False
        #fflog(f'{url=} {refresh=}')
        try:
            #url = re.sub("(?<=api_key=)[^&]*", self.tm_user, url)  # tu nie występuje nic z tmdb
            try:
                url = getattr(self, url + "_link")
            except Exception:
                #fflog_exc(1)
                pass
            #fflog(f'{url=}')
            if self.trakt_link in url and url == self.onDeck_link:
                # self.blist = cache.get(self.trakt_episodes_list, 0, url, self.trakt_user, self.lang)
                self.list = []
                self.list = self.trakt_episodes_list(url, self.trakt_user, self.lang)
                if self.list:
                    self.list = sorted(self.list, key=lambda k: int(k["paused_at"]), reverse=True)

            elif self.trakt_link in url and url == self.progress_link:
                cache_timeout = 0 if refresh else 1
                # self.blist = cache.get(self.trakt_progress_list, 720, url, self.trakt_user, self.lang)
                self.list = cache.get(self.trakt_progress_list, cache_timeout, url, self.trakt_user, self.lang)
                force_tvshow_title = True

            elif self.trakt_link in url and url == self.mycalendar_link:
                # self.blist = cache.get(self.trakt_episodes_list, 720, url, self.trakt_user, self.lang)
                cache_timeout = 0 if refresh else 12
                self.list = []
                self.list = cache.get(self.trakt_episodes_list, cache_timeout, url, self.trakt_user, self.lang)
                if self.list:
                    self.list = sorted(self.list, key=lambda k: k["premiered"], reverse=True)

            elif self.trakt_link in url and url == self.trakthistory_link:
                cache_timeout = 0 if refresh else 1
                self.list = cache.get(self.trakt_episodes_list, cache_timeout, url, self.trakt_user, self.lang)
                if self.list:
                    self.list = sorted(self.list, key=lambda k: int(k["watched_at"]), reverse=True)

            elif self.trakt_link in url and "/users/" in url:
                cache_timeout = 0 if refresh else 1
                self.list = cache.get(self.trakt_list, cache_timeout, url, self.trakt_user)
                if self.list:
                    self.list = self.list[::-1]

            elif self.trakt_link in url:
                cache_timeout = 0 if refresh else 1
                self.list = cache.get(self.trakt_list, cache_timeout, url, self.trakt_user)

            elif self.tvmaze_link in url and url == self.added_link:
                urls = [i["url"] for i in self.calendars(idx=False)][:5]
                self.list = []
                for url in urls:
                    self.list += cache.get(self.tvmaze_list, 720, url, True)

            elif self.tvmaze_link in url:
                self.list = cache.get(self.tvmaze_list, 1, url, False)


            if self.list:
                self.episodeDirectory(self.list, force_tvshow_title=force_tvshow_title)
            else:
                control.infoDialog('Nic nie znaleziono', "Błąd", icon="ERROR")
                control.directory(int(sys.argv[1]), cacheToDisc=False)
                control.execute('Action(Back)')

            return self.list

        except Exception:
            fflog_exc(1)
            pass


    def widget(self):
        if trakt.getTraktIndicatorsInfo():
            setting = control.setting("tv.widget.alt")
        else:
            setting = control.setting("tv.widget")

        if setting == "2":
            self.calendar(self.progress_link)
        elif setting == "3":
            self.calendar(self.mycalendar_link)
        else:
            self.calendar(self.added_link)


    def calendars(self, idx=True):
        m = control.lang(32060).split("|")
        try:
            months = [(m[0], "January"), (m[1], "February"), (m[2], "March"), (m[3], "April"), (m[4], "May"),
                (m[5], "June"), (m[6], "July"), (m[7], "August"), (m[8], "September"), (m[9], "October"),
                (m[10], "November"), (m[11], "December"), ]
        except:
            months = []

        d = control.lang(32061).split("|")
        try:
            days = [(d[0], "Monday"), (d[1], "Tuesday"), (d[2], "Wednesday"), (d[3], "Thursday"), (d[4], "Friday"),
                (d[5], "Saturday"), (d[6], "Sunday"), ]
        except:
            days = []

        for i in range(0, 30):
            try:
                name = self.datetime - datetime.timedelta(days=i)
                name = control.lang(32062) % (name.strftime("%A"), six.ensure_str(name.strftime("%d %B")),)
                for m in months:
                    name = name.replace(m[1], m[0])
                for d in days:
                    name = name.replace(d[1], d[0])
                # try: name = six.ensure_str(name)
                # except: pass

                url = self.calendar_link % (self.datetime - datetime.timedelta(days=i)).strftime("%Y-%m-%d")

                self.list.append({"name": name, "url": url, "action": "calendar", "image": "calendar.png",})
            except:
                pass
        if idx:
            self.addDirectory(self.list)
        return self.list


    def userlists(self):
        """ tylko listy trakt """
        fflog(f'{params=}', 1, 1)
        try:
            userlists = []
            if not trakt.getTraktCredentialsInfo():
                raise Exception()
            activity = trakt.getActivity()
            #fflog(f'{activity=}')
        except Exception:
            fflog_exc(1)
            pass

        try:
            if not trakt.getTraktCredentialsInfo():
                raise Exception()
            try:
                if activity > cache.timeout(self.trakt_user_list, self.traktlists_link, self.trakt_user):
                    raise Exception()
                #fflog(f'z cache')
                userlists += cache.get(self.trakt_user_list, 720, self.traktlists_link, self.trakt_user)
            except:
                #fflog(f'odświeżam')
                userlists += cache.get(self.trakt_user_list, 0, self.traktlists_link, self.trakt_user)
        except Exception:
            #fflog_exc(1)
            pass

        try:
            self.list = []
            if not trakt.getTraktCredentialsInfo():
                raise Exception()
            try:
                if activity > cache.timeout(self.trakt_user_list, self.traktlikedlists_link, self.trakt_user):
                    raise Exception()
                #fflog(f'z cache')
                userlists += cache.get(self.trakt_user_list, 720, self.traktlikedlists_link, self.trakt_user, )
            except:
                #fflog(f'odświeżam')
                userlists += cache.get(self.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)
        except Exception:
            #fflog_exc(1)
            pass

        self.list = userlists
        for i in range(0, len(self.list)):
            self.list[i].update({
                "action": "calendar",
                # "image": "userlists.png",
                "image": "trakt.png",
                })
        self.addDirectory(self.list, queue=True, add_refresh=True)
        return self.list


    def trakt_list(self, url, user):
        try:
            #fflog(f'{url=}')
            for i in re.findall(r"date\[(\d+)]", url):
                url = url.replace("date[%s]" % i, (self.datetime - datetime.timedelta(days=int(i))).strftime("%Y-%m-%d"), )

            q = dict(parse_qsl(urlsplit(url).query))
            q.update({"extended": "full"})
            q = (urlencode(q)).replace("%2C", ",")
            u = url.replace("?" + urlparse(url).query, "") + "?" + q
            # fflog(f'{u=}')
            itemlist = []
            items = trakt.getTraktAsJson(u)
        except Exception:
            fflog_exc(1)
            # print("Unexpected error in info builder script:", sys.exc_info()[0])
            # exc_type, exc_obj, exc_tb = sys.exc_info()
            # print(exc_type, exc_tb.tb_lineno)
            log_utils.log("trakt_list0", "indexer")
            return

        localtvshowtitles = {}

        # fflog(f'{len(items)=}')
        for item in items:
            try:
                # fflog(f'{item=}')
                if not item.get("episode"):
                    #raise Exception()
                    continue              

                title = item["episode"]["title"]
                if title is None or title == "":
                    #raise Exception()
                    continue
                title = client.replaceHTMLCodes(title)

                season = item["episode"]["season"]
                season = re.sub("[^0-9]", "", "%01d" % int(season))
                if season == "0" and self.specials != "true":
                    #raise Exception()
                    continue

                episode = item["episode"]["number"]
                episode = re.sub("[^0-9]", "", "%01d" % int(episode))
                if episode == "0":
                    #raise Exception()
                    continue

                tvshowtitle = item["show"]["title"]
                if not tvshowtitle:
                    #raise Exception()
                    continue
                else:
                    tvshowtitle = client.replaceHTMLCodes(six.ensure_str(tvshowtitle))

                year = item["show"]["year"]
                year = re.sub("[^0-9]", "", str(year))

                imdb = item["show"]["ids"].get("imdb")
                if imdb is None or imdb == "":
                    imdb = "0"
                else:
                    imdb = "tt" + re.sub("[^0-9]", "", str(imdb))

                tvdb = item["show"]["ids"].get("tvdb")
                if not tvdb:
                    tvdb == "0"
                tvdb = re.sub("[^0-9]", "", str(tvdb))

                tmdb = item["show"]["ids"]["tmdb"]
                if not tmdb:
                    #raise Exception()
                    continue
                tmdb = str(tmdb)

                premiered = item["episode"].get("first_aired")
                try:
                    premiered = re.compile(r"(\d{4}-\d{2}-\d{2})").findall(premiered)[0]
                except:
                    premiered = "0"

                studio = item["show"].get("network")
                if not studio:
                    studio = "0"

                genre = item["show"].get("genres")
                genre = [i.title() for i in genre] if genre else []
                if not genre:
                    genre = "0"
                else:
                    genre = " / ".join(genre)

                try:
                    duration = str(item["show"]["runtime"])
                except:
                    duration = ""
                if not duration:
                    duration = "0"

                try:
                    rating = str(item["episode"]["rating"])
                except:
                    rating = "0"
                if rating is None or rating == "0.0":
                    rating = "0"

                try:
                    votes = str(item["episode"]["votes"])
                except:
                    votes = "0"
                try:
                    votes = str(format(int(votes), ",d"))
                except:
                    pass
                if not votes:
                    votes = "0"

                mpaa = item["show"].get("certification")
                if not mpaa:
                    mpaa = "0"

                try:
                    plot = item["episode"]["overview"]
                except:
                    plot = ""
                if not plot:
                    plot = item["show"]["overview"]
                if not plot:
                    plot = "0"
                else:
                    plot = client.replaceHTMLCodes(six.ensure_str(plot, errors="replace"))

                try:
                    paused_at = item.get("paused_at", "0") or "0"
                    paused_at = re.sub("[^0-9]+", "", paused_at)
                except:
                    paused_at = "0"

                try:
                    watched_at = item.get("watched_at", "0") or "0"
                    watched_at = re.sub("[^0-9]+", "", watched_at)
                except:
                    watched_at = "0"

                try:
                    if self.lang != "en":
                        # fflog(f'tłumaczenia {imdb=} {season=} {episode=}')
                        trans_item = trakt.getTVShowTranslation(imdb, lang=self.lang, season=season, episode=episode, full=True)
                        # fflog(f'{trans_item=}')
                        if trans_item:
                            title = client.replaceHTMLCodes(six.ensure_str(trans_item.get("title") or "")) or title
                            plot = client.replaceHTMLCodes(six.ensure_str(trans_item.get("overview"), errors="replace")) or plot

                        # fflog(f'ustalenie polskiego tytułu serialu {imdb=}')
                        localtvshowtitle = localtvshowtitles.get(imdb)
                        if not localtvshowtitle:
                            # fflog(f'pobranie polskiego tytułu serialu z internetu {imdb=}')
                            localtvshowtitle = trakt.getTVShowTranslation(imdb, lang=self.lang) or tvshowtitle
                            localtvshowtitles[imdb] = localtvshowtitle
                        # fflog(f'{localtvshowtitle=}')
                except Exception:
                    fflog_exc(1)
                    localtvshowtitle = ""  # ważne
                    pass

                originaltvshowtitle = ""  # szkoda, że trakt nie daje takiej informacji

                itemlist.append(
                    {"title": title, "season": season, "episode": episode, "tvshowtitle": tvshowtitle, "year": year,
                        "premiered": premiered, "status": "Continuing", "studio": studio, "genre": genre,
                        "duration": duration, "rating": rating, "votes": votes, "mpaa": mpaa, "plot": plot,
                        "imdb": imdb, "tvdb": tvdb, "tmdb": tmdb, "poster": "0", "thumb": "0", "paused_at": paused_at,
                        "watched_at": watched_at, "localtvshowtitle": localtvshowtitle,
                        #"originaltvshowtitle": originaltvshowtitle,
                        })
            except Exception:
                fflog_exc(1)
                log_utils.log("trakt_list1", "indexer")
                pass

        itemlist = itemlist[::-1]
        return itemlist


    def trakt_progress_list(self, url, user, lang):
        try:
            url += "?extended=full"
            result = trakt.getTraktAsJson(url)
            # log_utils.log('prog_res: ' + str(result))
            items = []
        except:
            return

        sortorder = control.setting("prgr.sortorder")
        for item in result:
            try:
                num_1 = 0
                for i in range(0, len(item["seasons"])):
                    if item["seasons"][i]["number"] > 0:
                        num_1 += len(item["seasons"][i]["episodes"])
                num_2 = int(item["show"]["aired_episodes"])
                if num_1 >= num_2:
                    # raise Exception()
                    continue

                season = str(item["seasons"][-1]["number"])

                episode = [x for x in item["seasons"][-1]["episodes"] if "number" in x]
                episode = sorted(episode, key=lambda x: x["number"])
                episode = str(episode[-1]["number"])

                tvshowtitle = item["show"]["title"]
                if not tvshowtitle:
                    raise Exception()
                    # continue
                else:
                    tvshowtitle = client.replaceHTMLCodes(six.ensure_str(tvshowtitle))

                year = item["show"]["year"]
                year = re.sub("[^0-9]", "", str(year))
                if int(year) > int(self.datetime.strftime("%Y")):  # co to za warunek ?
                    # raise Exception()
                    continue

                imdb = item["show"]["ids"].get("imdb")
                if not imdb:
                    imdb = "0"

                tvdb = item["show"]["ids"].get("tvdb")
                if not tvdb:
                    tvdb = "0"
                else:
                    tvdb = re.sub("[^0-9]", "", str(tvdb))

                tmdb = item["show"]["ids"].get("tmdb")
                if not tmdb:
                    tmdb = "0"
                else:
                    tmdb = str(tmdb)

                studio = item.get("show").get("network", "0")
                if not studio:
                    studio = "0"

                duration = item["show"].get("runtime")
                if not duration:
                    duration = "0"

                mpaa = item["show"].get("certification")
                if not mpaa:
                    mpaa = "0"

                status = item["show"].get("status")
                if not status:
                    status = "0"

                genre = item["show"].get("genres")
                if not genre:
                    genre = "0"
                else:
                    genre = " / ".join(genre)

                last_watched = item.get("last_watched_at")
                if last_watched is None or last_watched == "":
                    last_watched = "0"

                if self.lang != "en":
                    localtvshowtitle = trakt.getTVShowTranslation(imdb, lang=self.lang) or tvshowtitle

                items.append({"imdb": imdb, "tvdb": tvdb, "tmdb": tmdb, "tvshowtitle": tvshowtitle, "year": year,
                    "studio": studio, "duration": duration, "mpaa": mpaa, "status": status, "genre": genre,
                    "snum": season, "enum": episode, "_last_watched": last_watched, "localtvshowtitle": localtvshowtitle, })
            except Exception:
                fflog_exc(1)
                pass

        try:
            result = trakt.getTraktAsJson(self.hiddenprogress_link)
            # log_utils.log('hid_prog_res: ' + str(result))
            result = [str(i["show"]["ids"]["tmdb"]) for i in result]

            items = [i for i in items if not i["tmdb"] in result]
        except Exception:
            log_utils.log("Trakt Progress List 1", "indexer")
            fflog_exc(1)
            pass


        def items_list(i, arts_from_fanarttv=None, meta_from_tmdb=None):

            tmdb, imdb, tvdb = i.get("tmdb"), i.get("imdb"), i.get("tvdb")
            if (not tmdb or tmdb == "0") and not imdb == "0":
                try:
                    url = self.tmdb_by_imdb % imdb
                    result = self.session.get(url, timeout=16).json()
                    tmdb_result = result["tv_results"][0]
                    tmdb = tmdb_result.get("id")
                    if not tmdb:
                        tmdb = "0"
                    else:
                        tmdb = str(tmdb)
                except Exception:
                    tmdb = "0"  # dać czy nie ?
                    pass

            # try:
            # item = [x for x in self.blist if x['tmdb'] == tmdb and x['snum'] == i['snum'] and x['enum'] == i['enum']][0]
            # item['action'] = 'episodes'
            # self.list.append(item)
            # return
            # except:
            # pass

            try:
                if tmdb == "0":
                    raise Exception()

                _episode = str(int(i["enum"]) + 1)
                _season = str(int(i["snum"]) + 1)

                url = self.tmdb_episode_link % (tmdb, i["snum"], _episode)
                r = self.session.get(url, timeout=10)
                if r.json().get("status_code") == 34:
                    url2 = self.tmdb_episode_link % (tmdb, _season, "1")
                    r = self.session.get(url2, timeout=10)
                r.raise_for_status()
                r.encoding = "utf-8"
                item = r.json()  # if six.PY3 else utils.json_loads_as_str(r.text)

                try:
                    premiered = item["air_date"]
                except:
                    premiered = ""
                if not premiered:
                    premiered = "0"

                unaired = ""
                if i.get("status") == "Ended":
                    pass
                elif premiered == "0":
                    raise Exception()
                elif int(re.sub(r"[^0-9]", "", str(premiered))) > int(re.sub(r"[^0-9]", "", str(self.today_date))):
                    unaired = "true"
                    if self.showunaired != "true":
                        raise Exception()

                title = item["name"]
                if not title:
                    title = "0"

                season = str(item["season_number"])
                # season = '%01d' % season
                if int(season) == 0 and self.specials != 'true':
                    raise Exception()

                episode = item["episode_number"]
                episode = "%01d" % episode

                tvshowtitle = i["tvshowtitle"]
                localtvshowtitle = i.get("localtvshowtitle", "")

                year = i["year"]

                try:
                    still_path = item["still_path"]
                except:
                    still_path = ""
                if not still_path:
                    thumb = "0"
                else:
                    thumb = self.tm_img_link % ("1280", still_path)

                try:
                    rating = str(item["vote_average"])
                except:
                    rating = ""
                if not rating:
                    rating = "0"

                try:
                    votes = str(item["vote_count"])
                except:
                    votes = ""
                if not votes:
                    votes = "0"

                try:
                    plot = item["overview"]
                except:
                    plot = ""
                if not plot:
                    url_en = self.tmdb_episode_link_en % (tmdb, i["snum"], _episode)
                    r_en = self.session.get(url_en, timeout=10)
                    if r_en.json().get("status_code") == 34:
                        url2_en = self.tmdb_episode_link_en % (tmdb, _season, "1")
                        r_en = self.session.get(url2_en, timeout=10)
                    r_en.raise_for_status()
                    r_en.encoding = "utf-8"
                    item_en = r_en.json()
                    try:
                        plot = item_en["overview"]
                    except:
                        plot = ""
                    if not plot:
                        plot = "0"

                try:
                    r_crew = item["crew"]
                    director = [d for d in r_crew if d["job"] == "Director"]
                    director = ", ".join([d["name"] for d in director])
                    writer = [w for w in r_crew if w["job"] == "Writer"]
                    writer = ", ".join([w["name"] for w in writer])
                except:
                    director = writer = ""
                if not director:
                    director = "0"
                if not writer:
                    writer = "0"

                castwiththumb = []
                try:
                    r_cast = item["credits"]["cast"][:30]
                    for person in r_cast:
                        _icon = person["profile_path"]
                        icon = self.tm_img_link % ("185", _icon) if _icon else ""
                        castwiththumb.append({"name": person["name"], "role": person["character"], "thumbnail": icon, })
                except:
                    pass
                if not castwiththumb:
                    castwiththumb = "0"

                poster = poster2 = fanart = fanart2 = landscape = landscape2 = clearlogo = clearart = keyart = banner = banner2 = characterart= "0"

                if meta_from_tmdb:
                    poster = meta_from_tmdb.get( (imdb, tmdb) ).get("poster") or "0"
                    poster2 = meta_from_tmdb.get( (imdb, tmdb) ).get("seasons_posters") or "0"
                    fanart = meta_from_tmdb.get( (imdb, tmdb) ).get("fanart") or "0"
                    fanart2 = meta_from_tmdb.get( (imdb, tmdb) ).get("seasons_fanarts") or "0"
                    landscape = meta_from_tmdb.get( (imdb, tmdb) ).get("landscape") or "0"
                    landscape2 = meta_from_tmdb.get( (imdb, tmdb) ).get("seasons_landscapes") or "0"
                    clearlogo = meta_from_tmdb.get( (imdb, tmdb) ).get("clearlogo") or "0"
                    clearart = meta_from_tmdb.get( (imdb, tmdb) ).get("clearart") or "0"
                    keyart = meta_from_tmdb.get( (imdb, tmdb) ).get("keyart") or "0"
                    banner = meta_from_tmdb.get( (imdb, tmdb) ).get("banner") or "0"
                    banner2 = meta_from_tmdb.get( (imdb, tmdb) ).get("seasons_banners") or "0"
                    characterart = meta_from_tmdb.get( (imdb, tmdb) ).get("characterart") or "0"

                    if isinstance(poster2, dict):
                        poster2 = poster2.get(season)
                    if isinstance(fanart2, dict):
                        fanart2 = fanart2.get(season)
                    if isinstance(landscape2, dict):
                        landscape2 = landscape2.get(season)
                    if isinstance(banner2, dict):
                        banner2 = banner2.get(season)

                """
                # fflog(f'{tvdb=}')
                if not tvdb == "0":
                    if self.fanartTV_artwork == "true":
                        # fflog('pobranie grafik z fanart_tv_art')
                        # (poster, poster2, fanart, banner, landscape, clearlogo, clearart,) = self.fanart_tv_art(tvdb)  # wyniosłem poza pętlę
                        try:
                            # fflog(f'próba pozyskania grafiki z FanartTV {tvdb=} {season=} {episode=}')
                            poster, poster2, fanart, banner, landscape, clearlogo, clearart, banner2, landscape2 = arts_from_fanarttv.get(tvdb)
                            if isinstance(poster2, dict):
                                poster2 = poster2.get(season)
                            if isinstance(banner2, dict):
                                banner2 = banner2.get(season)
                            if isinstance(landscape2, dict):
                                landscape2 = landscape2.get(season)
                            # fflog(f'Fanart TV zwrócił, co mógł')
                        except Exception:
                            fflog_exc(1)
                            pass
                else:
                    pass
                """
                """
                if (not poster or poster == "0") and arts_from_tmdb:
                    poster = arts_from_tmdb.get( (tmdb, season) )
                    poster = self.tm_img_link % ("500", poster) if poster else "0"
                    # fflog(f'{poster=} {tmdb=} {season=}')
                """
                if (not poster or poster == "0") and meta_from_tmdb:
                    seasons_posters = meta_from_tmdb.get( (imdb, tmdb) ).get("seasons_posters") or {}
                    poster = seasons_posters.get(season) or "0"
                    # fflog(f'{poster=} {tmdb=} {season=}')

                #if (not poster or poster == "0") and meta_from_tmdb:
                if meta_from_tmdb:
                    tvshow_poster = meta_from_tmdb.get( (imdb, tmdb) ).get("poster")
                    # fflog(f'{tvshow_poster=} {imdb=} {tmdb=}')
                    if (not poster or poster == "0"):
                        poster = tvshow_poster if tvshow_poster and tvshow_poster != "0" else "0"
                    # fflog(f'{poster=} {imdb=} {tmdb=}')
                else:
                    tvshow_poster = "0"

                if poster2 and poster2 != "0":
                    poster = poster2

                if banner2 and banner2 != "0":
                    banner = banner2
                if landscape2 and landscape2 != "0":
                    landscape = landscape2

                if fanart2 and fanart2 != "0":
                    fanart = fanart2

                if (not fanart or fanart == "0") and meta_from_tmdb:
                    fanart = meta_from_tmdb.get( (imdb, tmdb) ).get("fanart") or "0"
                    # fanart = self.tm_img_link % ("1280", fanart) if fanart else "0"
                    # fanart = fanart if fanart else "0"
                    # fflog(f'{fanart=} {imdb=} {tmdb=}')

                if (not landscape or landscape == "0") and meta_from_tmdb:
                    landscape = meta_from_tmdb.get( (imdb, tmdb) ).get("landscape") or "0"
                    # landscape = self.tm_img_link % ("1280", landscape) if landscape else "0"
                    # landscape = landscape if landscape else "0"
                    # fflog(f'{landscape=} {imdb=} {tmdb=}')

                if (not clearlogo or clearlogo == "0") and meta_from_tmdb:
                    clearlogo = meta_from_tmdb.get( (imdb, tmdb) ).get("clearlogo") or "0"
                    # fflog(f'{clearlogo=} {imdb=} {tmdb=}')

                # fflog(f'{poster=} {fanart=} {banner=} {landscape=} {clearlogo=} {clearart=}')

                self.list.append(
                    {"title": title, "season": season, "episode": episode, "tvshowtitle": tvshowtitle, "year": year,
                        "premiered": premiered, "studio": i.get("studio", ""), "genre": i.get("genre", ""),
                        "status": i.get("status"), "duration": i.get("duration", ""), "rating": rating, "votes": votes,
                        "mpaa": i.get("mpaa", ""), "director": director, "writer": writer, "castwiththumb": castwiththumb,
                        "plot": plot, "poster": poster, "banner": banner, "fanart": fanart, "thumb": thumb,
                        "clearlogo": clearlogo, "clearart": clearart, "landscape": landscape, "snum": i["snum"],
                        "enum": i["enum"], "action": "episodes", "unaired": unaired,
                        "_last_watched": i["_last_watched"], "imdb": imdb, "tvdb": tvdb, "tmdb": tmdb,
                        "_sort_key": max(i["_last_watched"], premiered), "localtvshowtitle": localtvshowtitle,
                        "tvshow.poster": tvshow_poster,
                        "keyart": keyart, "characterart": characterart,
                    })
            except:
                log_utils.log("trakt_progress_list", "indexer")
                pass

        items = items[:50]

        arts_from_fanarttv = {}
        """
        tvdb_list = list(set((i["tvdb"]) for i in items if i["tvdb"]!="0"))
        if self.fanartTV_artwork == "true":
            for tvdb in tvdb_list:
                arts = self.fanart_tv_art(tvdb)
                arts_from_fanarttv.update({tvdb: arts})
        # fflog(f'{len(arts_from_fanarttv)=}  {arts_from_fanarttv=}')
        """

        meta_from_tmdb = {}
        tmdb_list = list(set((i["imdb"], i["tmdb"]) for i in items))
        # fflog(f'{tmdb_list=}')
        for imdb, tmdb in tmdb_list:
            meta = self.get_meta_for_tvshow(imdb, tmdb)
            meta_from_tmdb[imdb, tmdb] = {k:v for k,v in meta.items() 
                                          # if k in ["poster", "landscape", "fanart", "seasons_posters", "clearlogo"]
                                          if k in [ "poster",
                                                    "seasons_posters",
                                                    "fanart",
                                                    "seasons_fanarts",
                                                    "landscape",
                                                    "seasons_landscapes",
                                                    "clearlogo",
                                                    "clearart",
                                                    "keyart",
                                                    "banner",
                                                    "seasons_banners",
                                                    "characterart",
                                                  ]
                                         }
        # fflog(f'{len(meta_from_tmdb)=}  {meta_from_tmdb=}')
        meta = None

        threads = []
        import threading

        for i in items:
            threads.append(threading.Thread(target=items_list, args=(i, arts_from_fanarttv, meta_from_tmdb,)))  # asynchronicznie
        [i.start() for i in threads]
        [i.join() for i in threads]

        try:
            if sortorder == "0":
                self.list = sorted(self.list, key=lambda k: k["premiered"], reverse=True)
            else:
                self.list = sorted(self.list, key=lambda k: k["_sort_key"], reverse=True)
        except Exception:
            fflog_exc(1)
            pass

        return self.list


    def trakt_episodes_list(self, url, user, lang):
        # fflog(f'{url=}')
        items = self.trakt_list(url, user)
        # fflog(f'{len(items)=}  {items=}')

        def items_list(i, arts_from_fanarttv=None, arts_from_tmdb=None, meta_from_tmdb=None):

            tmdb, imdb, tvdb = i.get("tmdb"), i.get("imdb"), i.get("tvdb")
            if (not tmdb or tmdb == "0") and not imdb == "0":
                try:
                    url = self.tmdb_by_imdb % imdb
                    # control.log(f'[trakt_episodes_list] {url=}', 1)
                    result = self.session.get(url, timeout=16).json()
                    tmdb_result = result["tv_results"][0]
                    tmdb = tmdb_result.get("id")
                    if not tmdb:
                        tmdb = "0"
                    else:
                        tmdb = str(tmdb)
                except Exception:
                    tmdb = "0"
                    fflog_exc(1)
                    pass

            # try:
                # item = [x for x in self.blist if x['tmdb'] == tmdb and x['season'] == i['season'] and x['episode'] == i['episode']][0]
                # if item['poster'] == '0': raise Exception()
                # self.list.append(item)
                # return
            # except Exception:
                # pass

            try:
                if tmdb == "0":
                    raise Exception()

                # if i['season'] == '0': raise Exception()
                if True:
                    url = self.tmdb_episode_link % (tmdb, i["season"], i["episode"])
                    # control.log(f'[trakt_episodes_list] {url=}', 1)
                    r = self.session.get(url, timeout=16)
                    r.encoding = "utf-8"
                    item = r.json()  # if six.PY3 else utils.json_loads_as_str(r.text)
                else:
                    item = i

                title = item.get("name", "")
                if not title:
                    title = "0"

                season = str(item["season_number"])
                # season = '%01d' % season
                if int(season) == 0 and self.specials != 'true':
                    raise Exception()

                episode = str(item["episode_number"])
                # episode = '%01d' % episode

                tvshowtitle = i["tvshowtitle"]
                localtvshowtitle = i.get("localtvshowtitle", "")

                premiered = i.get("premiered")

                status, duration, mpaa, studio, genre, year = (
                    i.get("status"), i.get("duration"), i.get("mpaa"), i.get("studio"), i.get("genre"), i.get("year"),)

                rating, votes = i.get("rating"), i.get("votes")

                try:
                    still_path = item["still_path"]  # stopklatka (miniatura) odcinka
                except:
                    still_path = ""
                if not still_path:
                    thumb = "0"
                else:
                    thumb = self.tm_img_link % ("1280", still_path)

                try:
                    plot = item["overview"]  # z tmdb
                except:
                    plot = ""
                if not plot:
                    plot = i["plot"]  # z trakt

                try:
                    r_crew = item["crew"]
                    director = [d for d in r_crew if d["job"] == "Director"]
                    director = ", ".join([d["name"] for d in director])
                    writer = [w for w in r_crew if w["job"] == "Writer"]
                    writer = ", ".join([w["name"] for w in writer])
                except:
                    director = writer = ""
                if not director:
                    director = "0"
                if not writer:
                    writer = "0"

                castwiththumb = []
                try:
                    r_cast = item["credits"]["cast"][:30]
                    for person in r_cast:
                        _icon = person["profile_path"]
                        icon = self.tm_img_link % ("185", _icon) if _icon else ""
                        castwiththumb.append({"name": person["name"], "role": person["character"], "thumbnail": icon, })
                except:
                    pass
                if not castwiththumb:
                    castwiththumb = "0"

                paused_at = i.get("paused_at", "0") or "0"

                watched_at = i.get("watched_at", "0") or "0"

                poster = poster2 = fanart = fanart2 = landscape = landscape2 = clearlogo = clearart = keyart = banner = banner2 = characterart= "0"

                if meta_from_tmdb:
                    poster = meta_from_tmdb.get( (imdb, tmdb) ).get("poster") or "0"
                    poster2 = meta_from_tmdb.get( (imdb, tmdb) ).get("seasons_posters") or "0"
                    fanart = meta_from_tmdb.get( (imdb, tmdb) ).get("fanart") or "0"
                    fanart2 = meta_from_tmdb.get( (imdb, tmdb) ).get("seasons_fanarts") or "0"
                    landscape = meta_from_tmdb.get( (imdb, tmdb) ).get("landscape") or "0"
                    landscape2 = meta_from_tmdb.get( (imdb, tmdb) ).get("seasons_landscapes") or "0"
                    clearlogo = meta_from_tmdb.get( (imdb, tmdb) ).get("clearlogo") or "0"
                    clearart = meta_from_tmdb.get( (imdb, tmdb) ).get("clearart") or "0"
                    keyart = meta_from_tmdb.get( (imdb, tmdb) ).get("keyart") or "0"
                    banner = meta_from_tmdb.get( (imdb, tmdb) ).get("banner") or "0"
                    banner2 = meta_from_tmdb.get( (imdb, tmdb) ).get("seasons_banners") or "0"
                    characterart = meta_from_tmdb.get( (imdb, tmdb) ).get("characterart") or "0"

                    if isinstance(poster2, dict):
                        poster2 = poster2.get(season)
                    if isinstance(fanart2, dict):
                        fanart2 = fanart2.get(season)
                    if isinstance(landscape2, dict):
                        landscape2 = landscape2.get(season)
                    if isinstance(banner2, dict):
                        banner2 = banner2.get(season)

                """
                # fflog(f'{tvdb=}')
                if not tvdb == "0":
                    if self.fanartTV_artwork == "true":
                        # fflog('pobranie grafik z fanart_tv_art')
                        # (poster, poster2, fanart, banner, landscape, clearlogo, clearart, banner2, landscape2) = self.fanart_tv_art(tvdb)  # wyniosłem poza pętlę
                        try:
                            # fflog(f'próba pozyskania grafiki z FanartTV {tvdb=} {season=} {episode=}')
                            poster, poster2, fanart, banner, landscape, clearlogo, clearart, banner2, landscape2 = arts_from_fanarttv.get(tvdb)
                            if isinstance(poster2, dict):
                                poster2 = poster2.get(season)
                            if isinstance(banner2, dict):
                                banner2 = banner2.get(season)
                            if isinstance(landscape2, dict):
                                landscape2 = landscape2.get(season)
                            # fflog(f'Fanart TV zwrócił, co mógł')
                        except Exception:
                            fflog_exc(1)
                            pass
                else:
                    pass
                """
                if (not poster or poster == "0") and arts_from_tmdb:
                    poster = arts_from_tmdb.get( (tmdb, season) )
                    poster = self.tm_img_link % ("500", poster) if poster else "0"
                    # fflog(f'{poster=} {tmdb=} {season=}')

                if (not poster or poster == "0") and meta_from_tmdb:
                    seasons_posters = meta_from_tmdb.get( (imdb, tmdb) ).get("seasons_posters") or {}
                    poster = seasons_posters.get(season) or "0"
                    # fflog(f'{poster=} {tmdb=} {season=}')

                #if (not poster or poster == "0") and meta_from_tmdb:
                if meta_from_tmdb:
                    tvshow_poster = meta_from_tmdb.get( (imdb, tmdb) ).get("poster")
                    # fflog(f'{tvshow_poster=} {imdb=} {tmdb=}')
                    if (not poster or poster == "0"):
                        poster = tvshow_poster if tvshow_poster and tvshow_poster != "0" else "0"
                    # fflog(f'{poster=} {imdb=} {tmdb=}')
                else:
                    tvshow_poster = "0"

                if poster2 and poster2 != "0":
                    poster = poster2

                if banner2 and banner2 != "0":
                    banner = banner2
                if landscape2 and landscape2 != "0":
                    landscape = landscape2

                if fanart2 and fanart2 != "0":
                    fanart = fanart2

                if (not fanart or fanart == "0") and meta_from_tmdb:
                    fanart = meta_from_tmdb.get( (imdb, tmdb) ).get("fanart") or "0"
                    # fanart = self.tm_img_link % ("1280", fanart) if fanart else "0"
                    # fanart = fanart if fanart else "0"
                    # fflog(f'{fanart=} {imdb=} {tmdb=}')

                if (not landscape or landscape == "0") and meta_from_tmdb:
                    landscape = meta_from_tmdb.get( (imdb, tmdb) ).get("landscape") or "0"
                    # landscape = self.tm_img_link % ("1280", landscape) if landscape else "0"
                    # landscape = landscape if landscape else "0"
                    # fflog(f'{landscape=} {imdb=} {tmdb=}')

                if (not clearlogo or clearlogo == "0") and meta_from_tmdb:
                    clearlogo = meta_from_tmdb.get( (imdb, tmdb) ).get("clearlogo") or "0"
                    # fflog(f'{clearlogo=} {imdb=} {tmdb=}')

                # fflog(f'{poster=} {fanart=} {banner=} {landscape=} {clearlogo=} {clearart=}')

                self.list.append(
                    {"title": title, "season": season, "episode": episode, "tvshowtitle": tvshowtitle, "year": year,
                        "premiered": premiered, "status": status, "studio": studio, "genre": genre,
                        "duration": duration, "rating": rating, "votes": votes, "mpaa": mpaa, "director": director,
                        "writer": writer, "castwiththumb": castwiththumb, "plot": plot, "imdb": imdb, "tvdb": tvdb,
                        "tmdb": tmdb, "poster": poster, "banner": banner, "fanart": fanart, "thumb": thumb, "keyart": keyart,
                        "clearlogo": clearlogo, "clearart": clearart, "landscape": landscape, "paused_at": paused_at,
                        "watched_at": watched_at, "localtvshowtitle": localtvshowtitle, "tvshow.poster": tvshow_poster,
                        "characterart": characterart,
                        })

            except Exception:
                log_utils.log("trakt_episodes_list", "indexer")
                fflog_exc(1)
                pass

        items = items[:100]
        # fflog(f'{len(items)=}  {items=}')

        arts_from_fanarttv = {}
        """
        tvdb_list = list(set((i["tvdb"]) for i in items if i["tvdb"]!="0"))
        if self.fanartTV_artwork == "true":
            for tvdb in tvdb_list:
                arts = self.fanart_tv_art(tvdb)
                arts_from_fanarttv.update({tvdb: arts})
        # fflog(f'{len(arts_from_fanarttv)=}  {arts_from_fanarttv=}')
        """

        arts_from_tmdb = {}  # do wywalenia (bo to daje tylko postery sezonu, a niżej mam więcej)
        """
        tmdb_list = list(set((i["tmdb"], i["season"]) for i in items))
        # fflog(f'{tmdb_list=}')
        for tmdb, season in tmdb_list:
            url = self.tmdb_season_lite_link % (tmdb, season)
            # control.log(f'{url=}', 1)
            try:
                r = self.session.get(url, timeout=16)
                r.encoding = "utf-8"
                item = r.json()
                arts = item.get("poster_path", "")  # tylko poster sezonu
                arts_from_tmdb[tmdb, season] = arts
            except Exception:
                # fflog_exc(1)
                pass
        # fflog(f'{len(arts_from_tmdb)=}  {arts_from_tmdb=}')
        """

        tmdb_list = list(set((i["imdb"], i["tmdb"]) for i in items))
        # fflog(f'{tmdb_list=}')
        meta_from_tmdb = {}
        for imdb, tmdb in tmdb_list:
            meta = self.get_meta_for_tvshow(imdb, tmdb)
            meta_from_tmdb[imdb, tmdb] = {k:v for k,v in meta.items() 
                                          #if k in ["poster", "landscape", "fanart", "seasons_posters", "clearlogo"]
                                          if k in [ "poster",
                                                    "seasons_posters",
                                                    "fanart",
                                                    "seasons_fanarts",
                                                    "landscape",
                                                    "seasons_landscapes",
                                                    "clearlogo",
                                                    "clearart",
                                                    "keyart",
                                                    "banner",
                                                    "seasons_banners",
                                                    "characterart",
                                                  ]
                                         }
        # fflog(f'{len(meta_from_tmdb)=}  {meta_from_tmdb=}')
        meta = None

        asynchronicznie = False
        threads = []
        if asynchronicznie:
            import threading
        # fflog('start')
        for i in items:
            if asynchronicznie:
                threads.append(threading.Thread(target=items_list, args=(i, arts_from_fanarttv, arts_from_tmdb, meta_from_tmdb,)))  # asynchronicznie
            else:
                items_list(i,arts_from_fanarttv,arts_from_tmdb, meta_from_tmdb)  # sychronicznie
        if threads:
            [i.start() for i in threads]
            [i.join() for i in threads]
        # fflog('koniec')

        return self.list


    def trakt_user_list(self, url, user):
        try:
            items = trakt.getTraktAsJson(url)
        except Exception:
            fflog_exc(1)
            pass

        for item in items:
            try:
                try:
                    name = item["list"]["name"]
                except:
                    name = item["name"]
                name = client.replaceHTMLCodes(name)

                try:
                    url = (trakt.slug(item["list"]["user"]["username"]), item["list"]["ids"]["slug"])
                except:
                    url = ("me", item["ids"]["slug"])
                url = self.traktlist_link % url
                # url = six.ensure_str(url)

                self.list.append({"name": name, "url": url, "context": url})
            except Exception:
                fflog_exc(1)
                pass

        self.list = sorted(self.list, key=lambda k: utils.title_key(k["name"]))
        return self.list


    def tvmaze_list(self, url, limit):  # ciekawe kiedy ta funkcja jest w użyciu
        fflog(f'[tvmaze_list] {url=} {limit=}')
        try:
            # result = client.request(url)
            items = self.session.get(url).json()
            itemlist = []
        # items = json.loads(result)
        except Exception:
            fflog_exc(1)
            return

        for item in items:
            try:
                if not "english" in item["show"]["language"].lower():
                    raise Exception()

                if limit == True and not "scripted" in item["show"]["type"].lower():
                    raise Exception()

                title = item["name"]
                if title is None or title == "":
                    raise Exception()
                title = client.replaceHTMLCodes(title)
                # title = six.ensure_str(title)

                season = item["season"]
                season = re.sub("[^0-9]", "", "%01d" % int(season))
                if season == "0":
                    raise Exception()
                # season = six.ensure_str(season)

                episode = item["number"]
                episode = re.sub("[^0-9]", "", "%01d" % int(episode))
                if episode == "0":
                    raise Exception()
                # episode = six.ensure_str(episode)

                tvshowtitle = item["show"]["name"]
                if tvshowtitle is None or tvshowtitle == "":
                    raise Exception()
                tvshowtitle = client.replaceHTMLCodes(tvshowtitle)
                # tvshowtitle = six.ensure_str(tvshowtitle)

                year = item["show"]["premiered"]
                year = re.findall(r"(\d{4})", year)[0]
                # year = six.ensure_str(year)

                imdb = item["show"]["externals"].get("imdb")
                if imdb is None or imdb == "":
                    imdb = "0"
                else:
                    imdb = "tt" + re.sub("[^0-9]", "", str(imdb))
                # imdb = six.ensure_str(imdb)

                tvdb = item["show"]["externals"].get("thetvdb")
                if tvdb is None or tvdb == "":
                    tvdb = "0"  # raise Exception()
                tvdb = re.sub("[^0-9]", "", str(tvdb))
                # tvdb = six.ensure_str(tvdb)

                poster1 = "0"
                try:
                    poster1 = item["show"]["image"]["original"]
                except:
                    poster1 = "0"
                if poster1 is None or poster1 == "":
                    poster1 = "0"
                else:
                    poster1 = six.ensure_str(poster1)

                try:
                    thumb1 = item["show"]["image"]["original"]
                except:
                    thumb1 = "0"
                try:
                    thumb2 = item["image"]["original"]
                except:
                    thumb2 = "0"
                if thumb2 is None or thumb2 == "0":
                    thumb = thumb1
                else:
                    thumb = thumb2
                if thumb is None or thumb == "":
                    thumb = "0"
                thumb = six.ensure_str(thumb)

                premiered = item.get("airdate")
                try:
                    premiered = re.findall(r"(\d{4}-\d{2}-\d{2})", premiered)[0]
                except:
                    premiered = "0"
                premiered = six.ensure_str(premiered)

                try:
                    studio = item["show"]["network"]["name"]
                except:
                    studio = "0"
                if studio is None:
                    studio = "0"
                studio = six.ensure_str(studio)

                try:
                    genre = item["show"]["genres"]
                except:
                    genre = "0"
                genre = [i.title() for i in genre]
                if not genre:
                    genre = "0"
                genre = " / ".join(genre)
                genre = six.ensure_str(genre)

                try:
                    duration = item["show"]["runtime"]
                except:
                    duration = "0"
                if duration is None:
                    duration = "0"
                duration = str(duration)
                # duration = six.ensure_str(duration)

                try:
                    rating = item["show"]["rating"]["average"]
                except:
                    rating = "0"
                if rating is None or rating == "0.0":
                    rating = "0"
                rating = str(rating)
                # rating = six.ensure_str(rating)

                votes = "0"

                try:
                    plot = item["show"]["summary"]
                except:
                    plot = "0"
                if plot is None:
                    plot = "0"
                plot = re.sub("<.+?>|</.+?>|\n", "", plot)
                plot = client.replaceHTMLCodes(plot)
                # plot = six.ensure_str(plot)

                poster2 = fanart = banner = landscape = clearlogo = clearart = banner2 = landscape2 = "0"

                if not tvdb == "0":
                    if self.fanartTV_artwork == "true":
                        poster1, poster2, fanart, banner, landscape, clearlogo, clearart, banner2, landscape2 = self.fanart_tv_art(tvdb)
                        if isinstance(poster2, dict):
                            poster2 = poster2.get(season)
                        if isinstance(banner2, dict):
                            banner2 = banner2.get(season)
                        if isinstance(landscape2, dict):
                            landscape2 = landscape2.get(season)

                poster = poster2 if poster2 and not poster2 == "0" else poster1
                banner = banner2 if banner2 and not banner2 == "0" else banner
                landscape = landscape2 if landscape2 and not landscape2 == "0" else landscape

                itemlist.append(
                    {"title": title, "season": season, "episode": episode, "tvshowtitle": tvshowtitle, "year": year,
                        "premiered": premiered, "status": "Continuing", "studio": studio, "genre": genre,
                        "duration": duration, "rating": rating, "votes": votes, "plot": plot, "imdb": imdb,
                        "tvdb": tvdb, "tmdb": "0", "thumb": thumb, "poster": poster, "banner": banner, "fanart": fanart,
                        "clearlogo": clearlogo, "clearart": clearart, "landscape": landscape, })

            except:
                pass

        itemlist = itemlist[::-1]
        return itemlist


    def fanart_tv_art(self, tvdb, season=None):  # "season" do usunięcia
        # chyba już tylko dla tvmaze_list list jest to uruchamiane
        poster = poster2 = fanart = banner = landscape = clearlogo = clearart = banner2 = landscape2 = "0"
        # props  = ["seasonposter", "tvposter", "showbackground", "tvbanner", "hdtvlogo", "hdclearart", "tvthumb", "seasonbanner", "seasonthumb"]
        # props += ["characterart"]  # to do
        order = 1  # -1 to odwrócenie (kiedyś tak było, ale dlaczego?)
        # control.log(f'{self.fanart_tv_user=}', 1)
        # control.log(f'{self.fanart_tv_headers=}', 1)
        if self.fanart_tv_user != '':

            try:
                # control.log(f'url: {self.fanart_tv_art_link % tvdb}  {self.fanart_tv_headers=}', 1)
                r = self.session.get(self.fanart_tv_art_link % tvdb, headers=self.fanart_tv_headers, timeout=10, )
                # fflog(f'from FanartTV: {r=}')
                if r.status_code >= 400:
                    # fflog(f'{r.text=}')
                    pass
                r.raise_for_status()

                r.encoding = "utf-8"
                art = r.json()  # if six.PY3 else utils.json_loads_as_str(r.text)
                # fflog(f'{art=}')
            except Exception:
                art = {}
                pass

            if art:
                try:

                    try:
                        _poster = art["tvposter"]
                        _poster = ([x for x in _poster if x.get("lang") == self.lang][::order] 
                                 + [x for x in _poster if x.get("lang") == "en"][::order] 
                                 + [x for x in _poster if x.get("lang") in ["00", ""]][::order]
                                )
                        _poster = _poster[0]["url"]
                        if _poster:
                            poster = _poster
                    except Exception:
                        # fflog_exc(1)
                        pass

                    #if season:
                    if True:
                        try:
                            _poster = art["seasonposter"]
                            _poster = ([x for x in _poster if x.get("lang") == self.lang][::order] 
                                     + [x for x in _poster if x.get("lang") == "en"][::order] 
                                     + [x for x in _poster if x.get("lang") in ["00", ""]][::order]
                                    )
                            # if season:
                                # _poster = [x for x in _poster if x.get("season") == season]
                                # _poster = _poster[0]["url"]
                            # _poster = [{x["season"]:x["url"]} for x in _poster]  # lista
                            _poster = {x["season"]:x["url"] for x in _poster}  # słownik
                            if _poster:
                                poster2 = _poster
                        except Exception:
                            # fflog_exc(1)
                            pass

                        try:
                            _banner = art["seasonbanner"]
                            _banner = ([x for x in _banner if x.get("lang") == self.lang][::order] 
                                     + [x for x in _banner if x.get("lang") == "en"][::order] 
                                     + [x for x in _banner if x.get("lang") in ["00", ""]][::order]
                                    )
                            # if season:
                                # _banner = [x for x in _banner if x.get("season") == season]
                                # _banner = _banner[0]["url"]
                            # _banner = [{x["season"]:x["url"]} for x in _banner]
                            _banner = {x["season"]:x["url"] for x in _banner}
                            if _banner:
                                banner2 = _banner
                        except Exception:
                            # fflog_exc(1)
                            pass

                        try:
                            _landscape = art["seasonthumb"]
                            _landscape = ([x for x in _landscape if x.get("lang") == self.lang][::order] 
                                     + [x for x in _landscape if x.get("lang") == "en"][::order] 
                                     + [x for x in _landscape if x.get("lang") in ["00", ""]][::order]
                                    )
                            # if season:
                                # _landscape = [x for x in _landscape if x.get("season") == season]
                                # _landscape = _landscape[0]["url"]
                            # _landscape = [{x["season"]:x["url"]} for x in _landscape]
                            _landscape = {x["season"]:x["url"] for x in _landscape}
                            if _landscape:
                                landscape2 = _landscape
                        except Exception:
                            # fflog_exc(1)
                            pass

                    try:
                        _fanart = art["showbackground"]
                        _fanart = ( [x for x in _fanart if x.get("lang") == self.lang][::order] + 
                                    [x for x in _fanart if x.get("lang") == "en"][::order] + 
                                    [x for x in _fanart if x.get("lang") in ["00", ""]][::order]
                                  )
                        _fanart = _fanart[0]["url"]
                        if _fanart:
                            fanart = _fanart
                    except Exception:
                        # fflog_exc(1)
                        pass


                    #if self.hq_artwork == "true":  # wywalić trzeba będzie
                    if True:
                        # fflog(f'{self.hq_artwork=}')
                        try:
                            _banner = art["tvbanner"]
                            _banner = ( [x for x in _banner if x.get("lang") == self.lang][::order] + 
                                        [x for x in _banner if x.get("lang") == "en"][::order] + 
                                        [x for x in _banner if x.get("lang") in ["00", ""]][::order]
                                      )
                            _banner = _banner[0]["url"]
                            if _banner:
                                banner = _banner
                        except Exception:
                            # fflog_exc(1)
                            pass

                        try:
                            if "hdtvlogo" in art:
                                _clearlogo = art["hdtvlogo"]
                            else:
                                _clearlogo = art["clearlogo"]
                            _clearlogo = (
                                    [x for x in _clearlogo if x.get("lang") == self.lang][::order] + 
                                    [x for x in _clearlogo if x.get("lang") == "en"][::order] + 
                                    [x for x in _clearlogo if x.get("lang") in ["00", ""]][::order]
                                    )
                            _clearlogo = _clearlogo[0]["url"]
                            if _clearlogo:
                                clearlogo = _clearlogo
                        except Exception:
                            # fflog_exc(1)
                            pass

                        try:
                            if "hdclearart" in art:
                                _clearart = art["hdclearart"]
                            else:
                                _clearart = art["clearart"]
                            _clearart = ([x for x in _clearart if x.get("lang") == self.lang][::order] + 
                                         [x for x in _clearart if x.get("lang") == "en"][::order] + 
                                         [x for x in _clearart if x.get("lang") in ["00", ""]][::order]
                                        )
                            _clearart = _clearart[0]["url"]
                            if _clearart:
                                clearart = _clearart
                        except Exception:
                            # fflog_exc(1)
                            pass

                        try:
                            if "tvthumb" in art:
                                _landscape = art["tvthumb"]
                            else:
                                _landscape = art["showbackground"]  # fallback
                            _landscape = (
                                    [x for x in _landscape if x.get("lang") == self.lang][::order] +
                                    [x for x in _landscape if x.get("lang") == "en"][::order] + 
                                    [x for x in _landscape if x.get("lang") in ["00", ""]][::order]
                                    )
                            _landscape = _landscape[0]["url"]
                            if _landscape:
                                landscape = _landscape
                        except Exception:
                            # fflog_exc(1)
                            pass

                except Exception:
                    log_utils.log("fanart.tv art fail", "indexer")
                    fflog_exc(1)
                    pass

        else:
            # brak danych do zalogowania do fanart
            fflog('brak danych do zalogowania do fanart')
            pass
        if r.status_code == 200:
            # fflog(f'\n{poster=} \n{poster2=} \n{fanart=} \n{banner=} \n{landscape=} \n{clearlogo=} \n{clearart=} \n{banner2=} \n{landscape2=}')
            pass
        # return poster, poster2, fanart, banner, landscape, clearlogo, clearart
        # return poster, poster2, fanart, banner, landscape, clearlogo, clearart, banner2
        return poster, poster2, fanart, banner, landscape, clearlogo, clearart, banner2, landscape2


    #def tmdb_list(self, tvshowtitle, year, imdb, tmdb, season, meta=None, localtvshowtitle="", originaltvshowtitle="", lite=False):
    def tmdb_list(self, tvshowtitle="", year="", imdb=None, tmdb=None, tvdb=None, season=None, meta=None, localtvshowtitle="", originaltvshowtitle="", lite=False):
        fflog(f'{tvshowtitle=} {imdb=} {tmdb=} {season=} {lite=}', 0)
        # tvdb = None

        if (tmdb is None or tmdb == "0") and not imdb == "0":
            try:
                url = self.tmdb_by_imdb % imdb
                result = self.session.get(url, timeout=16).json()
                # fflog(f'result={json.dumps(result, indent=2)}')
                tmdb_result = result["tv_results"][0]
                tmdb = tmdb_result["id"]
                if not tmdb:
                    tmdb = "0"
                else:
                    tmdb = str(tmdb)
                    fflog(f'{tmdb=} {tvshowtitle=}', 0)
            except Exception:
                fflog_exc(1)
                pass

        if tmdb is None and tvshowtitle:
            try:
                url = (self.search_link % (quote(tvshowtitle)) + "&first_air_date_year=" + year)
                result = self.session.get(url, timeout=16).json()
                # fflog(f'result={json.dumps(result, indent=2)}')
                results = result["results"]
                show = [r for r in results if cleantitle.get(r.get("name")) == cleantitle.get(tvshowtitle)][0]  # and re.findall('(\d{4})', r.get('first_air_date'))[0] == self.list[i]['year']][0]
                tmdb = show["id"]
                if not tmdb:
                    tmdb = "0"
                else:
                    tmdb = str(tmdb)
                    fflog(f'{tmdb=} {tvshowtitle=}', 0)
            except Exception:
                fflog_exc(1)
                tmdb = None
                fflog(f'{tmdb=}')
                pass

        try:
            if tmdb == "0" or tmdb is None:
                # fflog(f'{tmdb=}')
                raise Exception(f'{tmdb=}')

            mpaa = ""

            meta1 = {}
            if not tvshowtitle or not tvdb:
                # log_utils.fflog('trzeba pobrać dane serialu')
                meta1 = self.get_meta_for_tvshow(imdb, tmdb)
                tvshowtitle = meta1.get("originaltitle")
                year = meta1.get("year")
                localtvshowtitle = meta1.get("title")
                originaltvshowtitle = meta1.get("originalname")
                mpaa = meta1.get("mpaa")
                tvdb = meta1.get("tvdb")
                #meta = ep_meta # ?
                #meta1 = None  # nie, przydaje się później

            if not tvdb:
                tvdb = "0"

            # fflog(f'{season=}')

            # można jeszcze dodać pobieranie z fanart_tv
            # poster1 = poster2 = fanart1 = fanart2 = banner1 = landscape1 = clearlogo1 = clearart1 = banner2 = landscape2 = keyart1 = "0"
            """
            if not tvdb == "0":
                if self.fanartTV_artwork == "true":
                    poster1, poster2, fanart1, banner1, landscape1, clearlogo1, clearart1, banner2, landscape2 = self.fanart_tv_art(tvdb)
                    # czy tu jest znany season ? czyli numer sezonu ?
                    if isinstance(poster2, dict):
                        poster2 = poster2.get(season)
                    if isinstance(banner2, dict):
                        banner2 = banner2.get(season)
                    if isinstance(landscape2, dict):
                        landscape2 = landscape2.get(season)
            """
            poster1 = poster2 = fanart1 = fanart2 = landscape1 = landscape2 = clearlogo1 = clearart1 = keyart1 = banner1 = banner2 = characterart1 = "0"

            if meta1:
                poster = meta1.get("poster") or "0"
                poster2 = meta1.get("seasons_posters") or "0"
                fanart = meta1.get("fanart") or "0"
                fanart2 = meta1.get("seasons_fanarts") or "0"
                landscape = meta1.get("landscape") or "0"
                landscape2 = meta1.get("seasons_landscapes") or "0"
                clearlogo = meta1.get("clearlogo") or "0"
                clearart = meta1.get("clearart") or "0"
                keyart = meta1.get("keyart") or "0"
                banner = meta1.get("banner") or "0"
                banner2 = meta1.get("seasons_banners") or "0"
                characterart = meta1.get("characterart") or "0"

                if isinstance(poster2, dict):
                    poster2 = poster2.get(season)
                if isinstance(fanart2, dict):
                    fanart2 = fanart2.get(season)
                if isinstance(landscape2, dict):
                    landscape2 = landscape2.get(season)
                if isinstance(banner2, dict):
                    banner2 = banner2.get(season)

            seasons = self.tmdb_show_lite_link % tmdb
            # control.log(f"{seasons=}", 1)
            r = self.session.get(seasons, timeout=10)
            r.raise_for_status()
            r.encoding = "utf-8"
            result = r.json()  # if six.PY3 else utils.json_loads_as_str(r.text)
            # fflog(f'{result["number_of_seasons"]=}')
            #for season_tmp in range(1, result["number_of_seasons"] + 1, 1):
            for season_tmp in range(0, result["number_of_seasons"] + 1, 1):
                # fflog(f'{season=}')
                if season or season == 0:
                    season_tmp = season
                # fflog(f'{season_tmp=}')

                if self.specials == "false":
                    if season_tmp == 0 or season_tmp == '0':
                        # fflog(f'pomijam')
                        continue

                episodes_url = self.tmdb_season_link % (tmdb, season_tmp, self.lang)
                episodes_lite_url = self.tmdb_season_lite_link % (tmdb, season_tmp)
                if not lite:
                    url = episodes_url
                else:
                    url = episodes_lite_url

                # control.log('tmdb url: ' + repr(url), 1)
                r = self.session.get(url, timeout=10)
                if r.status_code == 404:
                    fflog(f'brak sesonu o numerze {season_tmp=}')
                    continue
                r.raise_for_status()
                r.encoding = "utf-8"
                result = r.json()  # if six.PY3 else utils.json_loads_as_str(r.text)

                episodes = result["episodes"]

                if self.specials == "false":
                    episodes = [e for e in episodes if not e["season_number"] == 0]

                if not episodes:
                    fflog(f'brak odcinków dla {tvshowtitle=} {year=} {season_tmp=}')
                    continue
                    # raise Exception()

                result_en = {}
                for item in episodes:
                    episodeplot = item["overview"]
                    if not episodeplot:
                        log_utils.fflog(f'potrzeba pobrania angielskich opisów dla odcinków', 0)
                        ##### En plot fetch - set up
                        episodes_url_en = self.tmdb_season_lite_link % (tmdb, season_tmp)
                        # control.log(f'{episodes_url_en=}', 1)
                        r_en = self.session.get(episodes_url_en, timeout=10)
                        r_en.raise_for_status()
                        r_en.encoding = "utf-8"
                        result_en = r_en.json()
                        ##########
                        break

                r_cast = result.get("aggregate_credits", {}).get("cast", [])

                poster_path = result.get("poster_path")
                if poster_path:
                    poster = self.tm_img_link % ("500", poster_path)
                else:
                    poster = "0"

                fanart = banner = clearlogo = clearart = landscape = duration = status = tvshow_poster = tvshow_banner = tvshow_landscape = keyart = tvshow_fanart = characterart = "0"
                season_banner = season_landscape = season_poster = "0"  # (na razie) nieużywane

                clearlogo = meta1.get("clearlogo") or "0"

                if meta:
                    try:
                        _meta = json.loads(unquote_plus(meta))
                    except Exception:
                        fflog_exc(1)
                        _meta = None
                        pass
                elif meta1:
                    _meta = meta1
                else:
                    _meta = None
                if _meta:
                    try:
                        if "poster" in _meta.keys():
                            poster = _meta["poster"]

                        if "tvshow.poster" in _meta.keys():
                            tvshow_poster = _meta["tvshow.poster"]

                        if "season.poster" in _meta.keys():
                            # season_poster = _meta["season.poster"]
                            poster = _meta["season.poster"]

                        if "fanart" in _meta.keys():
                            fanart = _meta["fanart"]

                        if "clearlogo" in _meta.keys():
                            clearlogo = _meta["clearlogo"]

                        if "clearart" in _meta.keys():
                            clearart = _meta["clearart"]

                        if "keyart" in _meta.keys():
                            keyart = _meta["keyart"]

                        if "characterart" in _meta.keys():
                            characterart = _meta["characterart"]

                        if "banner" in _meta.keys():
                            banner = _meta["banner"]

                        if "landscape" in _meta.keys():
                            landscape = _meta["landscape"]

                        if "duration" in _meta.keys():
                            duration = _meta["duration"]

                        if "status" in _meta.keys():
                            status = _meta["status"]

                        if "mpaa" in _meta.keys() and _meta["mpaa"]:
                            mpaa = _meta["mpaa"]

                        if "tvshow.banner" in _meta.keys():
                            tvshow_banner = _meta["tvshow.banner"]

                        if "tvshow.landscape" in _meta.keys():
                            tvshow_landscape = _meta["tvshow.landscape"]

                        if "tvshow.fanart" in _meta.keys():
                            tvshow_fanart = _meta["tvshow.fanart"]

                        if "season.banner" in _meta.keys():
                            # season_banner = _meta["season.banner"]
                            banner = _meta["season.banner"]

                        if "season.landscape" in _meta.keys():
                            # season_landscape = _meta["season.landscape"]
                            landscape = _meta["season.landscape"]

                    except Exception:
                        # fflog_exc(1)
                        pass


                tvshow_poster = poster1 if poster1 and poster1 != "0" else tvshow_poster
                poster = poster2 if poster2 and poster2 != "0" else poster  # season.poster
                poster = poster1 if (not poster2 or poster2 == "0") and poster1 and poster1 != "0" else poster

                fanart = fanart1 if fanart1 and fanart1 != "0" else fanart

                clearart = clearart1 if clearart1 and clearart1 != "0" else clearart

                clearlogo = clearlogo1 if clearlogo1 and clearlogo1 != "0" else clearlogo
                
                keyart = keyart1 if keyart1 and keyart1 != "0" else keyart

                characterart = characterart1 if characterart1 and characterart1 != "0" else characterart

                tvshow_banner = banner1 if banner1 and banner1 != "0" else tvshow_banner
                banner = banner2 if banner2 and banner2 != "0" else banner  # season.banner
                banner = banner1 if (not banner2 or banner2 == "0") and banner1 and banner1 != "0" else banner

                tvshow_landscape = landscape1 if landscape1 and landscape1 != "0" else tvshow_landscape
                landscape = landscape2 if landscape2 and landscape2 != "0" else landscape  # season.landscape
                landscape = landscape1 if (not landscape2 or landscape2 == "0") and landscape1 and landscape1 != "0" else landscape

                tvshow_fanart = fanart1 if fanart1 and fanart1 != "0" else tvshow_fanart
                fanart = fanart2 if fanart2 and fanart2 != "0" else fanart  # season.fanart
                fanart = fanart1 if (not fanart2 or fanart2 == "0") and fanart1 and fanart1 != "0" else fanart


                count = 0
                # fflog(f'{len(episodes)=}')
                for item in episodes:
                    # fflog(f'{count=}')
                    try:
                        season_tmp = str(item["season_number"])
                        episode = str(item["episode_number"])

                        title = item.get("name")
                        # fflog(f'{title=}')
                        # if not title or 'dcinek ' in title:
                        if not title or result_en and re.search(r'^[Oo]dcinek \d+$', title):
                            try:
                                title = result_en["episodes"][count]["name"]
                            except Exception:
                                # fflog_exc(1)
                                pass
                        # fflog(f'{title=}')
                        if not title or result_en and re.search(r'^[Ee]pisode \d+$', title):
                            # title = "Episode %s" % episode
                            title = "(odcinek %s)" % episode
                            # fflog(f'2 {title=}')

                        label = title

                        premiered = item.get("air_date")
                        if not premiered:
                            premiered = "0"

                        duration = item.get("runtime", "0")

                        unaired = ""
                        # fflog(f'{premiered=} {title=}')
                        if not premiered or premiered == "0":
                            pass
                            # brak daty może oznaczać, że nie znana jest jeszcze premiera (ale i też, że nie została wprowadzona informacja o tym)
                            unaired = "true"
                            if self.showunaired != "true":
                                continue
                        elif int(re.sub("[^0-9]", "", str(premiered))) > int(re.sub("[^0-9]", "", str(self.today_date))):
                            unaired = "true"
                            if self.showunaired != "true":
                                continue
                                # raise Exception()

                        still_path = item.get("still_path")
                        if still_path:
                            thumb = self.tm_img_link % ("1280", still_path)
                        else:
                            thumb = "0"

                        mpaa1 = mpaa
                        try:
                            mpaa = str(item["mpaa"])
                        except:
                           # mpaa = ""
                            mpaa = mpaa1
                        if not mpaa:
                            mpaa = "0"
                            pass


                        try:
                            rating = str(item["vote_average"])
                        except:
                            rating = ""
                        if not rating:
                            rating = "0"

                        try:
                            votes = str(item["vote_count"])
                        except:
                            votes = ""
                        if not votes:
                            votes = "0"

                        try:
                            episodeplot = item["overview"]
                        except:
                            episodeplot = ""
                        if not episodeplot:
                            try:
                                episodeplot = result_en["episodes"][count]["overview"]
                            except:
                                pass
                            if not episodeplot:
                                episodeplot = "0"

                        count += 1

                        # if not self.lang == 'en' and episodeplot == '0':
                        # try:
                        # en_item = en_result.get('episodes', [])
                        # episodeplot = en_item['overview']
                        # episodeplot = six.ensure_str(episodeplot)
                        # except:
                        # episodeplot = ''
                        # if not episodeplot: episodeplot = '0'

                        try:
                            r_crew = item["crew"]
                            director = [d for d in r_crew if d["job"] == "Director"]
                            director = ", ".join([d["name"] for d in director])
                            writer = [w for w in r_crew if w["job"] == "Writer"]
                            writer = ", ".join([w["name"] for w in writer])
                        except:
                            director = writer = ""
                        if not director:
                            director = "0"
                        if not writer:
                            writer = "0"

                        castwiththumb = []
                        try:
                            for person in r_cast[:30]:
                                _icon = person["profile_path"]
                                icon = (self.tm_img_link % ("185", _icon) if _icon else "")
                                castwiththumb.append({
                                    "name": person["name"],
                                    "role": person["roles"][0]["character"],
                                    "thumbnail": icon,
                                    })
                        except:
                            pass
                        if not castwiththumb:
                            castwiththumb = "0"

                        self.list.append({"title": title, "label": label, "season": season_tmp, "episode": episode,
                            "tvshowtitle": tvshowtitle, "year": year, "premiered": premiered, "rating": rating, "mpaa": mpaa,
                            "votes": votes, "director": director, "writer": writer, "castwiththumb": castwiththumb,
                            "duration": duration, "status": status, "plot": episodeplot, "imdb": imdb, "tmdb": tmdb,
                            "tvdb": tvdb, "unaired": unaired, "thumb": thumb, "poster": poster, "fanart": fanart,
                            "banner": banner, "clearlogo": clearlogo, "clearart": clearart, "landscape": landscape,
                            "localtvshowtitle": localtvshowtitle, "originaltvshowtitle": originaltvshowtitle, "keyart": keyart,
                            "tvshow.poster": tvshow_poster, "tvshow.banner": tvshow_banner, "tvshow.landscape": tvshow_landscape,
                            # "season.poster": season_poster, "season.banner": season_banner, "season.landscape": season_landscape,
                            "characterart": characterart,
                            })

                    except Exception:
                        log_utils.log("tmdb_list2 Exception", "indexer")
                        fflog_exc(1)
                        pass

                try:
                    if season or season == 0:
                        # fflog(f'wyskoczenie z pętli {season=} {season_tmp=}')  # musi wyskoczyć, gdy nie jest włączone spłaszczanie seriali
                        break
                except Exception as e:
                    fflog_exc(1)
                    pass

            # fflog(f'{self.list=}')
            # self.list = sorted(self.list, key=lambda k: k["premiered"], reverse=False)
            self.list = sorted(self.list, key=lambda k: (int(k["season"]), int(k["episode"])), reverse=False)

            try:
                # fflog(f'zapisywanie do cache')
                if season or season == 0:
                    cache.cache_insert("episodes" + f"_{tmdb or imdb}_s{season}", repr(self.list))
                else:
                    cache.cache_insert("episodes" + f"_{tmdb or imdb}", repr(self.list))
            except Exception:
                fflog_exc(1)
                pass

            return self.list

        except Exception as e:
            log_utils.log(f"tmdb_list1 Exception {e!r}", "indexer")
            fflog_exc(1)
            return self.list


    def get_meta_for_tvshow(self, imdb=None, tmdb=None):
        try:
            meta = cache.cache_get("superinfo" + f"_{tmdb or imdb}")  # sprawdzenie, czy nie ma już w cache
            if not meta:
                # log_utils.fflog('próba pobrania informacji o serialu przez super_info.py')
                # from resources.lib.indexers.super_info import SuperInfo
                media_list = [{'tmdb': tmdb, 'imdb': imdb}]
                # import requests
                # session = requests.Session()
                lang = control.apiLanguage()["tmdb"]
                super_info_obj = SuperInfo(media_list, self.session, lang, "tvshow")
                super_info_obj.get_info(0)

                meta = cache.cache_get("superinfo" + f"_{tmdb or imdb}")
            if meta:
                from ast import literal_eval
                meta = meta["value"]
                meta = literal_eval(meta)
            else:
                meta = {}
        except Exception:
            meta = {}
            fflog_exc(1)
        return meta


    def episodeDirectory(self, items, force_tvshow_title: bool = False):
        fflog(f'[episodeDirectory]')
        if items is None or len(items) == 0:
            sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        if control.setting("zastepcze_grafiki") == "true":
            addonPoster = control.addonPoster()
            addonFanart = control.addonFanart()
            addonBanner = control.addonBanner()
        else:
            addonPoster = addonFanart = addonBanner = ""

        settingFanart = control.setting("fanart")

        traktCredentials = trakt.getTraktCredentialsInfo()

        try:
            isOld = False
            control.item().getArt("type")
        except:
            isOld = True

        try:
            multi = [i["tvshowtitle"] for i in items]
        except:
            multi = []
        multi = force_tvshow_title or len(set(multi)) > 1

        try:
            sysaction = items[0]["action"]
        except:
            sysaction = ""

        isFolder = False if not sysaction == "episodes" else True
        isPlayable = "true" if "plugin" not in control.infoLabel("Container.PluginName") else "false"  # dziwny warunek - niżej go modyfikuje jeszcze
        playbackMenu = (control.lang(32063) if control.setting("hosts.mode") == "2" else control.lang(32064))
        dont_use_setResolvedUrl = control.setting("player.dont_use_setResolvedUrl") == "true"
        indicators = playcount.getTVShowIndicators(refresh=True)
        traktIndicators  = trakt.getTraktIndicatorsInfo()
        watchedMenu =   (control.lang(32068) if traktIndicators == True else control.lang(32066))
        unwatchedMenu = (control.lang(32069) if traktIndicators == True else control.lang(32067))
        indicator_kodi = control.setting("indicator.kodi") == "true"
        queueMenu = control.lang(32065)
        traktManagerMenu = control.lang(32070)
        tvshowBrowserMenu = control.lang(32071)
        addToLibrary = control.lang(32551)
        generate_short_path = control.setting("generate_short_path") == "true"
        disp_dir = False if control.setting("hosts.mode") != "1" else True
        kodiver = source_utils.get_kodi_version()

        # Spis odcinków w sezonie.
        addSortMethod(syshandle, sortMethod=SORT_METHOD_UNSORTED, labelMask="%L")

        downloads = (
            control.setting("downloads") == "true"
            and not (
                control.setting("movie.download.path") == ""
                or control.setting("tv.download.path") == ""
            )
        )
        downloadMenu = control.lang(32403)

        unpremiered_color = control.setting("unpremiered_color")
        if unpremiered_color == "inny":
            unpremiered_color = control.setting("unpremiered_custom_color")
        else:
            colors_map = {
                "szary": "gray",
                "czerwony": "red",
                "fioletowy": "magenta",
                "pomarańczowy": "orange",
                }
            unpremiered_color = colors_map[unpremiered_color]
        # fflog(f'{unpremiered_color=}')

        counter = 1
        # fflog(f'{len(items)=}')
        for i in items:
            try:
                #fflog(f'{i=}')
                if "label" not in i:
                    i["label"] = i["title"]
                if i["label"] == "0":
                    label = "%sx%02d  %s %s" % (i["season"], int(i["episode"]), "Episode", i["episode"],)
                else:
                    label = "%sx%02d  %s" % (i["season"], int(i["episode"]), i["label"],)
                syslabel = quote_plus(label)
                if multi:
                    label = "{} – {}".format(i.get("localtvshowtitle") or i["tvshowtitle"], label)

                imdb, tvdb, tmdb, year, season, episode = i["imdb"], i["tvdb"], i["tmdb"], i["year"], i["season"], i["episode"]

                systitle = quote_plus(i["title"])
                systvshowtitle = quote_plus(i["tvshowtitle"])
                syslocaltvshowtitle = quote_plus( i.get("localtvshowtitle") or "")
                syspremiered = quote_plus(i["premiered"])

                meta = {k: v for k, v in i.items() if not v == "0"}

                meta.update({"mediatype": "episode"})

                meta.update({"season": season})  # potrzebne dla sezonów o numerze 0
                meta.update({"episode": episode})  # potrzebne dla epizodów o numerze 0

                # meta.update({"trailer": "%s?action=trailer&name=%s" % (sysaddon, systvshowtitle)})
                # meta.update({"trailer": "%s?action=trailer&name=%s&url=%s" % (sysaddon, systvshowtitle, quote_plus(meta.get("trailer") or ""))})
                meta.update({"trailer": "%s?action=trailer&name=%s&url=%s" % (sysaddon, systvshowtitle + " " + syslabel, quote_plus(meta.get("trailer") or ""))})

                # fflog(f'{("duration" in i)=} {i.get("duration")=} {meta.get("duration")=} {i["label"]=}')
                if not "duration" in i:
                    # meta.update({"duration": "60"})
                    # meta.update({"duration": "1"})
                    pass
                elif i["duration"] == "0":
                    # meta.update({"duration": "60"})
                    # meta.update({"duration": "1"})
                    pass
                try:
                    if meta.get("duration") and meta.get("duration") != "0":
                        meta.update({"duration": str(int(meta["duration"]) * 60)})
                except:
                    pass
                # fflog(f'{("duration" in i)=} {i.get("duration")=} {meta.get("duration")=} {i["label"]=}')

                # try:
                #    meta.update({"genre": cleangenre.lang(meta["genre"], self.lang)})
                # except:
                #    pass

                try:
                    meta.update({"tvshowyear": i["year"]})
                    meta.update({"year": re.findall(r"(\d{4})", i["premiered"])[0]})
                except:
                    pass

                try:
                    meta.update({"title": i["label"]})
                except:
                    pass

                meta.update({"originalname": i.get("originaltvshowtitle", "")})

                meta.pop("next", None)

                sysmeta = quote_plus(json.dumps(meta))

                # url = "%s?action=play&title=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&meta=%s&t=%s" % (sysaddon, systitle, year, imdb, tvdb, season, episode, systvshowtitle, syspremiered, sysmeta, self.systime,)
                url = "%s?action=play&title=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&meta=%s" % (sysaddon, systitle, year, imdb, tmdb, tvdb, season, episode, systvshowtitle, syspremiered, sysmeta)
                sysurl = quote_plus(url)  # potrzebne dla context menu
                fullpath = ""
                if generate_short_path and disp_dir:
                    fullpath = url
                    url = "{}?action=play&item={}".format(sysaddon, counter)
                    #sysurl = quote_plus(url)  # ale czy to potrzebne? bo może bardziej zaszkodzi

                # ta zmienna chyba nie jest wykorzystywana
                # path = "%s?action=play&title=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s" % (sysaddon, systitle, year, imdb, tvdb, season, episode, systvshowtitle, syspremiered,)

                if isFolder:
                    url = "%s?action=episodes&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s" % (sysaddon, systvshowtitle, year, imdb, tmdb, tvdb, season, episode)  # czy tu nie trzeba dać jeszcze meta ?
                    if generate_short_path:
                        fullpath = url
                        url = "{}?action=episodes&item={}".format(sysaddon, counter)

                if "?action=play&" in url:
                    # disp = False if control.setting("hosts.mode") == "0" else True
                    # disp = False if control.setting("hosts.mode") != "1" else True  # disp_dir
                    disp = disp_dir
                else:
                    disp = isFolder

                isPlayable = "true" if not disp else "false"
                isPlayable = "false" if dont_use_setResolvedUrl else isPlayable


                cm = []

                if not isFolder:
                    # if isPlayable == "true":
                    if not disp:
                        cm.append(("EDYTUJ dane do wyszukiwarki", "RunPlugin(%s?action=alterSources&url=%s)" % (sysaddon, sysurl + quote_plus("&customTitles=3")),))
                    else:
                        if not generate_short_path:
                            cm.append(("EDYTUJ dane do wyszukiwarki", "Container.Update(%s?action=alterSources&url=%s)" % (sysaddon, sysurl + quote_plus("&customTitles=3")),))
                        else:
                            cm.append(("EDYTUJ dane do wyszukiwarki", "Container.Update(%s)" % (url + "&customTitles=1"),))

                if not disp:
                    if kodiver.major < 21 or kodiver.major >= 21 and kodiver.minor < 2:
                        cm.append((queueMenu, "RunPlugin(%s?action=queueItem)" % sysaddon))

                if multi:
                    if not generate_short_path:
                        cm.append((tvshowBrowserMenu,
                                   #"Container.Update(%s?action=seasons&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s,return)" % (
                                   "Container.Update(%s?action=seasons&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s)" % (
                                    sysaddon, systvshowtitle, year, imdb, tmdb, tvdb),))
                    else:
                        cm.append((tvshowBrowserMenu, "Container.Update(%s?action=seasons)" % (sysaddon, ), ))

                # if traktCredentials:
                # if True:
                # if not disp:
                if not isPlayable or (traktIndicators or not indicator_kodi):
                    try:
                        overlay = int(playcount.getEpisodeOverlay(indicators, imdb, tmdb, season, episode))
                        if overlay == 7:
                            cm.append((unwatchedMenu, "RunPlugin(%s?action=episodePlaycount&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s&query=6)" % (sysaddon, imdb, tmdb, tvdb, season, episode),))
                            meta.update({"playcount": 1, "overlay": 7})  # to zmienia ptaszki
                        else:
                            cm.append((watchedMenu,   "RunPlugin(%s?action=episodePlaycount&imdb=%s&tmdb=%s&tvdb=%s&season=%s&episode=%s&query=7)" % (sysaddon, imdb, tmdb, tvdb, season, episode),))
                            meta.update({"playcount": 0, "overlay": 6})  # to zmienia ptaszki
                    except Exception:
                        fflog_exc(1)
                        pass

                if traktCredentials:
                    cm.append((traktManagerMenu, "RunPlugin(%s?action=traktManager&name=%s&tmdb=%s&content=tvshow)" % (sysaddon, systvshowtitle, tmdb),))

                if not isFolder:
                    #cm.append((playbackMenu, "RunPlugin(%s?action=alterSources&url=%s&meta=%s)" % (sysaddon, sysurl, sysmeta),))  # w url jest już meta, więc bez sensu
                    cm.append((playbackMenu, "RunPlugin(%s?action=alterSources&url=%s)" % (sysaddon, sysurl),))

                if isOld:
                    cm.append((control.lang2(19033), "Action(Info)"))

                cm.append((addToLibrary,
                           "RunPlugin(%s?action=tvshowToLibrary&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&localtvshowtitle=%s)" % (
                           sysaddon, systvshowtitle, year, imdb, tmdb, syslocaltvshowtitle),))

                if fullpath:
                    cm.append(("[I]przygotuj do ulubionych[/I]", "Container.Update(%s?action=prepareItemForAddToLibrary)" % (sysaddon),))

                if downloads and not isFolder and not disp:
                    cm.append((downloadMenu, "RunPlugin(%s)" % (url + "&download=1"),))

                try:
                    if i["unaired"] == "true":
                        label = f"[COLOR {unpremiered_color}][I]%s[/I][/COLOR]" % label
                except:
                    pass


                item = control.item(label=label, offscreen=True)  # create ListItem


                item.addContextMenuItems(cm)


                art = {}
                # na liście odcinków skórki szukają w kolejności: postera sezonu, a potem postera serialu. Na końcu (jak nie znajdą poprzednich), to wyświetlają poster przypisany do zmiennej poster
                if "poster" in i and not i["poster"] == "0" or "tvshow.poster" in i or "season.poster" in i:
                    art.update({
                        "season.poster": i.get("season.poster") or i.get("poster") or "",  # ustawiamy poster sezonu (u mnie zmienna poster2)
                        "tvshow.poster": i.get("tvshow.poster") or i.get("poster") or "",  # ustawiamy poster serialu (u mnie zmienna poster1)
                        "poster": i.get("poster") or "",  # taki fallback, bo nie ma posteru odcinka raczej (u mnie zmienna poster)
                        })
                else:
                    # art.update({"poster": addonPoster})  # plakatu chyba nie
                    # art.update({"poster": ""})
                    # art.pop("poster", None)
                    pass
                # takie porządki
                if art.get("poster") == "0":
                    art.pop("poster", None)
                if art.get("tvshow.poster") == "0":
                    art.pop("tvshow.poster", None)
                if art.get("season.poster") == "0":
                    art.pop("season.poster", None)

                if "thumb" in i and not i["thumb"] == "0":
                    art.update({
                        "icon": i["thumb"],
                        "thumb": i["thumb"]
                        })
                # elif "fanart" in i and not i["fanart"] == "0":
                    # art.update({
                        # "icon": i["fanart"],
                        # "thumb": i["fanart"]
                        # })
                # elif "poster" in i and not i["poster"] == "0":
                    # art.update({
                        # "icon": i["poster"],
                        # "thumb": i["poster"]
                        # })
                else:
                    art.update({"icon": addonFanart, "thumb": addonFanart})
                    # art.update({"icon": "", "thumb": ""})
                    # art.pop("icon", None)
                    # art.pop("thumb", None)
                    pass
                art["icon"] = re.sub(r'(/t/p/w)\d{3,4}/', r'\g<1>200/', art.get("icon") or "")
                art["thumb"] = re.sub(r'(/t/p/w)\d{3,4}/', r'\g<1>200/', art.get("thumb") or "")
                if not art["thumb"]:
                    art.pop("thumb", None)
                    pass
                if not art["icon"]:
                    art.pop("icon", None)
                    pass

                if "fanart" in i and not i["fanart"] == "0":
                    art.update({"fanart": i["fanart"]})

                if "banner" in i and not i["banner"] == "0":
                    art.update({"banner": i["banner"]})
                elif "fanart" in i and not i["fanart"] == "0":
                    # art.update({"banner": i["fanart"]})
                    pass
                else:
                    art.update({"banner": addonBanner})
                    # art.update({"banner": ""})
                    # art.pop("banner", None)
                    pass

                if "tvshow.banner" in i and not i["tvshow.banner"] == "0":
                    art.update({"tvshow.banner": i["tvshow.banner"]})

                if "season.banner" in i and not i["season.banner"] == "0":
                    art.update({"season.banner": i["season.banner"]})

                if "landscape" in i and not i["landscape"] == "0":
                    art.update({"landscape": i["landscape"]})

                if "tvshow.landscape" in i and not i["tvshow.landscape"] == "0":
                    art.update({"tvshow.landscape": i["tvshow.landscape"]})

                if "season.landscape" in i and not i["season.landscape"] == "0":
                    art.update({"season.landscape": i["season.landscape"]})

                if "clearlogo" in i and not i["clearlogo"] == "0":
                    art.update({"clearlogo": i["clearlogo"]})
                    art.update({"tvshow.clearlogo": i["clearlogo"]})  # to jest ważniejsze dla skórki (tak są napisane warunki sprawdzające)

                if "clearart" in i and not i["clearart"] == "0":
                    art.update({"clearart": i["clearart"]})

                if "keyart" in i and not i["keyart"] == "0":
                    art.update({"keyart": i["keyart"]})

                """
                if "characterart" in i and not i["characterart"] == "0":
                    art.update({"characterart": i["characterart"]})
                """
                if "characterart" in i and not i["characterart"] == "0":
                    characterart = i["characterart"]
                    if isinstance(characterart, list):
                        for an in range(0, len(characterart)):
                            # art[f"characterart{an+1}"] = characterart[an]
                            art.update({f"characterart{an+1}": characterart[an]})
                            # art.update({f"tvshow.characterart{an+1}": characterart[an]})
                    else:
                        # art["characterart"] = characterart
                        art.update({"characterart": characterart})
                        # art.update({"tvshow.characterart": characterart})


                # fflog(f'{art=}')
                item.setArt(art)

                if settingFanart == "true" and "fanart" in i and not i["fanart"] == "0":
                    item.setProperty("Fanart_Image", i["fanart"])  # czy to nie dla jakiejś starszej wersji Kodi ?
                elif not addonFanart is None:
                    # item.setProperty("Fanart_Image", addonFanart)  # j.w.
                    pass

                # fflog(f'{addonFanart=}')
                # fflog(f'{addonPoster=}')

                # obsada
                castwiththumb = i.get("castwiththumb")
                if castwiththumb and not castwiththumb == "0":
                    item.setCast(castwiththumb)


                # meta.pop("imdb", None)
                # meta.pop("tmdb_id", None)
                # meta.pop("imdb_id", None)
                # meta.pop("poster", None)
                # meta.pop("clearlogo", None)
                # meta.pop("clearart", None)
                # meta.pop("fanart", None)
                # meta.pop("fanart2", None)
                # meta.pop("imdb", None)
                # meta.pop("tmdb", None)
                # meta.pop("metacache", None)
                # meta.pop("poster2", None)
                # meta.pop("poster3", None)
                # meta.pop("banner", None)
                # meta.pop("next", None)
                # meta.pop("tvdb", None)
                # meta.pop("tvdb_id", None)
                # meta.pop("banner2", None)
                # meta.pop("label", None)
                # meta.pop("thumb", None)


                item.setInfo(type="Video", infoLabels=control.metadataClean(meta))


                # korekta pod standard ListItem (bo super_info.py inaczej generuje)
                item.setInfo(type="Video", infoLabels={'TvShowTitle': meta.get("localtvshowtitle") or meta.get("tvshowtitle", "")})
                item.setProperty("englishTvShowTitle", meta.get("englishtvshowtitle") or meta.get("tvshowtitle", ""))
                #item.setProperty("OriginalTvShowTitle", meta.get("originaltvshowtitle") or meta.get("tvshowtitle", ""))
                item.setProperty("OriginalTvShowTitle", meta.get("originaltvshowtitle") or "")
                item.setProperty("TvShowYear", meta.get("tvshowyear") or meta.get("year", ""))


                if generate_short_path:
                    # fflog(f'{imdb=} {tmdb=} {tvdb=} {i["label"]=}')
                    try:
                        vtag = item.getVideoInfoTag()
                        vtag.setUniqueIDs({
                            'imdb' : imdb, 
                            'tmdb' : tmdb, 
                            'tvdb' : tvdb,
                        })
                    except Exception:
                        item.setProperty("imdb_id", imdb)
                        item.setProperty("tmdb_id", tmdb)
                        item.setProperty("tvdb_id", tvdb)

                    item.setProperty("meta", json.dumps(meta))
                    item.setProperty("fullpath", fullpath)


                # video_streaminfo = {"codec": "h264"};
                # item.addStreamInfo("video", video_streaminfo)  # czy to w czymś pomaga?


                item.setProperty("IsPlayable", isPlayable)


                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=disp)

                counter += 1
            except Exception:
                fflog_exc(1)
                pass

        params = dict(parse_qsl(sys.argv[2][1:]))
        updateListing = True if params.get("r") else False  # True świadczy, że po drodze było odświeżanie

        control.content(syshandle, "episodes")
        control.directory(syshandle, cacheToDisc=True, updateListing=updateListing)
        views.setView("episodes")



    def addDirectory(self, items, queue=False, add_refresh=False):
        # fflog(f'[addDirectory]')
        if items is None or len(items) == 0:
            return  #  ; sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        addonFanart, addonThumb, artPath = (control.addonFanart(), control.addonThumb(), control.artPath(),)
        queueMenu = control.lang(32065)
        generate_short_path = control.setting("generate_short_path") == "true"

        # Spis... czego właściwie? do kalendarza ?
        # addSortMethod(syshandle, sortMethod=SORT_METHOD_UNSORTED)
        for i in items:
            try:
                name = i["name"]

                if i["image"].startswith("http"):
                    thumb = i["image"]
                elif not artPath is None:
                    thumb = os.path.join(artPath, i["image"])
                else:
                    thumb = addonThumb

                # create ListItem
                try:
                    item = control.item(label=name, offscreen=True)
                except:
                    item = control.item(label=name)

                item.setArt({"icon": thumb, "thumb": thumb, "fanart": addonFanart})

                i["url"] = re.sub("(?<=api_key=)[^&]*", "", i["url"])

                log_utils.fflog(f'{i["action"]=}', 0)  # nie wiem jakie mogą być
                url = "{}?action={}".format(sysaddon, i["action"])
                try:
                    if not generate_short_path or i["action"] not in ["calendar"]:
                        url += "&url=%s" % quote_plus(i["url"])
                    else:
                        item.setProperty("url", i["url"])
                except Exception:
                    pass

                cm = []
                if queue:
                    cm.append((queueMenu, "RunPlugin(%s?action=queueItem)" % sysaddon))
                if add_refresh:
                    cm.append(("Odśwież teraz", "Container.Update(%s&refresh=1)" % url))
                item.addContextMenuItems(cm)

                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
            except Exception:
                fflog_exc(1)
                pass

        control.content(syshandle, "addons")
        control.directory(syshandle, cacheToDisc=True)
        views.setView("addons")  # dodatkowa funkcja FanFilm

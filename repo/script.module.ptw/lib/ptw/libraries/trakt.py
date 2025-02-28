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

import json
import re
import time
import urllib

import requests

try:
    import urllib.parse as urllib
except:
    pass

from ptw.libraries import cache
from ptw.libraries import cleandate
from ptw.libraries import client
from ptw.libraries import control
from ptw.libraries import log_utils
from ptw.libraries import utils
from ptw.libraries import apis
from ptw.libraries.utils import convert

from ptw.libraries.log_utils import log, fflog
from ptw.debug import log_exception, fflog_exc


BASE_URL = "https://api.trakt.tv"
V2_API_KEY = (
    apis.trakt_API
)  # "ccb4fbf0447d86edf30f71caf8f6a8c268e8d4014f84e536746b69752407bfd5"
CLIENT_SECRET = (
    apis.trakt_secret
)  # "ed7cff6b0c686789f101c91a5733d5b3e5122bafd1328f31dbd440d6fb5f4cbf"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


from threading import Thread, Lock
lock = Lock()

stosik = []

usuwanie_niepotrzebnych = True
debug1 = False
debug2 = False

def get_ticekt():
    moj_bilet = time.time()  # generuję nowy bilet
    moj_bilet = moj_bilet / 10000000000  # dla czytelności debugowania
    print(f'\n\n>TWORZE nowy bilet | {moj_bilet=}') if debug1 else ""
    with lock:
        stosik.append(moj_bilet)
        print(f' * ({len(stosik)}) {stosik=}') if debug1 else ""
    return moj_bilet


def check_queue(moj_bilet):
    for i in range(0, int(1/0.02)*5):  # max 5 sec.
        lock.acquire()
        print(f'\n>SPRAWDZAM | {moj_bilet=} w\n ({len(stosik)}) {stosik=}') if debug2 else ""
        if stosik and stosik[0] != moj_bilet:
            lock.release()
            print("muszę czekać") if not i else "" if debug2 else ""
            #print(f"muszę czekać {i=}") if debug2 else ""
            #time.sleep(0.02)
            control.sleep(20)
        elif usuwanie_niepotrzebnych and len(stosik) > 1 and stosik[-1] != moj_bilet:  # wariant że starszych niepotrzebujemy
            lock.release()
            print(f'SĄ NOWSZE, więć się wycofuje') if debug2 else ""
            return False
        else:
            lock.release()
            print(f"{'teraz ' if i else ''} mogę ({i=})") if debug2 else ""
            break
    if i >= (int(1/0.02)*5 - 1):
        print(f'wkurzyłem się - idę na chama')


def del_ticekt(moj_bilet):
    with lock:
        print(f'\n>DO SKASOWANIA\n{moj_bilet=} ze \n({len(stosik)}) {stosik=} ') if debug1 else ""
    try:
        with lock:
            # stosik.pop(0)
            stosik.remove(moj_bilet)  # chyba bezpieczniejsze
    except Exception:
        pass
    with lock:
        print(f'po skasowaniu ({len(stosik)}) {stosik=}\n') if debug1 else ""


def __getTrakt(url, post=None, tickets_required=None):
    ticket = None
    try:
        if tickets_required:
            ticket = get_ticekt()
            should_continue = check_queue(ticket)
            if should_continue is False:
                del_ticekt(ticket)
                return
        #now1 = time.time()
        #fflog(f'{url=} | {post=}')
        url = urllib.urljoin(BASE_URL, url)
        post = json.dumps(post) if post else None
        headers = {
            "Content-Type": "application/json",
            "trakt-api-key": V2_API_KEY,
            "trakt-api-version": "2",
        }

        if getTraktCredentialsInfo():
            headers.update({"Authorization": "Bearer %s" % control.setting("trakt.token")})

        # r = resp_code = resp_header = result = None
        def do_requests(second_chance=False):
            #nonlocal r, resp_code, resp_header, result
            #fflog(f'{url=}')
            # fflog(f'{url=} | {post=}')
            if not post:
                r = requests.get(url, headers=headers, timeout=30)
            else:
                r = requests.post(url, data=post, headers=headers, timeout=30)
            r.encoding = "utf-8"

            resp_code = str(r.status_code)
            resp_header = r.headers
            result = r.text

            if resp_code in ["500", "502", "503", "504", "520", "521", "522", "524"]:
                #log_utils.log("Temporary Trakt Error: %s" % resp_code, log_utils.LOGWARNING)
                log_utils.log("Temporary Trakt Error: %s" % resp_code, 1)
                return r
            elif resp_code in ["404"]:
                #log_utils.log("Object Not Found : %s" % resp_code, log_utils.LOGWARNING)
                log_utils.log("Object Not Found : %s" % resp_code, 1)
                return r
            elif resp_code in ["429"]:
                #log_utils.log("Trakt Rate Limit Reached: %s" % resp_code, log_utils.LOGWARNING)
                #log_utils.log("Trakt Rate Limit Reached: %s" % resp_code, 1)
                #fflog(f"Trakt Rate Limit Reached: {resp_code=}\n{resp_header=}", 1)
                fflog(f"Trakt Rate Limit Reached: {resp_code=}", 1)
                # a może dałoby się powtórzyć żadanie za sekundę ?
                if second_chance is False:
                    RetryAfter = resp_header.get("Retry-After")
                    fflog(f'{RetryAfter=}')
                    if RetryAfter:
                        RetryAfter = int(RetryAfter)
                        control.sleep(RetryAfter*1000)
                        r = do_requests(second_chance=True)
                        pass
                else:
                    fflog('no more chance')
                    pass
            return r

        r = do_requests()

        if not r:
            if ticket:
                del_ticekt(ticket)
            return r
        if r:
            resp_code = str(r.status_code)
            resp_header = r.headers
            result = r.text            

        if resp_code not in ["401", "405"]:
            if ticket:
                del_ticekt(ticket)
            #fflog(f'DUPA {time.time() - now1} s')
            return result, resp_header

        # dalsza część jest wykonywana jak jest błąd 401 lub 405 (problem z autoryzacją)
        fflog(f'problem z autoryzacją')
        fflog(f'{resp_code=} \n {resp_header=}')
        oauth = urllib.urljoin(BASE_URL, "/oauth/token")
        opost = {
            "client_id": V2_API_KEY,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "refresh_token",
            "refresh_token": control.setting("trakt.refresh"),
        }

        result = requests.post(oauth, data=json.dumps(opost), headers=headers, timeout=30)  # logowanie
        if result:  # może jeszcze kod sprawdzać trzeba ? str(result.status_code)
            result = result.json()

            token, refresh = result["access_token"], result["refresh_token"]

            control.setSetting(id="trakt.token", value=token)
            control.setSetting(id="trakt.refresh", value=refresh)

            headers["Authorization"] = "Bearer %s" % token

            # ponowne wysłanie żądania
            #r = do_requests()  # nie testowałem jeszcze
            if not post:
                r = requests.get(url, headers=headers, timeout=30)
            else:
                control.sleep0(1000)  # AUTHED_API_POST_LIMIT: 1 call per second (chyba, że nie dotyczy, jak poprzednim była autoryzacja - nie wiem)
                r = requests.post(url, data=post, headers=headers, timeout=30)
            r.encoding = "utf-8"

            if ticket:
                del_ticekt(ticket)
            return r.text, r.headers

    except Exception as e:
        if ticket:
            del_ticekt(ticket)
        log_utils.log("Unknown Trakt Error: %s" % e, log_utils.LOGWARNING)
        fflog_exc(1)
        pass


def getTraktAsJson(url, post=None):
    try:
        r, res_headers = __getTrakt(url, post)  # może zwrócić tylko 1 zmienną (przeważnie wtedy False)
        r = utils.json_loads_as_str(r)  # tu też może się wywalić kod
        if "X-Sort-By" in res_headers and "X-Sort-How" in res_headers:
            r = sort_list(res_headers["X-Sort-By"], res_headers["X-Sort-How"], r)
        return r
    except Exception as e:
        #fflog_exc(1)
        return {}  # a jak jest gdzieś sprawdzanie czy odpowiedź is None ?
        pass


def authTrakt():
    try:
        if getTraktCredentialsInfo():
            if control.yesnoDialog(
                control.lang(32511),
                control.lang(32512),
                "",
                "Trakt",
            ):
                control.setSetting(id="trakt.user", value="")
                control.setSetting(id="trakt.token", value="")
                control.setSetting(id="trakt.refresh", value="")
            raise Exception()

        result = getTraktAsJson("/oauth/device/code", {"client_id": V2_API_KEY})
        verification_url = control.lang(32513) % result["verification_url"]
        user_code = control.lang(32514) % result["user_code"]
        expires_in = int(result["expires_in"])
        device_code = result["device_code"]

        progressDialog = control.progressDialog
        progressDialog.create("Trakt", verification_url + "\n" + user_code)

        for i in range(0, expires_in):
            try:
                if progressDialog.iscanceled():
                    break
                time.sleep(1)
                r = getTraktAsJson(
                    "/oauth/device/token",
                    {
                        "client_id": V2_API_KEY,
                        "client_secret": CLIENT_SECRET,
                        "code": device_code,
                    },
                )
                if "access_token" in r:
                    break
            except:
                pass

        try:
            progressDialog.close()
        except:
            pass

        token, refresh = r["access_token"], r["refresh_token"]

        headers = {
            "Content-Type": "application/json",
            "trakt-api-key": V2_API_KEY,
            "trakt-api-version": "2",
            "Authorization": "Bearer %s" % token,
        }

        result = client.request(urllib.urljoin(BASE_URL, "/users/me"), headers=headers)
        result = utils.json_loads_as_str(result)
        result = convert(result)

        user = result["username"]

        control.setSetting(id="trakt.user", value=user)
        control.setSetting(id="trakt.token", value=token)
        control.setSetting(id="trakt.refresh", value=refresh)
        raise Exception()
    except:
        pass


def scrobbleMovie(imdb=None, progress=None, action="pause", trakt_id=None, tmdb=None):
    """
    Send scrobble for movie to Trakt API.
    Args:
        imdb (str): IMDb ID of the movie.
        progress (float): Percent of progress.
        action (str, optional): 'start', 'pause', or 'stop'. Defaults to 'pause'.
    """
    assert False
    if getTraktIndicatorsInfo():
        if trakt_id:
            data = {"movie": {"ids": {"trakt": trakt_id}}, "progress": progress, "action": action}
        elif imdb:
            data = {"movie": {"ids": {"imdb": imdb}}, "progress": progress, "action": action}
        elif tmdb:
            data = {"movie": {"ids": {"tmdb": tmdb}}, "progress": progress, "action": action}
        url = "scrobble/" + action

        asynchro = True
        if not asynchro:
            response = __getTrakt(url, post=data)
        else:
            # twrv = ThreadWithReturnValue(target=__getTrakt, args=(url,), kwargs={"post":data, "tickets_required":True})
            # twrv.start()
            # response = twrv.join()  # ala "asynchro"
            return Thread(target=__getTrakt, args=(url,), kwargs={"post":data, "tickets_required":True}).start()

        response = response[0] if response else response  # właściwie, to ta odpowiedź nie jest do niczego potrzebna
        return response
    else:
        return None


def scrobbleEpisode(imdb=None, season=None, episode=None, progress=None, action="pause", tmdb=None, trakt_id=None):
    """
    Send scrobble for episode to Trakt API.
    Args:
        imdb (str): IMDb ID of the show.
        season (int): Season number.
        episode (int): Episode number.
        progress (float): Percent of progress.
        action (str, optional): 'start', 'pause', or 'stop'. Defaults to 'pause'.
    """
    if getTraktIndicatorsInfo():
        if imdb:
            data = {
                "show": {"ids": {"imdb": imdb}},
                "episode": {"season": season, "number": episode},
                "progress": progress,
                "action": action,
            }
        elif tmdb:
            data = {
                "show": {"ids": {"tmdb": tmdb}},
                "episode": {"season": season, "number": episode},
                "progress": progress,
                "action": action,
            }
        elif trakt_id:
            data = {
                "show": {"ids": {"trakt": trakt_id}},
                "episode": {"season": season, "number": episode},
                "progress": progress,
                "action": action,
            }
        url = "scrobble/" + action
        asynchro = True
        if not asynchro:
            response = __getTrakt(url, post=data)
        else:
            # twrv = ThreadWithReturnValue(target=__getTrakt, args=(url,), kwargs={"post":data, "tickets_required":True})
            # twrv.start()
            # response = twrv.join()
            return Thread(target=__getTrakt, args=(url,), kwargs={"post":data, "tickets_required":True}).start()
        response = response[0] if response else response  # właściwie, to ta odpowiedź nie jest do niczego potrzebna
        return response
    else:
        return None


def getMovieProgress(imdb):  # nie używane
    """
    Retrieve scrobble progress for movie from Trakt API.
    Args:
        imdb (str): IMDb ID of the movie.
    Returns:
        float: progress percent (0.0 to 100.0), or None if not found.
    """
    url = "/sync/playback/movies"
    response_text = cache.get(__getTrakt, 720, url)
    fflog(f'{response_text=}')
    if response_text:
        movies = json.loads(response_text[0])
        fflog(f'{movies=}')
    else:
        return None
    for movie in movies:
        fflog(f'{movie=}')
        if movie["movie"]["ids"]["imdb"] == imdb:
            percent = movie["progress"]
            fflog(f'{percent=}')
            return percent
    return None


def getEpisodeProgress(imdb, season, episode):  # nie używane
    """
    Retrieve scrobble progress for episode from Trakt API.
    Args:
        imdb (str): IMDb ID of the show.
        season (int): Season number.
        episode (int): Episode number.
    Returns:
        float: progress percent (0.0 to 100.0), or None if not found.
    """
    url = "/sync/playback/episodes"
    response_text = cache.get(__getTrakt, 720, url)
    if response_text:
        episodes = json.loads(response_text[0])
    else:
        return None
    for ep in episodes:
        if (
            ep["show"]["ids"]["imdb"] == imdb
            and ep["episode"]["season"] == season
            and ep["episode"]["number"] == episode
        ):
            fflog(f'{ep=}')
            percent = ep["progress"]
            fflog(f'{percent=}')
            return percent
    return None


def getTraktCredentialsInfo():
    user = control.setting("trakt.user").strip()
    token = control.setting("trakt.token")
    refresh = control.setting("trakt.refresh")
    if user == "" or token == "" or refresh == "":
        return False
    return True


def getTraktIndicatorsInfo():
    indicators = (
        control.setting("indicators")
        if getTraktCredentialsInfo() == False
        else control.setting("indicators.alt")
    )
    indicators = True if indicators == "1" else False
    return indicators


def getTraktAddonMovieInfo():
    if control.condVisibility("System.HasAddon(script.trakt)") and control.condVisibility("System.AddonIsEnabled(script.trakt)"):
        try:
            scrobble = control.addon("script.trakt").getSetting("scrobble_movie")
        except:
            scrobble = ""
        try:
            ExcludeHTTP = control.addon("script.trakt").getSetting("ExcludeHTTP")
        except:
            ExcludeHTTP = ""
        try:
            authorization = control.addon("script.trakt").getSetting("authorization")
        except:
            authorization = ""

        if scrobble == "true" and ExcludeHTTP == "false" and not authorization == "":
            return True
        else:
            return False


def getTraktAddonEpisodeInfo():
    if control.condVisibility("System.HasAddon(script.trakt)") and control.condVisibility("System.AddonIsEnabled(script.trakt)"):
        try:
            scrobble = control.addon("script.trakt").getSetting("scrobble_episode")
        except:
            scrobble = ""
        try:
            ExcludeHTTP = control.addon("script.trakt").getSetting("ExcludeHTTP")
        except:
            ExcludeHTTP = ""
        try:
            authorization = control.addon("script.trakt").getSetting("authorization")
        except:
            authorization = ""

        if scrobble == "true" and ExcludeHTTP == "false" and not authorization == "":
            return True
        else:
            return False


def manager(name, imdb, tmdb, content):
    try:
        post = (
            {"movies": [{"ids": {"imdb": imdb}}]}
            if content == "movie"
            else {"shows": [{"ids": {"tmdb": tmdb}}]}
        )

        items = []
        items += [(control.lang(32516), "/sync/collection")]
        items += [(control.lang(32517), "/sync/collection/remove")]
        items += [(control.lang(32518), "/sync/watchlist")]
        items += [(control.lang(32519), "/sync/watchlist/remove")]
        items += [(control.lang(32520), "/users/me/lists/%s/items")]

        result = getTraktAsJson("/users/me/lists")
        lists = [(i["name"], i["ids"]["slug"]) for i in result]
        lists = [lists[i // 2] for i in range(len(lists) * 2)]
        for i in range(0, len(lists), 2):
            lists[i] = (
                (control.lang(32521) % lists[i][0]),
                "/users/me/lists/%s/items" % lists[i][1],
            )
        for i in range(1, len(lists), 2):
            lists[i] = (
                (control.lang(32522) % lists[i][0]),
                "/users/me/lists/%s/items/remove" % lists[i][1],
            )
        items += lists

        """
        # ostatnia pozycja
        external_script_trakt_enabled = control.condVisibility("System.AddonIsEnabled(script.trakt)")
        if external_script_trakt_enabled:
            items += [("Oceń", "RunScript(script.trakt,action=rate)")]  # ale musi byc DBID inaczej nie zadziała
            pass
        """

        select = control.selectDialog([i[0] for i in items], control.lang(32515))

        if select == -1:
            return
        #elif external_script_trakt_enabled and select == len(items)-1:  # ostatnia pozycja
            #control.execute(items[select][1])
            #pass
        elif select == 4:
            t = control.lang(32520)
            k = control.keyboard("", t)
            k.doModal()
            new = k.getText() if k.isConfirmed() else None
            if new == None or new == "":
                return
            result = __getTrakt(
                "/users/me/lists", post={"name": new, "privacy": "private"}
            )[0]

            try:
                slug = utils.json_loads_as_str(result)["ids"]["slug"]
            except:
                return control.infoDialog(
                    control.lang(32515),
                    heading=str(name),
                    sound=True,
                    icon="ERROR",
                )
            result = __getTrakt(items[select][1] % slug, post=post)[0]
        else:
            result = __getTrakt(items[select][1], post=post)[0]

        icon = control.infoLabel("ListItem.Icon") if not result == None else "ERROR"

        control.infoDialog(
            control.lang(32515),
            heading=str(name),
            sound=True,
            icon=icon,
        )
    except:
        return


def slug(name):
    name = name.strip()
    name = name.lower()
    name = re.sub("[^a-z0-9_]", "-", name)
    name = re.sub("--+", "-", name)
    fflog(f'[slug] {name=}')
    return name


def sort_list(sort_key, sort_direction, list_data):
    reverse = False if sort_direction == "asc" else True
    if sort_key == "rank":
        return sorted(list_data, key=lambda x: x["rank"], reverse=reverse)
    elif sort_key == "added":
        return sorted(list_data, key=lambda x: x["listed_at"], reverse=reverse)
    elif sort_key == "title":
        return sorted(
            list_data,
            key=lambda x: utils.title_key(x[x["type"]].get("title")),
            reverse=reverse,
        )
    elif sort_key == "released":
        return sorted(
            list_data, key=lambda x: _released_key(x[x["type"]]), reverse=reverse
        )
    elif sort_key == "runtime":
        return sorted(
            list_data, key=lambda x: x[x["type"]].get("runtime", 0), reverse=reverse
        )
    elif sort_key == "popularity":
        return sorted(
            list_data, key=lambda x: x[x["type"]].get("votes", 0), reverse=reverse
        )
    elif sort_key == "percentage":
        return sorted(
            list_data, key=lambda x: x[x["type"]].get("rating", 0), reverse=reverse
        )
    elif sort_key == "votes":
        return sorted(
            list_data, key=lambda x: x[x["type"]].get("votes", 0), reverse=reverse
        )
    else:
        return list_data


def _released_key(item):
    if "released" in item:
        return item["released"]
    elif "first_aired" in item:
        return item["first_aired"]
    else:
        return 0


def getActivity():
    try:
        i = getTraktAsJson("/sync/last_activities")

        activity = [
            i["movies"]["collected_at"],
            i["episodes"]["collected_at"],
            i["movies"]["watchlisted_at"],
            i["shows"]["watchlisted_at"],
            i["seasons"]["watchlisted_at"],
            i["episodes"]["watchlisted_at"],
            i["lists"]["updated_at"],
            i["lists"]["liked_at"],
        ]
        #fflog(f'{activity=}')
        activity = [int(cleandate.iso_2_utc(i)) for i in activity]
        #fflog(f'{activity=}')
        activity = sorted(activity, key=int)[-1]
        #fflog(f'{activity=}')
        return activity
    except Exception:
        fflog_exc(0)
        pass


def getWatchedActivity():
    try:
        i = getTraktAsJson("/sync/last_activities")

        activity = [i["movies"]["watched_at"], i["episodes"]["watched_at"]]
        activity = [int(cleandate.iso_2_utc(i)) for i in activity]
        activity = sorted(activity, key=int)[-1]

        return activity
    except:
        pass


def cachesyncMovies(timeout=0):
    indicators = cache.get(syncMovies, timeout, control.setting("trakt.user").strip())
    return indicators


def timeoutsyncMovies():
    timeout = cache.timeout(syncMovies, control.setting("trakt.user").strip())
    return timeout


def syncMovies(user):
    try:
        if not getTraktCredentialsInfo():
            return
        indicators = getTraktAsJson("/users/me/watched/movies")
        indicators = [i["movie"]["ids"] for i in indicators]
        indicators = [str(i["imdb"]) for i in indicators if "imdb" in i]
        #fflog(f'{indicators=}')
        return indicators
    except:
        pass


def cachesyncTVShows(timeout=0):
    indicators = cache.get(syncTVShows, timeout, control.setting("trakt.user").strip())
    return indicators


def timeoutsyncTVShows():
    timeout = cache.timeout(syncTVShows, control.setting("trakt.user").strip())
    return timeout


def syncTVShows(user):
    try:
        if not getTraktCredentialsInfo():
            return
        indicators = getTraktAsJson("/users/me/watched/shows?extended=full")
        indicators = [
            (
                i["show"]["ids"]["tmdb"],
                i["show"]["aired_episodes"],
                sum(
                    [
                        [(s["number"], e["number"]) for e in s["episodes"]]
                        for s in i["seasons"]
                    ],
                    [],
                ),
            )
            for i in indicators
        ]
        indicators = [(str(i[0]), int(i[1]), i[2]) for i in indicators]
        return indicators
    except:
        pass


def syncSeason(imdb):
    try:
        if not getTraktCredentialsInfo():
            return
        indicators = getTraktAsJson(
            "/shows/%s/progress/watched?specials=false&hidden=false" % imdb
        )
        indicators = indicators["seasons"]
        indicators = [
            (i["number"], [x["completed"] for x in i["episodes"]]) for i in indicators
        ]
        indicators = ["%01d" % int(i[0]) for i in indicators if not False in i[1]]
        return indicators
    except:
        pass


def markMovieAsWatched(imdb):
    if not imdb.startswith("tt"):
        imdb = "tt" + imdb
    return __getTrakt("/sync/history", {"movies": [{"ids": {"imdb": imdb}}]})[0]


def markMovieAsNotWatched(imdb):
    if not imdb.startswith("tt"):
        imdb = "tt" + imdb
    return __getTrakt("/sync/history/remove", {"movies": [{"ids": {"imdb": imdb}}]})[0]


def markTVShowAsWatched(imdb):
    return __getTrakt("/sync/history", {"shows": [{"ids": {"imdb": imdb}}]})[0]


def markTVShowAsNotWatched(imdb):
    return __getTrakt("/sync/history/remove", {"shows": [{"ids": {"imdb": imdb}}]})[0]


def markEpisodeAsWatched(imdb, season, episode):
    season, episode = int("%01d" % int(season)), int("%01d" % int(episode))
    return __getTrakt(
        "/sync/history",
        {
            "shows": [
                {
                    "seasons": [{"episodes": [{"number": episode}], "number": season}],
                    "ids": {"imdb": imdb},
                }
            ]
        },
    )[0]


def markEpisodeAsNotWatched(imdb, season, episode):
    season, episode = int("%01d" % int(season)), int("%01d" % int(episode))
    return __getTrakt(
        "/sync/history/remove",
        {
            "shows": [
                {
                    "seasons": [{"episodes": [{"number": episode}], "number": season}],
                    "ids": {"imdb": imdb},
                }
            ]
        },
    )[0]


def getMovieTranslation(id, lang, full=False):
    url = "/movies/%s/translations/%s" % (id, lang)
    try:
        item = getTraktAsJson(url)[0]
        return item if full else item.get("title")
    except:
        pass


def getTVShowTranslation(id, lang, season=None, episode=None, full=False):
    if season and episode:
        url = "/shows/%s/seasons/%s/episodes/%s/translations/%s" % (
            id,
            season,
            episode,
            lang,
        )
    else:
        url = "/shows/%s/translations/%s" % (id, lang)

    try:
        item = getTraktAsJson(url)[0]
        return item if full else item.get("title")
    except:
        pass


def getMovieAliases(id):
    try:
        return getTraktAsJson("/movies/%s/aliases" % id)
    except:
        return []


def getTVShowAliases(id):
    try:
        return getTraktAsJson("/shows/%s/aliases" % id)
    except:
        return []


def getMovieSummary(id, full=True):
    try:
        url = "/movies/%s" % id
        if full:
            url += "?extended=full"
        return getTraktAsJson(url)
    except:
        return


def getTVShowSummary(id, full=True):
    try:
        url = "/shows/%s" % id
        if full:
            url += "?extended=full"
        return getTraktAsJson(url)
    except:
        return


def getPeople(id, content_type, full=True):
    try:
        url = "/%s/%s/people" % (content_type, id)
        if full:
            url += "?extended=full"
        return getTraktAsJson(url)
    except:
        return


def SearchAll(title, year, full=True):
    try:
        return SearchMovie(title, year, full) + SearchTVShow(title, year, full)
    except:
        return


def SearchMovie(title, year, full=True):
    try:
        url = "/search/movie?query=%s" % urllib.quote_plus(title)

        if year:
            url += "&year=%s" % year
        if full:
            url += "&extended=full"
        return getTraktAsJson(url)
    except:
        return


def SearchTVShow(title, year, full=True):
    try:
        url = "/search/show?query=%s" % urllib.quote_plus(title)

        if year:
            url += "&year=%s" % year
        if full:
            url += "&extended=full"
        return getTraktAsJson(url)
    except:
        return


def IdLookup(content, type, type_id):
    try:
        r = getTraktAsJson("/search/%s/%s?type=%s" % (type, type_id, content))
        return r[0].get(content, {}).get("ids", [])
    except:
        return {}


def getGenre(content, type, type_id):
    try:
        r = "/search/%s/%s?type=%s&extended=full" % (type, type_id, content)
        r = getTraktAsJson(r)
        r = r[0].get(content, {}).get("genres", [])
        return r
    except:
        return []




"""
class ThreadWithReturnValue(Thread):
    
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return
"""

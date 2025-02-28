"""
    FanFilm Add-on
    Copyright (C) 2024

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

try:
    import urllib.parse as urlparse
except:
    import urllib.parse as urlparse  # ??

import json
import re
import requests

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from html import unescape

from ptw.libraries import cleantitle, source_utils
from ptw.libraries import client, cache
from ptw.debug import fflog_exc, fflog


class source:
    def __init__(self):
        self.priority = 1
        self.language = ["pl"]
        self.domains = ["cda-hd.cc"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            #"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            #":authority": self.domains,  # requests.exceptions.InvalidHeader: Invalid leading whitespace, reserved character(s), or returncharacter(s) in header name: ':authority'
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pl,en-US;q=0.7,en;q=0.3", "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            }
        """
        self.search_headers = {  # to do API (już raczej nie będzie potrzebne)
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "pl,en-US;q=0.7,en;q=0.3",
            "Connection": "keep-alive",
            "Origin": "https://cda-hd.cc",
            "Referer": "https://cda-hd.cc/",
            }
        """
        self.base_link = "https://cda-hd.cc"
        self.search_link = "/?s=%s"

    """
    def contains_word(self, str_to_check, word):
        str_to_check = cleantitle.get_title(str_to_check).split()
        if word.lower() in str_to_check:
            return True
        return False


    def contains_all_words(self, str_to_check, words):
        words = list(filter(None, words))
        for word in words:
            word = cleantitle.get_title(word)
            if not word:
                continue
            if not self.contains_word(str_to_check, word):
                return False
        return True
    """

    def movie(self, imdb, title, localtitle, aliases, year):
        # fflog(f'szukanie filmu {title=} {localtitle=} {year=} {aliases=}')
        return self.do_search(title, localtitle, year, aliases)


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        # fflog(f'szukanie serialu {tvshowtitle=} {localtvshowtitle=} {year=} {aliases=}')
        return self.do_search(tvshowtitle, localtvshowtitle, year, aliases)


    def do_search(self, title, localtitle, year, aliases=None):
        try:
            if aliases:
                originalname = [a for a in aliases if "originalname" in a]
                originalname = originalname[0]["originalname"] if originalname else ""
                # fflog(f'{originalname=}')
                originalname = "" if source_utils.czy_litery_krzaczki(originalname) else originalname
            else:
                originalname = ""

            titles = [localtitle, originalname, title]
            # titles = [cleantitle.normalize(cleantitle.getsearch(t)) for t in titles]  # niepotrzebne, bo zaczął szukać uwzgledniając wszystskie znaki i nie znajduje "wydzialu", ale znajduje "wydziału"
            # fflog(f'{titles=}')

            titles = list(filter(None, titles))  # usunięcie pustych
            titles = list(dict.fromkeys(titles))  # pozbycie się duplikatów
            # fflog(f'{titles=}')

            titles_for_compare = [t.replace("⁄", "").replace(" ", "") for t in titles]  # ułamki

            # działa bez tego
            # cookies = client.request(self.base_link, output="cookie", headers=self.headers)
            # fflog(f'{cookies=}')
            # cache.cache_insert("cdahd_cookies", cookies)

            for title in titles:
                try:
                    if not title:
                        continue

                    # to chyba niepotrzebne, bo albo szukamy poprzez url albo poprzez post - a poza tym, to jakoś musi być zgodne, bo serwer sprawdza
                    # url = urlparse.urljoin(self.base_link, self.search_link)
                    # url = url % urlparse.quote_plus(cleantitle.query(title))
                    # fflog(f'{url=}')

                    data = {"s": title}
                    # fflog(f'{data=}')

                    """
                    headers = {  # jeszcze inny header ??
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
                        "Accept": "*/*",
                        "Accept-Language": "pl,en-US;q=0.7,en;q=0.3",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "X-Requested-With": "XMLHttpRequest",
                        "Origin": self.base_link,
                        "DNT": "1",
                        "Alt-Used": "vizjer.eu",
                        "Connection": "keep-alive",
                        "Referer": "https://cda-hd.cc/?s=" + title,
                        "Sec-Fetch-Dest": "empty",
                        "Sec-Fetch-Mode": "cors",
                        "Sec-Fetch-Site": "same-origin",
                        "Pragma": "no-cache",
                        "Cache-Control": "no-cache",
                        "TE": "trailers",
                        }
                    """
                    #result = client.request("https://api.searchiq.co/api/search/results?q=%s&engineKey=59344ef44ca3ca07a4bbbeb7b6ee6b38&page=0&itemsPerPage=8&group=0&autocomplete=1" % url.replace("+", "%20"), headers=self.search_headers, )

                    url = self.base_link
                    headers = self.headers
                    #result = client.request(url, headers=headers, post=data)  # to coś chyba resolvera psuło
                    result = requests.post(url, headers=headers, data=data).text  # to daje html'a
                    #fflog(f'{result=}')
                    """
                    try:
                        result = json.loads(result)
                    except:
                        result = {}
                        continue
                    #fflog(f'{result=}')
                    """

                    if "rak wynik" in result:
                        fflog(f"Brak wyników dla {title=} ({data=})")
                        continue
                    elif "ykryto niezgodność wartości" in result:
                        fflog(f"Wykryto niezgodność wartości {title=} ({data=}) {url=}")
                        continue
                    # fflog(f'{result=}')
                    try:
                        result = client.parseDOM(result, "div", attrs={"class": "peliculas"})[0]
                        res = client.parseDOM(result, "div", attrs={"class": "item_1 items"})[0]
                        rows = client.parseDOM(res, "div", attrs={"class": "item"})
                    except:
                        if "<title>Just a moment...</title>" in result:
                            fflog(f'strona schowana obecnie za Cloudflare')
                            return
                        fflog(f'wystąpił jakiś błąd')
                        fflog_exc(1)
                        continue
                        
                    # fflog(f'{len(rows)=}')
                    """
                    for row in result["main"]["records"]:  # to dla jsona
                        tytul = row["title"]
                        rok = row["ct_release-year"][0]
                    """
                    for row in rows:
                        # fflog(f'{row=}')
                        rok = client.parseDOM(row, "span", attrs={"class": "year"})[0]
                        tytul = client.parseDOM(row, "h2")[0].replace(f" ({rok})", "").rstrip()
                        tytul = unescape(tytul)
                        tytuly = tytul.split(" / ")
                        title1 = tytuly[0]
                        title2 = tytuly[-1]
                        # title1 = cleantitle.normalize(cleantitle.getsearch(title1))
                        # title2 = cleantitle.normalize(cleantitle.getsearch(title2))
                        # tak jak titles_for_compare
                        title1 = title1.replace("⁄", "").replace(" ", "")
                        title2 = title2.replace("⁄", "").replace(" ", "")
                        #words = title.split(" ")
                        #fflog(f'\n{title=} {words=} \n {cleantitle.normalize(cleantitle.getsearch(tytul))=} \n{rok=} {year=}')
                        # fflog(f'\n {rok=}  {title1=}  {title2!r}   ({tytul=})\n{year=} {titles=} \n{titles_for_compare=}')
                        if (
                            str(year) in str(rok)
                            # and self.contains_all_words(cleantitle.normalize(cleantitle.getsearch(tytul)), words)
                            # and (title1 in titles_for_compare or title2 in titles_for_compare)
                            and any(t in titles_for_compare for t in (title1, title2))
                           ):
                            #url = row["url"]
                            url = client.parseDOM(row, "a", ret="href")[0]
                            fflog(f'pasuje {url=}')
                            return url
                except Exception:
                    fflog_exc(1)
                    continue
            fflog("nic nie znaleziono")
        except Exception:
            fflog_exc(1)
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        # fflog(f'szukanie odcinka {url=} {season=} {episode=}  ({title=} {premiered=} {imdb=} {tvdb=})')
        if not url:
            return

        try:
            cookies = cache.cache_get("cdahd_cookies")["value"]
        except:
            cookies = ""
        headers = self.headers
        if cookies:
            headers["Cookie"] = cookies

        #result = client.request(url, cookie=cookies, headers=self.headers)
        result = requests.get(url, headers=headers).text
        #fflog(f'{result=}')
        """  nie wiem czy warto takimi krokami dotrzeć do celu
        try:
            seasons = client.parseDOM(result, "div", attrs={"id": "seasons"})[0]
            #fflog(f'{seasons=}')
        except:
            return
        """
        """
        # episodes = client.parseDOM(result, "div", attrs={"class": "episodiotitle"})
        # fflog(f'{len(episodes)=}')
        #episodes = client.parseDOM(episodes, "a", ret="href")  # z powodu błędu w kodzie html strony cda-hd.cc klonuje niebotycznie (z 48 zrobił 2018 linków)
        # <div>\n</li> taki jest błąd w kodzie strony
        # episodes = [e[0] for ep in episodes if (e:=client.parseDOM(ep, "a", ret="href"))]  # a to działa, ale dlatego, że interesujący link jest pierwszy w analizowanym bloku
        """
        # dlatego z powodu tego błędu trochę inaczej wyszukuje
        seasons = client.parseDOM(result, "ul", attrs={"class": "episodios"})
        # fflog(f'{len(seasons)=}')
        episodes = client.parseDOM(seasons, "a", ret="href")
        # fflog(f'{len(episodes)=} {episodes=}')
        for episode_url in episodes:
            if f"sezon-{season}-odcinek-{episode}-" in episode_url:
                # fflog(f'pasujący odcinek to {episode_url=}')
                return episode_url
        fflog("brak pasującego odcinka")


    def sources(self, url, hostDict, hostprDict):
        # fflog(f'{url=}')
        sources = []
        if url is None:
            return sources
        url0 = url
        try:
            try:
                cookies = cache.cache_get("cdahd_cookies")["value"]
            except:
                cookies = ""
            headers = self.headers
            if cookies:
                headers["Cookie"] = cookies

            #fflog(f'{url=}')
            #result = client.request(url, cookie=cookies, headers=headers)
            result = requests.get(url, headers=headers).text
            #fflog(f'{result=}')


            if "/episode/" in url:
                serial = True
                result = client.parseDOM(result, "div", attrs={"class": "player2"})

                results_player = client.parseDOM(result, "div", attrs={"class": "embed2"})
                results_player = client.parseDOM(results_player, "div")

                results_navi = client.parseDOM(result, "div", attrs={"class": "navplayer2"})
                results_navi = client.parseDOM(results_navi, "a", attrs={"href": ""})  # tylko, co mają href
                # fflog(f'{results_navi=}')
            else:
                serial = False
                results_player = client.parseDOM(result, "div", attrs={"id": "player2"})  # może to i opcjonalne
                results_player = client.parseDOM(results_player, "div", attrs={"class": "movieplay"})

                results_navi = client.parseDOM(result, "div", attrs={"class": "player_nav"})
                results_navi = client.parseDOM(results_navi, "a")

            if len(results_navi) != len(results_player):
                fflog(f'nie można kontynuować, bo {len(results_navi)=} != {len(results_player)=}')
                return sources
            else:
                # fflog(f'{len(results_navi)=} {len(results_player)=}')
                pass

            try:
                quality = client.parseDOM(result, "span", attrs={"class": "calidad2"})[0]
            except:
                quality = ""
            # fflog(f'{quality=}')
            # brak znacznika HD dla filmu może świadczyć o dubbing kino, albo 720p (np. film Istoty fantastyczne)

            i = -1
            for item in results_navi:
                try:
                    i += 1
                    #fflog(f'{item=}')
                    jezyk = item
                    jezyk = re.sub("<[^>]+>", "", jezyk)  # uzyskanie samego tekstu (w środku jest tag obrazka)
                    # fflog(f'{jezyk=}')
                    jezyk, info = self.get_lang_by_type(jezyk)
                    # fflog(f'{jezyk=} {info=}')

                    url = results_player[i]
                    # fflog(f'{url=}')
                    try:
                        url = client.parseDOM(url, "iframe", ret="src")[0]
                        url = url.replace("player.cda-hd.co/", "hqq.to/")
                    except:
                        """ do analizy działania było potrzebne
                        url = "https://hqq.to/e/226260277253228276221235209264264223194271217271255"
                        url = "https://hqq.to/player/embed_player.php?vid=226260277253228276221235209264264223194271217271255&autoplay=none&hash_from=9577577afd53ec77bbeda5ff4d30054a"
                        url = "https://hqq.to/f/FhyaHxAO5llC"
                        """
                        try:
                            if not 'src="https://player.cda-hd.co/player/hash.php?hash=' in url:
                                raise Exception()
                            # hash = re.search("(?<=hash=)\d+", url)[0]  # mniej czytelne
                            hash = re.search(r"hash=(\d+)", url)[1]
                            # url = f"https://hqq.to/player/embed_player.php?vid={hash}&hash_from=9577577afd53ec77bbeda5ff4d30054a"
                            url = f"https://hqq.to/e/{hash}"  # krótsza forma
                        except:
                            fflog(f"can't find proper url for this source")
                            continue

                    valid, host = source_utils.is_host_valid(url, hostDict)
                    # fflog(f'{valid=} {host=}')

                    unsure = None
                    # strzelanie
                    if "wysoka" in quality.lower() or quality == "HD":
                        jakosc = "HD"
                        jakosc = "1080p"
                        unsure = ["quality"]
                    elif "rednia" in quality.lower():
                        jakosc = "SD"
                    elif "niska" in quality.lower() or quality == "CAM":
                        jakosc = "CAM"
                    else:
                        jakosc = "SD"  # tylko ryzyko, że filtry mogą odrzucać, jak ktoś ustawił min 720p
                        jakosc = "HD" if serial else jakosc

                    info2 = url0.rstrip("/").rsplit("/")
                    info2 = info2[-1]

                    sources.append({"source": host,
                                    "quality": jakosc,
                                    "language": jezyk,
                                    "url": url,
                                    "info": info,
                                    "info2": info2,
                                    "direct": False,
                                    "debridonly": False})
                    if unsure:
                        sources[-1].update({"unsure": unsure})
                        pass
                except:
                    fflog_exc(1)
                    continue

            fflog(f'przekazano źródeł: {len(sources)}')
            return sources

        except Exception:
            fflog_exc(1)
            return sources


    def get_lang_by_type(self, lang_type):
        if "dubbing" in lang_type.lower():
            if "kino" in lang_type.lower():
                return "pl", "Dubbing Kino"
            return "pl", "Dubbing"
        elif "lektor pl" in lang_type.lower():
            return "pl", "Lektor"
        elif "lektor" in lang_type.lower():
            return "pl", "Lektor"
        elif "napisy pl" in lang_type.lower():
            return "pl", "Napisy"
        elif "napisy" in lang_type.lower():
            return "pl", "Napisy"
        elif "POLSKI" in lang_type.lower():
            return "pl", None
        elif "pl" in lang_type.lower():
            return "pl", None
        return "en", None

    """
    def find_url_for_source(self, url):  # to już chyba nie działa (albo było potrzebne gdy dane były z api)
        url = url.split(";")
        fflog(f'{url=}')
        data = {"action": "doo_player_ajax", "post": url[0], "nume": url[1], "type": "movie", }
        response = requests.post("https://cda-hd.cc/wp-admin/admin-ajax.php", data=data)
        fflog(f'{response=}')
        response = response.text
        fflog(f'{response=}')
        try:
            url = client.parseDOM(response, "iframe", ret="src")[0]
        except:
            fflog(f"iframe tag not found")
        fflog(f'{url=}')
        return url
    """

    def resolve(self, url):
        fflog(f'{url=}')
        return url

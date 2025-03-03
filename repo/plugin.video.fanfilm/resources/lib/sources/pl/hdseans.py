"""
    FanFilm Add-on
    Copyright (C) 2018 CherryTeam

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
import requests
import urllib.parse as urllib
from ptw.libraries import source_utils, client, cleantitle, control, cache
from ptw.debug import log_exception, fflog_exc, fflog


class source:
    def __init__(self):
        self.priority = -1
        self.language = ["pl"]
        self.domains = ["hdseans.pl"]
        self.user_name = control.setting("hdseans.username")
        self.user_pass = control.setting("hdseans.password")
        self.base_link = "https://hdseans.pl"
        self.search_link = "/autocomplete?query=%s"
        self.session = requests.Session()  # czemuś nieużywane
        self.useragent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.40 Mobile Safari/537.36"



    def contains_word(self, str_to_check, word):
        if str(word).lower() in str(str_to_check).lower():
            return True
        return False


    def contains_all_words(self, str_to_check, words):
        str_to_check2 = cleantitle.normalize(cleantitle.getsearch(str_to_check))
        for word in words:
            if not self.contains_word(str_to_check, word) and not self.contains_word(str_to_check2, word):
                return False
        return True



    def login(self):

        s = requests.session()

        s.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0"}
        # s.headers = {
        #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        #     "Accept-Language": "pl,en-US;q=0.7,en;q=0.3",
        #     "Content-Type": "application/x-www-form-urlencoded",
        #     "Origin": "https://hdseans.pl",
        #     "Connection": "keep-alive",
        #     "Referer": "https://hdseans.pl/login",
        #     "Upgrade-Insecure-Requests": "1",
        #     "TE": "Trailers",
        # }

        cookies = ""

        result = s.get("https://hdseans.pl/").text
        # fflog(f'{result=}')
        if "wyloguj" in result.lower() and not self.user_pass and not self.user_pass:
            return

        login = self.user_name
        password = self.user_pass

        if not login or not password:
            login = "xohafe7712@otozuz.com"
            password = "Kodik!100"

        # data = {
        #     "_token": token,
        #     "previous": "https://hdseans.pl/filmy",
        #     "email": login,
        #     "password": password,
        #     "remember": "on",
        # }
        my_cookies = requests.utils.dict_from_cookiejar(s.cookies)
        X_XSRF_TOKEN = my_cookies.get("X-XSRF-TOKEN", None)
        tok = re.findall(r"""['"]csrf-token['"]\s*content=['"](.+?)['"]""", result)
        s.headers.update({"X-XSRF-TOKEN": X_XSRF_TOKEN, "X-CSRF-TOKEN": tok[0]})

        data = {"email": login, "password": password, "remember": True}

        result = s.post("https://hdseans.pl/login", json=data, allow_redirects=False, verify=False)
        # result = s.post("https://hdseans.pl/login-s", headers=headers, data=data)

        cookies = "; ".join(["{}={}".format(i.name, i.value) for i in result.cookies])
        cache.cache_insert("hdseans_cookie", cookies)



    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        return (tvshowtitle, localtvshowtitle), year



    def movie(self, imdb, title, localtitle, aliases, year):
        return self.search(title, localtitle, year)


    def search(self, title, localtitle, year):
        try:
            titles = [ cleantitle.normalize(cleantitle.getsearch(title)),
                       cleantitle.normalize(cleantitle.getsearch(localtitle)) ]

            titles = list(filter(None, titles))
            titles = list(dict.fromkeys(titles))

            try:
                cookies = cache.cache_get("hdseans_cookie")["value"]
            except:
                cookies = ""
            headers = {"Cookie": cookies}

            for title in titles:
                if not title:
                    continue

                try:
                    query = self.search_link % urllib.quote_plus(title)
                    url = urllib.urlparse.urljoin(self.base_link, query)
                    result = requests.get(url, headers=headers).text
                    results = json.loads(result)
                except Exception:
                    # fflog(f'{result=}')
                    continue

                for result in results:
                    try:
                        segosurl = result["video_url"]
                        segostitle = result["title"]
                        rok = result["release_year"]
                    except:
                        continue
                    try:
                        simply_name = title.replace("  ", " ")
                        words = simply_name.split(" ")
                        if (self.contains_all_words(cleantitle.normalize(cleantitle.getsearch(segostitle)), words, )
                            and year == rok
                           ):
                            return segosurl
                        continue  # po co dawać to na końcu pętli ?
                    except:
                        continue

        except Exception as e:
            print(str(e))
            log_exception()
            return



    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        return self.search_ep(url, season, episode)


    def fix_years_for_some_titles(self, title, year):
        return (
                 "2011" if title == "Gra o tron"
            else "2015" if title == "Mr. Robot"  # nie zweryfikowałem, bo domena padła
            else year
        )


    def search_ep(self, titles, season, episode):
        try:
            cookies = cache.cache_get("hdseans_cookie")["value"]
        except:
            cookies = ""
        headers = {"Cookie": cookies}

        try:
            for title in titles[0]:
                if not title:
                    continue

                year = self.fix_years_for_some_titles(title, titles[1])
                title = cleantitle.normalize(cleantitle.getsearch(title))

                try:
                    query = self.search_link % urllib.quote_plus(title)
                    url = urllib.urlparse.urljoin(self.base_link, query)
                    result = requests.get(url, headers=headers).text
                    results = json.loads(result)
                except Exception:
                    # fflog(f'{response=}')
                    continue

                for result in results:
                    try:
                        segosurl = result["video_url"]
                        segostitle = result["title"]
                        rok = result["release_year"]
                    except:
                        continue
                    try:
                        simply_name = title.replace("  ", " ")
                        words = simply_name.split(" ")
                        if (self.contains_all_words(cleantitle.normalize(cleantitle.getsearch(segostitle)), words, )
                            and year == rok
                           ):
                            query = "/S%01d-E%01d" % (int(season), int(episode))
                            return segosurl + query
                        continue  # po co dawać to na końcu pętli ?
                    except:
                        continue
        except Exception as e:
            print(str(e))
            return



    def sources(self, url, hostDict, hostprDict):
        sources = []
        if not url:
            return sources
        try:
            self.login()
            try:
                cookies = cache.cache_get("hdseans_cookie")["value"]
            except:
                cookies = ""
            headers = {"Cookie": cookies}
            result = requests.get(url, headers=headers)
            grid = client.parseDOM(result.text, "div", attrs={"class": "watch-table__column"})
            video_links = client.parseDOM(result.text, "div", attrs={"class": "watch-table__column"}, ret="data-link", )
            for item, link in zip(grid, video_links):
                try:
                    if not link:
                        continue
                    video_result = client.parseDOM(result.text, "div",
                        attrs={"class": "watch-table__row watch-table__row--small"}, )
                    # fflog(f'{video_result=!r}')
                    language = video_result[4]
                    lang, info = self.get_lang_by_type(language)
                    quality = video_result[5]
                    quality = source_utils.check_sd_url(quality)
                    valid, host = source_utils.is_host_valid(link, hostDict)
                    sources.append({"source": host,
                                    "quality": quality,
                                    "language": lang,
                                    "url": link,
                                    "info": info,
                                    "direct": False,
                                    "debridonly": False,
                                    })
                except:
                    continue
            return sources
        except Exception as e:
            log_exception()
            return sources



    def get_lang_by_type(self, lang_type):
        if "dubbing" in lang_type.lower():
            if "kino" in lang_type.lower():
                return "pl", "Dubbing Kino"
            return "pl", "Dubbing"
        elif "napisy pl" in lang_type.lower():
            return "pl", "Napisy"
        elif "napisy" in lang_type.lower():
            return "pl", "Napisy"
        elif "lektor pl" in lang_type.lower():
            return "pl", "Lektor"
        elif "lektor" in lang_type.lower():
            return "pl", "Lektor"
        elif "POLSKI" in lang_type.lower():
            return "pl", None
        elif "pl" in lang_type.lower():
            return "pl", None
        return "en", None



    def resolve(self, url):
        if "Cookie" in url:
            headers = requests.utils.default_headers()
            return url + "&User-Agent=" + headers["User-Agent"]
        else:
            return url

"""
    FanFilm Add-on
    Copyright (C) 2017 homik

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

# from ptw.libraries import cleantitle, source_utils
# from ptw.libraries import client, cache
from ptw.libraries import cleantitle, source_utils
from ptw.libraries import client
from ptw.debug import log_exception, fflog_exc, fflog

import requests

class source:
    def __init__(self):
        self.priority = -1
        self.language = ["pl"]
        self.domains = ["vizjer.eu"]

        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            ":authority": self.domains,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pl,en-US;q=0.7,en;q=0.3", "DNT": "1", "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1", }

        self.base_link = "https://vizjer.eu"
        self.search_link = "/?s=%s"


    def contains_word(self, str_to_check, word):
        if str(word).lower() in str(str_to_check).lower():
            return True
        return False


    def contains_all_words(self, str_to_check, words):
        for word in words:
            if not self.contains_word(str_to_check, word):
                return False
        return True


    def movie(self, imdb, title, localtitle, aliases, year):
        # fflog(f'{title=} {localtitle=} {year=}')
        return self.do_search(title, localtitle, year)


    def do_search(self, title, local_title, year):
        try:
            titles = [cleantitle.normalize(cleantitle.getsearch(title)),
                cleantitle.normalize(cleantitle.getsearch(local_title)), ]

            for title in titles:
                try:
                    url = urlparse.urljoin(self.base_link, self.search_link)
                    url = url % urlparse.quote_plus(cleantitle.query(title))
                    data = {"s": title}
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
                        "Accept": "*/*", "Accept-Language": "pl,en-US;q=0.7,en;q=0.3",
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "X-Requested-With": "XMLHttpRequest", "Origin": "https://vizjer.eu", "DNT": "1",
                        "Alt-Used": "vizjer.eu", "Connection": "keep-alive",
                        "Referer": "https://vizjer.eu/?s=" + title, "Sec-Fetch-Dest": "empty",
                        "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-origin", "Pragma": "no-cache",
                        "Cache-Control": "no-cache", "TE": "trailers", }
                    #result = client.request(self.base_link, headers=headers, post=data)
                    result = requests.post(self.base_link, headers=headers, data=data).text
                    # fflog(f'{result=}')
                    results = client.parseDOM(result, "div", attrs={"class": "result-item"})
                    for row in results:
                        # fflog(f'{row=}')
                        name = client.parseDOM(row, "div", attrs={"class": "title"})[0]
                        if "<a href=" in name:
                            name = client.parseDOM(name, "a")[0]
                        name = cleantitle.normalize(cleantitle.getsearch(name))
                        rok = client.parseDOM(row, "span", attrs={"class": "year"})[0]
                        words = title.split(" ")
                        # fflog(f'{name=} {words=} {year=} {rok=}')
                        if self.contains_all_words(name, words) and str(year) in str(rok):
                            url = client.parseDOM(row, "a", ret="href")[0]
                            # fflog(f'pasujący {url=}')
                            return url
                except Exception as e:
                    fflog_exc(1)
                    continue
        except Exception:
            fflog_exc(1)
            return


    def sources(self, url, hostDict, hostprDict):
        # fflog(f'{url=}')
        sources = []
        try:
            if url is None:
                fflog(f'brak źródeł')
                return sources
            sources = []

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "pl,en-US;q=0.7,en;q=0.3", "Referer": "https://vizjer.eu/?s=test",
                "DNT": "1", "Alt-Used": "vizjer.eu", "Connection": "keep-alive", "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1", "Pragma": "no-cache", "Cache-Control": "no-cache", }
            #result = client.request(url, headers=headers)
            result = requests.get(url, headers=headers)
            # fflog(f'0 {result=}')
            result = result.text
            # fflog(f'1 {result=}')
            result = client.parseDOM(result, "table", attrs={"class": "table table-bordered"})
            # fflog(f'2 {result=}')
            result = client.parseDOM(result, "tbody")[0]
            # fflog(f'3 {result=}')
            result = client.parseDOM(result, "tr")
            # fflog(f'4 {result=}')
            for item in result:
                try:
                    # fflog(f'{item=}')
                    item2 = client.parseDOM(result, "td")
                    jezyk = item2[2]
                    jezyk, info = self.get_lang_by_type(jezyk)
                    quality = item2[3]
                    url = client.parseDOM(item, "a", ret="href")[0]
                    valid, host = source_utils.is_host_valid(url, hostDict)
                    if "wysoka" in quality.lower():
                        sources.append({"source": host, "quality": "HD", "language": jezyk, "url": url, "info": info,
                            "direct": False, "debridonly": False, })
                    elif "rednia" in quality.lower():
                        sources.append({"source": host, "quality": "SD", "language": jezyk, "url": url, "info": info,
                            "direct": False, "debridonly": False, })
                    elif "niska" in quality.lower():
                        sources.append({"source": host, "quality": "SD", "language": jezyk, "url": url, "info": info,
                            "direct": False, "debridonly": False, })
                    else:
                        sources.append({"source": host, "quality": "SD", "language": jezyk, "url": url, "info": info,
                            "direct": False, "debridonly": False, })
                except:
                    continue

            fflog(f'przekazano źródeł: {len(sources)}')
            return sources

        except:
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


    def resolve(self, url):
        return url

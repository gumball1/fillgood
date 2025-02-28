# -*- coding: UTF-8 -*-


"""
    FanFilm Project
"""

import re
from urllib.parse import parse_qs, urljoin, urlparse, urlencode

from ptw.libraries import cfScraper
from ptw.libraries import cleantitle, client, debrid, log_utils, source_utils
from ptw.libraries import custom_base_link

custom_base = custom_base_link(__name__)


class source:
    def __init__(self):
        self.priority = 1
        self.language = ["en"]
        self.domains = ["rlsbb.ru", "rlsbb.to", "releasebb.net", "proxybb.com", ]  # cf: 'rlsbb.unblockit.ch'
        self.base_link = custom_base  # or 'https://rlsbb.to'  # self.search_base_link = 'http://search.rlsbb.ru'  # self.search_cookie = 'serach_mode=rlsbb'  # self.search_link = 'lib/search526049.php?phrase=%s&pindex=1&content=true'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {"imdb": imdb, "title": title, "year": year}
            url = urlencode(url)
            return url
        except:
            log_utils.log("RLSBB - Exception", "sources")
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {"imdb": imdb, "tvdb": tvdb, "tvshowtitle": tvshowtitle, "year": year}
            url = urlencode(url)
            return url
        except:
            log_utils.log("RLSBB - Exception", "sources")
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url is None:
                return

            url = parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, "") for i in url])
            url["title"], url["premiered"], url["season"], url["episode"] = (title, premiered, season, episode,)
            url = urlencode(url)
            return url
        except:
            log_utils.log("RLSBB - Exception", "sources")
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:

            if url is None:
                return sources

            if debrid.status() is False:
                return sources

            hostDict = hostprDict + hostDict

            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, "") for i in data])
            title = data["tvshowtitle"] if "tvshowtitle" in data else data["title"]
            year = (re.findall("(\d{4})", data["premiered"])[0] if "tvshowtitle" in data else data["year"])
            title = cleantitle.get_query(title)
            hdlr = ("S%02dE%02d" % (int(data["season"]), int(data["episode"])) if "tvshowtitle" in data else year)
            # premDate = ''

            query = ("%s S%02dE%02d" % (
            title, int(data["season"]), int(data["episode"])) if "tvshowtitle" in data else "%s %s" % (title, year))
            query = re.sub("(\\\|/| -|:|;|\*|\?|\"|'|<|>|\|)", "", query)
            query = query.replace(" ", "-")
            # query = self.search_link % quote_plus(query)

            if int(year) < 2021:
                for i, d in enumerate(self.domains):
                    self.domains[i] = "old3." + d
                self.base_link = None

            r, _base_link = client.list_request(self.base_link or self.domains, query)

            if not r and "tvshowtitle" in data:
                season = re.search("S(.*?)E", hdlr)
                season = season.group(1)
                query = title
                query = re.sub("(\\\|/| -|:|;|\*|\?|\"|'|<|>|\|)", "", query)
                query = query + "-S" + season
                query = query.replace("&", "and")
                query = query.replace("  ", " ")
                query = query.replace(" ", "-")
                r, _base_link = client.list_request(self.base_link or self.domains, query)

            for loopCount in range(0, 2):
                if loopCount == 1 or (r is None and "tvshowtitle" in data):
                    # premDate = re.sub('[ \.]', '-', data['premiered'])
                    query = re.sub(r'[\\:;*?"<>|/\-\']', "", title)
                    query = (query.replace("&", " and ").replace("  ", " ").replace(" ",
                                                                                    "-"))  # throw in extra spaces around & just in case
                    # query = query + "-" + premDate

                    url = urljoin(_base_link, query)
                    url = url.replace("The-Late-Show-with-Stephen-Colbert", "Stephen-Colbert")

                    r = cfScraper.get(url).text

                posts = client.parseDOM(r, "div", attrs={"class": "content"})
                items = []
                for post in posts:
                    try:
                        u = client.parseDOM(post, "a", ret="href")
                        for i in u:
                            try:
                                name = str(i)
                                if hdlr in name.upper():
                                    items.append(
                                        name)  # elif len(premDate) > 0 and premDate in name.replace(".", "-"):  # items.append(name)
                            except:
                                pass
                    except:
                        pass

                if len(items) > 0:
                    break

            seen_urls = set()

            for item in items:
                try:
                    url = str(item)
                    url = client.replaceHTMLCodes(url)

                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    host = url.replace("\\", "")
                    host2 = host.strip('"')
                    host = re.findall("(\w+[.]\w+)$", urlparse(host2.strip().lower()).netloc)[0]

                    if host not in hostDict:
                        continue
                    if any(x in host2 for x in [".rar", ".zip", ".iso", ".part"]):
                        continue

                    quality, info = source_utils.get_release_quality(host2)

                    info = " | ".join(info)

                    sources.append({"source": host, "quality": quality, "language": "en", "url": host2, "info": info,
                        "direct": False, "debridonly": True, })
                except:
                    log_utils.log("RLSBB - Exception", "sources")
                    pass
            check = [i for i in sources if not i["quality"] == "cam"]
            if check:
                sources = check
            return sources
        except:
            log_utils.log("RLSBB - Exception", "sources")
            return sources

    def resolve(self, url):
        return url

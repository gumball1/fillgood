# -*- coding: utf-8 -*-

"""
    FanFilm Project
"""

import re
from urllib.parse import urlencode, parse_qs, urljoin

from ptw.libraries import client
from ptw.libraries import directstream
from ptw.libraries import log_utils
from ptw.libraries import source_utils

direct_stream = tuple(source_utils.supported_video_extensions())


class source:
    def __init__(self):
        self.priority = 1
        self.language = ["en"]
        self.domains = ["v2.apimdb.net"]
        self.base_link = "https://v2.apimdb.net"
        self.search_link = "/e/movie/%s"
        self.search_link2 = "/e/tv/%s/%s/%s"

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {"imdb": imdb, "title": title, "year": year}
            url = urlencode(url)
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {"imdb": imdb, "tvdb": tvdb, "tvshowtitle": tvshowtitle, "year": year}
            url = urlencode(url)
            return url
        except:
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
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if url is None:
                return sources
            hostDict = hostprDict + hostDict

            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, "") for i in data])

            if not data["imdb"] or data["imdb"] == "0":
                return sources

            if "tvshowtitle" in data:
                query = self.search_link2 % (data["imdb"], data["season"], data["episode"],)
            else:
                query = self.search_link % data["imdb"]

            url = urljoin(self.base_link, query)
            posts = client.r_request(url)
            urls = client.parseDOM(posts, "div", attrs={"class": "server"}, ret="data-src")
            urls = [urljoin(self.base_link, url) if url.startswith("/") else url for url in urls]
            # log_utils.log('apimdb_urls: ' + repr(urls))
            for url in urls:
                try:
                    # pattern = r'%s/%s/%s/(.+?)/apimdb.' % (data['imdb'], data['season'], data['episode']) if 'tvshowtitle' in data else r'%s/(.+?)/apimdb.' % data['imdb']
                    # host = re.findall(pattern, url)[0]
                    host = re.findall(r"playS/(.+?)/", url)[0]
                    if "-drive" in host:
                        host = "cdn"
                    # log_utils.log('apimdb_url0: ' + repr(url) + ' | host: ' + repr(host))
                    valid, host = source_utils.is_host_valid(host, hostDict)
                    if valid:
                        sources.append({"source": host, "quality": "720p", "language": "en", "info": "", "url": url,
                            "direct": False, "debridonly": False, })
                    elif any(h in host for h in ["googledrive2", "googledrive9", "vip-", "hls-"]):
                        r = client.r_request(url)
                        # log_utils.log('apimdb_r: ' + r)
                        links = re.findall(r"""(?:src|file)[:=]\s*['"]([^"']+)""", r)
                        # log_utils.log('apimdb_links: ' + repr(links))
                        for url in links:
                            if url.startswith("http"):
                                # log_utils.log('apimdb_url1: ' + repr(url))
                                valid, host = source_utils.is_host_valid(url, hostDict)
                                if valid:
                                    direct = (True if url.endswith(direct_stream) else False)
                                    sources.append({"source": host, "quality": "720p", "language": "en", "url": url,
                                        "direct": direct, "debridonly": False, })
                                elif "/hls/" in url or url.endswith(direct_stream):
                                    # log_utils.log('apimdb_url1: ' + repr(url))
                                    sources.append({"source": host, "quality": "720p", "language": "en", "url": url,
                                        "direct": True, "debridonly": False, })
                except:
                    log_utils.log("apimdb sources1 - Exception", "sources")
                    pass
            return sources
        except:
            log_utils.log("apimdb sources - Exception", "sources")
            return sources

    def resolve(self, url):
        # log_utils.log('apimdb_rurl0: ' + repr(url))
        if "apimdb" in url:
            r = client.r_request(url)
            links = re.findall(r"""(?:src|file)[:=]\s*['"]([^"']+)""", r)
            url = [u for u in links if u.startswith("http")][0]  # log_utils.log('apimdb_rurl: ' + repr(url))
        if "google" in url and not url.endswith(direct_stream):
            url = directstream.googlepass(url)  # log_utils.log('apimdb_rur2: ' + repr(url))
        return url

# -*- coding: utf-8 -*-
"""
    FanFilm Add-on
    Copyright (C) 2018 :)

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



from urllib.parse import quote
import requests
from datetime import date
import time
from hashlib import md5

from ptw.libraries import source_utils
from ptw.libraries import cleantitle
from ptw.libraries import control
from ptw.libraries import cache
from ptw.libraries import apis
from ptw.debug import log, log_exception



class source:
    def __init__(self):
        self.priority = -1
        self.language = ["pl"]
        self.domains = ["filser"]
        self.base_link = f"https://filser.cc{{}}"
        self.api_link = f"https://filser.cc/api/watch/{{id}}/{{s}}/{{e}}"
        self.login_link = "https://filser.cc/api/account/login"
        self.search_link = f"https://filser.cc/api/search/?q={{query}}&sort=ratingcount&type={{content}}" \
                           f"&year_from={{year_start}}&year_to={{year_end}}"
        self.user_name = control.setting("filser.username")
        self.user_pass = control.setting("filser.password")
        self.COOKIE = 'filser_cookie'
        self.api_key = apis.fliser_api_key
        self.session = requests.session()
        self.HDR = self.make_hdr()

    def get_json(self, url):
        return self.session.get(url, headers=self.HDR).json()

    def make_hdr(self):
        key = self.hash_md5(self.api_key + str(date.today()))
        HDR = {"api-key": key}
        return HDR

    def login(self):
        data = {"email": self.user_name,
                "password": self.user_pass}
        r = self.session.post(self.login_link, headers=self.HDR, data=data, allow_redirects=False)
        cookie = r.cookies.get_dict()
        if 'remember_login' in cookie.keys():
            cookie = "; ".join([f'{k}={v}' for k, v in cookie.items()])
            cache.cache_insert(self.COOKIE, cookie)
            return True
        log(f'[filser.py] logowanie nie powiodło się')
        return False

    def get_cookie(self):
        now = int(time.time())
        exp = 1209600  # 14 days cookie valid
        self.cached_cookie = cache.cache_get(self.COOKIE)
        if self.cached_cookie:
            if now - self.cached_cookie['date'] > exp:
                return self.login()
            return True
        else:
            return self.login()

    def search(self, title, localtitle, year, content):
        self.login_success = self.get_cookie()
        if self.login_success:
            try:
                titles = []
                titles.append(cleantitle.normalize(cleantitle.getsearch(title)))
                titles.append(cleantitle.normalize(cleantitle.getsearch(localtitle)))

                for title in titles:
                    if not title:
                        continue
                    try:
                        url = self.search_link.format(query=quote(title), content=content,
                                                      year_start=year, year_end=year)
                        result = self.get_json(url)
                        res_list = result['full'] + result['splitted']
                        for t in res_list:
                            if cleantitle.normalize(cleantitle.getsearch(t.get("title_name"))):
                                return t
                    except Exception as e:
                        continue

            except Exception as e:
                log_exception()
                return None
        else:
            return None

    def movie(self, imdb, title, localtitle, aliases, year):
        res = self.search(title, localtitle, year, 'movie')
        if res:
            id = res['title_id']
            res.update({'watch_link': self.api_link.format(id=id, s=1, e=1)})
        return res

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        res = self.search(tvshowtitle, localtvshowtitle, year, 'show')
        return res

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        if url:
            id = url['title_id']
            url.update({'watch_link': self.api_link.format(id=id, s=season, e=episode)})
        return url

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if url == None:
                return sources

            results = self.get_json(url['watch_link'])

            for item in results['links']:

                if item.get('label'):
                    continue
                try:
                    link = item['name']
                    valid, host = source_utils.is_host_valid(link, hostDict)
                    sources.append(
                        {
                            "source": host,
                            "quality": item['quality'],
                            "language": "pl",
                            "url": self.base_link.format(item['link']),
                            "info": item['lang'],
                            "direct": False,
                            "debridonly": False,
                        }
                    )
                except:
                    continue
            return sources
        except:
            log_exception()
            return sources

    def resolve(self, url):
        r = self.session.get(url, headers=self.HDR).url
        return r

    def hash_md5(self, string):
        md = md5(string.encode('utf-8'))
        return md.hexdigest()

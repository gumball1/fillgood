# -*- coding: utf-8 -*-
"""
    FanFilm Add-on
    Copyright (C) 2024 :)

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

from ptw.libraries import source_utils, cleantitle, control, cache
from ptw.debug import log_exception, fflog_exc, fflog
from ast import literal_eval
import requests
import hashlib
import hmac
import base64
import re
import json
import time
from difflib import SequenceMatcher


class source:
    def __init__(self):
        self.priority = 1
        self.language = ["pl"]
        # self.domains = ["cda.pl"]
        self.base_link = "https://api.cda.pl"
        self.search_link = f"{self.base_link}/video/search"
        # self.search_link = f"{self.base_link}/video/show"
        self.session = requests.Session()

        self.email = ""
        self.passwd_ctrl = ""
        self.passwd_hash = ""
        self.passwd = ""

        """
        self.useragent = "pl.cda 1.0 (version 1.2.255 build 21541; Android 9; Samsung SM-G935F)"
        self.headers = {'User-Agent': self.useragent,
                        'Accept': 'application/vnd.cda.public+json',
                        'Accept-Encoding': 'gzip',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Host': 'api.cda.pl'
                        }
        """
        self.headers = {
                        'User-Agent':'pl.cda.tv 1.0 (version 1.2.20 build 10619; Android 8.0.0; Unknown sdk_google_atv_x86)',
                        'Accept': 'application/vnd.cda.public+json',
                        'Host': 'api.cda.pl',}

        # takie dziwne zapisy
        self.year = 0
        self.anime = False
        self.duration = 20 * 60  # chyba później zmieniane jest na "medium" (srednie)


    def hash_password(self, passwd):
        passw = passwd.encode('utf-8')
        md5 = hashlib.md5(passw).hexdigest()
        salt = "s01m1Oer5IANoyBXQETzSOLWXgWs01m1Oer5bMg5xrTMMxRZ9Pi4fIPeFgIVRZ9PeXL8mPfXQETZGUAN5StRZ9P"
        salt = salt.encode('utf-8')
        md5 = md5.encode('utf-8')
        hash = base64.b64encode(hmac.new(salt, md5, digestmod=hashlib.sha256).digest())
        hash = hash.decode('utf-8')
        return hash.replace("/", "_").replace("+", "-").replace("=", "")


    def check_email(self, email):
        fflog(f'sprawdzenie, czy istnieje zadany email (jako login)')
        data = {
            'email': email
        }
        self.headers.update({'Authorization': 'Basic YzU3YzBlZDUtYTIzOC00MWQwLWI2NjQtNmZmMWMxY2Y2YzVlOklBTm95QlhRRVR6U09MV1hnV3MwMW0xT2VyNWJNZzV4clRNTXhpNGZJUGVGZ0lWUlo5UGVYTDhtUGZaR1U1U3Q'})
        url = f'{self.base_link}/register/check-email'
        exist = self.session.post(url, data=data, headers=self.headers)  # wysłanie do serwera
        # fflog(f'{exist=}  {url=}  {data=}  {self.headers=}')
        if exist:
            try:
                exist = exist.json()
            except Exception:
                exist = ""
                pass
        fflog(f'{exist=}')
        if exist:
            return True
        else:
            return False


    def getProfileInfo(self):
        self.headers.update({'Authorization': f'Bearer {cache.cache_get("cdaprem_token")["value"]}'})
        url = f'{self.base_link}/user/me/premium'
        response2 = self.session.get(url, headers=self.headers).json()
        fflog(f' {response2=}')
        status = response2.get('status')
        if status.get('premium',None) == 'tak':
            wygasa = status.get('wygasa')
            stat = 'premium do '+ str(wygasa)
        else:
            stat = 'standard'
        fflog(f'typ {stat=}')


    def oauth(self, email, passwd):
        import time

        if not self.email:
            email = self.email = control.setting("cdapremium.username")
            self.passwd_ctrl = control.setting("cdapremium.password")
            if self.passwd_ctrl:
                self.passwd = self.hash_password(self.passwd_ctrl)
                self.passwd_hash = control.setSetting('cdapremium.password_hashed', self.passwd)
                control.setSetting("cdapremium.password", "")
            else:
                self.passwd = control.setting("cdapremium.password_hashed")
            passwd = self.passwd

        # cdaprem_token = cache.cache_get("cdaprem_token")
        cdaprem_token = cache.cache_get("cdaprem_expires_in")
        if cdaprem_token:
            cdaprem_token_date = cdaprem_token["date"]
            now = int(time.time())
            delta_t = now - int(cdaprem_token_date)
            try:
                # expires_in = int(cache.cache_get("cdaprem_expires_in")["value"])  # powinno być 86400 (24 godz.)
                expires_in = int(cdaprem_token["value"])
            except Exception:
                expires_in = 0
            # fflog(f'{expires_in=}')
            # delta_t = 0  # dla testów tylko
            if delta_t < expires_in:
                # cdaprem_token = cdaprem_token["value"]
                if cdaprem_token:
                    return True
                    pass

        if not email:
            fflog("Nie wprowadzono danych do zalogowania")
            return

        # if self.check_email(email):  # po co robić dodatkowy request ?
        if True:
            fflog(f'podjęcie próby uwierzytelnienia (zalogowania)')
            payload = {
                'grant_type': 'password',
                'login': email,
                'password': passwd
            }
            # self.headers.update({'Authorization': 'Basic YzU3YzBlZDUtYTIzOC00MWQwLWI2NjQtNmZmMWMxY2Y2YzVlOklBTm95QlhRRVR6U09MV1hnV3MwMW0xT2VyNWJNZzV4clRNTXhpNGZJUGVGZ0lWUlo5UGVYTDhtUGZaR1U1U3Q'})
            self.headers.update({'Authorization': 'Basic YmZjMDYyNDAtOTFkZi00MGYzLWFhMjEtZjc4MTBiZjgxYzYyOldFQ3NSQ0VEY0tLZzVHYkxuTHdiZEppMElQakJkSG45dzlTVUhjbjZsR2t2dU9uN2wya1NiZWhmeVZEWEZwR3c'})
            url = f'{self.base_link}/oauth/token'
            user = self.session.post(url, data=payload, headers=self.headers)
            if user:
                user = user.json()
            else:
                fflog(f'wystąpił jakiś błąd  {user=}')
                user = {}
            # fflog(f'{user=}\n  {url=}  \n{payload=}  \n{self.headers=}')
            if user.get('access_token'):
                # fflog(f'{user=}')
                a_token = user['access_token']
                # r_token = user.get('refresh_token')  # nie wiem, do czego to
                expires_in = user.get('expires_in', 0)
                # wstawienie do bazy
                cache.cache_insert("cdaprem_token", a_token)
                # cache.cache_insert("cdaprem_refresh_token", r_token  # do czego ten token służy ?
                cache.cache_insert("cdaprem_expires_in", expires_in)  # 86400 (24 godz.)
                fflog(f'zalogowano poprawnie')
                # profil = self.getProfileInfo()
                # control.sleep(1000)
                return True
            else:
                fflog(f'zalogowanie nie powiodło się {user=}')
                return False
        else:
            fflog(f'weryfikacja emaila (loginu) negatywna')  # jak jest sprawdzany, bo chcę z tego zrezygnować
            pass


    def get_originaltitle(self, aliases):
        if aliases:
            originalname = [a for a in aliases if "originalname" in a]
            originalname = originalname[0]["originalname"] if originalname else ""
            # fflog(f'{originalname=}')
            originalname = "" if source_utils.czy_litery_krzaczki(originalname) else originalname
            return originalname
        return ""


    def movie(self, imdb, title, localtitle, aliases, year):
        # fflog(f'rozpoczęcie szukanie filmu {title=} {localtitle=} {year=}  {imdb=}')
        # jeszcze wyłuskać tytuł oryginalny można spróbować (choć nie wiem, czy warto)
        return self.search(title, localtitle, self.get_originaltitle(aliases), year, True)


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        # fflog(f'rozpoczęcie szukanie serialu {tvshowtitle=} {localtvshowtitle=} {year=}  {imdb=}')
        return (tvshowtitle, localtvshowtitle, self.get_originaltitle(aliases)), year


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        # fflog(f'rozpoczęcie szukanie odcinka {season=} {episode=} dla serialu {title=}  {imdb=}')
        epNo = ""
        self.year = int(url[1])
        anime = False
        """
        anime = source_utils.is_anime("show", "tvdb", tvdb)
        self.anime = anime
        # fflog(f'{anime=}')
        """
        if anime:
            epNo = source_utils.absoluteNumber(tvdb, episode, season)
        if not epNo:
            epNo = "s" + season.zfill(2) + "e" + episode.zfill(2)
        # fflog(f'{epNo=}')
        return self.search_ep(url[0][0], url[0][1], url[0][2], self.year, premiered, epNo, season, episode)


    def contains_all_words(self, str_to_check, words):
        if self.anime:
            words_to_check = str_to_check.split(" ")
            for word in words_to_check:
                try:
                    liczba = int(word)
                    for word2 in words:
                        try:
                            liczba2 = int(word2)
                            if (liczba != liczba2 and liczba2 != self.year and liczba != self.year):
                                return False
                        except:
                            continue
                except:
                    continue

        str_to_check = cleantitle.get_title(str_to_check).split()
        words = list(filter(None, words))
        if not words:
            fflog(f'{words=}')
            raise Exception("Błąd", "zmienna nie może być pusta")
        for word in words:
            word = cleantitle.get_title(word)
            if not word:
                continue
            if not word in str_to_check:
                return False
        return True


    def similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio()
    

    def levenshtein(self, s, t):
        ''' From Wikipedia article; Iterative with two matrix rows. '''
        if s == t: return 0
        elif len(s) == 0: return len(t)
        elif len(t) == 0: return len(s)
        v0 = [None] * (len(t) + 1)
        v1 = [None] * (len(t) + 1)
        for i in range(len(v0)):
            v0[i] = i
        for i in range(len(s)):
            v1[0] = i + 1
            for j in range(len(t)):
                cost = 0 if s[i] == t[j] else 1
                v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
            for j in range(len(v0)):
                v0[j] = v1[j]
        return v1[len(t)]


    def getDuration(self):
        # control.log(f"{control.infoLabel('ListItem.Duration')=}", 1)
        # fflog(f"{control.infoLabel('ListItem.Duration')=}")
        # fflog(f"{control.infoLabel('ListItem.Duration(mins)')=}")
        # fflog(f"{control.infoLabel('ListItem.Duration(secs)')=}")
        duration_expected = control.infoLabel('ListItem.Duration(secs)')
        # fflog(f'L: {duration_expected=}')

        if not duration_expected:
            meta = control.window.getProperty("plugin.video.fanfilm.container.meta")
            try:
                meta = json.loads(meta)
            except Exception:
                # fflog_exc()
                meta = {}
            # fflog(f'{meta=}')
            duration_expected = meta.get("duration")
            # fflog(f'M: {duration_expected=}')

        if not duration_expected:
            zmienne = control.window.getProperty('FanFilm.var.curr_item_p')
            # fflog(f'{zmienne=}')
            try:
                zmienne = literal_eval(zmienne)
            except Exception:
                # fflog_exc(1)
                zmienne = {}
            # fflog(f'{zmienne=}')
            imdb = zmienne.get("imdb")
            tmdb = zmienne.get("tmdb")
            # fflog(f'{tmdb=} {imdb=}')
            episode = zmienne.get("episode")
            if not episode:
                meta = cache.cache_get("superinfo" + f"_{tmdb or imdb}")
            else:
                season = zmienne.get("season")
                if season or season == 0:
                    meta = cache.cache_get("episodes" + f"_{tmdb or imdb}_s{season}")
                else:
                    meta = cache.cache_get("episodes" + f"_{tmdb or imdb}")
                if not meta:
                    from resources.lib.indexers import episodes
                    meta = episodes.episodes().tmdb_list(imdb=imdb, tmdb=tmdb, season=season)
            # fflog(f'{meta=}')
            if meta:
                if "value" in meta:
                    meta = meta["value"]
                    meta = literal_eval(meta)
                if episode:
                    meta = meta[int(episode)-1]
                duration_expected = meta.get("duration") or 0  # tu jest w minutach
                duration_expected = int(duration_expected) * 60  # na sekundy
                # fflog(f'C: {duration_expected=}')

        duration_expected = int(duration_expected) if duration_expected else 0
        duration_expected = duration_expected if duration_expected > 5*60 else 0  # 5 minut
        # fflog(f'E: {duration_expected=}')
        return duration_expected


    def search(self, title, localtitle, originaltitle, year, is_movie_search):
        if self.oauth(self.email, self.passwd):
            # fflog(f'szukanie pasujących {title=} {localtitle=} {originaltitle=} {is_movie_search=}')

            title, localtitle = localtitle, title  # zamianka

            titles = [cleantitle.normalize(cleantitle.getsearch(title)),
                      cleantitle.normalize(cleantitle.getsearch(localtitle)),
                      cleantitle.normalize(cleantitle.getsearch(originaltitle)),
                     ]
            # fflog(f'{titles=}')

            # titles = [title, localtitle] 

            titles = list(filter(None, titles))  # usunięcie pustych
            titles = list(dict.fromkeys(titles))  # pozbycie się ewentualnych duplikatów

            # titles = [localtitle]
            # titles = [title]
            # fflog(f'{titles=}')

            banned_words = ["zwiastun", "trailer", "recenzja", "omowienie", "gameplay", "nazywo", "walktrough", "stream", "opis", "newsy"]

            duration_expected = self.getDuration()

            items = []

            for title in titles:
                # fflog(f'{title=}')
                q_title = title.replace("'", "").replace(":", "").replace("-", " ").lower()
                data = {
                    'query': q_title,
                    'duration': 'medium',  # zastanowić się, czy dla filmów nie zmienić na "długie" (tylko nie wiem jak to jest w api, może "long"?) (długie, to powyżej 60 min chyba)
                    'page': 1,
                    'limit': 200,
                    'sort': 'best',
                }
                self.headers.update({'Authorization': f'Bearer {cache.cache_get("cdaprem_token")["value"]}'})
                # fflog(f'{data=}')
                search = self.session.get(self.search_link, params=data, headers=self.headers)
                # fflog(f'{search=}')
                if search:
                    search = search.json()
                else:
                    fflog(f'jakiś błąd serwera {search=}')

                if search and len(search.get('data')):
                    # fflog(f'{search=}')

                    # given_name = cleantitle.normalize(title).lower()
                    # given_name = cleantitle.normalize(cleantitle.getsearch(title))  # to robię na początku dla każdego tytułu
                    given_name = title

                    banned_words2 = [word for word in banned_words if word not in given_name]

                    title1 = title

                    title1 = title1.replace(".", " ")
                    title1 = title1.replace("the ", " ")
                    title1 = title1.replace("  ", " ").strip()
                    words = title1.split(" ")
                    # fflog(f'{title1=} {words=}')

                    # fflog(f"{len(search.get('data'))=}")
                    for item in search.get('data'):
                        # fflog(f'{item=} | zadany {year=}')

                        if item['id'] in [i[0] for i in items]:
                            # fflog(f'już jest takie źródło w źródłach')
                            continue

                        # ewentualnie dać jako ostatnie
                        if duration_expected and (duration := item.get("duration")) and abs(duration_expected - duration) > 11*60:  # "żandarm na emeryturze" rozbieżność 11 minut
                            # fflog(f'odrzucone z powodu niepasującego czasu trwania  {duration_expected=}  {duration=}  {item=}')
                            continue
                            pass

                        finded_name = item['title']

                        finded_name = re.sub(r'\[.*?\]', '', finded_name).strip()  #  dla takich 'Dark Matter [WEB-DL. x264-NoNaNo][Lektor PL]'

                        finded_name = cleantitle.normalize(cleantitle.getsearch(finded_name))

                        if any(bw in finded_name for bw in banned_words2):
                            # fflog(f'odrzucenie z powodu wykrytych pewnych wyrazów  {item=}')
                            continue
                            pass

                        if year:
                            finded_name = finded_name.split(year)[0].strip()  # a jak jest zły rok ?

                        # wycięcie pewnych fraz
                        # (trudność polega na przewidzeniu wszystkich możliwości)
                        finded_name = re.sub(
                            r" *\b(lektor|subbed|napisy|dubbing|polish|po?l(dub|sub)?|us|fr|de|dual|multi|p2p|web[.-]?dl|remux|3d|imax)\b",
                            # "",
                            lambda x: x[0] if re.search(fr"\b{re.escape(x[0])}\b", title, flags=re.I) else "",  # aby nie usuwać tych fraz, które są w tytule (np. serial Office.PL)
                            finded_name,
                            flags=re.I)

                        ratio = self.similar(given_name, finded_name)
                        ratio2 = self.similar(given_name+" "+titles[-1], finded_name) if title != titles[-1] else 0
                        levenshtein = self.levenshtein(given_name, finded_name)
                        levenshtein2 = self.levenshtein(given_name+" "+titles[-1], finded_name) if title != titles[-1] else 100
                        # fflog(f'{finded_name=} {ratio=} {levenshtein=} {ratio2=} {levenshtein2=}')
                        if (
                                not(levenshtein  <= 22 and min(ratio,  0.39) <= ratio  <= max(ratio,  1.0))
                            and not(levenshtein2 <= 22 and min(ratio2, 0.39) <= ratio2 <= max(ratio2, 1.0))
                           ):
                            # fflog(f'levenshtein odrzuca, bo  {ratio=}  {levenshtein=}  {finded_name=}  given_name={given_name}')
                            # fflog(f'levenshtein odrzuca, bo {ratio2=} {levenshtein2=}  {finded_name=}  given_name={(given_name+" "+titles[-1])}')  if ratio2 else ""
                            continue
                            pass


                        # finded_name = item.get("title")  # finded_finded_name
                        # finded_name = cleantitle.normalize(cleantitle.getsearch(finded_name))
                        finded_name = finded_name.replace(".", " ")
                        finded_name = finded_name.replace("  ", " ")

                        # fflog(f'{finded_name=} | {title=} {words=} {year=}')
                        if (
                            self.contains_all_words(finded_name, words)
                           ):
                            # fflog(f"może pasować {item['id']=}")
                            if False:  # do likwidacji
                                items.append(item['id'])
                                pass
                            else:
                                if ( str(year) in finded_name
                                     or str(int(year)-1) in finded_name
                                     or not (yit := re.search(r"\b\d{4}\b", finded_name))  # gdy nie ma w ogóle roku w nazwie pliku
                                   ):
                                    # fflog(f'{item=}')
                                    # items.append(item['id'])
                                    items.append( (item['id'], "{}") )  # dla kompatybilności (aby można było usuwać duplikaty)
                                else:
                                    # fflog(f'odrzucono, bo zadany {year=} a w nazwie {yit[0]=} | {finded_name=}')
                                    # year_in_title = re.search(r"\b\d{4}\b", finded_name)
                                    # year_in_title = year_in_title[0] if year_in_title else ""
                                    # fflog(f'{year_in_title=}')
                                    items.append( (item['id'], repr({"trash": yit[0]})) )  # warunkowo
                        else:
                            # fflog(f'odrzucono')
                            # fflog(f'odrzucono, bo {finded_name=}, a szukamy: {title=} -> {words=}   ({year=})')
                            pass
                        # fflog(f'\n')

                    # fflog(f'{len(items)=}')
                    # fflog(f'{items=}')
                    # if len(items) < 1:
                        # fflog(f'nic nie znaleziono dla {title=}')
                    # return items
                else:
                    fflog(f'brak wyników dla {title=}')
        else:
            fflog("z powodu błędu autoryzacji szukanie niemożliwe")
            return
        if len(items) < 1:
            fflog(f'nic nie znaleziono')
        # fflog('DUPA')
        return items



    def _check_base_or_premiered_year_in_filename(self, filename, year, premiered, year_in_title, current_year):
        if not premiered and not year:
            return
        filename = filename.replace(year_in_title, "")
        #year_in_filename = re.findall(r"\b\d{4}\b", filename)  # też może być
        year_in_filename = re.search(r"\b\d{4}\b", filename)
        if year_in_filename:
            year_in_filename = year_in_filename[0]
            if 1900 <= int(year_in_filename) <= int(current_year) + 1:
                if premiered and (premiered.startswith(year_in_filename) or premiered.endswith(year_in_filename)) or year and str(year) == year_in_filename:
                    return True
                else:
                    return False



    def search_ep(self, title, localtitle, originaltitle, year, premiered, epNo, season, episode):
        if self.oauth(self.email, self.passwd):
            # fflog(f'szukanie pasujących {title=} {localtitle=} {originaltitle=}  {epNo=}  {year=}  {premiered=}')

            duration_expected = self.getDuration()


            epNo = epNo.lower()
            # fflog(f'{epNo=}')

            # epi = int(epNo[-2:])
            # sei = int(epNo[-5:-3])
            epi = int(episode)
            sei = int(season)

            pat_sez_re = re.compile(r"\b(?:sezon |s ?)(?P<sez>\d{1,2})\b")
            pat_epi_re = re.compile(r"\b(?:odcinek |e ?)(?P<odc>\d{1,3})\b")


            title, localtitle = localtitle, title  # zamianka

            titles = [cleantitle.normalize(cleantitle.getsearch(title)),
                      cleantitle.normalize(cleantitle.getsearch(localtitle)),
                      cleantitle.normalize(cleantitle.getsearch(originaltitle)),
                     ]

            titles = list(filter(None, titles))  # usunięcie pustych
            titles = list(dict.fromkeys(titles))  # pozbycie się ewentualnych duplikatów


            banned_words = ["zwiastun", "trailer", "recenzja", "omowienie", "gameplay", "nazywo", "walktrough", "stream", "opis", "newsy"]


            self.headers.update({'Authorization': f'Bearer {cache.cache_get("cdaprem_token")["value"]}'})


            # ustalenie bieżącego roku - a co jak ktoś ma złą datę na urządzeniu?
            current_year = int(time.strftime("%Y"))
            # fflog(f'{current_year=}', 1)


            items = []

            for title in titles:
                # fflog(f'{title=}')
                data = {
                    # 'query': title.lower() + (' ' + epNo if epNo and epNo not in title else ''),
                    # 'query': localtitle.lower(),
                    'query': title,
                    'duration': 'medium',
                    'page':  1,
                    'limit': 500,
                    'sort':  'best',
                }

                search = self.session.get(self.search_link, params=data, headers=self.headers)
                if search:
                    search = search.json()
                else:
                    fflog(f'jakiś błąd serwera {search=}')

                if search and len(search.get('data')):
                    # fflog(f"{len(search.get('data'))=}")

                    # sprawdzenie, czy tytuł serialu zawiera w sobię rok
                    year_in_title = re.search(r"\b\d{4}\b", title)
                    year_in_title = year_in_title[0] if year_in_title else ""

                    # given_name = cleantitle.normalize(title).lower()
                    given_name = cleantitle.normalize(cleantitle.getsearch(title))

                    banned_words2 = [word for word in banned_words if word not in given_name]

                    ep_given_name = f'{given_name} {epNo}'.strip()

                    title1 = title
                    title1 += f" {epNo}" if epNo and epNo not in title else ""
                    # fflog(f'{title1=}')
                    title1 = title1.replace(".", " ")
                    title1 = title1.replace("the ", " ")
                    title1 = title1.replace("  ", " ").strip()
                    words1 = title1.split(" ")


                    title2 = title1.replace("s01", "")
                    title2 = title2.replace("  ", " ").strip()
                    words2 = title2.split(" ")

                    title3 = title1.replace("s01e", "")
                    words3 = title3.split(" ")

                    title4 = title1.replace("s01e0", "")
                    words4 = title4.split(" ")
                    
                    # poniższe linijki to słabe rozwiązanie, ale nie chce mi się dzisiaj nic innego wymyślać, więc lecę schematem kopiuj wklej
                    title5 = title1.replace(f" {epNo}", "")
                    title5 += f" sezon {sei} e{epi}"
                    words5 = title5.split(" ")

                    title6 = title1.replace(f" {epNo}", "")
                    title6 += f" sezon {sei} odcinek {epi}"
                    words6 = title6.split(" ")

                    words7 = words8 = ''
                    if sei == 1:
                        title7 = title1.replace(f" {epNo}", "")
                        title7 += f"odcinek {epi}"
                        words7 = title7.split(" ")

                        title8 = title1.replace(f" {epNo}", "")
                        title8 += f"e{epi}"
                        words8 = title8.split(" ")
                    # jeszcze być może trzeba angielskie nazwy uwzględnić


                    for item in search.get('data'):

                        if item['id'] in items:
                            # fflog(f'już jest takie źródło w źródłach')
                            continue

                        if duration_expected and (duration := item.get("duration")) and abs(duration_expected - duration) > 5*60:
                            continue
                            pass

                        finded_name = item['title']

                        finded_name = cleantitle.normalize(finded_name.lower())  # polskie ogonki (akcenty)

                        if any(bw in finded_name for bw in banned_words2):
                            continue
                            pass

                        finded_name = re.sub(r'\[.*?\]', '', finded_name).strip()  #  dla takich 'Dark Matter S01E03 [WEB-DL. x264-NoNaNo][Lektor PL]'

                        finded_name = cleantitle.normalize(cleantitle.getsearch(finded_name))

                        # wycięcie pewnych fraz
                        # (trudność polega na przewidzeniu wszystkich możliwości)
                        finded_name = re.sub(
                            r" *\b(lektor|subbed|napisy|dubbing|polish|po?l(dub|sub)?|us|fr|de|dual|multi|p2p|web[.-]?dl|remux|3d|imax|final ?\d*|sezonu ?\d*)\b",
                            # "",
                            lambda x: x[0] if re.search(fr"\b{re.escape(x[0])}\b", title, flags=re.I) else "",  # aby nie usuwać tych fraz, które są w tytule (np. serial Office.PL)
                            finded_name,
                            flags=re.I)
                            
                        finded_name = finded_name.replace("()", "")

                        ratio = self.similar(given_name, finded_name)
                        ratio2 = self.similar(given_name+" "+titles[-1], finded_name) if title != titles[-1] else 0
                        levenshtein = self.levenshtein(ep_given_name, finded_name)
                        levenshtein2 = self.levenshtein(ep_given_name+" "+titles[-1], finded_name) if title != titles[-1] else 100
                        # fflog(f'{given_name=} {ep_given_name=} {finded_name=} {ratio=} {levenshtein=} {ratio2=} {levenshtein2=}')
                        if (
                                not(levenshtein  <= 22 and min(ratio,  0.39) <= ratio  <= max(ratio,  1.0))
                            and not(levenshtein2 <= 22 and min(ratio2, 0.39) <= ratio2 <= max(ratio2, 1.0))
                           ):
                            # fflog(f"levenshtein odrzuca {item['title']=}")
                            continue
                            pass

                        if premiered and re.search(r"\b\d{4}\b", finded_name):
                            if self._check_base_or_premiered_year_in_filename(finded_name, year, premiered, year_in_title, current_year) is False:
                                # fflog(f"  - odrzucono z powodu niepasującego roku ({year=} {premiered=}) w nazwie {finded_name=}", 1)
                                # fflog(f'levenshtein odrzuca, bo  {ratio=}  {levenshtein=}  {finded_name=}  given_name={given_name}')
                                # fflog(f'levenshtein odrzuca, bo {ratio2=} {levenshtein2=}  {finded_name=}  given_name={(given_name+" "+titles[-1])}')  if ratio2 else ""
                                continue
                                pass

                        # finded_name = item.get("title")
                        # finded_name = cleantitle.normalize(cleantitle.getsearch(finded_name))
                        # finded_name = cleantitle.getsearch(finded_name)
                        finded_name = finded_name.replace(".", " ")
                        finded_name = finded_name.replace("  ", " ")

                        match_sez = pat_sez_re.search(finded_name)
                        match_epi = pat_epi_re.search(finded_name)
                        # fflog(f'{match_sez=}')
                        # fflog(f'{match_epi=}')
                        if match_sez:
                            if int(match_sez["sez"]) != sei:
                                # fflog(f"zły sezon  {finded_name=}")
                                continue
                        if match_epi:
                            if int(match_epi["odc"]) != epi:
                                # fflog(f"zły odcinek  {finded_name=}")
                                continue

                        # fflog(f'{finded_name=} | {title=} {words1=} {year=}')
                        if(
                               self.contains_all_words(finded_name, words1)
                            or self.contains_all_words(finded_name, words2)
                            or self.contains_all_words(finded_name, words3)
                            or self.contains_all_words(finded_name, words4)
                            or self.contains_all_words(finded_name, words5)
                            or self.contains_all_words(finded_name, words6)
                            or words7 and self.contains_all_words(finded_name, words7)
                            or words8 and self.contains_all_words(finded_name, words8)
                            ):
                            # fflog(f"może pasować {item=}")
                            # fflog(f'\n         bo {finded_name=}, \bo szukamy: {title=} -> {words1=}  \n     lub  {title2=} ->   {words2=}  \n     lub  {title3=} ->    {words3=}  \n     lub  {title4=} ->     {words4=}\n     lub  {title5=} ->     {words5=}')
                            # return [item['id']]  # dla kompatybilności z filmami
                            items.append(item['id'])  # nie wiem, czy dla serialów też są różne warianty jak z napisami lub lektorem
                            # break  # jak nie chcemy szukać innych wariantów
                        else:
                            # fflog(f'odrzucono,\n         bo {finded_name=}, \na szukamy: {title=} -> {words1=}  \n     lub  {title2=} ->   {words2=}  \n     lub  {title3=} ->    {words3=}  \n     lub  {title4=} ->     {words4=}\n     lub  {title5=} ->     {words5=}\n     lub  {title6=} ->     {words6=}\n     lub  {title7=} ->     {words7=}\n     lub  {title8=} ->     {words8=}')
                            pass
                        # fflog(f'\n')

                else:
                    fflog(f'brak wyników dla {title=}')
        else:
            fflog("z powodu błędu autoryzacji szukanie niemożliwe")
            return
        # fflog(f'{len(items)=}')
        if len(items) < 1:
            fflog('nic nie znaleziono')
        # fflog('DUPA')
        return items


    def sources(self, links, hostDict, hostprDict):
        # fflog(f'{links=}')
        if links is None or not links:
            # fflog("brak danych do analizy")
            return []
        links = list(dict.fromkeys(links))  # pozbycie się ewentualnych duplikatów
        sources = []

        # fflog(f'szukanie źródeł dla ustalonych w poprzednim kroku pozycji')

        self.headers.update({'Authorization': f'Bearer {cache.cache_get("cdaprem_token")["value"]}'})

        for url in links:
            try:
                if not url:
                    continue
                else:
                    if isinstance(url, tuple):
                        extra_info = url[1]
                        extra_info = literal_eval(extra_info)
                        url = url[0]
                    else:
                        extra_info = {}

                    if not url:
                        continue

                    # fflog(f'{url=}')
                    query = self.session.get(f'{self.base_link}/video/{url}', headers=self.headers)  # odpytywanie serwera
                    # fflog(f'{query=}')

                    if not query:
                        fflog(f'błąd serwera albo brak źródeł  {url=}  {query=}')
                        continue
                    # fflog(query.status_code)

                    try:
                        query = query.json()
                    except Exception:
                        fflog(f'błąd parsowania {query=}')
                        query = {}

                    video = query.get('video')
                    # fflog(f'{video=}')

                    if video:
                        title = video['title']

                        lang, info = source_utils.get_lang_by_type(title)

                        info2 = title
                        # fflog(f'{title=} {lang=} {info=}')
                        info2 = re.sub(rf"[.([_-]?\b({lang}|{info})\b[.)\]_]?", "", info2, flags=re.I)

                        # wycięcie rozdzielczości
                        info2 = re.sub(
                            r" *\b(SD|HD|UHD|2k|4k|480p?|540p?|576p?|720p?|1080[pi]?|1440p?|2160p?)\b",
                            "",
                            info2)

                        info2 = re.sub(r" {2,}", " ", info2).strip()  # sprzątanie


                        source = ""  # po co powielać napis CDA

                        if video.get('audio_51'):
                            # fflog(f"{video.get('audio_51')=}")  # trafiłem też na fałszywe oznaczenia
                            info = "5.1 | " + info

                        max_available_quality = video.get('quality')  # pomyśleć, jak wykorzystać

                        if video.get('quality_adaptive'):
                            # fflog(f'jest też dostępny link typu adaptive dla {title=}')
                            pass
                        """
                        # check adaptive stream
                        # add if exist
                        # further process in resolve method
                        adaptive_data = video.get('quality_adaptive')
                        if adaptive_data and control.setting("_proxy_path"):
                            adaptive_quality = source_utils.get_qual(max_available_quality)
                            cache.cache_insert('DRMCDA', repr(adaptive_data))
                            sources.append(
                                {
                                    "source": source,
                                    "quality": f"{adaptive_quality}",
                                    "language": lang,
                                    "url": f'DRMCDA|{url}',
                                    "info": "DRM Adaptive | " + info,
                                    "direct": True,
                                    "debridonly": False,
                                    "info2": info2,
                                }
                            )
                        """

                        for quality in video['qualities']:
                            # fflog(f"{quality['name']=} {title=}  {quality['file']=}")
                            if not quality.get('file'):
                                continue
                            if int(quality['name'].replace("p","")) >= 480 or len(video['qualities'])==1:
                                sources.append(
                                    {
                                        "source": source,
                                        "quality": quality['name'],
                                        "language": lang,
                                        "url": quality['file'],
                                        "direct": True,
                                        "debridonly": False,
                                        "info": info,
                                        "info2": info2,
                                        "duration": video.get('duration'),  # odbiegające od innych może świadczyć o nieodpowiednim wyborze
                                    }
                                )
                                if extra_info:
                                    sources[-1].update(extra_info)
                                    pass

                    else:
                        # fflog(f'brak źródeł dla {url=} (być może zostały usunięte)  {query=}')
                        pass
            except Exception as e:
                # log_exception()
                fflog_exc(1)
                continue

        # fflog(f'{sources=}')
        fflog(f'przekazano źródeł: {len(sources)}')
        return sources


    def resolve(self, url):
        # fflog(f'{url=}')
        if not 'DRMCDA' in url:
            link = str(url).replace('\\', '/')
            fflog(f'{link=}')
            return str(link)
        """
        if 'DRMCDA' in url:
            adaptive = literal_eval(cache.cache_get('DRMCDA')["value"])
            PROTOCOL = 'mpd'
            DRM = 'com.widevine.alpha'
            manifest_url = adaptive.get('manifest')
            lic_url = adaptive.get('widevine_license')
            drm_header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.62',
                'X-Dt-Custom-Data': adaptive.get('drm_header_value')
            }
            drm_header = urlencode(drm_header)
            # setting proxy
            proxy_path = control.setting("_proxy_path")  # nie ma tego w starym FF
            #tunneling licence url
            lic_url = f'{proxy_path}drmcda={lic_url}'
            adaptive_data = {
                'protocol': PROTOCOL,
                'licence_type': DRM,
                'mimetype': 'application/xml+dash',
                'manifest': manifest_url,
                'licence_url': lic_url,
                'licence_header': drm_header,
                'post_data': 'R{SSM}',
                'response_data': ''
            }
            link = f'DRMCDA|{repr(adaptive_data)}'
            test = literal_eval(link.split('|')[-1])
            fflog(f'{test=} {link=}')
            return link
        """

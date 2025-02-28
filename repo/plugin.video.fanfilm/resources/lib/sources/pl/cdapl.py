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
import re
import json
import requests
import time
import urllib.parse as urllib
from html import unescape
from ast import literal_eval
from ptw.libraries import source_utils, cleantitle, client, control, cache
from ptw.debug import log_exception, fflog_exc, fflog
from difflib import SequenceMatcher

class source:
    def __init__(self):
        self.priority = 1
        self.language = ["pl"]
        self.domains = ["cda.pl"]

        self.base_link = "https://www.cda.pl/"
        self.search_link = "video/show/%s?duration=dlugie&s=best"
        self.search_link_ep = "video/show/%s?duration=srednie&s=best"
        self.anime = False
        self.year = 0
        """
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/jxl,image/webp,*/*;q=0.8",
            "Accept-Language": "pl,en-US;q=0.7,en;q=0.3", "Accept-Encoding": "gzip, deflate, br", "DNT": "1",
            "Connection": "keep-alive", "Upgrade-Insecure-Requests": "1", "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "same-origin", "Sec-Fetch-User": "?1", "Pragma": "no-cache",
            "Cache-Control": "no-cache", "TE": "trailers", }
        """
        self.headers = {"User-Agent": "vlc"}
        # self.headers = {}


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


    def get_originaltitle(self, aliases):
        if aliases:
            originalname = [a for a in aliases if "originalname" in a]
            originalname = originalname[0]["originalname"] if originalname else ""
            # fflog(f'{originalname=}')
            originalname = "" if source_utils.czy_litery_krzaczki(originalname) else originalname
            return originalname
        return ""


    def movie(self, imdb, title, localtitle, aliases, year):
        # fflog(f'{title=} {localtitle=} {year=}')
        return self.search(title, localtitle, self.get_originaltitle(aliases), year, True)


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        # fflog(f'{tvshowtitle=} {localtvshowtitle=} ')
        return (tvshowtitle, localtvshowtitle, self.get_originaltitle(aliases)), year


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        # fflog(f'{url=} {imdb=} {tvdb=} {title=} {premiered=} {season=} {episode=}')
        self.year = int(url[1])
        epNo = ""
        # anime = False
        """
        anime = source_utils.is_anime("show", "tvdb", tvdb)
        self.anime = anime
        if anime:
            fflog(f'to anime')
            epNo = "" + source_utils.absoluteNumber(tvdb, episode, season)
        """
        if not epNo:
            epNo = "s" + season.zfill(2) + "e" + episode.zfill(2)
        # fflog(f'{epNo=}')
        if epNo:
            # epNo = " " + epNo
            pass
        # return self.search_ep(url[0][0] + epNo, url[0][1] + epNo, "")
        return self.search_ep(url[0][0], url[0][1], url[0][2], self.year, premiered, epNo, season, episode)


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


    def search_ep(self, title1, title2, title3, year, premiered, epNo, season, episode):
        # fflog(f'{title1=} {title2=} {title3=} {epNo=} {year=} {premiered=}')
        try:
            titles = [cleantitle.normalize(cleantitle.getsearch(title1)),
                      cleantitle.normalize(cleantitle.getsearch(title2)),
                      cleantitle.normalize(cleantitle.getsearch(title3)),
                     ]

            titles = list(filter(None, titles))  # usunięcie pustych
            titles = list(dict.fromkeys(titles))  # pozbycie się duplikatów

            if not epNo:
                fflog(f'brak {epNo=} - szukanie odcinka niemożliwe')
                return

            epi = int(episode)
            sei = int(season)

            pat_sez_re = re.compile(r"\b(?:sezon |s ?)(?P<sez>\d{1,2})\b")
            pat_epi_re = re.compile(r"\b(?:odcinek |e ?)(?P<odc>\d{1,3})\b")

            links = []

            #session = requests.session()
            #session.get("https://cda.pl")

            banned_words = ["zwiastun", "trailer", "recenzja", "omowienie", "gameplay", "nazywo", "walktrough", "stream", "opis", "newsy"]

            duration_expected = self.getDuration()

            # ustalenie bieżącego roku - a co jak ktoś ma złą datę na urządzeniu?
            current_year = int(time.strftime("%Y"))
            # fflog(f'{current_year=}', 1)

            for title in titles:
                try:
                    if not title:
                        continue
                    # fflog(f'{title=}')
                    # title = title + f" {epNo}" if epNo and epNo not in title else title  # trzeba zawęzić zakres poszukiwań, bo standardoweo tylko pierwszych 20 wyników (1 strona)
                    url = urllib.urljoin(self.base_link, self.search_link_ep)
                    url = url % urllib.quote(str(title).replace(" ", "_"))

                    results = []
                    def do_requests(url, results):
                        self.headers.update({"Referer": url})
                        # fflog(f'{url=}')
                        #result = session.get(url, headers=self.headers)
                        result = requests.get(url, headers=self.headers, timeout=30)
                        # fflog(f'{result=}')
                        result = result.text
                        # fflog(f'{result=}')
                        result_v = client.parseDOM(result, "div", attrs={"class": "video-clip-wrapper"})
                        # fflog(f"{len(result_v)=}")
                        results += result_v
                        # fflog(f"{len(results)=}")

                        next_page = client.parseDOM(result, "a", ret="href", attrs={"class": "sbmBigNext btn-my btn-large fiximg"})
                        # fflog(f'{next_page=}')
                        next_page = next_page[-1] if next_page else ""
                        if "//p" in next_page:
                            return results
                        p = re.search(r'/p(\d)\?', next_page)
                        # fflog(f'{p=}')
                        p = int(p[1]) if p else 0
                        next_page = urllib.urljoin(self.base_link, next_page)
                        if p and p <= 3 and next_page != url:
                            results = do_requests(next_page, results)
                        return results

                    result = do_requests(url, results)
                        
                except Exception:
                    fflog_exc(1)
                    continue

                given_name = cleantitle.normalize(cleantitle.getsearch(title))

                banned_words2 = [word for word in banned_words if word not in given_name]

                # sprawdzenie, czy tytuł serialu zawiera w sobię rok
                year_in_title = re.search(r"\b\d{4}\b", title)
                year_in_title = year_in_title[0] if year_in_title else ""

                given_name = title

                title1 = title

                title1 = title1 + f" {epNo}" if epNo and epNo not in title else title
                title1 = title1.replace(".", " ")
                title1 = title1.replace("the ", " ")
                title1 = title1.replace("  ", " ").strip()
                words1 = title1.split(" ")

                ep_given_name = title1

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


                # fflog(f"{len(result)=}")
                for item in result:
                    try:
                        link = str(client.parseDOM(item, "a", ret="href")[0])

                        if link in links:
                            # fflog(f'już jest takie źródło w źródłach {link=}')
                            continue

                        video_premium = client.parseDOM(item, "span", attrs={"class": "flag-video-premium"})
                        if video_premium:
                            # fflog(f'materiał dostępny tylko dla premium ({link=})')
                            continue

                        duration = client.parseDOM(item, "span", attrs={"class": "timeElem"})
                        # fflog(f'{duration=}')
                        if duration:
                            duration = duration[0]
                            if duration:
                                duration = self.czas_na_sekundy(duration)
                        if duration_expected and duration and abs(duration_expected - duration) > 5*60:
                            continue
                            pass

                        name = str(client.parseDOM(item, "a", attrs={"class": "link-title-visit"})[0])
                        name = unescape(name)
                        # name = name.replace("[", " ").replace("]", " ")  # zmieniłem w cleantitle.py
                        # name = name.replace(' <span class="cc-tv-station-live">•</span> oglądaj na żywo', '')
                        if "cc-tv-station-live" in name or "oglądaj na żywo" in name:
                            continue

                        name = name.lower()
                        name = cleantitle.normalize(name)  # polskie ogonki (akcenty)

                        if any(bw in name for bw in banned_words2):
                            continue
                            pass

                        name = re.sub(r'\[.*?\]', '', name).strip()  #  dla takich 'Dark Matter S01E03 [WEB-DL. x264-NoNaNo][Lektor PL]'
                        name = cleantitle.normalize(cleantitle.getsearch(name))
                        name = name.replace(".", " ")
                        name = name.replace("  ", " ")

                        # wycięcie pewnych fraz
                        # (trudność polega na przewidzeniu wszystkich możliwości)
                        name = re.sub(
                            r" *\b(lektor|subbed|napisy|dubbing|polish|po?l(dub|sub)?|us|fr|de|dual|multi|p2p|web[.-]?dl|remux|3d|imax|final ?\d*|sezonu ?\d*)\b",
                            # "",
                            lambda x: x[0] if re.search(fr"\b{re.escape(x[0])}\b", title, flags=re.I) else "",  # aby nie usuwać tych fraz, które są w tytule (np. serial Office.PL)
                            name,
                            flags=re.I)

                        name = name.replace("()", "")

                        finded_name = name
                        ratio = self.similar(given_name, finded_name)
                        ratio2 = self.similar(given_name+" "+titles[-1], finded_name) if title != titles[-1] else 0
                        levenshtein = self.levenshtein(ep_given_name, finded_name)
                        levenshtein2 = self.levenshtein(ep_given_name+" "+titles[-1], finded_name) if title != titles[-1] else 100
                        # fflog(f'{given_name=} {ep_given_name=} {finded_name=} {ratio=} {levenshtein=}')
                        if (
                                not(levenshtein  <= 22 and min(ratio,  0.39) <= ratio  <= max(ratio,  1.0))
                            and not(levenshtein2 <= 22 and min(ratio2, 0.39) <= ratio2 <= max(ratio2, 1.0))
                           ):
                            # fflog(f"levenshtein odrzuca {link=}")
                            continue
                            pass

                        if premiered and re.search(r"\b\d{4}\b", finded_name):
                            if self._check_base_or_premiered_year_in_filename(finded_name, year, premiered, year_in_title, current_year) is False:
                                # fflog(f"  - odrzucono z powodu niepasującego roku ({year=} {premiered=}) w nazwie {finded_name=}", 1)
                                continue
                                pass

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

                        # fflog(f'{name=} | {title=} {words1=} {year=}')
                        # fflog(f'{name=} | {title4=} {words4=} {year=}')
                        if(
                               self.contains_all_words(name, words1)
                            or self.contains_all_words(name, words2)
                            or self.contains_all_words(name, words3)
                            or self.contains_all_words(name, words4)

                            or self.contains_all_words(finded_name, words5)
                            or self.contains_all_words(finded_name, words6)
                            or words7 and self.contains_all_words(finded_name, words7)
                            or words8 and self.contains_all_words(finded_name, words8)
                            ):
                            # fflog(f'pasuje {link=}')
                            links.append(link)
                        else:
                            # fflog(f'odrzucono,\n         bo {finded_name=}, \na szukamy: {title=} -> {words1=}  \n     lub  {title2=} ->   {words2=}  \n     lub  {title3=} ->    {words3=}  \n     lub  {title4=} ->     {words4=}\n     lub  {title5=} ->     {words5=}\n     lub  {title6=} ->     {words6=}\n     lub  {title7=} ->     {words7=}\n     lub  {title8=} ->     {words8=}')
                            pass
                    except Exception:
                        fflog_exc(1)
                        continue

            # fflog(f'{len(links)=} {links=}')
            if not links:
                fflog('nie znaleziono pasujących')
            return links
        except Exception as e:
            print(e)
            fflog_exc(1)
            return


    def search(self, title, localtitle, originaltitle, year, is_movie_search):
        try:
            title, localtitle = localtitle, title  # zamianka

            titles = [cleantitle.normalize(cleantitle.getsearch(title)),
                      cleantitle.normalize(cleantitle.getsearch(localtitle)),
                      cleantitle.normalize(cleantitle.getsearch(originaltitle)),
                     ]

            titles = list(filter(None, titles))  # usunięcie pustych
            titles = list(dict.fromkeys(titles))  # pozbycie się duplikatów

            links = []
            #session = requests.session()
            #session.get("https://cda.pl")

            banned_words = ["zwiastun", "trailer", "recenzja", "omowienie", "gameplay", "nazywo", "walktrough", "stream", "opis", "newsy"]

            duration_expected = self.getDuration()

            for title in titles:
                try:
                    if not title:
                        continue

                    url = urllib.urljoin(self.base_link, self.search_link)
                    url = url % urllib.quote(str(title).replace(" ", "_"))

                    results = []
                    def do_requests(url, results):
                        self.headers.update({"Referer": url})
                        # fflog(f'{url=}')
                        #result = session.get(url, headers=self.headers)
                        result = requests.get(url, headers=self.headers, timeout=30)
                        # fflog(f'{result=}')
                        result = result.text
                        # fflog(f'{result=}')
                        result_v = client.parseDOM(result, "div", attrs={"class": "video-clip-wrapper"})
                        # fflog(f"{len(result_v)=}")
                        results += result_v
                        # fflog(f"{len(results)=}")

                        next_page = client.parseDOM(result, "a", ret="href", attrs={"class": "sbmBigNext btn-my btn-large fiximg"})
                        # fflog(f'{next_page=}')
                        next_page = next_page[-1] if next_page else ""
                        if "//p" in next_page:
                            return results
                        p = re.search(r'/p(\d)\?', next_page)
                        # fflog(f'{p=}')
                        p = int(p[1]) if p else 0
                        next_page = urllib.urljoin(self.base_link, next_page)
                        if p and p <= 3 and next_page != url:
                            results = do_requests(next_page, results)
                        return results

                    result = do_requests(url, results)
                except Exception:
                    # fflog_exc(1)
                    continue

                # given_name = cleantitle.normalize(title).lower()
                given_name = cleantitle.normalize(cleantitle.getsearch(title))

                banned_words2 = [word for word in banned_words if word not in given_name]

                # fflog(f'{len(result)=} {result=}')
                for item in result:
                    try:
                        link = str(client.parseDOM(item, "a", ret="href")[0])
                        # fflog(f'{link=}')

                        if link in links:
                            # fflog(f'już jest takie źródło w źródłach {link=}')
                            continue

                        video_premium = client.parseDOM(item, "span", attrs={"class": "flag-video-premium"})
                        if video_premium:
                            # fflog(f'materiał dostępny tylko dla premium ({link=})')
                            continue

                        duration = client.parseDOM(item, "span", attrs={"class": "timeElem"})
                        # fflog(f'{duration=}')
                        if duration:
                            duration = duration[0]
                            if duration:
                                duration = self.czas_na_sekundy(duration)
                        if duration_expected and duration and abs(duration_expected - duration) > 11*60:
                            # fflog(f'odrzucone z powodu niepasującego czasu trwania  {duration_expected=} {duration=}  {link=}')
                            continue
                            pass

                        name = str(client.parseDOM(item, "a", attrs={"class": "link-title-visit"})[0])
                        name = unescape(name)
                        # fflog(f'{name=}')
                        # name = # oczyścić z zagnieżdzonych atrybutów, jak np. <span>  (to chyba dla transmisji na żywo występuje)
                        # name = name.replace(' <span class="cc-tv-station-live">•</span> oglądaj na żywo', '')
                        if "cc-tv-station-live" in name or "oglądaj na żywo" in name:
                            continue

                        name = name.lower()
                        name = cleantitle.normalize(name)  # polskie ogonki (akcenty)

                        if any(bw in name for bw in banned_words2):
                            # fflog(f'odrzucenie z powodu wykrytych pewnych wyrazów  {link=}')
                            continue
                            pass

                        name = re.sub(r'\[.*?\]', '', name).strip()  #  dla takich 'Dark Matter S01E03 [WEB-DL. x264-NoNaNo][Lektor PL]'
                        name = cleantitle.normalize(cleantitle.getsearch(name))
                        name = name.replace(".", " ")
                        name = name.replace("  ", " ")

                        # wycięcie pewnych fraz
                        # (trudność polega na przewidzeniu wszystkich możliwości)
                        name = re.sub(
                            r" *\b(lektor|subbed|napisy|dubbing|polish|po?l(dub|sub)?|us|fr|de|dual|multi|p2p|web[.-]?dl|remux|3d|imax)\b",
                            # "",
                            lambda x: x[0] if re.search(fr"\b{re.escape(x[0])}\b", title, flags=re.I) else "",  # aby nie usuwać tych fraz, które są w tytule (np. serial Office.PL)
                            name,
                            flags=re.I)

                        finded_name = name
                        finded_name = finded_name.split(year)[0].strip()

                        ratio = self.similar(given_name, finded_name)
                        ratio2 = self.similar(given_name+" "+titles[-1], finded_name) if title != titles[-1] else 0
                        levenshtein = self.levenshtein(given_name, finded_name)
                        levenshtein2 = self.levenshtein(given_name+" "+titles[-1], finded_name) if title != titles[-1] else 100
                        # fflog(f'{given_name=} {finded_name=} {ratio=} {levenshtein=}')
                        if (
                                not(levenshtein  <= 22 and min(ratio,  0.39) <= ratio  <= max(ratio,  1.0))
                            and not(levenshtein2 <= 22 and min(ratio2, 0.39) <= ratio2 <= max(ratio2, 1.0))
                           ):
                            # fflog(f"levenshtein odrzuca {link=}, bo {given_name=} {finded_name=} {ratio=} {levenshtein=}")
                            # fflog(f'levenshtein odrzuca {link=}, bo {ratio2=} {levenshtein2=}  {finded_name=}  given_name={(given_name+" "+titles[-1])}')  if ratio2 else ""
                            continue
                            pass


                        title = title.replace(".", " ")
                        title = title.replace("the ", " ")
                        title = title.replace("  ", " ").strip()
                        words = title.split(" ")

                        # fflog(f'{name=} | {title=} {words=} {year=}')
                        if (
                            self.contains_all_words(name, words)
                            and (str(year) in name
                                 or str(int(year)-1) in name
                                 or not re.search(r"\b\d{4}\b", name)  # gdy nie ma w ogóle roku w nazwie pliku
                                )
                           ):
                            # fflog(f'może pasować {link=}')
                            links.append(link)
                        else:
                            # fflog(f'odrzucono {link=}')
                            # fflog(f'odrzucono, bo {name=}, a szukamy: {title=} -> {words=}   ({year=})')
                            pass
                        # fflog(f'\n')
                    except Exception:
                        # fflog_exc(1)
                        continue
            # fflog(f'{len(links)=} {links=}')
            if not links:
                fflog('nie znaleziono pasujących')
            return links
        except Exception as e:
            print(e)
            fflog_exc(1)
            return


    def sources(self, links, hostDict, hostprDict):
        # fflog(f'{links=}')
        if links is None or not links:
            # fflog(f'brak danych do analizy')
            return []
        links = list(dict.fromkeys(links))  # pozbycie się ewentualnych duplikatów
        sources = []
        # session = requests.session()
        # session.get("https://cda.pl")
        user_max_quality = control.setting("hosts.quality")
        if user_max_quality == "":
            user_max_quality = "0"
        user_max_qmax = int(user_max_quality)
        quality_order = [2160, 1440, 1080, 720, 480]
        try:
            for lnk in links:
                try:
                    # fflog(f'{lnk=}')
                    if not lnk:
                        continue
                    url = urllib.urljoin(self.base_link, lnk)
                    # fflog(f'{url=} {lnk=}')
                    if "/folder/" in lnk:
                        continue
                    """
                    # if url == lnk or "/vfilm" in lnk:
                    if url == lnk:
                        fflog(f'materiał dostępny tylko dla premium ({lnk=})')
                        # fflog('dostępny tylko dla premium')
                        continue
                        pass
                    """
                    """
                    result1 = None
                    result1 = requests.get(url, headers=self.headers)
                    if result1 and not isinstance(result1, str):  # potrzebne gdy używam client.request
                        result1 = result1.text
                    embedUrl = re.search(r'"embedUrl": "([^"]*)"', result1)
                    embedUrl = embedUrl[1] if embedUrl else ""
                    fflog(f'{embedUrl=}')
                    """
                    # rozdz = "647x500"
                    rozdz = "620x368"  # nie wiem, czemu teraz taką daje
                    # ale chyba rozdzielczość może być dowolna
                    result2 = None
                    if url != lnk:
                        req_url = f"https://ebd.cda.pl/{rozdz}/" + url.split("/")[-1]
                    else:
                        req_url = f"https://ebd.cda.pl/{rozdz}/" + url.split("/video/")[-1]
                    # fflog(f'adres odtwarzacza: {req_url}')
                    #result2 = client.request(req_url, headers=self.headers)  # pierwotnie taka komenda była (client.request), tylko bez headers
                    if result2 is None:
                        # fflog(f'{result2=}')
                        result2 = requests.get(req_url, headers=self.headers)
                        pass
                    # result2 = session.get(req_url, headers=self.headers)
                    # fflog(f'{result2=}')

                    if result2 and not isinstance(result2, str):  # potrzebne gdy używam client.request
                        result2 = result2.text
                        # fflog(f'{result2=}')

                    try:
                        title = client.parseDOM(result2, "title")[0]
                        # fflog(f'{title=}')
                    except Exception:
                        # fflog_exc(1)
                        if result2 and (material_niedostepny := "Materiał na który wskazywał ten link został usunięty przez jego właściciela lub Administratora") in result2:
                            fflog(f'{material_niedostepny}')
                            pass
                        elif result2 and (material_niedostepny := "Ten film jest dostępny dla użytkowników premium") in result2:
                            fflog(f'{material_niedostepny}')
                            pass
                        else:
                            fflog(f'wystąpił jakiś błąd')
                            fflog(f'{result2=} {req_url=} {lnk=} {url=}')
                            pass
                        continue

                    lang, info = source_utils.get_lang_by_type(title)

                    valid, host = source_utils.is_host_valid(url, hostDict)  # olać to, bo nie wiem czemu, ale czasami wypisuje mi, że "host='cda.pl' not valid - sorry" (ale mógł to być błąd w kodzie resolvera, bo grzebałem tam ;)

                    # fflog(f'{valid=} {host=} {lang=} {info=} {title=}')

                    info2 = title
                    # opcjonalnie
                    info2 = re.sub(rf"[.([_-]?\b({lang}|{info})\b[.)\]_]?", "", info2, flags=re.I)
                    info2 = re.sub(r" {2,}", " ", info2).strip()

                    # match = re.search(r'player_data="([^"]+)"', result2) or re.search(r"player_data='([^']+)'", result2)  # czy to nie bezpieczniejsze niż poniższy miks?
                    match = re.search(r'player_data="([^"]*)"', result2) or re.search(r"player_data='([^']*)'", result2)  # czy to nie bezpieczniejsze niż poniższy miks?
                    # match = re.search(r'player_data=("|\')([^\1]+)\1', result2)  # coś nie działa jak trzeba
                    # match = re.search(r'player_data=("|\')(.*?)\1', result2)  # to działa
                    if match and match.group(1):
                    # if match and match.group(2):
                        # fflog(f'{match=}')
                        pdata = json.loads(unescape(match.group(1)))
                        # pdata = json.loads(unescape(match.group(2)))
                        # fflog(f'{pdata=}')
                        vdata = pdata.get('video', {})
                        # fflog(f'{vdata=}')
                        qdata = vdata.get('qualities')
                        # fflog(f'{qdata=}')
                        fdata = vdata.get('file')  # zakodowany directlink
                        # fflog(f'{fdata=}')
                        duration = vdata.get('duration')
                        if not fdata:  # to może oznaczać, że resolver nie wyciągnie wideo, do nie ma bezpośredniego, a będzie tylko adaptive, a to coś związane z drm
                            fflog(f'DRM protected  {title=}')
                            continue
                            pass
                        cda_sources = [(q, '?wersja={0}'.format(q)) for q in qdata.keys()]
                        # fflog(f'{cda_sources=} {len(cda_sources)=}')
                        if len(cda_sources) > 0:
                            if not valid:  # olać to
                                fflog(f'{host=} not valid - sorry')
                                #continue  # olewam to, choć jak się takie coś pojawi, to może być problem z odtworzeniem (miałem tak, ale okazało się, że był błąd w kodzie resolvera)
                                pass
                            for q in reversed(cda_sources):
                                # fflog(f'{url=} {q=}')
                                #if len(cda_sources) == 1 or int(q[0].replace("p" ,"")) >= 480:
                                # fflog(f'{q[0]=} {title=}')
                                if "p" in q[0] and quality_order[user_max_qmax] >= int(q[0].replace("p" ,"")):
                                    sources.append({
                                        "source": host if host != "cda.pl" else "",
                                        "quality": source_utils.label_to_quality(q[0]),
                                        "url": url + q[1],
                                        "language": lang,
                                        "info": info,
                                        "info2": info2,
                                        "direct": False,  # jak False, to idzie przes resolvera (Gujala), a do True, to trzeba samemu dołożyć dekoder, więc może lepiej skorzystać z gotowca
                                        "debridonly": False,
                                        "duration": duration,
                                    })
                                    break  # tylko maksymalną jakość
                    else:
                        fflog(f'wystąpił jakiś problem {match=}')

                except Exception:
                    fflog_exc(1)
                    continue

            # fflog(f'{sources=}')
            fflog(f'przekazano źródeł: {len(sources)}')
            return sources

        except Exception as e:
            print(e)
            fflog_exc(1)
            return sources

    """
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
        return "", None
    """


    def czas_na_sekundy(self, czas):
        parts = czas.split(':')
        if len(parts) == 3:
            godziny, minuty, sekundy = map(int, parts)
            return godziny * 3600 + minuty * 60 + sekundy
        else:
            minuty, sekundy = map(int, parts)
            return minuty * 60 + sekundy

    """
    def cda_decode(self, a):
        a = a.replace("_XDDD", "")
        a = a.replace("_CDA", "")
        a = a.replace("_ADC", "")
        a = a.replace("_CXD", "")
        a = a.replace("_QWE", "")
        a = a.replace("_Q5", "")
        a = a.replace("_IKSDE", "")
        a = urllib_parse.unquote(a)
        a = ''.join([chr(33 + (ord(char) + 14) % 94) if 32 < ord(char) < 127 else char for char in a])
        a = a.replace(".cda.mp4", "")
        a = a.replace(".2cda.pl", ".cda.pl")
        a = a.replace(".3cda.pl", ".cda.pl")
        return "https://{0}.mp4".format(a)
    """

    def resolve(self, url):
        #fflog(f' {url=}')
        url = str(url).replace("//", "/").replace(":/", "://")
        # url = url.split("?")[0]  # wycina jakość (ale KODI i tak wybiera maksymalną (bo to nie directlink), i chyba resolver wybieera najwyższą)
        fflog(f'{url=}')
        return url

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
import threading
import time
import sys
from ast import literal_eval
from html import unescape
from urllib.parse import unquote, quote

import requests
import urllib3

from ptw.libraries import source_utils
from ptw.libraries import cleantitle
from ptw.libraries import client, control, cache
from ptw.libraries import log_utils
from ptw.libraries.log_utils import fflog
from ptw.debug import log_exception, fflog_exc

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class source:
    """Scraper dla serwisu xt7.pl"""

    def __init__(self):
        self.VIDEO_EXTENSIONS = ("avi", "mkv", "mp4", "mpg", "mov", ".ts", "mts", "2ts")  # trzymać 3 znaki długości dla każdego elementu ("2ts" to od "m2ts")
        self.lock = threading.Lock()
        self.raw_results = []
        self.results = []
        self.trash = []
        #self.trash2 = []
        self.titles = []
        self.titles_requested = []
        self.pages = []
        self.priority = 1
        # self.tit_val_filt_for_one_title = None
        self.dodatkowy_filtr = None
        self.dodatkowy_filtr2 = None
        self.language = ["pl"]
        self.domains = ["xt7.pl"]
        self.base_link = "https://xt7.pl/"
        self.login_link = "login"
        self.mylibrary_link = "mojekonto/pliki"
        self.mynotepad_link = "mojekonto/notes"

        if control.settings.getBool("xt7.wiele_serwerow"):
            self.search_link = "mojekonto/szukaj"
            self.support_search_link = "mojekonto/szukaj/{}"  # do paginacji wyników
        else:
            self.search_link = "mojekonto/szukajka"
            self.support_search_link = "mojekonto/szukajka/{}"  # do paginacji wyników

        self.session = requests.Session()
        self.user_name = control.settings.getString("xt7.username")
        self.user_pass = control.settings.getString("xt7.password")
        self.headers = {
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36+SOSNF-CS20.10.5/200R0CVLCI-2BDE4C4A6B67444C",
            "DNT": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        }


    def movie(self, imdb, title, localtitle, aliases, year):
        # fflog('szukanie żródeł filmu', 1)
        return self.search(title, localtitle, year, aliases=aliases)


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        """ jakaś proteza pomocnicza przed szukaniem odcinka """
        # fflog(f'szukanie serialu {tvshowtitle=} {localtvshowtitle=} {year=} {aliases=}', 0)
        return (tvshowtitle, localtvshowtitle, aliases), year


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        # fflog(f'szukanie źródeł odcinka {url=} {premiered=} {season=} {episode=} {title=}', 1)
        epNo = ""
        """
        try:
            anime = source_utils.is_anime("show", "tvdb", tvdb)
        except Exception:
            anime = None
        if anime:
            epNo = source_utils.absoluteNumber(tvdb, episode, season)
        """
        if not epNo:
            epNo = f"s{season.zfill(2)}e{episode.zfill(2)}"
            # epNo = f"s{season.zfill(2)}e{episode.zfill(3)}"  # dla seriali co mają więcej niż 99 odcinków na sezon, tylko jak to wykryć ?
        return self.search(url[0][0], url[0][1], year=url[1], episode=epNo, aliases=url[0][2], premiered=premiered)


    def search(self, title, localtitle, year="", episode="", aliases=None, premiered=""):
        """Funkcja wysyła do serwera zapytania:
        oryginalny tytuł filmu oraz tłumaczenie tytułu
        """
        # fflog(f'{title=} {localtitle=} {year=} {episode=} {premiered=} {aliases=}')
        if not title:
            fflog(f'Błąd - szukanie niemożliwe, bo {title=}') 
            return

        results = []

        if aliases is None:
            aliases = []

        year = str(year)  # dla kompatybilności, gdy zmienna jest innego typu niż string

        try:
            # przechowanie zmiennej pod inną nazwą (będzie potrzebna później)
            title0 = title

            # jak brak opisu polskiego, a powinien być, to by nie odrzucało filmów co w nazwie mają polski tytuł
            # self.tit_val_filt_for_one_title = (title == localtitle)

            aliases1 = [
                (a.get("title") or a.get("originalname") or "")
                + " ("
                + a.get("country", "")
                + ")"
                for a in aliases
                # if a.get("country") in ("us", "en", "uk", "gb", "au", "pl", "original")
            ]
            aliases2 = [a.rpartition(" (")[0] for a in aliases1]  # country out
            aliases2 = [a.replace(year, "").replace("()", "").rstrip() for a in aliases2]  # year out
            # aliases2 = [a for a in aliases2 if re.search(r"[a-z0-9]", a, flags=re.I)]  # krzaczki out
            aliases2 = [a for a in aliases2 if not source_utils.czy_litery_krzaczki(a)]  # krzaczki out
            # aliases2 = list(dict.fromkeys(aliases2))  # duplicates out (ale tylko o tej samej wielkości liter)
            aliases2 = [alias for i, alias in enumerate(aliases2) if alias.lower() not in [x.lower() for x in aliases2[:i]]]  # kolejne duplikaty są usuwane niezależnie od wielkości liter
            # fflog(f'{aliases2=}')
            # aliases2.append('Rogue One: A Star Wars')  # test tylko
            # dodanie do późniejszego porównywania z nazwami plików
            self.titles = aliases2

            log_text = ""
            log_text += f"tytuł: {title!r}"
            log_text += f", polski tytuł: {localtitle!r}" if localtitle != title else ""
            log_text += f", rok (premiery{' serialu' if episode else ''}): {year!r}" if year else ""
            log_text += f", data premiery (sezonu): {premiered!r}" if premiered else ""
            log_text += f", odcinek: {episode!r}" if episode else ""
            log_text += f', aliasy tytułów: {aliases2[::-1]}' if aliases else ''
            # log_text += "\nALIASY1:\n "+("\n"+chr(32)).join(map(repr,aliases1)) if aliases else ''
            # log_text += "\nALIASY2:\n "+("\n"+chr(32)).join(map(repr,aliases2)) if aliases else ''
            fflog(f" {log_text}")

            titles = [title, localtitle]
            # dodanie do późniejszego porównywania z nazwami plików
            self.titles = titles + self.titles

            # # sprawdzenie, czy można zredukować listę tytułów
            # if (
            #     re.sub(r"\bthe\b", "", title, flags=re.I).strip().lower()
            #     == localtitle.lower()
            # ):  # np. film "The Batman"
            #     titles = [title]

            # czysczenie z "niepożądanych" znaków (w tym diakrytycznych)
            titles = [cleantitle.normalize(cleantitle.getsearch(t)) for t in titles]

            titles = list(filter(None, titles))  # usunięcie pustych
            titles = list(dict.fromkeys(titles))  # pozbycie się duplikatów

            titles0 = titles.copy()  # potrzebne do powiązania zadanego title i localtitle z wynikami

            # dodanie do późniejszego porównywania z nazwami plików
            self.titles = titles + self.titles

            self.titles = list(filter(None, self.titles))
            self.titles = list(dict.fromkeys(self.titles))
            # fflog(f"self.titles:{new_line}{new_line.join(self.titles)}")

            # przekształcenia tak jak dla titles (przyda się później)
            aliases2 = [cleantitle.normalize(cleantitle.getsearch(a)) for a in aliases2]

            # dla filmów można próbować redukować zapytania,
            #  ale dla seriali ponieważ może być doklejany numer odcinka
            #  i trzeba to robić oddzielnie dla tytułu oryginalnego i polskiego
            if not episode:
                aliases2 += titles
                aliases2 = list(dict.fromkeys(aliases2))
            # fflog(f"{aliases2=}")

            # """ serwis xt7 bardzo długo kazał czekać na wyniki, więc wymyśliłem
            # zapamiętywanie wyników, aby następne zapytania dotyczące tego samego tytułu
            # były szybciej zwracane użytkownikowi """
            # ostatni czas, jaki był potrzebny do zakończenia obsługi wszystkich requestów
            last_search_info = cache.cache_get("xt7_last_search_info", control.sourcescacheFile)
            if last_search_info:
                last_search_info = last_search_info["value"]
                last_search_info = literal_eval(last_search_info)
                last_total_time = int(last_search_info.get("total_time", 0))
            else:
                last_search_info = {}
                last_total_time = 0
            # fflog(f'{last_search_info=}')

            # funkcja pomocnicza
            def check_if_finished():
                results_cache_fin = cache.cache_get("xt7_results_finished", control.sourcescacheFile)
                # fflog(f'{results_cache_fin=} ')
                if results_cache_fin:
                    results_cache_val = results_cache_fin["value"]
                    if results_cache_val and klucz in results_cache_val:
                        results_cache_val = literal_eval(results_cache_val)
                        finished = results_cache_val[klucz]
                        return finished
                return None

            # czy wykonywać ponowny request do serwera, bo może można wykorzystać ostatnie wyniki
            # zależy od szukanych tytułów (rok i episod nie mają znaczenia)
            dont_request = False
            klucz = repr(titles0)
            results_cache_fin = cache.cache_get("xt7_results_finished", control.sourcescacheFile)
            # fflog(f'{results_cache_fin=} ')
            if results_cache_fin:
                results_cache_val = results_cache_fin["value"]
                results_cache_date = results_cache_fin["date"]

                if re.search(r']s[\do]{2}"', results_cache_val):
                    klucz += re.sub("(s.*?)(e.*)", r"\1", episode)
                elif re.search(r']s[\do]{2}e\d{2,4}"', results_cache_val):
                    klucz += episode
                elif re.search(r']e\d{2,4}"', results_cache_val):
                    klucz += re.sub("(s.*?)(e.*)", r"\2", episode)

                if results_cache_val:
                    results_cache_val = literal_eval(results_cache_val)

                if klucz not in results_cache_val:
                    # brak zgodności tytułów
                    fflog(f'brak zgodności tytułów, bo {klucz=} {results_cache_val=}', 0)
                    cache.cache_insert("xt7_results", "", control.sourcescacheFile)
                    cache.cache_insert("xt7_results_finished", "", control.sourcescacheFile)
                    cache.cache_insert("xt7_raw_results", "", control.sourcescacheFile)
                    #cache.cache_insert("xt7_trash", "", control.sourcescacheFile)
                else:
                    # tytuły się zgadzają
                    fflog(f'tytuły się zgadzają: {klucz=} {results_cache_val=}', 0)
                    """
                    # czy nie jest pusty i czy jest tam tytuł jako klucz
                    #if results_cache_val and klucz in results_cache_val:  # zdublowany warunek
                        #results_cache_val = literal_eval(results_cache_val)
                    """
                    # czy skończone, czy w trakcie (liczba to czas, jaki był wymagany do zakończenia wyszukiwania dla tych tytułów)
                    finished = results_cache_val[klucz]
                    # fflog(f'{finished=}')
                    now = int(time.time())
                    delta_t = now - int(results_cache_date)
                    # delta_t = 0  # dla testów tylko
                    if delta_t < (5 * 60):  # 5 minut
                        dont_request = True  # bezpieczniej dać także tu
                        if not finished:
                            timeout = control.settings.getInt("scrapers.timeout.1")
                            check_interval = 5  # w sekundach
                            fflog("... czekam na zakończenie poprzedniego requesta")
                            for i in range(
                                int(
                                    max(10, int(timeout - 10))
                                    / check_interval
                                )
                            ):  # czeka prawie do końca timeoutu
                                # fflog(f"pętla czekająca na zakończenie zapisu z poprzedniego requesta {i=}")
                                time.sleep(check_interval)
                                f = check_if_finished()
                                # fflog(f"?czy skończony poprzedni request: {f=}")
                                if f is None:
                                    dont_request = False  # choć nie wiem ile czasu zostało i czy nowy request zdąży się wykonać
                                    break
                                if f:
                                    dont_request = True
                                    break
                            # tu można by (w tej linijce) dać kod, gdy nie doczekaliśmy się skończenia poprzedniego requestu
                            if (not dont_request
                                and ( (timeout - int(time.time()) - now)
                                        < (last_total_time + 10)
                                )
                            ):
                                return []  # bo nie zdąży się wykonać następny request
                        else:
                            dont_request = True
            fflog(f'{dont_request=}', 0)

            saved_to_cache = False

            last_extended_search = last_search_info.get("extended_search")
            now_extended_search = control.settings.getBool("xt7.extended_search")
            if dont_request:
                if last_extended_search is False and now_extended_search is True:
                    dont_request = False
                    fflog(f'{dont_request=}', 0)

            def korekty_dla_wyszukiwarki_xt7(title):
                # korekty specyficzne dla wyszukiwarki xt7
                title = title.replace(" - ", " ")  # pomaga np. dla "mission impossible - ghost protocol"
                title = title.replace("-", "_")  # pomogło dla filmu "'E.T. the Extra-Terrestrial"
                title = title.replace(". ", ".")  # np. dla serialu Mr. Robot
                title = title.replace(".", "_")
                # title = title.replace(".", "_") if "_" in title else title  # 'Book Club.Następny rozdział'
                title = title.replace(" ", "_")  # np. "transformers_rise_of_the_beasts"
                title = title.replace(",", "")  # na przypadek "Poszukiwany, poszukiwana"
                title = title.replace("#", "")  # na przypadek "#BringBackAlice"
                title = re.sub(r'_?(\d)⁄', r'_\1_', title)  # na przypadek "Naga Broń 2 1/2"
                title = title.replace("_", " ")  # teraz już podkreślenie niepotrzebne
                title = title.replace("&", " and ")  # "Blood & Treasure" albo "Dungeons & Dragons"
                title = title.replace("  ", " ")  # ewentualnie uprzątnięcie
                return title

            # w poprzednich wynikach może nie być źródeł dla innego odcinka
            if dont_request:
                for title1 in titles:
                    self.titles = [korekty_dla_wyszukiwarki_xt7(title1)] + self.titles
                self.titles = list(dict.fromkeys(self.titles))
                self.get_pages_content(None, year, "", episode, premiered, aliases)
                results = self.results
                if not results:
                    dont_request = False
                    fflog(f'{dont_request=}', 0)

            if dont_request:
                fflog(f"NIE wykonuje ponownego requestu, bo od ostatniego minęło {delta_t} sek. ( < 300 )")
            else:
                # oznaczenie, że proces jeszcze nie został skończony
                cache.cache_insert(
                    "xt7_results_finished",
                    repr({klucz: 0}),
                    control.sourcescacheFile
                )
                saved_to_cache = True

                aliases3 = [korekty_dla_wyszukiwarki_xt7(a) for a in aliases2]  # przygotowanie do wybrania lepszej frazy do wyszukiwarki
                # fflog(f'{aliases3=}')

            def znajdz_wspolny_prefiks_wyrazowy(tytuly):
                if not tytuly:
                    return ""
                pierwszy_tytul = tytuly[0]
                wyrazy_pierwszego_tytulu = pierwszy_tytul.split(" ")
                for i, wyraz in enumerate(wyrazy_pierwszego_tytulu):
                    for tytul in tytuly[1:]:
                        wyrazy_drugiego_tytulu = tytul.split(" ")
                        if i >= len(wyrazy_drugiego_tytulu) or wyrazy_drugiego_tytulu[i] != wyraz:
                            return " ".join(wyrazy_pierwszego_tytulu[:i])
                return pierwszy_tytul

            self.login()

            # zapisanie podstron "notes" oraz "pliki" do cache
            # potrzebne do awaryjnego odzyskiwania źródeł
            biblio_cache, biblio_links = self.files_on_user_account(from_cache=False)[0:2]

            title_phrases_exceptions = titles2 = episode_added = last_chance = originalname = None
            
            customTitles = "customTitles" in sys.argv[2]

            if not dont_request:
                fflog(f'{self.search_link=}')  # informacyjnie
                pass

            monitor = control.monitor

            now0 = int(time.time())

            for title1 in titles:
            #title2 = titles[0]
            #for title1 in [title2]:
                # fflog(f"titles: ({len(titles)}) \n" + "\n".join(titles))  # kontrola
                title = title1

                if isinstance(title,str):

                    if not customTitles:
                        title = korekty_dla_wyszukiwarki_xt7(title)

                    if title not in self.titles:
                        self.titles = [title] + self.titles  # dodanie do późniejszego porównywania z nazwami plików

                    if dont_request:
                        continue

                    if not customTitles:
                        # może uda się znaleźć lepszą frazę do wysłania do wyszukiwarki?
                        #if len(titles) == len(titles0):
                        if title1 in titles0:
                            wspolny_prefiks = znajdz_wspolny_prefiks_wyrazowy([korekty_dla_wyszukiwarki_xt7(t) for t in titles if isinstance(t,str)])
                            # fflog(f'{titles=} {wspolny_prefiks=}')
                            if wspolny_prefiks or len(wspolny_prefiks) > 3:
                                if wspolny_prefiks not in aliases3:
                                    aliases3.append(wspolny_prefiks)

                        # szukanie aliasu w zadanym tytule
                        requesty_for_title = [a for a in aliases3 if re.search(f"^{re.escape(a)}", title)] if title1 in titles0 else []
                        # fflog(f"{requesty_for_title=}")

                        # czy obie poniższe dadzą takie same rezultaty?
                        # requesty_for_title.sort()
                        requesty_for_title.sort(key=lambda e: len(e))
                        # fflog(f"{requesty_for_title=}")

                        title_r = requesty_for_title[0] if requesty_for_title else title
                    else:
                        title_r = title

                    """ przeniosłem wyżej
                    # wg sugestii jednego z testerów ma pomóc na "blood & treasure" albo "Dungeons & Dragons"
                    if not customTitles:
                        if "&" in title_r:
                             title_r = title_r.replace("&", " and ")  # ("wplik" inaczej niż "wrzucaj" wyszukiwał)
                             title_r = title_r.replace("  ", " ")
                    """

                    if not customTitles:
                        title_r = re.sub("^(the|an?) ", "", title_r, 1)  # może zwiększyć ilość wyników
                        pass

                    if len(title_r) < 3:  # trzeba tak dla krótkich tytułów  "To" ("It"), "65"
                        if episode:
                            title_r += f' {episode!s}'
                        else:
                            title_r += f' {year!s}'

                    # dziwna przypadłość wyszukiwarki - nie wyszukuje "batman", ale "batman_" już tak (to samo dla "kruk", ale dla np. "dom" nie ma problemu)
                    # wciąż szukam najlepszego znaku, bo różne serwery różnie je traktują
                    # if " " not in title_r:
                    if not re.search(r"\W", title_r.rstrip("%")):
                        if title_r[-1] != "%":
                            title_r += "%"

                    titles_r = [title_r]
                    if now_extended_search:
                        if " " in title_r:  # pod OBOOM zanim ogarną swą wyszukiwarkę
                            # titles_r += [title_r.replace(" ", ".")]  # od razu
                            titles += [(title_r.replace(" ", "."),)]  # na koniec
                            pass

                else:
                    title = title[0]
                    title_r = title
                    titles_r = [title_r]


                for title_r in titles_r:

                    if monitor.abortRequested():
                        fflog(f'przerwanie wyszukiwania (z powodu sygnału zamknięcia Kodi)')
                        return sys.exit()
                    # ewentualnie jeszce wykrywanie sygnału przerwania wyszukiwania źródeł
                    if control.window.getProperty("blocked_sources_extend") == 'break':
                        fflog(f'przerwanie dalszego wyszukiwania')
                        dont_request = True
                        break

                    if now_extended_search:
                        if episode and re.search(r"s(0\d|\d0)", title_r):
                            titles_r += [re.sub(r"s(0\d|\d0)", lambda x: x[0].replace("0", "o"), title_r)]  # pod OBOOM
                            pass

                    # fflog(f'{title_r=} {self.titles_requested=}')
                    if title_r not in self.titles_requested:

                        self.titles_requested.append(title_r)
                        # fflog(f"self.titles_requested: ({len(self.titles_requested)}) \n" + "\n".join(self.titles_requested))  # kontrola

                        fflog(f"WYSŁANIE zapytania: {title_r!r}")

                        now1 = int(time.time())  # do pomiaru czasu obsługi zapytania przez serwer

                        post = {"search": title_r, "type": "1"}  # co ma być wysłane
                        pre_res = self.session.post(self.base_link+self.search_link, headers=self.headers, data=post)  # wysłanie zapytania (POST)
                        pre_res = pre_res.text  # odpowiedź z serwera
                        pre_res = pre_res.replace("\r", "").replace("\n", "")  # lepsza czytelność

                        now2 = int(time.time())
                        fflog(f" Czas odpowiedzi z serwera: {now2 - now1} sek.")

                        # sprawdzenie co jest w odpowiedzi
                        page_block = re.search('class="page-list"(.+?)</div>', pre_res, re.IGNORECASE)
                        if page_block is not None:
                            pages = len(re.findall("href=", page_block.group()))
                            #self.pages.append({title1: pages})
                            self.pages.append({title_r: pages})
                            fflog(f" sprawdzanie otrzymanych wyników ({pages} podstr.)")
                            # for page in range(pages):
                            #     self.get_pages_content(page + 1, year, title, episode)
                            self.get_pages_content(range(pages), year, title, episode, premiered)

                            results = self.results  # wyniki po filtracji

                            if not results:
                                fflog(' brak pasujących rekordów')

                            # dodanie do cache w razie jakby kolejna pętla nie zdążyła się wykonać a nadszedł Timeout
                            # fflog(f"Łącznie zapisano w cache rekordów: {len(results)}")
                            klucz = (
                                repr(titles0)
                                # if len(titles) == len(titles0) or not episode
                                if not episode_added
                                # else repr(titles0) + episode
                                # else repr(titles0) + re.sub("(s.*?)(e.*)", r"\1", episode)
                                else repr(titles0)  # chyba rezygnuje z tego bo i tak sprawdzam dodatkowo, czy będą źródła z cachu
                            )
                            # dane przefiltrowane
                            cache.cache_insert(
                                "xt7_results",
                                repr({klucz: results}),
                                control.sourcescacheFile
                            )
                            # dane "surowe" (wykorzystywane, jak nie jest robiony ponowny request)
                            cache.cache_insert(
                                "xt7_raw_results",
                                repr({klucz: self.raw_results}),
                                control.sourcescacheFile
                            )
                            saved_to_cache = True
                        else:
                            fflog(" nie otrzymano wyników")
                            # self.pages.append({title_r: 0})  # czy można wówczas zastąpić self.titles_requested ?

                    else:
                        fflog(f"Pominięto wysłanie zapytania {title_r!r} (bo już wystąpiło takie)")
                        pass

                #fflog(f'czy ostatni? {title1=} {titles[-1]=}')
                if ( title1 == titles[-1]  # ostatni
                     and (not results
                          # or True  # tylko do testów
                          or now_extended_search
                         )
                    ):
                    max_p = max((val for p in self.pages for val in p.values()), default=0)
                    #fflog(f'ostatni, więc {max_p=} {self.pages=}')

                    # próba wykluczenia pewnych fraz z tytułów
                    if (
                        episode  # tylko dla seriali
                        and (
                            not self.pages  # brak wyników z serwera
                            or max_p == 1
                            or now_extended_search
                        )
                        # and not titles2  # aby nie było nieskończoności
                        and title_phrases_exceptions is None  # aby nie było nieskończoności
                    ):
                        try:
                            title_phrases_exceptions = source_utils.antifalse_filter_exceptions
                        except:
                            title_phrases_exceptions = []
                        fflog(f'{title_phrases_exceptions=}', 0)
                        for ex in title_phrases_exceptions:
                            titles2 = [re.sub(rf"([_\W]+{ex})", "", t, flags=re.I) for t in titles if isinstance(t,str)]
                            titles2 = [t for t in titles2 if t not in titles]
                            titles += titles2  # rozszerzenie pętli
                        if titles2:
                            fflog(f'skrócono tytuł')
                            continue

                    # wyszukiwarka xt7 zwraca maksymalnie tylko 4 podstrony (jakieś ograniczenie)
                    # i jak jest bardzo dużo odcinków dla danego serialu, to przy wyszukiwaniu tylko samego tytułu
                    # może okazać się, że odcinka, którego szukamy nie będzie w wynikach, dlatego
                    # dodanie numeru odcinka do tytułu
                    if (
                        episode
                        and self.pages  # są jakieś wyniki z serwera
                        and not episode_added  # aby nie było nieskończoności
                    ):
                        if (max_p >= 4  # czasami to już bym od 3 nawet sprawdzał
                            # or " " not in "".join(titles0)  # nie pamiętam dlaczego tak (pewnie z jakimś tytułem miałem problem)
                            # or True  # do testów tylko
                            or now_extended_search
                           ):
                            for p in self.pages:
                                t = [*p][0]  # tytul
                                if p[t] == max_p:  # tylko dla tytułów, ktore miały najwięcej podstron
                                    if not re.search(r"e\d?\d{2}", t, flags=re.I):
                                        s_OrAnd_e = re.sub("(s.*?)(e.*)", r"\1", episode)
                                        sep = " " if " " in t else "."
                                        t2 = f"{t}{sep}{s_OrAnd_e}"
                                        if t2 not in titles:
                                            titles.append((t2,))  # rozszerzenie pętli
                                            episode_added = True
                            if episode_added:
                                continue

                    # niektóre seriale nie mają sezonów
                    if (
                        episode_added  # tylko gdy poprzedni wariant był uruchomiony
                        and not last_chance  # aby nie było nieskończoności
                        and re.search("s01(e.*)", episode, flags=re.I)  # tylko dla 1 sezonu
                    ):
                        for p in self.pages:
                            t = list(p)[0]  # ekwiwalent wcześniejszego ( [*p][0] )
                            if re.search("s[0o]1(e.*)?", t, flags=re.I):  # tylko dla tych co miały dokładane
                                t = re.sub(r"[\W_]s[0o]1(e.*)?", "", t)
                                ep_only = re.sub("s01(e.*)", r"\1", episode)
                                sep = " " if " " in t else "."
                                t2 = f"{t}{sep}{ep_only}"
                                if t2 not in titles and (t2,) not in titles:
                                    titles.append((t2,))  # rozszerzenie pętli
                                    last_chance = True
                        if last_chance:
                            continue

                    # wykorzystanie oryginalnego tytułu nieanglojęzycznego
                    if (
                        not originalname
                        # and not episode  # tylko dla filmów
                    ):
                        originalname = [a for a in aliases if "originalname" in a]
                        originalname = originalname[0]["originalname"] if originalname else ""
                        if (
                            originalname
                            and originalname != title0
                            and originalname != localtitle
                            # and re.search(r"[a-z0-9]", originalname, flags=re.I)  # aby wykluczyć japońskie znaki
                            and not source_utils.czy_litery_krzaczki(originalname)  # aby wykluczyć japońskie znaki
                        ):
                            if originalname not in titles:  # jeśli jakimś cudem już taka fraza byłaby
                                titles.append(originalname)  # rozszerzenie pętli
                                continue


            # aby do każdego szukania nie dowalać pozycji z bilioteki
            if control.settings.getBool("sources.title_validation_filter") and control.settings.getBool("sources.title_validation_filter.tx7"):
                rows = []
                if biblio_cache:
                    for b in biblio_cache.values():
                        href = b.get("url")
                        host = b.get("source")
                        fnme = b.get("filename")
                        size = b.get("size")
                        rows.append(f'<tr class="dowalona_z_biblioteki">\
                                        <td><input value="{href}"></td>\
                                        <td>{host}</td>\
                                        <td><label>{fnme}</label></td>\
                                        <td>{size}</td>\
                                    </tr>')
                elif biblio_links:
                    for fn in biblio_links:
                        href = fn[0]
                        fnme = unescape(unquote(fn[0].rpartition("/")[-1]))
                        rows.append(f'<tr class="dowalona_z_biblioteki">\
                                        <td><input value="{href}"></td>\
                                        <td></td>\
                                        <td><label>{fnme}</label></td>\
                                        <td></td>\
                                    </tr>')
                if rows:
                    self.get_pages_content(None, year, "", episode, premiered, aliases, rows)
                    results = self.results


            if saved_to_cache:
                now3 = int(time.time())
                tt = now3 - now0
                fflog(f"Łączny czas operacji = {tt} sek.")
                # oznaczenie, że proces skończony
                cache.cache_insert(
                    "xt7_results_finished",
                    repr({klucz: max(1, tt)}),
                    control.sourcescacheFile
                )
                # informacji o czasie całej operacji
                # może się przydać do analizy, jak długo czekać następnym razem
                cache.cache_insert("xt7_last_search_info", repr({
                    "total_time": max(1, tt),
                    "klucz": klucz,
                    "titles_r": titles_r,
                    "extended_search": now_extended_search,
                    }), control.sourcescacheFile)


            fflog(f' Zatwierdzonych rekordów: {len(results)} ')

        except Exception:
            fflog_exc(1)
            results = self.results  # zwracam co się da
            # oznaczenie, że proces przerwany (ala skończony)
            cache.cache_insert("xt7_results_finished", "", control.sourcescacheFile)  # problem, jak baza zablokowana
            # if "check_if_finished" in locals() and "klucz" in locals() and klucz:
            #     if not check_if_finished():
            #         cache.cache_insert(
            #             "xt7_results_finished",
            #             repr({klucz: None}),
            #             control.sourcescacheFile
            #         )

        # tą sekwencję można też dać do funkcji get_pages_content() (na końcu)
        # sprawdzenie, czy coś, co było wcześniej odrzucone, może zostało jednak dodane do źródeł
        if self.trash:
            self.trash = list(dict.fromkeys(self.trash))  # pozbycie się duplikatów
            for item in self.trash[:]:  # kopia, bo będzie usuwanie elementów
                if any(item in r for r in self.results):  # szukanie nazwy w każdym z rekordów
                    # główny cel tego fragmentu kodu
                    fflog(f"+ Przywrócono {unescape(unquote(item))!r}")
                    self.trash.remove(item)

        """
        # ta chyba tak samo jak powyższa (może być i tu i tam)
        # sprawdzenie, czy coś, co było wcześniej odrzucone, może zostało jednak dodane do źródeł
        if self.trash2:
            self.trash2 = list(dict.fromkeys(self.trash2))  # pozbycie się duplikatów
            for item in self.trash2[:]:  # kopia, bo będzie usuwanie elementów
                if item in self.results:
                    self.trash2.remove(item)

        # ta musi być tutaj, bo jest w niej analiza, która musi być zrobiona na samym końcu
        # zapisanie kosza
        self.trash2 = []  # do czasowego wyłączenia
        if self.trash2:
            # fflog(f'Analizowanie kosza (rekordów: {len(self.trash2)})')
            trash2 = self.trash2  # dane do przepuszczenia jeszcze przez funkcje sources()
            trash2 = self.sources(self.trash2, "", "", True)  # to musi być analizowane na samym końcu
            # fflog(f'{len(trash2)=}')
            cache.cache_insert("xt7_trash", repr(trash2), control.sourcescacheFile)
            # fflog('zapisano kosz do cache')
        """

        return results



    def prepare_pattern_for_titles(self, title, year="", episode=""):
        """tworzy wzorzec dla tytułów do porównywania z nazwami plików"""

        title_pat = title.lower()

        title_pat = re.escape(title_pat)
        # title_pat = re.sub(r"\\ ", " ", title_pat)  # spacje zostawiam
        title_pat = title_pat.replace(r"\ ", " ")  # spacje zostawiam

        # zastosowanie wyjątków na pewne frazy (stworzyłem dla serialu "Scream The TV series")
        # ale nie wiem, czy to dalej potrzebne
        # lepiej dopisywać zmiany na www.themoviedb.org (konto jest darmowe)
        # if episode:
        #     antifalse_filter_exceptions = source_utils.antifalse_filter_exceptions
        #     for ex in antifalse_filter_exceptions:
        #         # titles_pat = [re.sub(rf"([ \W]+{ex})", r"(\1)?", t, flags=re.I) for t in titles_pat]
        #         title_pat = re.sub(rf"([ \W]+{ex})", r"(\1)?", title_pat, flags=re.I)
        #         pass

        # znaki nieliterowe
        title_pat = re.sub(r'(?!\\?[&:,[\] .–-])(\\?)(\W)',  r'[\2 .–-]?', title_pat)
        title_pat = title_pat.replace("[^", r"[\^")  # korekta
        # poniższe dla np. "miraculous: biedronka i czarny kot. film" -> "miraculous - biedronka i czarny kot - film"
        # title_pat = title_pat.replace(r'\.', '[ .–-]+')
        # title_pat = re.sub(': ?', '[: .–-]+', title_pat)
        title_pat = re.sub(r' *(\\(\.|-)|–(?![^\[]*\])) *', '[ .–-]+', title_pat)
        title_pat = re.sub(r"(\[ \.–\-\])\+$", r"\1?" , title_pat)  # korekta dla dla "E.T.1982"
        title_pat = re.sub(' *([:,]) *', r'[\1 .–-]+', title_pat)
        # title_pat = re.sub(r"(\[[+=] \.–\-\])\?" ,r"\1+" , title_pat)  # matematyczne znaki (nie testowane jeszce)
        # a co z innymi znakami, jak "?", "!" - lepiej je chyba na samym początku przerobić
        # title_pat = re.sub(r'(((?!\\?[&:,[\]()^*+?/ ._–-])\W)+)(?![^\[]*\])', r"[\1 ._–-]?", title_pat)
        # title_pat = re.sub(r'(?!\\?[&:,[\]+ .–-])(\\?)(\W)',  r'[\2 .–-]?', title_pat)  # można tu, ale trzeba dodatkowo plusa obsłużyć

        # dla konkretnego zapisu ułamków jakie występują np. w "Naga broń 2 1⁄2"
        title_pat = re.sub(r'(\d )((\d) (\d( )?))', r'\1(i )?\3[ .,/-]\4', title_pat)  # "Naga broń 2 i 1-2"
        # poniższe związane jest z powyższym (może to "jednorazowa" akcja?)
        title_pat = re.sub(r'(\d)( )([a-zA-Z])', r'\1\2*\3', title_pat)  # np."2 The" -> "2The"

        # przekształcenie odstępów między wyrazami
        # title_pat = re.sub(r"[ ](?![^\[]*\])", "[ .–-]", title_pat)  # przekształcenie odstępów między słowami
        title_pat = re.sub(r"[ ](?![^\[]*\])", "[ .–-]+", title_pat)  # plus choć niby niepotrzebny przydaje się (łatwiej czyścić zdublowane)
        # ponieważ wyżej dodałem "+" na końcu, to mogą być konieczne następujące korekty:
        title_pat = title_pat.replace("+?", "?")  # bo inaczej zmieni się znaczenie
        title_pat = title_pat.replace("+*", "*")  # to bardzo ważne
        title_pat = title_pat.replace("++", "+")  # to raczej też
        # ewentualnie można jeszcze:
        # title_pat = re.sub(r"(\[ \.–\-\]\+?){2,}", "[ .–-]+", title_pat)  # eliminacja zdublowanych "odstępów", czyli spacji
        title_pat = re.sub(r"(\[(\W*?) \.–\-\]\?){2,}", lambda x: "["+re.sub(r"\[(\W*?) \.–\-\]\?", r"\1", x.group())+" .–-]*", title_pat)
        title_pat = re.sub(r"(\[(\W*?) \.–\-\]\+){2,}", lambda x: "["+re.sub(r"\[(\W*?) \.–\-\]\+", r"\1", x.group())+" .–-]+", title_pat)
        title_pat = re.sub(r"(\[(\W*?) \.–\-\][?+]?){2,}", lambda x: "["+re.sub(r"\[(\W*?) \.–\-\][?+]?", r"\1", x.group())+" .–-]+", title_pat)
        # nie wiem, czy trzeba jeszce  + z * ( = +)  lub/oraz  * z * ( = *)

        # ampersand
        title_pat = title_pat.replace(r"\&", r"(\&|and|i)")  # "Dungeons & Dragons: Złodziejski honor"
        # pattern = re.sub(r"\b(?<!\|)and(?!\|)\b" , r"(and|\&)", pattern)  # nie testowałem jeszcze

        # # matematyczne - tylko trzeba dodać wyjątki na początku - nie testowałem jeszcze
        # title_pat = title_pat.replace(r"\+", r"(\+|plus)")
        # title_pat = title_pat.replace(r"\-", r"(\+|minus)")

        # cyfry na słowa lub słowa na cyfry (także rzymskie)
        # title_pat = source_utils.numbers_in_pattern(title_pat)

        # obsługa znaków diakrytycznych ("akcentów")
        # title_pat = source_utils.diacritics_in_pattern(title_pat, mode=1)  # ą -> [ąa]
        title_pat = source_utils.normalize_unicode_in_pattern(title_pat)  # metoda bardziej uniwersalna

        # if control.settings.getBool("sources.allow_numbers_instead_of_letters_in_titles"):  # może dorobić takie coś?
        # na takie twory jak "Mira3ulum – Bied3onka i Cz3rny K3t"
        # czy zrobić to jako opcja?
        # title_pat = re.sub(r"(?<!\[)([^\W\d_])(?![?\]])", r"[\1\\d]", title_pat)
        # title_pat = title_pat.replace("?]", "?\d]")
        # title_pat = title_pat.replace("][", "]\d?[")  # do powyższego fix na "Noc7ne gr7affiti"

        return title_pat


    def prepare_pattern_for_titles_v2(self, title):
        """alternatywna wersja (ma być prostsza, choć to się jeszcze okaże)"""

        title = title.lower()  # opcjonalnie, bo wcześniej to jest robione

        # pattern = re.sub(r'(((?!\\?\&)\W)+)', r"[\1 .–-]+", title)  # znaki nieliterowe, oprócz "&" (obsłużony jest niżej)
        pattern = re.sub(r'([^\w&]+)', r"[\1 .–-]+", title)  # prostszy zapis, ale nie można wówczas stosować re.escape
        pattern = re.sub(r'(\[[^ \w]+ \.–\-\])\+', r'\1*', pattern)  # korekta dla pojedynczych znaków, gdy nie ma po nich spacji
        # pattern = re.sub(r'\[ *([^ \w]+ \.–-])\+', r'[\1*', pattern)  # dla niektórych przypadków trochę lepsze od powyższego
        # poniższe 3 mogą być niezbędne, jak nie był robiony escape znaków
        pattern = pattern.replace("[^", r"[\^")
        pattern = pattern.replace("[]", r"[\]")
        pattern = pattern.replace("[[", r"[\[")
        # sprzątanie
        # pattern = re.sub(r" *(\\?\W)\1+", r"\1", pattern)  # sprzątanie zdublowanych znaków
        # pattern = re.sub(r"(\[) *(\W*?)( *\\?[.–-])+(?= )", r"\1\2", pattern)  # aby nie powielać znaków ".–-"
        # pattern = re.sub(r"(\[) *(\W*?)( *(\\\.|–|\\\-))+(?= )", r"\1\2", pattern)  # alternatywa powyższego zapisu
        pattern = re.sub(r"(?<=\[)\W+?(?= \.–-])", lambda x: "".join(list(dict.fromkeys(re.sub("[ .–-]", "", x[0])))), pattern)

        # nie wiem czy warto
        # pattern = pattern.replace("[ .–-]+", "[ .–-]")  # reprezentacja spacji

        # ampersand
        pattern = pattern.replace(r"&", r"(\&|and|i)")  # "Dungeons & Dragons: Złodziejski honor"
        # pattern = re.sub(r"\b(?<!\|)and(?!\|)\b" , r"(and|\&)", pattern)  # nie testowałem jeszcze

        # dla konkretnego zapisu ułamków jakie występują np. w "Naga broń 2 1⁄2"
        sp = "[ .–-]+"  # uważać na plus na końcu
        spe = re.escape(sp)
        pattern = re.sub(rf'(\d{spe})((\d){spe}(\d({spe})?))', rf'\1(i{sp})?\3[ .,/-]\4', pattern)  # "Naga broń 2 i 1-2"
        # poniższe związane jest z powyższym (może to "jednorazowa" akcja?)
        pattern = re.sub(rf'(\d)({spe})([a-zA-Z])', r'\1\2*\3', pattern)  # np."2 The" -> "2The"
        pattern = pattern.replace("+*", "*")

        # i inne jak:
        title_pat = pattern  # dla kompatybilności

        # cyfry na słowa lub słowa na cyfry (także rzymskie)
        # title_pat = source_utils.numbers_in_pattern(title_pat)

        # obsługa znaków diakrytycznych ("akcentów")
        # title_pat = source_utils.diacritics_in_pattern(title_pat, mode=1)  # ą -> [ąa]
        title_pat = source_utils.normalize_unicode_in_pattern(title_pat)  # metoda uniwersalniejsza

        # if control.settings.getBool("sources.allow_numbers_instead_of_letters_in_titles"):  # może dorobić takie coś?
        # cyfry zamiast liter np. "Mira3ulum – Bied3onka i Cz3rny K3t"
        # title_pat = re.sub(r"(?<!\[)([^\W\d_])(?![?\]])", r"[\1\\d]", title_pat)
        # title_pat = title_pat.replace("?]", "?\d]")
        # do powyższego fix na np. "Noc7ne gr7affiti"
        # title_pat = title_pat.replace("][", "]\d?[")

        pattern = title_pat
        return pattern


    def get_pages_content(self, page, year, title="", episode="", premiered="", aliases=None, rows=None):
        """Funkcja filtruje wstępnie wyniki otrzymane z serwera
        sprawdzając czy pasują któreś z elementów: tytuł, rok, numer odcinka
        """
        # fflog(f'{title=} {year=} {episode=} {page=} {premiered=}')
        if not rows:
            if page:
                # if type(page) is range:
                if isinstance(page, range):
                    pages = page
                else:
                    pages = [page-1]
                rows = []
                for page in pages:
                    page += 1
                    # pobranie podstrony wyników
                    # fflog(f' pobranie ({page}) strony wyników')
                    res = self.session.get(
                        self.base_link + self.support_search_link.format(str(page)),
                        headers=self.headers,
                    ).text
                    row = client.parseDOM(res, "tr")[1:]
                    fflog(f' [{page}] strona: {len(row)} wyników')
                    rows += row
                fflog(f' Do przeanalizowania: {len(rows)}') if isinstance(pages, range) and page > 1 else ""
                self.raw_results += rows
                res = row = None  # czyszczenie ramu
            else:
                # pobranie wcześniej zapisanych danych
                results_cache = cache.cache_get("xt7_raw_results", control.sourcescacheFile)
                if results_cache and "value" in results_cache and results_cache["value"]:
                    results_cache = literal_eval(results_cache["value"])
                    # odczytanie danych nie znając klucza
                    rows = [results_cache[k] for k in results_cache][0]
                    fflog(f' Analizowanie wcześniejszych wyników [{len(rows)}]')
                    results_cache = None
                else:
                    fflog(" Brak danych do analizy")
                    return
        else:
            # to przeważnie dla pozycji z biblioteki
            # fflog(f' Analizuje zadane rekordy [{len(rows)}] {rows=}')
            pass

        if episode:
            # mógłbyć dołożony numer odcinka do zapytania
            #title = re.sub(r"(s\d{2})?e\d{2,3}$", "", title).rstrip("._ ")
            title = re.sub(r"(s[0o]?\d{1,2})?[ _.]?(e[\do]{2,4})?$", "", title).rstrip("._ ")
        if year:
            # mógłbyć dołożony rok do zapytania
            # title = title.replace(year, "", 1).rstrip("_ ")
            title = "".join(title.rsplit(year, 1)).rstrip("._ ")
            # ciekawe czy jest taki tytuł co ma rok taki sam jak data produkcji?
        title = title.rstrip("%")  # czy to nie popsuje nic ?
        # fflog(f'{title=}')
        #if " " not in title:
        title = title.replace(".", " ")

        # granice frazy (alternatywa dla \b)
        b1 = r"(?:^|(?<=[([ _.-]))"  # początkowa
        b2 = r"(?=[)\] _.-]|$)"  # końcowa

        # wzorzec roku
        # year_pat = r"([ ._]*[(\[]?(19\d[\dO]|[2-9][\dO]{3})[)\]]?)"
        yr_uni_pat = r"\b(19\d[\dOo]|2[Oo0][\dOo]{2})\b"  # (1900 - 2099)
        # yr_uni_pat = f"{b1}{yr_uni_pat}{b2}"
        # yr_uni_pat = f"[ ._([]*{yr_uni_pat}"
        if year:
            year_pat = f"{b1}{year}{b2}".replace("0", "[0Oo]")  # wzorzec dla konkretnej daty (roku)

        # wzorzec przydatny do sprawdzania, czy w ogóle jest taka sekwencja w nazwie pliku, sugerując jednocześnie, że to może być odcinek serialu
        # ep_uni_pat = r"((S\d{1,2})?[.,-]?E\d{2,3}|\bcz\.|\bodc\.|\bep\.|episode|odcinek|[\(\[]\d{2,3}[\)\]]|\- \d{2,3} [([-]|\bs\d{2}\b|\b\dx\d{2}\b)"  # łapie 'Tesciowie.2.2023.PL.1080p.WEB-DL.x264.AC3-S78.mp4'
        ep_uni_pat = r"((S\d{1,2})?[.,-]?E\d{2,4}|\bcz\.|\bodc\.|\bep\.|episode|odcinek|[\(\[]\d{2,3}[\)\]]|\- \d{2,3} [([-]|\b\dx\d{2}\b)"
        ep_uni_pat = ep_uni_pat.replace(r"\d", r"[\dO]").replace("0", "[0O]")  # czasami zamiast 0 wstawiane jest O

        ep_uni_pat2 = r"(S\d{2})?[.,-]?(E(\d{2,4}))"
        ep_uni_pat2 = ep_uni_pat2.replace(r"\d", r"[\dO]")  # czasami zamiast 0 wstawiane jest O

        # zmienne do zapamiętania stworzonego raz filtru
        dodatkowy_filtr = self.dodatkowy_filtr
        dodatkowy_filtr2 = self.dodatkowy_filtr2

        # jeszcze nie ma takiej opcji w ustawieniach
        allow_filename_without_year = True
        # allow_filename_without_year = control.settings.getBool("sources.allow_filename_without_year_within")

        if control.settings.getBool("sources.title_validation_filter") and control.settings.getBool("sources.title_validation_filter.tx7") and not self.dodatkowy_filtr:

            titles = self.titles  # zaczytanie wcześniej wybranych (m.in. aliasów)

            titles = [t.lower() for t in titles]
            titles = list(dict.fromkeys(titles))  # usunięcie duplikatów

            # dodanie bieżącego tytułu do listy (jeśli go tam jeszce nie ma)
            if title and title not in titles:
                titles = [title] + titles

            # opcjonalnie (może pomóc)
            # "spirited away: w krainie bogów" -> "w krainie bogów - spirited away"
            tmp = []
            for t in titles:
                if ": " in t and "-" not in t:
                    temp1 = " - ".join(t.split(": ")[::-1])
                    if temp1 not in titles:
                        tmp += [temp1]
            if tmp:
                titles += tmp

            fflog(f"titles (z aliasami): ({len(titles)}) \n" + "\n".join(titles), 0)  # kontrola

            # titles_pat_list = [self.prepare_pattern_for_titles(t) for t in titles]
            titles_pat_list = [self.prepare_pattern_for_titles_v2(t) for t in titles]

            titles_pat_list = list(dict.fromkeys(titles_pat_list))  # usunięcie duplikatów

            fflog(f"titles_pat_list: ({len(titles_pat_list)}) \n" + "\n".join(titles_pat_list), 0)  # kontrola

            title_pat = f'({"|".join(titles_pat_list)})'  # połączenie w 1 string

            # czasami są jeszcze takie przed rokiem
            res_pat = r"[ ._]*[(\[]?(720|1080)[pi]?[)\]]?"

            if episode or allow_filename_without_year:
                # wzorzec dla rozdzielczości
                res_pat = r"\b(SD|HD|UHD|2k|4k|480p?|540p?|576p?|720p?|1080[pi]?|1440p?|2160p?)\b"

                # wzorzec czasami spotykanych fraz
                # custom_pat = '([ ._][a-z]{2,})'  # za duża tolerancja i trafić może na ostatnie słowo innego tytułu np. "Titans go" dla filmu "Titans"
                custom_pat = r"\b(lektor|subbed|napisy|dubbing|polish|po?l(dub|sub)?|us|fr|de|dual|multi|p2p|web[.-]?(dl)?|remux|3d|imax)\b"  # trudnosć polega na przewidzeniu wszystkich możliwości

            # nazwa jakiejś grupy ludzi (powinna być na samym początku)
            # tylko nie wiem jakie mogą być dozwolone kombinacje
            # group_pat = r"\[[ .\-a-z]{3,}\]"
            # group_pat = r"\[[ .\-\w]{3,}\]"
            group_pat = r"^[.[][^.[\]]{3,}[.\]]"

            # rozszerzenia plików
            ext_pat = f'({"|".join(self.VIDEO_EXTENSIONS)})'.replace(".", "")

            if not episode:  # czyli dla filmów

                if allow_filename_without_year:
                    after_pat = fr"(\[\w*?\]|{res_pat}|{custom_pat}|{ext_pat}$)"
                else:
                    after_pat = yr_uni_pat

                # końcowy wzorzec do porównywania z nazwą pliku
                # if not self.tit_val_filt_for_one_title:  # to chyba już niepotrzebne
                if True:  # na razie tak
                    dodatkowy_filtr = re.compile(
                        # fr'(^|[/-]|  |\d{{1,2}})\W?(\b|_|\d{{1,2}}|^){title_pat}\d?(?=\b|[ ._]){year_pat}',
                        # rf"(^|[/-]|  |\d{{1,2}})\W?(\b|_|\d{{1,2}}|^){title_pat}([ ._-]{title_pat})?\d?(?=\b|[ ._]){year_pat}",
                        # rf"(^|[/-]|  |\d{{1,2}})\W?([ ._-]?{title_pat})+[ ._-]?\d?{year_pat}",
                        # rf"^\d{{0,2}}\.?\W?({title_pat}\d?[ ._/()-]{{1,4}})+[ ._-]?\d?{year_pat}?",
                        # rf"^(\d{{1,2}}|{yr_uni_pat}|{group_pat})?[ .-]*(\W?{title_pat}[ .-]?((?<!\d)\d)?[ ./()-]{{1,4}})+\d?[ .)-]?[(\[]?({yr_uni_pat}|{after_pat})",
                        rf"^(\d{{1,2}}|{yr_uni_pat}|{group_pat})?[ .-]*(\W?{title_pat}((?<!\d)\d|[ .-]1)?[ ./()-]{{1,4}})+((?<=[(])\d[)])?[ .-]?[(\[]?({yr_uni_pat}|{after_pat})",
                        flags=re.I)
                r"""
                else:  # chyba to nie będzie już potrzebne
                    fflog('używana będzie wersja filtru dopasowującego dla pojedyńczego tytułu')
                    dodatkowy_filtr = re.compile(
                        # fr'(^|[/-]|  |\d{{1,2}})\W?(\b|_|\d{{1,2}}|^){title_pat}\d?(?=\b|[ ._]){year_pat}',
                        # rf"(^|[/-]|  |\d{{1,2}})\W?(\b|_|\d{{1,2}}|^){title_pat}([ ._-]{title_pat})?\d?(?=\b|[ ._]){year_pat}",
                        # rf"(^|[/-]|  |\d{{1,2}})\W?([ ._-]?{title_pat})+[ ._-]?\d?{year_pat}?",
                        rf"^(\d{{1,2}}|{yr_uni_pat}|{group_pat})?([ .-]?\W?{title_pat})+[ .(-]*((?<!\d)\d)?[ .)(\]-]*({yr_uni_pat}|{after_pat})",
                        flags=re.I)
                """
                # zapamiętanie na kolejne wywołaniu tej funkcji, która dotyczyć będzie i tak tego samego filmu
                # (tylko inna fraza idzie do wyszukiwarki), a wszystkie tytuły zostały na początku ustalone w self.titles
                self.dodatkowy_filtr = dodatkowy_filtr

            if episode:  # dla seriali

                # do DEBUGOWANIA, jak się nie mieści pattern w logu
                # res_pat = custom_pat = yr_uni_pat = '()'
                # title_pat = '()'

                # definiowałem wcześniej do odróżniania filmów od seriali
                ep_uni_pat = ep_uni_pat[:-1] + r"|\b\d{2,3}\b)"  # dodanie dodatkowego wzorca

                # końcowe wzorce do porównywania z nazwą pliku
                dodatkowy_filtr = re.compile(
                    # rf"(^|[/-]|\d{{1,2}})\W?(\b|[ _]|^){title_pat}\d?(?=\b|_)({res_pat}|{yr_uni_pat}|{custom_pat})*[ ._-]*[([]?{ep_uni_pat}",
                    # rf"(^({group_pat})?|[/-]|\d{{1,2}})[ .]?\W?{title_pat}\d?[ .-]+[([]?([ .-]*({res_pat}|{yr_uni_pat}|{custom_pat}))*[)\]]?[ .-]*[([]?{ep_uni_pat}",
                    # rf"(^({group_pat})?|[/-]|\d{{1,2}})[ .]?(\W?{title_pat}[ .-]?((?<!\d)\d)?[ ./()-]{{1,4}})+\d?[ .)-]?[([]?([ .-]*({res_pat}|{yr_uni_pat}|{custom_pat}))*[)\]]?[ .-]*[([]?{ep_uni_pat}",
                    rf"(^({group_pat})?|[/-]|\d{{1,2}})[ .]?(\W?{title_pat}((?<!\d)\d|[ .-]1)?[ ./()-]{{1,4}})+((?<=[(])\d[)])?[ .-]?[([]?([ .-]*({res_pat}|{yr_uni_pat}|{custom_pat}))*[)\]]?[ .-]*[([]?{ep_uni_pat}",
                    flags=re.I,
                )

                # dodatkowy_filtr2 = re.compile(rf"(^\d{{0,2}}\.?\W?|[([]?{episode_pat}\W*)(\b|_){title_pat}(?=\b|_)([ ._]*[/-]|[ ._]{{2,}})", flags=re.I)
                dodatkowy_filtr2 = re.compile(rf"(^\d{{1,2}}\.?\W?|[([]?{ep_uni_pat2}\W*){title_pat}([ .]*[/-]|[ .]{{2,}})", flags=re.I)
                # zmienna 'dodatkowy_filtr2' jest na przypadek, gdy na początku jest numer odcinka a potem tytuł
                # ale problemem jest ograniczenie wyszukiwania, aby nie było jak z filmem "Titans" bez "go" na końcu

                # zapamiętanie na kolejne wywołaniu tej funkcji, która dotyczyć będzie i tak tego samego serialu
                # (tylko inna fraza idzie do wyszukiwarki), a wszystkie tytuły zostały na początku ustalone w self.titles
                self.dodatkowy_filtr = dodatkowy_filtr
                self.dodatkowy_filtr2 = dodatkowy_filtr2

        # poniższe zawsze musi być (niezależnie czy używany będzie filtr dopasowujący tytuły)
        # jeśli episode się nie zmienia, to może można to zapamiętać
        # jest po to, aby wybrać właściwy odcinek (którego szukamy)
        if episode:
            # wzorzec numerów odcinków
            # if re.search(r"e\d{3}", episode):
            #     episode_pat = re.sub(r"(S\d{2})(E(\d{3}))", r"\1[.-]?\2(?!\\d)", episode, flags=re.I)
            # else:
            #     # episode_pat = re.sub(r"(S\d\d)(E(\d\d))", r"\1[.-]?e0?\3(?!\\d)", episode, flags=re.I)
            #     episode_pat = re.sub(r"(S\d{2})(E(\d{2}))", r"\1[.-]?e(\\d{2,3}-?)?e?0?\3(?!\\d)", episode, flags=re.I)
            # episode_pat = re.sub(r"(S\d{2})(E(\d{2,3}))", r"\1[.,-]?e(\\d{2,3}-?)?e?0?\3(?!\\d)", episode, flags=re.I)
            episode_pat = re.sub(r"S0?(\d{1,2})(E(\d{2,4}))", r"s0?\1[.,-]?e(\\d{2,4}-?)?e?0?\3(?!\\d)", episode, flags=re.I)
            # jak próbowałem zrobić podobny numer dla odcinków, to z powodu dziwnego zapisu zakresu łapał mi e013 dla e3 - także na razie odpuszczam
            # na przypadek gdy nie ma innego sezonu
            # fflog(f'{episode_pat=}')
            episode_pat = re.sub(
                # r"(S01.*?)(E.*)",
                r"(S0\?1.*?)(E.*)",
                # r"(\1\2|(?<![se]\\d{2}[.,-])(?<![se]\\d{2})(?<!e\\d{3}[.,-])(?<!e\\d{3})\2)",
                r"(\1\2|(?<![se]\\d{1}[.,-])(?<![se]\\d{1})(?<![se]\\d{2}[.,-])(?<![se]\\d{2})(?<!e\\d{3}[.,-])(?<!e\\d{3})(?<!e\\d{4}[.,-])(?<!e\\d{4})\2)",
                episode_pat,
                flags=re.I,
            )
            # fflog(f'{episode_pat=}')
            # zauważyłem, że czasami zamiast 0 jest O
            episode_pat = episode_pat.replace(r"\d", r"[\dO]").replace("0", "[0O]")

            # dla łączonych odcinków
            eps = (re.search(r"e(\d{2,4})", episode).group(1))  # string
            epn = int(eps)  # liczba (numer)
            sn = int(re.search(r"s(\d{2})", episode).group(1))
            rang_re = re.compile(r"(?:s([\dO]{2})-?)?e(\d{2,4})-e?(\d{2,4})(?!\w)", flags=re.I)
            def ep_is_in_range(filename):
                rang = rang_re.search(filename)
                if rang:
                    # fflog(f'{filename=}')
                    # fflog(f'{rang=}')
                    if not rang.group(1) and sn==1 or rang.group(1) and int(rang.group(1).replace('O','0'))==sn:
                        # fflog(f'{sn=} {epn=}')
                        return epn in range(int(rang.group(2)), int(rang.group(3)))
                return None

            if re.search(r"[sS]01", episode):
                episode2_pat = fr"(?<!\d[2-9])[ .](cz\.|odc\.|ep\.|episode|odcinek)[ .-]{{,3}}0{{,2}}{epn}\b|[([]0{{,2}}{epn}[)\]](?!\.[a-z]{{2,3}}$)|\- 0{{,2}}{epn} [([-]|\b0?{sn}x0{{,2}}{epn}\b|\b0{{,2}}{epn}\.[a-z]{{2,3}}$|[a-z][ .]0{{,2}}{epn}[ .][a-z]"
            else:
                episode2_pat = "niemozenicznalezc"
            # fflog(f'{episode2_pat=}')

        allow_year_less_than_base = True
        # allow_year_less_than_base = control.settings.getBool("sources.allow_year_less_than_base")

        # with self.lock:  # to jakaś pozostałość po starym kodzie

        # fflog(f'ilość rekordów: {len(rows)}')

        log_rejected = control.settings.getBool("sources.title_validation_filter.log_rejected.tx7")
        # fflog(f'{log_rejected=}')

        # sprawdzenie, czy tytuł serialu zawiera w sobię rok
        year_in_title = re.search(r"\b\d{4}\b", title)
        year_in_title = year_in_title[0] if year_in_title else ""

        # ustalenie bieżącego roku - a co jak ktoś ma złą datę na urządzeniu?
        current_year = int(time.strftime("%Y"))
        fflog(f'{current_year=}', 0)

        def _check_base_or_premiered_year_in_filename(filename):
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

        yr_uni_re = re.compile(yr_uni_pat)
        year_re = re.compile(year_pat) if year else None
        episode_re = re.compile(episode_pat, flags=re.I) if episode else ""
        episode2_re = re.compile(episode2_pat, flags=re.I) if episode else ""
        ep_uni_re = re.compile(ep_uni_pat, flags=re.I)
        ep_uni2_re = re.compile(ep_uni_pat2, flags=re.I)
        for row in rows:
            if row in self.results:  # pozbycie się takich samych pozycji
                continue
            size = client.parseDOM(row, "td")[3]  # rozmiar pliku (informacyjnie)
            filename0 = "".join(client.parseDOM(row, "a") or client.parseDOM(row, "label"))  # nazwa pliku
            # odrzucenie rozszerzeń niebędących plikami video
            if filename0[-3:] not in self.VIDEO_EXTENSIONS:
                # fflog(f"  - niepasujące rozszerzenie {filename0[-3:]!r} w {unescape(unquote(filename0))!r}")
                continue
            # funkcji unquote() oraz unescape() najlepiej używać tylko do koncowego wyświetlenia
            # !nie uzywać do porównań z oryginałem,
            # ponieważ raczej nie da się odtworzyć w 100% stringu pierwotnego
            filename = filename0
            filename = unquote(filename)
            filename = unescape(filename)
            filename = filename.replace("_", " ")  # dla uproszczenia, ale sprawdzić patterny, bo mogłobyć wcześniej założenie, że nie ma spacji tylko _
            filename = re.sub(r"\b[0-9a-f]{8}\b", "", filename, flags=re.I)  # wyrzucenie CRC32 z nazwy pliku
            # fflog(f"{filename=}")
            if (
                # (year and year in filename)
                (not episode and year and year_re.search(filename))
                or (not episode and year and allow_year_less_than_base and str(int(year) - 1) in filename)  # przepuszcza filmy z rokiem o 1 mniejszym od bazowego
                or (not episode and year and allow_filename_without_year and not yr_uni_re.search(filename) and not ep_uni_re.search(filename))  # gdy brak roku w tytule
                or (episode and episode_re.search(filename))
                or (episode and ep_is_in_range(filename))
                or (episode and not ep_uni2_re.search(filename) and episode2_re.search(filename))  # inne warianty zapisu odcinków (m.in. dla niektórych anime)
                or (not year and not episode)
            ):
                # fflog(f'przed filtrem {filename=} {size=}\n')
                # jeśli w nazwie jest rok, to kontrola z datą premiery sezonu 
                if episode and premiered and re.search(r"\b\d{4}\b", filename):
                    if _check_base_or_premiered_year_in_filename(filename) is False:
                        #self.trash2.append(row)  # zapisanie do śmietnika
                        if filename0 not in self.trash:
                            fflog(f"  - odrzucono z powodu niepasującego roku ({year=} {premiered=}) w nazwie {unescape(unquote(filename0))!r} {size}", 0)
                            self.trash.append(filename0)
                        # row += "<trash/>"
                        # self.results.append(row)
                        continue

                # sprawdzenie zgodności nazwy pliku z szukanym tytułem
                # (jeśli taki filtr nie jest wyłączony przez użytkownika w ustawieniach)
                if (
                    not dodatkowy_filtr
                    or dodatkowy_filtr.search(filename)
                    or (dodatkowy_filtr2 and dodatkowy_filtr2.search(filename))
                ):
                    self.results.append(row)  # dodanie do listy zaakceptowanych
                    # fflog(f'  + przepuszczono {unescape(unquote(filename0))!r} {size}')
                    # fflog(f' bo {title=} {dodatkowy_filtr=} {year=} {episode=}\n')
                    if filename0 in self.trash:
                        fflog(f" + Przywrócono {unescape(unquote(filename0))!r} {size}", 0)
                        self.trash.remove(filename0)
                else:
                    # niezgodność tytułów
                    # self.trash2.append(row)
                    if log_rejected:
                        row += "<trash/>"
                        self.results.append(row)

                    # może trochę zaciemniać, jak developersko analizujemy co jest kiedy odrzucane,
                    # ale w logach dla usera ładniej wygląda.
                    if not any(filename0 in r for r in self.results):
                        if filename0 not in self.trash:
                            fflog(f"  - odrzucono  {unescape(unquote(filename0))!r} {size}", 0)
                            self.trash.append(filename0)
                            # fflog(f' bo {title=} {dodatkowy_filtr=} {year=} {episode=}\n')
                    else:
                        # TYLKO do developerskiej analizy działania filtra
                        # fflog(f'*(byłoby odrzucone {filename!r} {size}, choć potem zostałoby przywrócone)\n')
                        pass  # po to, aby bezpiecznie móc zakomentować powyższą linijkę
            else:
                # nie ten rok, albo nie ten odcinek
                # fflog(f' nie dodano, bo {filename=} {size=}\n')
                pass


    def sources(self, rows, hostDict, hostprDict, from_cache=None):
        """Funkcja sprawdza przefiltrowane wstępnie wyniki
        i dodaje je do listy wyświetlanej użytkownikowi
        """
        if not rows:
            fflog('Brak rekordów do przekazania')
            return []

        self.login()

        # fflog(f"sprawdzenie co jest na koncie (i notesie)")
        biblio_cache, biblio_links = self.files_on_user_account(from_cache=from_cache)[0:2]

        filter_duplicates = control.settings.getBool("filter.duplicates")

        ilosc_smieci = 0

        # fflog(f"parsing źródeł ({len(rows)})")
        sources = []
        try:
            for row in rows:
                try:
                    filename = client.parseDOM(row, "label")[0]
                    if "<a " in filename.lower():  # moze byc jeszcze tag a
                        filename = client.parseDOM(filename, "a")[0]

                    link = client.parseDOM(row, "input", ret="value")[0]
                    # fflog(f' ')
                    # fflog(f'analizowanie {link=}')

                    # sprawdzenie, czy wybrana pozycja może jest już na Koncie
                    on_account, on_account_link, case, on_account_expires = self.check_if_file_is_on_user_account(biblio_links, link, filename, biblio_cache)
                    #on_account = False  # test tylko

                    # uniknięcie zdublowań dla dołączonych z biblioteki
                    # if not size or "xt7.pl/pobieramy/" in link:  # to niweluje cały zamysł, bo taki link może być dla pewnych szczególnych pozycji
                    if 'dowalona_z_biblioteki' in row and on_account_link and any(on_account_link == s["on_account_link"] for s in sources):
                        # fflog(f'uniknięcie zdublowań dla dołączonych z biblioteki {on_account_link=}')
                        continue

                    hosting = client.parseDOM(row, "td")[1]  # hosting
                    size = client.parseDOM(row, "td")[3]  # rozmiar
                    quality = source_utils.check_sd_url(filename)

                    info = source_utils.get_lang_by_type(filename)
                    language = info[0]
                    if not info[1]:
                        info1 = ""
                    else:
                        info1 = f" | {info[1]}"
                    info = f"{info1} | {size}"

                    alt_links = []
                    alt_filenames = []  # (aby lepiej wykrywać, że jest na koncie)

                    trash = True if "<trash/>" in row else None

                    reject = False

                    # unikanie zdublowań lub wymiana na lepiej opisane
                    if filter_duplicates:
                        # digit_pat = r"[ ._-]\(\d\)"
                        # digit_pat = r"[ ._-]\(\d\)|(?<=((?![\d_])\w){2})\d(?=[\W_]\d{4})"  # numerki na końcu tytułów
                        digit_pat = r"[ ._-]\(\d\)|(?<=[^\W\d_]{2})\d(?=[\W_]\d{4})"  # to samo co linijka wyżej
                        len_filename1 = unescape(unquote(filename))
                        d_in_filename1 = re.search(digit_pat, len_filename1)
                        len_filename1 = re.sub(digit_pat, "", len_filename1)
                        len_filename1 = len(len_filename1)
                        for i in reversed(range(len(sources))):
                            s = sources[i]
                            if hosting in s["source"] and info == s["info"] and quality == s["quality"]:
                                # porównuje długość nazw zakładając, że im dłuższa,
                                # tym więcej będzie zawierała informacji
                                len_filename2 = unescape(unquote(s["filename"]))
                                d_in_filename2 = re.search(digit_pat, len_filename2)
                                len_filename2 = re.sub(digit_pat, "", len_filename2)
                                len_filename2 = len(len_filename2)
                                if len_filename2 < len_filename1 or on_account and not s["on_account"]:
                                    # fflog(f'1 wymiana {s["url"]=} na {link=}')
                                    alt_links = [s["url"]] + s["alt_links"]
                                    alt_filenames = [s["filename"]] + s["alt_filenames"]
                                    if s["on_account"] and not on_account:
                                        on_account = s["on_account"]
                                        on_account_link = s["on_account_link"]
                                        on_account_expires = s["on_account_expires"]
                                        hosting = s["source"]
                                        case = "~"
                                    del sources[i]
                                elif len_filename2 == len_filename1:
                                    if d_in_filename2 and not d_in_filename1:
                                        # fflog(f'2 wymiana {s["url"]=} na {link=}')
                                        alt_links = [s["url"]] + s["alt_links"]
                                        alt_filenames = [s["filename"]] + s["alt_filenames"]
                                        if s["on_account"] and not on_account:
                                            on_account = s["on_account"]
                                            on_account_link = s["on_account_link"]
                                            on_account_expires = s["on_account_expires"]
                                            hosting = s["source"]
                                            case = "~"
                                        del sources[i]
                                    else:
                                        # fflog(f'3 odrzucenie {link=}')
                                        if link not in s["alt_links"]:
                                            s["alt_links"].append(link)
                                        if filename not in s["alt_filenames"]:
                                            s["alt_filenames"].append(filename)
                                        reject = True
                                else:
                                    # fflog(f'4 odrzucenie {link=}')
                                    if link not in s["alt_links"]:
                                        s["alt_links"].append(link)
                                    if filename not in s["alt_filenames"]:
                                        s["alt_filenames"].append(filename)
                                    reject = True

                                break

                        if reject:
                            # fflog(f'dubel - {filename}{info} ({quality})')
                            continue

                    for s in sources:
                        if link == s["url"]:
                            if not trash and s.get("trash"):
                                s.pop("trash", None)
                                reject = True
                                ilosc_smieci -= 1
                                break
                    if reject:
                        continue

                    if trash:
                        ilosc_smieci += 1

                    hosting += case  # dodanie ewentualnie gwiazdki

                    sources.append(
                        {
                            "source": hosting,
                            "quality": quality,
                            "language": language,
                            "url": link,
                            "info": info,
                            "size": size,
                            "direct": True,
                            "debridonly": False,
                            "filename": filename,
                            "on_account": on_account,
                            "on_account_expires": on_account_expires,
                            "on_account_link": on_account_link,
                            "alt_links": alt_links,
                            "alt_filenames": alt_filenames,
                            "trash": trash,
                        }
                    )
                except Exception:
                    fflog_exc()
                    continue

            dubli = len(rows) - len(sources)
            fflog(f'wykryto dubli: {dubli}') if dubli > 0 else ""

            # zapisanie informacji w cache, aby potem wykorzystać w następnej funkcji,
            # gdyż instancja Klasy zostanie zniszczona (wada Kodi?)
            # src = {i['url']: i for i in sources}  # zrobienie z listy słownika, gdzie kluczem dla każdego źródła będzie jego link
            src = sources  # zostawiam jako listę
            cache.cache_insert("xt7_src", repr(src), control.sourcescacheFile)
            # w bazie cache będzie key(xt7_src), value(słownik w formie stringa)

            fflog(f'Przekazano źródeł: {len(sources)}')
            fflog(f'(W tym śmieci: {ilosc_smieci})') if ilosc_smieci > 0 else ""
            return sources

        except Exception:
            fflog_exc(1)
            return sources


    def resolve(self, url, buy_anyway=False, specific_source_data=None):
        """Funkcja odsyła link do playera"""
        # przechowanie wartości zmiennej
        # fflog(f'{url=} {specific_source_data=}')
        original_url = url
        if not specific_source_data:
            specific_source_data = {}

            # Pobranie informacji z cache, aby odczytać nazwę pliku powiązanego z url-em
            sources_data = cache.cache_get("xt7_src", control.sourcescacheFile)
            if sources_data:
                sources_data = sources_data["value"]
                sources_data = literal_eval(sources_data)
                try:
                    # specific_source_data = sources_data[url]  # gdy sources_data to słownik
                    # specific_source_data = [i for i in sources_data if i['url'] == url][0]  # gdy sources_data to lista
                    specific_source_data = next(i for i in sources_data if i["url"] == url)
                    # fflog(f' {specific_source_data=}')
                except Exception:
                    pass
            #else:
                #specific_source_data = {}
                #fflog("[resolve] UWAGA! - brak danych w BAZIE, które powinna zapisać poprzednia metoda 'sources()'")

        # player_link_after_redirection = control.settings.getBool("player.link_after_redirection")
        player_link_after_redirection = True

        def _check_on_account_link_before_play(on_account_link):
            # test i ewentualna próba naprawy nieaktywnego linku
            link = on_account_link
            if '/pobieramy/' in link:
                response = self.session.get(link, headers=self.headers, verify=False, allow_redirects=False)
                if response.status_code == 200:
                    control.execute('Dialog.Close(notification,true)')
                    if 'dla podanego linka Premium' in response.text:
                        control.dialog.ok('xt7', 'Wykorzystano limit połączeń dla tego źródła.')
                    else:
                        control.dialog.ok('xt7', 'Ważność linku wygasła.')
                        control.window.clearProperty('imdb_id')  # aby odświeżyć listę źródeł
                        control.window.setProperty('clear_SourceCache_for', control.window.getProperty('clear_SourceCache_for') + ',xt7')  # jak ktoś używa cache źródeł
                    # control.execute('Dialog.Close(notification,true)')
                    return None
                if response.status_code == 302:
                    link = response.headers['Location']
                    response = self.session.head(link, headers=self.headers, verify=False, allow_redirects=False)
                    if 'text' in response.headers['Content-Type']:
                        if 'download_token=' in link and '.wrzucaj.pl/' in link:  # tylko dla wrzucaj.pl
                            link = re.sub(r'(?<=//)\w+?\.(wrzucaj\.pl/)', r'\1file/', link)
                            link = re.sub(r'\&?download_token=[^&]*', '', link).rstrip('?')
                            try:
                                link = link.encode('latin1').decode('utf8')  # aby było czytelniej w logach
                            except Exception:
                                pass
                            on_account_link = link
                            response = self.session.head(link, headers=self.headers, verify=False, allow_redirects=False)
                        if response.status_code == 302:
                            link = response.headers['Location']
                            response = self.session.head(link, headers=self.headers, verify=False, allow_redirects=False)
                if response.status_code == 403:
                    control.execute('Dialog.Close(notification,true)')
                    control.dialog.ok('Dostęp został ograniczony', ' [CR] - sprawdź przyczynę na stronie internetowej')
                    return None  # choć VLC może odtworzyć, bo błąd 403 może w nim nie wystąpić
                    """
                    user_accepts = control.dialog.yesno(
                        'Dostęp został ograniczony', (
                            ' - sprawdź przyczynę na stronie internetowej.'
                            '\nCzy mimo to, chcesz spróbować kontynuować?'
                            '\n(może zadziałać w przypadku używania zewnętrznego odtwarzacza, np. VLC)'
                            ),
                    )
                    if not user_accepts:
                        return False
                    """
                elif response.status_code >= 400:
                    control.infoDialog(f'Serwer zwrócił błąd nr {response.status_code}', 'xt7', 'ERROR', 4000)
                    control.sleep(4000)
                    return None  # choć np. VLC może czasami odtworzyć, bo błąd 403 może w nim nie wystąpić
                fflog(f"1 {response.status_code=}", 0)
            if player_link_after_redirection:
                on_account_link = link  # czy to nie będzie powodowało problemów z rozpoznawianiem przez Kodi linku do kontynuacji?
                pass
            fflog(f"(rozwiązany?) {on_account_link=}", 0)
            # return on_account_link
            # return str(on_account_link + "|User-Agent=VLC&verifypeer=false")  # VLC nie odtwarza tego
            return on_account_link + f"|User-Agent={quote(self.headers.get('User-Agent', ''))}&verifypeer=false"

        # sprawdzenie, czy wybrane źródło jest już może na koncie użytkownika
        if not buy_anyway and specific_source_data:
            on_account = specific_source_data.get("on_account", False)
            if on_account:
                on_account_link = specific_source_data.get("on_account_link", "")
                if on_account_link:
                    on_account_link = on_account_link.replace("%2F", "-")  # fix dla plików z "/" w nazwie
                    return _check_on_account_link_before_play(on_account_link)

        self.login()

        # pobranie informacji o plikach na koncie ("notes_list" może być dalej potrzebny)
        biblio_cache, biblio_links, notes_list = self.files_on_user_account(mode=2, from_cache=False)

        # odczytanie nazwy pliku związanego z wybranym url-em
        filename = specific_source_data.get("filename", "")
        # fflog(f'{filename=}')

        if not buy_anyway:
            # Sprawdzenie czy wybrana pozycja jest już na koncie
            links = [original_url] + specific_source_data.get("alt_links", [])
            links = list(dict.fromkeys(links))  # ewentualne pozbycie się duplikatów
            filenames = ([filename] if filename else []) + specific_source_data.get("alt_filenames", [])
            filenames = list(dict.fromkeys(filenames))  # ewentualne pozbycie się duplikatów
            on_account, on_account_link, case = self.check_if_file_is_on_user_account(biblio_links, links, filenames, biblio_cache)[0:3]
            # jeśli tak, to zwróć link do niej
            if on_account:
                # fflog(f'{case=} {on_account=} {on_account_link=}')
                on_account_link = on_account_link.replace("%2F", "-")  # fix dla plików z "/" w nazwie
                return _check_on_account_link_before_play(on_account_link)

        auto_purchase = control.settings.getBool("autoxt7")
        if not auto_purchase:
            limit_info = self.session.get(self.base_link, headers=self.headers).text
            limit_info = client.parseDOM(limit_info, "div", attrs={"class": "textPremium"})
            remaining_limit = str(client.parseDOM(limit_info, "b")[-1])
            remaining_limit = re.sub(r"\s*\w+\s*=\s*([\"']?).*?\1(?=[\s>]|$)\s*", "", remaining_limit)
            remaining_limit = re.sub("<[^>]+>", "", remaining_limit)

            # przygotowanie nazwy pliku do wyświetlenia w okienku pytającym
            # if control.settings.getBool("sources.extrainfo"):
            if True:
                if not filename:
                    filename = url
                filename = unquote(filename)
                filename = unescape(filename)
                filename = self.prepare_filename_to_display(filename)

                try:
                    cp = source_utils.getPremColor()
                except Exception:
                    try:
                        cp = control.settings.getString("xt7.color.identify2")
                        # cp = cp if cp else control.settings.getString("prem.color.identify2")
                    except Exception:
                        cp = None
                if cp and cp != "nocolor":
                    filename = f"[COLOR {cp}]{filename}[/COLOR]"
                filename = f"[LIGHT]{filename}[/LIGHT]"
            else:
                filename = ""
                pass

            if "size" in specific_source_data:
                size_info = specific_source_data["size"]
            else:
                size_info = self.extract_size_from_source_info(specific_source_data.get("info", ""))

            size_info = size_info.replace(" ", "\u00A0")
            hosting = specific_source_data.get("source", "")

            if control.condVisibility('Window.IsActive(notification)'):
                control.execute('Dialog.Close(notification,true)')

            user_accepts = control.dialog.yesno(
                "Wymagane potwierdzenie",
                (
                    f"Czy chcesz odtworzyć tę pozycję" + (f", za [B]{size_info}[/B]" if size_info else "") + "?"
                    f"\n[I]{filename}[/I]"
                    f"\n[LIGHT](serwer: [I]{hosting}[/I] )[/LIGHT]"
                    f"\nAktualnie posiadasz: [B]{remaining_limit}[/B]"
                ),
            )
            if not user_accepts:  # rezygnacja
                return False

        # Ustalenie linku do filmu dla odtwarzacza

        links = [original_url] + specific_source_data.get("alt_links", [])
        # fflog(f'{links=}')
        links = list(dict.fromkeys(links))  # ewentualne pozbycie się duplikatów

        for link in links:
            # krok 1 - przesłanie adresu do sprawdzenia, czy aktywny
            data_step1 = {"step": "1", "content": link}
            response = self.session.post("https://xt7.pl/mojekonto/sciagaj", data=data_step1, headers=self.headers).text

            # srawdzenie, czy aktywny
            if ' value="Wgraj linki"' not in response:
                # control.window.clearProperty('imdb_id')  # aby odświeżyć listę źródeł
                fflog(f'nieaktywny {link=}')
                time.sleep(0.1)
                continue
            else:
                break

        if "ymagane dodatkowe" in response:
            control.dialog.ok('Brak środków', f'Brak wystarczającego transferu. \n[COLOR gray](aktualnie posiadasz [B]{remaining_limit}[/B])[/COLOR]')
            fflog(f'Brak wymaganego transferu')
            return None

        if ' value="Wgraj linki"' not in response:
            mnoga = len(links) > 1
            control.infoDialog((f"Wystąpił błąd. \nTa pozycja ma nieaktywn{'e' if mnoga else 'y'} link{'i' if mnoga else ''}."), 'xt7', 'ERROR')
            fflog(f'żaden link dla tej pozycji nie działa')
            return None

        if buy_anyway:
            if '/wrzucaj.pl/' in link:
                if not '/file/' in link:
                    link = link.replace('/wrzucaj.pl/' , '/wrzucaj.pl/file/')
                    if "/" in filename:
                        l = list(link.partition('/file/'))
                        l[-1] = list(l[-1].partition('/'))
                        l[-1][-1] = l[-1][-1].replace('/', '%2F')
                        l[-1] = ''.join(l[-1])
                        link = ''.join(l)
                link = link.replace("%2F", "-")  # fix dla plików z "/" w nazwie
                if player_link_after_redirection:
                    response = self.session.head(link, headers=self.headers, verify=False, allow_redirects=False)
                    if response.status_code == 302:
                        link = response.headers['Location']
                # return link
                return link + f"|User-Agent={quote(self.headers.get('User-Agent', ''))}&verifypeer=false"

        active_url = link
        fflog(f'   aktywny {link=}')
        # if not buy_anyway:  # nie wiem, czy tak lepiej ?
            # control.window.clearProperty('imdb_id')  # aby odświeżyć listę źródeł - nie trzeba tego tu
        control.window.setProperty('clear_SourceCache_for', control.window.getProperty('clear_SourceCache_for') + ',xt7')  # jak ktoś używa cache źródeł

        # do testów
        # return (False if not control.dialog.yesno("xt7", (f"Aktywny link to \n[LIGHT][B][I]{self.prepare_filename_to_display(active_url)}[/I][/B][/LIGHT]\nCzy kontynuować?") ) else True)

        # krok 2 - próba dodania źródła do biblioteki
        data_step2 = {"0": "on", "step": "2"}
        response = self.session.post("https://xt7.pl/mojekonto/sciagaj", data=data_step2, headers=self.headers).text

        # wydzielenie konkretnego fragmentu z odpowiedzi serwera
        div = client.parseDOM(response, "div", attrs={"class": "download"})
        try:
            link = client.parseDOM(div, "a", ret="href")[1]
            size = div[1].split("|")[-1].strip()
        except Exception:
            if "Nieaktywne linki" in response:
                control.dialog.notification("xt7", "Link okazał się nieaktywny")
                fflog(f'jednak zły {link=}')
            else:
                control.infoDialog("Wystąpił jakiś błąd. \nMoże brak wymaganego transferu?", "xt7", "ERROR")
            # control.dialog.ok('Brak środków', f'Brak wystarczającego transferu. \n[COLOR gray](aktualnie posiadasz [B]{remaining_limit}[/B])[/COLOR]')
            fflog_exc()
            return None

        # ewnentualne zapisanie informacji, aby następnym razem wiedzieć z jakim linkiem powiązać plik na koncie
        if control.settings.getBool("xt7.use_web_notebook_for_history") and specific_source_data:
            # nazwa pliku
            filename = unescape(unquote(specific_source_data["filename"]))
            # link
            link1 = link.rpartition("/")[0] if "/pobieramy/" in link else link
            # data ważności
            short_day = re.compile(r"([a-z]{2,3})[a-z]*|0(\d)(?=:)", flags=re.I)
            from datetime import datetime, timedelta
            after = timedelta(1)  # 1 dzień
            if "wplik" in specific_source_data["source"].lower():
                after = timedelta(hours=8)  # z przeprowadzonego doświadczenia
            expires = str((datetime.now() + after).strftime("%A %H:%M"))
            short_date = short_day.sub(r"\1\2", expires)

            # notes_dict = {k: [v['on_account_link'], v['filename'], v['size'], v['on_account_expires']] for k,v in biblio_cache.items()}
            # notes_dict = {k: v for k, v in sorted(notes_dict.items(), key=lambda item: item[1][-1], reverse=True)}  # sortowanie wg ostatniego, czyli daty wygaśnięcia
            # notes_list = [{k: v} for k, v in notes_dict.items()]
            # notes_list = [{original_url: [link1, filename, size, short_date]}] + notes_list  # najnowszy na początek
            notes_list = [{active_url: [link1, filename, size, short_date]}] + notes_list  # najnowszy na początek

            # zapisanie w Notesie na koncie
            while len(repr(notes_list)) >= 5000:  # limit narzucony przez serwis xt7.pl
                del notes_list[-1]
            now0 = int(time.time())
            self.session.post(
                self.base_link + self.mynotepad_link,
                data={"content": repr(notes_list)},
                headers=self.headers,
            )
            now1 = int(time.time())
            if (now1 - now0) > 5:
                fflog(f'!wysłanie historii plików do "xt7.pl/mojekonto/notes" zajęło {(now1 - now0)} sek.')

        # zwrócenie linku do odtwarzacza
        # fflog(f"link: {link!r}")
        link = link.replace("%2F", "-")  # fix dla plików z "/" w nazwie
        if player_link_after_redirection:
            return _check_on_account_link_before_play(link)
        else:
            # return str(link)
            # return str(link + "|User-Agent=vlc/3.0.0-git libvlc/3.0.0-git&verifypeer=false")  # VLC nie odtwarza tego
            return link + f"|User-Agent={quote(self.headers.get('User-Agent', ''))}&verifypeer=false"


    def prepare_filename_to_display(self, filename):
        # Pozwoli zawijać tekst (aby mieścił się w okienku)
        filename = filename[:-4].replace(".", " ").replace("_", " ") + filename[-4:]
        # Wywalenie ostatniego myślnika - zazwyczaj jest po nim nazwa "autora" pliku (uwzględniłem kod od TWOJPLIK)
        filename = re.sub(r"-(?=\w+( \(\d\))?( [0-9A-F]{3})?\.\w{2,4}$)", " ", filename, flags=re.I)
        # przywrócenie niezbędnych kropek i kresek dla niektórych fraz
        filename = self.replace_audio_format_in_filename(filename)
        return filename


    def replace_audio_format_in_filename(self, filename):
        replacements = [
            (r"(?<!\d)([57261]) ([10])\b", r"\1.\2"),  # ilość kanałów, np. 5.1 czy 2.0
            (r"\b([hx]) (26[45])\b", r"\1.\2", re.I),  # h264 x264 x265 h265
            (r"\b(DDP?) (EX)\b", r"\1-\2", re.I),  # np. DD-EX
            (r"\b(DTS) (HD(?!-?(?:TS|cam|TV))|ES|EX|X(?![ .]26))\b", r"\1-\2", re.I),  # DTS
            (r"\b(AAC) (LC)\b", r"\1-\2", re.I),  # AAC-LC
            (r"\b(AC) (3)\b", r"\1-\2", re.I),  # AC-3
            (r"\b(HE) (AAC)\b", r"\1-\2", re.I),  # HE-AAC
            (r"\b(WEB|Blu|DVD|DCP|B[DR]|HD) (DL|Ray|RIP|Rip|Rip|TS)\b", r"\1-\2", re.I),
        ]
        for pattern in replacements:
            if len(pattern) == 3:
                old, new, flags = pattern
                filename = re.sub(old, new, filename, flags=flags)
            else:
                old, new = pattern
                filename = re.sub(old, new, filename)
        return filename


    def extract_size_from_source_info(self, source_info):
        size_match = re.search(
            r"(?:^|\|)\s*(\d+(?:[.,]\d+)?)\s*([GMK]B)\b\s*(?:\||$)",
            source_info,
            flags=re.I,
        )
        size = f"{size_match[1]} {size_match[2]}" if size_match else ""
        return size


    def files_on_user_account(self, mode=1, from_cache=None):
        """funkcja pobiera informacja z zakładki Notes oraz Historia,
        zwraca linki z Historii,
        dane z Notesu przerabia na tablicę,
        tworzy słownik o nazwie biblio_cache
        """
        notes_list = []
        # Pobranie informacji o plikach na koncie zapisanych w notesie
        if control.settings.getBool("xt7.use_web_notebook_for_history"):  # a może zawsze sprawdzać?
            result = cache.cache_get(f"xt7.pl_{self.mynotepad_link}", control.sourcescacheFile)
            if result:
                if (
                    from_cache
                    or from_cache is not False
                    and ((int(time.time()) - int(result["date"])) < (5 * 60))
                ):
                    result = result["value"]
                    # fflog(f"wzięto z cache (notes)")
                else:
                    result = ""
            # fflog(f"{result=}")
            notes_page_content = result
            if not result:
                # fflog(f"sprawdzam adres {self.base_link+self.mynotepad_link}")
                now0 = int(time.time())
                notes_page_content = self.session.get(self.base_link + self.mynotepad_link, headers=self.headers).text
                now1 = int(time.time())
                if (now1 - now0) > 5:
                    fflog(f"!sprawdzanie {self.base_link+self.mynotepad_link} zajęło {(now1 - now0)} sek.")
                cache.cache_insert(f"xt7.pl_{self.mynotepad_link}", notes_page_content, control.sourcescacheFile)
            notes_value = client.parseDOM(notes_page_content, "textarea", attrs={"class": "notepad"})[0]

            if (notes_value
                and notes_value[0] == "["
                and notes_value[-1] == "]"
            ):
                try:
                    notes_list = literal_eval(notes_value)
                except Exception:
                    # notes_list = []
                    fflog("Uszkodzona struktura w Notesie !")
                    # fflog_exc()
            else:
                if notes_value:
                    fflog("Uszkodzona struktura Notesu")
                # notes_list = []

        # rozpisanie danych pobranych z notesu
        biblio_cache = {}
        for file_item in notes_list[::-1]:
            for url in file_item:
                if url in biblio_cache:
                    if mode == 2:
                        # fflog(f"!Istnieje więcej pozycji na koncie skojarzonych z adresem {url!r} (plik: {biblio_cache[url]['filename']!r} ({biblio_cache[url]['size']!s}) - zostanie wybrana najnowsza")
                        pass
                    # continue  # ale nie może być reverse na notes_list
                else:
                    biblio_cache[url] = {}  # ważne
                try:
                    biblio_cache[url]["filename"] = file_item[url][1]
                    biblio_cache[url]["size"] = file_item[url][2]
                    biblio_cache[url]["url"] = url
                    biblio_cache[url]["on_account_link"] = file_item[url][0]
                    biblio_cache[url]["on_account_expires"] = file_item[url][3]
                    biblio_cache[url]["source"] = re.sub(r"https?://(?:www\.)?([^.]+)\..+", r"\1", url, flags=re.I).upper()
                except Exception:
                    biblio_cache[url] = {}
                    fflog(f"nie udało się pobrać wszystkich danych z notesu dla {url!r}")
                    fflog_exc()

        # pobranie zawartości strony internetowej "historia zakupionych linków"
        result = cache.cache_get(f"xt7.pl_{self.mylibrary_link}", control.sourcescacheFile)
        if result:
            if (
                from_cache
                or from_cache is not False
                and ((int(time.time()) - int(result["date"])) < (5 * 60))
            ):
                result = result["value"]
                # fflog(f"wzięto z cache (pliki)")
            else:
                result = ""
        if not result:
            # fflog(f"sprawdzam adres {self.base_link+self.mylibrary_link}")
            now0 = int(time.time())
            result = self.session.get(self.base_link + self.mylibrary_link, headers=self.headers).text
            now1 = int(time.time())
            if (now1 - now0) > 5:
                fflog(f"!sprawdzanie {self.base_link+self.mylibrary_link} zajęło {(now1 - now0)} sek.")
            cache.cache_insert(f"xt7.pl_{self.mylibrary_link}", result, control.sourcescacheFile)
        # sprawdzenie, czy w odpowiedzi jest tabela
        table = client.parseDOM(result, "table", attrs={"class": "list"})
        try:
            biblio_links = client.parseDOM(table, "input", ret="value")
            if biblio_links:
                rows = client.parseDOM(table, "tr")[1:]
                biblio_links_exp = []
                for row in rows:
                    exp = client.parseDOM(row, "td")[3]
                    biblio_links_exp.append(exp)
                biblio_links2 = list(zip(biblio_links, biblio_links_exp))
            else:
                biblio_links2 = []
        except Exception:
            biblio_links = []
            # biblio_links_exp = []
            biblio_links2 = []
            fflog_exc()

        if control.settings.getBool("xt7.use_web_notebook_for_history"):
            # skrócenie linków
            # biblio_links1 = [x.rpartition("/")[0] for x in biblio_links if "/pobieramy/" in x]
            biblio_links1 = [(x.rpartition("/")[0] if "/pobieramy/" in x else x) for x in biblio_links]
            # "synchronizacja" z bilbioteką na stronie
            biblio_cache = {
                k: v
                for k, v in biblio_cache.items()
                # if any(l in v.values() for l in biblio_links1)  # szuka w tablicy
                if any(l in s for s in v.values() for l in biblio_links1)  # szuka w stringu
            }
            # odświeżenie Notesu
            notes_list = [
                n
                for n in notes_list
                for v in n.values()
                # if any(l in v for l in biblio_links1)
                if any(l in s for s in v for l in biblio_links1)  # szuka w stringu
            ]
            # wywalenie linków, które są w Notesie, aby nie wykrywać prawdopodobieństw, gdy może być pewność
            # biblio_links = [l for l in biblio_links if l.rpartition("/")[0] not in [i[0] for i in [v for n in notes_list for v in n.values()]]]
            # biblio_links2 = [l for l in biblio_links2 if l[0].rpartition("/")[0] not in [i[0] for i in [v for n in notes_list for v in n.values()]]]
            biblio_links2 = [l for l in biblio_links2 for s in [i[0] for i in [v for n in notes_list for v in n.values()]] if l[0].rpartition("/")[0] not in s] if notes_list else biblio_links2

        # fflog(f'\n{biblio_cache=} \n{biblio_links2=} \n{notes_list=}')
        return biblio_cache, biblio_links2, notes_list


    def check_if_file_is_on_user_account(self, biblio_links, links, filenames, biblio_cache=None):
        case = ""
        on_account = False
        on_account_expires = ""
        on_account_link = ""

        filename = filenames  # nie wiem czemu tu taki zapis (chyba tylko dla loga na końcu)
        ext_pat = f'({"|".join(self.VIDEO_EXTENSIONS)})'.replace(".", "")
        if isinstance(links, str):
            links = [links]
        # fflog(f'{len(links)=} {len(filenames)=} {filenames=}')
        for link in links:
            #fflog(f'{link=}')
            if biblio_cache:
                # na podstawie danych z notesu
                specific_biblio_cache = biblio_cache[link] if link in biblio_cache else None
                if not specific_biblio_cache:
                    if link.rpartition("/")[0] in biblio_cache:  # dla skracanych linków
                        specific_biblio_cache = biblio_cache[link.rpartition("/")[0]]
                if specific_biblio_cache:
                    on_account = True
                    on_account_link = specific_biblio_cache.get("on_account_link")
                    on_account_expires = specific_biblio_cache["on_account_expires"]
                    break

            if not on_account:
                # sprawdzenie starszą metodą
                # potrzebne, jak nie ma danych z cache lub są niekompletne (brak całej historii)
                # lub mimo wybrania opcj Notesu user "kupił" ze strony
                for item in biblio_links:  # element z "Historii linków"
                    item_org = item
                    item = item[0]
                    item = unescape(unquote(item.rstrip("/").split("/")[-1]))
                    item = item.replace('_', ' ')  # uproszczenie
                    # item = "".join(character for character in item if character.isalnum())
                    if "/twojplik.pl/" in link.lower():
                        item = re.sub(rf"\.[0-9A-F]{{3}}(\.{ext_pat})$", r".ZZZ\1", item)

                    url = unescape(unquote(link))  # badany oryginalny link
                    url = url.replace('_', ' ')  # uproszczenie
                    # url = "".join(character for character in url if character.isalnum())
                    if "/twojplik.pl/" in link.lower():
                        url = re.sub(rf"\.[0-9A-F]{{3}}(\.{ext_pat})$", r".ZZZ\1", url)

                    # fflog(f'{item=} {url=}')
                    if item in url:
                        on_account_link = item_org[0]
                        on_account_expires = item_org[1]
                        on_account = True
                        if on_account_link != link:
                            case += "*"  # bo można znaleźć nazwę z biblioteki w innym linku niż pierwotny, więc serwer też może być inny
                        break

            if on_account:
                break

        if not on_account:  # teraz test z nazwami plików

            if not on_account and filenames:  # porównanie z nazwą pliku widniejącą na liście
                for item in biblio_links:  # element z "Historii linków"
                    item_org = item
                    item = item[0]

                    if "/twojplik.pl/" in link.lower():  # serwery nie są mieszane, więc jakikolwiek z listy może być do wykrycia tegoż serwera
                        item = re.sub(rf"\.[0-9A-F]{{3}}(\.{ext_pat})$", r".ZZZ\1", item)  # najwyżej się nie wykona

                    filenames = [filenames] if isinstance(filenames, str) else filenames
                    for filename in filenames:
                        if not filename:
                            continue

                        if "/twojplik.pl/" in link.lower():
                            filename = re.sub(rf"\.[0-9A-F]{{3}}(\.{ext_pat})$", r".ZZZ\1", filename)  # ten sam pattern co wyżej

                        if unescape(unquote(filename)) in unescape(unquote(item)):
                            # dodatkowy warunek mogący pomóc, bo nie zawsze da się stwierdzić po url-u,
                            # gdyż np. linki do serwera "wplik" są zakodowane
                            # choć drobne ryzyko pomyłki istnieje, bo nie jest sprawdzany rozmiar czy serwer
                            # (strona xt7 nie podaje w tej zakładce ani serwera ani rozmiaru)
                            on_account_link = item_org[0]
                            on_account_expires = item_org[1]
                            on_account = True
                            case += "**"  # to co wyżej, tylko inny sposób porównywania
                            break
                    if on_account:
                        break

            if not on_account and filenames:
                for item in biblio_links:  # element z "Historii linków"
                    item_org = item
                    item = item[0]
                    if item[-3:] not in self.VIDEO_EXTENSIONS:  # gdy przez xt7 ucięty, jak dla "Flip i Flap Utopia"
                        # if "/twojplik.pl/" in link.lower():  # nie ma sensu, bo ucięty przecież jest
                            # item = re.sub(rf"\.[0-9A-F]{{3}}(\.{ext_pat})$", r"\1", item)
                        for filename in filenames:
                            if not filename:
                                continue
                            # if "/twojplik.pl/" in link.lower():  # też raczej nie ma sensu
                                # filename = re.sub(rf"\.[0-9A-F]{{3}}(\.{ext_pat})$", r"\1", filename)
                            if unquote(item.rpartition("/")[-1]) in filename:
                                on_account_link = item_org[0]
                                on_account_expires = item_org[1]
                                on_account = True
                                case += "***"  # ze względu na to, że to nie musi być ten serwer i ten link
                                break
                        if on_account:
                            break

        if on_account_expires:
            if case:
                try:
                    from datetime import datetime
                    on_account_expires = datetime.strptime(on_account_expires, "%H:%M %d.%m.%Y").strftime("%A %H:%M")
                except Exception:
                    pass
            on_account_expires = source_utils.months_to_miesiace(on_account_expires, short=1)
            on_account_expires = re.sub(r"0(\d)(?=:\d\d)", r"\1", on_account_expires)

        # fflog(f'koniec {on_account=} {on_account_link=} {case=} {link=} {filename=}')
        return on_account, on_account_link, case, on_account_expires


    def login(self):
        fflog('sprawdzenie czy zalogowany', 0)
        try:
            cookies = cache.cache_get("xt7_cookie", control.sourcescacheFile)["value"]
        except Exception:
            cookies = ""
        self.headers.update({"Cookie": cookies})

        result = cache.cache_get("xt7.pl_glowna", control.sourcescacheFile)
        if result:
            if (int(time.time()) - int(result["date"])) < (5 * 60):
                result = result["value"]
                fflog(f"zawartość strony wzięto z cache (główna)", 0)
            else:
                result = ""
        if not result:
            fflog(f"sprawdzam zalogowanie na stronie głównej", 0)
            now0 = int(time.time())
            result = self.session.get(self.base_link, headers=self.headers).text
            now1 = int(time.time())
            if (now1 - now0) > 5:
                fflog(f"!sprawdzanie, czy użytkownik jest zalogowany zajęło {(now1 - now0)} sek.")
            cache.cache_insert("xt7.pl_glowna", result, control.sourcescacheFile)
        if self.user_name in result:
            fflog('użytkownik jest już zalogowany', 0)
            return
        else:
            if self.user_name and self.user_pass:
                fflog("potrzeba zalogowania na konto", 0)
                self.session.post(
                    self.base_link + self.login_link,
                    verify=False,
                    allow_redirects=False,
                    data={"login": self.user_name, "password": self.user_pass},
                )
                result = self.session.get(self.base_link).text
                if self.user_name in result:
                    fflog('zalogowano poprawnie', 0)
                    cookies = self.session.cookies
                    cookies = "; ".join([str(x) + "=" + str(y) for x, y in cookies.items()])
                    cache.cache_insert("xt7_cookie", cookies, control.sourcescacheFile)
                    self.headers.update({"Cookie": cookies})
                    cache.cache_insert("xt7.pl_glowna", result, control.sourcescacheFile)
                else:
                    fflog("logowanie nieudane!")
                    control.infoDialog('logowanie nieudane', 'xt7', 'ERROR')
            else:
                fflog("BRAK danych do zalogowania! - sprawdź ustawienia")
                control.infoDialog('BRAK danych do zalogowania! - sprawdź ustawienia', 'xt7', 'ERROR')

import re
import traceback
from typing import NamedTuple
from ast import literal_eval

from ptw.libraries import apis
from ptw.libraries import control
from ptw.libraries import cache
from ptw.libraries import log_utils
from ptw.libraries.log_utils import log, fflog
from ptw.debug import log_exception, fflog_exc


class MediaLanguageDetails(NamedTuple):  # nie wiem, po co taki zabieg z klasą
    english_translated_result: dict  # chyba tylko to jest wykorzystywane
    # poniższe chyba nie są nigdzie wykorzystywane (jako właściwości tej klasy)
    """
    original_title: str
    title: str
    original_name: str
    # english_name: str
    """

class Crew(NamedTuple):
    writer: str
    director: str


class MediaItem:
    def __init__(self):
        self._item = {}

    def __setattr__(self, key, value):
        if key.startswith('_'):
            super().__setattr__(key, value)  # lub object.__setattr__(self, key, value)
        else:
            self._item[key] = value

    def __getattr__(self, key):
        return self._item.get(key, "")

    @property
    def item(self):
        return self._item

    @item.deleter
    def item(self):
        print("Delete item")
        del self._item



class SuperInfo:
    def __init__(self, media_list, session, lang="en", content_type='movie'):
        self.meta = []
        self.media_item = MediaItem()
        self.lang = lang  # musi być małymi literami
        # self.language = f"{self.lang}-{self.lang.upper()}"  # ale w odpowiedzi z serwera jest tylko np. "PL", czyli do zapytania "pl-PL", ale w odpowiedzi szukać tylko "PL"
        # self.region = self.lang.upper()
        # te dwa powyższe nie mają zastosowania (chyba) w tutejszych zapytaniach do serwera
        self.my_language_order = []
        self.content_type = content_type
        self.media_list = media_list
        self.session = session
        self.tm_user = control.setting("tm.user") or apis.tmdb_API
        # do czego poniższe w ogóle służy ?
        self.user = str(control.setting("fanart.tv.user")) + str(control.setting("tm.user"))  # po co tu user od fanart ?

        self.quality = control.setting("image.quality")
        if self.quality == "0":
            self.qualityp = "w500"
            self.qualityf = "w780"
        elif self.quality == "1":
            self.qualityp = "w780"
            self.qualityf = "w1280"
        elif self.quality == "2":
            self.qualityp = "w780"
            self.qualityf = "original"

        self.fanartby = control.setting("image.fanartby")
        if self.fanartby == "0":
            self.fanartby = "vote_average"
        elif self.fanartby == "1":
            self.fanartby = "vote_count"
        self.posterby = control.setting("image.posterby")
        if self.posterby == "0":
            self.posterby = "vote_average"
        elif self.posterby == "1":
            self.posterby = "vote_count"

        self.tmdb_by_imdb = f"https://api.themoviedb.org/3/find/%s?api_key={self.tm_user}&external_source=imdb_id"
        self.tmdb_api_link_movies  = f"https://api.themoviedb.org/3/movie/%s?api_key={self.tm_user}&language={self.lang}&append_to_response=credits,external_ids,release_dates,videos"
        self.tmdb_api_link_tvshows = f"https://api.themoviedb.org/3/tv/%s?api_key={self.tm_user}&language={self.lang}&append_to_response=credits,external_ids,content_ratings,videos"
        self.tm_img_link = "https://image.tmdb.org/t/p/w%s%s"
        self.tmdb_arts_movies  = f"https://api.themoviedb.org/3/movie/%s/images?api_key={self.tm_user}"
        self.tmdb_arts_tvshows = f"https://api.themoviedb.org/3/tv/%s/images?api_key={self.tm_user}"
        self.tmdb_providers_movies  = f"https://api.themoviedb.org/3/movie/%s/watch/providers?api_key={self.tm_user}"
        self.tmdb_providers_tvshows = f"https://api.themoviedb.org/3/tv/%s/watch/providers?api_key={self.tm_user}"

        # grafiki z FanartTV
        self.fanartTV_artwork = control.setting("fanartTV_artwork")
        self.fanart_tv_user = control.setting("fanart.tv.user") or apis.fanarttv_client_key
        self.fanart_tv_API_key = control.setting("fanart.tv.dev") or apis.fanarttv_API_key
        self.fanart_tv_headers = {"api-key": self.fanart_tv_API_key, "client-key": self.fanart_tv_user, }
        # self.fanart_tv_headers = {"api-key": "b018086af0e1478479adfc55634db97d", "client-key": self.fanart_tv_user}
        if content_type == "movie":
            self.fanart_tv_art_link   = "http://webservice.fanart.tv/v3/movies/%s"
            self.fanart_tv_level_link = "https://webservice.fanart.tv/v3/level"  # ?
        else:
            self.fanart_tv_art_link   = "http://webservice.fanart.tv/v3/tv/%s"


    def get_info(self, i, get_from_cache=True, include_next_page=True):
        # fflog(f'{i=}')
        try:
            imdb = self.media_list[i].get("imdb", "") if self.media_list[i].get("imdb", "") != "0" else ""
            self.media_item.imdb = imdb

            tmdb = self.media_list[i].get("tmdb", "") if self.media_list[i].get("tmdb", "") != "0" else ""
            self.media_item.tmdb = tmdb

            tvdb = self.media_list[i].get("tvdb", "") if self.media_list[i].get("tvdb", "") != "0" else ""
            self.media_item.tvdb = tvdb

            list_title = self.media_list[i].get("title")
            list_title = self.media_list[i].get("name") if not list_title else list_title  # nie wiem, czy potrzebne
            # fflog(f'{list_title=}  {i=}')


            tmdb_media_item_response = None
            # fflog(f'{get_from_cache=}')
            if get_from_cache:
                # fflog(f'szukam w bazie klucza {"superinfo" + f"_{tmdb or imdb}"}')
                cache_result = cache.cache_get("superinfo" + f"_{tmdb or imdb}")
                # fflog(f'{cache_result=}')
                if cache_result:
                    if cache._is_cache_valid(cache_result['date'], float(get_from_cache)):  # 1 godz. dla True
                        try:
                            tmdb_media_item_response = literal_eval(cache_result['value'])
                        except Exception:
                            fflog_exc(0)
                            pass
                    else:
                        fflog(f'przeterminowany cache  dla  {list_title=}  t(i)mdb={tmdb or imdb}')
                cache_result = None
            # fflog(f'{tmdb_media_item_response=}')


            if not tmdb_media_item_response:
                # fflog(f'z internetu  dla {list_title=}')

                media_id = self.get_media_id(tmdb, imdb)  # ustalenie id: tmdb lub imdb

                tmdb_media_item_response = self.get_tmdb_api_item(media_id)  # pobranie danych pozycji z serwera
                #log_utils.log(f'{tmdb_media_item_response=}', 1)

                # fflog(f'{tmdb_media_item_response.get("success")=}')
                if tmdb_media_item_response.get("success") is False:
                    fflog(f'Niepowodzenie  {tmdb_media_item_response=}  {list_title=}', 1)
                    # return
                    pass
                
                if not list_title:
                    list_title = tmdb_media_item_response.get("title")
                if not list_title:
                    list_title = tmdb_media_item_response.get("name")
                if not list_title:
                    fflog(f'brak tytułu dla  {media_id=}')
                    # fflog(f'{tmdb_media_item_response=}', 1)
                    # return
                    pass
                else:
                    # fflog(f'{list_title=}  {media_id=}')
                    pass

                original_language = tmdb_media_item_response.get("original_language", "")

                # Lista pasujących języków, wraz z `None`, bo czasem w JSON jest: "iso_639_1":null.
                self.my_language_order = [self.lang, "en", original_language, "00", "", None]

                if not imdb:
                    imdb = self.media_item.imdb = tmdb_media_item_response.get("external_ids", {}).get("imdb_id", "")

                if not tvdb:
                    tvdb = tmdb_media_item_response.get("external_ids", {}).get("tvdb_id", "")
                    tvdb = str(tvdb) if tvdb else None
                    self.media_item.tvdb = tvdb

                if not tmdb:
                    tmdb = self.media_item.tmdb

                #media_titles = self.get_media_titles(list_title, tmdb_media_item_response, original_language, list_title)
                media_titles = self.get_media_titles(tmdb_media_item_response, original_language, list_title)
                # fflog(f'{media_titles=}')
                if not media_titles.english_translated_result:
                    # fflog(f'brak angielskiego opisu dla  {list_title=}  {media_id=}')
                    # return
                    pass

                # fflog(f'{self.media_item.title=}')
                if not self.media_item.title:
                    fflog(f'nie udało się ustalić tytułu dla  {list_title=}  {media_id=}')
                    # fflog(f'{tmdb_media_item_response=}', 1)
                    if True and list_title:
                        self.media_item.label = list_title  # opcjonalnie
                        self.media_item.title = list_title
                        self.media_item.originaltitle = list_title  # to pozwala na szukanie źródeł
                        self.media_item.originalname = list_title
                    else:
                        # return  # bo nie wiem, czy coś ma zwrócić jednak, aby ilość elementów z listy się potem gdzieś zgadzała
                        pass

                plot = tmdb_media_item_response.get("overview", self.media_list[i].get("plot", ""))
                tagline = tmdb_media_item_response.get("tagline", "")
                if self.lang != "en":
                    if not plot:
                        plot = media_titles.english_translated_result.get("overview", "")
                    if not tagline:
                        en_tagline = media_titles.english_translated_result.get("tagline", "")
                        if en_tagline:
                            tagline = en_tagline
                self.media_item.plot = plot
                self.media_item.tagline = tagline

                premiered = tmdb_media_item_response.get("release_date", "") or tmdb_media_item_response.get("first_air_date", "")
                if not premiered:
                    premiered = self.media_list[i].get("premiered", "")
                self.media_item.premiered = premiered
                match = re.search(r"(\d{4})", premiered)
                _year = match.group() if match else self.media_list[i].get("year")
                year = tmdb_media_item_response.get("year", _year)
                self.media_item.year = year

                local_premieres = next(
                        #( x["release_dates"][0]["release_date"]  # bo może być kilka
                        ( x["release_dates"]
                          for x in tmdb_media_item_response.get("release_dates", {}).get("results", {})
                          if x.get("iso_3166_1") == "PL" )
                    , "")
                # dla seriali nie ma na razie możliwości uzyskania lokalnej daty premiery
                #log_utils.log(f'{local_premieres=}', 1)
                if local_premieres:
                    #localpremiered = localpremiered.split("T")[0]
                    self.media_item.local_premieres = local_premieres

                if self.content_type == "tvshow" or self.content_type == "tv":
                    episodes = tmdb_media_item_response.get("number_of_episodes") or 0
                    self.media_item.episodes = episodes
                    seasons = tmdb_media_item_response.get("number_of_seasons") or 0
                    self.media_item.seasons = seasons


                if self.content_type == "movie":
                    mpaa = ", ".join( set(cert
                                         for it in tmdb_media_item_response.get("release_dates", {}).get("results", [])
                                          if it.get("iso_3166_1") in ("US", "PL")
                                           for rel in it.get("release_dates", [])
                                            for cert in (rel.get("certification"),) if cert) )
                elif self.content_type == "tvshow" or self.content_type == "tv":
                    mpaa = ", ".join( set(it.get("rating")
                                          for it in tmdb_media_item_response.get("content_ratings", {}).get("results", [])
                                          if it.get("iso_3166_1") in ("US", "PL")
                                          ) )              
                if not mpaa:
                    mpaa = self.media_list[i].get("mpaa", "")
                    # fflog(f'{mpaa=}  {media_id=}',1,1)
                if mpaa:
                    self.media_item.mpaa = mpaa

                status = tmdb_media_item_response.get("status") or ""
                self.media_item.status = status

                studio = tmdb_media_item_response.get("production_companies")
                studio = studio[0].get("name") if studio else ""
                self.media_item.studio = studio

                genre = tmdb_media_item_response.get("genres")
                genre = " / ".join([d["name"] for d in genre]) if genre else self.media_list[i].get("genre", "")
                self.media_item.genre = genre

                country = tmdb_media_item_response.get("production_countries")
                country = " / ".join([c["name"] for c in country]) if country else ""
                self.media_item.country = country

                duration = str( tmdb_media_item_response.get("runtime") or "")
                self.media_item.duration = duration

                # self.media_item.rating = tmdb_media_item_response.get("vote_average", -1.0)
                self.media_item.rating = tmdb_media_item_response.get("vote_average", 0) or self.media_list[i].get("rating", "")
                # self.media_item.votes = tmdb_media_item_response.get("vote_count", -1.0)
                self.media_item.votes = tmdb_media_item_response.get("vote_count", 0) or self.media_list[i].get("votes", "")

                self.get_cast_with_thumbnail(tmdb_media_item_response)

                self.get_writer_and_director(tmdb_media_item_response)

                arts = self.get_arts(tmdb, imdb)
                if arts:
                    self.get_best_poster(i, arts)
                    # self.get_best_keyart(i, arts)  # poster bez napisów
                    self.get_best_keyart(tmdb_media_item_response, arts)  # poster (plakat) bez napisów
                    self.get_best_landscape(tmdb_media_item_response, arts)
                    self.get_best_fanart(tmdb_media_item_response, arts)  # landscape bez napisów, czyli bez określonego języka (kod 00 albo null)
                    self.get_best_clearlogo1(tmdb_media_item_response, arts)  # w1280
                    # self.get_best_clearlogo(i, arts)  # w780

                self.get_other_arts(tmdb, tvdb, list_title, year)  # banner, clearlogo, clearart, discart

                self.seasons_posters = {}
                if self.content_type == "tvshow" or self.content_type == "tv":
                    seasons = tmdb_media_item_response.get("seasons", {})
                    for s in seasons:
                        poster_path = s.get("poster_path", "")
                        if poster_path:
                            poster_path =  f"https://image.tmdb.org/t/p/{self.qualityp}{poster_path}"
                            self.seasons_posters.update({str(s.get("season_number")): poster_path})
                if self.seasons_posters:
                    self.media_item.seasons_posters = self.seasons_posters

                self.get_providers(tmdb, imdb)

                self.get_trailer(tmdb_media_item_response)

                if include_next_page:
                    self.media_item.next = self.media_list[i].get("next")

                tmdb_media_item_response = {k: v for k, v in self.media_item.item.items()}

                # fflog(f'{tmdb_media_item_response=}')
                self.media_list[i].update(tmdb_media_item_response)
                """
                kopia_mir = tmdb_media_item_response.copy()
                # kopia_mir.pop("next", None)
                kopia_mir = tmdb_media_item_response
                cache.cache_insert("superinfo" + f"_{tmdb or imdb}", repr(kopia_mir))
                """
                cache.cache_insert("superinfo" + f"_{tmdb or imdb}", repr(tmdb_media_item_response))

            else:  # jak pobrane z bazy cache
                fflog(f'z cache  dla {list_title=}', 0)

                tmdb_media_item_response["next"] = self.media_list[i].get("next")

                self.media_list[i].update(tmdb_media_item_response)

                # potrzebne do ostatniej linijki (wstawienie do meta)
                if not imdb:
                    imdb = tmdb_media_item_response.get("imdb")
                if not tvdb:
                    tvdb = tmdb_media_item_response.get("tvdb")
                if not tmdb:
                    tmdb = tmdb_media_item_response.get("tmdb")
                pass

            # meta = {"imdb": imdb, "tmdb": tmdb, "tvdb": tvdb, "lang": self.lang, "user": self.user, "item": tmdb_media_item_response}
            meta = {"item": tmdb_media_item_response}
            self.meta.append(meta)

        except Exception as e:
            fflog_exc(1)
            print(traceback.format_exc())
            pass


    def get_media_id(self, tmdb_id, imdb_id):
        if not tmdb_id and imdb_id:
            try:
                url = self.tmdb_by_imdb % imdb_id
                result = self.session.get(url, timeout=16).json()  # zapytanie do serwera

                if self.content_type == "movie":
                    result = result.get("movie_results", [])
                elif self.content_type == "tvshow" or self.content_type == "tv":
                    result = result.get("tv_results", [])
                if result:
                    result = result[0]
                    tmdb_id = str(result.get("id", ""))
                if tmdb_id:
                    self.media_item.tmdb = tmdb_id
            except Exception:
                fflog_exc(1)
                pass
        media_id = tmdb_id or imdb_id
        if not media_id:
            raise Exception("Media id not found")
        return media_id


    def get_best_poster(self, i, arts):
        posters = [{"url": self.media_list[i].get("poster", ""), "priority": 2, "lang": ""}]
        _poster2 = self.get_best_image(arts["posters"], "iso_639_1", self.posterby)
        if isinstance(_poster2, dict):
            posters.append({"url": f"https://image.tmdb.org/t/p/{self.qualityp}{_poster2['file_path']}", "priority": 1, "lang": _poster2["iso_639_1"]})
        if isinstance(_poster2, str):
            posters.append({"url": f"https://image.tmdb.org/t/p/{self.qualityp}{_poster2}", "priority": 1, "lang": ""})
        if posters:
            best_poster = min(posters, key=lambda x: x['priority']).get("url")
        else:
            best_poster = None
        self.media_item.poster = best_poster
        return best_poster


    def get_best_clearlogo(self, i, arts):
        posters = [{"url": self.media_list[i].get("clearlogo", ""), "priority": 2, "lang": ""}]
        _poster2 = self.get_best_image(arts["logos"], "iso_639_1", self.posterby)
        if isinstance(_poster2, dict):
            posters.append({"url": f"https://image.tmdb.org/t/p/{self.qualityp}{_poster2['file_path']}", "priority": 1, "lang": _poster2["iso_639_1"]})
        if isinstance(_poster2, str):
            posters.append({"url": f"https://image.tmdb.org/t/p/{self.qualityp}{_poster2}", "priority": 1, "lang": ""})
        if posters:
            best_poster = min(posters, key=lambda x: x['priority']).get("url")
        else:
            best_poster = None
        # fflog(f'[get_best_clearlogo] best_logo: {best_poster}')
        self.media_item.clearlogo = best_poster
        return best_poster


    def _get_best_landscape(self, tmdb_media_item_response, arts, *, no_lang: bool, anyone=True):
        fan_arts = []
        _fan_art2 = self.get_best_image(arts["backdrops"], "iso_639_1", self.fanartby, no_lang=no_lang, anyone=anyone)
        if isinstance(_fan_art2, dict):
            fan_arts.append({"url": f"https://image.tmdb.org/t/p/{self.qualityf}{_fan_art2['file_path']}", "priority": 1, "lang": _fan_art2["iso_639_1"]})
        if isinstance(_fan_art2, str):
            fan_arts.append({"url": f"https://image.tmdb.org/t/p/{self.qualityf}{_fan_art2}", "priority": 1, "lang": ""})
        fan_art = tmdb_media_item_response.get("backdrop_path")
        fan_arts.append(
            {"url": self.tm_img_link % ("1920",
             tmdb_media_item_response.get("backdrop_path")),
             "priority": 2,
             "lang": "",
            }) if fan_art else ""
        if fan_arts:
            return min(fan_arts, key=lambda x: x['priority']).get("url")
        return None


    def _get_best_poster(self, tmdb_media_item_response, arts, *, no_lang: bool, anyone=True):
        posters = []
        _poster2 = self.get_best_image(arts["posters"], "iso_639_1", self.fanartby, no_lang=no_lang, anyone=anyone)
        if isinstance(_poster2, dict):
            posters.append({"url": f"https://image.tmdb.org/t/p/{self.qualityp}{_poster2['file_path']}", "priority": 1, "lang": _poster2["iso_639_1"]})
        if isinstance(_poster2, str):
            posters.append({"url": f"https://image.tmdb.org/t/p/{self.qualityp}{_poster2}", "priority": 1, "lang": ""})
        if posters:
            return min(posters, key=lambda x: x['priority']).get("url")
        return None


    def _get_best_clearlogo1(self, tmdb_media_item_response, arts, *, no_lang: bool):
        fan_arts = []
        _fan_art2 = self.get_best_image(arts["logos"], "iso_639_1", self.fanartby, no_lang=no_lang)
        if isinstance(_fan_art2, dict):
            fan_arts.append({"url": f"https://image.tmdb.org/t/p/{self.qualityf}{_fan_art2['file_path']}", "priority": 1, "lang": _fan_art2["iso_639_1"]})
        if isinstance(_fan_art2, str):
            fan_arts.append({"url": f"https://image.tmdb.org/t/p/{self.qualityf}{_fan_art2}", "priority": 1, "lang": ""})
        fan_art = tmdb_media_item_response.get("logo_path")
        fan_arts.append(
            {"url": self.tm_img_link % ("1920",
             tmdb_media_item_response.get("logo_path")),
             "priority": 2,
             "lang": "",
            }) if fan_art else ""
        # fflog(f'[_get_best_clearlogo1] logos:{fan_arts}')
        if fan_arts:
            return min(fan_arts, key=lambda x: x['priority']).get("url")
        return None


    def get_best_keyart(self, tmdb_media_item_response, arts):
        art = self._get_best_poster(tmdb_media_item_response, arts, no_lang=True, anyone=False)  # poster (plakat) bez napisów, czyli bez języka (kod 00 albo null)
        self.media_item.keyart = art
        return art


    def get_best_fanart(self, tmdb_media_item_response, arts):
        art = self._get_best_landscape(tmdb_media_item_response, arts, no_lang=True)  # landscape bez napisów, czyli bez języka (kod 00 albo null)
        self.media_item.fanart = art
        return art


    def get_best_landscape(self, tmdb_media_item_response, arts):
        art = self._get_best_landscape(tmdb_media_item_response, arts, no_lang=False)
        self.media_item.landscape = art
        return art


    def get_best_clearlogo1(self, tmdb_media_item_response, arts):
        art = self._get_best_clearlogo1(tmdb_media_item_response, arts, no_lang=False)
        # fflog(f'[get_best_clearlogo1] logo: {art}')
        self.media_item.clearlogo = art
        return art


    def get_other_arts0(self):
        banner = clearart = discart = ""  # raczej zerowanie (tmdb tego nie udostępnia na razie)
        # clearlogo = ""  # już dorobiłem
        # self.media_item.clearlogo = clearlogo
        self.media_item.banner = banner
        self.media_item.clearart = clearart
        self.media_item.discart = discart
        # return banner, clearlogo, clearart, discart
        return banner, clearart, discart


    def get_other_arts(self, tmdb, tvdb, title, year):
        ret = {}
        if self.fanartTV_artwork == "true":
            if self.content_type == 'movie':
                ret = self.fanart_tv_art(tmdb, title, year)
                #pass
            else:
                if tvdb and tvdb not in ["None", "0"]:
                    # self.get_other_arts0()
                    ret = self.fanart_tv_art(tvdb, title, year)
                    #pass
            if ret:
                for k,v in ret.items():
                    # fflog(f'{k=} {v=}')
                    # if v:  # pustych nie zapisujemy
                    if not getattr(self.media_item, k):  # aby nie nadpisywać, bo często fanartTV nie ma obrazków w pl
                        setattr(self.media_item, k, v)
        else:
            # self.get_other_arts0()  # w sumie to po co to ?
            pass


    def get_trailer(self, tmdb_media_item_response):
        # videos = tmdb_media_item_response.get("videos")
        # fflog(f"\n{videos=}")
        # fflog(f'{tmdb_media_item_response.get("videos", {}).get("results", [])=}')
        # trailer = self.get_best_trailer(tmdb_media_item_response.get("videos", {}).get("results", []), "iso_639_1", "official")
        trailer = self.get_best_trailer(tmdb_media_item_response.get("videos", {}).get("results", []), "iso_639_1", "official", "size")
        if (trailer
            # and trailer.get("type") == "Trailer"  # może to trzeba wcześniej odfiltrowywać ?
           ):
            # fflog(f"\n{trailer=}")
            if trailer.get("site") == "YouTube":
                key = trailer.get("key")
                trailer = f"https://www.youtube.com/watch?v={key}"
                # name = trailer.get("name")
            else:
                pass  # bo nie wiem, co robić jak to nie z youtuba
                trailer = ""  # może na razie tak
            if trailer:
                self.media_item.trailer = trailer


    def get_tmdb_api_item(self, media_id):  # pobiera informacje o filmie bądź serialu
        # ustalenie adresu url
        if self.content_type == 'movie':
            en_url = self.tmdb_api_link_movies % media_id
        elif self.content_type == 'tvshow' or self.content_type == "tv":
            en_url = self.tmdb_api_link_tvshows % media_id
        f_url = f"{en_url},translations"
        url = en_url if self.lang == "en" else f_url
        # control.log(f'{url=}', 1)
        r = self.session.get(url, timeout=16)  # zapytanie do serwera
        if not r:
            fflog(f'{r=}  {url=}')
            # return
        r.encoding = "utf-8"
        return r.json()


    # def get_media_titles(self, title_from_list, tmdb_media_item_response, original_language, list_title) -> MediaLanguageDetails:
    def get_media_titles(self, tmdb_media_item_response, original_language, list_title) -> MediaLanguageDetails:
    
        try:
            if self.lang == "en":
                english_translated_result = None
            else:
                english_translated_result = next(
                    (x["data"] for x in tmdb_media_item_response.get("translations", {}).get("translations", {}) if x.get("iso_639_1") == "en"), {})

            name = tmdb_media_item_response.get("title", "")  # tłumaczenie na lokalny język interfejsu (czyli na 99% polski)
            if not name:
                name = tmdb_media_item_response.get("name", "")

            original_name = tmdb_media_item_response.get("original_title", "")  # tytuł oryginalny
            if not original_name:
                original_name = tmdb_media_item_response.get("original_name", "")

            en_trans_name = (english_translated_result.get("title", "") if not self.lang == "en" else None)  # angielski tytuł
            if not en_trans_name:
                en_trans_name = (english_translated_result.get("name", "") if not self.lang == "en" else None)

            if self.lang == "en":
                original_title = title = name
            elif self.lang == original_language:
                original_title = original_name
                title = name
            else:
                original_title = en_trans_name or original_name  # dlatego przeważnie ląduje tu angielski tytuł
                if name == original_name and en_trans_name:
                    title = en_trans_name
                else:
                    title = name

            self.media_item.title = title
            self.media_item.originaltitle = original_title  # a powinno być original_name
            # self.media_item.label = title  # nie wiem, po co to potrzebne
            self.media_item.originalname = original_name  # nie ma takiego pola (originalname) w ListItem (bo na to jest przeznaczone originaltitle)
            self.media_item.englishtitle = en_trans_name  # nieprzetestowane do końca jeszcze
            # self.media_item.originaltitle = original_name  # trzeba by przerobić pozostały kod

            # log_utils.fflog(f"\n {english_translated_result=} \n {original_title=} {title=} {original_name=} \n ({name=} {en_trans_name=})", 1)
            # log_utils.fflog(f"prawidłowo powinno być (standard ListItem): {title=} {original_name=} ({en_trans_name=})  |  {original_title=} {name=} {english_translated_result=}", 1)
            # log_utils.fflog(f"do wyszukiwarki źródeł powinno lecieć: {en_trans_name=} {name=} {original_name=}" ,1)
            #return MediaLanguageDetails(english_translated_result, original_title, title)
            # return MediaLanguageDetails(english_translated_result, original_title, title, original_name)
            return MediaLanguageDetails(english_translated_result)  # eksperyment
        except Exception:
            fflog_exc(1)
            #return MediaLanguageDetails({}, list_title, list_title)
            # return MediaLanguageDetails({}, list_title, list_title, list_title)
            return MediaLanguageDetails({})  # eksperyment


    def get_best_image(self, images, lang_key, vote_key=None, size_key=None, *, no_lang=False, anyone=True):
        """Get best image from `images` by `*_key` keys, matching to languages."""
        # fflog(f'{lang_key=} {vote_key=} {size_key=} {no_lang=} {anyone=}')
        # fflog(f'{images=}')
        if not images:
            return

        # Kolejnośc jezyków, z uwzględnieniem wymuszenia braku języka (przydatne dla fanart)
        if no_lang:
            if anyone:
                my_language_order = (None, False, "", "00", *self.my_language_order)
            else:
                my_language_order = (None, False, "", "00")
        else:
            my_language_order = self.my_language_order
        #fflog(f'{my_language_order=}')

        # Przeglądając **po kolei** jezyki sortujemy po głosowaniu i wielkości (o ile klucze podane)
        best = [img for lang in my_language_order
                 for img in sorted((
                                    # img for img in reversed(images)  # czemu reversed ?
                                    img for img in images
                                    if img[lang_key] == lang
                                    ),
                                     key=lambda im: (vote_key and -im[vote_key],
                                                     size_key and -im[size_key],
                                                    )
                                  )
               ]
        #fflog(f'{best=} \n')

        # pasujący, lub jakikolwiek.
        if best:
            #fflog(f'zwracam   {best[0]=} \n')
            return best[0]
        if anyone:
            #fflog(f'zwracam {images[0]=} \n')
            return images[0]


    def get_best_trailer(self, images, lang_key, vote_key=None, size_key=None, *, no_lang=False, anyone=True):
        """Get best video from `videos` by `*_key` keys, matching to languages."""
        """ przerobione na szybko z 'get_best_image' """
        # fflog(f'{lang_key=} {vote_key=} {size_key=} {no_lang=} {anyone=}')
        # fflog(f'{images=}')
        if not images:
            return

        # Kolejnośc jezyków, z uwzględnieniem wymuszenia braku języka (przydatne dla fanart)
        if no_lang:
            if anyone:
                my_language_order = (None, False, "", "00", *self.my_language_order)
            else:
                my_language_order = (None, False, "", "00")
        else:
            my_language_order = self.my_language_order
        #fflog(f'{my_language_order=}')

        # Przeglądając **po kolei** jezyki sortujemy po głosowaniu i wielkości (o ile klucze podane)
        best = [img for lang in my_language_order
                 for img in sorted((
                                    # img for img in reversed(images)  # czemu reversed ?
                                    img for img in images
                                    if (
                                        img[lang_key] == lang
                                        and img["type"] in ["Trailer", "Teaser"]
                                        and img["site"] == "YouTube"
                                       )
                                    ),
                                     key=lambda im: (vote_key and -im[vote_key],  # tu "official" or not
                                                     {'Trailer': 0, 'Teaser': 1,}[im["type"]],
                                                     size_key and -im[size_key],
                                                     "dubb" not in im["name"],  # dziwne, ale musi być zaprzeczenie tego, co chcemy aby było jako pierwsze
                                                    )
                                  )
               ]
        #fflog(f'{best=} \n')

        # pasujący, lub jakikolwiek.
        if best:
            #fflog(f'zwracam   {best[0]=} \n')
            return best[0]
        if anyone:
            #fflog(f'zwracam {images[0]=} \n')
            return images[0]


    def get_cast_with_thumbnail(self, media_item):
        cast_with_thumb = []
        cast = media_item.get("credits", {}).get("cast")
        cast = cast[:30] if cast else None
        if cast:
            for person in cast:
                _icon = person.get("profile_path")
                icon = self.tm_img_link % ("185", _icon) if _icon else ""
                cast_with_thumb.append({"name": person.get("name", ""), "role": person.get("character", ""), "thumbnail": icon, })
        if not cast_with_thumb:
            cast_with_thumb = ""
        self.media_item.castwiththumb = cast_with_thumb
        return cast_with_thumb


    def get_arts(self, tmdb, imdb):
        media_id = tmdb if tmdb else imdb
        if self.content_type == "movie":
            arts_url = self.tmdb_arts_movies % media_id
        elif self.content_type == "tvshow" or self.content_type == "tv":
            arts_url = self.tmdb_arts_tvshows % media_id
        result = self.session.get(arts_url, timeout=10)  # zapytanie do serwera
        # result.raise_for_status()  # dla 404 też wywala błąd
        if not result:
            fflog(f'brak grafik dla {media_id=}')
            return {}
        result.encoding = "utf-8"
        return result.json()


    def get_providers(self, tmdb, imdb):
        media_id = tmdb if tmdb else imdb
        if self.content_type == "movie":
            result = self.session.get(self.tmdb_providers_movies % media_id, timeout=10)  # serwer
        if self.content_type == "tvshow" or self.content_type == "tv":
            result = self.session.get(self.tmdb_providers_tvshows % media_id, timeout=10)  # serwer
        # result.raise_for_status()
        if not result:
            return ""
        result.encoding = "utf-8"
        provider = result.json()

        providers_results = provider.get("results")
        providers_link = providers_results.get(self.lang.upper(), {}).get("link", "") if providers_results else ""
        providers_list = [i.get("provider_name", "") for i in
                          providers_results.get(self.lang.upper(), {}).get("flatrate", [])]
        if providers_link:
            providers = {"link": providers_link, "provider_list": providers_list}
            self.media_item.__setattr__("providers", providers)
            return providers
        else:
            self.media_item.__setattr__("providers", "")
            return ""


    def get_writer_and_director(self, media_item) -> Crew:
        crew = media_item.get("credits", {}).get("crew")
        if crew:

            director_jobs = []
            for x in crew:
                if x.get("job") == "Director":
                    director_jobs.append(x)
            director_name = []
            for d in director_jobs:
                director_name.append(d.get("name", ""))
            director = ", ".join(director_name)

            writer_jobs = []
            for y in crew:
                if y.get("job") in ["Writer", "Screenplay", "Author", "Novel"]:
                    writer_jobs.append(y)
            writer_name = []
            for w in writer_jobs:
                writer_name.append(w.get("name", ""))
            writer = ", ".join(writer_name)

        else:
            director = writer = ""

        self.media_item.__setattr__("director", director)
        self.media_item.__setattr__("writer", writer)
        return Crew(writer, director)


    def fanart_tv_art(self, id_db, title="", year="", all_imgs=False):
        ret = {}
        lang = self.lang
        # control.log(f'{self.fanart_tv_user=}', 1)
        # control.log(f'{self.fanart_tv_headers=}', 1)
        if self.fanart_tv_user != '':
            try:
                # control.log(f'url: {self.fanart_tv_art_link % id_db}  {self.fanart_tv_headers=}', 1)
                r = self.session.get(self.fanart_tv_art_link % id_db, headers=self.fanart_tv_headers, timeout=10, )
                # fflog(f'from FanartTV: {r=}')
                if r.status_code >= 400 and r.status_code != 404:
                    fflog(f'code:{r.status_code}  {r.text=}   {id_db=} {title=} {year=}', 1)
                    pass
                r.raise_for_status()

                r.encoding = "utf-8"
                art = r.json()  # if six.PY3 else utils.json_loads_as_str(r.text)
                # fflog(f'{art=}')
            except Exception:
                art = {}
                pass

            if art:
                if self.content_type == "movie":
                    props  = [
                              ("poster", "movieposter"),
                              ("clearart", ("hdmovieclearart","clearart")),
                              ("clearlogo", ("hdmovielogo","clearlogo")),
                              ("banner", "moviebanner"),
                              ("fanart", ("moviebackground")),
                              # ("landscape", "moviethumb"),
                              ("landscape", ("moviethumb","moviebackground")),  # z fallbackiem
                              ("discart", "moviedisc"),
                              ("keyart", "movieposter"),  # poster tylko z językiem "00"
                             ]
                else:
                    # props = []  # dla seriali jeszcze nie zrobione
                    props  = [
                              ("poster", "tvposter"),
                              ("seasons_posters", "seasonposter"),
                              ("clearart", ("hdclearart","clearart")),
                              ("clearlogo", ("hdtvlogo","clearlogo")),
                              ("banner", "tvbanner"),
                              ("seasons_banners", "seasonbanner"),
                              ("fanart", ("showbackground")),
                              ("seasons_fanarts", ("showbackground")),
                              # ("landscape", "tvthumb"),
                              ("landscape", ("tvthumb","showbackground")),  # z fallbackiem
                              ("seasons_landscapes", "seasonthumb"),
                              ("keyart", "tvposter"),  # poster tylko z językiem "00"
                              ("characterart", "characterart"),  # nie wiem, czy jest jeszcze używane w Kodi i nie wiem, pod jaką powinno być to nazwą
                             ]

                order = 1  #
                # order = -1  # odwrócenie
                # ale teraz api zwraca mi jako pierwsze elementy, które mają najwięcej głosów, więc nie potrzeba odwracać

                def _get_property(var, prop):
                    val = ""
                    try:
                        if isinstance(prop, tuple):
                            prop, prop2 = prop
                        else:
                            prop2 = ""

                        if prop in art:
                            val = art[prop]
                        elif prop2 in art:
                            val = art[prop2]
                        else:
                            val = []

                        if var != "keyart":
                            val = (  [x for x in val if x.get("lang") == lang][::order] 
                                   + [x for x in val if x.get("lang") == "en"][::order] 
                                   + [x for x in val if x.get("lang") in ["00", ""]][::order]
                                  )
                        else:  # keyart
                            val = [x for x in val if x.get("lang") in ["00", ""]][::order]

                        if val:
                            if all_imgs:
                                if "season" in var:
                                    val = {x["season"]: x for x in val}
                                return val
                            elif "character" in prop:
                                val = [x["url"] for x in val]
                                if len(val) == 1:
                                    val = val[0]
                            else:
                                if "season" in var:
                                    # val = {x["season"]: x["url"] for x in reversed(val)}
                                    val = {x["season"]: x["url"] for x in val[::-order]}
                                else:
                                    if prop == "showbackground":
                                        val = [x for x in val if x.get("season") in ["all", ""]]
                                    val = val[0]["url"]

                        if not val:
                            val = ""  # bo może być coś innego niż string
                            pass

                    except Exception:
                        fflog_exc(1)
                        # raise Exception()
                        # val = ""
                        pass

                    # fflog(f'{var=} {val=}')
                    return val

                for var, prop in props:
                    val = _get_property(var, prop)
                    if val:
                        ret.update({var: val})

        else:
            fflog('brak danych do zalogowania do fanart')
            pass

        if r.status_code == 200:
            # fflog(f'{ret=}')
            pass

        return ret

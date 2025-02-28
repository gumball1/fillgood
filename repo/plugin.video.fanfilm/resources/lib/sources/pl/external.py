"""
    FanFilm Add-on  2024
"""

import json
# For playermb mylist support
import os.path
import re
from collections.abc import Mapping
from urllib.parse import parse_qs, urlencode

import requests
import xbmcaddon
import xbmcvfs
import xbmc

from ptw.libraries import cleantitle, control, apis
from ptw.libraries.log_utils import log, fflog
from ptw.debug import log_exception, fflog_exc

import xml.etree.ElementTree as ET

from resources.lib.indexers.jwgraph import jwgraph

netflix_plugin = "plugin.video.netflix"
prime_plugin = "plugin.video.amazon-test"
max_plugin = "slyguy.max"
disney_plugin = "slyguy.disney.plus"
iplayer_plugin = "plugin.video.iplayerwww"
curstream_plugin = "slyguy.curiositystream"
hulu_plugin = "slyguy.hulu"
paramount_plugin = "slyguy.paramount.plus"
playerpl_plugin = "plugin.video.playermb"
polsatbox_plugin = "plugin.video.pgobox"
viaplay_plugin = "plugin.video.viaplay"
# vodpl_plugin = "plugin.video.vod_pl"
vodpl_plugin = "plugin.video.vod_pl_NIEOBSLUGIWANY"
upcgo_plugin = "plugin.video.horizongo"
skyott_plugin = "plugin.video.skyott"
canalplus_plugin = "plugin.video.canalplus"  # strzelam, bo nie znam nazwy wtyczki

netflix_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % netflix_plugin)
prime_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % prime_plugin)
max_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % max_plugin)
disney_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % disney_plugin)
iplayer_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % iplayer_plugin)
curstream_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % curstream_plugin)
hulu_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % hulu_plugin)
paramount_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % paramount_plugin)
playerpl_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % playerpl_plugin)
polsatbox_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % polsatbox_plugin)
viaplay_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % viaplay_plugin)
vodpl_enabled = control.condVisibility('System.AddonIsEnabled(%s)' % vodpl_plugin)
upcgo_enabled = control.condVisibility('System.AddonIsEnabled(%s)' % upcgo_plugin )
skyott_enabled = control.condVisibility("System.AddonIsEnabled(%s)" % skyott_plugin)
canalplus_enabled = control.condVisibility('System.AddonIsEnabled(%s)' % canalplus_plugin )
# for info only (in debug mode)
fflog(f'\n {netflix_enabled=}\n {prime_enabled=}\n {max_enabled=}\n {disney_enabled=}\n {iplayer_enabled=}\n {curstream_enabled=}\n {hulu_enabled=}\n {paramount_enabled=}\n {playerpl_enabled=}\n {polsatbox_enabled=}\n {viaplay_enabled=}\n {vodpl_enabled=}\n {upcgo_enabled=}\n {skyott_enabled=}\n {canalplus_enabled=}', 0)

netflix_pattern = "plugin://plugin.video.netflix/play/movie/%s"
netflix_show_pattern = 'plugin://plugin.video.netflix/play/show/%s/season/%s/episode/%s/'
prime_pattern = "plugin://plugin.video.amazon-test/?asin=%s&mode=PlayVideo&name=None&adult=0&trailer=0&selbitrate=0"
max_pattern = "plugin://slyguy.max/?_=play&_play=1&id="
disney_pattern = "plugin://slyguy.disney.plus/?_=play&_play=1&family_id=%s&profile_id=%s"
iplayer_pattern = "plugin://plugin.video.iplayerwww/?url=%s&mode=202&name=null&iconimage=null&description=null&subtitles_url=&logged_in=False"
curstream_pattern = "plugin://slyguy.curiositystream/?_=play&_play=1&id="
hulu_pattern = "plugin://slyguy.hulu/?_=play&id="
paramount_pattern = "plugin://slyguy.paramount.plus/?_=play&id="
playerpl_pattern = "plugin://plugin.video.playermb/?mode=playvid&url="
polsatbox_pattern = "plugin://plugin.video.pgobox/?mode=playtvs&url="
viaplay_pattern = "plugin://plugin.video.viaplay/play?guid=%s&url=None&tve=false"
vodpl_pattern = "plugin://plugin.video.vod_pl/?mode=playvid&url="
upcgo_pattern = "plugin://plugin.video.horizongo/?mode=playReplayTV&progID="
skyott_pattern = "plugin://plugin.video.skyott/?action=play&slug="
canalplus_pattern = "plugin://plugin.video.canaplus/?akcja="  # fejkowy wpis, tylko na test

all_providers = [netflix_enabled, prime_enabled, max_enabled,
                 disney_enabled, iplayer_enabled, curstream_enabled,
                 hulu_enabled, paramount_enabled, playerpl_enabled,
                 polsatbox_enabled, viaplay_enabled, vodpl_enabled,
                 upcgo_enabled, skyott_enabled, canalplus_enabled]
scraper_init = any(e for e in all_providers)
fflog(f'{scraper_init=}')
if scraper_init:
    all_providers = {"netflix_enabled":netflix_enabled, "prime_enabled":prime_enabled, "max_enabled":max_enabled,
                     "disney_enabled":disney_enabled, "iplayer_enabled":iplayer_enabled, "curstream_enabled":curstream_enabled,
                     "hulu_enabled":hulu_enabled, "paramount_enabled":paramount_enabled, "playerpl_enabled":playerpl_enabled,
                     "polsatbox_enabled":polsatbox_enabled, "viaplay_enabled":viaplay_enabled, "vodpl_enabled":vodpl_enabled,
                     "upcgo_enabled":upcgo_enabled, "skyott_enabled":skyott_enabled, "canalplus_enabled":canalplus_enabled, }
    # fflog(f'{all_providers=}')
    enabled_providers = [k.replace("_enabled", "") for k,v in all_providers.items() if v]
    fflog(f'{enabled_providers=}')

class source:

    def __init__(self):
        try:
            self.priority = 1
            self.language = "pl"
            self.domains = []
            self.base_link = ""
            self.session = requests.Session()
            # self.tm_user = control.setting("tm.user") or apis.tmdb_API
            self.country = control.setting("external.country") or "US"
            # self.tmdb_by_imdb = "https://api.themoviedb.org/3/find/{}?api_key={}&external_source=imdb_id".format("%s", self.tm_user)
            self.aliases = []
            self.justwatch = jwgraph.JustWatchAPI(country=self.country)
            self.justwatch_pl = jwgraph.JustWatchAPI(country=self.country, language=self.language)
        except Exception:
            fflog_exc(1)
            pass


    def movie(self, imdb, title, localtitle, aliases, year):
        if not scraper_init:
            return
        try:
            self.aliases.extend(aliases)
            url = {"imdb": imdb, "title": title, "localtitle": localtitle, "year": year}
            url = urlencode(url)
            return url
        except Exception:
            fflog_exc(1)
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        if not scraper_init:
            return
        try:
            self.aliases.extend(aliases)
            url = {"imdb": imdb, "tvdb": tvdb, "tvshowtitle": tvshowtitle, "localtvshowtitle": localtvshowtitle, "year": year}
            url = urlencode(url)
            return url
        except Exception:
            fflog_exc(1)
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
        except Exception:
            fflog_exc(1)
            return


    def sources(self, url, hostDict, hostprDict):
        return self._sources(url, hostDict, hostprDict)


    def _sources(self, url, hostDict, hostprDict):
        def jget(url, params=None):
            return requests.get(url, params=params).json()

        sources = []
        if url is None:
            # fflog(f'{url=}')
            return sources

        data = parse_qs(url)
        data = dict([(i, data[i][0]) if data[i] else (i, "") for i in data])
        if not data:
            fflog(f"Given {url=} -> {data=} are wrong")
            return
            
        title = data["tvshowtitle"] if "tvshowtitle" in data else data.get("title")
        if not title:
            fflog(f'title is missing ({title=})')
            return
        localtitle = local_title = data["localtvshowtitle"] if "localtvshowtitle" in data else (data.get("localtitle", "") or "")
        year = data.get("year", "0") or "0"
        content = "movie" if "tvshowtitle" not in data else "show"

        result = None

        r = self.justwatch.search_item(title.lower())
        r_pl = self.justwatch_pl.search_item(title.lower())
        items = r['popularTitles']['edges']
        items = items + r_pl['popularTitles']['edges']

        jw_id = [x[1] for i in items for x in i.items()]

        for i in jw_id:
            if isinstance(i, dict):
                title = cleantitle.normalize(cleantitle.query(title)).lower()
                local_title = cleantitle.normalize(cleantitle.query(localtitle)).lower()
                content_title = cleantitle.normalize(cleantitle.query(i['content']['title'])).lower()
                if ((local_title == content_title and int(year) == int(i['content']['originalReleaseYear'])) or
                    (title == content_title and int(year) == int(i['content']['originalReleaseYear']))):
                    jw_id = i['content']['fullPath']
                    break

        if not isinstance(jw_id, str):
            fflog(f"Given params ({title=}, {local_title=}, {year=}) not match to any records in jw database")
            return

        r = self.justwatch.get_title(jw_id)

        if content == 'show':
            try:
                item = r["url"]["node"]["seasons"]
                item = [i for i in item if i['content']['seasonNumber'] == int(data["season"])][0]
                full_path = item['content']['fullPath']

                r = self.justwatch.get_title(full_path)
                item = r['url']['node']['episodes']
                id = [i['id'] for i in item if i['content']['episodeNumber'] == int(data['episode'])][0]
            except:
                fflog(f"Given params for tvshow (episode) do not match to any records in jw database")
                return
        else:
            id = r['url']['node']['id']

        result = self.justwatch.get_providers(id)
        #fflog('justwatch result: ' + repr(result))
        if not result:
            raise Exception(f"{title!r} not found in jw database")
        #fflog(f'{len(result)=}')

        offers = result['node']
        #fflog('justwatch offers: ' + repr(offers))
        if not offers:
            raise Exception(f"{title!r} not available in {self.country!r}")
        #fflog(f'{len(offers)=}')

        # for inforamtion only
        found_providers = [n for o in offers.get('flatrate',[]) if (n := o.get('package').get('clearName'))]
        found_providers += [n for o in offers if isinstance(o,dict) and (n := o.get("package_short_name"))]
        fflog(f'{found_providers=}')

        netflix = ["Netflix"]
        prime = ["Amazon Prime Video"]
        mmax = ["Max"]
        disney = ["Disney Plus"]
        iplayer = ["bbc"] # no clearname
        curstream = ["Curiosity Stream"]
        hulu = ["Hulu"]
        paramount = ["Paramount"]
        playerpl = ["Player"]
        polsatbox = ["ipl"] # no clearname
        viaplay = ["Viaplay"]
        vodpl = ["VOD Poland"]
        upcgo = ["Horizon"]
        skyott = ["SkyShowtime"]
        canalplus = ["Canal+ Premium"]

        streams = []


        if canalplus_enabled:
            # fflog('canalplus_enabled')
            streams.append(("Canal+", ""))  # tylko dla demonstracji, że justwatch zwraca też i dla Canal+
            pass


        if netflix_enabled:
            # fflog('netflix_enabled')
            try:
                nfx = [o for o in offers['flatrate'] if o['package']['clearName'] in netflix]
                if nfx:
                    nfx_id = nfx[0]["standardWebURL"]
                    nfx_id = nfx_id.rstrip("/").split("/")[-1]
                    if content == "movie":
                        netflix_id = nfx_id
                        streams.append(("netflix", netflix_pattern % netflix_id))
                    else:
                        netflix_id = self.netflix_ep_id(nfx_id, data["season"], data["episode"])
                        url = netflix_show_pattern % (nfx_id, netflix_id[1], netflix_id[0])
                        streams.append(("netflix", url))
            except Exception:
                fflog_exc(1)
                pass


        if prime_enabled:
            # fflog('prime_enabled')
            try:
                prv = [o for o in offers['flatrate'] if o['package']['clearName'] in prime]
                if prv:
                    prime_id = prv[0]["standardWebURL"]
                    prime_id = prime_id.rstrip("/").split("gti=")[1]
                    streams.append(("amazon prime", prime_pattern % prime_id))
            except Exception:
                fflog_exc(1)
                pass


        if max_enabled:
            # fflog('max_enabled')
            try:
                hbm = [o for o in offers['flatrate'] if o['package']['clearName'] in mmax]
                if hbm:
                    max_id = hbm[0]["standardWebURL"]
                    max_id = max_id.rstrip("/").split("/")[-1]
                    if content == "movie":
                        max_id = max_id.split("?")[0]
                    streams.append(("max", max_pattern + max_id))
            except Exception:
                fflog_exc(1)
                pass


        if skyott_enabled:
            # fflog('skyott_enabled')
            try:
                sott = [o for o in offers['flatrate'] if o['package']['clearName'] in skyott]
                if sott:
                    sott_id = sott[0]["standardWebURL"]
                    sott_id = sott_id.split('https://www.skyshowtime.com/pl/stream')
                    streams.append(("sky showtime", skyott_pattern + sott_id[1]))
            except Exception:
                fflog_exc(1)
                pass


        if viaplay_enabled:
            # fflog('viaplay_enabled')
            try:
                vip = [o for o in offers['flatrate'] if o['package']['clearName'] in viaplay]
                if vip:
                    viaplay_url = vip[0]["standardWebURL"]
                    """
                    via_r = requests.get(viaplay_url)
                    via_r = via_r.text.replace("\r", "").replace("\n", "")
                    via_api = re.findall(':"multiPartial","href":"(.+?)&multiPartial=true', via_r)[0]
                    via_api_r = requests.get(via_api).json()
                    viaplay_id = via_api_r["_embedded"]["viaplay:blocks"][0]["_embedded"]["viaplay:product"]["system"][
                        "guid"]
                    streams.append(("viaplay", viaplay_pattern % viaplay_id))
                    """
                    html = requests.get(viaplay_url).text
                    if mch := re.search(r'<script\s+id="__NEXT_DATA__"\s+type="application/json"\s*>', html):
                        start = mch.end()
                        if (end := html.index('</script>', start)) > 0:
                            data = json.loads(html[start:end])
                            # fflog(json.dumps(data, indent=2))
                            raw = data['props']['pageProps']['storeState']['page']['raw']
                            guid = raw['_embedded']['viaplay:blocks'][0]['_embedded']['viaplay:product']['system']['guid']
                            streams.append(("viaplay", viaplay_pattern % guid))

            except Exception as e:
                #fflog("external viaplay exception:", #fflogINFO)
                #fflog(e, #fflogINFO)
                fflog_exc(1)
                pass


        if disney_enabled:
            # fflog('disney_enabled')
            try:
                dnp = [o for o in offers['flatrate'] if o['package']['clearName'] in disney]
                if dnp:
                    new_sess = requests.Session()

                    webUrl = dnp[0].get("standardWebURL")

                    family_id = None

                    if webUrl:
                        pattern = r'.*%2F([^&]+)&'
                        match = re.search(pattern, webUrl)

                        if match:
                            family_id = match.group(1)

                    CLIENT_ID = 'disney-svod-3d9324fc'
                    CLIENT_VERSION = '9.7.0'
                    CONFIG_URL = f'https://bam-sdk-configs.bamgrid.com/bam-sdk/v5.0/{CLIENT_ID}/android/v{CLIENT_VERSION}/google/tv/prod.json'

                    try:
                        path = xbmcvfs.translatePath("special://home/userdata/addon_data/slyguy.disney.plus/settings.xml")
                        root = ET.parse(path).getroot()
                    except IOError:
                        userdata_element = None
                    else:
                        userdata_element = root.find(".//setting[@id='_userdata']")

                    json_object = {}
                    if userdata_element is not None:
                        # Extract and decode the JSON data
                        json_data = (userdata_element.text or '{}').replace('&quot;', '"')
                        json_object = json.loads(json_data)

                    profile_id = json_object.get("profile_id") or "default"

                    HEADERS = {
                        'User-Agent': 'BAMSDK/v{} ({} 2.26.2-rc1.0; v5.0/v{}; android; tv)'.format(CLIENT_VERSION, CLIENT_ID, CLIENT_VERSION),
                        'x-application-version': 'google',
                        'x-bamsdk-platform-id': 'android-tv',
                        'x-bamsdk-client-id': CLIENT_ID,
                        'x-bamsdk-platform': 'android-tv',
                        'x-bamsdk-version': CLIENT_VERSION,
                        'Accept-Encoding': 'gzip',
                    }

                    API_VERSION = 6.1
                    REGION = "PL"
                    MATURITY = 1850
                    KID_MODE = False
                    APP_LANG = "pl"
                    ENCODED_FAMILY_ID = family_id

                    _args = {
                        'apiVersion': API_VERSION,
                        'region': REGION,
                        'kidsModeEnabled': 'true' if KID_MODE else 'false',
                        'impliedMaturityRating': MATURITY,
                        'appLanguage': APP_LANG,
                    }

                    if data.get("season") and data.get("episode"):
                        seasons_args = _args
                        seasons_args.update({'encodedSeriesId': ENCODED_FAMILY_ID})

                        href = new_sess.get(CONFIG_URL).json()['services']['content']['client']['endpoints']['getDmcSeriesBundle']['href']
                        formatted_url = href.format(**seasons_args)

                        response = new_sess.get(formatted_url, headers=HEADERS).json()['data']['DmcSeriesBundle']['seasons']['seasons']

                        season = data["season"]
                        for row in response:
                            number = row["seasonSequenceNumber"]
                            if int(season) == int(number):
                                episodes_call = new_sess.get(CONFIG_URL).json()['services']['content']['client']['endpoints']['getDmcEpisodes']['href']
                                episodes_args = _args
                                PAGE_SIZE_CONTENT = 30
                                episodes_args.update({
                                     "seasonId": row["seasonId"],
                                     "pageSize": PAGE_SIZE_CONTENT,
                                     "page": 1

                                 })
                                eps_response = new_sess.get(episodes_call.format(**episodes_args)).json()

                                for video in eps_response["data"]["DmcEpisodes"]["videos"]:
                                    ep = data["episode"]
                                    if int(video["episodeSequenceNumber"]) == int(ep):
                                        family_id = video["family"]["encodedFamilyId"]

                    streams.append(("disney+", disney_pattern % (family_id, profile_id)))
            except Exception as e:
                #fflog("external disney exception:", #fflogINFO)
                #fflog(e, #fflogINFO)
                fflog_exc(1)
                pass


        if playerpl_enabled:
            # fflog('playerpl_enabled')

            def append(vod):
                quality = "4K" if vod.get("uhd") else "1080p"
                streams.append({"source": "player pl",
                    "url": playerpl_pattern + str(vod['id']), "quality": quality, })

            try:
                plp = [o for o in offers['flatrate'] if o['package']['clearName'] in playerpl]
                plp_id = plp[0]["standardWebURL"]

                r = re.search((r"(?:/(?P<serial_slug>[^/]*)-odcinki,(?P<sid>\d+))?"
                               r"/(?P<slug>[^/]+?)(?:,S(?P<season>\d+)E(?P<episode>\d+))?,(?P<id>\d+)$"),
                              plp_id, )
                if r:
                    slug, aid, sn, en = r.group("slug", "id", "season", "episode")
                    if sn:
                        slug = r.group("serial_slug")
                        sn, en = int(sn), int(en)

                params = {
                    '4K': True,
                    'platform': 'BROWSER'
                }
                api = jget(f'https://player.pl/playerapi/item/translate?articleId={aid}', params=params)
                found = jget("https://player.pl/playerapi/product/vod/search", params={'keyword': slug, **params})

                for item in found.get("items", []):
                    season = item.get("season", {})
                    serial = item.get("season", season.get("serial", {}))
                    vslug = (item["slug"] or season.get("slug", "") or serial.get("slug", ""))
                    if vslug == slug:
                        if sn and en:
                            # episode
                            url = f'https://player.pl/playerapi/product/vod/serial/{item["id"]}/season/list'
                            for season in jget(url, params=params):
                                if season["number"] == sn:
                                    url = f'https://player.pl/playerapi/product/vod/serial/{item["id"]}/season/{season["id"]}/episode/list'
                                    for episode in jget(url, params=params):
                                        if episode["episode"] == en:
                                            append(episode)
                                            break
                        else:
                            # vod (movie)
                            append(item)

            except Exception as e:
                #fflog("external playerpl exception:", #fflogINFO)
                #fflog(e, #fflogINFO)
                fflog_exc(1)
                pass


        if vodpl_enabled:
            # fflog('vodpl_enabled')
            try:
                vodpl = [o for o in offers['flatrate'] if o['package']['clearName'] in vodpl]
                vodpl_id = vodpl[0]["standardWebURL"].split(',')[-1]
                url = vodpl_pattern + str(vodpl_id)
                streams.append(("vod pl", url))
            except Exception as e:
                #fflog("external vodpl exception:", #fflogINFO)
                #fflog(e, #fflogINFO)
                fflog_exc(1)
                pass


        if upcgo_enabled:
            # fflog('upcgo_enabled')

            def append(id):
                source = "UPC TV Go - My Prime" if '8001' in id else "UPC TV Go"
                quality = "1080p" if 'OTT' in id else "SD"
                url = upcgo_pattern + id + '&contType=vod'
                if quality == '1080p':
                    streams.append({"source": source, "url": url, "quality": quality})

            try:
                hrz = [o for o in offers['flatrate'] if o['package']['clearName'] in upcgo]
                t_crid = re.search('crid:(.+)', hrz[0]['standardWebURL']).group(0).split('/')[0]
                if hrz:
                    api_url = 'https://spark-prod-pl.gnp.cloud.upctv.pl/pol/web'
                    search = f'{api_url}/discovery-service/v3/search/contents'
                    params = {
                                'profileId': 'anonymous',
                                'sharedProfile': True,
                                'includeDetails': True,
                                'replayOptedInTime': 0,
                                'clientType': 209,
                                'searchTerm': localtitle,
                                'queryLanguage': 'pl',
                                'startResults': 0,
                                'maxResults': 100,
                                'includeNotEntitled': True,
                                'maxRes': '4K',
                                'mergingOn': True,
                                'includeExternalProvider': 'ALL',
                                'goPlayableOnly': False
                            }
                    results = jget(search, params=params).get('results', {})

                    for result in results:
                        crid = re.search('crid:(.+)', result['id']).group(0)
                        if t_crid.split('~')[-1] == crid.split('~')[-1]:

                            params = {
                                'language': 'pl',
                                'profileId': 'anonymous',
                                'maxRes': 'HD',
                                'filterOnDemand': 'svod'
                            }
                            api = jget(f'{api_url}/vod-service/v2/detailscreen/{crid}', params=params)
                            source = [append(i.get('id', {})) for i in api.get('instances', [])]
                        else: #  serial
                            params = {
                                'language': 'pl',
                                'profileId': 'anonymous',
                                'maxRes': 'HD',
                                'filterOnDemand': 'svod'
                            }
                            api = jget(f'{api_url}/vod-service/v2/detailscreen/{t_crid}', params=params)
                            source = [append(i.get('id', {})) for i in api.get('instances', [])]

            except Exception as e:
                #fflog("external viaplay exception:", #fflogINFO)
                #fflog(e, #fflogINFO)
                fflog_exc(1)
                pass


        if polsatbox_enabled:
            # fflog('polsatbox_enabled')
            try:
                ipl = [o for o in offers if isinstance(o,dict) and o["package_short_name"] in polsatbox]
                if ipl:
                    polsat_id = ipl[0]["urls"]["standard_web"]
                    polsat_id = polsat_id.rstrip("/").split("/")[-1]
                    # TODO: sprawdzenie pakietu we wtyczce

                    streams.append(("polsat box", polsatbox_pattern + polsat_id + "%7Cnull"))
            except Exception as e:
                #fflog("external polsatbox exception:", #fflogINFO)
                #fflog(e, #fflogINFO)
                fflog_exc(1)
                pass


        if iplayer_enabled:
            fflog('iplayer_enabled')
            try:
                bbc = [o for o in offers if isinstance(o,dict) and o["package_short_name"] in iplayer]
                if bbc:
                    iplayer_id = bbc[0]["urls"]["standard_web"]
                    streams.append(("bbc iplayer", iplayer_pattern % iplayer_id))
            except Exception as e:
                #fflog("external iplayer exception:", #fflogINFO)
                #fflog(e, #fflogINFO)
                fflog_exc(1)
                pass


        if curstream_enabled:
            # fflog('curstream_enabled')
            try:
                cts = [o for o in offers if isinstance(o,dict) and o["package_short_name"] in curstream]
                if cts:
                    cts_id = cts[0]["urls"]["standard_web"]
                    cts_id = cts_id.rstrip("/").split("/")[-1]
                    streams.append(("curiosity stream", curstream_pattern + cts_id))
            except Exception as e:
                #fflog("external curstream exception:", #fflogINFO)
                #fflog(e, #fflogINFO)
                fflog_exc(1)
                pass


        if hulu_enabled:
            fflog('hulu_enabled')
            try:
                hlu = [o for o in offers if isinstance(o,dict) and o["package_short_name"] in hulu]
                if hlu:
                    hulu_id = hlu[0]["urls"]["standard_web"]
                    hulu_id = hulu_id.rstrip("/").split("/")[-1]
                    streams.append(("hulu", hulu_pattern + hulu_id))
            except Exception as e:
                #fflog("external hulu exception:", #fflogINFO)
                #fflog(e, #fflogINFO)
                fflog_exc(1)
                pass


        if paramount_enabled:
            # fflog('paramount_enabled')
            try:
                pmp = [o for o in offers if isinstance(o,dict) and o["package_short_name"] in paramount]
                if pmp:
                    pmp_url = pmp[0]["urls"]["standard_web"]
                    pmp_id = (pmp_url.split("?")[0].split("/")[-1] if content == "movie" else
                    re.findall("/video/(.+?)/", pmp_url)[0])
                    streams.append(("paramount+", paramount_pattern + pmp_id))
            except Exception as e:
                #fflog("external paramount exception:", #fflogINFO)
                #fflog(e, #fflogINFO)
                fflog_exc(1)
                pass


        # fflog(f'{len(streams)=} {streams=}')
        fflog(f'przekazano źródeł: {len(streams)}  (tylko z aktywnych wtyczek)')
        if streams:
            default = {"quality": "1080p", "language": "pl", "direct": True, "debridonly": False, "external": True}
            for s in streams:
                if isinstance(s, Mapping):
                    ss = s
                else:
                    ss = {"source": s[0], "url": s[1]}
                # fflog(f'{s[0]=}')
                sources.append({**default, **ss})
            return sources


    def resolve(self, url):
        return url


    def is_match(self, name, title, hdlr=None, aliases=None):
        try:
            name = name.lower()
            t = re.sub(r"(\+|\.|\(|\[|\s)(\d{4}|s\d+e\d+|s\d+|3d)(\.|\)|]|\s|)(.+|)", "", name)
            t = cleantitle.get(t)
            titles = [cleantitle.get(title)]

            if aliases:
                if not isinstance(aliases, list):
                    from ast import literal_eval

                    aliases = literal_eval(aliases)
                try:
                    titles.extend([cleantitle.get(i["title"]) for i in aliases])
                except:
                    pass

            if hdlr:
                return t in titles and hdlr.lower() in name
            return t in titles
        except Exception:
            #fflog("error from is_match exc", 1)
            return True


    def normalize(self, title):
        import unicodedata

        try:
            return str(
                "".join(c for c in unicodedata.normalize("NFKD", title) if unicodedata.category(c) != "Mn")).replace(
                "ł", "l")
        except:
            title = (
                title.replace("ą", "a").replace("ę", "e").replace("ć", "c").replace("ź", "z").replace("ż", "z").replace(
                    "ó", "o").replace("ł", "l").replace("ń", "n").replace("ś", "s"))
            return title


    def netflix_ep_id(self, show_id, season, episode):
        netflix_search_pattern = "http://unogs.com/api/title/episodes?netflixid=%s"

        user_id = {'user_name': '1683364584.456'}
        response = self.session.post('http://unogs.com/api/user', data=user_id)

        token = response.json()['token']['access_token']

        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Authorization': f'Bearer {token}',
            'Connection': 'keep-alive',
            'REFERRER': 'http://unogs.com',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

        r = self.session.get(netflix_search_pattern % show_id, headers=headers, timeout=5)
        r.raise_for_status()
        r.encoding = "utf-8"
        apianswer = r.json()
        apifetch = [s["episodes"] for s in apianswer if s["season"] == int(season)][0]
        ep_id = str([e["epid"] for e in apifetch if e["epnum"] == int(episode)][0])
        seas_id = str([e["seasid"] for e in apifetch if e["seasnum"] == int(season)][0])

        return ep_id, seas_id

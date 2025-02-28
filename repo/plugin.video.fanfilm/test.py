import os
import sys
import threading
import time

sys.path.append(os.path.join(os.path.curdir, "lib"))
from resources.lib import sources as openscrapers

hosts = ['example.com', 'adultswim.com', 'amazon.com', 'ani-stream.com', 'aparat.cam', 'wolfstream.tv', 'brupload.net',
         'castamp.com', 'm.cda.pl', 'cda.pl', 'www.cda.pl', 'ebd.cda.pl', 'chillx.top', 'clicknupload.to',
         'clicknupload.cc', 'clicknupload.co', 'clicknupload.com', 'clicknupload.me', 'clicknupload.link',
         'clicknupload.org', 'clicknupload.club', 'cloud.mail.ru', 'cos.tv', 'dailymotion.com', 'dai.ly', 'daxab.com',
         'dembed2.com', 'asianplay.net', 'asianplay.pro', 'asianstream.pro', 'asianhdplay.net', 'dood.watch',
         'doodstream.com', 'dood.to', 'dood.so', 'dood.cx', 'dood.la', 'dood.ws', 'dood.sh', 'doodstream.co', 'dood.pm',
         'dood.wf', 'dood.re', 'facebook.com', 'fastdrive.io', 'fastplay.sx', 'fastplay.cc', 'fastplay.to',
         'fembed.com', 'anime789.com', '24hd.club', 'vcdn.io', 'sharinglink.club', 'votrefiles.club', 'femoload.xyz',
         'feurl.com', 'dailyplanet.pw', 'jplayer.net', 'xstreamcdn.com', 'gcloud.live', 'vcdnplay.com', 'vidohd.com',
         'vidsource.me', 'votrefile.xyz', 'zidiplay.com', 'fcdn.stream', 'mediashore.org', 'there.to', 'femax20.com',
         'sexhd.co', 'viplayer.cc', 'mrdhan.com', 'embedsito.com', 'dutrag.com', 'youvideos.ru', 'streamm4u.club',
         'moviepl.xyz', 'asianclub.tv', 'vidcloud.fun', 'fplayer.info', 'diasfem.com', 'fembad.org', 'moviemaniac.org',
         'albavido.xyz', 'ncdnstm.com', 'fembed-hd.com', 'superplayxyz.club', 'cinegrabber.com', 'ndrama.xyz',
         'javstream.top', 'javpoll.com', 'suzihaza.com', 'fembed.net', 'ezsubz.com', 'reeoov.tube', 'diampokusy.com',
         'filmvi.xyz', 'vidsrc.xyz', 'i18n.pw', 'vanfem.com', 'fembed9hd.com', 'votrefilms.xyz', 'watchjavnow.xyz',
         'ncdnstm.xyz', 'albavide.xyz', 'kitabmarkaz.xyz', 'filepup.net', 'files.fm', 'file.fm', 'flashx.tv',
         'flashx.to', 'flashx.sx', 'flashx.bz', 'flashx.cc', 'gamovideo.com', 'gofile.io', 'goload.io', 'goload.pro',
         'gogohd.net', 'streamani.net', 'gogo-play.net', 'vidstreaming.io', 'gogohd.pro', 'googlevideo.com',
         'googleusercontent.com', 'get.google.com', 'plus.google.com', 'googledrive.com', 'drive.google.com',
         'docs.google.com', 'youtube.googleapis.com', 'bp.blogspot.com', 'blogger.com', 'hdvid.tv', 'hdvid.fun',
         'vidhdthe.online', 'hdvid.website', 'hdthevid.online', 'hexupload.net', 'holavid.com', 'indavideo.hu',
         'k2s.cc', 'publish2.me', 'tezfiles.com', 'lbry.tv', 'lbry.science', 'odysee.com', 'madiator.com',
         'letsupload.io', 'letsupload.org', 'stream.lewd.host', 'mail.ru', 'my.mail.ru', 'm.my.mail.ru',
         'videoapi.my.mail.ru', 'api.video.mail.ru', 'megaup.net', 'megogo.net', 'megogo.ru', 'mixdrop.co',
         'mixdrop.to', 'mixdrop.sx', 'mixdrop.bz', 'mixdrop.ch', 'mixdrp.co', 'mixdrp.to', 'mp4upload.com',
         'mvidoo.com', 'neohd.xyz', 'ninjahd.one', 'ok.ru', 'odnoklassniki.ru', 'pandafiles.com', 'peertube.tv',
         'peertube.co.uk', 'peertube.uno', 'pixeldrain.com', 'pkspeed.net', 'playhd.one', 'playdrive.xyz', 'prohd.one',
         'playwire.com', 'racaty.net', 'racaty.io', 'rovideo.net', 'rumble.com', 'rutube.ru', 'videos.sapo.pt',
         'saruch.co', 'sibnet.ru', 'streamable.com', 'streamingcommunity.xyz', 'streamingcommunity.one',
         'streamingcommunity.vip', 'streamingcommunity.work', 'streamingcommunity.name', 'streamingcommunity.video',
         'streamingcommunity.live', 'streamingcommunity.tv', 'streamingcommunity.space', 'streamingcommunity.art',
         'streamingcommunity.fun', 'streamingcommunity.website', 'streamingcommunity.host', 'streamingcommunity.site',
         'streamingcommunity.bond', 'streamingcommunity.icu', 'streamingcommunity.bar', 'streamingcommunity.top',
         'streamingcommunity.cc', 'streamingcommunity.monster', 'streamingcommunity.press',
         'streamingcommunity.business', 'streamingcommunity.org', 'streamingcommunity.best',
         'streamingcommunity.agency', 'streamingcommunity.blog', 'streamingcommunity.tech', 'streamingcommunity.golf',
         'streamingcommunity.city', 'streamingcommunity.help', 'streamlare.com', 'slmaxed.com', 'sltube.org',
         'slwatch.co', 'streamrapid.ru', 'rabbitstream.net', 'mzzcloud.life', 'dokicloud.one', 'streamruby.com',
         'sruby.xyz', 'sbembed.com', 'sbembed1.com', 'sbplay.org', 'sbvideo.net', 'streamsb.net', 'sbplay.one',
         'cloudemb.com', 'playersb.com', 'tubesb.com', 'sbplay1.com', 'embedsb.com', 'watchsb.com', 'sbplay2.com',
         'japopav.tv', 'viewsb.com', 'sbplay2.xyz', 'sbfast.com', 'sbfull.com', 'javplaya.com', 'ssbstream.net',
         'p1ayerjavseen.com', 'sbthe.com', 'vidmovie.xyz', 'sbspeed.com', 'streamsss.net', 'sblanh.com', 'tvmshow.com',
         'sbanh.com', 'streamovies.xyz', 'embedtv.fun', 'sblongvu.com', 'arslanrocky.xyz', 'sbchill.com',
         'streamtape.com', 'strtape.cloud', 'streamtape.net', 'streamta.pe', 'streamtape.site', 'strcloud.link',
         'strtpe.link', 'streamtape.cc', 'scloud.online', 'stape.fun', 'streamadblockplus.com', 'shavetape.cash',
         'streamtape.to', 'streamvid.co', 'streamvid.net', 'streamz.cc', 'streamz.vg', 'streamzz.to', 'streamz.ws',
         'superembeds.com', 'supervideo.tv', 'truhd.xyz', 'tubeload.co', 'redload.co', 'tubitv.com', 'tudou.com',
         'tusfiles.net', 'tusfiles.com', 'tvlogy.to', 'uploadbaz.me', 'uploadever.com', 'uploadever.in',
         'uploadflix.org', 'uploadingsite.com', 'uploadraja.com', 'upstream.to', 'uptobox.com', 'uptostream.com',
         'upvideo.to', 'videoloca.xyz', 'tnaket.xyz', 'makaveli.xyz', 'highload.to', 'embedo.co', 'userload.co',
         'veoh.com', 'vidbom.com', 'vidbem.com', 'vidbm.com', 'vedpom.com', 'vedbom.com', 'vedbom.org', 'vedbam.xyz',
         'vadbom.com', 'vidbam.org', 'vadbam.com', 'myviid.com', 'myviid.net', 'myvid.com', 'vidshare.com',
         'vedsharr.com', 'vedshar.com', 'vedshare.com', 'vadshar.com', 'vidshar.org', 'vidcloud9.com', 'vidnode.net',
         'vidnext.net', 'vidembed.net', 'vidembed.cc', 'vidembed.io', 'vidembed.me', 'membed.net', 'membed1.com',
         'videa.hu', 'videakid.hu', 'videobin.co', 'videoseyred.in', 'videowood.tv', 'byzoo.org', 'playpanda.net',
         'videozoo.me', 'videowing.me', 'easyvideo.me', 'play44.net', 'playbb.me', 'video44.net', 'vidmojo.net',
         'vidflare.net', 'embedojo.com', 'vidstore.me', 'vimeo.com', 'player.vimeo.com', 'vipss.club', 'vk.com',
         'videoslala.com', 'videoslala.net', 'voe.sx', 'voe-unblock.com', 'voe-unblock.net', 'voeunblock.com',
         'voeunbl0ck.com', 'voeunblck.com', 'voeunblk.com', 'voe-un-block.com', 'voeun-block.net', 'un-block-voe.net',
         'v-o-e-unblock.com', 'audaciousdefaulthouse.com', 'launchreliantcleaverriver.com',
         'reputationsheriffkennethsand.com', 'fittingcentermondaysunday.com', 'housecardsummerbutton.com',
         'fraudclatterflyingcar.com', 'bigclatterhomesguideservice.com', 'uptodatefinishconferenceroom.com',
         'realfinanceblogcenter.com', 'tinycat-voe-fashion.com', '20demidistance9elongations.com',
         'telyn610zoanthropy.com', 'toxitabellaeatrebates306.com', 'greaseball6eventual20.com', 'voeunblock1.com',
         'voeunblock2.com', 'voeunblock3.com', 'voeunblock4.com', 'voeunblock5.com', 'voeunblock6.com',
         'voeunblock7.com', 'voeunblock8.com', 'voeunblock9.com', 'voeunblock10.com', 'vshare.eu', 'yourupload.com',
         'yucache.net', 'youtube.com', 'youtu.be', 'youtube-nocookie.com', 'zplayer.live', 'aliez.me', 'anonfiles.com',
         'bayfiles.com', 'avideo.host', 'banned.video', 'freeworldnews.tv', 'electionnight.news', 'futurenews.news',
         'battleplan.news', 'theinfowar.tv', 'bitchute.com', 'brighteon.com', 'chromecast.video', 'cloudb.me',
         'cloudb2.me', 'gamatotv.site', 'cloudb.site', 'gmtvdb.com', 'gmtdb.me', 'streamclood.com', 'gmtv1.com',
         'cloudvideo.tv', 'downace.com', 'dropload.io', 'entervideo.net', 'eplayvid.com', 'eplayvid.net', 'filemoon.sx',
         'filemoon.to', 'filerio.in', 'files.im', 'gomoplayer.com', 'tunestream.net', 'xvideosharing.com',
         'goostream.net', 'hxfile.co', 'itemfix.com', 'justok.click', 'liivideo.com', 'liiivideo.com', 'linkbox.to',
         'sharezweb.com', 'mightyupload.com', 'mycloud.to', 'mcloud.to', 'vizcloud.digital', 'vizcloud.cloud',
         'myfeminist.com', 'myupload.co', 'newtube.app', 'send.cm', 'sendit.cloud', 'sendvid.com', 'solidfiles.com',
         'speedostream.com', 'speedostream.nl', 'streamhide.to', 'streamhub.to', 'streamoupload.com',
         'streamoupload.xyz', 'superitu.com', 'turboviplay.com', 'emturbovid.com', 'uqload.com', 'userscloud.com',
         'vidbob.com', 'vidcloud.co', 'vidcloud.pro', 'vidcloud.is', 'videoapne.co', 'videooo.news', 'vidfast.co',
         'vidmoly.me', 'vidmoly.to', 'vidmoly.net', 'vidmx.xyz', 'vembx.one', 'vido.lol', 'vidorg.net', 'vidpiz.xyz',
         'vidoza.net', 'vidoza.co', 'vidzstore.com', 'vkprime.com', 'vkspeed.com', 'speedwatch.us', 'voxzer.org',
         'vtube.to', 'vtplay.net', 'vudeo.net', 'vudeo.io', 'vupload.com', 'watching.vn', 'disk.yandex.ru',
         'disk.yandex.com', 'yadi.sk', 'youdbox.com', 'youdbox.net', 'youdbox.org', 'yodbox.com', 'zillastream.com']

# Set test_mode to 1 for automatic testing of all providers
# Set test_mode to 0 to select which provider to test
test_mode = 1

# Set test_mode to 'movie' to test movie scraping
# Set test_mode to 'episode' to test episode scraping
test_type = "episode"

# Test information
movie_info = {"title": "Pulp Fiction", "imdb": "tt1375666", "aliases": [], "localtitle": "Pulp Fiction",
              "year": "1994", }

# TODO Fill out showinfo and episode info for tests
show_info = {""}


def worker_thread(provider_name, provider_source):
    start_time = time.time()
    try:
        # Confirm Provider contains the movie function
        if not getattr(provider_source, test_type, False):
            return

        if not getattr(provider_source, "unit_test", False):

            # Run movie Call
            url = provider_source.movie(movie_info["imdb"], movie_info["title"], movie_info["localtitle"],
                                        movie_info["aliases"], movie_info["year"], )
            if url is None:
                failed_providers.append((provider_name, "Movie Call Returned None"))

            # Run source call
            url = provider_source.sources(url, hosts, [])
            if url is None:
                failed_providers.append((provider_name, "Sources Call Returned None"))

            # Gather time analytics
            runtime = time.time() - start_time

            passed_providers.append((provider_name, url, runtime))
        else:
            # Provider has unit test entry point, run provider with it
            try:
                unit_test = provider_source.unit_test("movie", hosts)
            except Exception as e:
                failed_providers.append((provider_name, e))
                return

            if unit_test is None:
                failed_providers.append((provider_name, "Unit Test Returned None"))
                return

            runtime = time.time() - start_time

            passed_providers.append((provider_name, unit_test, runtime))

    except Exception as e:
        # Appending issue provider to failed providers
        failed_providers.append((provider_name, e))


provider_list = openscrapers.sources()
failed_providers = []
passed_providers = []
workers = []

if __name__ == "__main__":

    total_runtime = time.time()

    print("Running Unit Tests. Please Wait...")

    # Build and run threads
    if test_mode == 1:
        for provider in provider_list:
            workers.append(threading.Thread(target=worker_thread, args=(provider[0], provider[1])))

        for worker in workers:
            worker.start()

        for worker in workers:
            worker.join()

    else:
        print("Please Select a provider:")
        for idx, provider in enumerate(provider_list):
            print("{}) {}".format(idx, provider[0]))

        while True:
            try:
                choice = int(input())
                provider = provider_list[choice]
                break
            except ValueError:
                print("Please enter a number")
            except IndexError:
                print("You've entered and incorrect selection")

        worker_thread(provider[0], provider[1])

    total_runtime = time.time() - total_runtime

    # Print any failures to the console
    print(" ")
    print("Provider Failures:")
    print("##################")
    if len(failed_providers) == 0:
        print("None")
        print(" ")
    else:
        for provider in failed_providers:
            print("Provider Name: %s" % provider[0].upper())
            print("Exception: %s" % provider[1])
            print(" ")

    if test_mode == 1:
        all_sources = [source for sources in passed_providers if sources[1] is not None for source in sources[1] if
                       source is not None]
    else:
        all_sources = passed_providers[0][1]
        if all_sources is None:
            all_sources = []

    # TODO Expand analytical information
    print("Analytical Data:")
    print("################")
    if test_mode == 1:
        print("Total Runtime: %s" % total_runtime)
        print("Total Passed Providers: %s" % len(passed_providers))
        print("Total Failed Providers: %s" % len(failed_providers))
        print("Skipped Providers: %s" % (len(provider_list) - (len(passed_providers) + len(failed_providers))))
        print("Total No. Sources: %s" % len(all_sources))
    else:
        print("Total No. Sources: %s" % len(all_sources))

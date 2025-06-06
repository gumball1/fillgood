# -*- coding: UTF-8 -*-
import sys
import urllib

from kover import autoinstall  # noqa: F401
import xbmcgui
import xbmcplugin
try:
    from xbmcgui import ListItem
except:
    from xbmcplugin import ListItem # K19 fix

from ptw.debug import log_exception

try:
    import urllib.parse as urllib
except:
    pass

PY2 = sys.version_info[0] == 2
if PY2:
    from urlparse import parse_qs
else:
    from urllib.parse import parse_qs


def addDir(
    name,
    url,
    mode="",
    icon="",
    thumb="",
    fanart="",
    poster="",
    banner="",
    clearart="",
    clearlogo="",
    genre="",
    year=0,
    rating=0,
    dateadded="",
    plot="",
    code="",
    label2Mask=None,
    isFolder=True,
    total=1,
):
    u = (
        sys.argv[0]
        + "?url="
        + urllib.quote_plus(url)
        + "&mode="
        + str(mode)
        + "&name="
        + urllib.quote_plus(name)
    )
    liz = ListItem(name)
    liz.setArt(
        {
            "thumb": thumb,
            "icon": icon,
            "fanart": fanart,
            "poster": poster,
            "banner": banner,
            "clearart": clearart,
            "clearlogo": clearlogo,
        }
    )
    vtag = liz.getVideoInfoTag()
    vtag.setTitle(name)
    vtag.setGenres([genre])
    vtag.setYear(int(year))
    vtag.setRating(int(rating))
    vtag.setDateAdded(dateadded)
    vtag.setPlot(plot)
    vtag.setProductionCode(code)
    vtag.setMediaType("movie")
    xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]),
        url=u,
        listitem=liz,
        isFolder=isFolder,
        totalItems=total,
    )
    xbmcplugin.addSortMethod(
        handle=int(sys.argv[1]),
        sortMethod=xbmcplugin.SORT_METHOD_NONE,
        label2Mask=label2Mask,
    )


def addLink(
    name,
    url,
    mode="",
    icon="",
    thumb="",
    fanart="",
    poster="",
    banner="",
    clearart="",
    clearlogo="",
    genre="",
    year=0,
    rating=0,
    dateadded="",
    plot="",
    code="",
    label2Mask=None,
    isFolder=False,
    total=1,
    type="Video",
):
    url = (
        sys.argv[0]
        + "?url="
        + urllib.quote_plus(url)
        + "&mode="
        + str(mode)
        + "&name="
        + urllib.quote_plus(name)
    )

    list_item = ListItem(label=name)
    # Set additional info for the list item.
    # 'mediatype' is needed for skin to display info for this ListItem correctly.
    vtag = list_item.getVideoInfoTag()
    vtag.setTitle(name)
    vtag.setGenres([genre])
    vtag.setYear(int(year))
    vtag.setRating(int(rating))
    vtag.setDateAdded(dateadded)
    vtag.setPlot(plot)
    vtag.setProductionCode(code)
    vtag.setMediaType("movie")

    list_item.setProperty("IsPlayable", "true")

    list_item.setArt(
        {
            "thumb": thumb,
            "icon": icon,
            "fanart": fanart,
            "poster": poster,
            "banner": banner,
            "clearart": clearart,
            "clearlogo": clearlogo,
        }
    )
    xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]),
        url=url,
        listitem=list_item,
        isFolder=isFolder,
        totalItems=total,
    )
    xbmcplugin.addSortMethod(
        handle=int(sys.argv[1]),
        sortMethod=xbmcplugin.SORT_METHOD_NONE,
        label2Mask=label2Mask,
    )


def get_params():
    paramstring = sys.argv[2]
    if paramstring.startswith("?"):
        paramstring = paramstring[1:]
    return dict((k, vv[0]) for k, vv in parse_qs(paramstring).items())


def PlayMedia(link, direct=False):
    pDialog = xbmcgui.DialogProgress()
    try:
        pDialog.create("Odtwarzanie", "Odpalanie linku...")
        if "rtmp" in link:
            url = link
        elif direct:
            url = link
        else:
            import resolveurl

            url = resolveurl.resolve(link)
        if url is False:
            raise ValueError("Nie udało się wyciągnąć linku")
        pDialog.close()
        li = ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
    except Exception as e:
        pDialog.close()
        xbmcgui.Dialog().ok("Error", "Błąd odpalania linku! %s" % e)
        log_exception()
        sys.exit()


def SourceSelect(items):
    if len(items) > 0:
        select = xbmcgui.Dialog().select("Wybór źródła", [x.get("name") for x in items])
        if select > -1:
            link = items[select].get("href")
            PlayMedia(link)
        else:
            sys.exit()
    else:
        xbmcgui.Dialog().ok("[COLOR red]Problem[/COLOR]", "Brak linków")
        sys.exit()

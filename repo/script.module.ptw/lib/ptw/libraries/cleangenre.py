# -*- coding: utf-8 -*-

"""
    FanFilm Add-on

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


def lang(i, lang):
    if lang == "bg":
        i = i.replace("Action", "\u0415\u043a\u0448\u044a\u043d")
        i = i.replace(
            "Adventure",
            "\u041f\u0440\u0438\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435",
        )
        i = i.replace("Animation", "\u0410\u043d\u0438\u043c\u0430\u0446\u0438\u044f")
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u041a\u043e\u043c\u0435\u0434\u0438\u044f")
        i = i.replace(
            "Crime", "\u041a\u0440\u0438\u043c\u0438\u043d\u0430\u043b\u0435\u043d"
        )
        i = i.replace(
            "Documentary",
            "\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u043b\u0435\u043d",
        )
        i = i.replace("Drama", "\u0414\u0440\u0430\u043c\u0430")
        i = i.replace("Family", "\u0421\u0435\u043c\u0435\u0435\u043d")
        i = i.replace("Fantasy", "\u0424\u0435\u043d\u0442\u044a\u0437\u0438")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace(
            "History",
            "\u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438",
        )
        i = i.replace("Horror", "\u0423\u0436\u0430\u0441")
        i = i.replace("Music ", "\u041c\u0443\u0437\u0438\u043a\u0430")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u041c\u0438\u0441\u0442\u0435\u0440\u0438\u044f")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0420\u043e\u043c\u0430\u043d\u0441")
        i = i.replace(
            "Science Fiction",
            "\u041d\u0430\u0443\u0447\u043d\u0430\u002d\u0444\u0430\u043d\u0442\u0430\u0441\u0442\u0438\u043a\u0430",
        )
        i = i.replace(
            "Sci-Fi",
            "\u041d\u0430\u0443\u0447\u043d\u0430\u002d\u0444\u0430\u043d\u0442\u0430\u0441\u0442\u0438\u043a\u0430",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0422\u0440\u0438\u043b\u044a\u0440")
        i = i.replace("War", "\u0412\u043e\u0435\u043d\u0435\u043d")
        i = i.replace("Western", "\u0423\u0435\u0441\u0442\u044a\u0440\u043d")

    elif lang == "cs":
        i = i.replace("Action", "\u0041\u006b\u010d\u006e\u00ed")
        i = i.replace(
            "Adventure",
            "\u0044\u006f\u0062\u0072\u006f\u0064\u0072\u0075\u017e\u006e\u00fd",
        )
        i = i.replace(
            "Animation", "\u0041\u006e\u0069\u006d\u006f\u0076\u0061\u006e\u00fd"
        )
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u004b\u006f\u006d\u0065\u0064\u0069\u0065")
        i = i.replace("Crime", "\u004b\u0072\u0069\u006d\u0069")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u006b\u0075\u006d\u0065\u006e\u0074\u00e1\u0072\u006e\u00ed",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u0061")
        i = i.replace("Family", "\u0052\u006f\u0064\u0069\u006e\u006e\u00fd")
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0079")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace(
            "History", "\u0048\u0069\u0073\u0074\u006f\u0072\u0069\u0063\u006b\u00fd"
        )
        i = i.replace("Horror", "\u0048\u006f\u0072\u006f\u0072")
        i = i.replace("Music ", "\u0048\u0075\u0064\u0065\u0062\u006e\u00ed")
        i = i.replace("Musical", "Musical")
        i = i.replace(
            "Mystery",
            "\u004d\u0079\u0073\u0074\u0065\u0072\u0069\u00f3\u007a\u006e\u00ed",
        )
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace(
            "Romance", "\u0052\u006f\u006d\u0061\u006e\u0074\u0069\u0063\u006b\u00fd"
        )
        i = i.replace(
            "Science Fiction",
            "\u0056\u011b\u0064\u0065\u0063\u006b\u006f\u0066\u0061\u006e\u0074\u0061\u0073\u0074\u0069\u0063\u006b\u00fd",
        )
        i = i.replace(
            "Sci-Fi",
            "\u0056\u011b\u0064\u0065\u0063\u006b\u006f\u0066\u0061\u006e\u0074\u0061\u0073\u0074\u0069\u0063\u006b\u00fd",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace("War", "\u0056\u00e1\u006c\u0065\u010d\u006e\u00fd")
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "da":
        i = i.replace("Action", "\u0041\u0063\u0074\u0069\u006f\u006e")
        i = i.replace("Adventure", "\u0045\u0076\u0065\u006e\u0074\u0079\u0072")
        i = i.replace(
            "Animation", "\u0041\u006e\u0069\u006d\u0061\u0074\u0069\u006f\u006e"
        )
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u004b\u006f\u006d\u0065\u0064\u0069\u0065")
        i = i.replace(
            "Crime",
            "\u004b\u0072\u0069\u006d\u0069\u006e\u0061\u006c\u0069\u0074\u0065\u0074",
        )
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u0063\u0075\u006d\u0065\u006e\u0074\u0061\u0072\u0079",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u0061")
        i = i.replace("Family", "\u0046\u0061\u006d\u0069\u006c\u0069\u0065")
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0079")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u0048\u0069\u0073\u0074\u006f\u0072\u0069\u0065 ")
        i = i.replace("Horror", "\u0047\u0079\u0073\u0065\u0072")
        i = i.replace("Music ", "\u004d\u0075\u0073\u0069\u006b")
        i = i.replace("Musical", "Musical")
        i = i.replace(
            "Mystery", "\u004d\u0079\u0073\u0074\u0065\u0072\u0069\u0075\u006d"
        )
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0052\u006f\u006d\u0061\u006e\u0074\u0069\u006b")
        i = i.replace("Science Fiction", "\u0053\u0063\u0069\u002d\u0066\u0069")
        i = i.replace("Sci-Fi", "\u0053\u0063\u0069\u002d\u0066\u0069")
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace("War", "\u004b\u0072\u0069\u0067")
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "de":
        i = i.replace("Action", "\u0041\u0063\u0074\u0069\u006f\u006e")
        i = i.replace(
            "Adventure", "\u0041\u0062\u0065\u006e\u0074\u0065\u0075\u0065\u0072"
        )
        i = i.replace(
            "Animation", "\u0041\u006e\u0069\u006d\u0061\u0074\u0069\u006f\u006e"
        )
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u004b\u006f\u006d\u00f6\u0064\u0069\u0065")
        i = i.replace("Crime", "\u004b\u0072\u0069\u006d\u0069")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u006b\u0075\u006d\u0065\u006e\u0074\u0061\u0072\u0066\u0069\u006c\u006d",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u0061")
        i = i.replace("Family", "\u0046\u0061\u006d\u0069\u006c\u0069\u0065")
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0079")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u0048\u0069\u0073\u0074\u006f\u0072\u0069\u0065")
        i = i.replace("Horror", "\u0048\u006f\u0072\u0072\u006f\u0072")
        i = i.replace("Music ", "\u004d\u0075\u0073\u0069\u006b")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u004d\u0079\u0073\u0074\u0065\u0072\u0079")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace(
            "Romance", "\u004c\u006f\u0076\u0065\u0073\u0074\u006f\u0072\u0079"
        )
        i = i.replace(
            "Science Fiction",
            "\u0053\u0063\u0069\u0065\u006e\u0063\u0065 \u0046\u0069\u0063\u0074\u0069\u006f\u006e",
        )
        i = i.replace(
            "Sci-Fi",
            "\u0053\u0063\u0069\u0065\u006e\u0063\u0065 \u0046\u0069\u0063\u0074\u0069\u006f\u006e",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace(
            "War", "\u004b\u0072\u0069\u0065\u0067\u0073\u0066\u0069\u006c\u006d"
        )
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "el":
        i = i.replace("Action", "\u0394\u03c1\u03ac\u03c3\u03b7")
        i = i.replace(
            "Adventure", "\u03a0\u03b5\u03c1\u03b9\u03c0\u03ad\u03c4\u03b5\u03b9\u03b1"
        )
        i = i.replace(
            "Animation",
            "\u039a\u03b9\u03bd\u03bf\u03cd\u03bc\u03b5\u03bd\u03b1 \u03a3\u03c7\u03ad\u03b4\u03b9\u03b1",
        )
        i = i.replace("Anime", "Anime")
        i = i.replace(
            "Biography", "\u0392\u03b9\u03bf\u03b3\u03c1\u03b1\u03c6\u03b9\u03ba\u03ae"
        )
        i = i.replace("Comedy", "\u039a\u03c9\u03bc\u03c9\u03b4\u03af\u03b1")
        i = i.replace(
            "Crime", "\u0391\u03c3\u03c4\u03c5\u03bd\u03bf\u03bc\u03b9\u03ba\u03ae"
        )
        i = i.replace(
            "Documentary",
            "\u039d\u03c4\u03bf\u03ba\u03c5\u03bc\u03b1\u03bd\u03c4\u03ad\u03c1",
        )
        i = i.replace("Drama", "\u0394\u03c1\u03ac\u03bc\u03b1")
        i = i.replace(
            "Family",
            "\u039f\u03b9\u03ba\u03bf\u03b3\u03b5\u03bd\u03b5\u03b9\u03b1\u03ba\u03ae",
        )
        i = i.replace(
            "Fantasy", "\u03a6\u03b1\u03bd\u03c4\u03b1\u03c3\u03af\u03b1\u03c2"
        )
        i = i.replace(
            "Game-Show",
            "\u03a4\u03b7\u03bb\u03b5\u03c0\u03b1\u03b9\u03c7\u03bd\u03af\u03b4\u03b9",
        )
        i = i.replace("History", "\u0399\u03c3\u03c4\u03bf\u03c1\u03b9\u03ba\u03ae")
        i = i.replace("Horror", "\u03a4\u03c1\u03cc\u03bc\u03bf\u03c5")
        i = i.replace("Music ", "\u039c\u03bf\u03c5\u03c3\u03b9\u03ba\u03ae")
        i = i.replace("Musical", "Musical")
        i = i.replace(
            "Mystery", "\u039c\u03c5\u03c3\u03c4\u03b7\u03c1\u03af\u03bf\u03c5"
        )
        i = i.replace("News", "\u0395\u03b9\u03b4\u03ae\u03c3\u03b5\u03b9\u03c2")
        i = i.replace("Reality-TV", "\u03a1\u03b9\u03ac\u03bb\u03b9\u03c4\u03c5")
        i = i.replace(
            "Romance", "\u03a1\u03bf\u03bc\u03b1\u03bd\u03c4\u03b9\u03ba\u03ae"
        )
        i = i.replace(
            "Science Fiction",
            "\u0395\u03c0\u002e \u03a6\u03b1\u03bd\u03c4\u03b1\u03c3\u03af\u03b1\u03c2",
        )
        i = i.replace(
            "Sci-Fi",
            "\u0395\u03c0\u002e \u03a6\u03b1\u03bd\u03c4\u03b1\u03c3\u03af\u03b1\u03c2",
        )
        i = i.replace("Sport", "\u0391\u03b8\u03bb\u03b7\u03c4\u03b9\u03ba\u03ae")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0398\u03c1\u03af\u03bb\u03b5\u03c1")
        i = i.replace("War", "\u03a0\u03bf\u03bb\u03b5\u03bc\u03b9\u03ba\u03ae")
        i = i.replace(
            "Western", "\u0393\u03bf\u03c5\u03ad\u03c3\u03c4\u03b5\u03c1\u03bd"
        )

    elif lang == "es":
        i = i.replace("Action", "\u0041\u0063\u0063\u0069\u00f3\u006e")
        i = i.replace("Adventure", "\u0041\u0076\u0065\u006e\u0074\u0075\u0072\u0061")
        i = i.replace(
            "Animation", "\u0041\u006e\u0069\u006d\u0061\u0063\u0069\u00f3\u006e"
        )
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u0043\u006f\u006d\u0065\u0064\u0069\u0061")
        i = i.replace("Crime", "\u0043\u0072\u0069\u006d\u0065\u006e")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u0063\u0075\u006d\u0065\u006e\u0074\u0061\u006c",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u0061")
        i = i.replace("Family", "\u0046\u0061\u006d\u0069\u006c\u0069\u0061")
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u00ed\u0061")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u0048\u0069\u0073\u0074\u006f\u0072\u0069\u0061")
        i = i.replace("Horror", "\u0054\u0065\u0072\u0072\u006f\u0072")
        i = i.replace("Music ", "\u004d\u00fa\u0073\u0069\u0063\u0061")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u004d\u0069\u0073\u0074\u0065\u0072\u0069\u006f")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0052\u006f\u006d\u0061\u006e\u0063\u0065")
        i = i.replace(
            "Science Fiction",
            "\u0043\u0069\u0065\u006e\u0063\u0069\u0061 \u0066\u0069\u0063\u0063\u0069\u00f3\u006e",
        )
        i = i.replace(
            "Sci-Fi",
            "\u0043\u0069\u0065\u006e\u0063\u0069\u0061 \u0066\u0069\u0063\u0063\u0069\u00f3\u006e",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0053\u0075\u0073\u0070\u0065\u006e\u0073\u0065")
        i = i.replace("War", "\u0047\u0075\u0065\u0072\u0072\u0061")
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "fr":
        i = i.replace("Action", "\u0041\u0063\u0074\u0069\u006f\u006e")
        i = i.replace("Adventure", "\u0041\u0076\u0065\u006e\u0074\u0075\u0072\u0065")
        i = i.replace(
            "Animation", "\u0041\u006e\u0069\u006d\u0061\u0074\u0069\u006f\u006e"
        )
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u0043\u006f\u006d\u00e9\u0064\u0069\u0065")
        i = i.replace("Crime", "\u0043\u0072\u0069\u006d\u0065")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u0063\u0075\u006d\u0065\u006e\u0074\u0061\u0069\u0072\u0065",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u0065")
        i = i.replace("Family", "\u0046\u0061\u006d\u0069\u006c\u0069\u0061\u006c")
        i = i.replace(
            "Fantasy",
            "\u0046\u0061\u006e\u0074\u0061\u0073\u0074\u0069\u0071\u0075\u0065",
        )
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u0048\u0069\u0073\u0074\u006f\u0069\u0072\u0065")
        i = i.replace("Horror", "\u0048\u006f\u0072\u0072\u0065\u0075\u0072")
        i = i.replace("Music ", "\u004d\u0075\u0073\u0069\u0071\u0075\u0065")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u004d\u0079\u0073\u0074\u00e8\u0072\u0065")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0052\u006f\u006d\u0061\u006e\u0063\u0065")
        i = i.replace(
            "Science Fiction",
            "\u0053\u0063\u0069\u0065\u006e\u0063\u0065\u002d\u0046\u0069\u0063\u0074\u0069\u006f\u006e",
        )
        i = i.replace(
            "Sci-Fi",
            "\u0053\u0063\u0069\u0065\u006e\u0063\u0065\u002d\u0046\u0069\u0063\u0074\u0069\u006f\u006e",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace("War", "\u0047\u0075\u0065\u0072\u0072\u0065")
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "he":
        i = i.replace("Action", "\u05d0\u05e7\u05e9\u05df")
        i = i.replace("Adventure", "\u05d4\u05e8\u05e4\u05ea\u05e7\u05d0\u05d5\u05ea")
        i = i.replace("Animation", "\u05d0\u05e0\u05d9\u05de\u05e6\u05d9\u05d4")
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u05e7\u05d5\u05de\u05d3\u05d9\u05d4")
        i = i.replace("Crime", "\u05e4\u05e9\u05e2")
        i = i.replace(
            "Documentary", "\u05d3\u05d5\u05e7\u05d5\u05de\u05e0\u05d8\u05e8\u05d9"
        )
        i = i.replace("Drama", "\u05d3\u05e8\u05de\u05d4")
        i = i.replace("Family", "\u05de\u05e9\u05e4\u05d7\u05d4")
        i = i.replace("Fantasy", "\u05e4\u05e0\u05d8\u05d6\u05d9\u05d4")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u05d4\u05e1\u05d8\u05d5\u05e8\u05d9\u05d4")
        i = i.replace("Horror", "\u05d0\u05d9\u05de\u05d4")
        i = i.replace("Music ", "\u05de\u05d5\u05e1\u05d9\u05e7\u05d4")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u05de\u05e1\u05ea\u05d5\u05e8\u05d9\u05df")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u05e8\u05d5\u05de\u05e0\u05d8\u05d9")
        i = i.replace(
            "Science Fiction",
            "\u05de\u05d3\u05e2 \u05d1\u05d3\u05d9\u05d5\u05e0\u05d9",
        )
        i = i.replace(
            "Sci-Fi", "\u05de\u05d3\u05e2 \u05d1\u05d3\u05d9\u05d5\u05e0\u05d9"
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u05de\u05d5\u05ea\u05d7\u05df")
        i = i.replace("War", "\u05de\u05dc\u05d7\u05de\u05d4")
        i = i.replace("Western", "\u05de\u05e2\u05e8\u05d1\u05d5\u05df")

    elif lang == "hu":
        i = i.replace("Action", "\u0041\u006b\u0063\u0069\u00f3")
        i = i.replace("Adventure", "\u004b\u0061\u006c\u0061\u006e\u0064")
        i = i.replace(
            "Animation", "\u0041\u006e\u0069\u006d\u00e1\u0063\u0069\u00f3\u0073"
        )
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u0056\u00ed\u0067\u006a\u00e1\u0074\u00e9\u006b")
        i = i.replace("Crime", "\u0042\u0171\u006e\u00fc\u0067\u0079\u0069")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u006b\u0075\u006d\u0065\u006e\u0074\u0075\u006d",
        )
        i = i.replace("Drama", "\u0044\u0072\u00e1\u006d\u0061")
        i = i.replace("Family", "\u0043\u0073\u0061\u006c\u00e1\u0064\u0069")
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0079")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace(
            "History", "\u0054\u00f6\u0072\u0074\u00e9\u006e\u0065\u006c\u006d\u0069"
        )
        i = i.replace("Horror", "\u0048\u006f\u0072\u0072\u006f\u0072")
        i = i.replace("Music ", "\u005a\u0065\u006e\u0065\u0069")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u0052\u0065\u006a\u0074\u00e9\u006c\u0079")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace(
            "Romance", "\u0052\u006f\u006d\u0061\u006e\u0074\u0069\u006b\u0075\u0073"
        )
        i = i.replace("Science Fiction", "\u0053\u0063\u0069\u002d\u0046\u0069")
        i = i.replace("Sci-Fi", "\u0053\u0063\u0069\u002d\u0046\u0069")
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace("War", "\u0048\u00e1\u0062\u006f\u0072\u00fa\u0073")
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "it":
        i = i.replace("Action", "\u0041\u007a\u0069\u006f\u006e\u0065")
        i = i.replace(
            "Adventure", "\u0041\u0076\u0076\u0065\u006e\u0074\u0075\u0072\u0061"
        )
        i = i.replace(
            "Animation", "\u0041\u006e\u0069\u006d\u0061\u007a\u0069\u006f\u006e\u0065"
        )
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u0043\u006f\u006d\u006d\u0065\u0064\u0069\u0061")
        i = i.replace("Crime", "\u0043\u0072\u0069\u006d\u0065")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u0063\u0075\u006d\u0065\u006e\u0074\u0061\u0072\u0069\u006f",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u006d\u0061")
        i = i.replace("Family", "\u0046\u0061\u006d\u0069\u0067\u006c\u0069\u0061")
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0079")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u0053\u0074\u006f\u0072\u0069\u0061")
        i = i.replace("Horror", "\u0048\u006f\u0072\u0072\u006f\u0072")
        i = i.replace("Music ", "\u004d\u0075\u0073\u0069\u0063\u0061")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u004d\u0069\u0073\u0074\u0065\u0072\u006f")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0052\u006f\u006d\u0061\u006e\u0063\u0065")
        i = i.replace(
            "Science Fiction",
            "\u0046\u0061\u006e\u0074\u0061\u0073\u0063\u0069\u0065\u006e\u007a\u0061",
        )
        i = i.replace(
            "Sci-Fi",
            "\u0046\u0061\u006e\u0074\u0061\u0073\u0063\u0069\u0065\u006e\u007a\u0061",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace("War", "\u0047\u0075\u0065\u0072\u0072\u0061")
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "ja":
        i = i.replace("Action", "\u30a2\u30af\u30b7\u30e7\u30f3")
        i = i.replace("Adventure", "\u30a2\u30c9\u30d9\u30f3\u30c1\u30e3\u30fc")
        i = i.replace("Animation", "\u30a2\u30cb\u30e1\u30fc\u30b7\u30e7\u30f3")
        i = i.replace("Anime", "\u30a2\u30cb\u30e1")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u30b3\u30e1\u30c7\u30a3")
        i = i.replace("Crime", "\u72af\u7f6a")
        i = i.replace("Documentary", "\u30c9\u30ad\u30e5\u30e1\u30f3\u30bf\u30ea\u30fc")
        i = i.replace("Drama", "\u30c9\u30e9\u30de")
        i = i.replace("Family", "\u30d5\u30a1\u30df\u30ea\u30fc")
        i = i.replace("Fantasy", "\u30d5\u30a1\u30f3\u30bf\u30b8\u30fc")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u5c65\u6b74")
        i = i.replace("Horror", "\u30db\u30e9\u30fc")
        i = i.replace("Music ", "\u97f3\u697d")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u8b0e")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u30ed\u30de\u30f3\u30b9")
        i = i.replace(
            "Science Fiction",
            "\u30b5\u30a4\u30a8\u30f3\u30b9\u30d5\u30a3\u30af\u30b7\u30e7\u30f3",
        )
        i = i.replace(
            "Sci-Fi",
            "\u30b5\u30a4\u30a8\u30f3\u30b9\u30d5\u30a3\u30af\u30b7\u30e7\u30f3",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u30b9\u30ea\u30e9\u30fc")
        i = i.replace("War", "\u6226\u4e89")
        i = i.replace("Western", "\u897f\u6d0b")

    elif lang == "ko":
        i = i.replace("Action", "\uc561\uc158")
        i = i.replace("Adventure", "\ubaa8\ud5d8")
        i = i.replace("Animation", "\uc560\ub2c8\uba54\uc774\uc158")
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\ucf54\ubbf8\ub514")
        i = i.replace("Crime", "\ubc94\uc8c4")
        i = i.replace("Documentary", "\ub2e4\ud050\uba58\ud130\ub9ac")
        i = i.replace("Drama", "\ub4dc\ub77c\ub9c8")
        i = i.replace("Family", "\uac00\uc871")
        i = i.replace("Fantasy", "\ud310\ud0c0\uc9c0")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\uc5ed\uc0ac")
        i = i.replace("Horror", "\uacf5\ud3ec")
        i = i.replace("Music ", "\uc74c\uc545")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\ubbf8\uc2a4\ud130\ub9ac")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\ub85c\ub9e8\uc2a4")
        i = i.replace("Science Fiction", "\u0053\u0046")
        i = i.replace("Sci-Fi", "\u0053\u0046")
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\uc2a4\ub9b4\ub7ec")
        i = i.replace("War", "\uc804\uc7c1")
        i = i.replace("Western", "\uc11c\ubd80")

    elif lang == "nl":
        i = i.replace("Action", "\u0041\u0063\u0074\u0069\u0065")
        i = i.replace("Adventure", "\u0041\u0076\u006f\u006e\u0074\u0075\u0075\u0072")
        i = i.replace("Animation", "\u0041\u006e\u0069\u006d\u0061\u0074\u0069\u0065")
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u004b\u006f\u006d\u0065\u0064\u0069\u0065")
        i = i.replace("Crime", "\u004d\u0069\u0073\u0064\u0061\u0061\u0064")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u0063\u0075\u006d\u0065\u006e\u0074\u0061\u0069\u0072\u0065",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u0061")
        i = i.replace("Family", "\u0046\u0061\u006d\u0069\u006c\u0069\u0065")
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0069\u0065")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace(
            "History", "\u0048\u0069\u0073\u0074\u006f\u0072\u0069\u0073\u0063\u0068"
        )
        i = i.replace("Horror", "\u0048\u006f\u0072\u0072\u006f\u0072")
        i = i.replace("Music ", "\u004d\u0075\u007a\u0069\u0065\u006b")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u004d\u0079\u0073\u0074\u0065\u0072\u0069\u0065")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace(
            "Romance", "\u0052\u006f\u006d\u0061\u006e\u0074\u0069\u0065\u006b"
        )
        i = i.replace(
            "Science Fiction",
            "\u0053\u0063\u0069\u0065\u006e\u0063\u0065\u0066\u0069\u0063\u0074\u0069\u006f\u006e",
        )
        i = i.replace(
            "Sci-Fi",
            "\u0053\u0063\u0069\u0065\u006e\u0063\u0065\u0066\u0069\u0063\u0074\u0069\u006f\u006e",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace("War", "\u004f\u006f\u0072\u006c\u006f\u0067")
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "pl":
        i = i.replace("Action", "\u0041\u006b\u0063\u006a\u0061")
        i = i.replace(
            "Adventure", "\u0050\u0072\u007a\u0079\u0067\u006f\u0064\u006f\u0077\u0079"
        )
        i = i.replace("Animation", "\u0041\u006e\u0069\u006d\u0061\u0063\u006a\u0061")
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u004b\u006f\u006d\u0065\u0064\u0069\u0061")
        i = i.replace("Crime", "\u004b\u0072\u0079\u006d\u0069\u006e\u0061\u0142")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u006b\u0075\u006d\u0065\u006e\u0074\u0061\u006c\u006e\u0079",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u0061\u0074")
        i = i.replace(
            "Family", "\u0046\u0061\u006d\u0069\u006c\u0069\u006a\u006e\u0079"
        )
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0079")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace(
            "History",
            "\u0048\u0069\u0073\u0074\u006f\u0072\u0079\u0063\u007a\u006e\u0079",
        )
        i = i.replace("Horror", "\u0048\u006f\u0072\u0072\u006f\u0072")
        i = i.replace("Music ", "\u004d\u0075\u007a\u0079\u0063\u007a\u006e\u0079")
        i = i.replace("Musical", "Musical")
        i = i.replace(
            "Mystery", "\u0054\u0061\u006a\u0065\u006d\u006e\u0069\u0063\u0061"
        )
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0052\u006f\u006d\u0061\u006e\u0073")
        i = i.replace("Science Fiction", "\u0053\u0063\u0069\u002d\u0046\u0069")
        i = i.replace("Sci-Fi", "\u0053\u0063\u0069\u002d\u0046\u0069")
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace("War", "\u0057\u006f\u006a\u0065\u006e\u006e\u0079")
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "pt":
        i = i.replace("Action", "\u0041\u00e7\u00e3\u006f")
        i = i.replace("Adventure", "\u0041\u0076\u0065\u006e\u0074\u0075\u0072\u0061")
        i = i.replace("Animation", "\u0041\u006e\u0069\u006d\u0061\u00e7\u00e3\u006f")
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u0043\u006f\u006d\u00e9\u0064\u0069\u0061")
        i = i.replace("Crime", "\u0043\u0072\u0069\u006d\u0065")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u0063\u0075\u006d\u0065\u006e\u0074\u00e1\u0072\u0069\u006f",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u0061")
        i = i.replace("Family", "\u0046\u0061\u006d\u00ed\u006c\u0069\u0061")
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0069\u0061")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u0048\u0069\u0073\u0074\u00f3\u0072\u0069\u0061")
        i = i.replace("Horror", "\u0054\u0065\u0072\u0072\u006f\u0072")
        i = i.replace("Music ", "\u004d\u00fa\u0073\u0069\u0063\u0061")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u004d\u0069\u0073\u0074\u00e9\u0072\u0069\u006f")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0052\u006f\u006d\u0061\u006e\u0063\u0065")
        i = i.replace(
            "Science Fiction",
            "\u0046\u0069\u0063\u00e7\u00e3\u006f \u0063\u0069\u0065\u006e\u0074\u00ed\u0066\u0069\u0063\u0061",
        )
        i = i.replace(
            "Sci-Fi",
            "\u0046\u0069\u0063\u00e7\u00e3\u006f \u0063\u0069\u0065\u006e\u0074\u00ed\u0066\u0069\u0063\u0061",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace("War", "\u0047\u0075\u0065\u0072\u0072\u0061")
        i = i.replace("Western", "\u0046\u0061\u0072\u006f\u0065\u0073\u0074\u0065")

    elif lang == "ro":
        i = i.replace("Action", "\u0041\u0063\u021b\u0069\u0075\u006e\u0065")
        i = i.replace("Adventure", "\u0041\u0076\u0065\u006e\u0074\u0075\u0072\u0069")
        i = i.replace("Animation", "\u0041\u006e\u0069\u006d\u0061\u0163\u0069\u0065")
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u0043\u006f\u006d\u0065\u0064\u0069\u0065")
        i = i.replace("Crime", "\u0043\u0072\u0069\u006d\u0103")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u0063\u0075\u006d\u0065\u006e\u0074\u0061\u0072",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u0103")
        i = i.replace("Family", "\u0046\u0061\u006d\u0069\u006c\u0069\u0065")
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0079")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u0049\u0073\u0074\u006f\u0072\u0069\u0063")
        i = i.replace("Horror", "\u0048\u006f\u0072\u0072\u006f\u0072")
        i = i.replace("Music ", "\u004d\u0075\u007a\u0069\u0063\u0103")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u004d\u0069\u0073\u0074\u0065\u0072")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0052\u006f\u006d\u0061\u006e\u0074\u0069\u0063")
        i = i.replace("Science Fiction", "\u0053\u0046")
        i = i.replace("Sci-Fi", "\u0053\u0046")
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace("War", "\u0052\u0103\u007a\u0062\u006f\u0069")
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "ru":
        i = i.replace("Action", "\u0431\u043e\u0435\u0432\u0438\u043a")
        i = i.replace(
            "Adventure",
            "\u043f\u0440\u0438\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f",
        )
        i = i.replace(
            "Animation", "\u043c\u0443\u043b\u044c\u0442\u0444\u0438\u043b\u044c\u043c"
        )
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u043a\u043e\u043c\u0435\u0434\u0438\u044f")
        i = i.replace("Crime", "\u043a\u0440\u0438\u043c\u0438\u043d\u0430\u043b")
        i = i.replace(
            "Documentary",
            "\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u043b\u044c\u043d\u044b\u0439",
        )
        i = i.replace("Drama", "\u0434\u0440\u0430\u043c\u0430")
        i = i.replace("Family", "\u0441\u0435\u043c\u0435\u0439\u043d\u044b\u0439")
        i = i.replace("Fantasy", "\u0444\u044d\u043d\u0442\u0435\u0437\u0438")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u0438\u0441\u0442\u043e\u0440\u0438\u044f")
        i = i.replace("Horror", "\u0443\u0436\u0430\u0441\u044b")
        i = i.replace("Music ", "\u043c\u0443\u0437\u044b\u043a\u0430")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u0434\u0435\u0442\u0435\u043a\u0442\u0438\u0432")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace(
            "Romance", "\u043c\u0435\u043b\u043e\u0434\u0440\u0430\u043c\u0430"
        )
        i = i.replace(
            "Science Fiction",
            "\u0444\u0430\u043d\u0442\u0430\u0441\u0442\u0438\u043a\u0430",
        )
        i = i.replace(
            "Sci-Fi", "\u0444\u0430\u043d\u0442\u0430\u0441\u0442\u0438\u043a\u0430"
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0442\u0440\u0438\u043b\u043b\u0435\u0440")
        i = i.replace("War", "\u0432\u043e\u0435\u043d\u043d\u044b\u0439")
        i = i.replace("Western", "\u0432\u0435\u0441\u0442\u0435\u0440\u043d")

    elif lang == "sl":
        i = i.replace("Action", "\u0041\u006b\u0063\u0069\u006a\u0061")
        i = i.replace("Adventure", "\u0041\u0076\u0061\u006e\u0074\u0075\u0072\u0061")
        i = i.replace(
            "Animation", "\u0041\u006e\u0069\u006d\u0061\u0063\u0069\u006a\u0061"
        )
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u041a\u043e\u043c\u0435\u0064\u0069\u006a\u0061")
        i = i.replace(
            "Crime", "\u041a\u0072\u0069\u006d\u0069\u006e\u0061\u006c\u006e\u0069"
        )
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u006b\u0075\u006d\u0065\u006e\u0074\u0061\u0072\u006e\u0069",
        )
        i = i.replace("Drama", "\u0044\u0072\u0430\u043c\u0430")
        i = i.replace(
            "Family", "\u0044\u0072\u0075\u017e\u0069\u006e\u0073\u006b\u0069"
        )
        i = i.replace(
            "Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0074\u0069\u006b\u0061"
        )
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace(
            "History",
            "\u005a\u0067\u006f\u0064\u006f\u0076\u0069\u006e\u0073\u006b\u0069",
        )
        i = i.replace(
            "Horror", "\u0047\u0072\u006f\u007a\u006c\u006a\u0069\u0076\u006b\u0061"
        )
        i = i.replace("Music ", "\u0047\u006c\u0061\u007a\u0062\u0065\u006e\u0069")
        i = i.replace("Musical", "Musical")
        i = i.replace(
            "Mystery", "\u004d\u0069\u0073\u0074\u0065\u0072\u0069\u006a\u0061"
        )
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace(
            "Romance", "\u0052\u006f\u006d\u0061\u006e\u0074\u0069\u006b\u0061"
        )
        i = i.replace(
            "Science Fiction",
            "\u005a\u006e\u0061\u006e\u0073\u0074\u0076\u0065\u006e\u0061 \u0066\u0061\u006e\u0074\u0061\u0073\u0074\u0069\u006b\u0061",
        )
        i = i.replace(
            "Sci-Fi",
            "\u005a\u006e\u0061\u006e\u0073\u0074\u0076\u0065\u006e\u0061 \u0066\u0061\u006e\u0074\u0061\u0073\u0074\u0069\u006b\u0061",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0422\u0072\u0069\u006c\u0065\u0072")
        i = i.replace(
            "War",
            "\u0056\u006f\u006a\u006e\u006f\u002d\u0070\u006f\u006c\u0069\u0074\u0069\u010d\u006e\u0069",
        )
        i = i.replace("Western", "\u0057\u0065\u0073\u0074\u0065\u0072\u006e")

    elif lang == "sr":
        i = i.replace("Action", "\u0410\u043a\u0446\u0438\u043e\u043d\u0438")
        i = i.replace(
            "Adventure",
            "\u0410\u0432\u0430\u043d\u0442\u0443\u0440\u0438\u0441\u0442\u0438\u0447\u043a\u0438",
        )
        i = i.replace("Animation", "\u0426\u0440\u0442\u0430\u043d\u0438")
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u041a\u043e\u043c\u0435\u0434\u0438\u0458\u0430")
        i = i.replace("Crime", "\u041a\u0440\u0438\u043c\u0438")
        i = i.replace(
            "Documentary",
            "\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0440\u043d\u0438",
        )
        i = i.replace("Drama", "\u0414\u0440\u0430\u043c\u0430")
        i = i.replace(
            "Family", "\u041f\u043e\u0440\u043e\u0434\u0438\u0447\u043d\u0438"
        )
        i = i.replace(
            "Fantasy", "\u0424\u0430\u043d\u0442\u0430\u0441\u0442\u0438\u043a\u0430"
        )
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace(
            "History", "\u0418\u0441\u0442\u043e\u0440\u0438\u0458\u0441\u043a\u0438"
        )
        i = i.replace("Horror", "\u0425\u043e\u0440\u043e\u0440")
        i = i.replace("Music ", "\u041c\u0443\u0437\u0438\u0447\u043a\u0438")
        i = i.replace("Musical", "Musical")
        i = i.replace(
            "Mystery", "\u041c\u0438\u0441\u0442\u0435\u0440\u0438\u0458\u0430"
        )
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0409\u0443\u0431\u0430\u0432\u043d\u0438")
        i = i.replace(
            "Science Fiction",
            "\u041d\u0430\u0443\u0447\u043d\u0430 \u0444\u0430\u043d\u0442\u0430\u0441\u0442\u0438\u043a\u0430",
        )
        i = i.replace(
            "Sci-Fi",
            "\u041d\u0430\u0443\u0447\u043d\u0430 \u0444\u0430\u043d\u0442\u0430\u0441\u0442\u0438\u043a\u0430",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0422\u0440\u0438\u043b\u0435\u0440")
        i = i.replace("War", "\u0420\u0430\u0442\u043d\u0438")
        i = i.replace("Western", "\u0412\u0435\u0441\u0442\u0435\u0440\u043d")

    elif lang == "sv":
        i = i.replace("Action", "\u0041\u0063\u0074\u0069\u006f\u006e")
        i = i.replace("Adventure", "\u00c4\u0076\u0065\u006e\u0074\u0079\u0072")
        i = i.replace("Animation", "\u0041\u006e\u0069\u006d\u0065\u0072\u0061\u0074")
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u004b\u006f\u006d\u0065\u0064\u0069")
        i = i.replace("Crime", "\u004b\u0072\u0069\u006d\u0069\u006e\u0061\u006c")
        i = i.replace(
            "Documentary",
            "\u0044\u006f\u006b\u0075\u006d\u0065\u006e\u0074\u00e4\u0072",
        )
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d\u0061")
        i = i.replace("Family", "\u0046\u0061\u006d\u0069\u006c\u006a")
        i = i.replace("Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0079")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace(
            "History", "\u0048\u0069\u0073\u0074\u006f\u0072\u0069\u0073\u006b"
        )
        i = i.replace("Horror", "\u0053\u006b\u0072\u00e4\u0063\u006b")
        i = i.replace("Music ", "\u004d\u0075\u0073\u0069\u0063")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u004d\u0079\u0073\u0074\u0069\u006b")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0052\u006f\u006d\u0061\u006e\u0074\u0069\u006b")
        i = i.replace(
            "Science Fiction",
            "\u0053\u0063\u0069\u0065\u006e\u0063\u0065 \u0046\u0069\u0063\u0074\u0069\u006f\u006e",
        )
        i = i.replace(
            "Sci-Fi",
            "\u0053\u0063\u0069\u0065\u006e\u0063\u0065 \u0046\u0069\u0063\u0074\u0069\u006f\u006e",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0054\u0068\u0072\u0069\u006c\u006c\u0065\u0072")
        i = i.replace("War", "\u004b\u0072\u0069\u0067")
        i = i.replace("Western", "\u0056\u00e4\u0073\u0074\u0065\u0072\u006e")

    elif lang == "tr":
        i = i.replace("Action", "\u0041\u006b\u0073\u0069\u0079\u006f\u006e")
        i = i.replace("Adventure", "\u004d\u0061\u0063\u0065\u0072\u0061")
        i = i.replace(
            "Animation", "\u0041\u006e\u0069\u006d\u0061\u0073\u0079\u006f\u006e"
        )
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u004b\u006f\u006d\u0065\u0064\u0069")
        i = i.replace("Crime", "\u0053\u0075\u00e7")
        i = i.replace("Documentary", "\u0042\u0065\u006c\u0067\u0065\u0073\u0065\u006c")
        i = i.replace("Drama", "\u0044\u0072\u0061\u006d")
        i = i.replace("Family", "\u0041\u0069\u006c\u0065")
        i = i.replace(
            "Fantasy", "\u0046\u0061\u006e\u0074\u0061\u0073\u0074\u0069\u006b"
        )
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u0054\u0061\u0072\u0069\u0068")
        i = i.replace("Horror", "\u004b\u006f\u0072\u006b\u0075")
        i = i.replace("Music ", "\u004d\u00fc\u007a\u0069\u006b")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u0047\u0069\u007a\u0065\u006d")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u0052\u006f\u006d\u0061\u006e\u0074\u0069\u006b")
        i = i.replace(
            "Science Fiction",
            "\u0042\u0069\u006c\u0069\u006d\u002d\u004b\u0075\u0072\u0067\u0075",
        )
        i = i.replace(
            "Sci-Fi",
            "\u0042\u0069\u006c\u0069\u006d\u002d\u004b\u0075\u0072\u0067\u0075",
        )
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u0047\u0065\u0072\u0069\u006c\u0069\u006d")
        i = i.replace("War", "\u0053\u0061\u0076\u0061\u015f")
        i = i.replace(
            "Western", "\u0056\u0061\u0068\u015f\u0069 \u0042\u0061\u0074\u0131"
        )

    elif lang == "zh":
        i = i.replace("Action", "\u52a8\u4f5c")
        i = i.replace("Adventure", "\u5192\u9669")
        i = i.replace("Animation", "\u52a8\u753b")
        i = i.replace("Anime", "Anime")
        i = i.replace("Biography", "Biography")
        i = i.replace("Comedy", "\u559c\u5267")
        i = i.replace("Crime", "\u72af\u7f6a")
        i = i.replace("Documentary", "\u7eaa\u5f55")
        i = i.replace("Drama", "\u5267\u60c5")
        i = i.replace("Family", "\u5bb6\u5ead")
        i = i.replace("Fantasy", "\u5947\u5e7b")
        i = i.replace("Game-Show", "Game-Show")
        i = i.replace("History", "\u5386\u53f2")
        i = i.replace("Horror", "\u6050\u6016")
        i = i.replace("Music ", "\u97f3\u4e50")
        i = i.replace("Musical", "Musical")
        i = i.replace("Mystery", "\u60ac\u7591")
        i = i.replace("News", "News")
        i = i.replace("Reality-TV", "Reality-TV")
        i = i.replace("Romance", "\u7231\u60c5")
        i = i.replace("Science Fiction", "\u79d1\u5e7b")
        i = i.replace("Sci-Fi", "\u79d1\u5e7b")
        i = i.replace("Sport", "Sport")
        i = i.replace("Talk-Show", "Talk-Show")
        i = i.replace("Thriller", "\u60ca\u609a")
        i = i.replace("War", "\u6218\u4e89")
        i = i.replace("Western", "\u897f\u90e8")

    return i

"""
Winamax odds scraper
"""

import datetime
import json
import urllib
import urllib.error
import urllib.request

from bs4 import BeautifulSoup

import sportsbetting as sb

def parse_winamax(url):
    """
    Retourne les cotes disponibles sur winamax
    """
    ids = url.split("/sports/")[1]
    try:
        tournament_id = int(ids.split("/")[2])
    except IndexError:
        tournament_id = -1
    sport_id = int(ids.split("/")[0])
    try:
        req = urllib.request.Request(
            url, headers={'User-Agent': sb.USER_AGENT})
        webpage = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(webpage, features="lxml")
    except urllib.error.HTTPError:
        raise sb.UnavailableSiteException
    match_odds_hash = {}
    for line in soup.find_all(['script']):
        if "PRELOADED_STATE" in str(line.string):
            json_text = (line.string.split("var PRELOADED_STATE = ")[1]
                         .split(";var BETTING_CONFIGURATION")[0])
            if json_text[-1] == ";":
                json_text = json_text[:-1]
            dict_matches = json.loads(json_text)
            if "matches" in dict_matches:
                for match in dict_matches["matches"].values():
                    if (tournament_id in (match['tournamentId'], -1) and match["competitor1Id"] != 0
                            and match['sportId'] == sport_id and 'isOutright' not in match.keys()):
                        try:
                            match_name = match["title"].strip().replace("  ", " ")
                            date_time = datetime.datetime.fromtimestamp(match["matchStart"])
                            if date_time < datetime.datetime.today():
                                continue
                            main_bet_id = match["mainBetId"]
                            odds_ids = dict_matches["bets"][str(
                                main_bet_id)]["outcomes"]
                            odds = [dict_matches["odds"]
                                    [str(x)] for x in odds_ids]
                            match_odds_hash[match_name] = {}
                            match_odds_hash[match_name]['odds'] = {
                                "winamax": odds}
                            match_odds_hash[match_name]['date'] = date_time
                        except KeyError:
                            pass
            if not match_odds_hash:
                raise sb.UnavailableCompetitionException
            return match_odds_hash
    raise sb.UnavailableSiteException
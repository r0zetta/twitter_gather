#from igraph import *
import networkx as nx
import community
import sys, os, io, random, json, re
import pandas as pd
import numpy as np
import requests
from collections import Counter, deque
from time_helpers import *
from file_helpers import *
from process_tweet_object import *

report_every = 100000

quarters = {"Q1": [1, 2, 3],
            "Q2": [4, 5, 6],
            "Q3": [7, 8, 9],
            "Q4": [10, 11, 12]}

md = {"Jan": "01",
"Feb": "02",
"Mar": "03",
"Apr": "04",
"May": "05",
"Jun": "06",
"Jul": "07",
"Aug": "08",
"Sep": "09",
"Oct": "10",
"Nov": "11",
"Dec": "12"}

keywords = {"brexit":["yellowvest", 
                      "leaveeu",
                      "#leave",
                      "leave the eu",
                      "hate the eu",
                      "eu hater",
                      "anti eu",
                      "52%",
                      "no deal",
                      "nodeal"
                      "country back",
                      "uk great again",
                      "brexit",
                      "remoaner",
                      "wto",
                      "gowto",
                      "leavemnsleave",
                      "beleave",
                      "voted brexit",
                      "voted leave",
                      "hardbrexit",
                      "standup4brexit",
                      "standupforbrexit",
                      "britaindeservesbetter",
                      "changepoliticsforgood",
                      "takingbackcontrol",
                      "marchtoleave",
                      "mbga"],
            "tommy": ["tommy robinson",
                      "tommyrobinson",
                      "iamtommy",
                      "istandwithtommy",
                      "i stand with tommy",
                      "i am tommy",
                      "freetommy",
                      "free tommy",
                      "tommyr",
                      "tommyisfree"],
            "maga":  ["maga",
                      "qanon",
                      "trump",
                      "blexit",
                      "wwg1wga"],
            "resist": ["fucktrump",
                       "#resistance",
                       "burnitdown",
                       "metoo",
                       "releasethereport"],
            "labour": ["#gtto",
                      "labour",
                      "#jc4pm"],
            "fbpe":  ["#fpbe",
                      "peoplesvote",
                      "revokea50",
                      "finalsayforall",
                      "stopbrexit",
                      "#remain"],
            "blm":    ["blacklivesmatter",
                       "#blm"],
            "generic": ["father",
                        "veteran",
                        "football",
                        "family",
                        " fc",
                        "wife",
                        "mother",
                        "husband",
                        "dad",
                        "mum",
                        "mom",
                        "married",
                        "free speech",
                        "son",
                        "daughter",
                        "children",
                        "grand",
                        "proud",
                        "patriot",
                        "christian",
                        "god"],
            "racist":["#banislam",
                      "#bansharialaw",
                      "#banmuslims",
                      "#deportmuslims",
                      "#removemuslims",
                      "#islamisthemovementofsatan",
                      "#banhalal",
                      "#closethemosques",
                      "#stopwhitegenocide",
                      "anti islam",
                      "hate islam",
                      "#noislam"]}

fbf = "config/uk_football.json"
football = []
if os.path.exists(fbf):
    football = load_json(fbf)

if football is not None:
    keywords["football"] = football

uscsfn = "config/us_location_matches_lower.json"
uscs = []
if os.path.exists(uscsfn):
    uscs = load_json(uscsfn)

#####################################
# Basic helper functions
#####################################
def get_date_shortened(ca):
    ds = "-UNK-"
    if len(ca) >= 10:
        yr = ca[-4:]
        mon = md[ca[4:7]]
        day = ca[8:10]
        ds = str(yr) + "-" + str(mon) + "-" + str(day)
    return ds

def is_date_after(twitter_timestamp, date_cutoff):
    if len(date_cutoff) < 4:
        return True
    yr_cutoff = "1970"
    mon_cutoff = "01"
    day_cutoff = "01"
    if len(date_cutoff) >= 4:
        yr_cutoff = int(date_cutoff[:4])
    if len(date_cutoff) >= 7:
        mon_cutoff = int(date_cutoff[5:7])
    if len(date_cutoff) >= 10:
        day_cutoff = int(date_cutoff[9:])
    dc = str(yr_cutoff) + "-" + str(mon_cutoff) + "-" + str(day_cutoff) 
    ds = get_date_shortened(twitter_timestamp)
    if ds == "-UNK-":
        return False

    date1 = time.strptime(dc, "%Y-%m-%d")
    date2 = time.strptime(ds, "%Y-%m-%d")
    return date2 > date1

def get_keywords():
    return keywords

def num_to_k(num):
    if int(num) > 1000:
        num = str(int(int(num)/1000.0)) + " k"
    else:
        if len(str(num)) < 3:
            num = str(num) + " "
    return num

def find_exact_string(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def load_json(fn):
    ret = None
    with io.open(fn, "r", encoding="utf-8") as f:
        ret = json.load(f)
    return ret

def load_jsons(filename):
    ret = []
    with io.open(filename, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            ret.append(entry)
    return ret

def save_json(d, fn):
    with io.open(fn, "w", encoding="utf-8") as f:
        f.write(json.dumps(d, indent=4))

def save_csv(inter, fn):
    with io.open(fn, "w", encoding="utf-8") as f:
        f.write("Source,Target,Weight\n")
        for source, targets in inter.items():
            for target, count in targets.items():
                f.write(source + "," + target + "," + str(count) + "\n")

def make_batches(data, batch_len):
    num_batches = int(len(data)/batch_len)
    batches = (data[i:i+batch_len] for i in range(0, len(data), batch_len))
    return batches

def print_tweet_list(tweet_list, tweet_url_map):
    for t in tweet_list:
        print(t + "\t" + tweet_url_map[t])

def print_sn_tweet_list(sn_tweet_list, tweet_url_map):
    for sn, tweets in sn_tweet_list.items():
        print("")
        print("https://twitter.com/" + sn)
        print("================================")
        for t in tweets:
            print("\t" + t)
            print("\t" + tweet_url_map[t])
            print("")

def print_tweet_counter(tweet_counter, tweet_url_map, num):
    for tweet, count in tweet_counter.most_common(num):
        print(str(count) + "\t" + tweet + "\t" + tweet_url_map[tweet])

def print_tweet_texts(twid_count, twid_text, twid_url, num):
    for twid, count in twid_count.most_common(num):
        text = twid_text[twid]
        url = twid_url[twid]
        print(str(count) + "\t" + text + "\t" + url + "\t[" + twid + "]")

def print_sn_list(sn_list):
    for sn in sn_list:
        print("https://twitter.com/" + sn)

def print_sn_counter(sn_list, num):
    for user, count in sn_list.most_common(num):
        snstr = "https://twitter.com/" + user
        print(str(count) + "\t" + snstr)

def print_hashtag_list(ht_list):
    for ht in ht_list:
        print("#" + ht)

def print_hashtag_counter(ht_list, num):
    for ht, count in ht_list.most_common(num):
        htstr = "#" + ht
        print(str(count) + "\t" + htstr)

def print_counter(ct, num):
    for item, count in ct.most_common(num):
        print(str(count) + "\t" + str(item))

def print_counters(counters, user_fields, list_len):
    counter_names = [x for x, y in counters.items()]
    for n in counter_names:
        print("")
        print(n + " (" + str(len(counters[n])) + ")")
        print("---------")
        if n in user_fields:
            print_sn_counter(counters[n], list_len)
        elif n == "hashtags":
            print_hashtag_counter(counters[n], list_len)
        else:
            print_counter(counters[n], list_len)

def print_short_heatmap(hm):
    days = ["M", "T", "W", "T", "F", "S", "S"]
    print("")
    print("   " + "| ".join(["%02d"%x for x in range(24)]) + "|")
    print("-" * ((4 * 25)-2))
    for x in range(7):
        print(days[x] + "|" + "|".join(["%3d"%y for y in hm[x]]) + "|")
    print("")

def print_long_heatmap(long_hm):
    days = ["M", "T", "W", "T", "F", "S", "S"]
    count = 0
    for weeknum, hm in sorted(long_hm.items(), reverse=True):
        if count >= 20:
            break
        count += 1
        print("Week " + str(weeknum))
        print("")
        print("   " + "| ".join(["%02d"%x for x in range(24)]) + "|")
        print("-" * ((4 * 25)-2))
        for x in range(7):
            print(days[x] + "|" + "|".join(["%3d"%y for y in hm[x]]) + "|")
        print("")

def print_tweet_counts(tc):
    for item in tc:
        count, date = item
        print(str(count) +  "\t" + date)

def print_summary_list(rdetails, rtw, min_retweets, date_cutoff):
    ret = []
    total = 0
    print("User                                            | sc    | fl    | fr    |egg|  ca        | summary")
    print("==================================================================================================")
    for d in rdetails:
        ds = "-UNK-"
        if "created_at" in d:
            ca = d["created_at"]
            ds = get_date_shortened(ca)
        sn = d["screen_name"]
        id_str = d["id_str"]
        sc = str(num_to_k(d["statuses_count"]))
        fl = str(num_to_k(d["followers_count"]))
        fr = "-"
        if "friends_count" in d:
            fr = str(num_to_k(d["friends_count"]))
        egg = " "
        if d["default_profile"] == True and d["default_profile_image"] == True:
            egg = "X"
        de = ""
        if d["description"] is not None:
            de = d["description"][:100]
        n = d["name"]
        suml = []
        if len(de) < 1:
            suml.append("empty")
        for label, kw in keywords.items():
            for w in kw:
                if w in de.lower() or w in n.lower():
                    suml.append(label)
                    break
        if d["location"] is not None:
            if d["location"].lower() in uscs:
                suml.append("US")
        summary = "[" + " ".join(suml) + "]"
        sep = "\t"
        if len(sn) < 12:
            sep = "\t\t"
        total += 1
        rtc = 0
        if sn in rtw:
            rtc = rtw[sn]
        msg = "https://twitter.com/" + sn + sep + "(" + str(rtc) + ")\t| " 
        msg += sc + "\t| " + fl + "\t| " + fr + "\t| " + str(egg) + " | " + ds + " | " + summary
        is_valid_rtc = True
        if rtc < min_retweets:
            is_valid_rtc = False
        is_valid_date = is_date_after(d["created_at"], date_cutoff)
        if is_valid_rtc == True and is_valid_date == True:
            ret.append(sn)
            print(msg)
    return ret


def print_alt_summary_list(rdetails, rtw, min_retweets, date_cutoff):
    ret = []
    total = 0
    print("User                                            | sc    | fl    | fr    |egg|  ca        | name")
    print("==================================================================================================")
    for d in rdetails:
        ds = "-UNK-"
        if "created_at" in d:
            ca = d["created_at"]
            ds = get_date_shortened(ca)
        sn = d["screen_name"]
        id_str = d["id_str"]
        sc = str(num_to_k(d["statuses_count"]))
        fl = str(num_to_k(d["followers_count"]))
        fr = "-"
        if "friends_count" in d:
            fr = str(num_to_k(d["friends_count"]))
        egg = " "
        if d["default_profile"] == True and d["default_profile_image"] == True:
            egg = "X"
        de = ""
        if d["description"] is not None:
            de = d["description"][:100]
        n = d["name"]
        sep = "\t"
        if len(sn) < 12:
            sep = "\t\t"
        total += 1
        rtc = 0
        if sn in rtw:
            rtc = rtw[sn]
        msg = "https://twitter.com/" + sn + sep + "(" + str(rtc) + ")\t| " 
        msg += sc + "\t| " + fl + "\t| " + fr + "\t| " + str(egg) + " | " + ds + " | " + n
        is_valid_rtc = True
        if rtc < min_retweets:
            is_valid_rtc = False
        is_valid_date = is_date_after(d["created_at"], date_cutoff)
        if is_valid_rtc == True and is_valid_date == True:
            ret.append(sn)
            print(msg)
    return ret


def print_category_match(full, include, exclude, min_rtw, date_cutoff):
    ret = []
    sn_details = full["sn_details"]
    rdetails = []
    rtw = Counter()
    for sn, d in sn_details.items():
        if full["counters"]["users"][sn] < min_rtw:
            continue
        de = ""
        if d["description"] is not None:
            de = d["description"][:100]
        n = d["name"]
        suml = []
        if len(de) < 1:
            suml.append("empty")
        for label, kw in keywords.items():
            for w in kw:
                if w in de.lower() or w in n.lower():
                    suml.append(label)
                    break
        if d["location"] is not None:
            if d["location"].lower() in uscs:
                suml.append("US")
        if len(set(suml).intersection(set(include))) > 0:
            if len(set(suml).intersection(set(exclude))) < 1:
                rdetails.append(d)
                rtw[sn] = full["counters"]["users"][sn]
    return print_alt_summary_list(rdetails, rtw, min_retweets=min_rtw, date_cutoff=date_cutoff)

def print_url_amplifiers(url, full, min_retweets, date_cutoff):
    ret = []
    url_sn = full["url_sn"]
    sn_details = full["sn_details"]
    matches = set()
    match_c = Counter()
    for full_url, snl in url_sn.items():
        if url in full_url:
            matches.add(full_url)
            for x, c in snl.items():
                match_c[full_url] += c
    if len(matches) < 1:
        print("URL: " + url + " wasn't in url_sn")
        return
    rtw = Counter()
    print("Matches:")
    for m, c in match_c.most_common():
        print(str(c) + "\t" + m)
        snl = url_sn[m]
        for sn, c in snl.items():
            rtw[sn] += c

    rlist = [x for x, c in rtw.items()]
    rdetails = []
    for sn in rlist:
        if sn in sn_details:
            rdetails.append(sn_details[sn])
    return print_alt_summary_list(rdetails, rtw, min_retweets=min_retweets, date_cutoff=date_cutoff)

def print_hashtag_amplifiers(hashtag, full, min_retweets, date_cutoff):
    ret = []
    hashtag_sn = full["hashtag_sn"]
    sn_details = full["sn_details"]
    if hashtag not in hashtag_sn:
        print("Hashtag: " + hashtag + " wasn't in hashtag_sn")
        return
    rtw = hashtag_sn[hashtag]
    rlist = [x for x, c in rtw.items()]
    rdetails = []
    for sn in rlist:
        if sn in sn_details:
            rdetails.append(sn_details[sn])
    return print_alt_summary_list(rdetails, rtw, min_retweets, date_cutoff)

def print_target_amplifiers(target, full, min_retweets, date_cutoff):
    ret = []
    rsn_sn = full["rsn_sn"]
    sn_details = full["sn_details"]
    if target not in rsn_sn:
        print("Target: " + target + " wasn't in rsn_sn")
        return
    rtw = rsn_sn[target]
    rlist = [x for x, c in rtw.items()]
    rdetails = []
    for sn in rlist:
        if sn in sn_details:
            rdetails.append(sn_details[sn])
    return print_alt_summary_list(rdetails, rtw, min_retweets=min_retweets, date_cutoff=date_cutoff)

def print_most_amplified(full, cutoff, include_verified = False):
    ret = []
    hr = set()
    sn_details = full["sn_details"]
    rsn_sn = full["rsn_sn"]
    counters = full["counters"]
    for x, c in counters["retweeted"].most_common():
        if c > cutoff:
            hr.add(x)
    hrdet = []
    for sn in hr:
        if sn in sn_details:
            hrdet.append(sn_details[sn])
    total = 0
    print("User                                    rtc - rtn       | sc    | fl    | fr    |egg|  ca     | summary")
    print("=====================================================================================================")
    for d in hrdet:
        if include_verified == False and d["verified"] == True:
            continue
        ds = "   -UNK-  "
        if "created_at" in d:
            ca = d["created_at"]
            yr = ca[-4:]
            mon = md[ca[4:7]]
            day = ca[8:10]
            ds = str(yr) + "-" + str(mon) + "-" + str(day)
        sn = d["screen_name"]
        id_str = d["id_str"]
        sc = str(num_to_k(d["statuses_count"]))
        fl = str(num_to_k(d["followers_count"]))
        fr = "-"
        if "friends_count" in d:
            fr = str(num_to_k(d["friends_count"]))
        egg = " "
        if d["default_profile"] == True and d["default_profile_image"] == True:
            egg = "X"
        de = ""
        if d["description"] is not None:
            de = d["description"][:100]
        n = d["name"]
        suml = []
        if len(de) < 1:
            suml.append("empty")
        for label, kw in keywords.items():
            for w in kw:
                if w in de.lower() or w in n.lower():
                    suml.append(label)
                    break
        summary = "[" + " ".join(suml) + "]"
        sep = "\t"
        if len(sn) < 12:
            sep = "\t\t"
        total += 1
        rtc = 0
        rtn = 0
        for x, c in rsn_sn[sn].items():
            rtn += 1
            rtc += c
        msg = "https://twitter.com/" + sn + sep + "(" + str(rtc) + " - " + str(rtn) + ")\t| " 
        msg += sc + "\t| " + fl + "\t| " + fr + "\t| " + str(egg) + " | " + ds + " | " + summary
        ret.append(sn)
        print(msg)
    return ret

##############################################################
# Some user analysis functions
##############################################################
def make_short_heatmap(tweets):
    timestamps = []
    for d in tweets:
        ca = d["created_at"]
        tobj = twitter_time_to_object(ca)
        timestamps.append(tobj)
    return create_heatmap(timestamps)

def make_long_heatmap(tweets):
    timestamps = []
    for d in tweets:
        ca = d["created_at"]
        tobj = twitter_time_to_object(ca)
        timestamps.append(tobj)
    return create_long_heatmap(timestamps)

def get_tweet_counts_plot_data(tweets, num_dates=0):
    num_counter = Counter()
    for d in tweets:
        ca = d["created_at"]
        num = twitter_time_to_readable(ca)[:10]
        num_counter[num] += 1
    num_c = dict(num_counter)
    plot_data = {}
    plot_data["date"] = []
    plot_data["count"] = []
    count = 0
    for num, c in sorted(num_c.items(), reverse=True):
        if num_dates > 0 and count >= num_dates:
            break
        count += 1
        plot_data["date"].append(num)
        plot_data["count"].append(c)
    return plot_data

def get_tweet_counts_scatter_plot_data(tweets, num_dates=0):
    tweet_times = {}
    count = 0
    for d in tweets:
        if num_dates > 0 and count >= num_dates:
            break
        ca = d["created_at"]
        r = twitter_time_to_readable(ca)
        num = r[:10]
        if num not in tweet_times:
            count += 1
            tweet_times[num] = Counter()
        h = r[11:13]
        tweet_times[num][h] += 1
    plot_data = {}
    plot_data["hour"] = []
    plot_data["date"] = []
    plot_data["count"] = []
    count = 0
    for date, tc in sorted(tweet_times.items(), reverse=False):
        if count == 0:
            for x in range(24):
                plot_data["date"].append("--")
                plot_data["hour"].append(x)
                plot_data["count"].append(0.1)
        count += 1
        for h, c in sorted(tc.items()):
            plot_data["date"].append(date)
            plot_data["hour"].append(h)
            plot_data["count"].append(c)
    return plot_data

def get_sorted_tweet_counts(tweets, num_dates=0):
    num_counter = Counter()
    for d in tweets:
        ca = d["created_at"]
        num = twitter_time_to_readable(ca)[:10]
        num_counter[num] += 1
    num_c = dict(num_counter)
    print_data = []
    count = 0
    for num, c in sorted(num_c.items(), reverse=True):
        if num_dates > 0 and count >= num_dates:
            break
        count += 1
        print_data.append([c, num])
    return print_data

def make_interarrivals_plot_data(tweets):
    interarrivals = Counter()
    previous_timestamp = None
    for d in tweets:
        ca = d["created_at"]
        unix = twitter_time_to_unix(ca)
        if previous_timestamp is not None:
            delta = abs(previous_timestamp - unix)
            interarrivals[delta] += 1
        previous_timestamp = unix
    plot_data = {}
    plot_data["deltas"] = []
    plot_data["counts"] = []
    num = 0
    for delta, count in sorted(interarrivals.items()):
        if num > 100:
            break
        num += 1
        plot_data["deltas"].append(delta)
        plot_data["counts"].append(count)
    return plot_data

def make_interarrivals_scatter_plot_data(tweets):
    deltas = []
    previous_timestamp = None
    for d in tweets:
        ca = d["created_at"]
        unix = twitter_time_to_unix(ca)
        if previous_timestamp is not None:
            delta = abs(previous_timestamp - unix)
            deltas.append(delta)
        previous_timestamp = unix
    plot_data = {}
    plot_data["deltas"] = []
    plot_data["index"] = []
    num = 0
    for index, delta in enumerate(deltas):
        if delta > 50000:
            continue
        plot_data["deltas"].append(delta)
        plot_data["index"].append(index)
    return plot_data



##############################################################
# Text processing
##############################################################
def tokenize_sentence(text, stopwords):
    text = text.replace(",", "")
    text = text.replace(".", "")
    words = re.split(r'(\s+)', text)
    if len(words) < 1:
        return
    tokens = []
    for w in words:
        if w is not None:
            w = w.strip()
            w = w.lower()
            if w.isspace() or w == "\n" or w == "\r":
                w = None
            if w is not None and "http" in w:
                w = None
            if w is not None and len(w) < 1:
                w = None
            if w is not None and u"…" in w:
                w = None
            if w is not None:
                tokens.append(w)
    if len(tokens) < 1:
        return []
# Remove stopwords and other undesirable tokens
    cleaned = []
    endtoks = [":", ",", "\'", "…", "."]
    for token in tokens:
        if len(token) > 0:
            if stopwords is not None:
                if token in stopwords:
                    token = None
            if token is not None and len(token) > 0 and token[-1] in endtoks:
                token = token[0:-1]
            if token is not None and len(token) > 0 and token[0] in endtoks:
                token = token[1:]
            if token is not None:
                if re.search(".+…$", token):
                    token = None
            if token is not None:
                if token == "#":
                    token = None
            if token is not None:
                cleaned.append(token)
    if len(cleaned) < 1:
        return []
    return cleaned

#####################################
# Data loading and caching
#####################################
def read_from_raw_data(start_time, end_time, filename):
    ret = []
    print("Reading data from: " + start_time + " to: " + end_time)
    start = time_object_to_unix(time_string_to_object(start_time))
    end = time_object_to_unix(time_string_to_object(end_time))
    count = 0
    with io.open(filename, "r", encoding="utf-8") as f:
        for line in f:
            count += 1
            if count % report_every == 0:
                print("Count: " + str(count))
            d = json.loads(line)
            timestamp = twitter_time_to_unix(d["created_at"])
            if timestamp >= end:
                break
            if timestamp >= start and timestamp <= end:
                ret.append(d)
    print("Saw a total of " + str(count) + " records.")
    print(str(len(ret)) + " records matched the date range.")
    return ret

def create_cache(start_time, end_time, filename, cachefile):
    print("Creating cache with data from: " + start_time + " to: " + end_time)
    start = time_object_to_unix(time_string_to_object(start_time))
    end = time_object_to_unix(time_string_to_object(end_time))
    cf = io.open(cachefile, "a", encoding="utf-8")
    count = 0
    matched = 0
    with io.open(filename, "r", encoding="utf-8") as f:
        for line in f:
            count += 1
            if count % report_every == 0:
                print("Count: " + str(count))
            d = json.loads(line)
            timestamp = twitter_time_to_unix(d["created_at"])
            if timestamp >= end:
                break
            if timestamp >= start and timestamp <= end:
                matched += 1
                cf.write(line)
    cf.close()
    print("Cached a total of " + str(matched) + " records.")
    return cachefile

def make_file_iterator(start_time, end_time, filename="data/raw.json"):
    print("Creating iterator from: " + start_time + " to: " + end_time)
    start = time_object_to_unix(time_string_to_object(start_time))
    end = time_object_to_unix(time_string_to_object(end_time))
    count = 0
    with io.open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if len(line) == 0:
                print("Resetting iterator")
                f.seek(0)
                return
            count += 1
            if count % report_every == 0:
                print("Count: " + str(count))
            d = json.loads(line)
            timestamp = twitter_time_to_unix(d["created_at"])
            if timestamp >= end:
                break
            if timestamp >= start and timestamp <= end:
                yield(d)

def read_timeline_data(filename):
    if not os.path.exists(filename):
        print("File: " + filename + " did not exist.")
        return
    print("Reading in " + filename)
    count = 0
    ret = []
    with io.open(filename, "r", encoding="utf-8") as f:
        for line in f:
            count += 1
            if count % 1000 == 0:
                print("Count: " + str(count))
            d = json.loads(line)
            ret.append(d)
    return ret

def make_timeline_iterator(filename):
    if not os.path.exists(filename):
        print("File: " + filename + " did not exist.")
        return
    print("Opening iterator on " + filename)
    count = 0
    with io.open(filename, "r", encoding="utf-8") as f:
        for line in f:
            count += 1
            if count % 1000 == 0:
                print("Count: " + str(count))
            d = json.loads(line)
            yield(d)

def get_timelines(filename):
    all_tweets = []
    seen = []
    raw_data = make_timeline_iterator(filename)
    for item in raw_data:
        sn = list(item.keys())[0]
        if sn.lower() not in seen:
            seen.append(sn.lower())
            tweets = list(item.values())[0]
            tweet_count = 0
            for d in tweets:
                all_tweets.append(d)
                tweet_count += 1
        print("https://twitter.com/" + sn + " : " + str(tweet_count))
    return all_tweets

def get_tweet_details(d):
    tweet_fields = ["id_str",
                    "text",
                    "lang",
                    "created_at", 
                    "in_reply_to_screen_name",
                    "in_reply_to_status_id",
                    "is_quote_status",
                    "retweet_count", 
                    "favorite_count", 
                    "quote_count", 
                    "reply_count", 
                    "source"]
    user_fields = ["id_str",
                   "screen_name",
                   "name",
                   "lang",
                   "friends_count",
                   "followers_count",
                   "description",
                   "location",
                   "statuses_count",
                   "favourites_count",
                   "listed_count",
                   "created_at",
                   "default_profile_image",
                   "default_profile",
                   "verified",
                   "protected"]
    entry = {}
    for f in tweet_fields:
        if f in d:
            entry[f] = d[f]
    if "retweeted_status" in d:
        s = d["retweeted_status"]
        entry["retweeted_status"] = {}
        for f in tweet_fields:
            if f in s:
                entry["retweeted_status"][f] = s[f]
        if "user" in s:
            u = s["user"]
            entry["retweeted_status"]["user"] = {}
            for fu in user_fields:
                if fu in u:
                    entry["retweeted_status"]["user"][fu] = u[fu]
    if "user" in d:
        u = d["user"]
        entry["user"] = {}
        for fu in user_fields:
            if fu in u:
                entry["user"][fu] = u[fu]
    entry["hashtags"] = get_hashtags_preserve_case(d)
    entry["urls"] = get_urls(d)
    entry["interactions"] = get_interactions_preserve_case(d)
    entry["mentioned"] = get_mentioned(d)
    entry["retweeted"] = get_retweeted_user(d)
    entry["quoted"] = get_quoted(d)
    return entry

#####################################
# Graph manipulation
#####################################
def match_graph(inter, sn_list):
    ret = {}
    for source, targets in inter.items():
        if source in sn_list:
            ret[source] = targets
            continue
        for target, weight in targets.items():
            if target in sn_list:
                ret[source] = targets
                break
    return ret

def match_graph2(inter, sn_list):
    ret = {}
    for source, targets in inter.items():
        if source in sn_list:
            for target, weight in targets.items():
                if target in sn_list:
                    if source not in ret:
                        ret[source] = {}
                    ret[source][target] = weight
    return ret

def trim_graph(inter, all_users, cutoff):
    print("All users: " + str(len(all_users)))
    trimmed_users = []
    for name, count in all_users.items():
        if count > cutoff:
            trimmed_users.append(name)
    print("Trimmed users: " + str(len(trimmed_users)))
    trimmed = {}
    for source, targets in inter.items():
        if source in trimmed_users:
            trimmed[source] = targets
            continue
        found = False
        for target, count in targets.items():
            if target in trimmed_users:
                trimmed[source] = targets
                break
    return trimmed

def trim_graph_influencers(inter, influencers, cutoff):
    print("Influencers: " + str(len(influencers)))
    trimmed_users = []
    for name, count in influencers.items():
        if count > cutoff:
            trimmed_users.append(name)
    print("Trimmed users: " + str(len(trimmed_users)))
    trimmed = {}
    for source, targets in inter.items():
        if source in trimmed_users:
            trimmed[source] = targets
            continue
        found = False
        for target, count in targets.items():
            if target in trimmed_users:
                trimmed[source] = targets
                break
    return trimmed

def trim_graph2(inter, all_users, cutoff):
    print("All users: " + str(len(all_users)))
    trimmed_users = []
    for name, count in all_users.items():
        if count > cutoff:
            trimmed_users.append(name)
    print("Trimmed users: " + str(len(trimmed_users)))
    trimmed = {}
    for source, targets in inter.items():
        if source in trimmed_users:
            for target, count in targets.items():
                if target in trimmed_users:
                    if source not in trimmed:
                        trimmed[source] = {}
                    trimmed[source][target] = count
            continue
        found = False
        for target, count in targets.items():
            if target in trimmed_users:
                if source not in trimmed:
                    trimmed[source] = {}
                trimmed[source][target] = count
    return trimmed

def get_communities(inter):
    mapping = []
    for source, targets in inter.items():
        for target, count in targets.items():
            mapping.append((source, target, count))
    g=nx.Graph()
    g.add_weighted_edges_from(mapping)
    communities = community.best_partition(g)

    clusters = {}
    for node, mod in communities.items():
        if mod not in clusters:
            clusters[mod] = []
        clusters[mod].append(node)
    return clusters
    
    print("Calculating communities")
    communities = community.best_partition(g)

def get_communities_old(inter):
    names = set()
    print("Building vocab")
    for source, targets in inter.items():
        names.add(source)
        for target, count in targets.items():
            names.add(target)
    vocab = {}
    vocab_inv = {}
    for index, name in enumerate(names):
        vocab[name] = index
        vocab_inv[index] = name
    print("Vocab length: " + str(len(vocab)))

    vocab_len = len(vocab)
    g = Graph()
    g.add_vertices(vocab_len)
    edge_count = 0
    max_s = len(inter)
    edges = []
    print("Getting edges")
    for source, target_list in inter.items():
        if len(target_list) > 0:
            for target, w in target_list.items():
                edges.append((vocab[source], vocab[target]))
                edge_count += 1
    print
    print("Found " + str(vocab_len) + " nodes.")
    print("Found " + str(edge_count) + " edges.")
    print("Building graph")
    g.add_edges(edges)
    print(summary(g))

    print("Getting communities.")
    communities = g.community_multilevel()
    print("Found " + str(len(communities)) + " communities.")

    clusters = {}
    for mod, nodelist in enumerate(communities):
        clusters[mod] = []
        for ident in nodelist:
            clusters[mod].append(vocab_inv[ident])
    return clusters

def get_cluster_for_sn(sn, clusters):
    for index, names in clusters.items():
        if sn in names:
            return names

def get_cluster_index_for_sn(sn, clusters):
    for index, names in clusters.items():
        if sn in names:
            return index

def get_cluster_overlaps_partial(clusters, sn_rsn, index_list):
    cluster_overlap = {}
    for index, names in clusters.items():
        if index not in index_list:
            continue
        if index not in cluster_overlap:
            cluster_overlap[index] = Counter()
        cluster_overlap[index][index] = 0
        for iindex, inames in clusters.items():
            if iindex not in index_list:
                continue
            if len(inames) > 10 and iindex != index:
                overlap_count = 0
                for n in inames:
                    if n in sn_rsn:
                        nl = set([x for x, c in sn_rsn[n].items()])
                        inter = set(names).intersection(nl)
                        overlap_count += len(inter)
                cluster_overlap[index][iindex] = overlap_count
    return cluster_overlap

def get_cluster_overlaps(clusters):
    cluster_overlap = {}
    for index, names in clusters.items():
        if len(names) > 10:
            if index not in cluster_overlap:
                cluster_overlap[index] = Counter()
            for iindex, inames in clusters.items():
                if len(inames) > 10 and iindex != index:
                    overlap_count = 0
                    for n in inames:
                        if n in sn_rsn:
                            nl = set([x for x, c in sn_rsn[n].items()])
                            inter = set(names).intersection(nl)
                            overlap_count += len(inter)
                    cluster_overlap[index][iindex] = overlap_count
    return cluster_overlap

def get_cluster_overlap(c1, c2, clusters):
    overlap_names = set()
    names1 = clusters[c1]
    names2 = clusters[c2]
    for n in names2:
        if n in sn_rsn:
            nl = set([x for x, c in sn_rsn[n].items()])
            inter = set(names1).intersection(nl)
            if len(inter) > 0:
                overlap_names.add(n)
    return overlap_names

#####################################
# Generic analysis of data
#####################################
def make_hashtag_interactions(raw_data, ht_list, whitelist):
    interactions = {}
    for d in raw_data:
        sn = d["user"]["screen_name"]
        if sn in whitelist:
            continue
        sn = "@" + sn
        if "hashtags" in d:
            hashtags = d["hashtags"]
            if len(set(hashtags).intersection(set(ht_list))) > 0:
                if sn not in interactions:
                    interactions[sn] = {}
                if "retweeted_status" in d:
                    rsn = d["retweeted_status"]["user"]["screen_name"]
                    if rsn not in whitelist:
                        rsn = "@" + rsn
                        if rsn not in interactions[sn]:
                            interactions[sn][rsn] = 1
                        else:
                            interactions[sn][rsn] += 1
                for h in hashtags:
                    ht = "#" + h
                    if ht not in interactions[sn]:
                        interactions[sn][ht] = 1
                    else:
                        interactions[sn][ht] += 1
    return interactions

def get_tweet_id_interactions(raw_data, twid_list):
    interactions = {}
    for d in raw_data:
        sn = d["user"]["screen_name"]
        twid = d["id_str"]
        if "retweeted_status" in d:
            twid = d["retweeted_status"]["id_str"]
        if twid in twid_list:
            if sn not in interactions:
                interactions[sn] = {}
            interactions[sn][twid] = 1
    return interactions

def counter_to_plot(cdata, label):
    plot_data = {}
    plot_data[label] = []
    plot_data["count"] = []
    for item, c in sorted(cdata.items(), reverse=True):
        plot_data[label].append(item)
        plot_data["count"].append(c)
    return plot_data

def trim_plot_data(plot_data, start, end):
    new_plot_data = {}
    for k in plot_data.keys():
        new_plot_data[k] = plot_data[k][start:end]
    return new_plot_data

def get_counters_and_interactions2(raw_data):
    stopwords = load_json("config/stopwords.json")
    stopwords = stopwords["en"]
    stopwords += ["rt", "-", "&amp;"]

    ngram_names =  ["words",
                    "2-grams",
                    "3-grams",
                    "4-grams",
                    "5-grams",
                    "6-grams",
                    "7-grams"]

    counter_names = ["users",
                     "susp_users",
                     "influencers",
                     "amplifiers",
                     "hashtags",
                     "mentioned",
                     "mentioners",
                     "quoted",
                     "quoters",
                     "retweeted",
                     "retweeters",
                     "replied_to",
                     "repliers",
                     "domains",
                     "sources",
                     "lang",
                     "urls"]

    user_fields = ["users",
                   "susp_users",
                   "influencers",
                   "amplifiers",
                   "mentioned",
                   "mentioners",
                   "quoted",
                   "quoters",
                   "repliers",
                   "retweeted",
                   "retweeters",
                   "replied_to"]

    timestamp_counts = Counter()
    hashtag_counts = {}
    user_counts = {}
    retweeted_user_counts = {}
    retweeted_twid_counts = {}
    twid_count = Counter()
    twid_rtc = Counter()
    twid_rt_count = Counter()
    twid_text = {}
    twid_url = {}
    twid_sn = {}
    twid_rsn = {}
    twid_doc = {}
    sn_twid = {}
    rsn_twid = {}
    sn_hashtag = {}
    hashtag_sn = {}
    hashtag_twid = {}
    sn_domain = {}
    domain_sn = {}
    domain_twid = {}
    url_twid = {}
    sn_url = {}
    url_sn = {}
    sn_source = {}
    source_sn = {}
    sn_details = {}

    susp_twids = set()
    orig_twids = set()
    susp_orig_twids = set()
    retweeted_twids = set()
    replied_twids = set()
    quoted_twids = set()

    sn_quo = {}
    quo_sn = {}
    sn_rsn = {}
    rsn_sn = {}
    sn_rep = {}
    rep_sn = {}
    sn_men = {}
    men_sn = {}
    counters = {}

    oldest = 0
    newest = 0
    all_min = 2
    all_max = 5
    min_tokens = 3

    for n in counter_names:
        counters[n] = Counter()
    for n in ngram_names:
        counters[n] = Counter()
        twid_doc[n] = {}
    twid_doc["all"] = {}
    count = 0
    for d in raw_data:
        count += 1
        suspicious = False
        original = False
        ca = twitter_time_to_readable(d["created_at"])
        unix = twitter_time_to_unix(d["created_at"])
        lang = d["lang"]
        counters["lang"][lang] += 1
        source = get_tweet_source(d)
        counters["sources"][source] += 1
        if oldest == 0:
            oldest = unix
        if unix > newest:
            newest = unix
        if unix < oldest:
            oldest = unix
        datestamp = ca[:10]
        hour = ca[11:13]
        timestamp = datestamp + " " + hour + ":00"
        timestamp_counts[timestamp] += 1
        twid = d["id_str"]
        sn = d["user"]["screen_name"]
        if sn not in user_counts:
            user_counts[sn] = Counter()
        if sn not in sn_source:
            sn_source[sn] = Counter()
        if source not in source_sn:
            source_sn[source] = Counter()
        sn_source[sn][source] += 1
        source_sn[source][sn] += 1
        user_counts[sn][timestamp] += 1
        sn_details[sn] = d["user"]
        counters["users"][sn] += 1
        text = d["text"]
        twid = d["id_str"]
        retweet_count = d["retweet_count"]
        like_count = d["favorite_count"]
        url = "https://twitter.com/" + sn + "/status/" + twid
        twid_count[twid] += 1
        twid_rtc[twid] = retweet_count
        twid_text[twid] = text.replace("\n", "")
        twid_url[twid] = url
        if twid not in twid_sn:
            twid_sn[twid] = Counter()
        twid_sn[twid][sn] += 1
        if sn not in sn_twid:
            sn_twid[sn] = Counter()
        sn_twid[sn][twid] += 1
        quote = False
        retweet = False
        reply = False

        fbid = ["followback", "follow back", "Follow Back", "FOLLOWERS", "FOLLOW ME", "RT this", "RT THIS", "retweet this", "RETWEET THIS", "Retweet this", "Follow me", "please retweet", "Please retweet", "PLEASE RETWEET", "RETWEET the FLAG"]
        for f in fbid:
            if f in text:
                susp_twids.add(twid)
                suspicious = True
                counters["susp_users"][sn] += 1

        num_grams = len(ngram_names)
        num_w = 0
        num_ht = 0
        prev = deque()
        docx = {}
        for n in range(num_grams):
            docx[ngram_names[n]] = []
        stopwords = None
        tokens = tokenize_sentence(text, stopwords)
        for i, t in enumerate(tokens):
            was_word = True
            if len(t) > 1:
                if t[0] == "#":
                    num_ht += 1
                    was_word = False
                elif t[0] == "@":
                    was_word = False
                else:
                    num_w += 1
                if was_word == True:
                    prev.append(t)
                    if len(prev) > num_grams:
                        prev.popleft()
                else:
                    prev.clear()
                if len(prev) > 0:
                    last = list(prev)
                    for n in range(len(last)):
                        gram = " ".join(last[:n+1])
                        cname = ngram_names[n]
                        counters[cname][gram] += 1
                        docx[cname].append(gram)
        all_doc = []
        for n in range(num_grams):
            cname = ngram_names[n]
            if n >= all_min:
                if len(docx[cname]) > 0:
                    for doc in docx[cname]:
                        all_doc.append(doc)
            if len(docx[cname]) >= min_tokens:
                twid_doc[cname][twid] = docx[cname]
        twid_doc["all"][twid] = all_doc

        num_images = 0
        if "image_urls" in d and d["image_urls"] is not None:
            num_images = len(d["image_urls"])

        if like_count > 50 and like_count < retweet_count*2:
            susp_twids.add(twid)
            suspicious = True
            counters["susp_users"][sn] += 1

        if num_images == 1 and num_w < 8 and num_ht >= 6:
            susp_twids.add(twid)
            suspicious = True
            counters["susp_users"][sn] += 1

        if num_w < 1 and num_ht >= 6:
            susp_twids.add(twid)
            suspicious = True
            counters["susp_users"][sn] += 1

        if "retweeted_status" in d:
            rsn = d["retweeted_status"]["user"]["screen_name"]
            sn_details[rsn] = d["retweeted_status"]["user"]
            counters["amplifiers"][sn] += 1
            counters["influencers"][rsn] += 1
            if "is_quote_status" in d and d["is_quote_status"] == True:
                quote = True
                quoted_twids.add(twid)
                counters["quoted"][rsn] += 1
                counters["quoters"][sn] += 1
                if sn not in sn_quo:
                    sn_quo[sn] = Counter()
                sn_quo[sn][rsn] += 1
                if rsn not in quo_sn:
                    quo_sn[rsn] = Counter()
                quo_sn[rsn][sn] += 1
            else:
                retweet = True
                text = d["retweeted_status"]["text"]
                rtwid = d["retweeted_status"]["id_str"]
                rretweet_count = d["retweeted_status"]["retweet_count"]
                url = "https://twitter.com/" + rsn + "/status/" + rtwid
                twid_rt_count[rtwid] += 1
                retweeted_twids.add(rtwid)
                if sn not in rsn_twid:
                    rsn_twid[sn] = []
                rsn_twid[sn].append(rtwid)
                if rtwid not in twid_rsn:
                    twid_rsn[rtwid] = []
                twid_rsn[rtwid].append(sn)
                if rsn not in retweeted_user_counts:
                    retweeted_user_counts[rsn] = Counter()
                retweeted_user_counts[rsn][timestamp] += 1
                if rtwid not in retweeted_twid_counts:
                    retweeted_twid_counts[rtwid] = Counter()
                retweeted_twid_counts[rtwid][timestamp] += 1
                counters["retweeted"][rsn] += 1
                counters["retweeters"][sn] += 1
                if sn not in sn_rsn:
                    sn_rsn[sn] = Counter()
                sn_rsn[sn][rsn] += 1
                if rsn not in rsn_sn:
                    rsn_sn[rsn] = Counter()
                rsn_sn[rsn][sn] += 1
                twid_count[rtwid] += 1
                twid_rtc[rtwid] = rretweet_count
                twid_text[rtwid] = text.replace("\n", "")
                twid_url[rtwid] = url
                if rtwid not in twid_sn:
                    twid_sn[rtwid] = Counter()
                twid_sn[rtwid][rsn] += 1
                if rsn not in sn_twid:
                    sn_twid[rsn] = Counter()
                sn_twid[rsn][rtwid] += 1

        if quote == True and num_w < 8 and num_ht >= 8:
            susp_twids.add(twid)
            suspicious = True
            counters["susp_users"][sn] += 1

        if "mentioned" in d and d["mentioned"] is not None:
            if len(d["mentioned"]) > 0:
                if sn not in sn_men:
                    sn_men[sn] = Counter()
                for m in d["mentioned"]:
                    if m not in men_sn:
                        men_sn[m] = Counter()
                    counters["mentioned"][m] += 1
                    counters["mentioners"][sn] += 1
                    sn_men[sn][m] += 1
                    men_sn[m][sn] += 1
                    counters["amplifiers"][sn] += 1
                    counters["influencers"][m] += 1

        if "in_reply_to_screen_name" in d and d["in_reply_to_screen_name"] is not None:
            reply = True
            replied_twids.add(twid)
            rep = d["in_reply_to_screen_name"]
            if sn not in sn_rep:
                sn_rep[sn] = Counter()
            sn_rep[sn][rep] += 1
            if rep not in rep_sn:
                rep_sn[rep] = Counter()
            rep_sn[rep][sn] += 1
            counters["replied_to"][rep] += 1
            counters["repliers"][sn] += 1
            counters["amplifiers"][sn] += 1
            counters["influencers"][rep] += 1

        if quote == False and retweet == False and reply == False:
            original = True
            orig_twids.add(twid)

        if original == True and suspicious == True:
            susp_orig_twids.add(twid)

        if "hashtags" in d:
            ht = d["hashtags"]
            if len(ht) > 0:
                if sn not in sn_hashtag:
                    sn_hashtag[sn] = Counter()
                for h in ht:
                    if h not in hashtag_counts:
                        hashtag_counts[h] = Counter()
                    hashtag_counts[h][timestamp] += 1
                    if h not in hashtag_twid:
                        hashtag_twid[h] = Counter()
                    hashtag_twid[h][twid] += 1
                    if h not in hashtag_sn:
                        hashtag_sn[h] = Counter()
                    hashtag_sn[h][sn] += 1
                    sn_hashtag[sn][h] += 1
                    counters["hashtags"][h] += 1

        if "urls" in d:
            urls = d["urls"]
            if len(urls) > 0:
                if sn not in sn_url:
                    sn_url[sn] = Counter()
                if sn not in sn_domain:
                    sn_domain[sn] = Counter()
                for u in urls:
                    match = re.match("https?\:\/\/w?w?w?\.?([a-z0-9]+\.[a-z]+\.?[a-z]*)\/.+$", u)
                    if match is not None:
                        domain = match.group(1)
                        if domain not in domain_twid:
                            domain_twid[domain] = Counter()
                        domain_twid[domain][twid] += 1
                        if domain not in domain_sn:
                            domain_sn[domain] = Counter()
                        domain_sn[domain][sn] += 1
                        sn_domain[sn][domain] += 1
                        if "twitter" not in domain:
                            counters["domains"][domain] += 1
                    if u not in url_twid:
                        url_twid[u] = Counter()
                    url_twid[u][twid] += 1
                    if u not in url_sn:
                        url_sn[u] = Counter()
                    url_sn[u][sn] += 1
                    sn_url[sn][u] += 1
                    if "twitter" not in u:
                        counters["urls"][u] += 1


    ts_data = counter_to_plot(timestamp_counts, "time")
    sn_ts_data = {}
    for sn, tsc in user_counts.items():
        total = 0
        for ts, c in tsc.items():
            total += c
        if total > 10:
            sn_ts_data[sn] = counter_to_plot(tsc, "time")
    hashtag_ts_data = {}
    for ht, tsc in hashtag_counts.items():
        total = 0
        for ts, c in tsc.items():
            total += c
        if total > 10:
            hashtag_ts_data[ht] = counter_to_plot(tsc, "time")
    rsn_ts_data = {}
    for sn, tsc in retweeted_user_counts.items():
        total = 0
        for ts, c in tsc.items():
            total += c
        if total > 10:
            rsn_ts_data[sn] = counter_to_plot(tsc, "time")
    rtwid_ts_data = {}
    for twid, tsc in retweeted_twid_counts.items():
        total = 0
        for ts, c in tsc.items():
            total += c
        if total > 10:
            rtwid_ts_data[twid] = counter_to_plot(tsc, "time")
    timespan = newest-oldest
    full = {}
    full["oldest"] = oldest
    full["newest"] = newest
    full["timespan"] = timespan
    full["user_fields"] = user_fields
    full["counters"] = counters
    full["sn_rsn"] = sn_rsn
    full["sn_rep"] = sn_rep
    full["sn_men"] = sn_men
    full["sn_quo"] = sn_quo
    full["rep_sn"] = rep_sn
    full["rsn_sn"] = rsn_sn
    full["men_sn"] = men_sn
    full["quo_sn"] = quo_sn
    full["twid_count"] = twid_count
    full["twid_rtc"] = twid_rtc
    full["twid_rt_count"] = twid_rt_count
    full["twid_text"] = twid_text
    full["twid_url"] = twid_url
    full["twid_sn"] = twid_sn
    full["twid_rsn"] = twid_rsn
    full["sn_twid"] = sn_twid
    full["rsn_twid"] = rsn_twid
    full["orig_twids"] = orig_twids
    full["susp_orig_twids"] = susp_orig_twids
    full["retweeted_twids"] = retweeted_twids
    full["replied_twids"] = replied_twids
    full["quoted_twids"] = quoted_twids
    full["hashtag_sn"] = hashtag_sn
    full["sn_hashtag"] = sn_hashtag
    full["domain_sn"] = domain_sn
    full["sn_domain"] = sn_domain
    full["sn_source"] = sn_source
    full["source_sn"] = source_sn
    full["domain_twid"] = domain_twid
    full["url_sn"] = url_sn
    full["sn_url"] = sn_url
    full["hashtag_twid"] = hashtag_twid
    full["url_twid"] = url_twid
    full["sn_details"] = sn_details
    full["ts_data"] = ts_data
    full["rsn_ts_data"] = rsn_ts_data
    full["rtwid_ts_data"] = rtwid_ts_data
    full["sn_ts_data"] = sn_ts_data
    full["hashtag_ts_data"] = hashtag_ts_data
    full["susp_twids"] = susp_twids

    print("Processed " + str(count) + " tweets.")
    print("Found " + str(len(counters["users"])) + " users.")
    print("Found " + str(len(counters["susp_users"])) + " susp_users.")
    print("Found " + str(len(counters["hashtags"])) + " hashtags.")
    print("Found " + str(len(counters["urls"])) + " urls.")
    print("Found " + str(len(counters["domains"])) + " domains.")
    print("Found " + str(len(counters["sources"])) + " sources.")
    print("Found " + str(len(counters["amplifiers"])) + " amplifiers.")
    print("Found " + str(len(counters["influencers"])) + " influencers.")
    print("Found " + str(len(counters["repliers"])) + " repliers.")
    print("Found " + str(len(counters["replied_to"])) + " replied_to.")
    print("Found " + str(len(counters["quoted"])) + " quoted.")
    print("Found " + str(len(counters["quoters"])) + " quoters.")
    print("Found " + str(len(counters["retweeted"])) + " retweeted.")
    print("Found " + str(len(counters["retweeters"])) + " retweeters.")
    print("Found " + str(len(counters["mentioned"])) + " mentioned.")
    print("Found " + str(len(counters["mentioners"])) + " mentioners.")
    print("Found " + str(len(orig_twids)) + " original tweets.")
    print("Found " + str(len(susp_twids)) + " suspicious tweets.")
    print("Found " + str(len(susp_orig_twids)) + " suspicious original tweets.")
    print("Found " + str(len(retweeted_twids)) + " retweets.")
    print("Found " + str(len(quoted_twids)) + " quote tweets.")
    print("Found " + str(len(replied_twids)) + " replies.")
    print("Found " + str(len(sn_details)) + " user details.")
    return full


# A simple routine for detecting obvious suspicious stuff:
# - very new accounts
# - new accounts with high number of tweets
# - egg accounts that are really old
# - accounts with loads of tweets and almost no followers
# - egg accounts with lots of followers
def get_susps(details):
    susp = set()
    for d in details:
        if d["verified"] == True:
            continue
        sn = d["screen_name"]
        desc = d["description"]
        egg = False
        if d["default_profile"] == True and d["default_profile_image"] == True:
            egg = True
        date = d["created_at"]
        year = date[-4:]
        if egg == True and len(desc) < 1:
            susp.add(sn)
        if year == "2019":
            susp.add(sn)
        if int(year) >= 2018 and d["statuses_count"] > 5000:
            susp.add(sn)
        if int(year) < 2015 and egg == True:
            susp.add(sn)
        if d["followers_count"] < 25 and d["statuses_count"] > 2000:
            susp.add(sn)
        if egg == True and d["statuses_count"] > 5000:
            susp.add(sn)
        if egg == True and d["followers_count"] > 1000:
            susp.add(sn)
    return susp

#####################################################################################
# Misc
#####################################################################################

# Breakdown of users by how much they tweet
def categorize_users(sn_counter, timespan_d):
    high_vol = timespan_d * 70
    med_vol = timespan_d * 30
    low_vol = timespan_d * 5
    utypes = ["high_volume", "medium_volume", "low_volume", "seen_once"]
    volumes = [high_vol, med_vol, low_vol, 1]
    tweet_cats = {}
    for t in utypes:
        tweet_cats[t] = 0
    for sn, c in sn_counter.most_common():
        for i in range(len(volumes)):
            l = utypes[i]
            if i < 1:
                if c > volumes[i]:
                    tweet_cats[l] += c
            elif i > 1 and i < len(volumes):
                if c > volumes[i] and c <= volumes[i-1]:
                    tweet_cats[l] += c
            else:
                if c <= volumes[i]:
                    tweet_cats[l] += c
    plot_data = {}
    plot_data["sizes"] = []
    for t in utypes:
        plot_data["sizes"].append(tweet_cats[t])
    plot_data["labels"] = utypes
    return plot_data

def get_mapping_overlaps(mapping, offset, num):
    counter = Counter()
    for item, ilist in mapping.items():
        for x, c in ilist.items():
            counter[item] += c
    top_items = [x for x, c in counter.most_common(num)][offset:]
    plot_data = {}
    for item in top_items:
        plot_data[item] = Counter()
        for iitem in top_items:
            if item == iitem:
                plot_data[item][iitem] = 0
            else:
                l1 = set([x for x, c in mapping[item].items()])
                l2 = set([x for x, c in mapping[iitem].items()])
                val = len(l1.intersection(l2))
                plot_data[item][iitem] = val
    return plot_data

def get_timestamps(num):
    current_unix = get_utc_unix_time()
    timestamps = []
    for _ in range(num):
        timestamp = datetime.fromtimestamp(int(current_unix)).strftime('%Y-%m-%d %H:00')
        timestamps.append(timestamp)
        current_unix -= 3600
    return timestamps

def get_timestamp_range(start, end):
    start_unix = int(datetime.strptime(start, "%Y-%m-%d %H:%M:%S").strftime("%s"))
    end_unix = int(datetime.strptime(end, "%Y-%m-%d %H:%M:%S").strftime("%s"))
    current_unix = end_unix
    timestamps = []
    while current_unix > start_unix:
        timestamp = datetime.fromtimestamp(int(current_unix)).strftime('%Y-%m-%d %H:00')
        timestamps.append(timestamp)
        current_unix -= 3600
    return timestamps

class Tweet(object):
    def __init__(self, s, embed_str=False):
        if not embed_str:
            # Use Twitter's oEmbed API
            # https://dev.twitter.com/web/embedded-tweets
            api = 'https://publish.twitter.com/oembed?url={}'.format(s)
            response = None
            try:
                response = requests.get(api)
            except:
                pass
            if response is not None:
                try:
                    self.text = response.json()["html"]
                except:
                    self.text = s
            else:
                self.text = s
        else:
            self.text = s

    def _repr_html_(self):
        return self.text

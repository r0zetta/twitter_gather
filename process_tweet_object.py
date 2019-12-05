from time_helpers import *
#from alphabet_detector import AlphabetDetector
import re

def get_mentioned(status):
    mentioned = []
    if "entities" in status:
        entities = status["entities"]
        if "user_mentions" in entities:
            for item in entities["user_mentions"]:
                if item is not None:
                    mention = item['screen_name']
                    if mention is not None:
                        if mention not in mentioned:
                            mentioned.append(mention)
    if len(mentioned) > 0:
        return mentioned

def get_quoted(status):
    if "quoted_status" in status:
        orig_tweet = status["quoted_status"]
        if "user" in orig_tweet:
            if orig_tweet["user"] is not None:
                user = orig_tweet["user"]
                if "screen_name" in user:
                    if user["screen_name"] is not None:
                            return user["screen_name"]

def get_retweeted_user_old(status):
    text = get_text(status)
    m = re.search("^RT\s+\@([^\:]+)\:\s+.+$", text)
    if m is not None:
        username = m.group(1)
        return username

def get_retweeted_status_old(status):
    text = get_text(status)
    m = re.search("^RT\s+\@[^\:]+\:\s+(.+)$", text)
    if m is not None:
        return m.group(1)

def is_old_retweet(status):
    if get_retweeted_user_old(status) is not None:
        return True
    return False

def get_retweeted_user(status):
    old_username = get_retweeted_user_old(status)
    new_username = None
    if "retweeted_status" in status:
        orig_tweet = status["retweeted_status"]
        new_username = get_screen_name(orig_tweet)
        if old_username is None:
            return new_username
    if new_username is None:
        return old_username
    if old_username != new_username:
        return old_username
    return new_username

def get_retweeted_tweet_time(status):
    if "retweeted_status" in status:
        orig_tweet = status["retweeted_status"]
        return get_tweet_created_at(orig_tweet)

def get_retweeted_tweet_id(status):
    if "retweeted_status" in status:
        orig_tweet = status["retweeted_status"]
        return get_tweet_id(orig_tweet)

def get_retweeted_status(status):
    old_rt_text = get_retweeted_status_old(status)
    new_rt_text = None
    if "retweeted_status" in status:
        orig_tweet = status["retweeted_status"]
        new_rt_text = get_text(orig_tweet)
        if old_rt_text is None:
            return new_rt_text
    if new_rt_text is None:
        return old_rt_text
    if old_rt_text != new_rt_text:
        return old_rt_text
    return new_rt_text

def get_retweeted_tweet_url(status):
    if "retweeted_status" in status:
        orig_tweet = status["retweeted_status"]
        screen_name = get_screen_name(orig_tweet)
        tweet_id = get_tweet_id(orig_tweet)
        if screen_name is not None and tweet_id is not None:
            url = "https://twitter.com/"+screen_name+"/status/"+tweet_id
            return url

def get_tweet_url(status):
    screen_name = get_screen_name(status)
    tweet_id = get_tweet_id(status)
    if screen_name is not None and tweet_id is not None:
        url = "https://twitter.com/"+screen_name+"/status/"+tweet_id
        return url

def get_replied(status):
    if "in_reply_to_screen_name" in status:
        if status["in_reply_to_screen_name"] is not None:
            return status["in_reply_to_screen_name"]

def get_interactions_preserve_case(status):
    interactions = set()
    screen_name = get_screen_name(status)
    if screen_name is None:
        return
    mentioned = get_mentioned(status)
    if mentioned is not None:
        for m in mentioned:
            interactions.add(m)
    quoted = get_quoted(status)
    if quoted is not None:
        interactions.add(quoted)
    retweeted = get_retweeted_user(status)
    if retweeted is not None:
        interactions.add(retweeted)
    replied = get_replied(status)
    if replied is not None:
        interactions.add(replied)
    return list(interactions)

def get_interactions(status):
    interactions = set()
    screen_name = get_screen_name(status)
    if screen_name is None:
        return
    mentioned = get_mentioned(status)
    if mentioned is not None:
        for m in mentioned:
            interactions.add(m)
    quoted = get_quoted(status)
    if quoted is not None:
        interactions.add(quoted)
    retweeted = get_retweeted_user(status)
    if retweeted is not None:
        interactions.add(retweeted)
    replied = get_replied(status)
    if replied is not None:
        interactions.add(replied)
    interactions = [x.lower() for x in interactions]
    return interactions

def get_hashtags_preserve_case(status):
    hashtags = []
    if "entities" in status:
        entities = status["entities"]
        if "hashtags" in entities:
            for item in entities["hashtags"]:
                if item is not None:
                    if "text" in item:
                        tag = item['text']
                        if tag is not None:
                            if tag not in hashtags:
                                hashtags.append(tag.lower())
    return hashtags

def get_coordinates(status):
    if "coordinates" in status:
        c = status["coordinates"]
        if c is not None and "coordinates" in c:
            return c["coordinates"]

def get_hashtags(status):
    hashtags = []
    if "entities" in status:
        entities = status["entities"]
        if "hashtags" in entities:
            for item in entities["hashtags"]:
                if item is not None:
                    if "text" in item:
                        tag = item['text']
                        if tag is not None:
                            if tag not in hashtags:
                                hashtags.append(tag.lower())
    hashtags = [x.lower() for x in hashtags]
    return hashtags

def get_urls(status):
    ret = []
    if "entities" in status:
        entities = status["entities"]
        if "urls" in entities:
            for item in entities["urls"]:
                if item is not None:
                    if "expanded_url" in item:
                        url = item['expanded_url']
                        if url is not None:
                            if url not in ret:
                                ret.append(url)
    return ret

def get_image_urls(status):
    ret = []
    if "entities" in status:
        entities = status["entities"]
        if "media" in entities:
            for item in entities["media"]:
                if item is not None:
                    if "media_url" in item:
                        url = item['media_url']
                        if url is not None:
                            if url not in ret:
                                ret.append(url)
    return ret

def get_text(status):
    text = None
    if "full_text" in status:
        text = status["full_text"]
    if text is None and "text" in status:
        text = status["text"]
    if text is not None:
        text = text.strip()
        text = re.sub("\n", " ", text)
    return text

def user_is_egg(user):
    if "default_profile" in user and user["default_profile"] is not None:
        if user["default_profile"] == False:
            return False
    if "default_profile_image" in user and user["default_profile_image"] is not None:
        if user["default_profile_image"] == False:
            return False
    return True

def user_get_user_created_at(user):
    if "created_at" in user:
        return user["created_at"]

def user_get_friends_count(user):
    if "friends_count" in user:
        return user["friends_count"]
    return 0

def user_get_followers_count(user):
    if "followers_count" in user:
        return user["followers_count"]
    return 0

def user_get_statuses_count(user):
    if "statuses_count" in user:
        return user["statuses_count"]
    return 0

def user_get_favourites_count(user):
    if "favourites_count" in user:
        return user["favourites_count"]
    return 0

def user_get_name(user):
    if "name" in user:
        return user["name"]

def user_get_screen_name(user):
    if "screen_name" in user:
        return user["screen_name"]

def user_get_id_str(user):
    if "id_str" in user:
        return user["id_str"]

def user_get_location(user):
    if "location" in user:
        return user["location"]

def user_get_description(user):
    if "description" in user:
        return user["description"]

def user_get_verified(user):
    if "verified" in user:
        return user["verified"]

def user_get_protected(user):
    if "protected" in user:
        return user["protected"]

def get_user_details_dict(user):
    details = {}
    detail_fields = ["id_str",
                     "screen_name",
                     "name",
                     "created_at",
                     "location",
                     "description",
                     "verified",
                     "protected",
                     "friends_count",
                     "followers_count",
                     "statuses_count",
                     "favourites_count"]
    for d in detail_fields:
        if d in user:
            details[d] = user[d]
        else:
            details[d] = "Unknown"
    return details

def get_user_details_list(user):
    details = []
    detail_fields = ["id_str",
                     "screen_name",
                     "name",
                     "created_at",
                     "location",
                     "description",
                     "verified",
                     "protected",
                     "friends_count",
                     "followers_count",
                     "statuses_count",
                     "favourites_count"]
    for d in detail_fields:
        if d in user:
            details.append(user[d])
        else:
            details.append("Unknown")
    return details

def is_egg(status):
    if "user" in status:
        user = status["user"]
        return user_is_egg(user)

def get_account_age_days(status):
    created_at = get_user_created_at(status)
    return seconds_to_days(seconds_since_twitter_time(created_at))

def get_user_created_at(status):
    if "user" in status:
        user = status["user"]
        return user_get_user_created_at(user)

def get_tweet_created_at(status):
    if "created_at" in status:
        return status["created_at"]

def get_screen_name(status):
    if "user" in status:
        user = status["user"]
        return user_get_screen_name(user)

def get_tweet_count(status):
    if "user" in status:
        user = status["user"]
        return user_get_statuses_count(user)

def get_tweets_per_day(status):
    ret = 0
    account_age_days = get_account_age_days(status)
    num_tweets = get_tweet_count(status)
    if account_age_days > 0 and num_tweets > 0:
        ret = account_age_days / float(num_tweets)
    return ret

def get_friends_count(status):
    if "user" in status:
        user = status["user"]
        return user_get_friends_count(user)

def get_profile_image_url(status):
    if "user" in status:
        user = status["user"]
        if "profile_image_url" in user:
            return user["profile_image_url"]

def get_tweet_id(status):
    if "id_str" in status:
        return status["id_str"]

def get_tweet_source(status):
    if "source" in status and status["source"] is not None:
        source_url = status["source"]
        m = re.search("^\<.+\>(.+)\<\/a\>$", source_url)
        if m is not None:
            source = m.group(1)
            return source

def get_user_id(status):
    if "user" in status:
        user = status["user"]
        return user_get_id_str(user)

def get_followers_count(status):
    if "user" in status:
        user = status["user"]
        return user_get_followers_count(user)

def is_new_account_bot(status):
    ret = False
    ad = AlphabetDetector()
    susp_score = 0
    egg = is_egg(status)
    if "user" not in status:
        return
    user = status["user"]
    sn = user["screen_name"]
    n = user["name"]
    bot_name = is_bot_name(sn)
    tweets = user["statuses_count"]
    friends = user["friends_count"]
    followers = user["followers_count"]
    created_at = user["created_at"]
    location = user["location"]
    time_obj = twitter_time_to_object(created_at)
    created_year = int(time_obj.strftime("%Y"))
    if egg == True:
        susp_score += 50
    if bot_name == True:
        susp_score += 100
    if created_year < 2017:
        susp_score -= 300
    if len(location) > 0:
        susp_score -= 150
    if len(sn) == 15:
        susp_score += 100
    if tweets == 0:
        susp_score += 50
    if tweets > 0:
        susp_score -= 50
    if tweets > 20:
        susp_score -= 100
    if friends == 21:
        susp_score += 100
    if friends == 0:
        susp_score += 50
    if friends != 21:
        susp_score -= 50
    if friends > 40:
        susp_score -= 100
    if friends > 100:
        susp_score -= 100
    if followers == 0:
        susp_score += 50
    if followers > 0:
        susp_score -= 200
    if len(n) < 3:
        susp_score += 100
    if ad.only_alphabet_chars(n, "CYRILLIC"):
        susp_score += 200
    if ad.only_alphabet_chars(n, "ARABIC"):
        susp_score += 200
    if ad.is_cjk(n):
        susp_score += 200
    if ad.only_alphabet_chars(n, "LATIN"):
        susp_score -= 100
    if susp_score > 0:
        return True
    else:
        return False

def is_bot_name(name):
    ret = True
    if re.search("^([A-Z]?[a-z]{1,})?[\_]?([A-Z]?[a-z]{1,})?[\_]?[0-9]{,9}$", name):
        ret = False
    if re.search("^[\_]{,3}[A-Z]{2,}[\_]{,3}$", name):
        ret = False
    if re.search("^[A-Z]{2}[a-z]{2,}$", name):
        ret = False
    if re.search("^([A-Z][a-z]{1,}){3}[0-9]?$", name):
        ret = False
    if re.search("^[A-Z]{1,}[a-z]{1,}[A-Z]{1,}$", name):
        ret = False
    if re.search("^[A-Z]{1,}[a-z]{1,}$", name):
        ret = False
    if re.search("^([A-Z]?[a-z]{1,}[\_]{1,}){1,}[A-Z]?[a-z]{1,}$", name):
        ret = False
    if re.search("^[A-Z]{1,}[a-z]{1,}[\_][A-Z][\_][A-Z]{1,}[a-z]{1,}$", name):
        ret = False
    if re.search("^[a-z]{1,}[A-Z][a-z]{1,}[A-Z][a-z]{1,}$", name):
        ret = False
    if re.search("^[A-Z][a-z]{1,}[A-Z][a-z]{1,}[A-Z]{1,}$", name):
        ret = False
    if re.search("^([A-Z][\_]){1,}[A-Z][a-z]{1,}$", name):
        ret = False
    if re.search("^[\_][A-Z][a-z]{1,}[\_][A-Z][a-z]{1,}[\_]?$", name):
        ret = False
    if re.search("^[A-Z][a-z]{1,}[\_][A-Z][\_][A-Z]$", name):
        ret = False
    if re.search("^[A-Z][a-z]{2,}[0-9][A-Z][a-z]{2,}$", name):
        ret = False
    if re.search("^[A-Z]{1,}[0-9]?$", name):
        ret = False
    if re.search("^[A-Z][a-z]{1,}[\_][A-Z]$", name):
        ret = False
    if re.search("^[A-Z][a-z]{1,}[A-Z]{2}[a-z]{1,}$", name):
        ret = False
    if re.search("^[\_]{1,}[a-z]{2,}[\_]{1,}$", name):
        ret = False
    if re.search("^[A-Z][a-z]{2,}[\_][A-Z][a-z]{2,}[\_][A-Z]$", name):
        ret = False
    if re.search("^[A-Z]?[a-z]{2,}[0-9]{2}[\_]?[A-Z]?[a-z]{2,}$", name):
        ret = False
    if re.search("^[A-Z][a-z]{2,}[A-Z]{1,}[0-9]{,2}$", name):
        ret = False
    if re.search("^[\_][A-Z][a-z]{2,}[A-Z][a-z]{2,}[\_]$", name):
        ret = False
    if re.search("^([A-Z][a-z]{1,}){2,}$", name):
        ret = False
    if re.search("^[A-Z][a-z]{2,}[\_][A-Z]{2}$", name):
        ret = False
    if re.search("^[a-z]{3,}[0-9][a-z]{3,}$", name):
        ret = False
    if re.search("^[a-z]{4,}[A-Z]{1,}$", name):
        ret = False
    if re.search("^[A-Z][a-z]{3,}[A-Z][0-9]{,9}$", name):
        ret = False
    if re.search("^[A-Z]{2,}[\_][A-Z][a-z]{3,}$", name):
        ret = False
    if re.search("^[A-Z][a-z]{3,}[A-Z]{1,3}[a-z]{3,}$", name):
        ret = False
    if re.search("^[A-Z]{3,}[a-z]{3,}[0-9]?$", name):
        ret = False
    if re.search("^[A-Z]?[a-z]{3,}[\_]+$", name):
        ret = False
    if re.search("^[A-Z][a-z]{3,}[\_][a-z]{3,}[\_][A-Za-z]{1,}$", name):
        ret = False
    if re.search("^[A-Z]{2,}[a-z]{3,}[A-Z][a-z]{3,}$", name):
        ret = False
    if re.search("^[A-Z][a-z]{2,}[A-Z][a-z]{3,}[\_]?[A-Z]{1,}$", name):
        ret = False
    if re.search("^[A-Z]{4,}[0-9]{2,9}$", name):
        ret = False
    if re.search("^[A-Z]{1,2}[a-z]{3,}[A-Z]{1,2}[a-z]{3,}[0-9]{1,9}$", name):
        ret = False
    if re.search("^[A-Z]+[a-z]{3,}[0-9]{1,9}$", name):
        ret = False
    if re.search("^([A-Z]?[a-z]{2,})+[0-9]{1,9}$", name):
        ret = False
    if re.search("^([A-Z]?[a-z]{2,})+\_?[a-z]+$", name):
        ret = False
    return ret


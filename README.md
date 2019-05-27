# twitter_gather
The latest version of my Twitter data collection and analysis tools. Consider all other stuff deprecated.

**Repeat: All other stuff is deprecated.**

# To use
- collect data with twitter_gatherer.py
- use gather_analysis_master.ipynb to analyze the collected data

# Set up valid API keys
First things first: you must create at least one key in the keys/ directory. There's an example file in there. Each key file can be named whatever you'd like. Each key file looks like this:

```
email=email.address@emailaddress.com
owner=twitter_handle
name=Twitter Name
owner_id=numeric_twitter_id
consumer_key=key_data
consumer_secret=key_data
access_token=key_data
access_token_secret=key_data
```

You don't have to fill out every field - just the last four, plus the owner field. The owner field can be whatever you'd like - its just a tag that will let you know which account the script is using if you have multiple keys available.

---
# How to use twitter_gatherer.py
_twitter_gatherer.py_ is best used to collect either a stream, or to listen to accounts.

* To listen to a stream, edit _targets.txt_ in the config directory to include all the search terms you wish to collect on (one per line), and then just run _twitter_gatherer.py_ with no command-line options.
* To listen to accounts, gather a list of the accounts' Twitter IDs, and write a file - _followid.txt_ under the config directory that contains one account ID per line. Then run _twitter_gatherer.py followid_

To convert screen_names into account IDs you can use _resolve_sns.ipynb_. Save the list of screen_names in a text file with one screen_name per line. Then edit resolve_sns.ipynb as appropriate to point to the file. It will attempt to resolve all of the screen_names and output details for each account resolved, and a text file of account IDs compatible with _twitter_gatherer.py_'s followid. Alternatively, use the approach detailed in the next paragraph, and copy-paste the IDs printed at the command line when _twitter_gatherer.py_ runs.

Note, you can also follow accounts by their screen_names. Create a file called follow.txt under the config directory. Write the screen_names to the file, one name per line. Then call _twitter_gatherer.py follow_
This will work fine, until accounts get renamed. Hence using id_strs is recommended.

All collected Twitter objects are abbreviated (see the source code for what is collected) and saved sequentially to data/raw.json as long as _twitter_gatherer.py_ is running. You may open _gatherer_analysis_master.ipynb_ at any time and load the data, as it is being collected.

---
# How to use gatherer_analysis_master.ipynb
gatherer_analysis_master.ipynb creates a directory named analysis_live, where it stores all processed metadata. You can use files such as _retweet_interactions.csv_ created under _analysis_live/_ to create gephi visualizations. 

_gatherer_analysis_master.ipynb_ is pretty self-explanatory. Early cells contain variables that can be set to dictate which time period the analysis runs on. Later, analyses are performed on lists of hashtags/domains/screen_names. These can be replaced with manually entered lists for targeted analysis.

---
# How to use twitter_user_analysis.ipynb
Use twitter_user_analysis.ipynb to analyze a single Twitter account. Edit the target field in the notebook to change the account analyzed. Each time it is run, it will create a directory with the _screen_name_ of the user queried under the _user_analysis/_ directory. It stores downloaded data in this directory. If you want to re-run a user analysis with updated information, delete or rename the relevant directory.

---
# Y NO twitter_no_rl_tool.py?
The _twitter_no_rl_tool.py_ file is not included in this repo. It is my own "proprietary technology" tool for gathering twitter user objects and for iterating followers and friends of Twitter accounts. If you need to replicate its behavior, it is entirely possible with tweepy/twarc/TwitterAPI.

_resolve_sns_no_save()_ simply takes a list of screen_names as input and returns a list of user objects
_get_follower_data_sn()_ and _get_friends_data_sn()_ take a screen_name as input and return a list of user objects (either followers or friends)

Example code (which I didn't test, and probably doesn't run - it's just a suggestion for code based on TwitterAPI that may work).

```python
from TwitterAPI import TwitterAPI
import time, json, time

consumer_key=""
consumer_secret=""
access_token=""
access_token_secret=""

def get_follower_data_sn(target):
    auth = TwitterAPI(consumer_key, consumer_secret, access_token, access_token_secret)
    follower_info = []
    cursor =  -1
    count = 0
    while True:
        followers_raw = auth.request('followers/list', {'screen_name': target, 
                                                        'count': 200, 
                                                        'cursor':cursor, 
                                                        'skip_status':True, 
                                                        'include_user_entities': False})
        followers_clean = json.loads(followers_raw.response.text)
        if "next_cursor" in followers_clean and followers_clean["next_cursor"] > 0:
            cursor = followers_clean['next_cursor']
            for follower in followers_clean["users"]:
                entry = {}
                fields = ["id_str", "name", "description", "screen_name", "followers_count", "friends_count", "statuses_count", "created_at", "favourites_count", "default_profile", "default_profile_image", "protected", "verified"]
                for field in fields:
                    if field in follower:
                        entry[field] = follower[field]
                follower_info.append(entry)
                count += 1
        else:
            if "errors" in followers_clean:
                for e in followers_clean["errors"]:
                    if "code" in e:
                        if e["code"] == 88:
                            print("Rate limit exceeded.")
                            time.sleep(900)
            else:
                print("Done. Found " + str(count) + " followers.")
                break
    return follower_info

def get_friends_data_sn(target):
    auth = TwitterAPI(consumer_key, consumer_secret, access_token, access_token_secret)
    friends_info = []
    cursor =  -1
    count = 0
    while True:
        friends_raw = auth.request('friends/list', {'screen_name': target, 
                                                    'count': 200, 
                                                    'cursor':cursor, 
                                                    'skip_status':True, 
                                                    'include_user_entities': False})
        friends_clean = json.loads(friends_raw.response.text)
        if "next_cursor" in friends_clean and friends_clean["next_cursor"] > 0:
            cursor = friends_clean['next_cursor']
            for friend in friends_clean["users"]:
                entry = {}
                fields = ["id_str", "name", "description", "screen_name", "followers_count", "friends_count", "statuses_count", "created_at", "favourites_count", "default_profile", "default_profile_image", "protected", "verified"]
                for field in fields:
                    if field in friend:
                        entry[field] = friend[field]
                friends_info.append(entry)
                count += 1
        else:
            if "errors" in friends_clean:
                for e in friends_clean["errors"]:
                    if "code" in e:
                        if e["code"] == 88:
                            print("Rate limit exceeded.")
                            time.sleep(900)
            else:
                print("Done. Found " + str(count) + " friends.")
                break
    return friends_info

def resolve_sns_no_save(sn_list):
    if len(sn_list) < 1:
        print("No users provided.")
        return
    print("Getting details on " + str(len(sn_list)) + " users.")
    batch_len = 100
    num_batches = int(len(sn_list)/batch_len)
    batches = (sn_list[i:i+batch_len] for i in range(0, len(sn_list), batch_len))
    auth = TwitterAPI(consumer_key, consumer_secret, access_token, access_token_secret)
    info = []
    count = 0
    for b in batches:
        data_raw = auth.request('users/lookup', {'screen_name': b})
        while True:
            data_clean = json.loads(data_raw.response.text)
            if "next_cursor" in data_clean and data_clean["next_cursor"] > 0:
                cursor = data_clean['next_cursor']
                for data in data_clean["users"]:
                    entry = {}
                    fields = ["id_str", "name", "description", "screen_name", "followers_count", "friends_count", "statuses_count", "created_at", "favourites_count", "default_profile", "default_profile_image", "protected", "verified"]
                    for field in fields:
                        if field in data and data[field] is not None:
                            entry[field] = data[field]
                    info.append(entry)
                    count += 1
            else:
                if "errors" in data_clean:
                    for e in data_clean["errors"]:
                        if "code" in e:
                            if e["code"] == 88:
                                print("Rate limit exceeded.")
                                countdown_timer(900)
                else:
                    print("Done. Found " + str(count) + " objects.")
                    break
    return info

t = "target_screen_name"

sn_list = set()

followers = get_follower_data_sn(t)
for d in followers:
    sn_list.add(d["screen_name"])
    if d["default_profile"] == True and d["default_profile_image"] == True:
        print(d["screen_name"] + " is an EGG!")

friends = get_friends_data_sn(t)
for d in friends:
    sn_list.add(d["screen_name"])
    if d["default_profile"] == True and d["default_profile_image"] == True:
        print(d["screen_name"] + " is an EGG!")

details = resolve_sns_no_save(list(sn_list))
for d in details:
    if d["default_profile"] == True and d["default_profile_image"] == True:
        print(d["screen_name"] + " is an EGG!")
```

I wrote the above code in this README. It might or might not work. But you get the idea.

You can also find various (slightly old) blog posts on Twitter collection methods here (https://labsblog.f-secure.com/author/andypatelfs/)

# Why is the code in your jupyter notebooks so copy-paste?
Most of the code was written in a hurry, while researching recent Twitter trends and topics. I guess that's the life of a disinfo researcher. I'm working on refactoring the code that's there, but I'm doing other stuff at the moment, and don't have time. Yeah, I agree that it's terrible to look at.

Refactoring will happen soon(tm). No need for PRs.

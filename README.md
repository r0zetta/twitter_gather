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

You don't have to fill out every field - just the last five. The owner_id field can be whatever you'd like - its just a tag that will let you know which account the script is using if you have multiple keys available.

---
# How to use twitter_gatherer.py

_twitter_gatherer.py_ is best used to collect either a stream, or to listen to accounts.

* To listen to a stream, edit targets.txt in the config directory to include all the search terms you wish to collect on (one per line), and then just run twitter_gatherer.py with no command-line options.
* To listen to accounts, gather a list of the accounts' Twitter IDs, and write a file - followid.txt under the config directory that contains one account ID per line. Then run _twitter_gatherer.py followid_

To convert screen_names into account IDs you can use resolve_sns.ipynb. Save the list of screen_names in a text file with one screen_name per line. Then edit resolve_sns.ipynb as appropriate to point to the file. It will attempt to resolve all of the screen_names and output details for each account resolved, and a text file of account IDs compatible with twitter_gatherer.py's followid. Alternatively, use the approach detailed in the next paragraph, and copy-paste the IDs printed at the command line when twitter_gatherer.py runs.

Note, you can also follow accounts by their screen_names. Create a file called follow.txt under the config directory. Write the screen_names to the file, one name per line. Then call _twitter_gatherer.py follow_
This will work fine, until accounts get renamed. Hence using id_strs is recommended.

All collected Twitter objects are abbreviated (see the source code for what is collected) and saved sequentially to data/raw.json as long as twitter_gatherer.py is running. You may open gatherer_analysis_master.ipynb at any time and load the data, as it is being collected.

gatherer_analysis_master.ipynb is pretty self-explanatory. Early cells contain variables that can be set to dictate which time period the analysis runs on. Later, analyses are performed on lists of hashtags/domains/screen_names. These can be replaced with manually entered lists for targeted analysis.

gatherer_analysis_master.ipynb creates a directory named analysis_live, where it stores all processed metadata. You can use files such as retweet_interactions.csv created under analysis_live to create gephi visualizations. 

Use twitter_user_analysis.ipynb to analyze a single Twitter account. Each time it is run, it will create a directory with the screen_name of the user queried under user_analysis. It stores downloaded data in this directory. If you want to re-run a user analysis, delete or rename the relevant directory.


# twitter_gather
The latest version of my Twitter data collection and analysis tools. Consider all other stuff deprecated.

All other stuff is deprecated.

To use:
- collect data with twitter_gatherer.py
- use gather_analysis_master.ipynb to analyze the collected data

Collecting data:

twitter_gatherer.py is best used to collect either a stream, or to listen to accounts.

To listen to a stream, edit targets.txt in the config directory to include all the search terms you wish to collect on (one per line), and then just run twitter_gatherer.py with no command-line options.
To listen to accounts, gather a list of the accounts' Twitter IDs, and write a file - followid.txt under the config directory that contains one account ID per line. Then run twitter_gatherer.py followid

All collected Twitter objects are abbreviated (see the source code for what is collected) and saved sequentially to data/raw.json as long as twitter_gatherer.py is running. You may open gatherer_analysis_master.ipynb at any time and load the data, as it is being collected.

gatherer_analysis_master.ipynb is pretty self-explanatory. Early cells contain variables that can be set to dictate which time period the analysis runs on. Later, analyses are performed on lists of hashtags/domains/screen_names. These can be replaced with manually entered lists for targeted analysis.

gatherer_analysis_master.ipynb creates a directory named analysis_live, where it stores all processed metadata. You can use files such as retweet_interactions.csv created under analysis_live to create gephi visualizations. 

Use twitter_user_analysis.ipynb to analyze a single Twitter account. Each time it is run, it will create a directory with the screen_name of the user queried under user_analysis. It stores downloaded data in this directory. If you want to re-run a user analysis, delete or rename the relevant directory.


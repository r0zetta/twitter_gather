# twitter_gather
The latest version of my Twitter data collection and analysis tools

All other stuff is deprecated.

To use:
- collect data with twitter_gatherer.py
- use gather_analysis_master.ipynb to analyze the collected data

Collecting data:

twitter_gatherer.py is best used to collect either a stream, or to listen to accounts.

To listen to a stream, edit targets.txt in the config directory to include all the search terms you wish to collect on (one per line), and then just run twitter_gatherer.py with no command-line options.
To listen to accounts, gather a list of the accounts' Twitter IDs, and write a file - followid.txt under the config directory that contains one account ID per line. Then run twitter_gatherer.py followid

All collected Twitter objects are abbreviated (see the source code for what is collected) and saved sequentially to data/raw.json as long as twitter_gatherer.py is running. You may open gatherer_analysis_master.json at any time and load the data, as it is being collected.

Use twitter_user_analysis.ipynb to analyze a single Twitter account.


# GetSocialNetwork
![getsocialnetwork](https://cloud.githubusercontent.com/assets/14153294/10562118/923f4574-74ff-11e5-8288-c93f1d34c08e.jpg)

## A framework to get data from social network. Python 2.7.10. Data: 17.10.15

Currently the supported platform is LinkedIn. The app supports only English language.

Usage:
```
# import necessary libraries. No external libs needed.
from linkedInStats import LinkedInStats
from socialNetwork import LinkedIn
import utils

# initiazlie LinkedInStats class to login into the network.
lstats = LinkedInStats('example@example.com', 'password')

# first we need to create the database of all connections
dataBase, errorProfiles = lstats.createDataBase(-1,4)

# than we can call other methods which will operate on the created database file
lstats.workOverTime(2008,2015)
lstats.experienceStats()
lstats.locationStats()
lstats.companyStats()
lstats.workStats()
```
The getSocialNetwork.py has data scraping methods. The recursive methods getProfileConnections() and getAllConnections() should be used with care! The overuse and abuse of the recursive methods getProfileConnections() and getAllConnections() may cause issues with LinkedIn. 

Usage:
```
# initialize the class.
link = LinkedIn('example@example.com','password')
# Get profile data by specifying name and lastname.
profileData = l.getProfileData('Name','Lastname')
```


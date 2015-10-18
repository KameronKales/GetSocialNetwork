# GetSocialNetwork
![getsocialnetwork](https://cloud.githubusercontent.com/assets/14153294/10562118/923f4574-74ff-11e5-8288-c93f1d34c08e.jpg)

## A framework to get data from social network. Python 2.7.10. Data: 17.10.15

Currently the supported platform is LinkedIn. The framework supports only English language.

Usage:
```
# import all project libraries.
from linkedInStats import LinkedInStats
from socialNetwork import LinkedIn
import utils

# initiazlie LinkedInStats class to login into the network.
lstats = LinkedInStats('example@example.com', 'password')

# first we need to create the database of all connections
dataBase, errorProfiles = lstats.createDataBase(-1,4)

# than we can call other methods which output txt file stats.
lstats.workOverTime(2008,2015)
lstats.experienceStats()
lstats.locationStats()
lstats.companyStats()
lstats.workStats()
```
The getSocialNetwork.py has data scraping methods. 

Usage:
```
# initialize the class.
link = LinkedIn('example@example.com','password')
# Get profile data by specifying name and lastname.
profileData = l.getProfileData('Name','Lastname')
```
### The txt files created by LinkedInStats methods can be easily graphed in Excel.
![mystats](https://cloud.githubusercontent.com/assets/14153294/10562266/f5312988-7507-11e5-84eb-dcaa8efcf5a2.jpg)

Known bugs and restrictions.

1. Sometimes, regex expressions do not grab the proper information. This results in minor inaccuracies in stats.
2. Languages other than English are not supported. Thus, the profiles which use other languages may cause errors.
3. The speed of scraping is deliberately limited, so LinkedIn don't think it is a bad bot.
4. The recursive methods getProfileConnections and getAllConnections should be used with care! 
5. The overuse and abuse of getProfileConnections and getAllConnections may cause issues with LinkedIn. 


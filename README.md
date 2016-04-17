# GetSocialNetwork
![getsocialnetwork](https://cloud.githubusercontent.com/assets/14153294/10562118/923f4574-74ff-11e5-8288-c93f1d34c08e.jpg)

## A framework to get data from a social network. Python 2.7.10 

Currently the supported platform is LinkedIn. The framework supports only English language. The module doesn't need any external libs. Case study on my blog: http://renderstory.com/linkedinstats/

Usage:
```
# Quick start:
# Create a file in the module directory and type in this code
# import all project libraries.

from linkedInStats import LinkedInStats
from socialNetwork import LinkedIn

# initiazlie LinkedInStats class to login into the network.
lstats = LinkedInStats('example@example.com', 'password')

# first we need to create the database of all connections. 
# The framework will download all contacts' profile pages to the local drive for further processing
# Once the download is over, you'll get a dataBase.json file which will contain various entries about 1st level contacts.
dataBase, errorProfiles = lstats.createDataBase(-1,4)

# then we can call other methods which output txt file stats in the root of the module.
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
profileData = l.get2ndConnections('Name','Lastname','fileDir')
```

#### The txt files created by LinkedInStats methods can be easily graphed in Excel.
![mystats](https://cloud.githubusercontent.com/assets/14153294/10562266/f5312988-7507-11e5-84eb-dcaa8efcf5a2.jpg)

![program pipeline](https://cloud.githubusercontent.com/assets/14153294/10562390/fe240676-750e-11e5-98f1-3e215bb137f4.jpg)

Known bugs and restrictions.
0. Since LinkedIn periodically updates its website api and html content some of GetSocialNetwork features might not work
1. Sometimes, regex expressions do not grab the proper information. This results in minor inaccuracies in stats.
2. Languages other than English are not supported. Thus, the profiles which use other languages may cause errors.
3. The speed of scraping is deliberately limited, so LinkedIn doesn't think it is a bad bot.
4. The recursive methods getProfileConnections and getAllConnections should be used with care! 
5. The overuse and abuse of getProfileConnections and getAllConnections may cause issues with LinkedIn. 


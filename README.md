# GetSocialNetwork
![getsocialnetwork](https://cloud.githubusercontent.com/assets/14153294/10562118/923f4574-74ff-11e5-8288-c93f1d34c08e.jpg)

## A framework to get data from social network. Currently the supported platform is LinkedIn. The app supports only English language.

Usage:
```
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


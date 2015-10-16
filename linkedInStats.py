import json, pprint, unicodedata, os
from socialNetwork import LinkedIn


class LinkedInStats(object):
    """ A class which outputs all the data as a .txt file for future use in Microsoft Excel app. """
    def __init__(self, login, password):

        self.link = LinkedIn(login, password)
        self.selfDir = os.path.dirname(__file__)
        self.allData = None

        self.companyStatsDir = os.path.join(self.selfDir, "companies stats.txt")
        self.countriesStatDir = os.path.join(self.selfDir, "countries stats.txt")
        self.positionStats = os.path.join(self.selfDir, "position stats.txt")
        self.dataBase = os.path.join(self.selfDir, "dataBase.json")


    def createDataBase(self, numberProfiles=-1, sleepTime=4):
        """
        This method goes through each profile in your connections and gets all the public
        data necessary for further statistics.The method uses time.sleep call, so betwee each
        profile query there is a user defined pause. By default the pause lasts 4 seconds.
        """
        self.allData, errorProfiles = self.link.getAllData(self.dataBase, numberProfiles, sleepTime)
        return self.allData, errorProfiles


    def companyStats(self):
        """ A function outputs a .txt file with a list of companies and people working in them. """
        companies_people =  self.link.getPeopleAtCompanies()
        all_companies = float(len(companies_people))
        d = {}

        for company in companies_people:
            accurance = len(companies_people[company])
            d[company] = accurance

        with open(self.companyStatsDir,'w') as f:
            f.write("total companies in profile: %s\n" %(all_companies))
            f.write("\n")
            f.write('company name and the number of people working at the company\n')
            f.write("\n")
            for company, value in sorted(d.items(),key=lambda x: x[1], reverse=True):
                names = companies_people[company]
                company = company[3:]
                self._write(f,company,value,names)


    def quickLocationStats(self):
        """
        A quick method which outputs a .txt file with countries and number of people living in the countries.
        If you profile friend didn't specify his postal code this method won't resolve the location. For Full
        location stats use locationStats() method.
        """
        locations = self.link.getCountries()
        totalLocations = len(locations)
        countryCount = {}
        globalCount = 0

        for country in locations:
            count = 0

            for city in locations[country]:
                size = len(locations[country][city])
                count+=size
            countryCount[country] = count
            globalCount+=count

        with open(self.countriesStatDir,'w') as f:
            f.write("total locations in profile: %s\n" %(totalLocations))
            f.write("\n")
            for country, cities in sorted(locations.items(), key = lambda x:len(x[1]), reverse=True):
                self._write(f, country, countryCount[country], cities)

            f.write('\n')


    def workStats(self):
        """ A function which sorts the job titles into a list of positions and outputs a .txt file. """
        positionCount = {}
        positions = self.link.getPosition()

        for position in positions:
            count = len(positions[position])
            positionCount[position] = count

        with open(self.positionStats,'w') as f:
            for position in positions:
                self._write(f, position, positionCount[position], positions[position])


    def locationStats(self):
        """
        A funtion iterates through a dictionary of profiles and reads the values. The dictionary file
        must be created using the method getConnectionsData().
        """
        profilesData = {}
        countries = {}
        countryCount = {}

        if not os.path.exists(self.dataBase):
            raise IOError('##### This method needs a database. Run getConnectionsData() method first to create the database.')

        with open(self.dataBase,'r') as f:
            profilesData = json.load(f)

        for profile in profilesData:
            country =  profilesData[profile]['country']

            if country in countries:
                countries[country].append(profile)

            else:
                countries[country] = [profile]

        for country in countries:
            count = len(countries[country])
            countryCount[country] = count

        with open(self.countriesStatDir,'w') as f:
            f.write("total locations in profile: %s\n" %(len(countries) ) )
            f.write("\n")
            for country in sorted(countries, key = lambda x:countryCount[x], reverse=True):
                self._write(f, country, countryCount[country], countries[country])

            f.write('\n')


    @staticmethod
    def _write(fileName,*args):
        flatList = []

        for arg in args:
            if hasattr(arg,'__iter__'):
                flatList.extend(arg)
            else:
                flatList.append(arg)
        newList =  []

        for item in flatList:
            if not item: continue
            if not isinstance(item, int) and not isinstance(item, str):
                item = unicodedata.normalize('NFKD', item).encode('ascii', 'ignore')

            newList.append(item)

        flatList = newList
        title = str(flatList[0])+":"
        stringValue = ', '.join(map(str,flatList[1:]))
        fileName.write(title+' '+stringValue+'\n')

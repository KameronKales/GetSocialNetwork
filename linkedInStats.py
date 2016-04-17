import json, pprint, unicodedata, os, utils
from socialNetwork import LinkedIn


class LinkedInStats(object):
    """ A class which outputs all the data as a .txt file for future use in Microsoft Excel app. """
    def __init__(self, login, password):

        self.link = LinkedIn(login, password)
        self.selfDir = os.path.dirname(__file__)
        self.outputDir = 'output'

        if not os.path.exists('output'):
            os.makedirs('output')

        self.companyStatsDir = os.path.join(self.outputDir, "companies stats.txt")
        self.countriesStatDir = os.path.join(self.outputDir, "countries stats.txt")
        self.positionStatsDir = os.path.join(self.outputDir, "position stats.txt")
        self.workOverTimeStatsDir = os.path.join(self.outputDir, "work time stats.txt")
        self.expYearsDir = os.path.join(self.outputDir, "exp years stats.txt")
        self.dataBaseDir = os.path.join(self.outputDir, "dataBaseDir.json")


    def createDataBase(self, numberProfiles=-1, sleepTime=1):
        """
        This method will download all the contacts' profile html pages to the local drive and parse
        them to create a json dataBaseDir. The method uses time intervals.
        """
        # Download pages to th local drive
        self.link.downloadContactPages(sleepTime)
        # Parse all the downloaded pages
        data, errorProfiles = self.link.getAllContatcsData(self.dataBaseDir, numberProfiles, sleepTime)
        return data, errorProfiles


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

        with open(self.positionStatsDir,'w') as f:
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

        if not os.path.exists(self.dataBaseDir):
            raise IOError('##### This method needs a dataBaseDir. Run getConnectionsData() method first to create the dataBaseDir.')

        with open(self.dataBaseDir,'r') as f:
            profilesData = json.load(f)

        for profile in profilesData:
            location =  profilesData[profile]['linkedInLocation']

            country, city = self.link._getCountryByCity(location)

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

    def workOverTime(self, istartYear, iendYear):
        """ The method displays how many people swtiched their jobs during the user specified period."""
        if not isinstance(istartYear, int) or not isinstance(iendYear, int):
            raise TypeError('{} or {} is not integer.'.format(startYear, endYear) )
        totalPeople = []
        period = [year for year in xrange(istartYear, iendYear+1)]
        workTimeStats = {}

        for year in period:
            workTimeStats[str(year)]=[]

        with open(self.dataBaseDir, 'r') as f:
            dataBaseDir = json.load(f)

        for profile in dataBaseDir:
            startCareer = []
            workExp = dataBaseDir[profile]['workExp']
            tressholdYear = False
            for company in workExp:
                startYear = utils.findInteger(workExp[company]['start'])
                startCareer.append(startYear)

                for careerYear in startCareer:
                    if careerYear <= istartYear:
                        tressholdYear = True
                        break

                if startYear in period and tressholdYear == True:
                    workTimeStats[str(startYear)].append(profile)

        for year in workTimeStats:

            for profile in workTimeStats[year]:

                if not profile in totalPeople:
                    totalPeople.append(profile)

        with open(self.workOverTimeStatsDir, 'w') as f:
            self._write(f,'total people', len(totalPeople) )
            for year in sorted(workTimeStats, key=lambda x: int(x) ):
                count = len(workTimeStats[year])
                self._write(f, year, count, workTimeStats[year] )

    #
    def experienceStats(self):
        """ The method sorts profiles according to their experience and outputs the results as txt file. """
        otherExp = []
        experience = {'under 5 years': [], 'under 10 years': [], 'under 15 years': [], 'under 20 years': [], 'under 30 years': [], 'over 30 years': []}
        count = 0
        with open(self.dataBaseDir, 'r') as f:
            dataBaseDir = json.load(f)

        for profile in dataBaseDir:
            years = utils.WorkTime(0,0)

            for company in dataBaseDir[profile]['workExp']:
                duration = dataBaseDir[profile]['workExp'][company]['duration']

                if not duration: continue

                year, month = utils.convertDuration(duration)
                years += utils.WorkTime(year, month)

            allYears, allMonths =  years.getTimeInteger()

            if allYears >= 1 and allYears < 5:
                experience['under 5 years'].append(profile)

            elif allYears >= 5 and allYears < 10:
                experience['under 10 years'].append(profile)

            elif allYears >= 10 and allYears < 15:
                experience['under 15 years'].append(profile)

            elif allYears >= 15 and allYears < 20:
                experience['under 20 years'].append(profile)

            elif allYears >= 20 and allYears < 30:
                experience['under 30 years'].append(profile)

            elif allYears >= 30:
                experience['over 30 years'].append(profile)
            else:
                otherExp.append(profile)

        with open(self.expYearsDir, 'w') as f:
            for exp in experience:
                self._write(f, exp, len(experience[exp]), experience[exp])

            self._write(f,'unknown', len(otherExp), otherExp)


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

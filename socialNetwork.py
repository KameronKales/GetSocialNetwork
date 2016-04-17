import urllib, urllib2, cookielib, re, json, math, os, sys, time, random
from pprint import pprint
import unicodedata


class SocialNetwork(object):
    """A base class to login and load pages."""
    def __init__(self, login, password, startURL, loginURL):
        self.login = login
        self.password = password
        self.cookieJar = cookielib.CookieJar()
        self.handler_list = [
            urllib2.HTTPCookieProcessor(self.cookieJar),
            urllib2.HTTPHandler(),
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPSHandler()
            ]
        self.header = [('User-Agent',('(Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36)'))]
        self.opener = urllib2.build_opener(*self.handler_list)
        self.opener.addheaders = self.header
        self.start_url = startURL
        self.login_url = loginURL


    def loadPage(self, url, data = None, tryAgain = 2):
        """Rquest and html page"""
        if tryAgain <= 0:
            raise IOError('{} {} is not accesable.'.format(url, data) )

        tryAgain-=1
        try:
            if data is not None:
                data = urllib.urlencode(data)
                response = self.opener.open(url, data)

            else:
                response = self.opener.open(url)

            return str(response.read())

        except:
            self.loadPage(url, data, tryAgain)


    def loginPage(self):
        """Starts with the homepage to obtain the csrf, once its done logins using login, pass and csrf."""
        loginPage = self.loadPage(self.start_url)
        csrfMatch = re.compile(r'(?<=id="loginCsrfParam-login" type="hidden" value=")[A-z,0-9,-]+')
        csrf = csrfMatch.search(loginPage).group()
        loginData = {'session_key'      : self.login,
                     'session_password' : self.password,
                     'loginCsrfParam'   : csrf }

        homePage = self.loadPage(self.login_url, loginData)

        return homePage


class LinkedIn(SocialNetwork):
    """The class that logins and reads a user's profile connection data."""
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.startURL = "https://www.linkedin.com/"
        self.loginURL = "https://www.linkedin.com/uas/login-submit"
        self.conUrl = "https://www.linkedin.com/contacts/api/contacts/?"
        self.conUrl2 = "https://www.linkedin.com/connected/api/v2/contacts?"
        super(LinkedIn, self).__init__(self.login, self.password, self.startURL, self.loginURL)
        self.homePage = self.loginPage()
        self.countryDict = self.loadCountryDict()
        self.numCon = self.getNumCons()
        self.conUrls = self.getAllContacsJson()     # api2 json file which contains urls and all contacts info
        self.conData = self.getConnections()        # api1 json file contains contatcs info but no urls
        self.currentPath = os.path.dirname(os.path.abspath(__file__))
        self.profilePages =  'profilesPages/'


    def getNumCons(self):
        """Parse the user's web page and get the number of connections"""
        numCon = re.search(r'\"numConnections\":\d+', self.homePage)
        number = numCon.group().split(':')[1]
        return number

    def _getCountryByCity(self, location):
        """A helper function which finds countires by an area or city."""
        city = None
        country = None
        location =  location.split(',')

        if len(location) == 3:
            city = location[1]
            city = re.sub(r'[ ](?=[A-z,0-9])','', city, 1)

        else:
            city = location[0]

        city = re.sub(" Area", '', city)
        city = re.sub(" Region", '', city)
        city = re.sub(" Metropolitan", '', city)
        city = re.sub(" Bay", '', city)
        city = re.sub("Greater ", '', city)
        city = re.sub(r" \(\w+\)", '', city) # takes out everything that is inside ().
        city = re.sub(r'\/[A-z ]*', '', city) # takes out everything that comes after /.
        # print city
        for dictCountry in self.countryDict:
            for dictCity in self.countryDict[dictCountry]:
                cityMatch = re.compile(dictCity)
                match = cityMatch.match(city)

                if match:
                    match = match.group()
                    if len(match) == len(city):
                        country = dictCountry
                        # print country
                        return country, city
        else:
            return 'Unresolved place', city


    def loadCountryDict(self):
        script_dir = os.path.dirname(__file__)
        file_dir = 'countryCity.json'
        absolute_dir = os.path.join(script_dir, file_dir)

        with open(absolute_dir, 'r') as f:
            countryDict = json.load(f)

        return countryDict


    def getConnections(self):
        """ Get the list of all connections """
        params = {'start' : 0,
                  'count' : self.numCon, #TODO replace with self.numCon
                  'fields': 'id,name,first_name,last_name,company,title,geo_location,tags,emails,sources,display_sources,last_interaction,secure_profile_image_url',
                  'sort'  : '-last_interaction',
                  '_'     : '1440213783954'}

        params = urllib.urlencode(params)
        connectionsPage = self.loadPage(self.conUrl+params)
        conData = json.loads(connectionsPage)
        # for index in conData['contacts']:
        #     try:
        #         print '#first name:', index['first_name'], '# Title: ', index['title'], '#studio: ', index['company']['id']
        #     except:
        #         print 'profile skiped'

        return conData #return a dictionary

    def getPeopleAtCompanies(self):
        """ Generate a dictionary of comanies and people that work at the companies. """

        conData = self.conData
        companies = {}

        for person in conData['contacts']:

            if person['company']:
                company = person['company']['id']

                if company in companies:
                    companies[company].append(person['first_name']+' '+person['last_name'])

                else:
                    companies[company] = [person['first_name']+' '+person['last_name']]

        return companies


    def quickGetCountries(self):
        """ Identify a contact's country using the data in self.conData """

        countries = {'Unspecified':{'unspecified city':[]} }

        count = 0

        for person in self.conData['contacts']:
            name = unicodedata.normalize('NFKD', person['first_name']).encode('ascii','ignore')
            lastname = unicodedata.normalize('NFKD', person['last_name']).encode('ascii','ignore')
            personNameLastName = '{} {}'.format(name, lastname)

            if person['geo_location']:
                location = person['geo_location']['name']

                if location:
                    country = self._getCountryByCity(location)

                    if country in countries:

                        if _city in countries[country]:
                            countries[country][_city].append(personNameLastName)

                        else: countries[country].update({_city: [ personNameLastName] } )

                    else:
                        countries[country]= {_city: [personNameLastName]}
            else:
                countries['Unspecified']['unspecified city'].append(personNameLastName)

        return countries


    def getPosition(self):
        """ Get a contact's occupation from self.conData """
        def _positionMatch(extendedTitle, positions):
            if not isinstance(extendedTitle, list):
                raise TypeError('{} is not a list'.format(extendedTitle) )

            for word in extendedTitle:
                for position in positions:

                    if word == position:
                        return position

            else:
                return 'other'

        positions = {'manager':[], 'animator':[], 'ceo':[], 'cto':[], 'owner':[], 'professor':[],
                    'supervisor':[], 'recruiter':[], 'producer':[], 'artist':[], 'marketing':[], 'designer':[],
                    'developer':[], 'strategist':[], 'td': [],'scientist':[], 'freelance':[], 'compositor':[],
                    'artist':[], 'generalist':[], 'founder':[], 'coordinator':[], 'creative':[], 'lighter':[],
                    'director':[], 'technical director':[], 'engineer':[], 'senior':[], 'software':[],
                    'junior':[], 'other':[], 'lead': [] }


        for person in self.conData['contacts']:
            n = unicodedata.normalize('NFKD',person['first_name']).encode('ascii','ignore')
            l = unicodedata.normalize('NFKD',person['last_name']).encode('ascii','ignore')
            personNameLastname = n+' '+l

            if person['title']:
                title = unicodedata.normalize('NFKD',person['title']).encode('ascii','ignore')
                title = title.split(' ')
                extendedTitle = []

                for word in title:
                    word = word.lower().split('/')
                    extendedTitle.extend(word)

                if 'owner' in extendedTitle:
                    positions['owner'].append(personNameLastname)
                    continue

                elif 'supervisor' in extendedTitle:
                    positions['supervisor'].append(personNameLastname)
                    continue

                elif 'senior' in extendedTitle:
                    positions['senior'].append(personNameLastname)
                    continue

                elif 'lead' in extendedTitle:
                    positions['lead'].append(personNameLastname)
                    continue

                else:
                    position = _positionMatch(extendedTitle, positions)
                    positions[position].append(personNameLastname)

            else:
                continue

        return positions


    def _get2ndConnections(self, profileID, depth, maxcount, minSleep = 3):
        """A lower level recursive method that requests a json file of the second level
        contacts. The method would recursively grab N level connection if depth is more
        than 0
        """
        depth -= 1
        profileConDataURL = 'https://www.linkedin.com/profile/profile-v2-connections?'
        x = 0
        size = 10
        offset = 0
        conData = []
        deepContacts = {}
        contatcs = {}
        print '###loading profile and its connections:', profileID

        while(True):

            print 'offset:', offset, 'count:', x
            sleepTime = random.uniform(minSleep, minSleep*2)
            time.sleep(sleepTime)

            paramsConnections = {'id': profileID, 'offset': offset, 'count': 10, 'distance': 1, 'type': 'ALL', '_': x }
            print 'sleep time', sleepTime

            try:
                profileConData = self.loadPage(profileConDataURL, paramsConnections)
                profileConData = json.loads(profileConData)

            except:
                print 'Can not load #profileID. LinkedIn could have blocked the access.', profileID, '#offset', offset, '#x', x
                break

            if 'connections' not in profileConData['content'] or 'connections' not in profileConData['content']['connections']:
                break

            listCons = profileConData['content']['connections']['connections']
            conData.extend(listCons)
            offset += 10
            x+=1

            if offset >= maxcount and maxcount != -1:
                break

        for dic in conData:
            name = dic['fmt__full_name'].split(" ")
            memberID = dic['memberID']

            if depth > 0:
                deepContacts = self._get2ndConnections(memberID, depth, maxcount, minSleep)

            if len(name)==1:
                contact = {'first_name': name[0], 'last_name': '', 'id': memberID, 'profile connections': deepContacts }

            else:
                contact = {'first_name': name[0], 'last_name': name[1], 'id': memberID, 'profile connections': deepContacts }

            nameLastname = contact['first_name'] + ' ' + contact['last_name']
            contatcs[nameLastname] = contact

        return contatcs


    def _getProfileID(self, name, lastname):
        """Get the profile id from self.conData """

        if not isinstance(name, basestring) or not isinstance(lastname, basestring):
            raise TypeError('{} or {} is not a string'.format(name, lastname) )

        profileID = 0

        for profile in self.conData['contacts']:

            if name == profile['first_name'] and lastname == profile['last_name']:
                profileID = profile['id']
                profileID = profileID[3:]
                return profileID

        else:
            raise ValueError('{} {} is not in the contacts.'.format(name, lastname) )


    def get2ndConnections(self, name, lastname, fileDir, depth=0, maxcount=-1, minSleep = 3):
        """A wraper method arround _get2ndConnections method.
        The method writes a json file where each contact has a tree of n level connections.
        """
        nameLastname = name + ' ' + lastname
        profileID = self._getProfileID(name, lastname)
        profileConData = {nameLastname: {'first_name': name, 'last_name': lastname, 'id': profileID, 'connections':{} } }
        profileConData[nameLastname]['connections'] = self._get2ndConnections(profileID, depth, maxcount, minSleep)

        with open(fileDir, 'w') as f:
            json.dump(profileConData, f, indent=4, sort_keys=True)

        return profileConData


    def getAll2ndConnections(self, fileDir, depth=0, maxcount=-1, minSleep = 4):
        """The method would iterate through all the contacts,
        get 2nd level connections and write them to a json file
        """
        if not isinstance(fileDir, basestring):
            raise TypeError('{} is not a string.'.format(fileDir) )
        if not isinstance(depth, int):
            raise TypeError('{} is not an integer'.format(depth) )

        connectionsTree = {}

        for profile in self.conData['contacts']:
            profileID = profile['id'][3:]
            # nameLastname = '{} {}'.format(profile['first_name'], profile['last_name'])
            nameLastname = profile['first_name'] + ' ' + profile['last_name']
            connections = self._get2ndConnections(profileID, depth, maxcount, minSleep)
            profile['connections'] = connections
            profile['num_cons'] = len(connections)
            profile.pop('tags')
            profile.pop('emails')
            profile.pop('sources')
            profile.pop('display_sources')
            connectionsTree[nameLastname] = profile

        with open(fileDir, 'w') as f:
            json.dump(connectionsTree, f, indent=4, sort_keys=True)

        return connectionsTree


    def getAllContacsJson(self):
        """ This function requests a json file which has all contatcs info including contcats' page links.
        The request uses linkedin api2
        """
        jsonData = ''

        params = {
                'start' : 0,
                'count' : self.numCon,
                'fields': 'id'
                }
        params = urllib.urlencode(params)

        try:
            jsonData = self.loadPage(self.conUrl2 + params)

        except:
            raise IOError('Could not get the json file')

        jsonData = json.loads(jsonData)
        contactUrls = {i['name']: i['profileUrl'] for i in jsonData['values']}

        return contactUrls


    def downloadContactPages(self, sleepTime=1):
        """This method writes the contacts' pages to the drive for further processing."""
        fullDir = os.path.join(self.currentPath, self.profilePages)

        # Check if the dir exists if not create a new one
        if not os.path.exists(fullDir):
            os.makedirs(fullDir)

        profilePage = ''

        # For name and its url, try to load the page and write it on the drive
        for name, url in self.conUrls.items():

            try:
                profilePage = self.loadPage(url)
                sleepTime = random.uniform(sleepTime, sleepTime*2)
                time.sleep(sleepTime)

            except IOError:
                print 'failed to load {} page'.format(name)
                continue

            if profilePage != '':
                with open(fullDir + name + '.html', 'w') as f:
                    f.write(profilePage)



    def parseContactPage(self, pageDir):
        """The method that parses a contact's webpage for extracting more detailed information."""
        profilePage = ''
        with open(pageDir, 'r') as f:
            profilePage = f.read()

        city = None
        country = None
        rawLocation = None
        locationPattern = re.compile(r'(?<=name=\'location\' title=\"Find other members in )[ A-z,0-9\.]+')
        location = locationPattern.search(profilePage)

        if location:
            location = location.group()
            rawLocation = location
            country, city = self._getCountryByCity(location)

        titlePattern = re.compile(r'(?<=title=\"Learn more about this title\">)[ &#39,A-z,0-9]+')
        titles = titlePattern.findall(profilePage)

        startTimePattern = re.compile(r'(?<=<span class=\"experience-date-locale\"><time>)[ A-z,0-9]+')
        startTimes = startTimePattern.findall(profilePage)
        endTimes = []

        for start in startTimes:
            endTimePattern = re.compile(r'(?<=<span class=\"experience-date-locale\"><time>' + start+ r'</time> &#8211; <time>)[ A-z,0-9]+')
            endTime = endTimePattern.findall(profilePage)
            if len(endTime)==0:
                endTime = ['Present']
            endTimes.extend(endTime)

        endTimesSize = len(endTimes)
        startTimesSize = len(startTimes)
        startEndDifference = startTimesSize - endTimesSize
        workExp = {}

        for x in range(startTimesSize):
            start = startTimes[startTimesSize-1-x]
            end = endTimes[startTimesSize-1-x]
            title = titles[startTimesSize-1-x]
            durationPattern = re.compile(r'(?<='+ end + r'</time> \()[ A-z,0-9,\|,\/]+')
            duration = durationPattern.search(profilePage)

            if duration: duration = duration.group()

            if end == 'Present':

                durationPattern = re.compile(r'(?<=&#8211; Present \()[ A-z,0-9]+')
                duration = durationPattern.search(profilePage)
                if duration: duration = duration.group()

            companyPattern = re.compile(r'[ A-z,0-9,&#39.]+(?=</a></strong></span></h5></header><span class=\"experience-date-locale\"><time>' + start + r')')
            company = companyPattern.search(profilePage)

            if not company:
                companyPattern = re.compile(r'[ A-z,0-9,.]+(?=</a></h5></header><span class=\"experience-date-locale\"><time>' + start + r')')
                company = companyPattern.search(profilePage)

            if company: company = company.group()

            workExp[company] = {'start': start, 'end': end, 'duration': duration, 'title': title}

        return workExp, country, city, rawLocation


    def getAllContatcsData(self, outputFile='database.json', numberProfiles=-1, minSleepTime=3):
        """ Parse all web pages and create a json file."""
        workExp = {}
        errorProfiles = []
        profilesExp = {}

        # load all web pages
        webPages = os.listdir(self.profilePages)

        for page in webPages:
            workExp, country, city, rawLocation = self.parseContactPage(self.profilePages + page)
            profilesExp[page] = {'workExp': workExp, 'country': country, 'city':city, 'linkedInLocation': rawLocation}


        with open(outputFile, 'w') as f:
            json.dump(profilesExp, f, indent=4, sort_keys=True)

        return profilesExp, errorProfiles

import urllib, urllib2, cookielib, re, json, math, os
from pprint import pprint
import unicodedata


class SocialNetwork(object):
    """ A base class to login and load pages """
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

    def loadPage(self, url, data = None):
        try:
            if data is not None:
                data = urllib.urlencode(data)
                response = self.opener.open(url, data)

            else:
                response = self.opener.open(url)

            return str(response.read())

        except:
            raise IOError('{} is not accesable.'.fromat(url))


    def loginPage(self):
        """
        starts with the homepage to obtain the csrf, once its done logins using login, pass and csrf
        """
        loginPage = self.loadPage(self.start_url)
        csrfMatch = re.compile(r'(?<=id="loginCsrfParam-login" type="hidden" value=")[A-z,0-9,-]+')
        csrf = csrfMatch.search(loginPage).group()
        loginData = {'session_key'      : self.login,
                     'session_password' : self.password,
                     'loginCsrfParam'   : csrf }

        homePage = self.loadPage(self.login_url, loginData)

        return homePage


class LinkedIn(SocialNetwork):
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.startURL = "https://www.linkedin.com/"
        self.loginURL = "https://www.linkedin.com/uas/login-submit"
        self.con_url = "https://www.linkedin.com/contacts/api/contacts/?"
        super(LinkedIn, self).__init__(self.login, self.password, self.startURL, self.loginURL)
        self.homePage = self.loginPage()
        self.countryDict = self.loadCountryDict()
        self.num_con = self.getNumCons()
        self.conData = self.getConnections()

    def getNumCons(self):
        numCon = re.search(r'\"numConnections\":\d+', self.homePage)
        number = numCon.group().split(':')[1]
        return number

    def _getCountryByCity(self, city):
        country = None
        city = unicodedata.normalize('NFKD', city).encode('ascii','ignore')
        city = re.sub(" Area", '', city)
        city = re.sub(" Metropolitan", '', city)
        city = re.sub(" Bay", '', city)
        city = re.sub("Greater ", '', city)
        city = re.sub(r" \(\w+\)", '', city) # takes out everything that is inside ().
        city = re.sub(r'\/[A-z ]*', '', city) # takes out everything that comes after /.

        for dictCountry in self.countryDict:
            for dictCity in self.countryDict[dictCountry]:
                cityMatch = re.compile(dictCity)
                match = cityMatch.match(city)

                if match:
                    match = match.group()
                    if len(match) == len(city):
                        country = dictCountry
                        return country
        else:
            return 'Unresolved place'

    def loadCountryDict(self):
        script_dir = os.path.dirname(__file__)
        file_dir = 'countryCity.json'
        absolute_dir = os.path.join(script_dir,file_dir)
        f = file(absolute_dir,'r')
        countryDict = json.load(f)
        f.close()
        return countryDict


    def getConnections(self):
        """
        get the list of all connections
        """
        params = {'start' : 0,
                  'count' : self.num_con, #TODO replace with self.num_con
                  'fields': 'id,name,first_name,last_name,company,title,geo_location,tags,emails,sources,display_sources,last_interaction,secure_profile_image_url',
                  'sort'  : '-last_interaction',
                  '_'     : '1440213783954'}
        params = urllib.urlencode(params)
        connectionsPage = self.loadPage(self.con_url+params)
        conData = json.loads(connectionsPage)
        # for index in conData['contacts']:
        #     try:
        #         print '#first name:', index['first_name'], '# Title: ', index['title'], '#studio: ', index['company']['id']
        #     except:
        #         print 'profile skiped'

        return conData #return a dictionary

    def getPeopleAtCompanies(self):
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


    def getCountries(self):
        countries = {'Unspecified':{'unspecified city':[]} }

        count = 0
        for person in self.conData['contacts']:
            name = unicodedata.normalize('NFKD', person['first_name']).encode('ascii','ignore')
            lastname = unicodedata.normalize('NFKD', person['last_name']).encode('ascii','ignore')
            personNameLastName = '{} {}'.format(name, lastname)
            if person['geo_location']:
                location = person['geo_location']['name']
                location =  location.split(',')

                if location:
                    _city = location[0]
                    country = self._getCountryByCity(_city)

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
                print personNameLastname, extendedTitle

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

    def _getProfileConnections(self, profileID):

        profileConDataURL = 'https://www.linkedin.com/profile/profile-v2-connections?'
        x = 0
        size = 10
        offset = 0
        conData = []
        listCons = []
        switch = True

        while(switch):
            paramsConnections = {'id': profileID, 'offset': offset, 'count': 10, 'distance': 1, 'type': 'ALL', '_': x }
            profileConData = self.loadPage(profileConDataURL, paramsConnections)
            profileConData = json.loads(profileConData)

            if 'connections' not in profileConData['content'] or 'connections' not in profileConData['content']['connections']:
                break

            listCons = profileConData['content']['connections']['connections']
            conData.extend(listCons)
            offset += 10
            x+=1

        return conData


    def _getProfileID(self, name, lastname):
        profileID = 0
        profileURL = 'https://www.linkedin.com/profile/view?'
        for profile in self.conData['contacts']:

            if name == profile['first_name'] and lastname == profile['last_name']:
                profileID = profile['id']
                profileID = profileID[3:]
                break

        else:
            raise ValueError('{} {} is not in the contacts'.format(name, lastname) )

        return profileID


    def _getProfileExperience(self):
        raise NotImplementedError('_getProfileExperience is not implemented.')


    def getProfileData(self, name, lastname):
        profileID = self._getProfileID(name, lastname)
        profileConData = self._getProfileConnections(profileID)
        print len(profileConData)

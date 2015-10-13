import datetime, math, json, re
class WorkTime(object):
    def __init__(self, iyear, imonth):
        if not isinstance(iyear, int):
            raise TypeError('{} is not an integer'.format(iyear) )

        if not isinstance(imonth, int):
            raise TypeError('{} is not an integer'.format(imonth) )

        if imonth > 12:
            raise ValueError("{} shouldn't be more than 12".format(imonth) )

        self.year = iyear
        self.month = imonth

    def __str__(self):
        return "{} years, {} months".format(self.year, self.month)

    def __add__(self, other):
        if not isinstance(other, WorkTime):
            raise TypeError('{} is not an instance of WorkTime'.format(other) )

        years = self.year + other.year
        month = self.month + other.month
        if month > 12:
            _year_month = month/12.0
            _year = math.floor(_year_month)
            month = 0
            month = round(12*(_year_month-_year))
            years+= _year

        return WorkTime(int(years), int(month))

    def setYears(self, years):
        if not isinstance(years, int):
            raise TypeError('{} is not an integer'.format(years) )
        self.year = years

    def setMonths(self, months):
        if not isinstance(month, int):
            raise TypeError('{} is not an integer'.format(months) )
        if months > 12:
            raise ValueError("{} shouldn't be more than 12".format(months) )

        self.month = months

def convertDate(stringDate):
    """ The function converts a string date into pair of integers. """
    if not isinstance(stringDate, basestring):
        raise TypeError('{} is not a string'.format(stringDate) )
    yearPattern = re.compile(r'[0-9](?= year)')
    year = yearPattern.search(stringDate)

    if year:
        year = year.group()
    else:
        year = 0

    monthPattern = re.compile(r'[0-9](?= month)')
    month = monthPattern.search(stringDate)

    if month:
        month = month.group()
    else:
        month = 0

    return int(year), int(month)




class Profile(object):

    def __init__(self, name, lastname, gender=None, location=None, id=None, year=None, month=None, day=None, image=None):
        if not isinstance(name, basestring):
            raise TypeError('{} is not a string'.format(name) )

        if not isinstance(lastname, basestring):
            raise TypeError('{} is not a string'.format(lastname) )

        if not isinstance(gender, basestring) and gender is not None:
            raise TypeError('{} is not a string'.format(gender) )

        if not isinstance(location,tuple) and location is not None:
            raise TypeError('{} is not a tuple'.format(location) )

        for arg in [id, day, month, year]:
            if not isinstance(arg, int) and arg is not None:
                raise TypeError('{} is not an integer'.format(arg) )

        self.nameLastName = '{0} {1}'.format(name, lastname)
        self.data = {'personalData': {},
                     'workData': {} }

        self.data['personalData']={'name': name,
                                   'lastname': lastname,
                                   'gender': gender,
                                   'location': location,
                                   'id': id,
                                   'day': day,
                                   'month': month,
                                   'year': year,
                                   'image': image}

    def __str__(self):
        return "{} {}".format(self.data['personalData']['name'], self.data['personalData']['lastname'])

    def getBirthday(self):
        return (self.data['personalData']['day'], self.data['personalData']['month'], self.data['personalData']['year'])

    def getAge(self):
        currentDate = datetime.date.today()
        birthdayTime = datetime.date(self.data['personalData']['year'], self.data['personalData']['month'], self.data['personalData']['day'])
        age =  currentDate-birthdayTime
        return age.days/360

    def getLocation(self):
        return self.data['personalData']['location']

    def getId(self):
        return self.data['personalData']['id']


class LinkedinProfile(Profile):
    def __init__(self, name, lastname, id, gender=None, location=None, year=None, month=None, day=None):
        super(LinkedinProfile,self).__init__(name, lastname, gender, location, id, year, month, day)

    def setCompanyPeriodTitle(self,company, years, months, title, present=None):
        for arg in [company,title]:
            if not isinstance(arg, basestring):
                raise TypeError('{} is not a string'.format(arg) )

        for arg in [years, months]:
            if not isinstance(arg, int):
                raise TypeError('{} is not an integer'.format(arg) )

        if not isinstance(present, bool) and present is not None:
            raise TypeError('{} is not a bool value.'.format(present) )

        self.data['workData'][company]={'time':{'year':years, 'months':months}, 'title':title, 'present':present}

    def setImage(self, imageDir):
        if not isinstance(imageDir, basestring):
            raise TypeError('{} is not a string.'.format(imageDir) )

        self.data['personalData']['image'] = imageDir

    def getTotalTime(self):
        totalTime = WorkTime(0, 0)
        if self.data['workData']:
            for company in self.data['workData']:
                coYear = self.data['workData'][company]['time']['year']
                coMonths = self.data['workData'][company]['time']['months']
                coTime = WorkTime(coYear, coMonths)
                totalTime+= coTime

        return totalTime

    def getPeriod(self, company):
        if not isinstance(company, basestring):
            raise TypeError('{} is not a string.'.format(company) )

        return self.data['workData'][company]['time']

    def getAllCompanies(self):
        return [company for company in self.data['workData']]

    def getCurrentPosition(self):
        for company in self.data['workData']:
            if self.data['workData'][company]['present']:

                return self.data['workData'][company]['title']

    def getAllExp(self):
        return self.data['workData']

    def getNameLastName(self):
        """ The method can be used to create a key value for a dictionary of profiles. """
        return self.nameLastName

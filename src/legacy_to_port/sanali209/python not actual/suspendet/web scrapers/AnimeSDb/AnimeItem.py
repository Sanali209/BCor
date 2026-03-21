import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float, Boolean, create_engine, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, relationship
from tqdm import tqdm

import model as model


# create engine and session


anime_item_tags_table = Table('anime_item_tags', model.Base.metadata,
                              Column('anime_item_id', Integer, ForeignKey('anime_item.id'), primary_key=True),
                              Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True)
                              )


class AnimeItem(model.Base):
    __tablename__ = 'anime_item'
    id = Column(Integer, primary_key=True)
    siteid = Column(Integer)
    sourceUrl = Column(String, nullable=False)
    title = Column(String)
    description = Column(String)
    created = Column(DateTime)
    modified = Column(DateTime)
    tumbnail = Column(LargeBinary)
    rating = Column(Float)
    ratingStory = Column(Float)
    ratingAnimation = Column(Float)
    ratingSound = Column(Float)
    favorite = Column(Boolean)
    error = Column(String)
    temexist = Column(Boolean, default=False)

    bagevalue = Column(String)
    needupdate = Column(Boolean, default=True)
    tags = relationship("Tag", secondary=anime_item_tags_table, back_populates="animeItems")


class Tag(model.Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    created = Column(DateTime)
    modified = Column(DateTime)
    animeItems = relationship("AnimeItem", secondary=anime_item_tags_table, back_populates="tags")




class SeleniumScraper:
    def __init__(self):
        self.url_curent = 'https://anime1.animebesst.org/'

        self.driver = webdriver.Chrome()
        # set wait time 30 seconds

        self.paginationLinks = []
        self.paginationLinks_processed = []
        self.detailsPageLinks = []
        self.driver.get(self.url_curent)

        self.driver.implicitly_wait(30)
        self.Login()

    def ScraperRestart(self):
        self.driver.quit()
        self.driver = webdriver.Chrome()

    def Login(self):
        self.driver.get('https://anime1.animebesst.org')
        self.driver.find_element(By.ID, 'login_name').send_keys('sanali209')
        self.driver.find_element(By.ID, 'login_password').send_keys('agentli301829')
        self.driver.find_element(By.CLASS_NAME, 'btn').click()

    def Scrap(self):
        self.getPaginationLinks()
        self.getItems()

        while len(self.paginationLinks) > 0:
            self.url_curent = self.paginationLinks.pop(0)
            print(self.url_curent)
            self.paginationLinks_processed.append(self.url_curent)
            self.driver.get(self.url_curent)
            # get details page links
            self.getItems()
            self.getPaginationLinks()

    def getPaginationLinks(self):

        # get pagination links by class = pages-numbers
        pagination = self.driver.find_element(By.CLASS_NAME, 'pages-numbers')
        # get all links from pagination
        paginationLinks = pagination.find_elements(By.TAG_NAME, 'a')
        # get links value
        paginationLinkswals = list([link.get_attribute('href') for link in paginationLinks])
        # add links to paginationLinks if not exist
        for link in paginationLinkswals:
            if link not in self.paginationLinks and link not in self.paginationLinks_processed:
                self.paginationLinks.append(link)

    def getItems(self):
        # get all items
        items = self.driver.find_elements(By.CLASS_NAME, 'shortstory')
        # iterate items
        for item in items:
            # create AnimeItem
            animeItem = AnimeItem()
            animeItem.sourceUrl = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
            # split url by - and get first part
            animeItem.siteid = animeItem.sourceUrl.split('-')[0]
            # split animeItem.siteid by / and get last part
            animeItem.siteid = animeItem.siteid.split('/')[-1]
            # faind element by class = fbadge-full if not exist set to 0
            self.driver.implicitly_wait(0.1)
            try:
                item.find_element(By.CLASS_NAME, 'fbadge-full').text
                animeItem.bagevalue = 'full'
            except:
                animeItem.bagevalue = '0'
            if animeItem.bagevalue == '0':
                try:
                    item.find_element(By.CLASS_NAME, 'fbadge-ova').text
                    animeItem.bagevalue = 'ova'
                except:
                    animeItem.bagevalue = '0'
            if animeItem.bagevalue == '0':
                try:
                    item.find_element(By.CLASS_NAME, 'fbadge-movie').text
                    animeItem.bagevalue = 'movie'
                except:
                    animeItem.bagevalue = '0'
            if animeItem.bagevalue == '0':
                try:
                    item.find_element(By.CLASS_NAME, 'fbadge-ongoing').text
                    animeItem.bagevalue = 'movie'
                except:
                    animeItem.bagevalue = '0'
            self.driver.implicitly_wait(30)

            # check if animeitem exist in db
            if session.query(AnimeItem).filter(AnimeItem.siteid == animeItem.siteid).count() == 0:
                session.add(animeItem)
                session.commit()
                print(str(animeItem.siteid) + ' added to db')
            else:
                print(str(animeItem.siteid) + ' already in db')

    def getDetails(self):
        itemscoll = session.query(AnimeItem).filter(AnimeItem.needupdate == True).filter(AnimeItem.error == None)
        # iterate trouth animeItems
        tqdmin = tqdm(itemscoll.all())
        count = 0
        for animeItem in tqdmin:
            count += 1
            if count > 90:
                count = 0
                time.sleep(60)
            print(animeItem.siteid)

            if animeItem.error is not None:
                continue
            # check html page PathLabelVal to "Bad Request"
            if 'Bad Request' in self.driver.page_source:
                print('Bad Request')
                break;

            self.driver.get(animeItem.sourceUrl)
            # get Title class = fullstory-title
            # delay 5 seconds
            time.sleep(1)
            try:
                titleelement = self.driver.find_element(By.CLASS_NAME, 'fullstory-title')
            except:
                animeItem.error = 'title not found'
                session.commit()
                continue
            titleh1value = titleelement.find_element(By.TAG_NAME, 'h1').text
            animeItem.title = titleh1value

            # get teme and kategoti and convert to tag
            try:
                player = self.driver.find_element(By.ID, 'initPlayer')
            except:
                animeItem.error = 'player not found'
                print('error')
                continue

            # faind subitems <a>
            subitems = player.find_elements(By.TAG_NAME, 'a')
            # iterate subitems

            for subitem in subitems:
                # get subitem href
                subitemhref = subitem.get_attribute('href')
                # if link subitemhref contains /temy/ mark item temexist = True
                if '/temy/' in subitemhref:
                    animeItem.temexist = True
                # get subitem PathLabelVal
                subitemtext = subitem.text
                # check if subitemtext is not empty
                if subitemtext != '':
                    # check if subitemtext is not in db
                    if session.query(Tag).filter(Tag.name == subitemtext).count() == 0:
                        # create tag
                        tag = Tag()
                        tag.name = subitemtext
                        session.add(tag)
                        session.commit()
                        print(tag.name + ' added to db')
                    else:
                        tag = session.query(Tag).filter(Tag.name == subitemtext).first()
                    # check if animeItem has tag
                    if session.query(anime_item_tags_table).filter(
                            anime_item_tags_table.c.anime_item_id == animeItem.id).filter(
                        anime_item_tags_table.c.tag_id == tag.id).count() == 0:
                        # add tag to animeItem
                        animeItem.tags.append(tag)
                        session.commit()
                        print(tag.name + ' added to ' + str(animeItem.siteid))
                    else:
                        print(tag.name + ' already in ' + str(animeItem.siteid))

            # get description class = fstory-contenttab
            descriptionelement = self.driver.find_element(By.CLASS_NAME, 'fstory-contentab')
            animeItem.description = descriptionelement.text

            # get rating class = m-rating-rate
            ratingelement = self.driver.find_element(By.CLASS_NAME, 'm-rating-rate')
            rating = float(ratingelement.text.split('\n')[0])
            animeItem.rating = rating

            animeItem.needupdate = False
            session.commit()


engine = create_engine('sqlite:///anime.db')
model.Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# mark 4921,1734,4883,4862,4854,4860 animeItems needupdate = True
items = session.query(AnimeItem).filter(AnimeItem.siteid.in_([''])).all()
for animeItem in items:
    animeItem.needupdate = True
    animeItem.error = None
    session.commit()

scraper = SeleniumScraper()
# delete anime item with siteid = novosti
# session.query(AnimeItem).filter(AnimeItem.siteid == 'novosti').delete()
scraper.Scrap()
scraper.getDetails()


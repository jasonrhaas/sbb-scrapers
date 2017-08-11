# -*- coding: utf-8 -*-
import re
import logging

import scrapy
from scrapy.loader import ItemLoader
from leads.items import PostItem, UserItem, ThreadItem
from leads.processors import to_int


class HomebrewtalkSpider(scrapy.Spider):
    name = 'homebrewtalk'
    allowed_domains = ['homebrewtalk.com']
    start_urls = ['http://www.homebrewtalk.com/forum.php']

    # Thread ID 12345 would look like: 'http://example.com/showthread.php?t=12345...'
    patterns = {
                'thread_id': re.compile('t=(\d+)'),
                'next_page_url': "//*[@class='pagenav']//*[@href and contains(text(), '>')]/@href"
                }

    def paginate(self, response, next_page_callback):
        """Returns a scrapy.Request for the next page, or returns None if no next page found.
        response should be the Response object of the current page."""
        # This gives you the href of the '>' button to go to the next page
        # There are two identical ones with the same XPath, so just extract_first.
        next_page = response.xpath(self.patterns['next_page_url'])

        if next_page:
            url = response.urljoin(next_page.extract_first())
            logging.info("NEXT PAGE IS: %s" % url)
            return scrapy.Request(url, next_page_callback)
        else:
            logging.info("NO MORE PAGES FOUND")
            return None

    def parse(self, response):
        # Parse the board (aka index) for forum URLs
        forum_urls = response.xpath('.//td[contains(@id,"f")]/div/a/@href').extract()
        for url in forum_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_forum)
            # yield {'url': url}

    def parse_forum(self, response):
        logging.info("STARTING NEW FORUM SCRAPE (GETTING THREADS)")
        thread_urls = response.xpath('.//a[contains(@id,"thread_title")]/@href').extract()
        for url in thread_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_posts)
            # yield {'thread_urls': url}

        # return the next forum page if it exists
        yield self.paginate(response, next_page_callback=self.parse_forum)

    def parse_posts(self, response):
        logging.info("STARTING NEW PAGE SCRAPE")

        # Get info about thread
        # TODO: move this into parse_forum, b/c here the code runs every page of the thread
        # thread = ThreadItem()
        # thread['thread_id'] = to_int(re.findall(self.patterns['thread_id'], response.url)[0])
        # thread['thread_name'] = response.xpath('.//meta[@name="twitter:title"]/@content').extract_first()
        # thread['thread_path'] = response.xpath('.//div/table//tr/td/table//tr/td[3]//a/text()').extract()


        # Scrape all the posts on a page for post & user info
        for post in response.xpath("//table[contains(@id,'post')]"):
            p = PostItem()

            # p['thread_id'] = thread['thread_id']
            p['user_id'] = post.xpath(".//a[@class='bigusername']/@href").re_first('u=(\d+)')
            # p['timestamp'] = post.xpath("string(.//tr/td/div[@class='normal'][2])").extract_first().strip()
            # p['quotes'] = post.xpath('.//blockquote/text()').extract()

            # Message text, excluding blockquotes
            # Also excluding the <div> that has user "signatures"
            # (perhaps later on for NLP you'd want to insert a BLOCKQUOTE word-marker)
            # p['message'] = post.xpath(".//*[contains(@id,'post_message_')]//text()[not(parent::blockquote)]").extract()

            # p['post_no'] = to_int(post.xpath(".//tr/td/div[@class='normal'][1]/a//text()").extract_first())

            # user info
            user = UserItem()
            user['user_id'] = p['user_id']
            user['user_name'] = post.xpath(".//a[@class='bigusername']//text()").extract_first()

            if not user.get('user_name'):
                logging.warning('USED ALTERNATIVE USERNAME SELECTOR')
                user['user_name'] = post.css('a.bigusername').css('font::text').extract_first()

            # yield p
            # yield user
            request = scrapy.Request('http://homebrewtalk.com/members/' + user['user_name'], callback=self.parse_profile)
            request.meta['user'] = user
            yield request
            # yield scrapy.Request('http://homebrewtalk.com/members/' + user['user_name'], callback=self.parse_profile)

        # yield thread

        # Pagination across thread: search for the link that the next button '>' points to, if any
        # next_page_request = self.paginate(next_page_callback=self.parse_posts)
        # if next_page_request:
            # yield next_page_request
        # WARNING TODO just trying this, it might be None
        yield self.paginate(response, next_page_callback=self.parse_posts)

    def parse_profile(self, response):
        logging.info("STARTING NEW PROFILE SCRAPE")

        try:
            user = response.meta['user']
        except KeyError:
            user = UserItem()

        # user['general_interests'] = response.css('strong').css('a::text').extract()

        try:
            user['age'] = response.css('div.profile-top').re(r'(?<=Age:<\/small><\/p><div class="newline"><\/div>)\d+')[0]
        except:
            logging.debug('Age not found.')
        # user['birthday'] = response.css('div.profile-top').re(r"(?<=Birthday:<\/small><div class='newline'><\/div>)\d+\/\d+\/\d+")

        # About me section
        for item in response.css('div.profile-bottom').css('li'):
            label = item.css('label::text').extract_first().strip(' :')
            value = item.css('strong::text').extract_first()

            for key, field in user.fields.items():
                if label == field.get('label'):
                    user[key] = value

        yield user


class HomebrewUsernameSpid(scrapy.Spider):
    name = 'usernames'

    start_urls = ['http://www.homebrewtalk.com/showthread.php?t=221302']

    def parse(self, response):
        # users = ItemLoader(item=UserItem(), response=response)
        users = UserItem()

        userids = set(response.xpath(".//a[@class='bigusername']/@href").re('u=(\d+)'))
        usernames_1 = response.css('a.bigusername').css('font::text').extract()
        usernames_2 = response.css('a.bigusername::text').extract()
        usernames = set(usernames_1 + usernames_2)

        users['user_id'] = userids
        users['names'] = usernames

        yield users


        # for userid in userids:
        #     yield {'userid': userid}

        # for username in usernames:
        #     yield {'username': username}

        next_page = response.xpath("//*[@class='pagenav']//*[@href and contains(text(), '>')]/@href").extract_first()
        if next_page is not None:
            yield response.follow(next_page, self.parse)

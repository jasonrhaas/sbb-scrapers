# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PostItem(scrapy.Item):
    collection = 'post'
    unique_fields = ['thread_id', 'post_no']

    thread_id = scrapy.Field()
    user_id = scrapy.Field()
    timestamp = scrapy.Field()
    message = scrapy.Field()
    quotes = scrapy.Field()
    post_no = scrapy.Field()
    # post_no is shown on upper right of each post container.

    # post_id is '202020' in the last part of URL: http://metaldetectingforum.com/showpost.php?p=202020
    # But I'm not using post_id right now.


class UserItem(scrapy.Item):
    collection = 'user'
    unique_fields = ['user_id']

    user_id = scrapy.Field()
    user_name = scrapy.Field()
    join_date = scrapy.Field()
    last_activity = scrapy.Field()
    age = scrapy.Field()
    birthday = scrapy.Field()
    referrals = scrapy.Field()
    likes = scrapy.Field()
    general_interests = scrapy.Field(label='General Interests')
    real_name = scrapy.Field(label='Real Name')
    occupation = scrapy.Field(label='Occupation')
    gender = scrapy.Field(label='Gender')
    status = scrapy.Field(label='Status')
    city = scrapy.Field(label='City')
    state = scrapy.Field(label='State/Provice')


class ThreadItem(scrapy.Item):
    collection = 'thread'
    unique_fields = ['thread_id']

    thread_id = scrapy.Field()
    thread_name = scrapy.Field()
    thread_path = scrapy.Field()
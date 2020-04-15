# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 17:00:47 2020

@author: Chan Chak Tong
"""

from selenium import webdriver
from datetime import datetime
from itertools import compress
from getpass import getpass
import time
import re

class Worm:
    def __init__(self):
        self.username = input('Username of FACEBOOK: ')
        self.password = getpass('Password of FACEBOOK: ')
    
    def __login(self):
        # Locate the textbox and enter the correspondings
        self.driver.find_element_by_id("email").send_keys(self.username)
        self.driver.find_element_by_id("pass").send_keys(self.password)
        self.driver.find_element_by_id("loginbutton").click()
        
        # Wait the respond of website
        time.sleep(1)
    
    def __scroll_down(self, times):
        # Scroll the browser about k-times
        for i in range(times):
            self.driver.execute_script('window.scrollTo(0, %d)' % (500 * (i+1)))
            time.sleep(1)
    
    def __open_feed(self, feed_id):
        # Once the keyword matches, open the feed on a blank page
        feed_link = self.group_link + 'permalink/' + feed_id
        self.driver.execute_script('window.open("%s","_blank");' % feed_link)
        self.driver.switch_to.window(self.driver.window_handles[0])
        
    def start(self, group_link):
        # Opens browser and go to FACEBOOK
        # Requires 'chromedriver.exe'
        profile = webdriver.ChromeOptions()
        prefs = {'profile.default_content_setting_values.notifications': 2}
        profile.add_experimental_option('prefs', prefs)
        self.driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=profile)
        self.driver.get("http://www.facebook.com")
        
        # Login
        self.__login()
        
        # Go to the given group
        self.group_link = group_link
        self.driver.get(group_link + '?sorting_setting=CHRONOLOGICAL')
    
    def listen(self, keyword, top=10, scroll_times=6, freq=30):
        # Keep listening the feeds and refresh after (freq) secs
        self.seen = []      # Record the seen feed
        print('[Start] %s' % str(datetime.today()))
        print('------------------------------')
        while True:
            self.__scroll_down(scroll_times)
            message_list = self.__get_messages(top)
            id_list = self.__get_feed_ids(top)
            matched = list(map(lambda m: m.find(keyword) != -1, message_list))
            match_id = list(compress(id_list, matched))
            
            print('[Refresh] %s' % str(datetime.today()))
            print('Matched cases: ',  sum(matched))
            print('Matched ID:', match_id)
            print('------------------------------')
            
            # Open the feed if it hasn't seen before.
            for feed_id in match_id:
                if feed_id not in self.seen:
                    self.seen.append(feed_id)
                    self.__open_feed(feed_id)
                    
            time.sleep(freq)
            self.driver.refresh()
    
    def __get_feed_ids(self, top):
        # Capture the ID of feed
        subtitle_block = self.driver.find_elements_by_xpath("//div[@data-testid='story-subtitle']")
        feed_list = []
        for i, block in enumerate(subtitle_block[:top]):
            feed_id = block.get_attribute('id')
            m = re.search('feed_subtitle_(.+?):', feed_id)
            if m: feed_list.append(m.group(1))
        return feed_list
    
    def __get_messages(self, top):
        # Capture all paragraphs of feed
        p_block = self.driver.find_elements_by_xpath("//div[@data-testid='post_message']")
        message_list = []
        for i, block in enumerate(p_block[:top]):
            message = ''
            try:
                see_more_btn = block.find_element_by_class_name('see_more_link')
                see_more_btn.click()
            except:
                pass
            finally:
                p_list = block.find_elements_by_tag_name('p')
                message = '\n'.join(map(lambda p: p.text, p_list))
                message_list.append(message)
        return message_list

    def stop(self):
        # Shut down the driver
        self.driver.quit()
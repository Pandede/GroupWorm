# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 17:00:47 2020

@author: Chan Chak Tong
"""

from PyQt5.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import datetime
from itertools import compress
import time
import re

class Worm:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.seen = []
        
    def __login(self):
        # Locate the textbox and enter the correspondings
        self.driver.find_element_by_id("email").send_keys(self.username)
        self.driver.find_element_by_id("pass").send_keys(self.password)
        self.driver.find_element_by_id("pass").send_keys(Keys.ENTER)
        
        # Wait the respond of website
        time.sleep(1)
    
    def __scroll_down(self, times):
        # Scroll the browser about k-times
        for i in range(times):
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(1)
    
    def __open_feed(self, feed_id):
        # Once the keyword matches, open the feed on a blank page
        feed_link = self.group_link + 'permalink/' + feed_id
        self.driver.execute_script('window.open("%s","_blank");' % feed_link)
        self.driver.switch_to.window(self.driver.window_handles[0])
        
    def locate(self, group_link):
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
    
    def listen(self, keywords, top=10, scroll_times=6):
        records = []
        
        # Refresh the website
        self.driver.refresh()
        
        # Scroll the window
        self.__scroll_down(scroll_times)
        
        # Get all messages and feed ID on whole page
        message_list = self.__get_messages(top)
        id_list = self.__get_feed_ids(top)
        
        # Get the messages and feed ID which contains keywords
        matched = [self.__match(m, keywords) for m in message_list]
        match_id = list(compress(id_list, matched))
        
        # Write down the time
        record_time = str(datetime.today())
        
        # Add the records if it hasn't been seen yet
        for feed_id in match_id:
            if feed_id not in self.seen:
                feed_link = self.group_link + 'permalink/' + feed_id
                self.seen.append(feed_id)
                records.append([record_time, feed_id, feed_link])
        
        # Compose the status dictionary
        status = {
            'total_cases': len(message_list),
            'matched_cases': len(match_id)
            }
        
        return status, records
    
    def __match(self, message, keywords):
        # The message is valid if it contains one of keywords.
        validity = [message.find(k) != -1 for k in keywords]
        return sum(validity) > 0
    
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
        # Close the browser
        self.driver.close()
        
class WormThread(Worm, QThread):
    '''
    This class implements the class "Worm" as a thread (QThread)
    '''
    record_signal = pyqtSignal(list)
    status_signal = pyqtSignal(dict)
    
    def __init__(self, username, password, parent=None):
        Worm.__init__(self, username, password)
        QThread.__init__(self, parent)
        
        # Toggle on the thread
        self.is_listening = True
    
    def __del__(self):
        self.terminal()
    
    def terminal(self):
        Worm.stop(self)
        QThread.quit(self)
        
        # Stop the thread
        self.is_listening = False
    
    def locate(self, group_link):
        # Override the function "locate" in class "Worm"
        self.group_link = group_link
        
    def listen(self, keywords, top=10, scroll_times=6, freq=60):
        # Override the function "listen" in class "Worm"
        self.keywords = keywords
        self.top = top
        self.scroll_times = scroll_times
        self.freq = freq
        
        self.start()
        
    def run(self):
        super().locate(self.group_link)
        while self.is_listening:
            status, records = super().listen(self.keywords, self.top, self.scroll_times)
            self.record_signal.emit(records)
            self.status_signal.emit(status)
            self.sleep(self.freq)
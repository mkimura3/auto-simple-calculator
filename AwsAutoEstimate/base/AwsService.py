#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.events import EventFiringWebDriver
from selenium.webdriver.support.events import AbstractEventListener
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

class ScreenshotListener(AbstractEventListener):
    def on_exception(self, exception, driver):
        screenshot_name = "exception.png"
        driver.get_screenshot_as_file(screenshot_name)
        print("Screenshot saved as '%s'" % screenshot_name)

class AwsService(object):
    RETRY = 3
    #
    driver = None
    eventdriver = None

    def __init__(self, driver):
        self.driver = driver
        self.eventdriver = EventFiringWebDriver(self.driver, ScreenshotListener())

    def get_screenshot(self, name ):
        self.driver.get_screenshot_as_file( self.file_prefix + name + '.png' )

    def get_selectedText(self,select):
        return select.find_elements_by_tag_name('option')[ int(select.get_attribute('selectedIndex')) ].text

    def is_checked( self, css, driver=None ):
        element = self.get_element(css, driver)
        if element :
            chk = element.get_attribute('checked')
            return chk == u'true'
        else :
            return False

    def get_value( self, css, driver=None ):
        element = self.get_element(css, driver)
        if element :
            return element.get_attribute('value')
        else :
            return ''
    def get_text( self, css, driver=None ):
        element = self.get_element(css, driver)
        if element :
            return element.text
        else :
            return ''

    def get_element( self,css, driver=None ):
        if driver==None : driver=self.eventdriver
        try :
            ret=driver.find_element_by_css_selector(css)
        except NoSuchElementException, e: return None
        return ret

    def get_elements(self, css, driver=None):
        if driver==None : driver=self.eventdriver
        return driver.find_elements_by_css_selector(css)

    def get_elements(self, css, driver=None):
        if driver==None : driver=self.eventdriver
        return driver.find_elements_by_css_selector(css)

    def get_val_and_type(self, css, driver=None):
        if driver==None : driver=self.eventdriver
        # input
        i = driver.find_element_by_css_selector(css + ' input')
        if self.is_member(i, 'integerNumericField') :
            v = int(i.get_attribute('value'))
        elif self.is_member(i, 'NumericField') or self.is_member(i, 'numericTextBox'):
            v = float(i.get_attribute('value'))
        else:
            v = i.get_attribute('value')
        # select
        s = driver.find_element_by_css_selector(css + ' select')
        t = self.get_selectedText(s)
        return (v,t)

    def set_textbox( self, css, value, driver=None):
        element = self.get_element(css, driver)
        element.clear()
        element.send_keys(value)

    def set_value( self, css, value, driver=None, value_type=None):
        if value_type:
            v = value_type(value)
        else:
            v = value
        element = self.get_element(css, driver)
        if element.is_enabled() :
            element.clear()
            element.send_keys([str(v), Keys.ENTER])

    def set_checkbox( self, css, value, driver=None):
        chkbox = self.get_element(css, driver)
        chk = chkbox.get_attribute('checked')
        if value :
            # True
            if (chk!=u'true') : chkbox.click()
        else :
            # False
            if (chk==u'true') : chkbox.click()

    def set_select( self, css, value, driver=None):
        s = self.get_element(css, driver)
        Select(s).select_by_visible_text(value)

    def set_val_and_type(self, css, values, driver=None, value_type=None):
        if driver==None : driver=self.eventdriver
        # select
        if 'Type' in values :
            self.set_select( css + ' select', values['Type'], driver)
        # input
        if 'Value' in values :
            self.set_value( css + ' input', values['Value'], driver, value_type)

    def is_member(self, target , cname):
        return cname in target.get_attribute("class").split(" ")

    def get_serviceConfig(self, config):
        pass

    def set_serviceConfig(self,config):
        pass


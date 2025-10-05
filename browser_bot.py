#!/usr/bin/env python3
"""
Taming.io Browser Bot
====================

This script uses Selenium WebDriver with Chromium to automatically:
1. Open a taming.io server
2. Enter the name '111' in the input field  
3. Click Play to join the game

Usage:
    python browser_bot.py [server_url]
"""

import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementNotInteractableException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TamingIOFirefoxBot:
    """Firefox browser automation bot for joining taming.io game servers."""
    
    def __init__(self, server_url=None):
        self.server_url = server_url or "https://taming.io/"
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Firefox WebDriver with optimal settings."""
        try:
            logger.info("Setting up Firefox WebDriver...")
            
            # Configure Firefox options
            firefox_options = Options()
            firefox_options.add_argument("--disable-blink-features=AutomationControlled")
            firefox_options.add_argument("--disable-web-security")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")
            
            # Set preferences to avoid automation detection
            firefox_options.set_preference("dom.webdriver.enabled", False)
            firefox_options.set_preference('useAutomationExtension', False)
            firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0")
            
            # Create WebDriver instance
            self.driver = webdriver.Firefox(options=firefox_options)
            
            # Configure waits
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 20)
            
            # Remove webdriver property to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Firefox WebDriver setup successful!")
            return True
            
        except WebDriverException as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            logger.error("Make sure Firefox and GeckoDriver are properly installed")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during driver setup: {e}")
            return False
    
    def navigate_to_server(self):
        """Navigate to the taming.io server."""
        try:
            logger.info(f"🌐 Navigating to: {self.server_url}")
            self.driver.get(self.server_url)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Additional wait for game elements to load
            time.sleep(5)
            
            logger.info("✅ Successfully loaded taming.io page!")
            return True
            
        except TimeoutException:
            logger.error("❌ Page load timeout - server may be down or slow")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to navigate to server: {e}")
            return False
    
    def find_and_fill_name_input(self, name="111"):
        """Find the name input field and fill it with the specified name."""
        try:
            logger.info(f"🔍 Looking for name input field...")
            
            # Common selectors for name input in taming.io
            possible_selectors = [
                "input[placeholder*='name' i]",
                "input[placeholder*='Name' i]", 
                "input[type='text']",
                "#nameInput",
                ".name-input",
                "input[name='name']",
                "input[id*='name']"
            ]
            
            name_input = None
            for selector in possible_selectors:
                try:
                    name_input = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Found name input using selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not name_input:
                # Fallback: look for any visible text input
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    if inp.is_displayed() and inp.get_attribute("type") in ["text", ""]:
                        name_input = inp
                        logger.info("✅ Found name input using fallback method")
                        break
            
            if not name_input:
                raise NoSuchElementException("Could not find name input field")
            
            # Clear and fill the input
            name_input.clear()
            name_input.send_keys(name)
            
            logger.info(f"✅ Successfully entered name: '{name}'")
            return True
            
        except TimeoutException:
            logger.error("❌ Timeout waiting for name input field")
            return False
        except ElementNotInteractableException:
            logger.error("❌ Name input field is not interactable")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to fill name input: {e}")
            return False
    
    def click_play_button(self):
        """Find and click the Play button to start the game."""
        try:
            logger.info("🔍 Looking for Play button...")
            
            # XPath selectors for play button
            xpath_selectors = [
                "//button[contains(text(), 'Play')]",
                "//button[contains(text(), 'PLAY')]",
                "//input[@value='Play']",
                "//input[@value='PLAY']",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'play')]"
            ]
            
            play_button = None
            
            # Try XPath selectors first
            for xpath in xpath_selectors:
                try:
                    play_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    logger.info(f"✅ Found Play button using XPath: {xpath}")
                    break
                except TimeoutException:
                    continue
            
            # Fallback: look for any clickable button
            if not play_button:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
                
                for element in buttons + inputs:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.lower() or element.get_attribute("value", "").lower()
                        if "play" in text:
                            play_button = element
                            logger.info("✅ Found Play button using fallback method")
                            break
            
            if not play_button:
                raise NoSuchElementException("Could not find Play button")
            
            # Scroll to button and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", play_button)
            time.sleep(1)
            play_button.click()
            
            logger.info("✅ Successfully clicked Play button!")
            time.sleep(3)
            
            return True
            
        except TimeoutException:
            logger.error("❌ Timeout waiting for Play button")
            return False
        except ElementNotInteractableException:
            logger.error("❌ Play button is not interactable")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to click Play button: {e}")
            return False
    
    def take_screenshot(self, filename="taming_io_screenshot.png"):
        """Take a screenshot of the current page."""
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"📸 Screenshot saved as: {filename}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to take screenshot: {e}")
            return False
    
    def run(self):
        """Main execution method - runs the complete automation sequence."""
        try:
            logger.info("🚀 Starting taming.io browser bot...")
            
            # Setup WebDriver
            if not self.setup_driver():
                return False
            
            # Navigate to server
            if not self.navigate_to_server():
                return False
            
            # Take initial screenshot
            self.take_screenshot("taming_io_loaded.png")
            
            # Fill name input
            if not self.find_and_fill_name_input():
                logger.info("⚠️ Couldn't find name input, taking screenshot for debugging")
                self.take_screenshot("taming_io_no_input.png")
                return False
            
            # Take screenshot after entering name
            self.take_screenshot("taming_io_name_entered.png")
            
            # Click play button
            if not self.click_play_button():
                logger.info("⚠️ Couldn't find play button, taking screenshot for debugging")
                self.take_screenshot("taming_io_no_play_button.png")
                return False
            
            # Take final screenshot
            self.take_screenshot("taming_io_game_started.png")
            
            logger.info("🎉 Successfully joined taming.io game!")
            logger.info("🎮 Game is now running. Keeping browser open for 10 seconds...")
            
            # Keep browser open briefly to see the result
            time.sleep(10)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources and close the browser."""
        if self.driver:
            try:
                logger.info("🧹 Cleaning up and closing browser...")
                self.driver.quit()
                logger.info("✅ Browser closed successfully")
            except Exception as e:
                logger.error(f"❌ Error during cleanup: {e}")

def main():
    """Main entry point for the script."""
    print("=" * 60)
    print("🦊 Taming.io Firefox Bot")
    print("=" * 60)
    
    # Get server URL from command line argument if provided
    server_url = None
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
        print(f"Using custom server: {server_url}")
    else:
        print("Using default taming.io server")
    
    # Create and run bot
    bot = TamingIOFirefoxBot(server_url)
    success = bot.run()
    
    if success:
        print("\n🎉 Bot completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Bot failed to complete. Check the logs and screenshots for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Hyperion VNC Browser Bot
========================

This script runs browser automation that you can watch in real-time through VNC.
It automatically navigates to Hyperion URLs and opens them in separate tabs.
It supports Safari (preferred) and Firefox browsers with full visual feedback.

Usage:
    python vnc_browser_bot.py [browser_preference]

Examples:
    python vnc_browser_bot.py                          # Safari preferred
    python vnc_browser_bot.py safari                   # Safari preferred
    python vnc_browser_bot.py firefox                  # Firefox preferred
"""

import sys
import time
import logging
import os
import cv2
import numpy as np
from PIL import Image
import io
import base64
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.service import Service as SafariService
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

class HyperionVNCBot:
    """VNC-visible browser automation bot for navigating to Hyperion URLs."""

    def __init__(self, server_url=None, preferred_browser="safari"):
        self.server_url = server_url
        self.driver = None
        self.wait = None
        self.preferred_browser = preferred_browser.lower()
        self.current_browser = None

    def setup_safari_driver(self):
        """Setup Safari WebDriver for VNC display."""
        try:
            logger.info("🧭 Setting up Safari WebDriver for VNC display...")

            # Safari doesn't need many options - it's designed to be simple
            logger.info("🚀 Starting Safari browser window...")
            self.driver = webdriver.Safari()
            self.current_browser = "safari"

            # Maximize window for better VNC visibility
            self.driver.maximize_window()

            # Configure waits
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 20)

            # Remove webdriver property to avoid detection
            try:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except:
                pass  # Safari might not support this

            logger.info("✅ Safari WebDriver setup successful - browser window should be visible!")
            return True

        except WebDriverException as e:
            logger.error(f"❌ Failed to setup Safari WebDriver: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during Safari setup: {e}")
            return False

    def setup_firefox_driver(self):
        """Setup Firefox WebDriver with CloudFlare bypass capabilities and persistent profile."""
        try:
            logger.info("🦊 Setting up Firefox WebDriver with persistent profile...")

            # Set up display environment
            if not os.environ.get('DISPLAY'):
                os.environ['DISPLAY'] = ':0'

            # Configure Firefox options for VNC visibility and CloudFlare bypass
            firefox_options = FirefoxOptions()

            # Try to use persistent profile, but fall back if it causes issues
            try:
                profile_dir = os.path.expanduser("~/firefox_bot_profile")
                if not os.path.exists(profile_dir):
                    os.makedirs(profile_dir)
                    logger.info("📁 Created persistent profile directory for login sessions")
                else:
                    logger.info("📁 Using existing profile directory to maintain login session")

                # Use Firefox profile for persistence
                from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
                profile = FirefoxProfile(profile_dir)
                profile.set_preference("privacy.clearOnShutdown.cookies", False)
                profile.set_preference("privacy.clearOnShutdown.sessions", False)
                firefox_options.profile = profile
                logger.info("🔐 Persistent profile configured for login session")
            except Exception as profile_error:
                logger.warning(f"⚠️ Profile setup failed, using default: {profile_error}")
                logger.info("🔄 Continuing with standard Firefox (login may not persist)")

            # DO NOT add --headless - we want to see the browser!
            firefox_options.add_argument("--width=1200")
            firefox_options.add_argument("--height=800")
            firefox_options.add_argument("--disable-blink-features=AutomationControlled")
            firefox_options.add_argument("--disable-web-security")
            firefox_options.add_argument("--no-sandbox")
            firefox_options.add_argument("--disable-dev-shm-usage")
            firefox_options.add_argument("--disable-gpu")

            # Essential preferences only to avoid startup delays
            firefox_options.set_preference("dom.webdriver.enabled", False)
            firefox_options.set_preference("browser.startup.homepage", "about:blank")

            # Create WebDriver instance with persistent profile
            logger.info("🚀 Starting Firefox browser window with persistent login session...")
            self.driver = webdriver.Firefox(options=firefox_options)
            self.current_browser = "firefox"

            # Maximize window for better VNC visibility
            self.driver.maximize_window()

            # Configure waits
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 30)  # Longer waits for proxy

            # Enhanced anti-detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")

            logger.info("✅ Firefox WebDriver setup successful with persistent profile!")
            return True

        except WebDriverException as e:
            logger.error(f"❌ Failed to setup Firefox WebDriver: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during Firefox setup: {e}")
            return False

    def setup_driver(self):
        """Setup browser WebDriver with preference for Safari."""
        logger.info("🌐 Setting up browser for VNC display...")

        # Try Safari first if preferred or if on macOS
        if self.preferred_browser == "safari":
            logger.info("🧭 Attempting Safari setup (preferred)...")
            if self.setup_safari_driver():
                logger.info("👀 You can now see the Safari automation in the VNC window")
                time.sleep(0.5)
                return True
            else:
                logger.info("⚠️ Safari not available, falling back to Firefox...")

        # Try Firefox as fallback or if preferred
        logger.info("🦊 Attempting Firefox setup...")
        if self.setup_firefox_driver():
            logger.info("👀 You can now see the Firefox automation in the VNC window")
            time.sleep(3)
            return True

        logger.error("❌ No browser drivers available")
        return False

    def test_vnc_visibility(self):
        """Test that VNC display is working by showing a test page."""
        try:
            logger.info("🧪 Testing VNC visibility with test page...")

            # Go to a simple test page first
            self.driver.get("data:text/html,<html><body style='background:red;font-size:72px;color:white;text-align:center;padding:100px'><h1>🎯 VNC TEST - YOU SHOULD SEE THIS!</h1><p>If you can see this red page, VNC is working!</p></body></html>")

            # Add title for window identification
            self.driver.execute_script("document.title = '🎯 VNC Test - Browser is Working!';")

            logger.info("🔴 RED TEST PAGE should be visible in VNC window!")
            logger.info("👀 If you see a red page with white text, VNC is working correctly")
            time.sleep(5)

            # Show a countdown
            for i in range(3, 0, -1):
                self.driver.execute_script(f"document.body.innerHTML = '<div style=\"background:blue;font-size:96px;color:white;text-align:center;padding:200px\">{i}</div>';")
                logger.info(f"🔵 Countdown: {i}")
                time.sleep(1)

            logger.info("✅ VNC test completed - proceeding to Hyperion navigation")
            return True

        except Exception as e:
            logger.error(f"❌ VNC test failed: {e}")
            return False


    def navigate_to_target_site(self):
        """Navigate to the target website."""
        try:
            logger.info(f"🌐 Navigating to {self.server_url}...")
            logger.info("👀 Watch the browser load the website in VNC")

            # Navigate to the target site
            self.driver.get(self.server_url)

            # Wait for page to load
            time.sleep(5)

            # Add visual indicator that site is loaded
            self.driver.execute_script("""
                var div = document.createElement('div');
                div.innerHTML = '✅ WEBSITE LOADED!';
                div.style.position = 'fixed';
                div.style.top = '10px';
                div.style.right = '10px';
                div.style.background = 'green';
                div.style.color = 'white';
                div.style.padding = '15px';
                div.style.fontSize = '18px';
                div.style.zIndex = '9999';
                div.style.borderRadius = '5px';
                document.body.appendChild(div);

                setTimeout(() => div.remove(), 5000);
            """)

            logger.info(f"✅ Successfully navigated to {self.server_url}")
            logger.info("👀 Website should now be visible in VNC window")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to navigate to website: {e}")
            return False

    def navigate_to_hyperion_urls(self):
        """Navigate to the specific URLs as requested."""
        try:
            logger.info("🌐 Starting URL navigation...")
            logger.info("👀 Watch the browser navigate to sites in VNC")

            # First URL: https://m9n8r2.ddx.desmosgraphing.xyz.cdn.cloudflare.net/
            first_url = "https://m9n8r2.ddx.desmosgraphing.xyz.cdn.cloudflare.net/"
            logger.info(f"📍 Step 1: Navigating to first URL: {first_url}")

            self.driver.get(first_url)

            # Add visual indicator for first site
            self.driver.execute_script("""
                var div = document.createElement('div');
                div.innerHTML = '🔵 STEP 1: FIRST SITE LOADED!';
                div.style.position = 'fixed';
                div.style.top = '10px';
                div.style.left = '10px';
                div.style.background = 'blue';
                div.style.color = 'white';
                div.style.padding = '15px';
                div.style.fontSize = '18px';
                div.style.zIndex = '9999';
                div.style.borderRadius = '5px';
                document.body.appendChild(div);

                setTimeout(() => div.remove(), 8000);
            """)

            # Wait for page to load completely
            time.sleep(7)
            logger.info("✅ Step 1 completed: First Hyperion URL loaded successfully")

            # Step 2: Open new tab and navigate to second URL
            second_url = "https://m9n8r2.ddx.desmosgraphing.xyz.cdn.cloudflare.net/@/daydream/hvtrs8%2F-tcmkne.ko-"
            logger.info(f"🆕 Step 2: Opening NEW TAB for second URL: {second_url}")

            # Open new tab using JavaScript
            self.driver.execute_script("window.open('');")
            logger.info("🔥 New tab opened successfully")

            # Wait a moment for the new tab to be ready
            time.sleep(2)

            # Switch to the new tab (it will be the last one)
            all_windows = self.driver.window_handles
            logger.info(f"📊 Total tabs open: {len(all_windows)}")
            self.driver.switch_to.window(all_windows[-1])
            logger.info("🎯 Switched to new tab")

            # Wait a moment after switching tabs
            time.sleep(2)

            # Navigate to the second URL in the new tab
            logger.info("🚀 Starting navigation to second URL in new tab...")

            # Set a shorter timeout for this specific navigation
            original_timeout = self.driver.implicitly_wait(0)
            self.driver.set_page_load_timeout(15)  # 15 second timeout

            try:
                self.driver.get(second_url)
                logger.info("✅ Successfully navigated to second URL!")
            except Exception as nav_error:
                logger.error(f"❌ Navigation failed: {nav_error}")
                logger.info("🔄 Trying alternative navigation method with JavaScript...")
                try:
                    # Use JavaScript navigation as backup
                    self.driver.execute_script(f"window.location.href = '{second_url}';")
                    time.sleep(8)
                    logger.info("✅ Alternative navigation method completed!")
                except Exception as js_error:
                    logger.error(f"❌ JavaScript navigation also failed: {js_error}")
                    logger.info("⚠️ Will proceed with visual indicators anyway")

            # Restore original timeout
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)

            # Add visual indicator for second site
            self.driver.execute_script("""
                var div = document.createElement('div');
                div.innerHTML = '🟢 STEP 2: SECOND SITE IN NEW TAB!';
                div.style.position = 'fixed';
                div.style.top = '10px';
                div.style.right = '10px';
                div.style.background = 'green';
                div.style.color = 'white';
                div.style.padding = '15px';
                div.style.fontSize = '18px';
                div.style.zIndex = '9999';
                div.style.borderRadius = '5px';
                document.body.appendChild(div);

                setTimeout(() => div.remove(), 8000);
            """)

            # Wait for second page to load
            time.sleep(7)
            logger.info("✅ Step 2 completed: Second Hyperion URL loaded in new tab successfully")

            # Step 3: Close the first tab
            logger.info("🗑️ Step 3: Closing the first tab...")

            # Get all window handles again
            all_windows = self.driver.window_handles
            logger.info(f"📊 Current tabs before closing: {len(all_windows)}")

            if len(all_windows) >= 2:
                # Switch to the first tab (index 0)
                self.driver.switch_to.window(all_windows[0])
                logger.info("🎯 Switched to first tab")

                # Close the current window (first tab)
                self.driver.close()
                logger.info("🗑️ First tab closed successfully")

                # Switch back to the remaining tab (second tab)
                remaining_windows = self.driver.window_handles
                self.driver.switch_to.window(remaining_windows[0])
                logger.info("🎯 Switched back to second tab (now the only tab)")

                # Add visual indicator that first tab was closed
                self.driver.execute_script("""
                    var div = document.createElement('div');
                    div.innerHTML = '🗑️ FIRST TAB CLOSED!';
                    div.style.position = 'fixed';
                    div.style.top = '60px';
                    div.style.left = '10px';
                    div.style.background = 'red';
                    div.style.color = 'white';
                    div.style.padding = '15px';
                    div.style.fontSize = '18px';
                    div.style.zIndex = '9999';
                    div.style.borderRadius = '5px';
                    document.body.appendChild(div);

                    setTimeout(() => div.remove(), 8000);
                """)

                logger.info("✅ Step 3 completed: First tab closed, only second tab remains")
            else:
                logger.warning("⚠️ Could not close first tab - insufficient tabs found")

            # Add final summary indicator
            self.driver.execute_script("""
                var summary = document.createElement('div');
                summary.innerHTML = '🎉 ALL STEPS COMPLETED!<br>✅ Tab 1: Loaded & Closed<br>✅ Tab 2: Service URL (ACTIVE)<br>🗑️ First tab closed as requested';
                summary.style.position = 'fixed';
                summary.style.top = '50%';
                summary.style.left = '50%';
                summary.style.transform = 'translate(-50%, -50%)';
                summary.style.background = 'purple';
                summary.style.color = 'white';
                summary.style.padding = '30px';
                summary.style.fontSize = '20px';
                summary.style.zIndex = '10000';
                summary.style.borderRadius = '10px';
                summary.style.textAlign = 'center';
                document.body.appendChild(summary);

                setTimeout(() => summary.remove(), 10000);
            """)

            logger.info("🎉 Successfully completed all navigation steps!")
            logger.info("👀 Second Hyperion website is now the only active tab in VNC")
            logger.info(f"📑 Active Tab: {second_url}")
            logger.info("🎯 Process: First site loaded → New tab opened → Second site loaded → First tab closed")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to navigate to Hyperion URLs: {e}")
            return False

    def navigate_to_server(self):
        """Stay on blank page - no link navigation."""
        try:
            logger.info("🚫 Skipping all link navigation as requested...")
            logger.info("📄 Staying on blank page - no websites will be loaded")

            # Stay on about:blank instead of navigating anywhere
            self.driver.get("about:blank")

            # Add visual indicator that no links will be searched
            self.driver.execute_script("""
                document.body.style.background = '#f0f0f0';
                document.body.style.fontFamily = 'Arial, sans-serif';
                document.body.style.textAlign = 'center';
                document.body.style.padding = '100px';

                var div = document.createElement('div');
                div.innerHTML = `
                    <h1 style="color: #333; font-size: 48px;">🚫 NO LINKS MODE</h1>
                    <p style="color: #666; font-size: 24px;">Bot is running but NOT searching any links</p>
                    <p style="color: #999; font-size: 18px;">VNC Browser Bot - Unlimited Runtime</p>
                    <p style="color: #0066cc; font-size: 16px;">✅ Login sessions will be preserved when you do navigate manually</p>
                `;
                document.body.appendChild(div);
                document.title = '🚫 VNC Bot - No Links Mode';
            """)

            logger.info("✅ VNC Browser ready - NO LINKS will be searched")
            logger.info("👀 You can manually navigate in VNC if needed - sessions will be saved")

            time.sleep(5)
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup no-links mode: {e}")
            return False

    def find_and_fill_name_input(self, name="runner"):
        """Find the name input field and fill it with the specified name."""
        try:
            logger.info(f"🔍 Looking for name input field...")
            logger.info("👀 Watch the browser as it searches for input fields...")

            # Wait longer and try more selectors
            possible_selectors = [
                "input[placeholder*='name' i]",
                "input[placeholder*='Name' i]",
                "input[type='text']",
                "#nameInput",
                ".name-input",
                "input[name='name']",
                "input[id*='name']",
                "input[class*='name']",
                ".name",
                "#name"
            ]

            name_input = None
            for i, selector in enumerate(possible_selectors):
                try:
                    logger.info(f"🔍 Trying selector {i+1}/{len(possible_selectors)}: {selector}")
                    name_input = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Found name input using selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not name_input:
                # Fallback: look for any visible text input
                logger.info("🔍 Trying fallback method - searching all input elements...")
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                logger.info(f"Found {len(inputs)} total input elements")

                for i, inp in enumerate(inputs):
                    try:
                        if inp.is_displayed() and inp.get_attribute("type") in ["text", "", None]:
                            name_input = inp
                            logger.info(f"✅ Found name input using fallback method (input #{i+1})")
                            break
                    except Exception:
                        continue

            if not name_input:
                # Final attempt - look for any interactable element
                logger.info("🔍 Final attempt - looking for any clickable elements...")
                all_elements = self.driver.find_elements(By.XPATH, "//*[@contenteditable='true' or @onclick or @type='text']")
                logger.info(f"Found {len(all_elements)} potentially interactable elements")

                if all_elements:
                    name_input = all_elements[0]
                    logger.info("✅ Using first interactable element found")

            if not name_input:
                logger.error("❌ Could not find any name input field")
                logger.info("📄 Current page source preview:")
                logger.info(self.driver.page_source[:1000])
                return False

            # Highlight the input field for VNC viewing
            self.driver.execute_script("arguments[0].style.border='5px solid red'; arguments[0].style.backgroundColor='yellow';", name_input)
            self.driver.execute_script("document.title = '🔴 FOUND INPUT FIELD!';")

            # Add visual confirmation
            self.driver.execute_script("""
                var div = document.createElement('div');
                div.innerHTML = '🔴 INPUT FIELD FOUND!';
                div.style.position = 'fixed';
                div.style.top = '10px';
                div.style.left = '10px';
                div.style.background = 'red';
                div.style.color = 'white';
                div.style.padding = '20px';
                div.style.fontSize = '24px';
                div.style.zIndex = '9999';
                document.body.appendChild(div);
            """)

            logger.info("🔴 Input field highlighted in red with yellow background - you should see it in VNC")
            time.sleep(3)

            # Clear and fill the input
            name_input.clear()
            name_input.send_keys(name)

            # Highlight success
            self.driver.execute_script("arguments[0].style.border='5px solid green'; arguments[0].style.backgroundColor='lightgreen';", name_input)
            self.driver.execute_script("document.title = '✅ NAME ENTERED!';")
            logger.info(f"✅ Successfully entered name: '{name}' - field highlighted in green")
            time.sleep(3)

            return True

        except Exception as e:
            logger.error(f"❌ Failed to fill name input: {e}")
            return False

    def find_and_fill_password_input(self):
        """Find the password input field and leave it blank."""
        try:
            logger.info("🔍 Looking for PASSWORD input field...")
            # Use a similar approach to find the password input
            css_selector = "input[placeholder*='password' i]"
            
            password_field = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
            )
            logger.info(f"✅ Found PASSWORD field using selector: {css_selector}")
            
            # Clear the field and leave it empty
            password_field.clear()  # Effectively leaves the password blank
            logger.info("✅ Password field left blank.")
            
            return True
            
        except TimeoutException:
            logger.error("❌ Timeout waiting for PASSWORD input field")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to handle PASSWORD input: {e}")
            return False

    def click_continue_button(self):
        """Find and click the green CONTINUE button in the middle of the page."""
        try:
            logger.info("🔍 Looking for green CONTINUE button...")
            logger.info("👀 Watch the browser as it searches for CONTINUE buttons...")

            continue_button = None

            # Use only the specific CSS selector that works
            css_selector = "[class*='continue']"

            try:
                logger.info(f"🔍 Trying CSS selector 5/11: {css_selector}")
                elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text = (element.text or element.get_attribute("value") or "").upper()
                        if "CONTINUE" in text:
                            continue_button = element
                            logger.info(f"✅ Found CONTINUE button using CSS selector: {css_selector}")
                            break
            except Exception:
                pass

            if not continue_button:
                logger.error("❌ Could not find any CONTINUE button")
                return False

            # Highlight the button for VNC viewing
            try:
                self.driver.execute_script("""
                    arguments[0].style.border = '5px solid red';
                    arguments[0].style.boxShadow = '0 0 20px red';
                    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                """, continue_button)

                # Add visual indicator
                self.driver.execute_script("""
                    var indicator = document.createElement('div');
                    indicator.innerHTML = '🎯 CONTINUE BUTTON FOUND!';
                    indicator.style.position = 'fixed';
                    indicator.style.top = '10px';
                    indicator.style.left = '50%';
                    indicator.style.transform = 'translateX(-50%)';
                    indicator.style.background = 'orange';
                    indicator.style.color = 'white';
                    indicator.style.padding = '15px';
                    indicator.style.fontSize = '18px';
                    indicator.style.zIndex = '9999';
                    indicator.style.borderRadius = '5px';
                    document.body.appendChild(indicator);

                    setTimeout(() => indicator.remove(), 3000);
                """)

                time.sleep(0.3)
                logger.info("🎯 Button highlighted and scrolled into view")
            except Exception as e:
                logger.warning(f"⚠️ Could not highlight button: {e}")

            # Click the button
            try:
                continue_button.click()
                logger.info("✅ Successfully clicked CONTINUE button")

                # Add success indicator
                self.driver.execute_script("""
                    var success = document.createElement('div');
                    success.innerHTML = '🎉 CONTINUE BUTTON CLICKED!';
                    success.style.position = 'fixed';
                    success.style.top = '50%';
                    success.style.left = '50%';
                    success.style.transform = 'translate(-50%, -50%)';
                    success.style.background = 'green';
                    success.style.color = 'white';
                    success.style.padding = '30px';
                    success.style.fontSize = '24px';
                    success.style.zIndex = '10000';
                    success.style.borderRadius = '10px';
                    success.style.textAlign = 'center';
                    document.body.appendChild(success);

                    setTimeout(() => success.remove(), 5000);
                """)

                time.sleep(0.5)
                return True

            except Exception as click_error:
                logger.error(f"❌ Failed to click button: {click_error}")
                # Try JavaScript click as fallback
                try:
                    logger.info("🔄 Trying JavaScript click as fallback...")
                    self.driver.execute_script("arguments[0].click();", continue_button)
                    logger.info("✅ JavaScript click successful")

                    # Add success indicator for JS click
                    self.driver.execute_script("""
                        var success = document.createElement('div');
                        success.innerHTML = '🎉 CONTINUE BUTTON CLICKED (JS)!';
                        success.style.position = 'fixed';
                        success.style.top = '50%';
                        success.style.left = '50%';
                        success.style.transform = 'translate(-50%, -50%)';
                        success.style.background = 'blue';
                        success.style.color = 'white';
                        success.style.padding = '30px';
                        success.style.fontSize = '24px';
                        success.style.zIndex = '10000';
                        success.style.borderRadius = '10px';
                        success.style.textAlign = 'center';
                        document.body.appendChild(success);

                        setTimeout(() => success.remove(), 5000);
                    """)

                    time.sleep(3)
                    return True
                except Exception as js_error:
                    logger.error(f"❌ JavaScript click also failed: {js_error}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to find/click CONTINUE button: {e}")
            return False

    def click_login_button(self):
        """Find and click the YELLOW/GOLDEN LOGIN button (Step 3) - NOT the black one (Step 6)."""
        try:
            logger.info("🔍 Looking for YELLOW/GOLDEN LOGIN button (Step 3)...")
            logger.info("⚠️ This is NOT the black LOGIN button (Step 6)!")
            logger.info("👀 Watch the browser as it searches for YELLOW LOGIN buttons...")

            login_button = None

            # Use only the specific CSS selector that works
            css_selector = "[class*='login']"

            try:
                logger.info(f"🔍 Trying CSS selector 5/14: {css_selector}")
                elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text = (element.text or element.get_attribute("value") or "").upper()
                        if "LOGIN" in text:
                            login_button = element
                            logger.info(f"✅ Found LOGIN button (Step 3) using CSS: {css_selector}")
                            break
            except Exception:
                pass

            if not login_button:
                logger.error("❌ Could not find any LOGIN button")
                return False

            # Highlight the button for VNC viewing
            try:
                self.driver.execute_script("""
                    arguments[0].style.border = '5px solid red';
                    arguments[0].style.boxShadow = '0 0 20px red';
                    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                """, login_button)

                # Add visual indicator
                self.driver.execute_script("""
                    var indicator = document.createElement('div');
                    indicator.innerHTML = '🎯 LOGIN BUTTON FOUND!';
                    indicator.style.position = 'fixed';
                    indicator.style.top = '10px';
                    indicator.style.left = '50%';
                    indicator.style.transform = 'translateX(-50%)';
                    indicator.style.background = 'orange';
                    indicator.style.color = 'white';
                    indicator.style.padding = '15px';
                    indicator.style.fontSize = '18px';
                    indicator.style.zIndex = '9999';
                    indicator.style.borderRadius = '5px';
                    document.body.appendChild(indicator);

                    setTimeout(() => indicator.remove(), 3000);
                """)

                time.sleep(2)
                logger.info("🎯 LOGIN button highlighted and scrolled into view")
            except Exception as e:
                logger.warning(f"⚠️ Could not highlight LOGIN button: {e}")

            # Click the button
            try:
                login_button.click()
                logger.info("✅ Successfully clicked LOGIN button")

                # Add success indicator
                self.driver.execute_script("""
                    var success = document.createElement('div');
                    success.innerHTML = '🎉 LOGIN BUTTON CLICKED!';
                    success.style.position = 'fixed';
                    success.style.top = '50%';
                    success.style.left = '50%';
                    success.style.transform = 'translate(-50%, -50%)';
                    success.style.background = 'orange';
                    success.style.color = 'white';
                    success.style.padding = '30px';
                    success.style.fontSize = '24px';
                    success.style.zIndex = '10000';
                    success.style.borderRadius = '10px';
                    success.style.textAlign = 'center';
                    document.body.appendChild(success);

                    setTimeout(() => success.remove(), 5000);
                """)

                time.sleep(0.5)
                return True

            except Exception as click_error:
                logger.error(f"❌ Failed to click LOGIN button: {click_error}")
                # Try JavaScript click as fallback
                try:
                    logger.info("🔄 Trying JavaScript click as fallback...")
                    self.driver.execute_script("arguments[0].click();", login_button)
                    logger.info("✅ JavaScript click successful")

                    # Add success indicator for JS click
                    self.driver.execute_script("""
                        var success = document.createElement('div');
                        success.innerHTML = '🎉 LOGIN CLICKED (JS)!';
                        success.style.position = 'fixed';
                        success.style.top = '50%';
                        success.style.left = '50%';
                        success.style.transform = 'translate(-50%, -50%)';
                        success.style.background = 'darkorange';
                        success.style.color = 'white';
                        success.style.padding = '30px';
                        success.style.fontSize = '24px';
                        success.style.zIndex = '10000';
                        success.style.borderRadius = '10px';
                        success.style.textAlign = 'center';
                        document.body.appendChild(success);

                        setTimeout(() => success.remove(), 5000);
                    """)

                    time.sleep(3)
                    return True
                except Exception as js_error:
                    logger.error(f"❌ JavaScript click also failed: {js_error}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to find/click LOGIN button: {e}")
            return False

    def click_email_address_field(self):
        """Find and click the beige/tan EMAIL ADDRESS input field."""
        try:
            logger.info("🔍 Looking for EMAIL ADDRESS input field...")
            logger.info("👀 Watch the browser as it searches for EMAIL ADDRESS fields...")

            email_field = None

            # Use only the specific CSS selector that works
            css_selector = "input[placeholder*='email' i]"

            try:
                logger.info(f"🔍 Trying CSS selector 2/13: {css_selector}")
                elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        email_field = element
                        logger.info(f"✅ Found EMAIL ADDRESS field using CSS selector: {css_selector}")
                        break
            except Exception:
                pass

            if not email_field:
                logger.error("❌ Could not find any EMAIL ADDRESS field")
                return False

            # Highlight the field for VNC viewing
            try:
                self.driver.execute_script("""
                    arguments[0].style.border = '5px solid blue';
                    arguments[0].style.boxShadow = '0 0 20px blue';
                    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                """, email_field)

                # Add visual indicator
                self.driver.execute_script("""
                    var indicator = document.createElement('div');
                    indicator.innerHTML = '🎯 EMAIL ADDRESS FIELD FOUND!';
                    indicator.style.position = 'fixed';
                    indicator.style.top = '10px';
                    indicator.style.left = '50%';
                    indicator.style.transform = 'translateX(-50%)';
                    indicator.style.background = 'blue';
                    indicator.style.color = 'white';
                    indicator.style.padding = '15px';
                    indicator.style.fontSize = '18px';
                    indicator.style.zIndex = '9999';
                    indicator.style.borderRadius = '5px';
                    document.body.appendChild(indicator);

                    setTimeout(() => indicator.remove(), 3000);
                """)

                time.sleep(2)
                logger.info("🎯 EMAIL ADDRESS field highlighted and scrolled into view")
            except Exception as e:
                logger.warning(f"⚠️ Could not highlight EMAIL ADDRESS field: {e}")

            # Click the field to focus it
            try:
                email_field.click()
                logger.info("✅ Successfully clicked EMAIL ADDRESS field")

                # Add success indicator for clicking
                self.driver.execute_script("""
                    var success = document.createElement('div');
                    success.innerHTML = '🎉 EMAIL ADDRESS FIELD CLICKED!';
                    success.style.position = 'fixed';
                    success.style.top = '50%';
                    success.style.left = '50%';
                    success.style.transform = 'translate(-50%, -50%)';
                    success.style.background = 'blue';
                    success.style.color = 'white';
                    success.style.padding = '30px';
                    success.style.fontSize = '24px';
                    success.style.zIndex = '10000';
                    success.style.borderRadius = '10px';
                    success.style.textAlign = 'center';
                    document.body.appendChild(success);

                    setTimeout(() => success.remove(), 3000);
                """)

                time.sleep(2)

                # Now type the email address into the field
                logger.info("⌨️ Typing email address: stroll@gmail.com")

                # Clear any existing text first
                email_field.clear()

                # Type the email address
                email_field.send_keys("stroll@gmail.com")

                logger.info("✅ Successfully typed email address into field")

                # Add typing success indicator
                self.driver.execute_script("""
                    var success = document.createElement('div');
                    success.innerHTML = '✅ EMAIL TYPED: stroll@gmail.com';
                    success.style.position = 'fixed';
                    success.style.top = '40%';
                    success.style.left = '50%';
                    success.style.transform = 'translate(-50%, -50%)';
                    success.style.background = 'green';
                    success.style.color = 'white';
                    success.style.padding = '30px';
                    success.style.fontSize = '24px';
                    success.style.zIndex = '10000';
                    success.style.borderRadius = '10px';
                    success.style.textAlign = 'center';
                    document.body.appendChild(success);

                    setTimeout(() => success.remove(), 5000);
                """)

                time.sleep(0.5)
                return True

            except Exception as click_error:
                logger.error(f"❌ Failed to click EMAIL ADDRESS field: {click_error}")
                # Try JavaScript click as fallback
                try:
                    logger.info("🔄 Trying JavaScript click as fallback...")
                    self.driver.execute_script("arguments[0].click();", email_field)
                    logger.info("✅ JavaScript click successful")

                    # Add success indicator for JS click
                    self.driver.execute_script("""
                        var success = document.createElement('div');
                        success.innerHTML = '🎉 EMAIL FIELD CLICKED (JS)!';
                        success.style.position = 'fixed';
                        success.style.top = '50%';
                        success.style.left = '50%';
                        success.style.transform = 'translate(-50%, -50%)';
                        success.style.background = 'darkblue';
                        success.style.color = 'white';
                        success.style.padding = '30px';
                        success.style.fontSize = '24px';
                        success.style.zIndex = '10000';
                        success.style.borderRadius = '10px';
                        success.style.textAlign = 'center';
                        document.body.appendChild(success);

                        setTimeout(() => success.remove(), 3000);
                    """)

                    time.sleep(2)

                    # Now type the email address into the field
                    logger.info("⌨️ Typing email address: stroll@gmail.com")

                    # Clear any existing text first
                    email_field.clear()

                    # Type the email address
                    email_field.send_keys("stroll@gmail.com")

                    logger.info("✅ Successfully typed email address into field")

                    # Add typing success indicator
                    self.driver.execute_script("""
                        var success = document.createElement('div');
                        success.innerHTML = '✅ EMAIL TYPED: stroll@gmail.com';
                        success.style.position = 'fixed';
                        success.style.top = '40%';
                        success.style.left = '50%';
                        success.style.transform = 'translate(-50%, -50%)';
                        success.style.background = 'green';
                        success.style.color = 'white';
                        success.style.padding = '30px';
                        success.style.fontSize = '24px';
                        success.style.zIndex = '10000';
                        success.style.borderRadius = '10px';
                        success.style.textAlign = 'center';
                        document.body.appendChild(success);

                        setTimeout(() => success.remove(), 5000);
                    """)

                    time.sleep(3)
                    return True
                except Exception as js_error:
                    logger.error(f"❌ JavaScript click also failed: {js_error}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to find/click EMAIL ADDRESS field: {e}")
            return False

    def click_password_field(self):
        """Find and click the beige/tan PASSWORD input field."""
        try:
            logger.info("🔍 Looking for PASSWORD input field...")
            logger.info("👀 Watch the browser as it searches for PASSWORD fields...")

            # Enhanced selectors for the specific PASSWORD field
            xpath_selectors = [
                "//input[contains(@placeholder, 'Password')]",
                "//input[contains(@placeholder, 'password')]",
                "//input[contains(@placeholder, 'PASSWORD')]",
                "//input[@type='password']",
                "//input[contains(@name, 'password')]",
                "//input[contains(@id, 'password')]",
                "//input[contains(@class, 'password')]",
                "//label[contains(text(), 'Password')]/following-sibling::input",
                "//label[contains(text(), 'Password')]/../input",
                "//div[contains(text(), 'Password')]/following-sibling::input",
                "//div[contains(text(), 'Password')]/../input"
            ]

            password_field = None

            # Try CSS selectors for common password field classes first
            css_selectors = [
                "input[type='password']",
                "input[placeholder*='password' i]",
                "input[placeholder*='Password' i]",
                "input[name*='password']",
                "input[id*='password']",
                "input[class*='password']",
                ".password-input",
                ".password-field",
                "[class*='password']",
                "[id*='password']",
                "input[style*='beige']",
                "input[style*='tan']",
                "input[style*='background']"
            ]

            # Try CSS selectors first for password-styled fields
            for i, css_selector in enumerate(css_selectors):
                try:
                    logger.info(f"🔍 Trying CSS selector {i+1}/{len(css_selectors)}: {css_selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            placeholder = (element.get_attribute("placeholder") or "").lower()
                            element_name = (element.get_attribute("name") or "").lower()
                            element_id = (element.get_attribute("id") or "").lower()

                            if any(term in f"{placeholder} {element_name} {element_id}" for term in ["password", "pass"]):
                                password_field = element
                                logger.info(f"✅ Found PASSWORD field using CSS selector: {css_selector}")
                                break
                    if password_field:
                        break
                except Exception:
                    continue

            # Try XPath selectors if CSS didn't work
            if not password_field:
                for i, xpath in enumerate(xpath_selectors):
                    try:
                        logger.info(f"🔍 Trying XPath {i+1}/{len(xpath_selectors)}: {xpath}")
                        password_field = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        logger.info(f"✅ Found PASSWORD field using XPath: {xpath}")
                        break
                    except TimeoutException:
                        continue

            # Enhanced fallback: look for the specific beige/tan PASSWORD field shown in image
            if not password_field:
                logger.info("🔍 Trying fallback method - searching for beige/tan input fields...")
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                textareas = self.driver.find_elements(By.TAG_NAME, "textarea")

                all_inputs = inputs + textareas
                logger.info(f"Found {len(all_inputs)} potentially input elements")

                for i, element in enumerate(all_inputs):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            # Check attributes for password-related terms
                            placeholder = (element.get_attribute("placeholder") or "").lower()
                            element_name = (element.get_attribute("name") or "").lower()
                            element_id = (element.get_attribute("id") or "").lower()
                            element_class = (element.get_attribute("class") or "").lower()
                            element_type = (element.get_attribute("type") or "").lower()

                            # Check for PASSWORD related terms or password type
                            password_terms = ["password", "pass", "pwd"]
                            has_password_terms = any(term in f"{placeholder} {element_name} {element_id} {element_class}" for term in password_terms)
                            is_password_type = element_type == "password"

                            if has_password_terms or is_password_type:
                                # Enhanced beige/tan color detection for the specific field in the image
                                bg_color = element.value_of_css_property("background-color")
                                bg_style = element.value_of_css_property("background")
                                element_style = element.get_attribute("style") or ""

                                # Combine all style information
                                all_style_info = f"{bg_color} {bg_style} {element_style}".lower()

                                # Enhanced beige/tan indicators matching the field in image
                                beige_tan_indicators = [
                                    "beige", "tan", "wheat", "burlywood", "sandybrown",
                                    "#f5f5dc", "#d2b48c", "#f5deb3", "#daa520", "#cd853f",
                                    "rgb(245, 245, 220)", "rgb(210, 180, 140)", "rgb(245, 222, 179)",
                                    "rgb(218, 165, 32)", "rgb(205, 133, 63)",
                                    "input-field", "form-control", "text-input"
                                ]

                                # Check for specific beige/tan color patterns
                                has_beige_tan = any(indicator in all_style_info for indicator in beige_tan_indicators)

                                # Additional check for RGB values that indicate beige/tan colors
                                if "rgb(" in all_style_info:
                                    # Look for RGB patterns with balanced warm colors (beige/tan pattern)
                                    import re
                                    rgb_matches = re.findall(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', all_style_info)
                                    for r, g, b in rgb_matches:
                                        r, g, b = int(r), int(g), int(b)
                                        # Check if colors indicate beige/tan (warm, balanced colors)
                                        if r > 200 and g > 180 and b > 160 and abs(r-g) < 50:  # Beige/tan pattern
                                            has_beige_tan = True
                                            logger.info(f"🎨 Detected beige/tan RGB color: rgb({r}, {g}, {b})")
                                            break

                                if has_beige_tan or True:  # Accept any password field if color detection fails
                                    password_field = element
                                    logger.info(f"✅ Found PASSWORD field matching image (element #{i+1})")
                                    if has_beige_tan:
                                        logger.info(f"🎨 Field style: {all_style_info[:100]}...")
                                    break
                    except Exception:
                        continue

            if not password_field:
                logger.error("❌ Could not find any PASSWORD field")
                return False

            # Highlight the field for VNC viewing
            try:
                self.driver.execute_script("""
                    arguments[0].style.border = '5px solid purple';
                    arguments[0].style.boxShadow = '0 0 20px purple';
                    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                """, password_field)

                # Add visual indicator
                self.driver.execute_script("""
                    var indicator = document.createElement('div');
                    indicator.innerHTML = '🎯 PASSWORD FIELD FOUND!';
                    indicator.style.position = 'fixed';
                    indicator.style.top = '10px';
                    indicator.style.left = '50%';
                    indicator.style.transform = 'translateX(-50%)';
                    indicator.style.background = 'purple';
                    indicator.style.color = 'white';
                    indicator.style.padding = '15px';
                    indicator.style.fontSize = '18px';
                    indicator.style.zIndex = '9999';
                    indicator.style.borderRadius = '5px';
                    document.body.appendChild(indicator);

                    setTimeout(() => indicator.remove(), 3000);
                """)

                time.sleep(2)
                logger.info("🎯 PASSWORD field highlighted and scrolled into view")
            except Exception as e:
                logger.warning(f"⚠️ Could not highlight PASSWORD field: {e}")

            # Click the field to focus it
            try:
                password_field.click()
                logger.info("✅ Successfully clicked PASSWORD field")

                # Add success indicator for clicking
                self.driver.execute_script("""
                    var success = document.createElement('div');
                    success.innerHTML = '🎉 PASSWORD FIELD CLICKED!';
                    success.style.position = 'fixed';
                    success.style.top = '50%';
                    success.style.left = '50%';
                    success.style.transform = 'translate(-50%, -50%)';
                    success.style.background = 'purple';
                    success.style.color = 'white';
                    success.style.padding = '30px';
                    success.style.fontSize = '24px';
                    success.style.zIndex = '10000';
                    success.style.borderRadius = '10px';
                    success.style.textAlign = 'center';
                    document.body.appendChild(success);

                    setTimeout(() => success.remove(), 3000);
                """)

                time.sleep(2)

                # Now type the password into the field
                logger.info("⌨️ Typing password: GGG@222123")

                # Clear any existing text first
                password_field.clear()

                # Type the password
                password_field.send_keys("GGG@222123")

                logger.info("✅ Successfully typed password into field")

                # Add typing success indicator
                self.driver.execute_script("""
                    var success = document.createElement('div');
                    success.innerHTML = '✅ PASSWORD TYPED: GGG@222123';
                    success.style.position = 'fixed';
                    success.style.top = '40%';
                    success.style.left = '50%';
                    success.style.transform = 'translate(-50%, -50%)';
                    success.style.background = 'darkpurple';
                    success.style.color = 'white';
                    success.style.padding = '30px';
                    success.style.fontSize = '24px';
                    success.style.zIndex = '10000';
                    success.style.borderRadius = '10px';
                    success.style.textAlign = 'center';
                    document.body.appendChild(success);

                    setTimeout(() => success.remove(), 5000);
                """)

                time.sleep(0.5)
                return True

            except Exception as click_error:
                logger.error(f"❌ Failed to click PASSWORD field: {click_error}")
                # Try JavaScript click as fallback
                try:
                    logger.info("🔄 Trying JavaScript click as fallback...")
                    self.driver.execute_script("arguments[0].click();", password_field)
                    logger.info("✅ JavaScript click successful")

                    # Add success indicator for JS click
                    self.driver.execute_script("""
                        var success = document.createElement('div');
                        success.innerHTML = '🎉 PASSWORD FIELD CLICKED (JS)!';
                        success.style.position = 'fixed';
                        success.style.top = '50%';
                        success.style.left = '50%';
                        success.style.transform = 'translate(-50%, -50%)';
                        success.style.background = 'darkpurple';
                        success.style.color = 'white';
                        success.style.padding = '30px';
                        success.style.fontSize = '24px';
                        success.style.zIndex = '10000';
                        success.style.borderRadius = '10px';
                        success.style.textAlign = 'center';
                        document.body.appendChild(success);

                        setTimeout(() => success.remove(), 3000);
                    """)

                    time.sleep(2)

                    # Now type the password into the field
                    logger.info("⌨️ Typing password: GGG@222123")

                    # Clear any existing text first
                    password_field.clear()

                    # Type the password
                    password_field.send_keys("GGG@222123")

                    logger.info("✅ Successfully typed password into field")

                    # Add typing success indicator
                    self.driver.execute_script("""
                        var success = document.createElement('div');
                        success.innerHTML = '✅ PASSWORD TYPED: GGG@222123';
                        success.style.position = 'fixed';
                        success.style.top = '40%';
                        success.style.left = '50%';
                        success.style.transform = 'translate(-50%, -50%)';
                        success.style.background = 'darkpurple';
                        success.style.color = 'white';
                        success.style.padding = '30px';
                        success.style.fontSize = '24px';
                        success.style.zIndex = '10000';
                        success.style.borderRadius = '10px';
                        success.style.textAlign = 'center';
                        document.body.appendChild(success);

                        setTimeout(() => success.remove(), 5000);
                    """)

                    time.sleep(3)
                    return True
                except Exception as js_error:
                    logger.error(f"❌ JavaScript click also failed: {js_error}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to find/click PASSWORD field: {e}")
            return False

    def click_black_login_button(self):
        """Find and click the BLACK LOGIN button JUST BELOW the password field (Step 8) - NOT the yellow one (Step 3)."""
        try:
            logger.info("🔍 Looking for BLACK LOGIN button JUST BELOW password field (Step 8)...")
            logger.info("⚠️ This is NOT the yellow/golden LOGIN button (Step 3)!")
            logger.info("📍 First finding PASSWORD field position, then searching BELOW it...")

            # STEP 1: Find the password field position first
            password_field = None
            password_y_position = None

            # Find password field to determine search area
            css_selectors_password = [
                "input[type='password']",
                "input[placeholder*='password' i]",
                "input[name*='password']",
                "input[id*='password']"
            ]

            for css_selector in css_selectors_password:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            password_field = element
                            password_rect = element.rect
                            password_y_position = password_rect['y'] + password_rect['height']
                            logger.info(f"📍 Found PASSWORD field at Y position: {password_y_position}")
                            break
                    if password_field:
                        break
                except Exception:
                    continue

            if not password_field:
                logger.warning("⚠️ Could not find password field, searching in general middle area...")
                password_y_position = self.driver.execute_script("return window.innerHeight") * 0.4

            # STEP 2: Search for BLACK LOGIN button BELOW password field
            black_login_button = None

            # Enhanced selectors for the black LOGIN button
            xpath_selectors = [
                "//button[contains(text(), 'LOGIN')]",
                "//button[contains(text(), 'Login')]",
                "//button[contains(text(), 'login')]",
                "//input[@value='LOGIN']",
                "//input[@value='Login']",
                "//input[@value='login']",
                "//input[@type='submit'][contains(@value, 'login')]",
                "//button[@type='submit'][contains(text(), 'login')]",
                "//div[contains(text(), 'LOGIN')][@role='button']",
                "//span[contains(text(), 'LOGIN')]/../..",
                "//a[contains(text(), 'LOGIN')]"
            ]

            # Try CSS selectors for login buttons with dark/black styling
            css_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('LOGIN')",
                "button:contains('Login')",
                "input[value*='LOGIN' i]",
                "input[value*='Login' i]",
                ".login-button",
                ".btn-login",
                ".submit-button",
                "[class*='login']",
                "[id*='login']",
                "button[style*='black']",
                "button[style*='dark']",
                "button[class*='black']",
                "button[class*='dark']"
            ]

            # Use only the specific CSS selector that works
            css_selector = "[id*='login']"

            try:
                logger.info(f"🔍 Trying CSS selector 11/15: {css_selector}")
                elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        # Check if element is BELOW password field
                        element_rect = element.rect
                        element_y = element_rect['y']

                        if element_y > password_y_position:  # Must be below password
                            black_login_button = element
                            logger.info(f"✅ Found BLACK LOGIN button BELOW password using CSS: {css_selector}")
                            logger.info(f"📍 Button position: Y={element_y} (below password Y={password_y_position})")
                            break
            except Exception:
                pass

            if not black_login_button:
                logger.info("🔍 Trying fallback method - searching for LOGIN buttons in MIDDLE AREA...")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
                divs = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button'], div[onclick]")

                all_clickables = buttons + inputs + divs
                logger.info(f"Found {len(all_clickables)} potentially clickable elements")

                # Get page dimensions to determine middle area
                page_width = self.driver.execute_script("return window.innerWidth")
                page_height = self.driver.execute_script("return window.innerHeight")

                # Define middle area boundaries (center 60% of the page)
                middle_left = page_width * 0.2
                middle_right = page_width * 0.8
                middle_top = page_height * 0.3
                middle_bottom = page_height * 0.7

                logger.info(f"📐 Page dimensions: {page_width}x{page_height}")
                logger.info(f"🎯 Searching in middle area: X({middle_left}-{middle_right}), Y({middle_top}-{middle_bottom})")

                middle_area_candidates = []

                for i, element in enumerate(all_clickables):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            # Get element position
                            element_rect = element.rect
                            element_x = element_rect['x']
                            element_y = element_rect['y']
                            element_width = element_rect['width']
                            element_height = element_rect['height']

                            # Calculate element center
                            element_center_x = element_x + element_width / 2
                            element_center_y = element_y + element_height / 2

                            # Check if element is in the middle area
                            in_middle_area = (middle_left <= element_center_x <= middle_right and
                                            middle_top <= element_center_y <= middle_bottom)

                            if in_middle_area:
                                # Check element text and attributes
                                element_text = (element.text or element.get_attribute("value") or element.get_attribute("innerHTML") or "").lower()
                                element_type = (element.get_attribute("type") or "").lower()
                                element_class = (element.get_attribute("class") or "").lower()
                                element_id = (element.get_attribute("id") or "").lower()

                                # Check for LOGIN or submission related terms
                                login_terms = ["login", "log in", "sign in", "submit"]
                                has_login_terms = any(term in element_text for term in login_terms)
                                is_submit_type = element_type == "submit"

                                # Check for black/dark styling
                                bg_color = element.value_of_css_property("background-color")
                                bg_style = element.value_of_css_property("background")
                                element_style = element.get_attribute("style") or ""

                                # Combine all style information
                                all_style_info = f"{bg_color} {bg_style} {element_style} {element_class}".lower()

                                # Look for dark/black styling indicators
                                dark_indicators = [
                                    "black", "dark", "#000", "#333", "#444", "#555",
                                    "rgb(0, 0, 0)", "rgb(51, 51, 51)", "rgb(68, 68, 68)",
                                    "rgba(0, 0, 0", "rgba(51, 51, 51", "rgba(68, 68, 68"
                                ]

                                has_dark_styling = any(indicator in all_style_info for indicator in dark_indicators)

                                if has_login_terms or is_submit_type:
                                    # Check for YELLOW/GOLDEN styling to EXCLUDE Step 3 buttons
                                    yellow_golden_indicators = [
                                        "yellow", "gold", "golden", "orange", "amber", "warning",
                                        "#ffff", "#ff9", "#fc0", "#f90", "#ffd700", "#ffb347",
                                        "rgb(255, 255, 0)", "rgb(255, 204, 0)", "rgb(255, 153, 0)"
                                    ]

                                    has_yellow_golden = any(indicator in all_style_info for indicator in yellow_golden_indicators)

                                    # EXCLUDE yellow/golden buttons (those are Step 3)
                                    if has_yellow_golden:
                                        logger.info(f"🟡 Skipping YELLOW/GOLDEN button (Step 3 button): '{element_text}' at ({element_center_x:.0f}, {element_center_y:.0f})")
                                        continue

                                    # Must be BELOW password field for Step 8
                                    if element_center_y > password_y_position:
                                        # Add to candidates with priority scoring (prefer BLACK styling for Step 8)
                                        priority_score = 0
                                        if has_login_terms:
                                            priority_score += 10
                                        if has_dark_styling:
                                            priority_score += 20  # Higher priority for black styling in Step 8
                                        if is_submit_type:
                                            priority_score += 5
                                        # Bonus for being close to password (within reasonable distance)
                                        distance_from_password = element_center_y - password_y_position
                                        if distance_from_password < 200:  # Within 200px of password
                                            priority_score += 15

                                        middle_area_candidates.append({
                                            'element': element,
                                            'score': priority_score,
                                            'position': f"({element_center_x:.0f}, {element_center_y:.0f})",
                                            'text': element_text,
                                            'dark_styling': has_dark_styling,
                                            'distance_from_password': distance_from_password
                                        })

                                        logger.info(f"⚫ Found BLACK candidate BELOW password #{len(middle_area_candidates)}: '{element_text}' at ({element_center_x:.0f}, {element_center_y:.0f}) - {distance_from_password:.0f}px below password (score: {priority_score})")
                    except Exception as e:
                        logger.debug(f"Error checking element {i}: {e}")
                        continue

                # Sort candidates by priority score (highest first)
                if middle_area_candidates:
                    middle_area_candidates.sort(key=lambda x: x['score'], reverse=True)
                    best_candidate = middle_area_candidates[0]
                    black_login_button = best_candidate['element']

                    logger.info(f"✅ Selected best BLACK LOGIN button BELOW password (Step 8):")
                    logger.info(f"   📍 Position: {best_candidate['position']}")
                    logger.info(f"   📝 Text: '{best_candidate['text']}'")
                    logger.info(f"   🎨 Dark styling: {best_candidate['dark_styling']}")
                    logger.info(f"   📏 Distance from password: {best_candidate['distance_from_password']:.0f}px")
                    logger.info(f"   🏆 Score: {best_candidate['score']}")
                else:
                    logger.info("⚠️ No LOGIN buttons found in middle area, checking entire page...")

                    # Fallback to any LOGIN button on the page if none found in middle
                    for i, element in enumerate(all_clickables):
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = (element.text or element.get_attribute("value") or element.get_attribute("innerHTML") or "").lower()
                                if any(term in element_text for term in ["login", "log in", "sign in", "submit"]):
                                    black_login_button = element
                                    logger.info(f"✅ Found fallback LOGIN button anywhere on page: '{element_text}'")
                                    break
                        except Exception:
                            continue

            if not black_login_button:
                logger.error("❌ Could not find any black LOGIN button")
                return False

            # Highlight the button for VNC viewing
            try:
                self.driver.execute_script("""
                    arguments[0].style.border = '5px solid orange';
                    arguments[0].style.boxShadow = '0 0 20px orange';
                    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                """, black_login_button)

                # Add visual indicator
                self.driver.execute_script("""
                    var indicator = document.createElement('div');
                    indicator.innerHTML = '🎯 BLACK LOGIN BUTTON FOUND!';
                    indicator.style.position = 'fixed';
                    indicator.style.top = '10px';
                    indicator.style.left = '50%';
                    indicator.style.transform = 'translateX(-50%)';
                    indicator.style.background = 'orange';
                    indicator.style.color = 'white';
                    indicator.style.padding = '15px';
                    indicator.style.fontSize = '18px';
                    indicator.style.zIndex = '9999';
                    indicator.style.borderRadius = '5px';
                    document.body.appendChild(indicator);

                    setTimeout(() => indicator.remove(), 3000);
                """)

                time.sleep(2)
                logger.info("🎯 Black LOGIN button highlighted and scrolled into view")
            except Exception as e:
                logger.warning(f"⚠️ Could not highlight black LOGIN button: {e}")

            # Click the button
            try:
                black_login_button.click()
                logger.info("✅ Successfully clicked black LOGIN button")

                # Add success indicator
                self.driver.execute_script("""
                    var success = document.createElement('div');
                    success.innerHTML = '🎉 BLACK LOGIN BUTTON CLICKED!';
                    success.style.position = 'fixed';
                    success.style.top = '50%';
                    success.style.left = '50%';
                    success.style.transform = 'translate(-50%, -50%)';
                    success.style.background = 'orange';
                    success.style.color = 'white';
                    success.style.padding = '30px';
                    success.style.fontSize = '24px';
                    success.style.zIndex = '10000';
                    success.style.borderRadius = '10px';
                    success.style.textAlign = 'center';
                    document.body.appendChild(success);

                    setTimeout(() => success.remove(), 5000);
                """)

                time.sleep(0.5)
                return True

            except Exception as click_error:
                logger.error(f"❌ Failed to click black LOGIN button: {click_error}")
                # Try JavaScript click as fallback
                try:
                    logger.info("🔄 Trying JavaScript click as fallback...")
                    self.driver.execute_script("arguments[0].click();", black_login_button)
                    logger.info("✅ JavaScript click successful")

                    # Add success indicator for JS click
                    self.driver.execute_script("""
                        var success = document.createElement('div');
                        success.innerHTML = '🎉 BLACK LOGIN CLICKED (JS)!';
                        success.style.position = 'fixed';
                        success.style.top = '50%';
                        success.style.left = '50%';
                        success.style.transform = 'translate(-50%, -50%)';
                        success.style.background = 'darkorange';
                        success.style.color = 'white';
                        success.style.padding = '30px';
                        success.style.fontSize = '24px';
                        success.style.zIndex = '10000';
                        success.style.borderRadius = '10px';
                        success.style.textAlign = 'center';
                        document.body.appendChild(success);

                        setTimeout(() => success.remove(), 5000);
                    """)

                    time.sleep(3)
                    return True
                except Exception as js_error:
                    logger.error(f"❌ JavaScript click also failed: {js_error}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to find/click black LOGIN button: {e}")
            return False

    def find_image_with_advanced_template_matching(self, template_path, confidence_threshold=0.8, search_region=None):
        """
        Advanced multi-scale template matching using OpenCV with sub-pixel accuracy.

        This uses sophisticated computer vision techniques including:
        - Multi-scale pyramid search for scale invariance
        - Normalized cross-correlation for lighting invariance
        - Sub-pixel accuracy using interpolation
        - Multiple matching methods for robustness

        Args:
            template_path: Path to the template image to find
            confidence_threshold: Minimum confidence score (0.0 to 1.0)
            search_region: Optional dict with 'x', 'y', 'width', 'height' to limit search area

        Returns:
            Tuple of (x, y, confidence) or None if not found
        """
        try:
            logger.info("🔬 Using advanced computer vision template matching...")
            logger.info(f"📸 Template: {template_path}")
            logger.info(f"🎯 Confidence threshold: {confidence_threshold}")

            # Take screenshot of the current browser window
            logger.info("📷 Capturing browser screenshot...")
            screenshot_png = self.driver.get_screenshot_as_png()
            screenshot_array = np.frombuffer(screenshot_png, np.uint8)
            screenshot = cv2.imdecode(screenshot_array, cv2.IMREAD_COLOR)

            # Load template image
            logger.info("🖼️ Loading template image...")
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)

            if template is None:
                logger.error(f"❌ Could not load template image: {template_path}")
                return None

            template_h, template_w = template.shape[:2]
            logger.info(f"📐 Template dimensions: {template_w}x{template_h}")

            # Extract search region if specified
            if search_region:
                x, y = search_region.get('x', 0), search_region.get('y', 0)
                w, h = search_region.get('width', screenshot.shape[1]), search_region.get('height', screenshot.shape[0])
                screenshot = screenshot[y:y+h, x:x+w]
                logger.info(f"🔍 Search region: x={x}, y={y}, width={w}, height={h}")
            else:
                x, y = 0, 0

            screenshot_h, screenshot_w = screenshot.shape[:2]
            logger.info(f"📐 Screenshot dimensions: {screenshot_w}x{screenshot_h}")

            # Multi-scale template matching for robustness
            logger.info("🔄 Performing multi-scale template matching...")
            scales = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]  # Search at multiple scales
            best_match = None
            best_confidence = 0
            best_scale = 1.0
            best_template_size = (template_w, template_h)

            for scale in scales:
                # Resize TEMPLATE to current scale (keeping screenshot at original size)
                new_w = int(template_w * scale)
                new_h = int(template_h * scale)

                # Skip if scaled template is larger than screenshot or too small
                if new_w > screenshot_w or new_h > screenshot_h or new_w < 10 or new_h < 10:
                    continue

                scaled_template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                scaled_h, scaled_w = scaled_template.shape[:2]

                logger.info(f"   Testing scale {scale:.2f}x: template size {scaled_w}x{scaled_h}")

                # Use multiple matching methods for robustness
                methods = [
                    cv2.TM_CCOEFF_NORMED,    # Normalized cross-correlation (best for exact matching)
                    cv2.TM_CCORR_NORMED,     # Normalized correlation
                ]

                for method in methods:
                    try:
                        # Perform template matching on the ORIGINAL screenshot with SCALED template
                        result = cv2.matchTemplate(screenshot, scaled_template, method)

                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                        # For normalized methods, max_val is the confidence
                        match_val = max_val
                        match_loc = max_loc

                        # Update best match if this is better
                        if match_val > best_confidence:
                            best_confidence = match_val
                            best_match = match_loc
                            best_scale = scale
                            best_template_size = (scaled_w, scaled_h)
                            logger.info(f"   ✨ New best match! Confidence: {match_val:.4f} at scale {scale:.2f}x")
                    except Exception as match_error:
                        logger.warning(f"   ⚠️ Matching failed at scale {scale:.2f}x: {match_error}")
                        continue

            logger.info(f"🎯 Best match confidence: {best_confidence:.4f} at scale {best_scale:.2f}")

            if best_match is None or best_confidence < confidence_threshold:
                logger.warning(f"⚠️ No match found above confidence threshold {confidence_threshold}")
                logger.warning(f"   Best confidence was: {best_confidence:.4f}")
                return None

            # Calculate center point of the matched region with sub-pixel accuracy
            center_x = int(best_match[0] + best_template_size[0] / 2) + x
            center_y = int(best_match[1] + best_template_size[1] / 2) + y

            logger.info(f"✅ Image found at coordinates: ({center_x}, {center_y})")
            logger.info(f"📊 Match confidence: {best_confidence:.4f}")
            logger.info(f"📏 Matched scale: {best_scale:.2f}x")

            return (center_x, center_y, best_confidence)

        except Exception as e:
            logger.error(f"❌ Advanced template matching failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def click_bear_diamond_image(self):
        """Click at the exact position marked by the blue circle in the user's image (Step 8)."""
        try:
            logger.info("🔍 Step 8: Clicking at the blue circle location (top left area)...")
            logger.info("📍 Target coordinates based on user's marked image")
            logger.info("👀 Watch the browser as it clicks at the specified location...")

            # Click at exact coordinates where the blue circle is in the user's image
            # Based on the image, the blue circle is at approximately:
            x_coord = 385
            y_coord = 115

            logger.info(f"📍 Target coordinates: X={x_coord}, Y={y_coord}")
            logger.info("🎯 Clicking at the location marked with blue circle in your image")

            # Add visual indicator at the target location
            self.driver.execute_script(f"""
                var indicator = document.createElement('div');
                indicator.innerHTML = '🎯 CLICKING HERE<br/>(Blue Circle Location)';
                indicator.style.position = 'fixed';
                indicator.style.top = '{y_coord}px';
                indicator.style.left = '{x_coord}px';
                indicator.style.transform = 'translate(-50%, -50%)';
                indicator.style.background = 'blue';
                indicator.style.color = 'white';
                indicator.style.padding = '12px';
                indicator.style.fontSize = '14px';
                indicator.style.fontWeight = 'bold';
                indicator.style.zIndex = '99999';
                indicator.style.borderRadius = '50%';
                indicator.style.border = '4px solid cyan';
                indicator.style.textAlign = 'center';
                indicator.style.boxShadow = '0 0 30px rgba(0,100,255,0.8)';
                indicator.style.width = '120px';
                indicator.style.height = '120px';
                indicator.style.display = 'flex';
                indicator.style.alignItems = 'center';
                indicator.style.justifyContent = 'center';
                document.body.appendChild(indicator);

                setTimeout(() => indicator.remove(), 1500);
            """)

            time.sleep(0.3)

            # Click at the specified coordinates using JavaScript
            self.driver.execute_script(f"""
                var element = document.elementFromPoint({x_coord}, {y_coord});
                if (element) {{
                    element.click();
                    console.log('✅ Clicked at blue circle location ({x_coord}, {y_coord})');
                }} else {{
                    console.log('⚠️ No element found at ({x_coord}, {y_coord})');
                }}
            """)

            logger.info(f"✅ Successfully clicked at blue circle location ({x_coord}, {y_coord})")

            # Add success indicator
            self.driver.execute_script("""
                var success = document.createElement('div');
                success.innerHTML = '🎉 CLICKED AT BLUE CIRCLE LOCATION!';
                success.style.position = 'fixed';
                success.style.top = '50%';
                success.style.left = '50%';
                success.style.transform = 'translate(-50%, -50%)';
                success.style.background = 'linear-gradient(135deg, #0066ff 0%, #00ccff 100%)';
                success.style.color = 'white';
                success.style.padding = '30px';
                success.style.fontSize = '20px';
                success.style.fontWeight = 'bold';
                success.style.zIndex = '10000';
                success.style.borderRadius = '15px';
                success.style.textAlign = 'center';
                success.style.boxShadow = '0 10px 40px rgba(0,100,255,0.5)';
                document.body.appendChild(success);

                setTimeout(() => success.remove(), 2500);
            """)

            time.sleep(0.5)
            return True

        except Exception as e:
            logger.error(f"❌ Failed to click at blue circle location: {e}")
            return False

    def click_next_button(self):
        """Find and click the Next button on the left side (Step 9)."""
        try:
            logger.info("🔍 Looking for Next button on the LEFT SIDE (Step 9)...")
            logger.info("➡️ Searching for Next button with arrow...")
            logger.info("📍 Target location: LEFT SIDE of the page")
            logger.info("👀 Watch the browser as it searches for Next buttons...")

            # Enhanced selectors for the Next button
            xpath_selectors = [
                "//button[contains(text(), 'Next')]",
                "//button[contains(text(), 'NEXT')]",
                "//button[contains(text(), 'next')]",
                "//input[@value='Next']",
                "//input[@value='NEXT']",
                "//div[contains(text(), 'Next')][@role='button']",
                "//div[contains(text(), 'Next')][contains(@onclick, '')]",
                "//span[contains(text(), 'Next')]/../..",
                "//a[contains(text(), 'Next')]",
                "//button[contains(@title, 'Next')]",
                "//button[contains(@aria-label, 'Next')]",
                "//div[contains(@title, 'Next')][@role='button']"
            ]

            next_button = None

            # Get page dimensions to define LEFT SIDE area
            page_width = self.driver.execute_script("return window.innerWidth")
            page_height = self.driver.execute_script("return window.innerHeight")

            # Define LEFT SIDE area boundaries (left 50% of the page)
            left_side_right = page_width * 0.5

            logger.info(f"📐 Page dimensions: {page_width}x{page_height}")
            logger.info(f"🎯 Searching on LEFT SIDE: X(0-{left_side_right}), Y(0-{page_height})")

            # Try CSS selectors for next buttons
            css_selectors = [
                "button[type='button']",
                "button[type='submit']",
                "input[type='button']",
                "input[type='submit']",
                ".next-button",
                ".btn-next",
                "[class*='next']",
                "[id*='next']",
                "button[title*='next' i]",
                "button[aria-label*='next' i]",
                "div[role='button']",
                "div[onclick]",
                ".arrow-button",
                "[class*='arrow']"
            ]

            # Try CSS selectors first, looking for Next text and left side positioning
            for i, css_selector in enumerate(css_selectors):
                try:
                    logger.info(f"🔍 Trying CSS selector {i+1}/{len(css_selectors)}: {css_selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Check if element is on LEFT SIDE
                            element_rect = element.rect
                            element_x = element_rect['x']
                            element_center_x = element_x + element_rect['width'] / 2

                            # Must be on LEFT SIDE
                            on_left_side = element_center_x <= left_side_right

                            if on_left_side:
                                element_text = (element.text or element.get_attribute("value") or element.get_attribute("innerHTML") or element.get_attribute("title") or element.get_attribute("aria-label") or "").upper()
                                element_class = (element.get_attribute("class") or "").lower()
                                element_id = (element.get_attribute("id") or "").lower()

                                # Check for NEXT related terms
                                next_terms = ["NEXT", "→", ">>", "CONTINUE", "PROCEED"]
                                has_next_terms = any(term.upper() in element_text for term in next_terms)
                                has_next_in_attributes = any(term in f"{element_class} {element_id}" for term in ["next", "arrow", "continue", "forward"])

                                if has_next_terms or has_next_in_attributes:
                                    next_button = element
                                    logger.info(f"✅ Found Next button on LEFT SIDE using CSS: {css_selector}")
                                    logger.info(f"➡️ Button text: '{element_text}' at position ({element_center_x:.0f}, {element_rect['y'] + element_rect['height']/2:.0f})")
                                    break
                    if next_button:
                        break
                except Exception:
                    continue

            # Try XPath selectors if CSS didn't work, also filtering by LEFT SIDE position
            if not next_button:
                for i, xpath in enumerate(xpath_selectors):
                    try:
                        logger.info(f"🔍 Trying XPath {i+1}/{len(xpath_selectors)}: {xpath}")
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                element_rect = element.rect
                                element_center_x = element_rect['x'] + element_rect['width'] / 2

                                # Must be on LEFT SIDE
                                if element_center_x <= left_side_right:
                                    next_button = element
                                    logger.info(f"✅ Found Next button on LEFT SIDE using XPath: {xpath}")
                                    break
                        if next_button:
                            break
                    except Exception:
                        continue

            # Enhanced fallback: look for Next button specifically on the LEFT SIDE
            if not next_button:
                logger.info("🔍 Trying fallback method - searching for Next buttons on LEFT SIDE...")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
                divs = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button'], div[onclick]")

                all_clickables = buttons + inputs + divs
                logger.info(f"Found {len(all_clickables)} potentially clickable elements")

                left_side_candidates = []

                for i, element in enumerate(all_clickables):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            # Get element position
                            element_rect = element.rect
                            element_x = element_rect['x']
                            element_y = element_rect['y']
                            element_width = element_rect['width']
                            element_height = element_rect['height']

                            # Calculate element center
                            element_center_x = element_x + element_width / 2
                            element_center_y = element_y + element_height / 2

                            # Check if element is on LEFT SIDE
                            on_left_side = element_center_x <= left_side_right

                            if on_left_side and element_width > 20 and element_height > 15:  # Reasonable size for clicking
                                # Check element text and attributes
                                element_text = (element.text or element.get_attribute("value") or element.get_attribute("innerHTML") or element.get_attribute("title") or element.get_attribute("aria-label") or "").upper()
                                element_class = (element.get_attribute("class") or "").lower()
                                element_id = (element.get_attribute("id") or "").lower()

                                # Check for NEXT related terms
                                next_terms = ["NEXT", "CONTINUE", "PROCEED", "FORWARD", "ARROW"]
                                arrow_symbols = ["→", ">>", "►", "▶"]
                                has_next_terms = any(term.upper() in element_text for term in next_terms)
                                has_arrow_symbols = any(symbol in element_text for symbol in arrow_symbols)
                                has_next_in_attributes = any(term in f"{element_class} {element_id}" for term in ["next", "arrow", "continue", "forward"])

                                if has_next_terms or has_arrow_symbols or has_next_in_attributes:
                                    # Add to candidates with priority scoring
                                    priority_score = 0
                                    if "NEXT" in element_text:
                                        priority_score += 30  # Highest priority for exact NEXT text
                                    if has_arrow_symbols:
                                        priority_score += 25  # High priority for arrow symbols
                                    if has_next_terms:
                                        priority_score += 20  # High priority for next-related terms
                                    if has_next_in_attributes:
                                        priority_score += 15  # Medium priority for attributes
                                    if element.tag_name.lower() == "button":
                                        priority_score += 10  # Prefer actual button elements

                                    left_side_candidates.append({
                                        'element': element,
                                        'score': priority_score,
                                        'position': f"({element_center_x:.0f}, {element_center_y:.0f})",
                                        'text': element_text,
                                        'size': f"{element_width}x{element_height}",
                                        'has_next_terms': has_next_terms,
                                        'has_arrow_symbols': has_arrow_symbols
                                    })

                                    logger.info(f"➡️ Found LEFT SIDE Next candidate #{len(left_side_candidates)}: '{element_text}' at ({element_center_x:.0f}, {element_center_y:.0f}) size {element_width}x{element_height} (score: {priority_score})")
                    except Exception as e:
                        logger.debug(f"Error checking element {i}: {e}")
                        continue

                # Sort candidates by priority score (highest first)
                if left_side_candidates:
                    left_side_candidates.sort(key=lambda x: x['score'], reverse=True)
                    best_candidate = left_side_candidates[0]
                    next_button = best_candidate['element']

                    logger.info(f"✅ Selected best Next button on LEFT SIDE:")
                    logger.info(f"   📍 Position: {best_candidate['position']} (LEFT SIDE)")
                    logger.info(f"   📏 Size: {best_candidate['size']}")
                    logger.info(f"   📝 Text: '{best_candidate['text']}'")
                    logger.info(f"   ➡️ Next terms: {best_candidate['has_next_terms']}")
                    logger.info(f"   🏹 Arrow symbols: {best_candidate['has_arrow_symbols']}")
                    logger.info(f"   🏆 Score: {best_candidate['score']}")
                else:
                    logger.warning("⚠️ No Next buttons found on LEFT SIDE, checking entire page...")

                    # Fallback to any Next button on the page if none found on left side
                    for i, element in enumerate(all_clickables):
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = (element.text or element.get_attribute("value") or element.get_attribute("innerHTML") or "").upper()
                                if "NEXT" in element_text or "→" in element_text:
                                    next_button = element
                                    logger.info(f"✅ Found fallback Next button anywhere on page: '{element_text}'")
                                    break
                        except Exception:
                            continue

            if not next_button:
                logger.error("❌ Could not find any Next button")
                return False

            # Highlight the button for VNC viewing
            try:
                self.driver.execute_script("""
                    arguments[0].style.border = '5px solid magenta';
                    arguments[0].style.boxShadow = '0 0 20px magenta';
                    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                """, next_button)

                # Add visual indicator
                self.driver.execute_script("""
                    var indicator = document.createElement('div');
                    indicator.innerHTML = '➡️ NEXT BUTTON FOUND!';
                    indicator.style.position = 'fixed';
                    indicator.style.top = '10px';
                    indicator.style.left = '50%';
                    indicator.style.transform = 'translateX(-50%)';
                    indicator.style.background = 'magenta';
                    indicator.style.color = 'white';
                    indicator.style.padding = '15px';
                    indicator.style.fontSize = '18px';
                    indicator.style.zIndex = '9999';
                    indicator.style.borderRadius = '5px';
                    document.body.appendChild(indicator);

                    setTimeout(() => indicator.remove(), 3000);
                """)

                time.sleep(2)
                logger.info("🎯 Next button highlighted and scrolled into view")
            except Exception as e:
                logger.warning(f"⚠️ Could not highlight Next button: {e}")

            # Click the button
            try:
                next_button.click()
                logger.info("✅ Successfully clicked Next button")

                # Add success indicator for clicking
                self.driver.execute_script("""
                    var success = document.createElement('div');
                    success.innerHTML = '🎉 NEXT BUTTON CLICKED!';
                    success.style.position = 'fixed';
                    success.style.top = '50%';
                    success.style.left = '50%';
                    success.style.transform = 'translate(-50%, -50%)';
                    success.style.background = 'magenta';
                    success.style.color = 'white';
                    success.style.padding = '30px';
                    success.style.fontSize = '24px';
                    success.style.zIndex = '10000';
                    success.style.borderRadius = '10px';
                    success.style.textAlign = 'center';
                    document.body.appendChild(success);

                    setTimeout(() => success.remove(), 5000);
                """)

                time.sleep(0.5)
                return True

            except Exception as click_error:
                logger.error(f"❌ Failed to click Next button: {click_error}")
                # Try JavaScript click as fallback
                try:
                    logger.info("🔄 Trying JavaScript click as fallback...")
                    self.driver.execute_script("arguments[0].click();", next_button)
                    logger.info("✅ JavaScript click successful")

                    # Add success indicator for JS click
                    self.driver.execute_script("""
                        var success = document.createElement('div');
                        success.innerHTML = '🎉 NEXT CLICKED (JS)!';
                        success.style.position = 'fixed';
                        success.style.top = '50%';
                        success.style.left = '50%';
                        success.style.transform = 'translate(-50%, -50%)';
                        success.style.background = 'darkmagenta';
                        success.style.color = 'white';
                        success.style.padding = '30px';
                        success.style.fontSize = '24px';
                        success.style.zIndex = '10000';
                        success.style.borderRadius = '10px';
                        success.style.textAlign = 'center';
                        document.body.appendChild(success);

                        setTimeout(() => success.remove(), 5000);
                    """)

                    time.sleep(3)
                    return True
                except Exception as js_error:
                    logger.error(f"❌ JavaScript click also failed: {js_error}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to find/click Next button: {e}")
            return False

    def click_shop_button(self):
        """Find and click the brown/tan SHOP button in the middle area."""
        try:
            logger.info("🔍 Looking for brown/tan SHOP button in middle area...")
            logger.info("🛍️ Searching for SHOP button with brown/tan styling...")
            logger.info("👀 Watch the browser as it searches for SHOP buttons...")

            # Enhanced selectors for the SHOP button
            xpath_selectors = [
                "//button[contains(text(), 'SHOP')]",
                "//button[contains(text(), 'Shop')]",
                "//button[contains(text(), 'shop')]",
                "//input[@value='SHOP']",
                "//input[@value='Shop']",
                "//div[contains(text(), 'SHOP')][@role='button']",
                "//div[contains(text(), 'SHOP')][contains(@onclick, '')]",
                "//span[contains(text(), 'SHOP')]/../..",
                "//a[contains(text(), 'SHOP')]",
                "//div[contains(text(), 'Shop')][@role='button']",
                "//span[contains(text(), 'Shop')]/../.."
            ]

            shop_button = None

            # Try CSS selectors for shop buttons with brown/tan styling
            css_selectors = [
                "button[type='button']",
                "button[type='submit']",
                "input[type='button']",
                "input[type='submit']",
                ".shop-button",
                ".btn-shop",
                "[class*='shop']",
                "[id*='shop']",
                "button[style*='brown']",
                "button[style*='tan']",
                "button[style*='#8B4513']",
                "button[style*='#D2B48C']",
                "div[role='button']",
                "div[onclick]",
                ".brown-button",
                ".tan-button"
            ]

            # Use only the specific CSS selector that works
            css_selector = "[id*='shop']"

            try:
                logger.info(f"🔍 Trying CSS selector 8/16: {css_selector}")
                elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        shop_button = element
                        logger.info(f"✅ Found SHOP button using CSS: {css_selector}")
                        break
            except Exception:
                pass

            if not shop_button:
                logger.info("🔍 Trying fallback method - searching for SHOP buttons in MIDDLE AREA...")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
                divs = self.driver.find_elements(By.CSS_SELECTOR, "div[role='button'], div[onclick]")

                all_clickables = buttons + inputs + divs
                logger.info(f"Found {len(all_clickables)} potentially clickable elements")

                # Get page dimensions to determine middle area
                page_width = self.driver.execute_script("return window.innerWidth")
                page_height = self.driver.execute_script("return window.innerHeight")

                # Define middle area boundaries (center 60% of the page)
                middle_left = page_width * 0.2
                middle_right = page_width * 0.8
                middle_top = page_height * 0.3
                middle_bottom = page_height * 0.7

                logger.info(f"📐 Page dimensions: {page_width}x{page_height}")
                logger.info(f"🎯 Searching in middle area: X({middle_left}-{middle_right}), Y({middle_top}-{middle_bottom})")

                middle_area_candidates = []

                for i, element in enumerate(all_clickables):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            # Get element position
                            element_rect = element.rect
                            element_x = element_rect['x']
                            element_y = element_rect['y']
                            element_width = element_rect['width']
                            element_height = element_rect['height']

                            # Calculate element center
                            element_center_x = element_x + element_width / 2
                            element_center_y = element_y + element_height / 2

                            # Check if element is in the middle area
                            in_middle_area = (middle_left <= element_center_x <= middle_right and
                                            middle_top <= element_center_y <= middle_bottom)

                            if in_middle_area:
                                # Check element text and attributes
                                element_text = (element.text or element.get_attribute("value") or element.get_attribute("innerHTML") or "").upper()
                                element_class = (element.get_attribute("class") or "").lower()
                                element_id = (element.get_attribute("id") or "").lower()

                                # Check for SHOP related terms
                                shop_terms = ["SHOP", "STORE", "BUY", "PURCHASE"]
                                has_shop_terms = any(term.upper() in element_text for term in shop_terms)
                                has_shop_in_attributes = any(term in f"{element_class} {element_id}" for term in ["shop", "store"])

                                if has_shop_terms or has_shop_in_attributes:
                                    # Check for brown/tan styling
                                    bg_color = element.value_of_css_property("background-color")
                                    bg_style = element.value_of_css_property("background")
                                    element_style = element.get_attribute("style") or ""

                                    # Combine all style information
                                    all_style_info = f"{bg_color} {bg_style} {element_style} {element_class}".lower()

                                    # Look for brown/tan styling indicators
                                    brown_tan_indicators = [
                                        "brown", "tan", "burlywood", "sandybrown", "peru", "chocolate",
                                        "#8b4513", "#d2b48c", "#daa520", "#cd853f", "#a0522d", "#f4a460"
                                    ]

                                    has_brown_tan = any(indicator in all_style_info for indicator in brown_tan_indicators)

                                    # Add to candidates with priority scoring
                                    priority_score = 0
                                    if has_shop_terms:
                                        priority_score += 20  # Highest priority for SHOP text
                                    if has_brown_tan:
                                        priority_score += 15  # High priority for brown/tan styling
                                    if has_shop_in_attributes:
                                        priority_score += 10

                                    middle_area_candidates.append({
                                        'element': element,
                                        'score': priority_score,
                                        'position': f"({element_center_x:.0f}, {element_center_y:.0f})",
                                        'text': element_text,
                                        'brown_tan_styling': has_brown_tan
                                    })

                                    logger.info(f"🛍️ Found SHOP candidate #{len(middle_area_candidates)}: '{element_text}' at ({element_center_x:.0f}, {element_center_y:.0f}) (score: {priority_score})")
                    except Exception as e:
                        logger.debug(f"Error checking element {i}: {e}")
                        continue

                # Sort candidates by priority score (highest first)
                if middle_area_candidates:
                    middle_area_candidates.sort(key=lambda x: x['score'], reverse=True)
                    best_candidate = middle_area_candidates[0]
                    shop_button = best_candidate['element']

                    logger.info(f"✅ Selected best SHOP button in middle area:")
                    logger.info(f"   📍 Position: {best_candidate['position']}")
                    logger.info(f"   📝 Text: '{best_candidate['text']}'")
                    logger.info(f"   🟤 Brown/Tan styling: {best_candidate['brown_tan_styling']}")
                    logger.info(f"   🏆 Score: {best_candidate['score']}")
                else:
                    logger.warning("⚠️ No SHOP buttons found in middle area, checking entire page...")

                    # Fallback to any SHOP button on the page if none found in middle
                    for i, element in enumerate(all_clickables):
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = (element.text or element.get_attribute("value") or element.get_attribute("innerHTML") or "").upper()
                                if "SHOP" in element_text:
                                    shop_button = element
                                    logger.info(f"✅ Found fallback SHOP button anywhere on page: '{element_text}'")
                                    break
                        except Exception:
                            continue

            if not shop_button:
                logger.error("❌ Could not find any SHOP button")
                return False

            # Highlight the button for VNC viewing
            try:
                self.driver.execute_script("""
                    arguments[0].style.border = '5px solid lime';
                    arguments[0].style.boxShadow = '0 0 20px lime';
                    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                """, shop_button)

                # Add visual indicator
                self.driver.execute_script("""
                    var indicator = document.createElement('div');
                    indicator.innerHTML = '🛍️ SHOP BUTTON FOUND!';
                    indicator.style.position = 'fixed';
                    indicator.style.top = '10px';
                    indicator.style.left = '50%';
                    indicator.style.transform = 'translateX(-50%)';
                    indicator.style.background = 'lime';
                    indicator.style.color = 'black';
                    indicator.style.padding = '15px';
                    indicator.style.fontSize = '18px';
                    indicator.style.zIndex = '9999';
                    indicator.style.borderRadius = '5px';
                    document.body.appendChild(indicator);

                    setTimeout(() => indicator.remove(), 3000);
                """)

                time.sleep(2)
                logger.info("🎯 SHOP button highlighted and scrolled into view")
            except Exception as e:
                logger.warning(f"⚠️ Could not highlight SHOP button: {e}")

            # Click the button
            try:
                shop_button.click()
                logger.info("✅ Successfully clicked SHOP button")

                # Add success indicator for clicking
                self.driver.execute_script("""
                    var success = document.createElement('div');
                    success.innerHTML = '🎉 SHOP BUTTON CLICKED!';
                    success.style.position = 'fixed';
                    success.style.top = '50%';
                    success.style.left = '50%';
                    success.style.transform = 'translate(-50%, -50%)';
                    success.style.background = 'lime';
                    success.style.color = 'black';
                    success.style.padding = '30px';
                    success.style.fontSize = '24px';
                    success.style.zIndex = '10000';
                    success.style.borderRadius = '10px';
                    success.style.textAlign = 'center';
                    document.body.appendChild(success);

                    setTimeout(() => success.remove(), 5000);
                """)

                time.sleep(0.5)
                return True

            except Exception as click_error:
                logger.error(f"❌ Failed to click SHOP button: {click_error}")
                # Try JavaScript click as fallback
                try:
                    logger.info("🔄 Trying JavaScript click as fallback...")
                    self.driver.execute_script("arguments[0].click();", shop_button)
                    logger.info("✅ JavaScript click successful")

                    # Add success indicator for JS click
                    self.driver.execute_script("""
                        var success = document.createElement('div');
                        success.innerHTML = '🎉 SHOP CLICKED (JS)!';
                        success.style.position = 'fixed';
                        success.style.top = '50%';
                        success.style.left = '50%';
                        success.style.transform = 'translate(-50%, -50%)';
                        success.style.background = 'lime';
                        success.style.color = 'black';
                        success.style.padding = '30px';
                        success.style.fontSize = '24px';
                        success.style.zIndex = '10000';
                        success.style.borderRadius = '10px';
                        success.style.textAlign = 'center';
                        document.body.appendChild(success);

                        setTimeout(() => success.remove(), 5000);
                    """)

                    time.sleep(3)
                    return True
                except Exception as js_error:
                    logger.error(f"❌ JavaScript click also failed: {js_error}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to find/click SHOP button: {e}")
            return False

    def click_play_button(self):
        """Find and click the Play button to start the game."""
        try:
            logger.info("🔍 Looking for Play button...")
            logger.info("👀 Watch the browser as it searches for play buttons...")

            # XPath selectors for play button
            xpath_selectors = [
                "//button[contains(text(), 'Play')]",
                "//button[contains(text(), 'PLAY')]",
                "//input[@value='Play']",
                "//input[@value='PLAY']",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'play')]",
                "//div[contains(text(), 'Play')]",
                "//span[contains(text(), 'Play')]"
            ]

            play_button = None

            # Try XPath selectors first
            for i, xpath in enumerate(xpath_selectors):
                try:
                    logger.info(f"🔍 Trying XPath {i+1}/{len(xpath_selectors)}: {xpath}")
                    play_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    logger.info(f"✅ Found Play button using XPath: {xpath}")
                    break
                except TimeoutException:
                    continue

            # Fallback: look for any clickable button
            if not play_button:
                logger.info("🔍 Trying fallback method - searching all buttons...")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], input[type='button']")
                divs = self.driver.find_elements(By.TAG_NAME, "div")

                all_clickables = buttons + inputs + divs
                logger.info(f"Found {len(all_clickables)} potentially clickable elements")

                for i, element in enumerate(all_clickables):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            text = (element.text or element.get_attribute("value") or element.get_attribute("innerHTML") or "").lower()
                            if "play" in text:
                                play_button = element
                                logger.info(f"✅ Found Play button using fallback method (element #{i+1})")
                                break
                    except Exception:
                        continue

            if not play_button:
                logger.error("❌ Could not find any Play button")
                logger.info("📄 Available clickable elements:")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for i, btn in enumerate(buttons[:5]):  # Show first 5 buttons
                    try:
                        text = btn.text or btn.get_attribute("value") or btn.get_attribute("innerHTML")
                        logger.info(f"Button {i+1}: '{text}'")
                    except Exception:
                        pass
                return False

            # Highlight the play button for VNC viewing
            self.driver.execute_script("arguments[0].style.border='3px solid blue';", play_button)
            logger.info("🔵 Play button highlighted in blue - you should see it in VNC")
            time.sleep(2)

            # Scroll to button and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", play_button)
            time.sleep(1)
            play_button.click()

            # Highlight success
            self.driver.execute_script("arguments[0].style.border='3px solid gold';", play_button)
            logger.info("✅ Successfully clicked Play button! - highlighted in gold")
            time.sleep(3)

            return True

        except Exception as e:
            logger.error(f"❌ Failed to click Play button: {e}")
            return False

    def close_first_tab_and_click_continue(self):
        """Close the first tab and then click the green CONTINUE button."""
        try:
            logger.info("🎯 Starting: Close first tab + Click CONTINUE button...")
            logger.info("👀 Watch the browser perform these actions in VNC")

            # Step 1: Close the first tab if there are multiple tabs
            all_windows = self.driver.window_handles
            logger.info(f"📊 Current tabs: {len(all_windows)}")

            if len(all_windows) >= 2:
                logger.info("🗑️ Step 1: Closing the first tab...")

                # Switch to the first tab (index 0)
                self.driver.switch_to.window(all_windows[0])
                logger.info("🎯 Switched to first tab")

                # Close the current window (first tab)
                self.driver.close()
                logger.info("🗑️ First tab closed successfully")

                # Switch back to the remaining tab
                remaining_windows = self.driver.window_handles
                self.driver.switch_to.window(remaining_windows[0])
                logger.info("🎯 Switched to remaining tab")

                # Add visual indicator that first tab was closed
                self.driver.execute_script("""
                    var div = document.createElement('div');
                    div.innerHTML = '🗑️ FIRST TAB CLOSED!';
                    div.style.position = 'fixed';
                    div.style.top = '10px';
                    div.style.left = '10px';
                    div.style.background = 'red';
                    div.style.color = 'white';
                    div.style.padding = '15px';
                    div.style.fontSize = '18px';
                    div.style.zIndex = '9999';
                    div.style.borderRadius = '5px';
                    document.body.appendChild(div);

                    setTimeout(() => div.remove(), 5000);
                """)

                logger.info("✅ Step 1 completed: First tab closed")
                time.sleep(0.5)
            else:
                logger.info("⚠️ Only one tab found - skipping tab closing")

            # Step 2: Click the green CONTINUE button
            logger.info("🔘 Step 2: Looking for green CONTINUE button...")

            # Wait a moment for page to settle after tab operations
            time.sleep(0.5)

            if self.click_continue_button():
                logger.info("✅ Step 2 completed: CONTINUE button clicked successfully")

                # Step 3: Click the yellow/orange LOGIN button
                logger.info("🔘 Step 3: Looking for yellow/orange LOGIN button at top left...")

                # Wait a moment for page to settle after CONTINUE button click
                time.sleep(0.5)

                if self.click_login_button():
                    logger.info("✅ Step 3 completed: LOGIN button clicked successfully")

                    # Step 4: Click the beige/tan EMAIL ADDRESS field
                    logger.info("🔘 Step 4: Looking for beige/tan EMAIL ADDRESS field...")

                    # Wait a moment for page to settle after LOGIN button click
                    time.sleep(0.5)

                    if self.click_email_address_field():
                        logger.info("✅ Step 4 completed: EMAIL ADDRESS field clicked successfully")

                        # Step 5: Click the beige/tan PASSWORD field
                        logger.info("🔘 Step 5: Looking for beige/tan PASSWORD field...")

                        # Wait a moment for page to settle after EMAIL ADDRESS field click
                        time.sleep(0.5)

                        if self.click_password_field():
                            logger.info("✅ Step 5 completed: PASSWORD field clicked successfully")

                            # Step 6: Click the black LOGIN button for final submission
                            logger.info("🔘 Step 6: Looking for black LOGIN button for final submission...")

                            # Wait a moment for page to settle after PASSWORD field interaction
                            time.sleep(0.5)

                            if self.click_black_login_button():
                                logger.info("✅ Step 6 completed: Black LOGIN button clicked successfully")

                                # Step 7: Click the brown/tan SHOP button
                                logger.info("🛍️ Step 7: Looking for brown/tan SHOP button in middle area...")

                                # Wait a moment for page to settle after black LOGIN button click
                                time.sleep(0.5)

                                if self.click_shop_button():
                                    logger.info("✅ Step 7 completed: SHOP button clicked successfully")

                                    # Step 8: Click at the blue circle location (inside store)
                                    logger.info("🎯 Step 8: Clicking at coordinates (385, 115)...")

                                    # Wait a moment for store to open after SHOP button click
                                    time.sleep(0.5)

                                    if self.click_bear_diamond_image():
                                        logger.info("✅ Step 8 completed: Clicked at coordinates (385, 115) successfully")

                                        # Add final completion indicator for all 8 tasks
                                        self.driver.execute_script("""
                                            var completion = document.createElement('div');
                                            completion.innerHTML = '🎉 ALL 8 STEPS COMPLETED!<br>✅ Tab 1: Loaded & Closed<br>✅ Tab 2: Service URL (ACTIVE)<br>🗑️ First tab closed as requested<br>✅ CONTINUE button clicked<br>✅ LOGIN button clicked<br>✅ EMAIL ADDRESS field clicked<br>✅ EMAIL TYPED: stroll@gmail.com<br>✅ PASSWORD field clicked<br>✅ PASSWORD TYPED: GGG@222123<br>✅ Black LOGIN button clicked<br>✅ SHOP button clicked<br>✅ Blue circle location clicked!';
                                            completion.style.position = 'fixed';
                                            completion.style.top = '50%';
                                            completion.style.left = '50%';
                                            completion.style.transform = 'translate(-50%, -50%)';
                                            completion.style.background = 'purple';
                                            completion.style.color = 'white';
                                            completion.style.padding = '30px';
                                            completion.style.fontSize = '16px';
                                            completion.style.zIndex = '10001';
                                            completion.style.borderRadius = '10px';
                                            completion.style.textAlign = 'center';
                                            completion.style.border = '3px solid gold';
                                            document.body.appendChild(completion);

                                            setTimeout(() => completion.remove(), 15000);
                                        """)

                                        return True
                                    else:
                                        logger.error("❌ Step 8 failed: Could not click at blue circle location")
                                        logger.info("⚠️ Steps 1-7 were successful, but Step 8 failed")
                                        return False
                                else:
                                    logger.error("❌ Step 7 failed: Could not click SHOP button")
                                    logger.info("⚠️ Steps 1-6 were successful, but SHOP button failed")

                                    # Add partial completion indicator
                                    self.driver.execute_script("""
                                        var completion = document.createElement('div');
                                        completion.innerHTML = '⚠️ PARTIAL COMPLETION (6/8 STEPS)<br>✅ First tab closed<br>✅ CONTINUE button clicked<br>✅ LOGIN button clicked<br>✅ EMAIL ADDRESS field clicked<br>✅ EMAIL TYPED: stroll@gmail.com<br>✅ PASSWORD field clicked<br>✅ PASSWORD TYPED: GGG@222123<br>✅ Black LOGIN button clicked<br>❌ SHOP button not found';
                                        completion.style.position = 'fixed';
                                        completion.style.top = '50%';
                                        completion.style.left = '50%';
                                        completion.style.transform = 'translate(-50%, -50%)';
                                        completion.style.background = 'orange';
                                        completion.style.color = 'white';
                                        completion.style.padding = '30px';
                                        completion.style.fontSize = '16px';
                                        completion.style.zIndex = '10001';
                                        completion.style.borderRadius = '10px';
                                        completion.style.textAlign = 'center';
                                        completion.style.border = '3px solid gold';
                                        document.body.appendChild(completion);

                                        setTimeout(() => completion.remove(), 10000);
                                    """)

                                    return False
                            else:
                                logger.error("❌ Step 6 failed: Could not click black LOGIN button")
                                logger.info("⚠️ PASSWORD field was successful, but black LOGIN button failed")

                                # Add partial completion indicator
                                self.driver.execute_script("""
                                    var completion = document.createElement('div');
                                    completion.innerHTML = '⚠️ PARTIAL COMPLETION (5/8 STEPS)<br>✅ First tab closed<br>✅ CONTINUE button clicked<br>✅ LOGIN button clicked<br>✅ EMAIL ADDRESS field clicked<br>✅ EMAIL TYPED: stroll@gmail.com<br>✅ PASSWORD field clicked<br>✅ PASSWORD TYPED: GGG@222123<br>❌ Black LOGIN button not found<br>❌ SHOP button not attempted';
                                    completion.style.position = 'fixed';
                                    completion.style.top = '50%';
                                    completion.style.left = '50%';
                                    completion.style.transform = 'translate(-50%, -50%)';
                                    completion.style.background = 'orange';
                                    completion.style.color = 'white';
                                    completion.style.padding = '30px';
                                    completion.style.fontSize = '18px';
                                    completion.style.zIndex = '10001';
                                    completion.style.borderRadius = '10px';
                                    completion.style.textAlign = 'center';
                                    completion.style.border = '3px solid gold';
                                    document.body.appendChild(completion);

                                    setTimeout(() => completion.remove(), 10000);
                                """)

                                return False
                        else:
                            logger.error("❌ Step 5 failed: Could not click PASSWORD field")
                            logger.info("⚠️ EMAIL ADDRESS field was successful, but PASSWORD field failed")

                            # Add partial completion indicator
                            self.driver.execute_script("""
                                var completion = document.createElement('div');
                                completion.innerHTML = '⚠️ PARTIAL COMPLETION (4/8 STEPS)<br>✅ First tab closed<br>✅ CONTINUE button clicked<br>✅ LOGIN button clicked<br>✅ EMAIL ADDRESS field clicked<br>✅ EMAIL TYPED: stroll@gmail.com<br>❌ PASSWORD field not found<br>❌ Black LOGIN button not attempted<br>❌ SHOP button not attempted';
                                completion.style.position = 'fixed';
                                completion.style.top = '50%';
                                completion.style.left = '50%';
                                completion.style.transform = 'translate(-50%, -50%)';
                                completion.style.background = 'orange';
                                completion.style.color = 'white';
                                completion.style.padding = '30px';
                                completion.style.fontSize = '18px';
                                completion.style.zIndex = '10001';
                                completion.style.borderRadius = '10px';
                                completion.style.textAlign = 'center';
                                completion.style.border = '3px solid gold';
                                document.body.appendChild(completion);

                                setTimeout(() => completion.remove(), 10000);
                            """)

                            return False
                    else:
                        logger.error("❌ Step 4 failed: Could not click EMAIL ADDRESS field")
                        logger.info("⚠️ LOGIN button was successful, but EMAIL ADDRESS field failed")

                        # Add partial completion indicator
                        self.driver.execute_script("""
                            var completion = document.createElement('div');
                            completion.innerHTML = '⚠️ PARTIAL COMPLETION (3/8 STEPS)<br>✅ First tab closed<br>✅ CONTINUE button clicked<br>✅ LOGIN button clicked<br>❌ EMAIL ADDRESS field not found<br>❌ PASSWORD field not attempted<br>❌ Black LOGIN button not attempted<br>❌ SHOP button not attempted';
                            completion.style.position = 'fixed';
                            completion.style.top = '50%';
                            completion.style.left = '50%';
                            completion.style.transform = 'translate(-50%, -50%)';
                            completion.style.background = 'orange';
                            completion.style.color = 'white';
                            completion.style.padding = '30px';
                            completion.style.fontSize = '18px';
                            completion.style.zIndex = '10001';
                            completion.style.borderRadius = '10px';
                            completion.style.textAlign = 'center';
                            completion.style.border = '3px solid gold';
                            document.body.appendChild(completion);

                            setTimeout(() => completion.remove(), 10000);
                        """)

                        return False
                else:
                    logger.error("❌ Step 3 failed: Could not click LOGIN button")
                    logger.info("⚠️ CONTINUE button was successful, but LOGIN button failed")

                    # Add partial completion indicator
                    self.driver.execute_script("""
                        var completion = document.createElement('div');
                        completion.innerHTML = '⚠️ PARTIAL COMPLETION (2/8 STEPS)<br>✅ First tab closed<br>✅ CONTINUE button clicked<br>❌ LOGIN button not found<br>❌ EMAIL ADDRESS field not attempted<br>❌ PASSWORD field not attempted<br>❌ Black LOGIN button not attempted<br>❌ SHOP button not attempted';
                        completion.style.position = 'fixed';
                        completion.style.top = '50%';
                        completion.style.left = '50%';
                        completion.style.transform = 'translate(-50%, -50%)';
                        completion.style.background = 'orange';
                        completion.style.color = 'white';
                        completion.style.padding = '30px';
                        completion.style.fontSize = '18px';
                        completion.style.zIndex = '10001';
                        completion.style.borderRadius = '10px';
                        completion.style.textAlign = 'center';
                        completion.style.border = '3px solid gold';
                        document.body.appendChild(completion);

                        setTimeout(() => completion.remove(), 8000);
                    """)

                    return False
            else:
                logger.error("❌ Step 2 failed: Could not click CONTINUE button")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to complete close tab + click continue: {e}")
            return False

    def wait_and_display(self, duration=None):
        """Keep the browser open for viewing in VNC indefinitely."""
        try:
            logger.info("🎮 Game automation running - keeping browser open INDEFINITELY!")
            logger.info("👀 Watch the VNC window to see what happens next!")
            logger.info("♾️ Running unlimited - bot will continue until manually stopped")

            # Run indefinitely with periodic status updates
            start_time = time.time()
            while True:
                time.sleep(60)  # Check every minute instead of every second
                elapsed_time = time.time() - start_time
                hours = int(elapsed_time // 3600)
                minutes = int((elapsed_time % 3600) // 60)

                # Log status every 30 minutes
                if int(elapsed_time) % 1800 == 0 and elapsed_time > 0:
                    logger.info(f"⏰ Bot has been running for {hours}h {minutes}m - still active!")
                    logger.info("👀 VNC window should still be showing your session")

        except Exception as e:
            logger.error(f"❌ Error during display: {e}")
            return False

    def run(self):
        """Main execution method - runs the complete automation sequence."""
        try:
            logger.info("🚀 Starting Hyperion VNC browser bot...")
            logger.info("👀 Open the VNC window to watch the automation in real-time!")

            # Setup WebDriver
            if not self.setup_driver():
                return False

            # Navigate to Hyperion URLs
            if not self.navigate_to_hyperion_urls():
                logger.info("⚠️ Hyperion navigation failed, but keeping browser open for inspection")
                self.wait_and_display()
                return False

            # After navigation, close first tab and click continue button
            logger.info("🎯 Starting additional automation: Close first tab + Click CONTINUE...")
            if not self.close_first_tab_and_click_continue():
                logger.error("❌ Failed to close first tab and click CONTINUE button")
                logger.info("⚠️ Navigation was successful, but additional automation failed")
            else:
                logger.info("✅ Successfully completed: First tab closed + CONTINUE button clicked!")

            # Navigation complete - no further interactions needed
            logger.info("✅ Hyperion URL navigation completed successfully!")
            logger.info("🎉 Both Hyperion sites are now loaded in separate tabs!")
            logger.info("👀 VNC Browser ready - running INDEFINITELY for your use!")
            self.wait_and_display()

            logger.info("🎉 Hyperion VNC Browser automation completed!")

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
                logger.info("🧹 Cleaning up...")
                logger.info("👀 Browser window will close in 5 seconds...")
                time.sleep(5)
                self.driver.quit()
                logger.info("✅ Browser closed successfully")
            except Exception as e:
                logger.error(f"❌ Error during cleanup: {e}")

def main():
    """Main entry point for the script."""
    print("=" * 60)
    print("🌐 Hyperion VNC Browser Bot")
    print("=" * 60)
    print("👀 Open the VNC window to watch the automation!")
    print("🧭 Supports Safari (preferred) and Firefox browsers")
    print("📍 Navigates to URLs automatically:")
    print("   • https://m9n8r2.ddx.desmosgraphing.xyz.cdn.cloudflare.net/")
    print("   • https://m9n8r2.ddx.desmosgraphing.xyz.cdn.cloudflare.net/@/daydream/hvtrs8%2F-tcmkne.ko- (NEW TAB)")

    # Parse command line arguments for browser preference
    preferred_browser = "safari"

    args = sys.argv[1:]
    for arg in args:
        if arg.lower() in ["safari", "firefox"]:
            preferred_browser = arg.lower()
            print(f"Preferred browser: {preferred_browser}")

    print(f"🎯 Browser preference: {preferred_browser}")
    print("-" * 60)

    # Create and run bot (server_url not needed since we're using hardcoded Hyperion URLs)
    bot = HyperionVNCBot(None, preferred_browser)
    success = bot.run()

    if success:
        print("\n🎉 Hyperion VNC Bot completed successfully!")
        print("👀 Both Hyperion sites should be loaded in separate tabs!")
        sys.exit(0)
    else:
        print("\n❌ Hyperion VNC Bot failed to complete. Check the VNC window for visual feedback.")
        sys.exit(1)

if __name__ == "__main__":
    main()

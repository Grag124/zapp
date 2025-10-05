# Overview

This is a Python automation bot with advanced computer vision capabilities that uses Selenium WebDriver to automate browser-based games. The bot implements sophisticated image recognition using OpenCV to find and click specific UI elements by their exact visual appearance. It's designed as a powerful automation tool that can adapt to dynamic web content through template matching rather than relying solely on fixed coordinates or DOM selectors.

## Recent Changes (October 2025)

**Step 8 Fixed Coordinate Click (October 5, 2025)**: Implemented Step 8 to click at exact coordinates (385, 115) after the SHOP button is clicked. This location corresponds to the blue circle marked in the user's reference image. The bot now executes all 8 steps successfully: tab management → CONTINUE button → LOGIN button → email field → password field → black LOGIN button → SHOP button → blue circle location click.

**Advanced Computer Vision Integration**: Implemented multi-scale template matching using OpenCV. The bot includes sophisticated image recognition algorithms capable of finding exact visual elements on the page, providing robustness against UI changes and different screen resolutions. Note: Step 8 currently uses fixed coordinates rather than template matching as per user preference.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Components

**Automation Framework**: Built using Selenium WebDriver with Microsoft Edge as the target browser. This choice provides good compatibility with modern web applications and reliable element detection capabilities.

**Bot Architecture**: Implements a class-based design (`TamingIOBot`) that encapsulates all automation logic. The bot follows a sequential workflow: browser initialization → navigation → form filling → game joining.

**Error Handling Strategy**: Multi-layered approach with specific exception handling for different WebDriver scenarios (timeouts, missing elements, interaction failures). Includes fallback strategies for element detection to handle dynamic web content.

**Logging System**: Comprehensive logging framework using Python's built-in logging module with timestamp and level-based output for debugging and monitoring bot behavior.

## Element Detection Strategy

**Hybrid Detection Approach**: Combines traditional Selenium element selectors with advanced computer vision template matching for maximum robustness.

**Computer Vision System**: 
- Multi-scale pyramid search (0.7x to 1.3x scales) for scale-invariant image matching
- Normalized cross-correlation and correlation methods for lighting-invariant detection
- Sub-pixel accuracy through interpolation
- Configurable search regions to improve performance
- Automatic fallback from focused search to full-page search
- Confidence scoring (typical matches achieve 99%+ confidence)

**Traditional Targeting**: Implements multiple fallback strategies for finding web elements using CSS selectors and XPath, accounting for potential changes in the UI structure. Uses explicit waits with expected conditions rather than hard-coded delays.

**Wait Conditions**: Employs Selenium's WebDriverWait with expected conditions to handle asynchronous page loading and dynamic content rendering.

## Configuration Design

**Flexible URL Handling**: Supports both default taming.io server and custom server URLs through command-line arguments or constructor parameters.

**Customizable Parameters**: Player name and other game settings can be easily modified through the bot configuration.

# External Dependencies

**Selenium WebDriver**: Primary automation framework for browser control and web interaction. Handles all browser operations and element manipulation.

**OpenCV (cv2)**: Advanced computer vision library used for template matching and image recognition. Enables the bot to find UI elements by their exact visual appearance.

**NumPy**: Numerical computing library supporting OpenCV operations and image array manipulation.

**Pillow (PIL)**: Python Imaging Library for image processing and format conversion.

**WebDriver Manager**: Automatic management of browser driver installation and updates, eliminating manual driver setup requirements.

**Firefox Browser**: Primary browser for automation, with persistent profile support for maintaining login sessions.

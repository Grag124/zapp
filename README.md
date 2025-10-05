# Taming.io Auto-Join Bot

A Python Selenium script that automates joining a taming.io game server using Microsoft Edge WebDriver.

## Features

- 🌐 Automatically opens Microsoft Edge browser
- 🎯 Navigates to taming.io server (custom URL supported)
- ✏️ Fills in the name field with '111' (customizable)
- 🎮 Clicks the Play button to start the game
- ⏳ Includes proper wait conditions and error handling
- 🔧 Robust element detection with multiple fallback strategies
- 📝 Detailed logging for debugging

## Prerequisites

### Required Software
1. **Python 3.7+** - [Download Python](https://www.python.org/downloads/)
2. **Microsoft Edge Browser** - Usually pre-installed on Windows
3. **Selenium WebDriver** - Install via pip (see installation section)

### EdgeDriver
Selenium will automatically manage EdgeDriver, but you can also install it manually:
- Download from [Microsoft Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)
- Or use WebDriver Manager (recommended)

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd taming-io-bot

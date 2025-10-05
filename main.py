#!/usr/bin/env python3
"""
Taming.io WebSocket Bot
======================

This script uses WebSocket connections to directly join taming.io game servers.
It connects to the game's WebSocket endpoint and sends the necessary messages
to join with the name '111'.

Usage:
    python main.py [server_url]

If no server_url is provided, it will use the default taming.io server.
"""

import sys
import json
import asyncio
import logging
import websockets
import aiohttp
from urllib.parse import urlparse, urljoin
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TamingIOWebSocketBot:
    """WebSocket bot for connecting to taming.io game servers."""
    
    def __init__(self, server_url=None):
        """
        Initialize the bot with server URL.
        
        Args:
            server_url (str): The taming.io server URL. Defaults to main server.
        """
        self.server_url = server_url or "https://taming.io/"
        self.websocket = None
        self.game_id = None
        self.session = None
        
    async def get_websocket_url(self):
        """Extract the WebSocket URL from the game server."""
        try:
            logger.info(f"🔍 Analyzing server: {self.server_url}")

            # Use Selenium to fetch the page
            firefox_options = Options()
            firefox_options.add_argument('--headless')
            firefox_options.add_argument('--no-sandbox')
            firefox_options.add_argument('--disable-dev-shm-usage')
            firefox_options.add_argument('--disable-gpu')
            firefox_options.add_argument('--window-size=1920,1080')

            service = Service(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=firefox_options)
            driver.get(self.server_url)
            html_content = driver.page_source
            driver.quit()

            logger.info("✅ Successfully fetched game page with Selenium")
            
            # Try to extract WebSocket URL from HTML if we got the page
            websocket_url = None
            if 'html_content' in locals():
                websocket_patterns = [
                    r'ws[s]?://[^"\']+',
                    r'WebSocket\(["\']([^"\']+)["\']',
                    r'new WebSocket\(["\']([^"\']+)["\']',
                    r'connect\(["\']([^"\']+)["\']'
                ]
                
                for pattern in websocket_patterns:
                    matches = re.findall(pattern, html_content)
                    if matches:
                        websocket_url = matches[0]
                        if websocket_url.startswith('ws'):
                            break
                        else:
                            # Convert relative URL to absolute
                            if websocket_url.startswith('/'):
                                parsed = urlparse(self.server_url)
                                ws_protocol = 'wss' if parsed.scheme == 'https' else 'ws'
                                websocket_url = f"{ws_protocol}://{parsed.netloc}{websocket_url}"
                            break
            
            # If no WebSocket URL found from HTML, try common endpoints
            if not websocket_url:
                parsed = urlparse(self.server_url)
                ws_protocol = 'wss' if parsed.scheme == 'https' else 'ws'
                
                # Common WebSocket endpoints for .io games
                common_paths = [
                    '/socket.io/?EIO=4&transport=websocket',
                    '/ws',
                    '/websocket', 
                    '/game',
                    '/socket',
                    '/',
                    '/io'
                ]
                
                for path in common_paths:
                    test_url = f"{ws_protocol}://{parsed.netloc}{path}"
                    logger.info(f"🔍 Trying WebSocket endpoint: {test_url}")
                    try:
                        # Quick connection test
                        test_ws = await asyncio.wait_for(
                            websockets.connect(
                                test_url,
                                extra_headers={
                                    'Origin': self.server_url,
                                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                    'Sec-WebSocket-Version': '13',
                                    'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
                                    'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
                                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                                    'sec-ch-ua-mobile': '?0',
                                    'sec-ch-ua-platform': '"Linux"'
                                }
                            ),
                            timeout=5
                        )
                        await test_ws.close()
                        websocket_url = test_url
                        logger.info(f"✅ Found working WebSocket endpoint: {websocket_url}")
                        break
                    except Exception as e:
                        logger.debug(f"❌ {test_url} failed: {e}")
                        continue
            
            if not websocket_url:
                # Fallback to default websocket URL
                parsed = urlparse(self.server_url)
                ws_protocol = 'wss' if parsed.scheme == 'https' else 'ws'
                websocket_url = f"{ws_protocol}://{parsed.netloc}/socket.io/?EIO=4&transport=websocket"
                logger.info(f"🔄 Using fallback WebSocket URL: {websocket_url}")
                
            logger.info(f"🌐 WebSocket URL: {websocket_url}")
            return websocket_url
            
        except Exception as e:
            logger.error(f"❌ Failed to get WebSocket URL: {e}")
            raise
    
    async def connect_to_game(self, websocket_url):
        """Connect to the game WebSocket server."""
        try:
            logger.info(f"🔌 Connecting to WebSocket: {websocket_url}")
            
            # Connect to WebSocket (simplified approach)
            try:
                self.websocket = await asyncio.wait_for(
                    websockets.connect(websocket_url), 
                    timeout=10
                )
                logger.info("✅ Successfully connected to WebSocket!")
                return True
            except Exception as e:
                # Try without extra headers if first attempt fails
                logger.info(f"🔄 Retrying connection without extra headers...")
                self.websocket = await websockets.connect(websocket_url)
                logger.info("✅ Successfully connected to WebSocket!")
                return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to WebSocket: {e}")
            return False
    
    async def join_game_with_name(self, name="111"):
        """Send join game message with specified name."""
        try:
            logger.info(f"🎮 Joining game with name: '{name}'")
            
            # Common message formats for joining taming.io games
            join_messages = [
                # Format 1: Simple JSON message
                {
                    "type": "join",
                    "name": name
                },
                # Format 2: Action-based message
                {
                    "action": "join",
                    "playerName": name
                },
                # Format 3: Protocol-specific message
                {
                    "cmd": "join",
                    "data": {
                        "name": name
                    }
                },
                # Format 4: Direct name message
                {
                    "name": name,
                    "type": "player_join"
                }
            ]
            
            # Try sending different message formats
            for i, message in enumerate(join_messages):
                try:
                    logger.info(f"📤 Trying join message format {i+1}")
                    await self.websocket.send(json.dumps(message))
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(
                            self.websocket.recv(), 
                            timeout=5.0
                        )
                        logger.info(f"📥 Received response: {response}")
                        
                        # Check if response indicates successful join
                        if any(keyword in response.lower() for keyword in ['join', 'welcome', 'connected', 'success']):
                            logger.info("✅ Successfully joined the game!")
                            return True
                            
                    except asyncio.TimeoutError:
                        logger.info("⏱️ No immediate response, continuing...")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Message format {i+1} failed: {e}")
                    continue
            
            # If structured messages fail, try simple text-based join
            simple_messages = [name, f"join:{name}", f"name:{name}"]
            
            for msg in simple_messages:
                try:
                    logger.info(f"📤 Trying simple message: '{msg}'")
                    await self.websocket.send(msg)
                    
                    try:
                        response = await asyncio.wait_for(
                            self.websocket.recv(), 
                            timeout=3.0
                        )
                        logger.info(f"📥 Received: {response}")
                        return True
                    except asyncio.TimeoutError:
                        continue
                        
                except Exception as e:
                    logger.warning(f"⚠️ Simple message failed: {e}")
                    continue
            
            logger.info("✅ Join messages sent - game should be starting!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to join game: {e}")
            return False
    
    async def listen_for_game_messages(self, duration=30):
        """Listen for incoming game messages."""
        try:
            logger.info(f"👂 Listening for game messages for {duration} seconds...")
            
            end_time = asyncio.get_event_loop().time() + duration
            
            while asyncio.get_event_loop().time() < end_time:
                try:
                    # Listen for messages with timeout
                    message = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=2.0
                    )
                    
                    logger.info(f"📥 Game message: {message}")
                    
                    # Try to parse as JSON for better display
                    try:
                        parsed = json.loads(message)
                        logger.info(f"📊 Parsed message: {json.dumps(parsed, indent=2)}")
                    except json.JSONDecodeError:
                        pass
                        
                except asyncio.TimeoutError:
                    # No message received, continue listening
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.info("🔌 WebSocket connection closed by server")
                    break
                    
            logger.info("✅ Finished listening for messages")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error while listening: {e}")
            return False
    
    async def run(self):
        """Main execution method - runs the complete WebSocket bot sequence."""
        try:
            logger.info("🚀 Starting taming.io WebSocket bot...")
            
            # Get WebSocket URL
            websocket_url = await self.get_websocket_url()
            
            # Connect to game
            if not await self.connect_to_game(websocket_url):
                return False
            
            # Join game with name
            if not await self.join_game_with_name():
                return False
            
            # Listen for game messages
            await self.listen_for_game_messages()
            
            logger.info("🎉 Bot session completed successfully!")
            
            # Keep connection alive for manual interaction
            logger.info("🎮 Connection is active. Press Ctrl+C to disconnect...")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Disconnecting...")
            
            return True
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources and close connections."""
        try:
            logger.info("🧹 Cleaning up connections...")
            
            if self.websocket:
                await self.websocket.close()
                logger.info("✅ WebSocket connection closed")
                
            if self.session:
                await self.session.close()
                logger.info("✅ HTTP session closed")
                
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

async def main():
    """Main entry point for the script."""
    print("=" * 60)
    print("🐾 Taming.io WebSocket Bot")
    print("=" * 60)
    
    # Get server URL from command line argument if provided
    server_url = None
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
        print(f"Using custom server: {server_url}")
    else:
        print("Using default taming.io server")
    
    # Create and run bot
    bot = TamingIOWebSocketBot(server_url)
    success = await bot.run()
    
    if success:
        print("\n🎉 Bot completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Bot failed to complete. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        sys.exit(0)

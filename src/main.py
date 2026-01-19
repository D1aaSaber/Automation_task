import time
import pyautogui
import os
from pathlib import Path
from .vision import VisionCore
from .controller import DesktopBot
from .fetcher import DataProvider
from .utils import setup_logging, release_all_keys, load_config

def main():
    logger = setup_logging()
    config = load_config()
    release_all_keys()
    
    logger.info("Starting Automation...")

    template_path = Path("assets/notepad_icon.png")
    output_dir = Path("output_files")
    output_dir.mkdir(exist_ok=True)

    vision = VisionCore(template_path, config=config.get('vision'))
    bot = DesktopBot(config=config.get('automation'))
    provider = DataProvider()

    posts = provider.fetch_posts(limit=3)
    results_tracker = []

    for post in posts:
        try:
            # Step A: Clear desktop
            bot.prepare_desktop()
            
            # Step B: Ensure mouse is NOT on the icon before searching
            pyautogui.moveTo(100, 100) 
            time.sleep(1) # Wait for tooltips to disappear
            
            result = vision.find_icon()
            
            if result:
                file_path = output_dir.absolute() / f"post_{post['id']}.txt"
                bot.process_task(post, file_path, result.center)
                
                # Step C: Move mouse again immediately after task finishes
                pyautogui.moveTo(100, 100)
                logger.info(f"Post {post['id']} done. Mouse reset.")
            else:
                logger.warning(f"Could not see icon for Post {post['id']}")
                
        except Exception as e:
            logger.error(f"Error: {e}")
            pyautogui.moveTo(100, 100) # Move mouse on error too

    print("\n" + "="*30 + "\nFINAL REPORT\n" + "="*30)
    for res in results_tracker:
        print(f"Post {res['id']}: {'SUCCESS' if res['success'] else 'FAILED'}")
    
    os.startfile(output_dir)

if __name__ == "__main__":
    main()
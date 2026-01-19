import pyautogui
import time
import pygetwindow as gw
import logging
from .utils import release_all_keys

class DesktopBot:
    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        self.cfg = config if config else {}
        pyautogui.FAILSAFE = True
        # Set a default pause between actions for stability
        pyautogui.PAUSE = self.cfg.get('typing_interval', 0.02) 

    def prepare_desktop(self):
        """Clears the screen using Win+D."""
        pyautogui.hotkey('win', 'd')
        time.sleep(1)

    def process_task(self, post_data, file_path, coords):
        """Complete workflow: Open -> Type -> Save -> Close -> Verify."""
        try:
            # 1. OPEN
            x, y = coords
            release_all_keys()
            pyautogui.moveTo(x, y, duration=self.cfg.get('mouse_speed', 0.8))
            pyautogui.doubleClick()
            
            # 2. WAIT FOR FOCUS
            notepad_window = None
            timeout = self.cfg.get('window_timeout', 10)
            start_time = time.time()
            while time.time() - start_time < timeout:
                wins = gw.getWindowsWithTitle('Notepad')
                if wins:
                    notepad_window = wins[0]
                    notepad_window.activate()
                    break
                time.sleep(1)
            
            if not notepad_window:
                raise Exception("Notepad failed to open or focus.")

            # 3. TYPE
            self.logger.info(f"Typing Post {post_data['id']}...")
            content = f"ID: {post_data['id']}\nTITLE: {post_data['title']}\n\n{post_data['body']}"
            pyautogui.write(content, interval=self.cfg.get('typing_interval', 0.02))
            time.sleep(1)

           # 4. SAVE
            self.logger.info("Saving file...")
            pyautogui.hotkey('ctrl', 's')
            time.sleep(self.cfg.get('save_dialog_wait', 2.0))
            
            pyautogui.write(str(file_path))
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1)
            
            # Handle 'Overwrite' popup if file already exists
            pyautogui.press(' ') 
            time.sleep(1)

            # 5. CLOSE TAB
            self.logger.info("Closing Notepad tab (Ctrl+W)...")
            release_all_keys()
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(1)

            # 6. FORCE CLOSE REMAINING WINDOWS
            # We wrap this in a separate loop to ensure the desktop is clean
            for win in gw.getWindowsWithTitle('Notepad'):
                try:
                    win.close()
                    time.sleep(0.5)
                    pyautogui.press('n')
                except:
                    pass

            # --- THE FIX: MOVE MOUSE TO NEUTRAL ZONE ---
            self.logger.info("Moving mouse to neutral zone (100, 100)...")
            pyautogui.moveTo(100, 100, duration=0.2) 
            # -------------------------------------------

        except Exception as e:
            self.logger.error(f"Task failed: {e}")
            raise
        finally:
            # Emergency move in case of error
            pyautogui.moveTo(100, 100)
            release_all_keys()
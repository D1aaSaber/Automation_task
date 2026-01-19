import cv2
import numpy as np
import pytesseract
import pyautogui
from dataclasses import dataclass
from typing import Tuple, List, Optional
import logging

# CONFIGURATION
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

@dataclass
class DetectionResult:
    center: Tuple[int, int]
    confidence: float
    method: str
    box: Tuple[int, int, int, int]

class VisionCore:
    def __init__(self, template_path, config=None):
        self.logger = logging.getLogger(__name__)
        self.cfg = config if config else {}
        
        # CHANGE 1: Lower threshold to 0.60 to handle different wallpapers
        self.threshold = self.cfg.get('confidence', 0.60)
        self.target_text = self.cfg.get('target_text', "Notepad").lower()
        
        self.template = cv2.imread(str(template_path))
        if self.template is None:
            raise FileNotFoundError(f"Template not found at {template_path}")
            
        self.t_h, self.t_w = self.template.shape[:2]

    def capture_screen(self):
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def preprocess_for_ocr(self, img_crop):
        gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(filtered)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def _get_ocr_score(self, image_roi) -> float:
        try:
            processed = self.preprocess_for_ocr(image_roi)
            data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT, config='--psm 11')
            best_score = 0.0
            
            for i, text in enumerate(data['text']):
                text = text.lower().strip()
                if not text: continue
                
                conf = int(data['conf'][i]) / 100.0
                if conf < 0.1: continue

                text_score = 0.0
                if text == self.target_text: text_score = 1.0
                elif text.startswith(self.target_text): text_score = 0.8
                elif self.target_text in text: text_score = 0.6
                
                final_score = (text_score * 0.9) + (conf * 0.1)
                if final_score > best_score: best_score = final_score

            return best_score
        except Exception:
            return 0.0

    def find_icon(self) -> Optional[DetectionResult]:
        screen = self.capture_screen()
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
        
        candidates: List[DetectionResult] = []
        
        # 1. Multi-Scale Template Matching
        scales = np.linspace(0.7, 1.5, 10)
        
        for scale in scales:
            # Resize template (handle size differences)
            resized_template = cv2.resize(template_gray, None, fx=scale, fy=scale)
            if resized_template.shape[0] > screen_gray.shape[0] or resized_template.shape[1] > screen_gray.shape[1]:
                continue
                
            res = cv2.matchTemplate(screen_gray, resized_template, cv2.TM_CCOEFF_NORMED)
            locs = np.where(res >= self.threshold)
            
            w, h = resized_template.shape[::-1]
            for pt in zip(*locs[::-1]):
                center = (pt[0] + w//2, pt[1] + h//2)
                if not any(np.linalg.norm(np.array(c.center) - np.array(center)) < 20 for c in candidates):
                    candidates.append(DetectionResult(center=center, confidence=res[pt[1], pt[0]], method="template", box=(pt[0], pt[1], w, h)))

        # CHANGE 2: Pure Text Fallback (The Wallpaper Fix)
        if not candidates:
            self.logger.info("Template match failed. Scanning for text (Wallpaper Fallback)...")
            
            # Scan the whole screen for the word "Notepad"
            data = pytesseract.image_to_data(screen_gray, output_type=pytesseract.Output.DICT, config='--psm 11')
            
            for i, text in enumerate(data['text']):
                if self.target_text in text.lower():
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    
                    # If we find the text, the icon is usually ~35 pixels ABOVE the text
                    # We aim for that spot blindly
                    icon_center = (x + w//2, y - 35)
                    
                    pyautogui.moveTo(10, 10) # Reset mouse
                    return DetectionResult(
                        center=icon_center, 
                        confidence=1.0, 
                        method="text_only_fallback", 
                        box=(x, y-50, w, h+50)
                    )
            
            return None

        # Sort and Select Best Candidate
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        top_candidate = candidates[0]
        
        # Reset mouse so it doesn't block next scan
        pyautogui.moveTo(10, 10)
        
        # Run OCR Verification if needed (Ambiguity Check)
        run_ocr = False
        if len(candidates) > 1:
            if (candidates[0].confidence - candidates[1].confidence) < 0.1: run_ocr = True
            elif candidates[1].confidence > 0.91: run_ocr = True

        if run_ocr:
            best_ocr_candidate = None
            highest_score = -1
            
            for cand in candidates[:3]:
                x, y, w, h = cand.box
                # Expanded ROI to catch text under the icon
                roi = screen[y+h-5:y+h+60, x-40:x+w+40]
                score = self._get_ocr_score(roi)
                
                if score > highest_score:
                    highest_score = score
                    best_ocr_candidate = cand

            if best_ocr_candidate and highest_score > 0.65:
                best_ocr_candidate.method = "template+ocr"
                return best_ocr_candidate

        return top_candidate
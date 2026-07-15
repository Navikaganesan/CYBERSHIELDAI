import os
import pickle
import time
from dataclasses import dataclass

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


COOKIE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instagram_cookies.pkl")


@dataclass
class InstagramComment:
    username: str
    comment: str
    timestamp: str = ""
    profile_url: str = ""


class InstagramScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None

    def start_browser(self):
        if self.driver:
            return
        chrome_options = Options()
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument("--disable-popup-blocking")
        if self.headless:
            chrome_options.add_argument("--headless=new")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(45)

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def load_instagram_session(self):
        self.start_browser()
        self.safe_get("https://www.instagram.com/")
        time.sleep(3)
        if os.path.exists(COOKIE_PATH):
            with open(COOKIE_PATH, "rb") as cookie_file:
                cookies = pickle.load(cookie_file)
            for cookie in cookies:
                cookie.pop("sameSite", None)
                try:
                    self.driver.add_cookie(cookie)
                except WebDriverException:
                    continue
            self.driver.refresh()
            time.sleep(3)
            cookie_names = {cookie.get("name") for cookie in self.driver.get_cookies()}
            current_url = self.driver.current_url.lower()
            return "sessionid" in cookie_names and "/accounts/login" not in current_url
        return False

    def save_instagram_session(self):
        self.start_browser()
        with open(COOKIE_PATH, "wb") as cookie_file:
            pickle.dump(self.driver.get_cookies(), cookie_file)

    def wait_for_login(self, timeout=180):
        print("Log in to Instagram in the opened browser. The app will continue automatically.")
        end_time = time.time() + timeout
        while time.time() < end_time:
            current_url = self.driver.current_url.lower()
            cookies = {cookie.get("name") for cookie in self.driver.get_cookies()}
            if "sessionid" in cookies and "/accounts/login" not in current_url:
                self.save_instagram_session()
                return True
            time.sleep(2)
        return False

    def open_reel(self, reel_url):
        self.start_browser()
        session_loaded = self.load_instagram_session()
        self.safe_get(reel_url)
        self.wait_for_reel_page()
        if not session_loaded and self.is_login_required():
            if not self.wait_for_login():
                raise TimeoutError("Instagram login was not completed within 3 minutes.")
            self.save_instagram_session()
            self.safe_get(reel_url)
            self.wait_for_reel_page()
        self.expand_reel_comments()

    def safe_get(self, url):
        try:
            self.driver.get(url)
        except TimeoutException:
            self.driver.execute_script("window.stop();")

    def wait_for_reel_page(self, timeout=20):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "main, article, video, div[role='dialog']"))
            )
        except TimeoutException:
            pass
        time.sleep(2)

    def is_login_required(self):
        current_url = self.driver.current_url.lower()
        if "/accounts/login" in current_url:
            return True
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        login_phrases = (
            "log in to instagram",
            "log in to see",
            "sign up to see",
            "sorry, this page isn't available",
        )
        has_reel_content = bool(self.driver.find_elements(By.CSS_SELECTOR, "article, video, a[href*='/p/'], a[href*='/reel/']"))
        return any(phrase in page_text for phrase in login_phrases) and not has_reel_content

    def scroll_comments(self):
        candidates = self.driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'], main")
        target = candidates[0] if candidates else self.driver.find_element(By.TAG_NAME, "body")
        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", target)
        time.sleep(1)

    def expand_reel_comments(self):
        button_labels = (
            "View all comments",
            "View comments",
            "Load more comments",
            "View more comments",
            "more comments",
        )
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main, article, div[role='dialog']")))
        except WebDriverException:
            return

        for _ in range(3):
            clicked = False
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, div[role='button']")
            for button in buttons:
                try:
                    label = button.text.strip()
                    aria = button.get_attribute("aria-label") or ""
                    text = f"{label} {aria}".lower()
                    if any(candidate.lower() in text for candidate in button_labels):
                        self.driver.execute_script("arguments[0].click()", button)
                        time.sleep(2)
                        clicked = True
                        break
                except WebDriverException:
                    continue
            if not clicked:
                break

    def fetch_comments(self):
        if not self.driver:
            return []
        self.expand_reel_comments()
        self.scroll_comments()
        comments = self.fetch_comments_from_dom()
        if comments:
            return self._dedupe(comments)

        # Fallback for older Instagram layouts.
        comments = []
        article_nodes = self.driver.find_elements(By.CSS_SELECTOR, "ul li, article, div[role='dialog'] div")
        for node in article_nodes:
            try:
                links = node.find_elements(By.CSS_SELECTOR, "a[href^='/']")
                spans = [span.text.strip() for span in node.find_elements(By.CSS_SELECTOR, "span")]
                username = links[0].text.strip() if links and links[0].text.strip() else ""
                profile_url = ""
                if links:
                    href = links[0].get_attribute("href") or ""
                    profile_url = href if href.startswith("http") else f"https://www.instagram.com{href}"
                comment_text = self._best_comment_text(spans, username)
                timestamp = ""
                time_nodes = node.find_elements(By.CSS_SELECTOR, "time")
                if time_nodes:
                    timestamp = time_nodes[0].get_attribute("datetime") or time_nodes[0].text
                if username and comment_text:
                    comments.append(
                        InstagramComment(
                            username=username,
                            comment=comment_text,
                            timestamp=timestamp,
                            profile_url=profile_url,
                        )
                    )
            except WebDriverException:
                continue
        return self._dedupe(comments)

    def fetch_comments_from_dom(self):
        rows = self.driver.execute_script(
            """
            const root = [...document.querySelectorAll("div[role='dialog'], main, body")]
                .find((node) => /comments/i.test(node.innerText || "")) || document.body;

            const badUsernames = new Set([
                "explore", "reels", "direct", "accounts", "p", "reel"
            ]);
            const ignoredLines = new Set([
                "Reply", "See translation", "View replies", "View all replies",
                "Hide replies", "Follow", "Following", "Add a comment..."
            ]);

            function clean(value) {
                return String(value || "").replace(/\\s+/g, " ").trim();
            }

            function visibleText(node) {
                const style = window.getComputedStyle(node);
                if (style.display === "none" || style.visibility === "hidden") return "";
                return String(node.innerText || node.textContent || "").trim();
            }

            function usernameFromHref(href) {
                try {
                    const url = new URL(href, window.location.origin);
                    const parts = url.pathname.split("/").filter(Boolean);
                    if (parts.length !== 1) return "";
                    const username = parts[0];
                    if (badUsernames.has(username.toLowerCase())) return "";
                    return username;
                } catch {
                    return "";
                }
            }

            function nearestCommentBlock(anchor) {
                let node = anchor;
                for (let i = 0; i < 8 && node; i += 1) {
                    const text = visibleText(node);
                    if (
                        text.includes(anchor.textContent.trim()) &&
                        /\\b(reply|like|see translation|view replies|\\d+[smhdw])\\b/i.test(text)
                    ) {
                        return node;
                    }
                    node = node.parentElement;
                }
                return anchor.parentElement;
            }

            const results = [];
            const seen = new Set();
            const anchors = [...root.querySelectorAll("a[href^='/'], a[href*='instagram.com/']")];
            for (const anchor of anchors) {
                const href = anchor.getAttribute("href") || "";
                const username = clean(anchor.textContent) || usernameFromHref(href);
                const profileUsername = usernameFromHref(href);
                const finalUsername = username || profileUsername;
                if (!finalUsername || badUsernames.has(finalUsername.toLowerCase())) continue;

                const block = nearestCommentBlock(anchor);
                if (!block) continue;

                const lines = visibleText(block)
                    .split(/\\n+/)
                    .map(clean)
                    .filter(Boolean);

                const filtered = lines.filter((line) => {
                    const lower = line.toLowerCase();
                    if (line === finalUsername) return false;
                    if (ignoredLines.has(line)) return false;
                    if (/^\\d+\\s*(like|likes)$/i.test(line)) return false;
                    if (/^\\d+[smhdw]$/i.test(line)) return false;
                    if (/^view all \\d+ repl/i.test(lower)) return false;
                    if (lower === "comments") return false;
                    return true;
                });

                let comment = "";
                const usernameLine = lines.find((line) => line.startsWith(finalUsername));
                if (usernameLine && usernameLine.length > finalUsername.length) {
                    comment = usernameLine
                        .replace(finalUsername, "")
                        .replace(/^\\s*\\d+[smhdw]\\s*/i, "")
                        .trim();
                }
                if (!comment) {
                    comment = filtered.find((line) => line !== finalUsername && line.length > 1) || "";
                }
                if (!comment) continue;

                const key = `${finalUsername.toLowerCase()}|${comment.toLowerCase()}`;
                if (seen.has(key)) continue;
                seen.add(key);
                results.push({
                    username: finalUsername,
                    comment,
                    profile_url: new URL(href, window.location.origin).href,
                    timestamp: ""
                });
            }
            return results;
            """
        )
        return [
            InstagramComment(
                username=row.get("username", ""),
                comment=row.get("comment", ""),
                timestamp=row.get("timestamp", ""),
                profile_url=row.get("profile_url", ""),
            )
            for row in rows
            if row.get("username") and row.get("comment")
        ]

    @staticmethod
    def _best_comment_text(spans, username):
        ignored = {username, "Reply", "See translation", "View replies"}
        text_spans = [text for text in spans if text and text not in ignored and "likes" not in text.lower()]
        return max(text_spans, key=len) if text_spans else ""

    @staticmethod
    def _dedupe(comments):
        seen = set()
        unique = []
        for item in comments:
            key = (item.username.lower(), item.comment.strip().lower())
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

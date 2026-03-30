"""
CDP Raw Fallback — For pages too heavy for dev-browser (Facebook, Meta Business Suite)
Uses direct Chrome DevTools Protocol via websocket.
"""
import json
import base64
import time
from urllib.request import urlopen
import websocket


class CDPBrowser:
    """Direct CDP connection to Chrome with remote debugging."""

    def __init__(self, port=9222, screenshot_dir=".", timeout=30):
        self.port = port
        self.screenshot_dir = screenshot_dir
        self.timeout = timeout
        self.ws = None
        self.counter = 0

    def connect(self, url_filter=None):
        """Connect to a Chrome tab matching the URL filter."""
        tabs = json.loads(
            urlopen(f"http://localhost:{self.port}/json/list").read()
        )
        skip = ("fbsbx", "sw?", "static_resources", "about:blank")

        if url_filter:
            tab = next(
                (
                    t
                    for t in tabs
                    if url_filter in t.get("url", "")
                    and not any(s in t.get("url", "") for s in skip)
                ),
                tabs[0],
            )
        else:
            tab = next(
                (t for t in tabs if not any(s in t.get("url", "") for s in skip)),
                tabs[0],
            )

        self.ws = websocket.create_connection(
            tab["webSocketDebuggerUrl"], timeout=self.timeout
        )
        self._cmd("DOM.enable")
        return self

    def _cmd(self, method, params=None):
        self.counter += 1
        msg = {"id": self.counter, "method": method}
        if params:
            msg["params"] = params
        self.ws.send(json.dumps(msg))
        for _ in range(300):
            r = json.loads(self.ws.recv())
            if r.get("id") == self.counter:
                return r
        return {}

    def navigate(self, url, wait=3):
        self._cmd("Page.navigate", {"url": url})
        time.sleep(wait)
        return self

    def url(self):
        r = self._cmd(
            "Runtime.evaluate",
            {"expression": "window.location.href", "returnByValue": True},
        )
        return r.get("result", {}).get("result", {}).get("value", "")

    def screenshot(self, name="screenshot"):
        r = self._cmd(
            "Page.captureScreenshot", {"format": "png", "quality": 85}
        )
        if "result" in r:
            path = f"{self.screenshot_dir}/{name}.png"
            with open(path, "wb") as f:
                f.write(base64.b64decode(r["result"]["data"]))
            return path
        return None

    def click(self, x, y):
        self._cmd(
            "Input.dispatchMouseEvent",
            {"type": "mouseMoved", "x": x, "y": y},
        )
        self._cmd(
            "Input.dispatchMouseEvent",
            {
                "type": "mousePressed",
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1,
            },
        )
        time.sleep(0.05)
        self._cmd(
            "Input.dispatchMouseEvent",
            {
                "type": "mouseReleased",
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1,
            },
        )
        return self

    def type_fast(self, text):
        self._cmd("Input.insertText", {"text": text})
        return self

    def find_and_click(self, search_text, x_max=None):
        """Find DOM element by text and click its center."""
        self._cmd("DOM.getDocument", {"depth": -1})
        search = self._cmd("DOM.performSearch", {"query": search_text})
        count = search.get("result", {}).get("resultCount", 0)
        if count == 0:
            return False

        results = self._cmd(
            "DOM.getSearchResults",
            {
                "searchId": search["result"]["searchId"],
                "fromIndex": 0,
                "toIndex": min(count, 10),
            },
        )

        for nid in results["result"]["nodeIds"]:
            try:
                self._cmd("DOM.scrollIntoViewIfNeeded", {"nodeId": nid})
                time.sleep(0.2)
                box = self._cmd("DOM.getBoxModel", {"nodeId": nid})
                if "result" not in box:
                    continue
                co = box["result"]["model"]["content"]
                w = co[2] - co[0]
                x = co[0]
                if w > 10 and (x_max is None or x < x_max):
                    cx = int((co[0] + co[2]) / 2)
                    cy = int((co[1] + co[5]) / 2)
                    self.click(cx, cy)
                    return True
            except Exception:
                continue
        return False

    def js(self, expression):
        r = self._cmd(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        return r.get("result", {}).get("result", {}).get("value")

    def close(self):
        if self.ws:
            self.ws.close()


if __name__ == "__main__":
    cdp = CDPBrowser(screenshot_dir="C:/Users/Administrator/browser-agent-test")
    cdp.connect("facebook.com")
    print(f"Connected to: {cdp.url()}")
    cdp.screenshot("cdp_test")
    cdp.close()
    print("CDPBrowser working!")

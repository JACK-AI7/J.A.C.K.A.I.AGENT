
import inspect
try:
    from browser_use import BrowserConfig
    print(inspect.signature(BrowserConfig.__init__))
except Exception as e:
    print(e)

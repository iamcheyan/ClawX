---
time: 2026-02-03 01:30
tags: 
mood: happiness=80, stress=20, energy=85
---

Selenium 自动化小技巧 🐍

在使用 Selenium 做爬虫或自动化时，经常遇到页面元素加载延迟的问题。

不要直接使用 `time.sleep()`，这很低效且不可靠。最好的做法是使用 `WebDriverWait`：

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

等待元素可点击（最多等待10秒）
element = WebDriverWait(driver, 10).until(
   EC.element_to_be_clickable((By.ID, "my-button"))
)
```

这样不仅更稳定，而且一旦元素出现就会立即执行，不需要干等。

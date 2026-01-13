class ScreenshotManager {
  constructor() {
    this.screenshotCount = 0;
    this.sessionId = Date.now();
  }

  async captureWithHighlight(element, stepId) {
    try {
      const originalOutline = element.style.outline;
      const originalBoxShadow = element.style.boxShadow;

      element.style.outline = '3px solid #FF6B6B';
      element.style.boxShadow = '0 0 10px rgba(255, 107, 107, 0.5)';

      element.scrollIntoView({
        behavior: 'instant',
        block: 'center',
        inline: 'center'
      });

      await this.sleep(400);

      const screenshot = await this.captureScreenshot();

      element.style.outline = originalOutline;
      element.style.boxShadow = originalBoxShadow;

      if (screenshot) {
        await this.saveScreenshot(screenshot, stepId, element);
        return screenshot;
      }

      return null;
    } catch (err) {
      console.error('captureWithHighlight error:', err);
      return null;
    }
  }

  async captureSimple(stepId) {
    try {
      await this.sleep(400);
      const screenshot = await this.captureScreenshot();

      if (screenshot) {
        await this.saveScreenshot(screenshot, stepId, null);
        return screenshot;
      }
      return null;
    } catch (err) {
      console.error('captureSimple error:', err);
      return null;
    }
  }

  async captureScreenshot() {
    return new Promise(resolve => {
      chrome.runtime.sendMessage(
        { action: 'captureScreenshot' },
        response => {
          if (!response || !response.success) {
            console.warn('Screenshot skipped:', response?.error);
            resolve(null);
          } else {
            resolve(response.dataUrl);
          }
        }
      );
    });
  }

  async saveScreenshot(dataUrl, stepId, element) {
    this.screenshotCount++;

    const screenshot = {
      id: stepId,
      screenshotNumber: this.screenshotCount,
      timestamp: Date.now(),
      dataUrl,
      filename: `screenshot_${this.sessionId}_${String(this.screenshotCount).padStart(3, '0')}.png`,
      metadata: {
        url: location.href,
        title: document.title,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        }
      }
    };

    if (element) {
      const rect = element.getBoundingClientRect();
      screenshot.element = {
        tagName: element.tagName,
        text: element.innerText?.slice(0, 100) || '',
        position: rect.toJSON()
      };
    }

    const { screenshots = [] } = await chrome.storage.local.get('screenshots');
    screenshots.push(screenshot);
    await chrome.storage.local.set({ screenshots });

    console.log(`📸 Screenshot saved (${this.screenshotCount})`);
    return screenshot;
  }

  sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  static async clearScreenshots() {
    await chrome.storage.local.set({ screenshots: [] });
  }
}

window.ScreenshotManager = ScreenshotManager;

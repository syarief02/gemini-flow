import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_suno():
    p = await async_playwright().start()
    b = await p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    ctx = b.contexts[0]
    suno_tab = None
    for page in ctx.pages:
        if 'suno.com' in page.url or 'suno.ai' in page.url:
            suno_tab = page
            break
    if suno_tab:
        await suno_tab.set_viewport_size({"width": 1400, "height": 900})
        await suno_tab.bring_to_front()
        await suno_tab.wait_for_timeout(2000)
        links = await suno_tab.evaluate('''() => {
            const anchors = Array.from(document.querySelectorAll('a[href*="/song/"]'));
            return anchors.map(a => ({ href: a.href, text: a.innerText.trim() }));
        }''')
        print("Suno song links:", json.dumps(links[:8], indent=2))
        await suno_tab.screenshot(path='suno_latest_status.png')
    else:
        print("No Suno tab open")
    await p.stop()

if __name__ == "__main__":
    asyncio.run(inspect_suno())

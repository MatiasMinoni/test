import puppeteer from "puppeteer-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";
import { executablePath } from "puppeteer";

puppeteer.use(StealthPlugin());


(async () => {
    const browser = await puppeteer.launch({
        executablePath: executablePath(),
        headless: true,
        args: [
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-site-isolation-trials",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        ],
    });
    const page = await browser.newPage();
    await page.goto("https://www.chollometro.com/visit/homenew/980470");
    // await page.screenshot({ path: "example.png" });
    console.log(page.url());
    await browser.close();
    })();


const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// Synthetic data only: render the real dashboard components without a database.
const reportRow = {
  BranchID: 'All', Date: '', 'Start-Date': '2026-07-22', 'End-Date': '2026-10-20',
  'Total-Started': '9,882', 'Total-Submitted': '9,334',
  'Total-Opened/Approved': '5,750', 'Grand-Total': '9,882',
};
for (const key of ['Total-Started', 'Total-Submitted', 'Total-Opened/Approved']) {
  for (const type of ['Lending', 'Deposit', 'Mixed', 'Multi', 'Single']) {
    reportRow[`${key}-[${type}]`] = '306';
  }
}
const insights = {
  Started: { Total: '9,882', Online: '6,000', 'Banker Assisted': '3,882' },
  Submitted: '9,334', 'Opened/Approved': '5,750', 'Grand Total': '9,882',
};
for (const key of Object.keys(insights)) insights['_report_' + key] = [{ Status: key, Count: 10 }];
for (const key of ['Total-Started', 'Total-Submitted', 'Total-Opened/Approved', 'Grand-Total']) {
  reportRow['_report_' + key] = [{ Status: key, Count: 10 }];
}

async function mockBackend(page) {
  await page.route('**/api/**', route => {
    const pathname = decodeURIComponent(new URL(route.request().url()).pathname);
    let payload = [];
    if (pathname.endsWith('/query')) {
      return route.fulfill({ contentType: 'text/plain', body: String(route.request().postDataJSON().query) });
    }
    if (pathname.includes('/charts/')) {
      const name = pathname.split('/charts/')[1];
      if (name === 'All Branch Ids') payload = { rows: ['All'] };
      else if (name === 'Current Total DDS Amount and Switches Insights') {
        payload = { 'Current Total DDS Amount': '10,000', 'Total Number of Successful Switches': '100' };
      } else if (name.endsWith('Insights')) payload = insights;
      else if (['Branch Originated Reports', 'Business Deposit Reports', 'Abandonment Report'].includes(name)) {
        payload = { headers: Object.keys(reportRow), rows: [reportRow] };
      } else payload = { headers: ['Month', 'Total'], rows: [], labels: [], list: [], datasetMap: {} };
    } else if (pathname.includes('metrics')) payload = {};
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });
  });
}

const reports = [
  'In_Branch Originated Report', 'Business Deposits and Loans Report', 'Abandonment Report',
  'E-Delivery Report', 'Payment Switch Reports', 'Direct Deposit Switch',
  'PennState University Banking Reports',
];
for (const width of [375, 768, 1440]) {
  for (const name of reports) {
    test(`${name}: card layout at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 1000 });
      await mockBackend(page);
      await page.goto('/');
      await page.waitForTimeout(1300);
      if (width < 800) await page.getByRole('button', { name: 'Expand navigation' }).click();
      await page.getByRole('button', { name, exact: true }).click();
      const grid = page.locator('.report-cards').first();
      await expect(grid).toBeVisible();
      await expect(grid.locator(':scope > .report-card').first()).toBeVisible();
      // Allow the mobile navigation's existing margin transition to finish.
      await page.waitForTimeout(400);
      for (const container of await page.locator('.report-cards').all()) {
        const geometry = await container.evaluate(element => {
          const box = element.getBoundingClientRect();
          return {
            display: getComputedStyle(element).display,
            wrap: getComputedStyle(element).flexWrap,
            left: box.left, right: box.right,
            cards: [...element.children].map(card => {
              const r = card.getBoundingClientRect();
              return { left: r.left, right: r.right, top: r.top, bottom: r.bottom };
            }),
          };
        });
        expect(geometry.display).toBe('flex');
        expect(geometry.wrap).toBe('wrap');
        expect(geometry.cards.length).toBeGreaterThanOrEqual(3);
        for (const card of geometry.cards) {
          expect(card.left).toBeGreaterThanOrEqual(geometry.left - 1);
          expect(card.right).toBeLessThanOrEqual(geometry.right + 1);
          expect(card.right).toBeLessThanOrEqual(width + 1);
        }
        for (let i = 0; i < geometry.cards.length; i++) {
          for (const b of geometry.cards.slice(i + 1)) {
            const a = geometry.cards[i];
            expect(a.right <= b.left + 1 || b.right <= a.left + 1 ||
              a.bottom <= b.top + 1 || b.bottom <= a.top + 1).toBe(true);
          }
        }
        if (width === 1440) expect(geometry.cards[1].top).toBe(geometry.cards[0].top);
        if (width === 375) expect(geometry.cards[1].top).toBeGreaterThan(geometry.cards[0].top);
      }
      const filename = name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
      const destination = path.join(__dirname, 'screenshots', `report-${filename}-${width}.png`);
      fs.mkdirSync(path.dirname(destination), { recursive: true });
      await grid.screenshot({ path: destination });
    });
  }
}

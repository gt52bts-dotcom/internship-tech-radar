import { synthetics } from '@aws/synthetics-playwright';

const BASE_URL = process.env.BASE_URL;

function requireBaseUrl() {
  if (!BASE_URL || !BASE_URL.startsWith('https://')) {
    throw new Error('BASE_URL must be an HTTPS sandbox or test endpoint.');
  }
  return BASE_URL.replace(/\/$/, '');
}

export async function handler(event, context) {
  const baseUrl = requireBaseUrl();
  const browser = await synthetics.launch();
  const browserContext = await browser.newContext();
  const page = await synthetics.getPage(browserContext);

  try {
    await synthetics.executeStep('homepage_load', async () => {
      await page.goto(baseUrl, { waitUntil: 'load', timeout: 15000 });
      await page.waitForLoadState('networkidle', { timeout: 10000 });
    });

    await synthetics.executeStep('quote_api', async () => {
      const result = await page.evaluate(async () => {
        const response = await fetch('/api/quote', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            product: 'travel',
            coverage: 1000000,
            mode: 'synthetics_preview_only'
          })
        });
        return {
          ok: response.ok,
          status: response.status,
          body: await response.text()
        };
      });

      if (!result.ok) {
        throw new Error(`quote_api failed with HTTP ${result.status}: ${result.body.slice(0, 300)}`);
      }
    });

    await synthetics.executeStep('application_preview', async () => {
      const result = await page.evaluate(async () => {
        const response = await fetch('/api/application/preview', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            quote_id: 'QT-SYNTHETICS-PREVIEW',
            mode: 'preview_only'
          })
        });
        const body = await response.text();
        return {
          ok: response.ok,
          status: response.status,
          body
        };
      });

      if (!result.ok) {
        throw new Error(`application_preview failed with HTTP ${result.status}: ${result.body.slice(0, 300)}`);
      }
    });

    await synthetics.executeStep('frontend_error_check', async () => {
      const result = await page.evaluate(async () => {
        const response = await fetch('/api/client-errors');
        const payload = await response.json();
        return {
          ok: response.ok,
          status: response.status,
          errors: payload.errors || []
        };
      });

      if (!result.ok) {
        throw new Error(`frontend_error_check failed with HTTP ${result.status}`);
      }
      if (result.errors.length > 0) {
        throw new Error(`frontend runtime errors detected: ${JSON.stringify(result.errors).slice(0, 500)}`);
      }
    });
  } finally {
    await synthetics.close();
  }
}

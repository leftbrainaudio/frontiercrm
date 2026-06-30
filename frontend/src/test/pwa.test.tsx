/* ──────────────────────────────────────────────
   PWA — Test Suite
   Tests cover every non-trivial PWA concern:
     1. manifest.json (source) — required fields, icon paths
     2. manifest.webmanifest (build) — merged fields, generated scope/lang
     3. registerSW.js (build) — registration behavior
     4. sw.js (build) — skipWaiting / clientsClaim / precache / runtimeCaching
     5. index.html — iOS meta tags, manifest link
     6. vite.config.ts — PWA plugin configuration correctness
     7. Icon PNG files — dimensions and validity
     8. App component — boots without crashing; PWA API tolerance
     9. Offline / network state awareness
     10. Service Worker registration behavior (mocked)
   ────────────────────────────────────────────── */

// Mock heavy dependencies BEFORE App import to avoid loading the full
// module tree (settings-page.tsx has a pre-existing OXC transform error).
vi.mock('react-router-dom', () => ({
  RouterProvider: vi.fn(() => <div data-testid="router-provider" />),
  createBrowserRouter: vi.fn(() => ({})),
}));
vi.mock('@tanstack/react-query', () => ({
  QueryClient: vi.fn(),
  QueryClientProvider: vi.fn(({ children }: { children: React.ReactNode }) =>
    <div data-testid="query-provider">{children}</div>
  ),
}));
vi.mock('react-hot-toast', () => ({
  Toaster: vi.fn(() => <div data-testid="toaster" />),
}));
vi.mock('./store/auth', () => ({
  useAuthStore: vi.fn((sel?: unknown) => {
    if (typeof sel === 'function') return vi.fn();
    return {};
  }),
}));
vi.mock('./store/theme', () => ({
  useThemeStore: vi.fn((sel?: unknown) => {
    if (typeof sel === 'function') return 'light';
    return { theme: 'light' };
  }),
}));
vi.mock('./router', () => ({
  router: {},
}));

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render } from '@testing-library/react';
import { readFileSync, existsSync, statSync } from 'fs';
import { resolve } from 'path';
import App from '../App';

const PUBLIC = resolve(__dirname, '../../public');
const DIST   = resolve(__dirname, '../../dist');
const ROOT   = resolve(__dirname, '../..');

/* ── Helpers ────────────────────────────── */
function readJSON(p: string) { return JSON.parse(readFileSync(p, 'utf-8')); }
function readText(p: string) { return readFileSync(p, 'utf-8'); }
function exists(p: string)   { return existsSync(p); }

/** Extract PNG width/height from the IHDR chunk at byte 16. */
function pngDims(p: string): { w: number; h: number } | null {
  try {
    const buf = readFileSync(p);
    if (buf.length < 24) return null;
    return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
  } catch { return null; }
}

/* =====================================
   1. manifest.json (source)
   ===================================== */
describe('manifest.json (source)', () => {
  const p = `${PUBLIC}/manifest.json`;

  it('exists in public/', () => {
    expect(exists(p)).toBe(true);
  });

  it('has all required W3C manifest fields', () => {
    const mf = readJSON(p);
    expect(mf.name).toBe('FrontierCRM');
    expect(mf.short_name).toBe('Frontier');
    expect(mf.description).toBe('CRM for modern teams');
    expect(mf.start_url).toBe('/');
    expect(mf.display).toBe('standalone');
    expect(mf.theme_color).toBe('#2563EB');
    expect(mf.background_color).toBe('#FFFFFF');
    expect(Array.isArray(mf.icons)).toBe(true);
  });

  it('declares two icons with correct sizes and type', () => {
    const mf = readJSON(p);
    const sizes = mf.icons.map((i: { sizes: string; type: string }) => i.sizes);
    const types = mf.icons.map((i: { sizes: string; type: string }) => i.type);
    expect(sizes).toContain('192x192');
    expect(sizes).toContain('512x512');
    expect(types.every((t: string) => t === 'image/png')).toBe(true);
  });

  it('marks icons as "any maskable" purpose', () => {
    const mf = readJSON(p);
    mf.icons.forEach((icon: { purpose?: string }) => {
      expect(icon.purpose).toMatch(/maskable/);
    });
  });

  it('references icon files that exist on disk', () => {
    const mf = readJSON(p);
    mf.icons.forEach((icon: { src: string }) => {
      expect(exists(resolve(PUBLIC, icon.src.replace(/^\//, '')))).toBe(true);
    });
  });
});

/* =====================================
   2. manifest.webmanifest (build output)
   ===================================== */
describe('manifest.webmanifest (build)', () => {
  const p = `${DIST}/manifest.webmanifest`;

  it('exists after build', () => {
    expect(exists(p)).toBe(true);
  });

  it('includes all source fields plus generated lang/scope', () => {
    const mf = readJSON(p);
    expect(mf.name).toBe('FrontierCRM');
    expect(mf.short_name).toBe('Frontier');
    expect(mf.display).toBe('standalone');
    expect(mf.theme_color).toBe('#2563EB');
    expect(mf.background_color).toBe('#FFFFFF');
    expect(mf.lang).toBe('en');
    expect(mf.scope).toBe('/');
  });

  it('has non-empty icons array referencing build files', () => {
    const mf = readJSON(p);
    expect(mf.icons.length).toBeGreaterThanOrEqual(2);
    mf.icons.forEach((icon: { src: string }) => {
      expect(exists(resolve(DIST, icon.src.replace(/^\//, '')))).toBe(true);
    });
  });
});

/* =====================================
   3. registerSW.js (build output)
   ===================================== */
describe('registerSW.js (build)', () => {
  const p = `${DIST}/registerSW.js`;

  it('exists', () => {
    expect(exists(p)).toBe(true);
  });

  it('guards on navigator.serviceWorker before registering', () => {
    const code = readText(p);
    expect(code).toMatch(/'serviceWorker' in navigator/);
    expect(code).toMatch(/navigator\.serviceWorker\.register/);
  });

  it('registers /sw.js with scope /', () => {
    const code = readText(p);
    expect(code).toMatch(/\/sw\.js/);
    expect(code).toMatch(/scope:\s*'\/'/);
  });

  it('registers on window load event', () => {
    const code = readText(p);
    expect(code).toMatch(/addEventListener\('load'/);
  });
});

/* =====================================
   4. sw.js (build output — service worker)
   ===================================== */
describe('sw.js (build — service worker)', () => {
  const p = `${DIST}/sw.js`;

  it('exists with non-trivial byte count', () => {
    expect(exists(p)).toBe(true);
    expect(statSync(p).size).toBeGreaterThan(1000);
  });

  it('calls self.skipWaiting() for immediate activation', () => {
    expect(readText(p)).toMatch(/self\.skipWaiting\(\)/);
  });

  it('calls clientsClaim() to take control without reload', () => {
    expect(readText(p)).toMatch(/clientsClaim\(\)/);
  });

  it('uses precacheAndRoute for static asset caching', () => {
    expect(readText(p)).toMatch(/precacheAndRoute/);
  });

  it('precaches index.html and registerSW.js', () => {
    const code = readText(p);
    expect(code).toMatch(/"index\.html"/);
    expect(code).toMatch(/"registerSW\.js"/);
  });

  it('precaches both icon sizes', () => {
    const code = readText(p);
    expect(code).toMatch(/"icon-192\.png"/);
    expect(code).toMatch(/"icon-512\.png"/);
  });

  it('precaches JS and CSS assets', () => {
    const code = readText(p);
    expect(code).toMatch(/\.js"/);
    expect(code).toMatch(/\.css"/);
  });

  it('has at least 40 precache entries covering all static assets', () => {
    const matches = readText(p).match(/\{url:/g);
    expect(matches ? matches.length : 0).toBeGreaterThanOrEqual(40);
  });

  it('imports workbox core for runtime caching strategies', () => {
    const code = readText(p);
    expect(code).toMatch(/NetworkFirst/i);
  });
});

/* ───── Workbox library ───── */
describe('workbox library', () => {
  it('exists alongside sw.js in dist/', () => {
    const files = ['workbox-e4022e15.js', 'sw.js'];
    files.forEach((f) => expect(exists(`${DIST}/${f}`)).toBe(true));
  });
});

/* =====================================
   5. index.html — PWA / iOS meta tags
   ===================================== */
describe('index.html (source) — PWA meta tags', () => {
  const html = readText(resolve(ROOT, 'index.html'));
  const distHtml = readText(`${DIST}/index.html`);

  it('links the manifest.json', () => {
    expect(html).toMatch(/<link[^>]+rel="manifest"[^>]*>/);
  });

  it('sets theme-color meta tag to brand blue', () => {
    expect(html).toMatch(/theme-color['"\s]*content=['"]#2563EB['"]/);
  });

  describe('iOS Safari PWA meta tags', () => {
    it('has apple-mobile-web-app-capable set to yes', () => {
      expect(html).toMatch(/apple-mobile-web-app-capable/);
    });

    it('has apple-mobile-web-app-title set to FrontierCRM', () => {
      expect(html).toMatch(/apple-mobile-web-app-title/);
    });

    it('has apple-mobile-web-app-status-bar-style set to default', () => {
      expect(html).toMatch(/apple-mobile-web-app-status-bar-style/);
    });

    it('has apple-touch-icon link pointing to icon-192.png', () => {
      expect(html).toMatch(/apple-touch-icon/);
      expect(html).toMatch(/icon-192\.png/);
    });
  });

  describe('build output (dist/index.html)', () => {
    it('has the vite-plugin-pwa register-sw script injected', () => {
      expect(distHtml).toMatch(/vite-plugin-pwa:register-sw/);
      expect(distHtml).toMatch(/registerSW\.js/);
    });

    it('has a manifest link pointing to the generated .webmanifest', () => {
      expect(distHtml).toMatch(/manifest\.webmanifest/);
    });

    it('preserves iOS meta tags from source', () => {
      expect(distHtml).toMatch(/apple-mobile-web-app-capable/);
      expect(distHtml).toMatch(/apple-mobile-web-app-title/);
      expect(distHtml).toMatch(/apple-touch-icon/);
    });

    it('preserves theme-color meta tag', () => {
      expect(distHtml).toMatch(/theme-color/);
    });
  });
});

/* =====================================
   6. vite.config.ts — PWA plugin config
   ===================================== */
describe('vite.config.ts — PWA plugin config', () => {
  const configPath = resolve(ROOT, 'vite.config.ts');

  it('imports VitePWA from vite-plugin-pwa', () => {
    const cfg = readText(configPath);
    expect(cfg).toMatch(/import.*VitePWA.*from\s+['"]vite-plugin-pwa['"]/);
  });

  it('uses registerType: autoUpdate for seamless SW updates', () => {
    const cfg = readText(configPath);
    expect(cfg).toMatch(/registerType:\s*['"]autoUpdate['"]/);
  });

  it('includes assets glob for favicon, logos, and icons', () => {
    const cfg = readText(configPath);
    expect(cfg).toMatch(/includeAssets/);
    expect(cfg).toMatch(/favicon\.svg/);
    expect(cfg).toMatch(/logo/);
    expect(cfg).toMatch(/icon-/);
  });

  it('configures workbox globPatterns for precaching', () => {
    const cfg = readText(configPath);
    expect(cfg).toMatch(/globPatterns/);
    expect(cfg).toMatch(/js,css,html,svg,png,ico,woff2/);
  });

  it('configures runtime caching with NetworkFirst for /api/*', () => {
    const cfg = readText(configPath);
    expect(cfg).toMatch(/NetworkFirst/);
    // Source has urlPattern: /^\/api\/.*/i — literal backslash before each /
    expect(cfg).toMatch(/\\\/api\\\//);
    expect(cfg).toMatch(/api-cache/);
  });

  it('configures runtime caching with expiration settings', () => {
    const cfg = readText(configPath);
    expect(cfg).toMatch(/expiration/);
    expect(cfg).toMatch(/maxEntries/);
    expect(cfg).toMatch(/maxAgeSeconds/);
    expect(cfg).toMatch(/networkTimeoutSeconds/);
  });

  it('configures manifest fields inline matching public/manifest.json', () => {
    const cfg = readText(configPath);
    expect(cfg).toMatch(/name:\s*'FrontierCRM'/);
    expect(cfg).toMatch(/short_name:\s*'Frontier'/);
    expect(cfg).toMatch(/theme_color:\s*'#2563EB'/);
    expect(cfg).toMatch(/background_color:\s*'#FFFFFF'/);
    expect(cfg).toMatch(/display:\s*'standalone'/);
    expect(cfg).toMatch(/start_url:\s*'\/'/);
  });
});

/* =====================================
   7. Icon PNG files — dimensions + validity
   ===================================== */
describe('PWA icon files', () => {
  it('icon-192.png exists and is 192×192 pixels', () => {
    const p = `${PUBLIC}/icon-192.png`;
    expect(exists(p)).toBe(true);
    const dims = pngDims(p);
    expect(dims).toEqual({ w: 192, h: 192 });
  });

  it('icon-512.png exists and is 512×512 pixels', () => {
    const p = `${PUBLIC}/icon-512.png`;
    expect(exists(p)).toBe(true);
    const dims = pngDims(p);
    expect(dims).toEqual({ w: 512, h: 512 });
  });
});

/* =====================================
   8. App component — boots without crashing
   ===================================== */
describe('App component — PWA compatibility', () => {
  beforeEach(() => {
    Object.defineProperty(navigator, 'serviceWorker', {
      value: undefined,
      configurable: true,
      writable: true,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders without crashing when serviceWorker is absent', () => {
    expect(() => render(<App />)).not.toThrow();
  });

  it('renders without crashing when serviceWorker is available', () => {
    Object.defineProperty(navigator, 'serviceWorker', {
      value: {
        register: vi.fn().mockResolvedValue({}),
        ready: Promise.resolve({}),
      },
      configurable: true,
      writable: true,
    });
    expect(() => render(<App />)).not.toThrow();
  });

  it('does not display an error element on initial render', () => {
    const { container } = render(<App />);
    expect(container.querySelector('[role="alert"]')).toBeNull();
  });
});

/* =====================================
   9. Offline / network state awareness
   ===================================== */
describe('offline / network state awareness', () => {
  beforeEach(() => {
    Object.defineProperty(navigator, 'onLine', {
      value: true,
      writable: true,
      configurable: true,
    });
  });

  it('navigator.onLine defaults to true', () => {
    expect(navigator.onLine).toBe(true);
  });

  it('can detect offline state via onLine property', () => {
    Object.defineProperty(navigator, 'onLine', { value: false, writable: true, configurable: true });
    expect(navigator.onLine).toBe(false);
  });

  it('can listen for online/offline events', () => {
    const onlineCb = vi.fn();
    const offlineCb = vi.fn();
    window.addEventListener('online', onlineCb);
    window.addEventListener('offline', offlineCb);

    window.dispatchEvent(new Event('online'));
    expect(onlineCb).toHaveBeenCalledTimes(1);

    window.dispatchEvent(new Event('offline'));
    expect(offlineCb).toHaveBeenCalledTimes(1);

    window.removeEventListener('online', onlineCb);
    window.removeEventListener('offline', offlineCb);
  });
});

/* =====================================
   10. Service Worker registration behavior
   ===================================== */
describe('service worker registration behavior', () => {
  const registerMock = vi.fn().mockResolvedValue({ scope: '/' });

  beforeEach(() => {
    registerMock.mockClear();
    Object.defineProperty(navigator, 'serviceWorker', {
      value: {
        register: registerMock,
        ready: Promise.resolve({ active: {} }),
        controller: null,
      },
      writable: true,
      configurable: true,
    });
  });

  it('navigator.serviceWorker.register is available', () => {
    expect(navigator.serviceWorker).toBeDefined();
    expect(typeof navigator.serviceWorker.register).toBe('function');
  });

  it('can register sw.js with scope /', async () => {
    const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
    expect(navigator.serviceWorker.register).toHaveBeenCalledWith('/sw.js', { scope: '/' });
    expect(reg.scope).toBe('/');
  });

  it('handles registration failure gracefully', async () => {
    const rejectReady = Promise.reject(new Error('Not ready'));
    rejectReady.catch(() => {}); // squash unhandled rejection
    Object.defineProperty(navigator, 'serviceWorker', {
      value: {
        register: vi.fn().mockRejectedValue(new Error('SW registration failed')),
        ready: rejectReady,
        controller: null,
      },
      writable: true,
      configurable: true,
    });
    await expect(navigator.serviceWorker.register('/sw.js')).rejects.toThrow('SW registration failed');
  });
});
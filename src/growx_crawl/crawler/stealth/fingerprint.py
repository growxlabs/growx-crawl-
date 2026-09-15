"""
Level 2: Deep Anti-Detect Browser Fingerprint Masking Engine.
Injects runtime evasion scripts into Playwright pages/contexts to eliminate automation leaks.
"""

import random
from typing import Any, Dict, Optional

# Realistic WebGL GPU profiles
GPU_PROFILES = [
    {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    },
    {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    },
    {
        "vendor": "Google Inc. (Apple)",
        "renderer": "ANGLE (Apple, Apple M2 Pro, OpenGL 4.1)",
    },
    {
        "vendor": "Google Inc. (Intel)",
        "renderer": "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    },
]


def get_stealth_init_script(
    gpu_profile: Optional[Dict[str, str]] = None,
    hardware_concurrency: int = 8,
    device_memory: int = 8,
    noise_seed: Optional[int] = None,
) -> str:
    """
    Generates a bulletproof JavaScript injection payload to execute before any page scripts.
    Removes all automation signatures and spoofs hardware fingerprints down to the DOM level.
    """
    gpu = gpu_profile or random.choice(GPU_PROFILES)
    seed = noise_seed or random.randint(1, 999999)

    return f"""
    (() => {{
        'use strict';

        // ── 1. Navigator.webdriver Bypass ──
        try {{
            Object.defineProperty(Navigator.prototype, 'webdriver', {{
                get: () => undefined,
                enumerable: true,
                configurable: true,
            }});
            delete navigator.webdriver;
        }} catch (e) {{}}

        // ── 2. window.chrome Mocking ──
        try {{
            if (!window.chrome) {{
                window.chrome = {{}};
            }}
            window.chrome.app = {{
                InstallState: {{ DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }},
                RunningState: {{ CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }},
                getDetails: function() {{}},
                getIsInstalled: function() {{ return false; }},
                installState: function() {{}},
                isInstalled: false,
                runningState: function() {{ return 'cannot_run'; }}
            }};
            window.chrome.runtime = {{
                OnInstalledReason: {{ CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' }},
                OnRestartRequiredReason: {{ APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' }},
                PlatformArch: {{ ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' }},
                PlatformNaclArch: {{ ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' }},
                PlatformOs: {{ ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' }},
                RequestUpdateCheckStatus: {{ NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' }},
                connect: function() {{}},
                sendMessage: function() {{}}
            }};
            window.chrome.csi = function() {{ return {{ onloadT: Date.now(), pageT: 100, startE: Date.now(), tran: 15 }}; }};
            window.chrome.loadTimes = function() {{
                return {{
                    commitLoadTime: Date.now() / 1000,
                    connectionInfo: 'http/1.1',
                    finishDocumentLoadTime: Date.now() / 1000,
                    finishLoadTime: Date.now() / 1000,
                    firstPaintAfterLoadTime: 0,
                    firstPaintTime: Date.now() / 1000,
                    navigationType: 'Other',
                    npnNegotiatedProtocol: 'http/1.1',
                    requestTime: Date.now() / 1000,
                    startLoadTime: Date.now() / 1000,
                    wasAlternateProtocolAvailable: false,
                    wasFetchedViaSpdy: false,
                    wasNpnNegotiated: false
                }};
            }};
        }} catch (e) {{}}

        // ── 3. Navigator Plugins & MimeTypes Emulation ──
        try {{
            const fakePlugins = [
                {{ name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                {{ name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                {{ name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                {{ name: 'Microsoft Edge PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                {{ name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }}
            ];
            Object.defineProperty(navigator, 'plugins', {{
                get: () => fakePlugins,
                enumerable: true,
                configurable: true,
            }});
        }} catch (e) {{}}

        // ── 4. WebGL Vendor & Renderer Spoofing ──
        try {{
            const vendor = "{gpu['vendor']}";
            const renderer = "{gpu['renderer']}";

            const getParameterProxy = function(target, thisArg, args) {{
                const param = args[0];
                // 37445 = UNMASKED_VENDOR_WEBGL
                if (param === 37445) return vendor;
                // 37446 = UNMASKED_RENDERER_WEBGL
                if (param === 37446) return renderer;
                return Reflect.apply(target, thisArg, args);
            }};

            if (window.WebGLRenderingContext) {{
                WebGLRenderingContext.prototype.getParameter = new Proxy(
                    WebGLRenderingContext.prototype.getParameter,
                    {{ apply: getParameterProxy }}
                );
            }}
            if (window.WebGL2RenderingContext) {{
                WebGL2RenderingContext.prototype.getParameter = new Proxy(
                    WebGL2RenderingContext.prototype.getParameter,
                    {{ apply: getParameterProxy }}
                );
            }}
        }} catch (e) {{}}

        // ── 5. Canvas Fingerprint Micro-Noise Injection ──
        try {{
            const seedVal = {seed};
            const shift = (seedVal % 3) - 1; // -1, 0, or 1

            const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                const imgData = origGetImageData.apply(this, args);
                if (imgData.data.length > 4) {{
                    // Add imperceptible micro-shift to pixel 0 to scramble canvas hash
                    imgData.data[0] = Math.min(255, Math.max(0, imgData.data[0] + shift));
                }}
                return imgData;
            }};
        }} catch (e) {{}}

        // ── 6. AudioContext Fingerprint Micro-Noise ──
        try {{
            if (window.AudioBuffer) {{
                const origGetChannelData = AudioBuffer.prototype.getChannelData;
                AudioBuffer.prototype.getChannelData = function(channel) {{
                    const data = origGetChannelData.apply(this, [channel]);
                    for (let i = 0; i < Math.min(10, data.length); i++) {{
                        data[i] += 0.0000001;
                    }}
                    return data;
                }};
            }}
        }} catch (e) {{}}

        // ── 7. Permissions Query Normalization ──
        try {{
            if (navigator.permissions && navigator.permissions.query) {{
                const origQuery = navigator.permissions.query;
                navigator.permissions.query = (parameters) => {{
                    if (parameters.name === 'notifications') {{
                        return Promise.resolve({{ state: Notification.permission || 'default' }});
                    }}
                    return origQuery.call(navigator.permissions, parameters);
                }};
            }}
        }} catch (e) {{}}

        // ── 8. Hardware & Locale Consistency ──
        try {{
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {hardware_concurrency},
                enumerable: true,
                configurable: true,
            }});
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {device_memory},
                enumerable: true,
                configurable: true,
            }});
            Object.defineProperty(navigator, 'languages', {{
                get: () => ['en-US', 'en'],
                enumerable: true,
                configurable: true,
            }});
        }} catch (e) {{}}

        // ── 9. Strip Automation CDC Properties ──
        try {{
            for (const key of Object.keys(window)) {{
                if (key.startsWith('cdc_') || key.startsWith('__playwright')) {{
                    delete window[key];
                }}
            }}
        }} catch (e) {{}}

    }})();
    """


STEALTH_INIT_SCRIPT = get_stealth_init_script()


async def apply_stealth_to_context(context: Any) -> None:
    """Applies stealth script globally to all new pages in a Playwright BrowserContext."""
    script = get_stealth_init_script()
    await context.add_init_script(script)


async def apply_stealth_to_page(page: Any) -> None:
    """Applies stealth script to a specific Playwright Page."""
    script = get_stealth_init_script()
    await page.add_init_script(script)

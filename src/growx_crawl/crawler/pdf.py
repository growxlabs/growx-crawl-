from pathlib import Path
import time
import uuid
from typing import Any, Dict, Optional


class PDFEngine:
    """
    Capability 6: Publication-Grade PDF Generation (A4, Letter, Legal).
    """

    def __init__(self):
        self.output_dir = Path("exports/pdfs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate(
        self,
        url: str,
        format: str = "A4",
        print_background: bool = True,
        margin: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        doc_id = f"pdf_{uuid.uuid4().hex[:10]}"
        filename = f"{doc_id}.pdf"
        file_path = self.output_dir / filename
        m = margin or {"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"}

        start_time = time.time()
        try:
            from playwright.async_api import async_playwright
            from growx_crawl.crawler.stealth import apply_stealth_to_context, solve_turnstile_if_present
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                context = await browser.new_context()
                await apply_stealth_to_context(context)
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until="load", timeout=30000)
                except Exception:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Solve Turnstile challenge if present before PDF rendering
                await solve_turnstile_if_present(page, timeout_seconds=6)

                try:
                    await page.evaluate("() => document.fonts ? document.fonts.ready : Promise.resolve()")
                except Exception:
                    pass

                await page.wait_for_timeout(500)

                pdf_bytes = await page.pdf(
                    path=str(file_path),
                    format=format,
                    print_background=print_background,
                    margin=m,
                )
                await browser.close()

                latency_ms = int((time.time() - start_time) * 1000)
                return {
                    "status": "success",
                    "url": url,
                    "format": format,
                    "file_path": str(file_path),
                    "file_name": filename,
                    "size_bytes": len(pdf_bytes),
                    "latency_ms": latency_ms,
                }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "error": "PDFGenerationFailed",
                "message": str(e),
                "latency_ms": latency_ms,
            }

    async def generate_from_html(
        self,
        html: str,
        output_path: Optional[Path] = None,
        format: str = "A4",
        print_background: bool = True,
    ) -> Path:
        """Render raw HTML into a publication-grade PDF file."""
        target_file = output_path or (self.output_dir / f"pdf_{uuid.uuid4().hex[:8]}.pdf")
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            page = await browser.new_page()
            await page.set_content(html, wait_until="load")
            await page.pdf(
                path=str(target_file),
                format=format,
                print_background=print_background,
                margin={"top": "1.2cm", "bottom": "1.2cm", "left": "1.2cm", "right": "1.2cm"},
            )
            await browser.close()
        return target_file


pdf_engine = PDFEngine()

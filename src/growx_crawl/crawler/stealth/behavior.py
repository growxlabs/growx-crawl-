"""
Level 5: Human Behavioral Emulation Engine.
Provides Bezier-curve mouse physics, natural scrolling, and realistic human dwell pacing.
"""

import asyncio
import math
import random
from typing import Any, Dict, List, Optional, Tuple, Union


def _generate_bezier_curve(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    steps: int = 25,
    deviation: float = 80.0,
) -> List[Tuple[float, float]]:
    """
    Generates a realistic curved mouse trajectory using cubic Bezier curves
    with randomized control points, acceleration, deceleration, and micro-jitter.
    """
    x0, y0 = p0
    x1, y1 = p1

    dist = math.hypot(x1 - x0, y1 - y0)
    if dist < 5:
        return [p1]

    # Calculate perpendicular vector for curve deviation
    dx = x1 - x0
    dy = y1 - y0
    norm = math.hypot(dx, dy)
    ux = -dy / norm
    uy = dx / norm

    # Control point 1 (around 25% along the path)
    r1 = random.uniform(-deviation, deviation)
    c1x = x0 + dx * 0.25 + ux * r1
    c1y = y0 + dy * 0.25 + uy * r1

    # Control point 2 (around 75% along the path)
    r2 = random.uniform(-deviation, deviation)
    c2x = x0 + dx * 0.75 + ux * r2
    c2y = y0 + dy * 0.75 + uy * r2

    points = []
    for i in range(1, steps + 1):
        # Ease-in-out timing function
        t = i / steps
        # Smoothstep easing: 3t^2 - 2t^3
        eased_t = t * t * (3 - 2 * t)

        # Cubic Bezier formula
        u = 1 - eased_t
        tt = eased_t * eased_t
        uu = u * u
        uuu = uu * u
        ttt = tt * eased_t

        x = uuu * x0 + 3 * uu * eased_t * c1x + 3 * u * tt * c2x + ttt * x1
        y = uuu * y0 + 3 * uu * eased_t * c1y + 3 * u * tt * c2y + ttt * y1

        # Add human micro-jitter (except at the very destination)
        if i < steps:
            jitter = random.uniform(-1.2, 1.2)
            x += jitter
            y += jitter

        points.append((x, y))

    return points


class HumanBehavior:
    """Orchestrates human-like interaction on Playwright pages."""

    def __init__(self, page: Any):
        self.page = page
        self.current_pos: Tuple[float, float] = (
            float(random.randint(100, 400)),
            float(random.randint(100, 300)),
        )

    async def move_to(
        self,
        target_x: float,
        target_y: float,
        steps: int = 25,
    ) -> None:
        """Moves cursor along a natural Bezier curve trajectory to the target position."""
        curve = _generate_bezier_curve(self.current_pos, (target_x, target_y), steps=steps)
        for x, y in curve:
            await self.page.mouse.move(x, y)
            self.current_pos = (x, y)
            # Micro delay between 4ms and 15ms per step
            await asyncio.sleep(random.uniform(0.004, 0.015))

    async def click(
        self,
        target: Union[str, Tuple[float, float]],
        wait_after_ms: int = 200,
    ) -> bool:
        """
        Naturally moves to target (selector or (x, y)) and clicks with human dwell.
        """
        if isinstance(target, str):
            el = await self.page.query_selector(target)
            if not el:
                return False
            box = await el.bounding_box()
            if not box:
                return False
            # Click slightly off-center (20% to 80% boundary) to emulate natural human aim
            tx = box["x"] + box["width"] * random.uniform(0.25, 0.75)
            ty = box["y"] + box["height"] * random.uniform(0.25, 0.75)
        else:
            tx, ty = target

        await self.move_to(tx, ty, steps=random.randint(18, 30))
        
        # Pre-click hover dwell
        await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # Natural mousedown -> dwell -> mouseup
        await self.page.mouse.down()
        await asyncio.sleep(random.uniform(0.06, 0.12))
        await self.page.mouse.up()

        if wait_after_ms > 0:
            await asyncio.sleep(wait_after_ms / 1000.0)

        return True

    async def scroll(
        self,
        distance: Optional[int] = None,
        max_bursts: int = 4,
    ) -> None:
        """
        Simulates natural human page reading with variable scroll bursts and pauses.
        """
        bursts = random.randint(2, max_bursts)
        for _ in range(bursts):
            delta = distance or random.randint(180, 450)
            await self.page.mouse.wheel(0, delta)
            # Variable dwell while reading
            await asyncio.sleep(random.uniform(0.2, 0.6))
            
            # 20% chance of micro-scroll up (natural human adjustment)
            if random.random() < 0.2:
                await self.page.mouse.wheel(0, -random.randint(40, 100))
                await asyncio.sleep(random.uniform(0.1, 0.3))


async def human_move(page: Any, target_x: float, target_y: float) -> None:
    hb = HumanBehavior(page)
    await hb.move_to(target_x, target_y)


async def human_click(page: Any, target: Union[str, Tuple[float, float]]) -> bool:
    hb = HumanBehavior(page)
    return await hb.click(target)


async def human_scroll(page: Any, distance: Optional[int] = None) -> None:
    hb = HumanBehavior(page)
    await hb.scroll(distance)


async def random_dwell(min_ms: int = 200, max_ms: int = 800) -> None:
    """Async sleep with humanized randomized duration."""
    delay = random.uniform(min_ms / 1000.0, max_ms / 1000.0)
    await asyncio.sleep(delay)

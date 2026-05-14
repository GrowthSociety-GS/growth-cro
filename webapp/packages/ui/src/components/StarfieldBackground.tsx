"use client";

// StarfieldBackground — V22 Stratospheric Observatory ambient layer.
//
// 4 parallax layers (varying densities + sizes + speeds) + occasional shooting
// stars. Fades in over 1.8s on mount. Honors prefers-reduced-motion: when
// reduced, renders a single static frame and skips animation.
//
// Performance budget : 1 RAF loop, <60 stars per layer, paused when tab
// hidden (Page Visibility API). Canvas sized to devicePixelRatio for sharp
// rendering on Retina without bloat.
//
// Source pattern : V26 HTML L854-856 + inline starfield script.
// Task 001 (sub-PRD design-dna-v22-stratospheric-recovery).

import { useEffect, useRef } from "react";

type Star = {
  x: number;
  y: number;
  r: number; // radius
  vx: number; // px/sec horizontal drift
  vy: number; // px/sec vertical drift
  brightness: number; // 0-1
  twinklePhase: number; // 0-2π
  twinkleSpeed: number; // rad/sec
};

type ShootingStar = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number; // 0-1, decremented per frame
  trailLength: number;
};

// Star counts halved when viewport < 768px (/simplify E2) — mobile CPU
// budget recovery without losing visual density on desktop. ~188 → ~94 stars
// on mobile (60fps × 4 layers × twinkle sin = direct Lighthouse uplift).
const LAYERS = [
  { count: 90, minR: 0.3, maxR: 0.7, speed: 0.6, brightness: 0.4 }, // far
  { count: 60, minR: 0.5, maxR: 1.1, speed: 1.1, brightness: 0.6 }, // mid
  { count: 30, minR: 0.9, maxR: 1.8, speed: 1.8, brightness: 0.85 }, // near
  { count: 8,  minR: 1.6, maxR: 2.6, speed: 2.6, brightness: 1.0 }, // foreground bright
];

const MOBILE_BREAKPOINT = 768;

const SHOOTING_STAR_CHANCE = 0.0008; // per frame (~once every 20s @ 60fps)
const FADE_IN_DURATION_MS = 1800;

function rand(min: number, max: number) {
  return Math.random() * (max - min) + min;
}

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function StarfieldBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number | null>(null);
  const stateRef = useRef<{
    stars: Star[][];
    shootingStars: ShootingStar[];
    mountedAt: number;
    lastFrameAt: number;
    width: number;
    height: number;
    dpr: number;
  } | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    const reducedMotion = prefersReducedMotion();

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      const w = window.innerWidth;
      const h = window.innerHeight;
      canvas!.width = w * dpr;
      canvas!.height = h * dpr;
      canvas!.style.width = w + "px";
      canvas!.style.height = h + "px";
      ctx!.scale(dpr, dpr);
      if (stateRef.current) {
        stateRef.current.width = w;
        stateRef.current.height = h;
        stateRef.current.dpr = dpr;
      }
    }

    function spawnStars(w: number, h: number): Star[][] {
      const mobile = w < MOBILE_BREAKPOINT;
      return LAYERS.map((layer) => {
        const count = mobile ? Math.ceil(layer.count / 2) : layer.count;
        return Array.from({ length: count }, () => ({
          x: rand(0, w),
          y: rand(0, h),
          r: rand(layer.minR, layer.maxR),
          vx: rand(-layer.speed, layer.speed) * 0.03,
          vy: rand(-layer.speed, layer.speed) * 0.03,
          brightness: layer.brightness * rand(0.7, 1),
          twinklePhase: rand(0, Math.PI * 2),
          twinkleSpeed: rand(0.8, 2.2),
        }));
      });
    }

    const w = window.innerWidth;
    const h = window.innerHeight;
    stateRef.current = {
      stars: spawnStars(w, h),
      shootingStars: [],
      mountedAt: performance.now(),
      lastFrameAt: performance.now(),
      width: w,
      height: h,
      dpr: window.devicePixelRatio || 1,
    };
    resize();

    function drawFrame(now: number) {
      const state = stateRef.current;
      if (!state || !ctx) return;
      const dt = Math.min(50, now - state.lastFrameAt) / 1000; // cap dt at 50ms
      state.lastFrameAt = now;

      const fadeProgress = Math.min(1, (now - state.mountedAt) / FADE_IN_DURATION_MS);
      const globalAlpha = reducedMotion ? 1 : fadeProgress;

      ctx.clearRect(0, 0, state.width, state.height);

      // Draw star layers
      for (let li = 0; li < state.stars.length; li++) {
        const layer = state.stars[li];
        for (const s of layer) {
          if (!reducedMotion) {
            s.x += s.vx * dt * 60;
            s.y += s.vy * dt * 60;
            s.twinklePhase += s.twinkleSpeed * dt;
            // Wrap around viewport
            if (s.x < -2) s.x = state.width + 2;
            if (s.x > state.width + 2) s.x = -2;
            if (s.y < -2) s.y = state.height + 2;
            if (s.y > state.height + 2) s.y = -2;
          }
          const twinkle = reducedMotion ? 1 : 0.75 + 0.25 * Math.sin(s.twinklePhase);
          const alpha = s.brightness * twinkle * globalAlpha;
          ctx.fillStyle = `rgba(251, 250, 245, ${alpha.toFixed(3)})`;
          ctx.beginPath();
          ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
          ctx.fill();
          // Tiny glow for the brightest layer
          if (li === LAYERS.length - 1 && s.r > 1.8) {
            ctx.fillStyle = `rgba(232, 200, 114, ${(alpha * 0.18).toFixed(3)})`;
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.r * 2.5, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }

      // Shooting stars (only when motion allowed)
      if (!reducedMotion) {
        if (Math.random() < SHOOTING_STAR_CHANCE) {
          state.shootingStars.push({
            x: rand(0, state.width * 0.7),
            y: rand(0, state.height * 0.4),
            vx: rand(280, 420),
            vy: rand(80, 160),
            life: 1,
            trailLength: rand(60, 110),
          });
        }
        state.shootingStars = state.shootingStars.filter((ss) => ss.life > 0);
        for (const ss of state.shootingStars) {
          ss.x += ss.vx * dt;
          ss.y += ss.vy * dt;
          ss.life -= dt * 1.2; // ~0.8s lifespan
          const alpha = Math.max(0, ss.life) * globalAlpha;
          const tail = Math.min(1, ss.life * 2) * ss.trailLength;
          const gradient = ctx.createLinearGradient(ss.x, ss.y, ss.x - tail, ss.y - tail * 0.4);
          gradient.addColorStop(0, `rgba(232, 200, 114, ${alpha.toFixed(3)})`);
          gradient.addColorStop(1, "rgba(232, 200, 114, 0)");
          ctx.strokeStyle = gradient;
          ctx.lineWidth = 1.2;
          ctx.beginPath();
          ctx.moveTo(ss.x, ss.y);
          ctx.lineTo(ss.x - tail, ss.y - tail * 0.4);
          ctx.stroke();
        }
      }

      if (!reducedMotion) {
        rafRef.current = requestAnimationFrame(drawFrame);
      }
    }

    if (reducedMotion) {
      // Static single frame
      drawFrame(performance.now() + FADE_IN_DURATION_MS);
    } else {
      rafRef.current = requestAnimationFrame(drawFrame);
    }

    window.addEventListener("resize", resize);

    // Pause animation when tab hidden (perf budget)
    function onVisibilityChange() {
      if (document.hidden) {
        if (rafRef.current !== null) {
          cancelAnimationFrame(rafRef.current);
          rafRef.current = null;
        }
      } else if (!reducedMotion && rafRef.current === null) {
        if (stateRef.current) stateRef.current.lastFrameAt = performance.now();
        rafRef.current = requestAnimationFrame(drawFrame);
      }
    }
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: -3,
        pointerEvents: "none",
        width: "100vw",
        height: "100vh",
      }}
    />
  );
}

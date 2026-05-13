"use client";

import type { ReactNode } from "react";
import { useEffect, useRef } from "react";

type Props = {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  width?: string;
};

const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "textarea:not([disabled])",
  "input:not([disabled]):not([type=hidden])",
  "select:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

export function Modal({ open, onClose, title, children, footer, width }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const prevFocusRef = useRef<HTMLElement | null>(null);

  // Wave C.3 (audit A.6 P0.2): clamp width so a hardcoded callsite value
  // (e.g. "560px") never overflows the viewport on mobile (360px).
  // Falls back to the CSS default (`width: min(640px, 100%)`) when no
  // explicit width prop is passed.
  const modalStyle = width
    ? { width: `min(${width}, calc(100vw - 32px))` }
    : undefined;

  // Open/close lifecycle: ESC, body scroll lock, restore focus on close.
  useEffect(() => {
    if (!open) return;
    prevFocusRef.current = document.activeElement as HTMLElement | null;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      // Restore focus to the element that triggered the modal.
      prevFocusRef.current?.focus?.();
    };
  }, [open, onClose]);

  // Initial focus + focus trap (Wave C.3, audit A.6 P0.3).
  useEffect(() => {
    if (!open || !ref.current) return;
    const root = ref.current;
    // Initial: focus the first focusable element, fallback to the dialog itself.
    const focusables = root.querySelectorAll<HTMLElement>(FOCUSABLE);
    const first = focusables[0];
    (first ?? root).focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      const items = root.querySelectorAll<HTMLElement>(FOCUSABLE);
      if (items.length === 0) {
        e.preventDefault();
        return;
      }
      const firstEl = items[0];
      const lastEl = items[items.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (e.shiftKey) {
        if (active === firstEl || !root.contains(active)) {
          e.preventDefault();
          lastEl.focus();
        }
      } else if (active === lastEl) {
        e.preventDefault();
        firstEl.focus();
      }
    };
    root.addEventListener("keydown", onKey);
    return () => {
      root.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="gc-modal-backdrop"
      onClick={onClose}
      role="presentation"
    >
      <div
        ref={ref}
        className="gc-modal"
        style={modalStyle}
        role="dialog"
        aria-modal="true"
        aria-labelledby="gc-modal-title"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="gc-modal__head">
          <h3 id="gc-modal-title" className="gc-modal__title">{title}</h3>
          <button
            type="button"
            className="gc-modal__close"
            onClick={onClose}
            aria-label="Fermer"
          >
            ×
          </button>
        </div>
        <div className="gc-modal__body">{children}</div>
        {footer ? <div className="gc-modal__foot">{footer}</div> : null}
      </div>
    </div>
  );
}

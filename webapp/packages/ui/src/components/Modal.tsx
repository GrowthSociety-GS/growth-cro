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

export function Modal({ open, onClose, title, children, footer, width }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  useEffect(() => {
    if (open && ref.current) {
      ref.current.focus();
    }
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
        style={width ? { width } : undefined}
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

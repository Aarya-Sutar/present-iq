"use client";

import { createContext, useContext, useMemo, useRef, useState } from "react";

type PopupTone = "neutral" | "success" | "warning" | "danger";

type PopupOptions = {
  title: string;
  message: string;
  tone?: PopupTone;
  confirmLabel?: string;
  cancelLabel?: string;
};

type PopupContextValue = {
  notify: (options: PopupOptions) => Promise<void>;
  confirm: (options: PopupOptions) => Promise<boolean>;
};

type PopupState =
  | {
      kind: "notice";
      title: string;
      message: string;
      tone: PopupTone;
      confirmLabel: string;
    }
  | {
      kind: "confirm";
      title: string;
      message: string;
      tone: PopupTone;
      confirmLabel: string;
      cancelLabel: string;
    };

const PopupContext = createContext<PopupContextValue | null>(null);

const toneStyles: Record<
  PopupTone,
  {
    badge: string;
    accent: string;
    button: string;
  }
> = {
  neutral: {
    badge: "border-zinc-700 bg-zinc-900 text-zinc-200",
    accent: "from-zinc-500/20 via-zinc-500/10 to-transparent",
    button: "bg-white text-black hover:bg-zinc-200",
  },
  success: {
    badge: "border-emerald-700 bg-emerald-950 text-emerald-300",
    accent: "from-emerald-500/20 via-emerald-500/10 to-transparent",
    button: "bg-emerald-400 text-zinc-950 hover:bg-emerald-300",
  },
  warning: {
    badge: "border-amber-700 bg-amber-950 text-amber-300",
    accent: "from-amber-500/20 via-amber-500/10 to-transparent",
    button: "bg-amber-300 text-zinc-950 hover:bg-amber-200",
  },
  danger: {
    badge: "border-red-700 bg-red-950 text-red-300",
    accent: "from-red-500/20 via-red-500/10 to-transparent",
    button: "bg-red-400 text-zinc-950 hover:bg-red-300",
  },
};

function PopupSurface({
  title,
  message,
  tone,
  onClose,
  onConfirm,
  confirmLabel,
  cancelLabel,
}: {
  title: string;
  message: string;
  tone: PopupTone;
  onClose: () => void;
  onConfirm: () => void;
  confirmLabel: string;
  cancelLabel?: string;
}) {
  const styles = toneStyles[tone];
  const isConfirm = Boolean(cancelLabel);

  return (
    <div
      className="fixed inset-0 z-100 flex items-center justify-center bg-black/65 px-4 py-6 backdrop-blur-sm"
      onMouseDown={onClose}
      role="presentation"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="popup-title"
        aria-describedby="popup-message"
        className="relative w-full max-w-lg overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/50"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className={`absolute inset-x-0 top-0 h-1.5 bg-linear-to-r ${styles.accent}`} />
        <div className="space-y-5 p-6 sm:p-7">
          <div className="flex items-start justify-between gap-4">
            <div>
              <span
                className={`inline-flex rounded-full border px-3 py-1 text-[11px] uppercase tracking-[0.32em] ${styles.badge}`}
              >
                {tone}
              </span>
              <h2 id="popup-title" className="mt-4 text-2xl font-semibold text-white">
                {title}
              </h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1 text-sm text-zinc-300 transition hover:bg-zinc-800 hover:text-white"
              aria-label="Close popup"
            >
              x
            </button>
          </div>

          <p id="popup-message" className="text-sm leading-6 text-zinc-300">
            {message}
          </p>

          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            {isConfirm ? (
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm font-medium text-zinc-200 transition hover:bg-zinc-800"
              >
                {cancelLabel}
              </button>
            ) : null}
            <button
              type="button"
              onClick={onConfirm}
              className={`rounded-xl px-4 py-3 text-sm font-semibold transition ${styles.button}`}
            >
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function PopupProvider({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [popup, setPopup] = useState<PopupState | null>(null);
  const resolverRef = useRef<((value: boolean) => void) | null>(null);

  const closePopup = (value: boolean) => {
    setPopup(null);

    if (resolverRef.current) {
      resolverRef.current(value);
      resolverRef.current = null;
    }
  };

  const value = useMemo<PopupContextValue>(
    () => ({
      notify: async ({
        title,
        message,
        tone = "neutral",
        confirmLabel = "OK",
      }) => {
        setPopup({
          kind: "notice",
          title,
          message,
          tone,
          confirmLabel,
        });

        return new Promise<void>((resolve) => {
          resolverRef.current = () => resolve();
        });
      },
      confirm: async ({
        title,
        message,
        tone = "warning",
        confirmLabel = "Continue",
        cancelLabel = "Cancel",
      }) => {
        setPopup({
          kind: "confirm",
          title,
          message,
          tone,
          confirmLabel,
          cancelLabel,
        });

        return new Promise<boolean>((resolve) => {
          resolverRef.current = resolve;
        });
      },
    }),
    [],
  );

  return (
    <PopupContext.Provider value={value}>
      {children}
      {popup ? (
        <PopupSurface
          {...popup}
          onClose={() => closePopup(false)}
          onConfirm={() => closePopup(true)}
          confirmLabel={popup.confirmLabel}
          cancelLabel={popup.kind === "confirm" ? popup.cancelLabel : undefined}
        />
      ) : null}
    </PopupContext.Provider>
  );
}

export function usePopup() {
  const context = useContext(PopupContext);

  if (!context) {
    throw new Error("usePopup must be used within a PopupProvider");
  }

  return context;
}
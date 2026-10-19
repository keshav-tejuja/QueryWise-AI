import { useEffect, useRef, type ReactNode } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

/** Built on the native <dialog>: the browser provides focus trapping, Escape-to-close and inertness. */
export function Modal({ open, onClose, title, children }: ModalProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === ref.current) onClose(); // click on the backdrop
      }}
      aria-labelledby="modal-title"
      className="m-auto w-[calc(100%-2rem)] max-w-lg rounded-lg border border-border bg-card p-0 text-card-foreground shadow-xl backdrop:bg-black/60"
    >
      {open && (
        <div className="max-h-[85vh] overflow-y-auto p-6">
          <h2 id="modal-title" className="mb-4 text-lg font-semibold tracking-tight">
            {title}
          </h2>
          {children}
        </div>
      )}
    </dialog>
  );
}
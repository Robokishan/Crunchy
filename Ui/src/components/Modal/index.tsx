import React from "react";
import OutsideClickHandler from "react-outside-click-handler";

interface ModalProps {
  onCancelClick: () => void;
  onConfirmClick: () => void;
  icon: any;
  title: string;
  description: string;
  confirmText: string;
  children?: JSX.Element | React.ReactNode;
}

export default function Modal({
  onCancelClick,
  onConfirmClick,
  title,
  description,
  icon,
  confirmText,
  children,
}: ModalProps) {
  return (
    <>
      <div className="fixed inset-0 z-10 bg-slate-900/50 backdrop-blur-sm transition-opacity dark:bg-slate-900/70" aria-hidden />
      <div className="fixed inset-0 z-10 overflow-y-auto p-4">
        <div className="flex min-h-full items-center justify-center">
          <OutsideClickHandler onOutsideClick={onCancelClick}>
            <div className="relative w-full max-w-lg overflow-hidden rounded-card border border-slate-200/80 bg-white shadow-modal dark:border-slate-700/60 dark:bg-surface-dark-elevated dark:shadow-modal-dark">
              <div className="px-5 pt-5 pb-4 sm:p-6">
                <div className="flex gap-4">
                  <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400">
                    {icon}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="page-title text-base" id="modal-title">
                      {title}
                    </h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                      {description}
                    </p>
                    {children}
                  </div>
                </div>
              </div>
              <div className="flex flex-row-reverse flex-wrap gap-3 border-t border-slate-200 bg-slate-50/80 px-5 py-4 dark:border-slate-700/60 dark:bg-slate-800/40 sm:px-6">
                <button
                  onClick={onConfirmClick}
                  type="button"
                  className="inline-flex w-full justify-center rounded-button bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-red-700 focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 sm:w-auto"
                >
                  {confirmText}
                </button>
                <button
                  onClick={onCancelClick}
                  type="button"
                  className="btn-secondary w-full sm:w-auto"
                >
                  Cancel
                </button>
              </div>
            </div>
          </OutsideClickHandler>
        </div>
      </div>
    </>
  );
}

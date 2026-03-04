interface SmallButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  disabled?: boolean;
  children: JSX.Element | React.ReactNode;
}

export default function SmallButton({
  children,
  disabled,
  ...props
}: SmallButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled}
      className={
        disabled
          ? "cursor-not-allowed rounded-button bg-slate-200 px-4 py-2 text-slate-500 dark:bg-slate-600 dark:text-slate-400"
          : "btn-secondary cursor-pointer"
      }
      type="button"
    >
      {children}
    </button>
  );
}

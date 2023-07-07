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
      className={`cursor-pointer p-2 rounded-md  transition ease-in-out 
      ${!disabled ? 'bg-slate-600  text-white hover:bg-slate-700 active:bg-slate-900 shadow-xl shadow-gray-400' : 'bg-gray-200 text-slate-400'}`}
      type="button"
    >
      {children}
    </button>
  );
}

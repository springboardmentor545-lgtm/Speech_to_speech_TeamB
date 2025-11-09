// src/components/ui/PrimaryButton.jsx
const PrimaryButton = ({ children, className = "", ...props }) => {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg font-semibold bg-gradient-to-r from-indigo-500 to-blue-600 shadow-lg hover:shadow-indigo-600/60 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-60 disabled:cursor-not-allowed ${className}`}
    >
      {children}
    </button>
  );
};

export default PrimaryButton;

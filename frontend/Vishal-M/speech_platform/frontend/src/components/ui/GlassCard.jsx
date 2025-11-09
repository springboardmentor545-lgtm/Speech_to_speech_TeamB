// src/components/ui/GlassCard.jsx
const GlassCard = ({ children, className = "", ...props }) => {
  return (
    <div
      {...props}
      className={`rounded-2xl p-6 bg-white/5 backdrop-blur-xl border border-white/10 shadow-[0_8px_25px_rgba(0,0,0,0.25)] ${className}`}
    >
      {children}
    </div>
  );
};

export default GlassCard;

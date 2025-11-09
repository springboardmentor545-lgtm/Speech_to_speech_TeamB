// src/components/ui/GradientBackground.jsx
export default function GradientBackground({ children }) {
  return (
    <div className="min-h-screen w-full bg-[radial-gradient(circle_at_top,_var(--tw-gradient-stops))] from-[#0b1631] via-[#0a0f24] to-black text-white relative overflow-hidden">
      <div className="absolute -top-24 -left-24 w-[520px] h-[520px] bg-indigo-600/25 blur-[140px] rounded-full" />
      <div className="absolute bottom-0 right-0 w-[420px] h-[420px] bg-blue-500/20 blur-[140px] rounded-full" />
      <div className="relative z-10">{children}</div>
    </div>
  );
}

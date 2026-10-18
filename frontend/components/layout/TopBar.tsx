import { Calendar } from "lucide-react";

interface TopBarProps {
  title?: string;
}

export function TopBar({ title }: TopBarProps) {
  return (
    <header className="h-16 border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-30 px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        {title && <h2 className="font-semibold text-slate-800 text-base">{title}</h2>}
      </div>

      <div className="flex items-center gap-4">
        {/* Date Filter pill */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md border border-slate-200 text-xs text-slate-600 bg-slate-50">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          <span>Oct 1 – 31, 2026</span>
        </div>

        {/* Client Tag */}
        <div className="flex items-center gap-2 pl-2">
          <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 font-semibold text-xs flex items-center justify-center border border-slate-300">
            DC
          </div>
          <span className="text-xs font-medium text-slate-700 hidden md:inline">Dev Client</span>
        </div>
      </div>
    </header>
  );
}

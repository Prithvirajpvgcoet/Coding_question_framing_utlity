"use client";

interface TestCasePolicyProps {
  hiddenCount: number;
  visibleCount: number;
  pointsPerTest: number;
  onHiddenChange: (val: number) => void;
  onVisibleChange: (val: number) => void;
  onPointsChange: (val: number) => void;
}

export function TestCasePolicy({
  hiddenCount,
  visibleCount,
  pointsPerTest,
  onHiddenChange,
  onVisibleChange,
  onPointsChange,
}: TestCasePolicyProps) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
          Test Case Policy
        </label>
        <span className="text-[11px] text-slate-500">6 tests total recommended</span>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs text-slate-600 mb-1">Visible / Sample</label>
          <input
            type="number"
            min={1}
            max={5}
            value={visibleCount}
            onChange={(e) => onVisibleChange(parseInt(e.target.value) || 2)}
            className="w-full text-sm border border-slate-300 rounded-md px-3 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-600 mb-1">Hidden / Edge</label>
          <input
            type="number"
            min={1}
            max={10}
            value={hiddenCount}
            onChange={(e) => onHiddenChange(parseInt(e.target.value) || 3)}
            className="w-full text-sm border border-slate-300 rounded-md px-3 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-600 mb-1">Points / Test</label>
          <input
            type="number"
            min={1}
            max={100}
            value={pointsPerTest}
            onChange={(e) => onPointsChange(parseInt(e.target.value) || 1)}
            className="w-full text-sm border border-slate-300 rounded-md px-3 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-600"
          />
        </div>
      </div>
    </div>
  );
}

"use client";

import { DesignSpec } from "@/lib/api";
import { Home, Maximize, Compass, Layers as LayersIcon, MapPin } from "lucide-react";

export default function SpecPanel({ spec }: { spec: DesignSpec | undefined }) {
  if (!spec) {
    return (
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6 text-slate-400 text-sm">
        Spec will appear here after generation.
      </div>
    );
  }

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-5">
      <h3 className="text-lg font-semibold text-white flex items-center gap-2">
        <LayersIcon className="w-5 h-5 text-amber-400" />
        Design Spec
      </h3>

      <div className="grid grid-cols-2 gap-3">
        <Stat icon={<Home className="w-4 h-4" />} label="BHK" value={`${spec.bhk}`} />
        <Stat
          icon={<Maximize className="w-4 h-4" />}
          label="Area"
          value={`${Math.round(spec.total_area_sqft)} sqft`}
        />
        <Stat
          icon={<Compass className="w-4 h-4" />}
          label="Facing"
          value={spec.facing.toUpperCase()}
        />
        <Stat
          icon={<MapPin className="w-4 h-4" />}
          label="Vastu"
          value={spec.vastu_compliant ? "Yes" : "No"}
          accent={spec.vastu_compliant ? "emerald" : "rose"}
        />
      </div>

      <div>
        <h4 className="text-sm font-medium text-slate-300 mb-3">
          Rooms ({spec.rooms.length})
        </h4>
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {spec.rooms.map((r, i) => (
            <div
              key={i}
              className="flex items-center justify-between bg-slate-900/50 border border-white/5 rounded-lg px-3 py-2 text-sm"
            >
              <span className="text-slate-200 capitalize">
                {r.type.replace(/_/g, " ")}
              </span>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                {r.area_sqft && <span>{Math.round(r.area_sqft)} sqft</span>}
                {r.vastu_zone && (
                  <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300">
                    {r.vastu_zone}
                  </span>
                )}
                {r.attached_bath && (
                  <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300">
                    attached
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {spec.notes && (
        <div className="text-xs text-slate-400 bg-slate-900/30 rounded-lg p-3 border border-white/5">
          <span className="text-slate-500">Note: </span>
          {spec.notes}
        </div>
      )}
    </div>
  );
}

function Stat({
  icon,
  label,
  value,
  accent = "slate",
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent?: string;
}) {
  const colors: Record<string, string> = {
    slate: "text-slate-200",
    emerald: "text-emerald-300",
    rose: "text-rose-300",
  };
  return (
    <div className="bg-slate-900/50 border border-white/5 rounded-lg p-3">
      <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
        {icon}
        {label}
      </div>
      <div className={`text-lg font-semibold ${colors[accent]}`}>{value}</div>
    </div>
  );
}

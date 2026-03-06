import { cn } from "@/lib/utils"

interface ProgressProps {
  value: number;
  max?: number;
  className?: string;
  barClassName?: string;
}

export function Progress({ value, max = 100, className, barClassName }: ProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn("w-full rounded-full bg-gray-200 h-2", className)}>
      <div
        className={cn("h-full rounded-full transition-all duration-500", barClassName || "bg-green-600")}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

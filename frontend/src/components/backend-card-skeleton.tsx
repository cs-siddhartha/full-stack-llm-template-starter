import { Skeleton } from "@/components/ui/skeleton";

export function BackendDetailsSkeleton() {
  return (
    <div
      aria-busy="true"
      aria-label="Loading backend details"
      className="grid min-h-28 gap-3"
    >
      <Skeleton className="h-5 w-20 rounded-full" />
      {Array.from({ length: 3 }, (_, index) => (
        <Skeleton
          className="h-4"
          key={index}
          style={{ width: `${100 - index * 15}%` }}
        />
      ))}
    </div>
  );
}

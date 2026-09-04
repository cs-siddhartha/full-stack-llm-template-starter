import { Skeleton } from "@/components/ui/skeleton";

/** Holds each data region steady with the same number of rows it will render. */
export function BackendDetailsSkeleton({ rowCount = 3 }: { rowCount?: number }) {
  return (
    <div
      aria-busy="true"
      aria-label="Loading backend details"
      className="grid min-h-28 gap-3"
    >
      <Skeleton className="h-5 w-20 rounded-full" />
      {Array.from({ length: rowCount }, (_, index) => (
        <Skeleton
          className="h-4"
          key={index}
          style={{ width: `${100 - index * 15}%` }}
        />
      ))}
    </div>
  );
}

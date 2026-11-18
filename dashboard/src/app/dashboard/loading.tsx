export default function DashboardLoading() {
  return (
    <div className="space-y-8">
      <div>
        <div className="h-3 w-24 animate-pulse rounded-full bg-navy-800" />
        <div className="mt-3 h-9 w-64 animate-pulse rounded-xl bg-navy-800" />
        <div className="mt-3 h-4 w-2/3 animate-pulse rounded-full bg-navy-800/70" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div
            key={index}
            className="h-32 animate-pulse rounded-2xl border border-navy-800 bg-navy-900/50"
          />
        ))}
      </div>
      <div className="h-72 animate-pulse rounded-2xl border border-navy-800 bg-navy-900/50" />
    </div>
  );
}

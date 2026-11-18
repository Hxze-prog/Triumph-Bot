export default function Loading() {
  return (
    <div className="min-h-screen bg-navy-950">
      <div className="mx-auto w-full max-w-6xl px-4 py-20 sm:px-6">
        <div className="h-4 w-32 animate-pulse rounded-full bg-navy-800" />
        <div className="mt-6 h-12 w-2/3 animate-pulse rounded-xl bg-navy-800" />
        <div className="mt-4 h-4 w-1/2 animate-pulse rounded-full bg-navy-800/70" />
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <div
              key={index}
              className="h-36 animate-pulse rounded-2xl border border-navy-800 bg-navy-900/50"
            />
          ))}
        </div>
      </div>
    </div>
  );
}

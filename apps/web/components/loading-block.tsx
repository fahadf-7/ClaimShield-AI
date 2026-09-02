export function LoadingBlock({ count = 3 }: { count?: number }) {
  return (
    <div className="stack" aria-label="Loading content" aria-live="polite">
      {Array.from({ length: count }).map((_, index) => (
        <div className="skeleton" key={index} />
      ))}
    </div>
  );
}


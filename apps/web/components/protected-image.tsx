"use client";

import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import { useEffect, useMemo } from "react";
import { apiBlob, readableError } from "@/lib/api";

export function ProtectedImage({
  path,
  token,
  alt,
  className,
  priority = false,
}: {
  path: string;
  token: string;
  alt: string;
  className?: string;
  priority?: boolean;
}) {
  const image = useQuery({
    queryKey: ["protected-image", path],
    queryFn: () => apiBlob(path, token),
    staleTime: 5 * 60 * 1000,
  });
  const source = useMemo(() => image.data ? URL.createObjectURL(image.data) : null, [image.data]);
  useEffect(() => {
    return () => { if (source) URL.revokeObjectURL(source); };
  }, [source]);

  if (image.error) {
    return <div className="analysis-image-error" role="alert">{readableError(image.error)}</div>;
  }
  if (!source) return <div className="analysis-image-loading" aria-label="Loading protected evidence" />;
  return (
    <Image
      src={source}
      alt={alt}
      fill
      sizes="(max-width: 800px) 100vw, 70vw"
      className={className}
      unoptimized
      priority={priority}
    />
  );
}

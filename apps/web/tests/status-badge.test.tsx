import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge } from "@/components/status-badge";

describe("StatusBadge", () => {
  it("renders a readable label in addition to color", () => {
    render(<StatusBadge value="EVIDENCE_PENDING" />);
    expect(screen.getByText("EVIDENCE PENDING")).toBeInTheDocument();
  });

  it("uses the success treatment for completed states", () => {
    render(<StatusBadge value="SUCCEEDED" />);
    expect(screen.getByText("SUCCEEDED")).toHaveClass("badge-success");
  });
});


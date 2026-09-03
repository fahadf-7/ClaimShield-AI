import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FindingReviewForm } from "@/components/finding-review-form";

describe("FindingReviewForm", () => {
  it("shows correction controls and submits a version without replacing the original", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "correction-1",
          analysis_run_id: "run-1",
          finding_type: "DAMAGE",
          finding_id: "damage-1",
          reviewer_id: "reviewer-1",
          action: "CORRECT",
          corrected_class: "SCRATCH",
          corrected_part_detection_id: "part-1",
          corrected_severity: "MINOR",
          notes: "Reviewed against the source image.",
          version: 1,
          created_at: new Date().toISOString(),
        }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      ),
    );
    const onClose = vi.fn();
    const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <FindingReviewForm
          runId="run-1"
          findingType="DAMAGE"
          findingId="damage-1"
          originalClass="DENT"
          originalSeverity="MODERATE"
          originalPartId="part-1"
          taxonomy={["DENT", "SCRATCH", "UNKNOWN"]}
          parts={[{ id: "part-1", media_id: "media-1", model_version_id: "model-1", class_name: "FRONT_BUMPER", confidence: 0.91, mask_area: 500, bbox_json: [0, 0, 10, 10] }]}
          token="test-token"
          onClose={onClose}
        />
      </QueryClientProvider>,
    );

    fireEvent.change(screen.getByLabelText("Review action"), { target: { value: "CORRECT" } });
    expect(screen.getByLabelText("Corrected class")).toBeInTheDocument();
    expect(screen.getByLabelText("Corrected visible part")).toBeInTheDocument();
    expect(screen.getByLabelText("Corrected rule severity")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Corrected class"), { target: { value: "SCRATCH" } });
    fireEvent.change(screen.getByLabelText("Corrected rule severity"), { target: { value: "MINOR" } });
    fireEvent.change(screen.getByLabelText("Reviewer notes"), { target: { value: "Reviewed against the source image." } });
    fireEvent.click(screen.getByRole("button", { name: "Save review version" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    const request = fetchMock.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(String(request.body))).toMatchObject({
      action: "CORRECT",
      corrected_class: "SCRATCH",
      corrected_severity: "MINOR",
    });
    await waitFor(() => expect(onClose).toHaveBeenCalledOnce());
    fetchMock.mockRestore();
  });
});

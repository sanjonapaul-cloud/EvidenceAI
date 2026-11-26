import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import QuestionCoverage from "./QuestionCoverage.jsx";

describe("QuestionCoverage", () => {
  it("renders nothing when report is null", () => {
    const { container } = render(
      <QuestionCoverage report={null} />
    );

    expect(container.firstChild).toBeNull();
  });

  it("displays the coverage percentage and counts", () => {
    render(
      <QuestionCoverage
        report={{
          total_parts: 4,
          addressed_parts: 3,
          unanswered_parts: 1,
          gaps: [],
          warnings: [],
        }}
      />
    );

    expect(
      screen.getByRole("heading", {
        name: "Question Coverage Report",
      })
    ).toBeInTheDocument();

    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("renders missing information gaps", () => {
    render(
      <QuestionCoverage
        report={{
          total_parts: 2,
          addressed_parts: 1,
          unanswered_parts: 1,
          gaps: [
            {
              requested_part: "What are the Sunday opening hours?",
              status: "missing_information",
              explanation: "The retrieved evidence does not specify Sunday hours.",
              evidence_ids: [],
            },
          ],
          warnings: [],
        }}
      />
    );

    expect(
      screen.getByText("What are the Sunday opening hours?")
    ).toBeInTheDocument();

    expect(screen.getByText("Missing information")).toBeInTheDocument();

    expect(
      screen.getByText(
        "The retrieved evidence does not specify Sunday hours."
      )
    ).toBeInTheDocument();
  });

  it("renders incomplete evidence gaps", () => {
    render(
      <QuestionCoverage
        report={{
          total_parts: 2,
          addressed_parts: 1,
          unanswered_parts: 1,
          gaps: [
            {
              requested_part: "What were the study outcomes?",
              status: "incomplete_evidence",
              explanation: "Only some outcomes are documented.",
              evidence_ids: ["E1"],
            },
          ],
          warnings: [],
        }}
      />
    );

    expect(screen.getByText("Incomplete evidence")).toBeInTheDocument();
    const evidenceText = screen.getByText("Related evidence:", { selector: "strong" }).closest("p");
    expect(evidenceText).toHaveTextContent("Related evidence: E1");
  });

  it("renders conflicting evidence gaps", () => {
    render(
      <QuestionCoverage
        report={{
          total_parts: 2,
          addressed_parts: 1,
          unanswered_parts: 1,
          gaps: [
            {
              requested_part: "What is the reported result?",
              status: "conflicting_evidence",
              explanation: "The retrieved sources report different results.",
              evidence_ids: ["E1", "E2"],
            },
          ],
          warnings: [],
        }}
      />
    );

    expect(screen.getByText("Conflicting evidence")).toBeInTheDocument();
    const evidenceText = screen.getByText("Related evidence:", { selector: "strong" }).closest("p");
    expect(evidenceText).toHaveTextContent("Related evidence: E1, E2");
  });

  it("renders warnings", () => {
    render(
      <QuestionCoverage
        report={{
          total_parts: 1,
          addressed_parts: 1,
          unanswered_parts: 0,
          gaps: [],
          warnings: ["Some evidence may be incomplete."],
        }}
      />
    );

    expect(screen.getByText("Warnings")).toBeInTheDocument();
    expect(
      screen.getByText("Some evidence may be incomplete.")
    ).toBeInTheDocument();
  });

  it("renders the progress bar with the correct accessibility values", () => {
    render(
      <QuestionCoverage
        report={{
          total_parts: 5,
          addressed_parts: 2,
          unanswered_parts: 3,
          gaps: [],
          warnings: [],
        }}
      />
    );

    const progress = screen.getByRole("progressbar", {
      name: "Question coverage",
    });

    expect(progress).toHaveAttribute("aria-valuenow", "40");
    expect(progress).toHaveAttribute("aria-valuemin", "0");
    expect(progress).toHaveAttribute("aria-valuemax", "100");
  });
});
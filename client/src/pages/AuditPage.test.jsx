import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { listAuditEvents } from "../services/api.js";
import AuditPage from "./AuditPage.jsx";

vi.mock("../services/api.js", () => ({
  listAuditEvents: vi.fn(),
}));

async function unlockAuditPage() {
  render(<AuditPage />);

  fireEvent.change(screen.getByLabelText("Audit API key"), {
    target: { value: "test-audit-secret" },
  });

  fireEvent.click(
    screen.getByRole("button", { name: "Unlock audit trail" })
  );

  await waitFor(() => {
    expect(listAuditEvents).toHaveBeenCalled();
  });
}

describe("AuditPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    listAuditEvents.mockResolvedValue({
      total: 0,
      limit: 20,
      offset: 0,
      events: [],
    });
  });

  it("does not request audit events before the key is submitted", () => {
    render(<AuditPage />);

    expect(
      screen.getByLabelText("Audit API key")
    ).toHaveAttribute("type", "password");

    expect(
      screen.getByRole("button", { name: "Unlock audit trail" })
    ).toBeDisabled();

    expect(listAuditEvents).not.toHaveBeenCalled();
  });

  it("renders the audit heading and empty state", async () => {
    await unlockAuditPage();

    expect(
      screen.getByRole("heading", { name: "Audit Trail" })
    ).toBeInTheDocument();

    expect(await screen.findByText("No audit events found."))
      .toBeInTheDocument();

    expect(listAuditEvents).toHaveBeenCalledWith({
      limit: 20,
      offset: 0,
      eventType: "",
      apiKey: "test-audit-secret",
    });
  });

  it("renders event metadata and claim verification counts", async () => {
    listAuditEvents.mockResolvedValueOnce({
      total: 1,
      limit: 20,
      offset: 0,
      events: [
        {
          event_id: "event-12345678",
          event_type: "chat_response_answered",
          created_at: "2026-11-24T08:00:00Z",
          request_id: "request-001",
          document_ids: ["doc-001", "doc-002"],
          evidence_ids: ["evidence-001"],
          claim_status_counts: {
            supported: 2,
            partially_supported: 1,
            contradicted: 0,
            insufficient: 1,
          },
        },
      ],
    });

    await unlockAuditPage();

    expect(
      await screen.findByText("chat_response_answered")
    ).toBeInTheDocument();

    expect(screen.getByText("event-12")).toBeInTheDocument();
    expect(screen.getByText("request-001")).toBeInTheDocument();
    expect(screen.getByText("Supported: 2")).toBeInTheDocument();
    expect(screen.getByText("Partially supported: 1")).toBeInTheDocument();
    expect(screen.getByText("Contradicted: 0")).toBeInTheDocument();
    expect(screen.getByText("Insufficient: 1")).toBeInTheDocument();

    expect(screen.getByText("2", { selector: ".audit-metadata span" }))
      .toBeInTheDocument();

    expect(screen.getByText("1", { selector: ".audit-metadata span" }))
      .toBeInTheDocument();
  });

  it("filters events by event type", async () => {
    await unlockAuditPage();

    await screen.findByText("No audit events found.");

    fireEvent.change(screen.getByLabelText("Event type"), {
      target: { value: "chat_response_answered" },
    });

    await waitFor(() => {
      expect(listAuditEvents).toHaveBeenLastCalledWith({
        limit: 20,
        offset: 0,
        eventType: "chat_response_answered",
        apiKey: "test-audit-secret",
      });
    });
  });

  it("displays an error and allows retry when the API fails", async () => {
    listAuditEvents
      .mockRejectedValueOnce(new Error("Audit API unavailable"))
      .mockResolvedValueOnce({
        total: 0,
        limit: 20,
        offset: 0,
        events: [],
      });

    await unlockAuditPage();

    expect(
      await screen.findByText("Could not load audit events.")
    ).toBeInTheDocument();

    expect(screen.getByRole("alert"))
      .toHaveTextContent("Audit API unavailable");

    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText("No audit events found."))
      .toBeInTheDocument();

    expect(listAuditEvents).toHaveBeenCalledTimes(2);
  });

  it("loads the next page when Next is clicked", async () => {
    listAuditEvents
      .mockResolvedValueOnce({
        total: 21,
        limit: 20,
        offset: 0,
        events: Array.from({ length: 20 }, (_, index) => ({
          event_id: `event-${index + 1}`,
          event_type: "chat_response_answered",
          created_at: "2026-11-24T08:00:00Z",
          request_id: `request-${index + 1}`,
          document_ids: [],
          evidence_ids: [],
          claim_status_counts: {},
        })),
      })
      .mockResolvedValueOnce({
        total: 21,
        limit: 20,
        offset: 20,
        events: [
          {
            event_id: "event-21",
            event_type: "chat_response_answered",
            created_at: "2026-11-24T09:00:00Z",
            request_id: "request-21",
            document_ids: [],
            evidence_ids: [],
            claim_status_counts: {},
          },
        ],
      });

    await unlockAuditPage();

    expect(await screen.findByText("Page 1 of 2 · 21 events"))
      .toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText("request-21"))
      .toBeInTheDocument();

    expect(screen.getByText("Page 2 of 2 · 21 events"))
      .toBeInTheDocument();

    expect(listAuditEvents).toHaveBeenLastCalledWith({
      limit: 20,
      offset: 20,
      eventType: "",
      apiKey: "test-audit-secret",
    });
  });

  it("returns to the previous page when Previous is clicked", async () => {
    listAuditEvents
      .mockResolvedValueOnce({
        total: 21,
        limit: 20,
        offset: 0,
        events: Array.from({ length: 20 }, (_, index) => ({
          event_id: `event-${index + 1}`,
          event_type: "chat_response_answered",
          created_at: "2026-11-24T08:00:00Z",
          request_id: `request-${index + 1}`,
          document_ids: [],
          evidence_ids: [],
          claim_status_counts: {},
        })),
      })
      .mockResolvedValueOnce({
        total: 21,
        limit: 20,
        offset: 20,
        events: [
          {
            event_id: "event-21",
            event_type: "chat_response_answered",
            created_at: "2026-11-24T09:00:00Z",
            request_id: "request-21",
            document_ids: [],
            evidence_ids: [],
            claim_status_counts: {},
          },
        ],
      })
      .mockResolvedValueOnce({
        total: 21,
        limit: 20,
        offset: 0,
        events: [
          {
            event_id: "event-1",
            event_type: "chat_response_answered",
            created_at: "2026-11-24T08:00:00Z",
            request_id: "request-1",
            document_ids: [],
            evidence_ids: [],
            claim_status_counts: {},
          },
        ],
      });

    await unlockAuditPage();

    await screen.findByText("request-1");

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText("request-21"))
      .toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Previous" }));

    expect(await screen.findByText("Page 1 of 2 · 21 events"))
      .toBeInTheDocument();

    expect(listAuditEvents).toHaveBeenLastCalledWith({
      limit: 20,
      offset: 0,
      eventType: "",
      apiKey: "test-audit-secret",
    });
  });
});

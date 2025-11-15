// frontend/testcase/components/StatusBadge.test.jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import StatusBadge from "../../src/components/StatusBadge.jsx";

describe("StatusBadge", () => {
  it("renders the status text", () => {
    render(<StatusBadge status="Open" />);
    expect(screen.getByText("Open")).toBeInTheDocument();
  });

  it("uses the fallback style for unknown status", () => {
    const { getByText } = render(<StatusBadge status="UnknownStatus" />);
    const badge = getByText("UnknownStatus");
    expect(badge.className).toContain("bg-slate-100");
    expect(badge.className).toContain("text-slate-700");
  });
});

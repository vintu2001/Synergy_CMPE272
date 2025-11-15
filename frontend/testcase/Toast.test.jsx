// frontend/testcase/components/Toast.test.jsx
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render } from "@testing-library/react";
import Toast from "../../src/components/Toast.jsx";

describe("Toast", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("renders the message text", () => {
    const { getByText } = render(<Toast message="Hello world" onClose={() => {}} />);
    expect(getByText("Hello world")).toBeInTheDocument();
  });

  it("applies success styles by default", () => {
    const { container } = render(<Toast message="Ok" onClose={() => {}} />);
    const root = container.firstChild;
    expect(root.className).toContain("bg-green-50");
  });

  it("applies error styles when type is error", () => {
    const { container } = render(<Toast message="Oops" type="error" onClose={() => {}} />);
    const root = container.firstChild;
    expect(root.className).toContain("bg-red-50");
  });

  it("calls onClose after the timeout", () => {
    const onClose = vi.fn();
    render(<Toast message="Bye" onClose={onClose} />);

    // 4000ms for auto-hide + 300ms for exit transition
    vi.advanceTimersByTime(4300);

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

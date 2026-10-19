import { required, validateHost, validatePort } from "./connection-validation";

describe("validateHost", () => {
  it("requires a value", () => expect(validateHost(" ")).toBe("Host is required."));
  it("rejects spaces and symbols", () => expect(validateHost("bad host!")).toBe("Host contains invalid characters."));
  it("accepts names and IPs", () => {
    expect(validateHost("db.example.com")).toBeUndefined();
    expect(validateHost("127.0.0.1")).toBeUndefined();
  });
});

describe("validatePort", () => {
  it("requires a value", () => expect(validatePort("")).toBe("Port is required."));
  it.each(["abc", "0", "70000", "54.5"])("rejects %s", (value) =>
    expect(validatePort(value)).toBe("Port must be a number between 1 and 65535."),
  );
  it("accepts a valid port", () => expect(validatePort("5432")).toBeUndefined());
});

describe("required", () => {
  it("flags blank values", () => expect(required("Name")("  ")).toBe("Name is required."));
  it("accepts text", () => expect(required("Name")("x")).toBeUndefined());
});
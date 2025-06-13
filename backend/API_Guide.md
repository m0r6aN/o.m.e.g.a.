# API Evolution: Modifying vs. Versioning Endpoints

**Page Owner:** | `Clint Morgan` | **Last Updated:** | `04.06.2023`

## 1. Purpose

<div class="confluence-information-macro confluence-information-macro-information"><span class="aui-icon aui-icon-small aui-iconfont-info confluence-information-macro-icon"></span><div class="confluence-information-macro-body">
This guide provides a clear framework for deciding when to modify an existing API endpoint versus when to create a new, versioned endpoint. Following these principles ensures we maintain a stable, reliable, and predictable API for all our consumers, both internal and external.
</div></div>

<div>
Our primary goal is to prevent unintentional disruption to our API consumers.
</div>

### The Golden Rule
> **Thou Shalt Not Break Thy Consumers.**
>
> Any change that forces a consumer to update their code to avoid errors is a **breaking change**.

---

## 2. The Decision Framework

The choice between modifying and creating a new endpoint boils down to one question: **Is the change breaking?**

| Change Type | Action | Rationale |
| :--- | :--- | :--- |
| **Non-Breaking** | ✅ **Modify** the existing endpoint. | The change is backward-compatible. Existing consumers will not be affected. |
| **Breaking** | ❌ **Create a new** versioned endpoint. | The change is not backward-compatible. This allows existing consumers to continue using the old version while new consumers (and migrating ones) can adopt the new version. |

### 💡 Quick Decision Flowchart

![alt text](<API Decision.png>)

## 3. Non-Breaking Changes (Modify Existing Endpoint)

These are *additive* changes that enhance the API without altering its core contract. Consumers who are unaware of the change will continue to function without issue.

<div class="confluence-information-macro confluence-information-macro-note"><span class="aui-icon aui-icon-small aui-iconfont-approve confluence-information-macro-icon"></span><div class="confluence-information-macro-body">
<h4>Examples of Non-Breaking Changes</h4>

*   **Adding a new, optional field to a JSON response body.**
    ```json
    // V1 Response (Before)
    {
      "id": 123,
      "name": "Project Phoenix"
    }

    // V1 Response (After - Still backward compatible)
    {
      "id": 123,
      "name": "Project Phoenix",
      "status": "active" // New optional field
    }
    ```

*   **Adding a new, optional query parameter.**
    *   `GET /api/v1/tasks` can be enhanced with `GET /api/v1/tasks?status=completed`. Old clients can still call the endpoint without the new parameter.

*   **Adding a new value to an existing `enum` field.**
    *   If a `status` field can be `"pending"` or `"complete"`, adding `"archived"` is non-breaking as long as consumers have a default case for handling unknown enum values (which they should!).

*   **Adding a new, optional field to a `POST` or `PUT` request body.**
    *   The server can provide a default value if the new field is not present.

*   **Adding a new API endpoint.**
    *   Creating `POST /api/v1/users/{id}/reset-password` doesn't break any existing endpoints.

</div></div>

### Checklist for Non-Breaking Changes

1.  [ ] Implement the change.
2.  [ ] Verify the change is fully backward-compatible. Consider edge cases.
3.  [ ] Update the Swagger documentation to reflect the new field or parameter.
4.  [ ] Communicate the enhancement in release notes so consumers can take advantage of it.

---

## 4. Breaking Changes (Create a New Versioned Endpoint)

These are changes that are *subtractive* or *transformative*. They will cause errors or unexpected behavior for existing consumers. We **must** introduce these changes under a new API version.

Our standard for versioning is via the URL path: `/api/v2/...`

<div class="confluence-information-macro confluence-information-macro-warning"><span class="aui-icon aui-icon-small aui-iconfont-error confluence-information-macro-icon"></span><div class="confluence-information-macro-body">
<h4>Examples of Breaking Changes</h4>

*   **Removing a field from a JSON response.**
    ```json
    // V1 Response
    { "id": 123, "name": "Factorhawk" }

    // V2 Response (Breaking change)
    { "id": 123 } // 'name' field removed
    ```

*   **Renaming a field in the request or response.**
    *   Changing `"name"` to `"projectName"` will break any client expecting `"name"`.

*   **Changing the data type of a field.**
    *   Changing `"id": 123` (Number) to `"id": "user-123"` (String).

*   **Changing the structure of the response.**
    *   Changing a field from a single object to an array of objects.

*   **Making an optional request field required.**
    *   If `description` was optional on a `POST /tasks` request and is now required, old clients not sending it will receive `400 Bad Request` errors.

*   **Changing an existing validation rule.**
    *   e.g., Shortening the max length of a `name` field.

*   **Changing authentication or authorization rules for an endpoint.**
    *   If an endpoint was public and now requires an `Authorization` header, that is a breaking change.

*   **Changing a success response code.**
    *   Changing a `200 OK` to a `202 Accepted`.

</div></div>

### Process for Introducing a Breaking Change

1.  **Identify the Need:** Confirm the change is necessary and truly breaking.
2.  **Create the New Version:**
    *   Copy the existing controller/handler logic for the v1 endpoint.
    *   Create a new route for the v2 endpoint (e.g., `GET /api/v2/users/{id}`).
    *   Implement the breaking change in the v2 logic.
3.  **Document Both Versions:**
    *   The Swagger documentation must clearly show both v1 and v2.
    *   Mark the v1 endpoint as **deprecated** in the documentation.
4.  **Communicate:**
    *   Announce the new v2 endpoint and the deprecation of the v1 endpoint in release notes and developer channels.
    *   Provide a clear migration guide for consumers.
5.  **Implement a Deprecation Strategy:** (See section below)

---

## 5. API Deprecation Policy

When a new version (v2) of an endpoint is released, the old version (v1) enters a "deprecated" state. We do not support old versions indefinitely.

<div class="confluence-information-macro confluence-information-macro-information"><span class="aui-icon aui-icon-small aui-iconfont-info confluence-information-macro-icon"></span><div class="confluence-information-macro-body">
<h4>Deprecation Lifecycle</h4>

1.  **Active:** The primary, recommended version of the API (e.g., v2).
2.  **Deprecated:** The old version (v1) is still functional but no longer recommended for use. It will not receive new features. Consumers should be actively migrating away from it.
3.  **Sunset/Decommissioned:** The deprecated version is turned off and no longer accessible. Requests will result in an error (e.g., `410 Gone`).

</div></div>

### Deprecation Best Practices

*   **Timeline:** A deprecated API version should be supported for a minimum of **6 months** after its successor is released. This period may be longer for critical or external-facing APIs.
*   **Communication:**
    *   **`Deprecation` Header:** When a consumer calls a deprecated endpoint, the response should include a `Deprecation` header.
        ```http
        HTTP/1.1 200 OK
        Content-Type: application/json
        Deprecation: true
        ```
    *   **`Link` Header:** The `Link` header should point to the new version and relevant documentation.
        ```http
        Link: <https://api.otrsolutions.com/v2/users>; rel="successor-version", <https://docs.otrsolutions.com/api/migration-v2>; rel="deprecation-doc"
        ```
    *   **Documentation:** Clearly mark the endpoint as deprecated in the API documentation.
    *   **Direct Outreach:** For critical, high-traffic consumers, direct communication via email or Slack is required before sunsetting an endpoint. Wait for comfirmation!

---

## 6. Summary Table

Use this table as a quick reference.

| Type of Change | Example | Action |
| :--- | :--- | :--- |
| **ADDITIVE** | Adding a new **optional** field to a response. | ✅ **Modify** existing endpoint. |
| | Adding a new **optional** query parameter. | ✅ **Modify** existing endpoint. |
| | Adding a new endpoint entirely. | ✅ **Create** the new endpoint (no versioning needed). |
| **TRANSFORMATIVE**| Renaming a field. | ❌ **Create** a new versioned endpoint. |
| | Changing a field's data type (e.g., `int` -> `string`). | ❌ **Create** a new versioned endpoint. |
| | Changing response structure (e.g., `object` -> `array`).| ❌ **Create** a new versioned endpoint. |
| **SUBTRACTIVE** | Removing a field from a response. | ❌ **Create** a new versioned endpoint. |
| | Making an optional request field **required**. | ❌ **Create** a new versioned endpoint. |
| | Tightening validation rules. | ❌ **Create** a new versioned endpoint. |
| **CONTRACTUAL** | Changing auth/authz rules. | ❌ **Create** a new versioned endpoint. |
| | Changing a success or error status code. | ❌ **Create** a new versioned endpoint. |
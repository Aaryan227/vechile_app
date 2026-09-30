import json
import re
from typing import Generic, TypeVar, Optional, Any, Tuple, Dict
from pydantic import BaseModel
from starlette.types import ASGIApp, Scope, Receive, Send

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response envelope."""
    success: bool = True
    statusCode: int = 200
    code: str
    message: str
    data: Optional[T] = None


ENDPOINT_META: Dict[Tuple[str, str], Tuple[str, str]] = {
    # Auth
    ("POST", "/api/v1/auth/register"): ("USER_REGISTERED", "User registered successfully."),
    ("POST", "/api/v1/auth/login"): ("LOGIN_SUCCESS", "Signed in successfully."),
    ("POST", "/api/v1/auth/refresh"): ("TOKEN_REFRESHED", "Token refreshed successfully."),
    ("GET", "/api/v1/auth/me"): ("CURRENT_USER_FETCHED", "Current user profile retrieved successfully."),
    ("POST", "/api/v1/auth/change-password"): ("PASSWORD_CHANGED", "Password changed successfully."),
    ("POST", "/api/v1/auth/logout"): ("LOGOUT_SUCCESS", "Signed out successfully."),

    # Users
    ("GET", "/api/v1/users"): ("USERS_FETCHED", "Users retrieved successfully."),
    ("POST", "/api/v1/users"): ("USER_CREATED", "User created successfully."),
    ("GET", "/api/v1/users/{user_id}"): ("USER_FETCHED", "User details retrieved successfully."),
    ("PATCH", "/api/v1/users/{user_id}"): ("USER_UPDATED", "User updated successfully."),

    # Admin Dashboard & Fleet Compliance
    ("GET", "/api/v1/admin/dashboard"): ("DASHBOARD_SUMMARY_FETCHED", "Dashboard summary retrieved successfully."),
    ("GET", "/api/v1/admin/taxes"): ("TAXES_FETCHED", "Fleet tax records retrieved successfully."),
    ("GET", "/api/v1/admin/taxes/due-soon"): ("TAXES_DUE_SOON_FETCHED", "Taxes due soon retrieved successfully."),
    ("GET", "/api/v1/admin/taxes/overdue"): ("TAXES_OVERDUE_FETCHED", "Overdue taxes retrieved successfully."),
    ("GET", "/api/v1/admin/taxes/expired"): ("TAXES_EXPIRED_FETCHED", "Expired taxes retrieved successfully."),

    # Vehicles
    ("GET", "/api/v1/vehicles"): ("VEHICLES_FETCHED", "Vehicles retrieved successfully."),
    ("POST", "/api/v1/vehicles"): ("VEHICLE_CREATED", "Vehicle registered successfully."),
    ("GET", "/api/v1/vehicles/{vehicle_id}"): ("VEHICLE_FETCHED", "Vehicle details retrieved successfully."),
    ("PATCH", "/api/v1/vehicles/{vehicle_id}"): ("VEHICLE_UPDATED", "Vehicle updated successfully."),
    ("DELETE", "/api/v1/vehicles/{vehicle_id}"): ("VEHICLE_DELETED", "Vehicle deleted successfully."),

    # Documents
    ("POST", "/api/v1/documents/upload"): ("DOCUMENT_UPLOADED", "Document uploaded successfully."),
    ("POST", "/api/v1/documents/{document_id}/request-reupload"): ("REUPLOAD_REQUESTED", "Document re-upload requested successfully."),
    ("POST", "/api/v1/documents/{document_id}/allow-reupload"): ("REUPLOAD_ALLOWED", "Re-upload permission granted."),
    ("POST", "/api/v1/documents/{document_id}/reject-reupload"): ("REUPLOAD_REJECTED", "Re-upload request rejected."),
    ("GET", "/api/v1/documents/reupload-requests"): ("REUPLOAD_REQUESTS_FETCHED", "Re-upload requests retrieved successfully."),
    ("GET", "/api/v1/documents/vehicle/{vehicle_id}"): ("DOCUMENTS_FETCHED", "Vehicle documents retrieved successfully."),
    ("GET", "/api/v1/documents/expired"): ("EXPIRED_DOCUMENTS_FETCHED", "Expired documents retrieved successfully."),
    ("GET", "/api/v1/documents/expiring-soon"): ("EXPIRING_DOCUMENTS_FETCHED", "Expiring documents retrieved successfully."),
    ("DELETE", "/api/v1/documents/{document_id}"): ("DOCUMENT_DELETED", "Document deleted successfully."),

    # Tanker Reports
    ("POST", "/api/v1/tanker-reports"): ("TANKER_REPORT_CREATED", "Tanker report entry saved successfully."),
    ("GET", "/api/v1/tanker-reports"): ("TANKER_REPORTS_FETCHED", "Tanker reports retrieved successfully."),
    ("GET", "/api/v1/tanker-reports/{report_id}"): ("TANKER_REPORT_FETCHED", "Tanker report retrieved successfully."),
    ("PATCH", "/api/v1/tanker-reports/{report_id}"): ("TANKER_REPORT_UPDATED", "Tanker report updated successfully."),
    ("DELETE", "/api/v1/tanker-reports/{report_id}"): ("TANKER_REPORT_DELETED", "Tanker report deleted successfully."),

    # Taxes & Vehicle Compliance
    ("POST", "/api/v1/vehicles/{vehicle_id}/taxes"): ("TAX_RECORD_CREATED", "Tax record created successfully."),
    ("GET", "/api/v1/vehicles/{vehicle_id}/taxes"): ("TAXES_FETCHED", "Vehicle tax records retrieved successfully."),
    ("GET", "/api/v1/vehicles/{vehicle_id}/taxes/{tax_id}"): ("TAX_RECORD_FETCHED", "Tax record details retrieved successfully."),
    ("PATCH", "/api/v1/vehicles/{vehicle_id}/taxes/{tax_id}"): ("TAX_RECORD_UPDATED", "Tax record updated successfully."),
    ("DELETE", "/api/v1/vehicles/{vehicle_id}/taxes/{tax_id}"): ("TAX_RECORD_DELETED", "Tax record deleted successfully."),
    ("POST", "/api/v1/vehicles/{vehicle_id}/taxes/{tax_id}/receipt"): ("TAX_RECEIPT_UPLOADED", "Tax receipt uploaded successfully."),
    ("POST", "/api/v1/vehicles/{vehicle_id}/government-charges"): ("GOVERNMENT_CHARGE_CREATED", "Government charge recorded successfully."),
    ("GET", "/api/v1/vehicles/{vehicle_id}/government-charges"): ("GOVERNMENT_CHARGES_FETCHED", "Government charges retrieved successfully."),
    ("GET", "/api/v1/vehicles/{vehicle_id}/government-charges/{charge_id}"): ("GOVERNMENT_CHARGE_FETCHED", "Government charge details retrieved successfully."),
    ("PATCH", "/api/v1/vehicles/{vehicle_id}/government-charges/{charge_id}"): ("GOVERNMENT_CHARGE_UPDATED", "Government charge updated successfully."),
    ("DELETE", "/api/v1/vehicles/{vehicle_id}/government-charges/{charge_id}"): ("GOVERNMENT_CHARGE_DELETED", "Government charge deleted successfully."),
    ("POST", "/api/v1/vehicles/{vehicle_id}/challans"): ("CHALLAN_CREATED", "Challan recorded successfully."),
    ("GET", "/api/v1/vehicles/{vehicle_id}/challans"): ("CHALLANS_FETCHED", "Challans retrieved successfully."),
    ("GET", "/api/v1/vehicles/{vehicle_id}/challans/{challan_id}"): ("CHALLAN_FETCHED", "Challan details retrieved successfully."),
    ("PATCH", "/api/v1/vehicles/{vehicle_id}/challans/{challan_id}"): ("CHALLAN_UPDATED", "Challan updated successfully."),
    ("DELETE", "/api/v1/vehicles/{vehicle_id}/challans/{challan_id}"): ("CHALLAN_DELETED", "Challan deleted successfully."),
    ("GET", "/api/v1/vehicles/{vehicle_id}/fastag"): ("FASTAG_FETCHED", "FASTag details retrieved successfully."),
    ("PUT", "/api/v1/vehicles/{vehicle_id}/fastag"): ("FASTAG_UPDATED", "FASTag details updated successfully."),

    # Firms
    ("GET", "/api/v1/firms"): ("FIRMS_FETCHED", "Firms retrieved successfully."),
    ("POST", "/api/v1/firms"): ("FIRM_CREATED", "Firm created successfully."),
    ("GET", "/api/v1/firms/{firm_id}"): ("FIRM_FETCHED", "Firm details retrieved successfully."),
    ("PATCH", "/api/v1/firms/{firm_id}"): ("FIRM_UPDATED", "Firm updated successfully."),
    ("DELETE", "/api/v1/firms/{firm_id}"): ("FIRM_DELETED", "Firm deleted successfully."),

    # Route Points
    ("GET", "/api/v1/route-points"): ("ROUTE_POINTS_FETCHED", "Route points retrieved successfully."),
    ("POST", "/api/v1/route-points"): ("ROUTE_POINT_CREATED", "Route point created successfully."),
    ("PATCH", "/api/v1/route-points/{point_id}"): ("ROUTE_POINT_UPDATED", "Route point updated successfully."),

    # Expenses
    ("GET", "/api/v1/expenses"): ("EXPENSES_FETCHED", "Vehicle expenses retrieved successfully."),
    ("POST", "/api/v1/expenses"): ("EXPENSE_CREATED", "Vehicle expense recorded successfully."),
    ("GET", "/api/v1/expenses/{expense_id}"): ("EXPENSE_FETCHED", "Vehicle expense details retrieved successfully."),
    ("PATCH", "/api/v1/expenses/{expense_id}"): ("EXPENSE_UPDATED", "Vehicle expense updated successfully."),
    ("DELETE", "/api/v1/expenses/{expense_id}"): ("EXPENSE_DELETED", "Vehicle expense deleted successfully."),

    # Financials
    ("GET", "/api/v1/financials/profit-loss"): ("PROFIT_LOSS_FETCHED", "Profit and loss summary retrieved successfully."),
    ("GET", "/api/v1/financials/log-book"): ("FINANCIAL_LOG_BOOK_FETCHED", "Financial log book retrieved successfully."),

    # Reports
    ("GET", "/api/v1/reports/audit-logs"): ("AUDIT_LOGS_FETCHED", "Audit logs retrieved successfully."),
}


def resolve_endpoint_metadata(method: str, route_path: Optional[str], raw_path: str) -> Tuple[str, str]:
    """Find the semantic code and message for a given endpoint and HTTP method."""
    method = method.upper()
    
    # 1. Exact match on route template
    if route_path:
        key = (method, route_path.rstrip("/"))
        if key in ENDPOINT_META:
            return ENDPOINT_META[key]
            
    # 2. Exact match on raw path
    clean_raw = raw_path.split("?")[0].rstrip("/")
    if (method, clean_raw) in ENDPOINT_META:
        return ENDPOINT_META[(method, clean_raw)]

    # 3. Regex pattern match against registered route templates
    for (m, p), (code, msg) in ENDPOINT_META.items():
        if m == method:
            pattern = "^" + re.sub(r'\{[^}]+\}', '[^/]+', p.rstrip("/")) + "$"
            if re.match(pattern, clean_raw):
                return code, msg

    # 4. Fallback generation from path segments
    segments = [s for s in clean_raw.replace("/api/v1", "").split("/") if s and not s.isdigit() and not s.startswith("{")]
    entity = "_".join(segments).upper() if segments else "RESOURCE"
    
    action_map = {
        "GET": ("FETCHED", "retrieved successfully."),
        "POST": ("CREATED", "created successfully."),
        "PUT": ("UPDATED", "updated successfully."),
        "PATCH": ("UPDATED", "updated successfully."),
        "DELETE": ("DELETED", "deleted successfully.")
    }
    action, action_msg = action_map.get(method, ("PROCESSED", "processed successfully."))
    code = f"{entity}_{action}"
    message = f"{entity.replace('_', ' ').title()} {action_msg}"
    return code, message


class ApiResponseEnvelopeMiddleware:
    """
    ASGI Middleware ensuring every JSON response under /api/v1/ conforms to the standard envelope:
    {
        "success": true | false,
        "statusCode": 200,
        "code": "DASHBOARD_SUMMARY_FETCHED",
        "message": "Dashboard summary retrieved successfully.",
        "data": { ... }
    }
    Binary / file download streams (Excel, images, documents) remain untouched.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        raw_path = scope.get("path", "")
        # Only process /api/v1 endpoints, skipping documentation / static files
        if not raw_path.startswith("/api/v1") or raw_path.startswith(("/api/v1/openapi.json", "/static")):
            await self.app(scope, receive, send)
            return

        initial_message = {}
        body_chunks = []

        async def custom_send(message):
            if message["type"] == "http.response.start":
                initial_message.update(message)
            elif message["type"] == "http.response.body":
                body_chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    status_code = initial_message.get("status", 200)
                    headers = dict(initial_message.get("headers", []))
                    content_type = headers.get(b"content-type", b"").decode("latin1").lower()

                    # Convert 204 No Content to 200 JSON Envelope
                    if status_code == 204:
                        status_code = 200
                        initial_message["status"] = 200
                        content_type = "application/json"

                    # Only wrap JSON responses
                    if "application/json" in content_type:
                        full_body_str = b"".join(body_chunks).decode("utf-8")
                        try:
                            parsed_data = json.loads(full_body_str) if full_body_str.strip() else None

                            # Check if already wrapped
                            if isinstance(parsed_data, dict) and "success" in parsed_data and "statusCode" in parsed_data:
                                await send(initial_message)
                                await send({"type": "http.response.body", "body": full_body_str.encode("utf-8"), "more_body": False})
                                return

                            route = scope.get("route")
                            route_path = getattr(route, "path", None)
                            method = scope.get("method", "GET")
                            
                            code, msg = resolve_endpoint_metadata(method, route_path, raw_path)

                            # If payload is a dict with an explicit custom message, use it
                            if isinstance(parsed_data, dict) and "message" in parsed_data and isinstance(parsed_data["message"], str):
                                msg = parsed_data["message"]

                            wrapped_envelope = {
                                "success": status_code < 400,
                                "statusCode": status_code,
                                "code": code,
                                "message": msg,
                                "data": parsed_data
                            }

                            # OAuth2 / RFC 6749 compliance: if response payload contains access_token,
                            # also surface access_token and token_type at root for Swagger UI / OAuth2 clients
                            if isinstance(parsed_data, dict) and "access_token" in parsed_data:
                                wrapped_envelope["access_token"] = parsed_data["access_token"]
                                wrapped_envelope["token_type"] = parsed_data.get("token_type", "bearer")

                            new_body = json.dumps(wrapped_envelope).encode("utf-8")

                            # Replace Content-Length and Content-Type headers
                            filtered_headers = [
                                (k, v) for k, v in initial_message.get("headers", [])
                                if k.lower() not in (b"content-length", b"content-type")
                            ]
                            filtered_headers.append((b"content-type", b"application/json"))
                            filtered_headers.append((b"content-length", str(len(new_body)).encode("latin1")))
                            initial_message["headers"] = filtered_headers

                            await send(initial_message)
                            await send({"type": "http.response.body", "body": new_body, "more_body": False})
                            return
                        except Exception:
                            # Fallback if JSON decoding fails
                            pass

                    # Non-JSON or streaming: stream through unchanged
                    await send(initial_message)
                    await send({"type": "http.response.body", "body": b"".join(body_chunks), "more_body": False})

        await self.app(scope, receive, custom_send)

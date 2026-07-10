"""Shared helper for returning generated files (PDF/Excel/CSV) to the
frontend as a base64-encoded JSON envelope rather than a raw binary
HTTP response.

Every generated-file endpoint in this project (attendance reports,
invoices, transcripts) is consumed exclusively through the frontend's
authenticated XHR-blob download path (exportClient.ts) — never via a
direct browser navigation. Returning `Content-Type: application/pdf`
(or .xlsx/.csv) directly was found, via live runtime debugging, to
still be intercepted at the network layer by third-party download
managers (e.g. IDM's "Advanced Browser Integration") purely on the
Content-Type/file-extension signal, independent of the
Content-Disposition value — the download manager re-requests the URL
itself, without the JS-held bearer token, producing a spurious 401 and
its own credential prompt. Wrapping the bytes in a JSON body removes
that signal entirely: no HTTP client-side tool recognizes
`application/json` as a downloadable file, so nothing intercepts it.
"""

import base64

from fastapi.responses import JSONResponse


def file_json_response(content: bytes, media_type: str, filename: str) -> JSONResponse:
    return JSONResponse(
        content={
            "filename": filename,
            "content_type": media_type,
            "data_base64": base64.b64encode(content).decode("ascii"),
        }
    )

<example>
<diff>
diff --git a/tests/integration/clerk.py b/tests/integration/clerk.py
index a05c57a..44ffa39 100644
--- a/tests/integration/clerk.py
+++ b/tests/integration/clerk.py
@@ -91,9 +91,11 @@ def is_publishable_key(key: str) -> bool:
         PUBLISHABLE_KEY_TEST_PREFIX
     )
 
-    has_valid_postfix = base64_decode(
-        key.split("_")[2] if len(key.split("_")) > 2 else ""
-    ).decode("utf-8").endswith("$")
+    has_valid_postfix = (
+        base64_decode(key.split("_")[2] if len(key.split("_")) > 2 else "")
+        .decode("utf-8")
+        .endswith("$")
+    )
 
     return has_valid_prefix and has_valid_postfix
 
@@ -219,4 +221,3 @@ def teardown_clerk_testing_token(
         frontend_api_url = parsed_result.frontend_api
 
     page.unroute(f"https://{frontend_api_url}/v1/**")
-
diff --git a/tests/routes/utils.py b/tests/routes/utils.py
index 83d399b..deaac5a 100644
--- a/tests/routes/utils.py
+++ b/tests/routes/utils.py
@@ -1,4 +1,3 @@
-import base64
 import json
 import typing as t
 
@@ -162,6 +161,7 @@ def distribution_headers(distribution) -> dict[str, str]:
 def decode_cookie(response: Response):
     "decode a signed cookie into a dict for inspection and assertion"
     from app.routes.middleware import SESSION_SECRET_KEY
+
     from tests.utils import starlette_session_decode
 
     signer = itsdangerous.Signer(SESSION_SECRET_KEY)
diff --git a/tests/utils.py b/tests/utils.py
index c2a69f6..e32844f 100644
--- a/tests/utils.py
+++ b/tests/utils.py
@@ -1,8 +1,17 @@
 import base64
-import typing as t
 
 from tenacity import retry, stop_after_attempt
 
+from app.configuration.clerk import clerk
+from app.environments import is_testing
+from app.utils.geolocation import get_cached_public_ip
+
+from tests.constants import (
+    CLERK_ALL_USERS_TO_PRESERVE,
+)
+
+from .log import log
+
 
 def base64_decode(original_b64_string: str | bytes, url_safe: bool = False) -> bytes:
     """
@@ -37,17 +46,6 @@ def starlette_session_decode(decoded_signed_value: bytes) -> bytes:
     return base64_decode(data, url_safe=True)
 
 
-from app.configuration.clerk import clerk
-from app.environments import is_testing
-from app.utils.geolocation import get_cached_public_ip
-
-from tests.constants import (
-    CLERK_ALL_USERS_TO_PRESERVE,
-)
-
-from .log import log
-
-
 def get_public_ip_address() -> str | None:
     """
     Get the current public IP address of this server. Helpful when you have geolocation stuff that is
</diff>
<diffAnalysis>
- small diff
- omit body
- primary change: style adjustments to satisfy linter
</diffAnalysis>
<commitMessage>
style: linter fixes
</commitMessage>
</example>

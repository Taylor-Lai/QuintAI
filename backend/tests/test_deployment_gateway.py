from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")


class GatewayDeploymentTests(unittest.TestCase):
    def test_compose_exposes_only_the_gateway(self) -> None:
        compose = _read("compose.yaml")

        self.assertIn("gateway:", compose)
        self.assertIn('${HTTP_PORT:-8000}:80', compose)
        self.assertNotIn("--root-path", compose)
        self.assertIn('expose:\n      - "8000"', compose)
        self.assertNotIn('ports:\n      - "8000:8000"', compose)

    def test_gateway_separates_api_and_spa_routes(self) -> None:
        locations = _read("deploy/nginx/app-locations.conf")

        self.assertIn("location /api/", locations)
        self.assertIn("proxy_pass http://app:8000;", locations)
        self.assertIn("try_files $uri $uri/ /index.html;", locations)
        self.assertIn("proxy_set_header X-Forwarded-Proto $scheme;", locations)

    def test_gateway_builds_the_web_application(self) -> None:
        dockerfile = _read("deploy/nginx/Dockerfile")

        self.assertIn("FROM node:", dockerfile)
        self.assertIn("ENV VITE_API_BASE_URL=/api", dockerfile)
        self.assertIn("FROM nginx:", dockerfile)
        self.assertIn("/usr/share/nginx/html", dockerfile)

    def test_https_profile_enforces_modern_transport_security(self) -> None:
        https_config = _read("deploy/nginx/https.conf.template")
        https_compose = _read("deploy/nginx/compose.https.yaml")

        self.assertIn("return 308 https://$host$request_uri;", https_config)
        self.assertIn("ssl_protocols TLSv1.2 TLSv1.3;", https_config)
        self.assertIn("Strict-Transport-Security", https_config)
        self.assertIn("fullchain.pem", https_compose)
        self.assertIn("privkey.pem", https_compose)

    def test_android_defaults_to_the_gateway_api_prefix(self) -> None:
        build_config = _read("android-app/app/build.gradle.kts")

        self.assertIn("https://api.example.com/api/", build_config)
        self.assertIn("http://10.0.2.2:8000/api/", build_config)


if __name__ == "__main__":
    unittest.main()

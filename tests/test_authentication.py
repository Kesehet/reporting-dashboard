"""Synthetic authentication contract tests. No LDAP/Azure/SQL network calls."""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from types import SimpleNamespace

from flask import Flask
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api-server'))
from authentication import authentication, request_identity, unauthorized


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        env = mock.patch.dict(os.environ, {
            'ALL_FILTERS_CHART_API_KEY': 'synthetic-key',
            'RELAY_SERVER_SECRET': 'synthetic-secret',
            'REACT_APP_AZURE_CLIENT_ID': '',
            'REACT_APP_AZURE_TENANT_ID': '',
        })
        env.start()
        self.addCleanup(env.stop)
        app = Flask(__name__)
        app.register_blueprint(authentication)
        @app.route('/protected', methods=['GET', 'POST'])
        def protected():
            identity = request_identity()
            if identity is None:
                return unauthorized()
            return {'role': identity.get('role', 'msal')}
        self.client = app.test_client()

    def test_api_key_header_and_legacy_query_and_json(self):
        self.assertEqual(self.client.get('/protected', headers={'X-API-Key': 'synthetic-key'}).status_code, 200)
        self.assertEqual(self.client.get('/protected?api_key=synthetic-key').status_code, 200)
        self.assertEqual(self.client.post('/protected', json={'api_key': 'synthetic-key'}).status_code, 200)

    def test_wrong_or_missing_credentials(self):
        self.assertEqual(self.client.get('/protected').status_code, 401)
        self.assertEqual(self.client.get('/protected', headers={'X-API-Key': 'not-it'}).status_code, 401)
        self.assertEqual(self.client.get('/protected', headers={
            'X-API-Key': 'synthetic-key', 'Authorization': 'Bearer invalid',
        }).status_code, 401)

    def test_ldap_signed_jwt_expires(self):
        import jwt
        for minutes, expected in [(5, 200), (-5, 401)]:
            token = jwt.encode({
                'email': 'fixture', 'role': 'grp_SSO_DIS_ITBSReportUser',
                'exp': datetime.now(timezone.utc) + timedelta(minutes=minutes),
            }, 'synthetic-secret', algorithm='HS256')
            self.assertEqual(self.client.get('/protected', headers={
                'Authorization': 'Bearer ' + token,
            }).status_code, expected)

    def test_api_key_unset_never_allows_access(self):
        os.environ.pop('ALL_FILTERS_CHART_API_KEY')
        self.assertEqual(self.client.get('/protected', headers={'X-API-Key': 'synthetic-key'}).status_code, 401)

    def test_login_validation_and_msal_config(self):
        self.assertEqual(self.client.post('/login', json={}).status_code, 400)
        self.assertEqual(self.client.get('/msalConfig').status_code, 503)
        os.environ['REACT_APP_AZURE_CLIENT_ID'] = 'public-client'
        os.environ['REACT_APP_AZURE_TENANT_ID'] = 'tenant-id'
        resp = self.client.get('/msalConfig')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['auth']['authority'], 'https://login.microsoftonline.com/tenant-id')



    def test_direct_microsoft_header_valid_for_v1_and_v2(self):
        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        tenant = '11111111-2222-3333-4444-555555555555'
        client = '66666666-7777-8888-9999-000000000000'
        os.environ['REACT_APP_AZURE_TENANT_ID'] = tenant
        os.environ['REACT_APP_AZURE_CLIENT_ID'] = client
        signing_keys = SimpleNamespace(
            get_signing_key_from_jwt=lambda token: SimpleNamespace(key=key.public_key())
        )
        with mock.patch('authentication.microsoft_jwks', return_value=signing_keys) as v2, \
             mock.patch('authentication.microsoft_v1_jwks', return_value=signing_keys) as v1:
            for issuer in (
                f'https://sts.windows.net/{tenant}/',
                f'https://login.microsoftonline.com/{tenant}/v2.0',
            ):
                claims = {
                    'tid': tenant, 'aud': client, 'iss': issuer, 'sub': 'fixture-user',
                    'exp': datetime.now(timezone.utc) + timedelta(minutes=30),
                }
                valid = jwt.encode(claims, key, algorithm='RS256', headers={'kid': 'test-key'})
                with self.subTest(issuer=issuer):
                    result = self.client.get('/protected', headers={
                        'X-MSAL-ID-Token': valid, 'Authorization': 'Negotiate IIS',
                    })
                    self.assertEqual(result.status_code, 200)
                    self.assertEqual(result.json['role'], 'msal')
                    self.assertEqual(self.client.post('/protected', headers={
                        'X-MSAL-ID-Token': valid,
                    }).status_code, 200)
                for claim, value in (
                    ('aud', 'bad-audience'), ('tid', 'bad-tenant'),
                    ('iss', 'https://untrusted.invalid/'),
                    ('exp', datetime.now(timezone.utc) - timedelta(minutes=1)),
                ):
                    invalid = jwt.encode({**claims, claim: value}, key, algorithm='RS256')
                    with self.subTest(issuer=issuer, invalid_claim=claim):
                        self.assertEqual(self.client.get('/protected', headers={
                            'X-MSAL-ID-Token': invalid,
                        }).status_code, 401)
            self.assertTrue(v1.called)
            self.assertTrue(v2.called)

    def test_static_sso_marker_rejected_api_key_retained(self):
        os.environ['REACT_APP_AZURE_TENANT_ID'] = 'tenant'
        os.environ['REACT_APP_AZURE_CLIENT_ID'] = 'client'
        self.assertEqual(self.client.get('/protected', headers={
            'X-MSAL-ID-Token': 'true',
        }).status_code, 401)
        self.assertEqual(self.client.get('/protected', headers={
            'X-API-Key': 'synthetic-key',
        }).status_code, 200)
        self.assertEqual(self.client.post('/sso/session', json={}).status_code, 404)


if __name__ == '__main__':
    unittest.main()

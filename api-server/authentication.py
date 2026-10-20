"""Legacy LDAP, Azure MSAL and chart API-key authentication."""
import hmac
import os
from datetime import datetime, timedelta, timezone
from flask import Blueprint, current_app, jsonify, request
from config import get_env_value

authentication = Blueprint('authentication', __name__)

def setting(key, default=None):
    return os.environ.get(key) or get_env_value(key) or default

def verify_token(value):
    """Accept only verified, unexpired, server-issued or Microsoft identity tokens."""
    token = (value or '').strip()
    if token.lower().startswith('bearer '):
        token = token[7:].strip()
    if not token:
        return None
    import jwt
    try:
        secret = setting('RELAY_SERVER_SECRET')
        if secret:
            try:
                return jwt.decode(token, secret, algorithms=['HS256'], options={'require': ['exp']})
            except jwt.InvalidTokenError:
                pass
        tenant = setting('REACT_APP_AZURE_TENANT_ID')
        client_id = setting('REACT_APP_AZURE_CLIENT_ID')
        if tenant and client_id:
            jwks_url = f'https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys'
            key = jwt.PyJWKClient(jwks_url, cache_keys=True).get_signing_key_from_jwt(token)
            return jwt.decode(
                token, key.key, algorithms=['RS256'], audience=client_id,
                issuer=f'https://login.microsoftonline.com/{tenant}/v2.0',
                options={'require': ['exp', 'iss', 'aud']},
            )
    except Exception:
        return None
    return None

def request_identity():
    token = request.headers.get('Authorization', '').strip()
    if token:
        return verify_token(token)
    provided = request.headers.get('X-API-Key', '') or request.args.get('api_key', '')
    if not provided and request.is_json:
        body = request.get_json(silent=True) or {}
        provided = body.get('api_key', '') if isinstance(body, dict) else ''
    expected = setting('ALL_FILTERS_CHART_API_KEY', '')
    if expected and isinstance(provided, str) and hmac.compare_digest(expected, provided):
        return {'role': 'api_key'}
    return None

def unauthorized():
    return jsonify({'error': 'Invalid or missing login token / API key.'}), 401

@authentication.route('/msalConfig', methods=['GET'])
def msal_config():
    client_id = setting('REACT_APP_AZURE_CLIENT_ID')
    tenant = setting('REACT_APP_AZURE_TENANT_ID')
    if not client_id or not tenant:
        return jsonify({'error': 'Microsoft SSO is not configured.'}), 503
    frontend = setting('REACT_APP_FE_SERVER_BASE_URL', request.host_url)
    return jsonify({
        'auth': {
            'clientId': client_id,
            'authority': f'https://login.microsoftonline.com/{tenant}',
            'redirectUri': frontend,
            'postLogoutRedirectUri': frontend,
        },
        'cache': {'cacheLocation': 'localStorage', 'storeAuthStateInCookie': False},
    })

@authentication.route('/login', methods=['POST'])
def ldap_login():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({'message': 'Both email and password are required.'}), 400
    username = (payload.get('email') or '').strip()
    password = payload.get('password')
    if not username or not password:
        return jsonify({'message': 'Both email and password are required.'}), 400
    secret = setting('RELAY_SERVER_SECRET')
    if not secret:
        return jsonify({'message': 'Login is not configured on the server.'}), 503
    from ldap3 import Server, Connection, ALL, NTLM, SUBTREE, ALL_ATTRIBUTES
    from ldap3.utils.conv import escape_filter_chars
    from role_filter import get_role
    import jwt
    connection = None
    try:
        server = Server(setting('LDAP_SERVER_URL', 'ldaps://ldap.myfnb.us:636'), use_ssl=True, get_info=ALL)
        connection = Connection(
            server, user=f"{setting('LDAP_DOMAIN', 'MYFNB')}\\{username}",
            password=password, authentication=NTLM, auto_bind=True,
        )
        connection.search(
            search_base=setting('LDAP_SEARCH_BASE', 'dc=myfnb,dc=us'),
            search_filter=f'(sAMAccountName={escape_filter_chars(username)})',
            search_scope=SUBTREE, attributes=ALL_ATTRIBUTES,
        )
        if not connection.entries:
            return jsonify({'message': 'User not found in LDAP.'}), 404
        entry = connection.entries[0]
        info = {key: entry[key].value for key in entry.entry_attributes_as_dict}
        display_name = info.get('displayName') or username
        try:
            role = get_role(info)
        except (TypeError, ValueError):
            return jsonify({'message': 'You do not have access to this dashboard.'}), 403
        try:
            minutes = max(1, int(setting('REACT_APP_SESSION_TIMEOUT_MINUTES', '60')))
        except ValueError:
            minutes = 60
        expiry = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        token = jwt.encode({'email': username, 'role': role, 'exp': expiry}, secret, algorithm='HS256')
        return jsonify({
            'message': 'Login successful.', 'token': token, 'user': display_name,
            'role': role, 'expires_at': int(expiry.timestamp() * 1000),
        })
    except Exception as error:
        current_app.logger.warning('LDAP authentication failed: %s', type(error).__name__)
        return jsonify({'message': 'Invalid credentials or directory unavailable.'}), 401
    finally:
        if connection is not None:
            try:
                connection.unbind()
            except Exception:
                pass

@authentication.route('/logout', methods=['GET', 'POST'])
def logout():
    return jsonify({'message': 'Logged out successfully.'})

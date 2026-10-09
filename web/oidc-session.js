"use strict";
/* CapitalBridge OIDC Authorization Code + PKCE browser client.
 * Configure immutable trusted same-origin issuer endpoints at deployment.
 * Access tokens are memory-only. No localStorage, cookies or token logging.
 * This client is an initial foundation and requires a real configured IdP.
 */
(function () {
  const settings = window.capitalBridgeOidcConfig;
  if (!settings) return;
  function safeHttps(value) {
    const u = new URL(value, window.location.origin);
    if (u.protocol !== "https:" || u.origin === "null") throw Error("HTTPS required");
    return u;
  }
  const issuer = safeHttps(settings.issuer);
  const auth = safeHttps(settings.authorizationEndpoint);
  const tokenEndpoint = safeHttps(settings.tokenEndpoint);
  const redirect = new URL(settings.redirectUri, location.origin);
  if (redirect.origin !== location.origin || issuer.origin !== auth.origin || issuer.origin !== tokenEndpoint.origin) {
    throw Error("Untrusted OIDC origin");
  }
  const clientId = String(settings.clientId || "");
  if (!clientId || !Array.isArray(settings.scopes) || !settings.scopes.includes("openid")) {
    throw Error("Invalid OIDC client configuration");
  }
  let accessToken = null, expiresAt = 0;
  const encoder = new TextEncoder();
  const b64url = bytes => btoa(String.fromCharCode(...bytes)).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/,"");
  const random = () => b64url(crypto.getRandomValues(new Uint8Array(32)));
  async function challenge(verifier) {
    return b64url(new Uint8Array(await crypto.subtle.digest("SHA-256",encoder.encode(verifier))));
  }
  function forget() { accessToken = null; expiresAt = 0; }
  async function login() {
    const verifier = random(), state = random(), nonce = random();
    // sessionStorage contains non-secret, short-lived OAuth CSRF/PKCE transaction
    // values, never bearer tokens.
    sessionStorage.setItem("cb:oidc:transaction",JSON.stringify({verifier,state,nonce,created:Date.now()}));
    const url = new URL(auth);
    url.searchParams.set("response_type","code");
    url.searchParams.set("client_id",clientId);
    url.searchParams.set("redirect_uri",redirect.href);
    url.searchParams.set("scope",settings.scopes.join(" "));
    url.searchParams.set("state",state);
    url.searchParams.set("nonce",nonce);
    url.searchParams.set("code_challenge",await challenge(verifier));
    url.searchParams.set("code_challenge_method","S256");
    location.assign(url.href);
  }
  async function completeRedirect() {
    const url = new URL(location.href);
    if (!url.searchParams.has("code") && !url.searchParams.has("error")) return false;
    const raw = sessionStorage.getItem("cb:oidc:transaction");
    sessionStorage.removeItem("cb:oidc:transaction");
    history.replaceState(null,"",redirect.pathname);
    if (!raw) throw Error("Login transaction missing");
    const transaction = JSON.parse(raw);
    if (Date.now()-transaction.created > 5*60*1000 || transaction.state !== url.searchParams.get("state"))
      throw Error("Invalid login state");
    if (url.searchParams.has("error")) throw Error("Identity provider rejected sign-in");
    const body = new URLSearchParams({grant_type:"authorization_code",code:url.searchParams.get("code"),
      client_id:clientId,redirect_uri:redirect.href,code_verifier:transaction.verifier});
    const response = await fetch(tokenEndpoint,{method:"POST",body,headers:{"Content-Type":"application/x-www-form-urlencoded"},cache:"no-store",credentials:"omit",redirect:"error"});
    if (!response.ok) throw Error("Token exchange unsuccessful");
    const result = await response.json();
    if (!result.access_token || result.token_type?.toLowerCase() !== "bearer" ||
        !Number.isFinite(Number(result.expires_in))) throw Error("Invalid token response");
    // Access JWT signature, issuer and audience are verified independently by
    // the server on every authenticated finance API request.
    accessToken = result.access_token;
    expiresAt = Date.now()+Math.max(0,Number(result.expires_in)-30)*1000;
    return true;
  }
  const identity = Object.freeze({
    login,
    completeRedirect,
    logout: forget,
    async getAccessToken() {
      if (!accessToken || Date.now() >= expiresAt) {
        forget();
        throw Error("Session expired. Sign in again.");
      }
      return accessToken;
    },
    get signedIn() { return Boolean(accessToken && Date.now()<expiresAt); }
  });
  Object.defineProperty(window,"capitalBridgeIdentity",{value:identity,writable:false,configurable:false});
})();

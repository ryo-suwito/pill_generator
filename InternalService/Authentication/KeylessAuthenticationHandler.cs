using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Options;
using Neuer;

namespace PillGenerator.Internal.Authentication;

public class KeylessAuthenticationOptions : AuthenticationSchemeOptions
{
}

public class KeylessAuthenticationHandler : AuthenticationHandler<KeylessAuthenticationOptions>
{
    private readonly Neuer.CryptoService.CryptoServiceClient _keylessClient;
    private readonly dotnet_etcd.EtcdClient _etcdClient;

    public KeylessAuthenticationHandler(
        IOptionsMonitor<KeylessAuthenticationOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder,
        Neuer.CryptoService.CryptoServiceClient keylessClient,
        dotnet_etcd.EtcdClient etcdClient)
        : base(options, logger, encoder)
    {
        _keylessClient = keylessClient;
        _etcdClient = etcdClient;
    }

    protected override async Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.ContainsKey("Authorization"))
            return AuthenticateResult.Fail("Missing Authorization Header");

        string token = Request.Headers["Authorization"].ToString();
        if (token.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
        {
            token = token.Substring("Bearer ".Length).Trim();
        }

        if (string.IsNullOrEmpty(token))
            return AuthenticateResult.Fail("Empty Token");

        try
        {
            var handler = new JwtSecurityTokenHandler();
            if (!handler.CanReadToken(token))
                return AuthenticateResult.Fail("Malformed Token");

            var jwt = handler.ReadJwtToken(token);
            var headerAlg = jwt.Header.Alg;
            var keyId = jwt.Subject; // 'sub' claim

            if (string.IsNullOrEmpty(keyId))
                return AuthenticateResult.Fail("Token missing 'sub' claim");

            if (headerAlg == "EdDSA" || headerAlg == "Ed25519") // Check specifically for EdDSA
            {
                // Trusted Local Verification (The PKI Path)
                Logger.LogInformation("Verifying EdDSA token locally via PKI for {KeyId}", keyId);
                
                // 1. Fetch Public Key from Etcd
                var etcdKey = $"burnt_pills/{keyId}";
                var pubKeyVal = await _etcdClient.GetValAsync(etcdKey);
                
                if (string.IsNullOrEmpty(pubKeyVal))
                {
                    Logger.LogWarning("Public Key not found in Etcd for {KeyId}", keyId);
                    return AuthenticateResult.Fail("Public Key not found");
                }

                // 2. Decode Public Key
                byte[] pubKeyBytes;
                try 
                {
                    pubKeyBytes = Convert.FromBase64String(pubKeyVal);
                }
                catch
                {
                    return AuthenticateResult.Fail("Invalid Public Key format");
                }

                // 3. Verify Signature
                // Reconstruct data: header.payload
                var parts = token.Split('.');
                if (parts.Length != 3) return AuthenticateResult.Fail("Invalid Token Format");
                
                var dataBytes = System.Text.Encoding.UTF8.GetBytes(parts[0] + "." + parts[1]);
                var signatureBytes = Microsoft.IdentityModel.Tokens.Base64UrlEncoder.DecodeBytes(parts[2]);

                try 
                {
                    var algorithm = NSec.Cryptography.SignatureAlgorithm.Ed25519;
                    var key = NSec.Cryptography.PublicKey.Import(algorithm, pubKeyBytes, NSec.Cryptography.KeyBlobFormat.RawPublicKey);
                    
                    if (!algorithm.Verify(key, dataBytes, signatureBytes))
                    {
                        Logger.LogWarning("EdDSA Signature Verification Failed for {KeyId}", keyId);
                        return AuthenticateResult.Fail("Invalid Signature");
                    }
                }
                catch (Exception ex)
                {
                     Logger.LogError(ex, "Crypto error during verification");
                     return AuthenticateResult.Fail("Crypto Error");
                }
                
                Logger.LogInformation("EdDSA Verified Successfully for {KeyId}", keyId);
            }
            else
            {
                // Legacy / Fallback to Keyless RPC (HS256)
                Logger.LogInformation("Falling back to Keyless verification for {Alg} token", headerAlg);
                
                var req = new Neuer.Request
                {
                    KeyId = keyId,
                    Payload = Google.Protobuf.ByteString.CopyFromUtf8(token)
                };

                var resp = await _keylessClient.VerifyJWTAsync(req);

                if (!string.IsNullOrEmpty(resp.Error))
                {
                    Logger.LogWarning("Keyless verification failed: {Error}", resp.Error);
                    return AuthenticateResult.Fail("Invalid Token: " + resp.Error);
                }
            }

            // Success - Create Principal
            var claims = new List<Claim>(jwt.Claims);
            var sub = claims.FirstOrDefault(c => c.Type == "sub" || c.Type == JwtRegisteredClaimNames.Sub);
            if (sub != null)
            {
                claims.Add(new Claim(ClaimTypes.NameIdentifier, sub.Value));
            }

            var identity = new ClaimsIdentity(claims, "Keyless");
            var principal = new ClaimsPrincipal(identity);
            var ticket = new AuthenticationTicket(principal, Scheme.Name);

            return AuthenticateResult.Success(ticket);
        }
        catch (Exception ex)
        {
            Logger.LogError(ex, "Authentication failed");
            return AuthenticateResult.Fail(ex);
        }
    }
}

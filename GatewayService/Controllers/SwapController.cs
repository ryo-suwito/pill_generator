using Microsoft.AspNetCore.Mvc;
using PillGenerator.Common.Crypto;
using PillGenerator.Common.Models;
using PillGenerator.Common.Protos;
using NSec.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace PillGenerator.Gateway.Controllers;

public class SwapRequest
{
    public string Pill { get; set; } = string.Empty;
}

[ApiController]
[Route("[controller]")]
public class SwapController : ControllerBase
{
    private readonly SubscriptionService.SubscriptionServiceClient _subscriptionClient;
    private readonly Neuer.CryptoService.CryptoServiceClient _keylessClient;
    private readonly ILogger<SwapController> _logger;
    private static readonly PublicKey _issuancePublicKey = AuthorityKey.PublicKey;

    public SwapController(
        SubscriptionService.SubscriptionServiceClient subscriptionClient, 
        Neuer.CryptoService.CryptoServiceClient keylessClient,
        ILogger<SwapController> logger)
    {
        _subscriptionClient = subscriptionClient;
        _keylessClient = keylessClient;
        _logger = logger;
    }

    [HttpPost]
    public async Task<IActionResult> Swap([FromBody] SwapRequest request)
    {
        // 1. Verify Signature
        var payload = PillSigner.Verify<PillPayload>(request.Pill, _issuancePublicKey);
        if (payload == null)
        {
            return BadRequest(new { detail = "Invalid signature or malformed pill" });
        }

        // 2. Burn Pill
        try
        {
            var burnResponse = await _subscriptionClient.BurnAsync(new BurnRequest { PillId = payload.Pid });
            
            if (!burnResponse.Success)
            {
                return BadRequest(new { detail = "Burn failed: " + burnResponse.Message });
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error communicating with Subscription Service");
            return StatusCode(500, new { detail = "Internal Error" });
        }

        // 3. Issue JWT via Keyless
        try 
        {
            var claims = new Dictionary<string, object>
            {
                { "sub", payload.Pid },
                { "iss", "PillGateway" },
                { "role", "user" },
                { "alg", "EdDSA" } // Request Asymmetric Signing
            };

            if (payload.ExtensionData != null)
            {
                _logger.LogInformation("Processing {Count} extension data items", payload.ExtensionData.Count);
                foreach (var kvp in payload.ExtensionData)
                {
                    _logger.LogInformation("Processing Key: {Key}, ValueKind: {Kind}", kvp.Key, kvp.Value.ValueKind);
                    // Avoid overwriting reserved claims if they happen to be in payload
                    if (!claims.ContainsKey(kvp.Key))
                    {
                        // To be safe, let's clone the element or just pass it.
                        // System.Text.Json should handle JsonElement serialization.
                        claims.Add(kvp.Key, kvp.Value);
                    }
                }
            }
            
            _logger.LogInformation("Serializing claims...");
            var claimsJson = JsonSerializer.SerializeToUtf8Bytes(claims);
            _logger.LogInformation("Serialized claims length: {Length}", claimsJson.Length);
            
            
            var mintReq = new Neuer.Request
            {
                KeyId = payload.Pid, // Use the Pill ID as the signing key identity
                Payload = Google.Protobuf.ByteString.CopyFrom(claimsJson)
            };
            
            var mintResp = await _keylessClient.MintJWTAsync(mintReq);
            
            if (!string.IsNullOrEmpty(mintResp.Error))
            {
                _logger.LogError("Keyless Mint failed: {Error}", mintResp.Error);
                return StatusCode(500, new { detail = "Token Generation Failed: " + mintResp.Error });
            }
            
            // Neuer returns token string in Data bytes
            var tokenString = mintResp.Data.ToStringUtf8();
            return Ok(new TokenResponse { Token = tokenString, ExpiresIn = 300 });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error communicating with Keyless Service");
            return StatusCode(500, new { detail = "Token Service Unavailable" });
        }
    }
}

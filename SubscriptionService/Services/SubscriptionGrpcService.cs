using Grpc.Core;
using PillGenerator.Common.Protos;
using dotnet_etcd;
using NSec.Cryptography;
using Neuer;

namespace PillGenerator.Subscription.Services;

public class SubscriptionGrpcService : SubscriptionService.SubscriptionServiceBase
{
    private readonly EtcdClient _etcdClient;
    private readonly Neuer.CryptoService.CryptoServiceClient _cryptoClient;
    private readonly ILogger<SubscriptionGrpcService> _logger;
    private static readonly SignatureAlgorithm _algorithm = SignatureAlgorithm.Ed25519;

    public SubscriptionGrpcService(
        EtcdClient etcdClient, 
        Neuer.CryptoService.CryptoServiceClient cryptoClient,
        ILogger<SubscriptionGrpcService> logger)
    {
        _etcdClient = etcdClient;
        _cryptoClient = cryptoClient;
        _logger = logger;
    }

    public override async Task<BurnResponse> Burn(BurnRequest request, ServerCallContext context)
    {
        var pillId = request.PillId;
        var key = $"burnt_pills/{pillId}";

        try
        {
            // 1. Check if already burnt (Skipped)
            
            // 2. Generate Keypair (Synchronously to avoid unsafe/ref issue in async)
            var (publicKeyBytes, privateKeyBytes) = GenerateEd25519KeyPair();
            
            var pubKeyBase64 = Convert.ToBase64String(publicKeyBytes);
            
            // 3. Store Private Key in Neuer Keyless
            try 
            {
                var storeReq = new Neuer.Request
                {
                    KeyId = pillId,
                    Payload = Google.Protobuf.ByteString.CopyFrom(privateKeyBytes)
                };
                
                var storeResp = await _cryptoClient.StoreSecretAsync(storeReq);
                
                if (!string.IsNullOrEmpty(storeResp.Error))
                {
                    _logger.LogError("Failed to store secret for pill {PillId}: {Error}", pillId, storeResp.Error);
                    return new BurnResponse { Success = false, Message = "Key storage failed: " + storeResp.Error };
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Exception contacting Neuer Keyless for pill {PillId}", pillId);
                return new BurnResponse { Success = false, Message = "Key storage service unavailable" };
            }

            // 4. Burn Pill in Etcd
            var requestOp = new Etcdserverpb.RequestOp()
            {
                RequestPut = new Etcdserverpb.PutRequest()
                {
                    Key = Google.Protobuf.ByteString.CopyFromUtf8(key),
                    Value = Google.Protobuf.ByteString.CopyFromUtf8(pubKeyBase64) 
                }
            };
            
            var condition = new Etcdserverpb.Compare()
            {
                 Key = Google.Protobuf.ByteString.CopyFromUtf8(key),
                 Target = Etcdserverpb.Compare.Types.CompareTarget.Create,
                 Result = Etcdserverpb.Compare.Types.CompareResult.Equal,
                 CreateRevision = 0 
            };

            var transaction = new Etcdserverpb.TxnRequest();
            transaction.Compare.Add(condition);
            transaction.Success.Add(requestOp);
            
            var response = await _etcdClient.TransactionAsync(transaction);

            if (response.Succeeded)
            {
                _logger.LogInformation("Pill {PillId} burnt successfully. Key stored.", pillId);
                return new BurnResponse { Success = true, Message = "Burn successful" };
            }
            else
            {
                _logger.LogWarning("Double spend detected for Pill {PillId}.", pillId);
                return new BurnResponse { Success = false, Message = "Double spend detected" };
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error burning pill {PillId}", pillId);
            return new BurnResponse { Success = false, Message = "Internal error" };
        }
    }

    private (byte[] PublicKey, byte[] PrivateKey) GenerateEd25519KeyPair()
    {
        var creationParams = new KeyCreationParameters { ExportPolicy = KeyExportPolicies.AllowPlaintextExport };
        using var privateKey = Key.Create(_algorithm, creationParams);
        var publicKeyBytes = privateKey.PublicKey.Export(KeyBlobFormat.RawPublicKey);
        var privateKeyBytes = privateKey.Export(KeyBlobFormat.RawPrivateKey);
        return (publicKeyBytes, privateKeyBytes);
    }
}

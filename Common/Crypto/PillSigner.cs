using NSec.Cryptography;
using System.Text;
using System.Text.Json;

namespace PillGenerator.Common.Crypto;

public static class PillSigner
{
    private static readonly SignatureAlgorithm Algorithm = SignatureAlgorithm.Ed25519;

    public static string Sign(object payload, Key key)
    {
        var json = JsonSerializer.Serialize(payload);
        var data = Encoding.UTF8.GetBytes(json);
        var signature = Algorithm.Sign(key, data);
        
        return $"{Convert.ToBase64String(data)}.{Convert.ToHexString(signature)}";
    }

    public static T? Verify<T>(string pill, PublicKey publicKey)
    {
        var parts = pill.Split('.');
        if (parts.Length != 2) return default;

        try
        {
            var data = Convert.FromBase64String(parts[0]);
            var signature = Convert.FromHexString(parts[1]);

            if (Algorithm.Verify(publicKey, data, signature))
            {
                var json = Encoding.UTF8.GetString(data);
                return JsonSerializer.Deserialize<T>(json);
            }
        }
        catch
        {
            // Ignore parse errors, signature validation failed or format error
        }
        return default;
    }
    
    public static Key GenerateKey() => Key.Create(Algorithm);
    
    public static Key ImportKey(byte[] blob) => Key.Import(Algorithm, blob, KeyBlobFormat.RawPrivateKey);
}

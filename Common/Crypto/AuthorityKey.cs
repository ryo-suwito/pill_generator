using NSec.Cryptography;
using System;

namespace PillGenerator.Common.Crypto;

public static class AuthorityKey
{
    private static readonly Key _key;

    static AuthorityKey()
    {
        var seedHex = Environment.GetEnvironmentVariable("AUTHORITY_SEED");
        byte[] seed;

        if (!string.IsNullOrEmpty(seedHex))
        {
            try 
            {
                seed = Convert.FromHexString(seedHex);
                if (seed.Length != 32)
                {
                     Console.Error.WriteLine($"AUTHORITY_SEED must be 32 bytes (64 hex chars). Got {seed.Length} bytes. Falling back to dummy.");
                     seed = GetDummySeed();
                }
            }
            catch (Exception ex)
            {
                 Console.Error.WriteLine($"Failed to parse AUTHORITY_SEED: {ex.Message}. Falling back to dummy.");
                 seed = GetDummySeed();
            }
        }
        else
        {
            Console.WriteLine("No AUTHORITY_SEED found. Using dummy seed.");
            seed = GetDummySeed();
        }

        _key = Key.Import(SignatureAlgorithm.Ed25519, seed, KeyBlobFormat.RawPrivateKey);
    }

    private static byte[] GetDummySeed()
    {
        var seed = new byte[32];
        for(int i=0;i<32;i++) seed[i] = (byte)i;
        return seed;
    }

    public static Key PrivateKey => _key;
    public static PublicKey PublicKey => _key.PublicKey;
}

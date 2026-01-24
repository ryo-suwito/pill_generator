using System.Text.Json;
using System.Text.Json.Serialization;

namespace PillGenerator.Common.Models;

public class PillPayload
{
    [JsonPropertyName("pid")]
    public string Pid { get; set; } = string.Empty;

    [JsonPropertyName("iat")]
    public long Iat { get; set; }

    [JsonExtensionData]
    public Dictionary<string, JsonElement>? ExtensionData { get; set; }
}

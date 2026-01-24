using Microsoft.AspNetCore.Mvc;
using PillGenerator.Common.Crypto;
using PillGenerator.Common.Models;
using NSec.Cryptography;

namespace PillGenerator.Issuance.Controllers;

[ApiController]
[Route("[controller]")]
public class IssueController : ControllerBase
{
    private static readonly Key _signingKey = AuthorityKey.PrivateKey;
    private readonly ILogger<IssueController> _logger;

    public IssueController(ILogger<IssueController> logger)
    {
        _logger = logger;
    }

    [HttpPost]
    public IActionResult Issue([FromBody] PillPayload payload)
    {
        _logger.LogInformation("Issuing pill for {Pid}", payload.Pid);
        
        // Ensure IAT is set if missing (though model validation might require it, let's treat it as user input)
        // Actually, Python example passed IAT.
        
        var pillString = PillSigner.Sign(payload, _signingKey);
        
        return Ok(new { pill = pillString });
    }
}

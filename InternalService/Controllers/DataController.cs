using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;

namespace PillGenerator.Internal.Controllers;

[ApiController]
[Route("[controller]")]
public class DataController : ControllerBase
{
    [HttpGet]
    [Authorize]
    public IActionResult GetData()
    {
        var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value ?? "unknown";
        
        return Ok(new
        {
            message = "Access granted",
            user_id = userId,
            service = "Internal Service A"
        });
    }
}

using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using PillGenerator.Common.Crypto;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddAuthorization();

// Add Etcd Client
builder.Services.AddSingleton<dotnet_etcd.EtcdClient>(sp =>
{
    var etcdHost = Environment.GetEnvironmentVariable("ETCD_HOST") ?? "http://etcd:2379";
    return new dotnet_etcd.EtcdClient(etcdHost);
});

// Add gRPC Client for Keyless
builder.Services.AddGrpcClient<Neuer.CryptoService.CryptoServiceClient>(o =>
{
    var address = Environment.GetEnvironmentVariable("KEYLESS_HOST") ?? "http://neuer-keyless:8080";
    o.Address = new Uri(address);
});

builder.Services.AddAuthentication("Keyless")
    .AddScheme<PillGenerator.Internal.Authentication.KeylessAuthenticationOptions, PillGenerator.Internal.Authentication.KeylessAuthenticationHandler>("Keyless", null);

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();

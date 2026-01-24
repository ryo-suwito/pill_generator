using PillGenerator.Subscription.Services;
using dotnet_etcd;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddGrpc();
builder.Services.AddSingleton<EtcdClient>(sp => {
    // Connect to 'etcd' service (docker-compose)
    return new EtcdClient("etcd", 2379); 
});

builder.Services.AddGrpcClient<Neuer.CryptoService.CryptoServiceClient>(o =>
{
    var address = Environment.GetEnvironmentVariable("KEYLESS_HOST") ?? "http://neuer-keyless:8080";
    o.Address = new Uri(address);
});

var app = builder.Build();

// Configure the HTTP request pipeline.
app.MapGrpcService<SubscriptionGrpcService>();
app.MapGet("/", () => "Communication with gRPC endpoints must be made through a gRPC client. To learn how to create a client, visit: https://go.microsoft.com/fwlink/?linkid=2086909");

app.Run();

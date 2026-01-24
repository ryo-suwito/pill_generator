using PillGenerator.Common.Protos;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddAuthorization();

// Add gRPC Client
builder.Services.AddGrpcClient<SubscriptionService.SubscriptionServiceClient>(o =>
{
    o.Address = new Uri("http://subscription_service:5000"); // Using docker service name
});

builder.Services.AddGrpcClient<Neuer.CryptoService.CryptoServiceClient>(o =>
{
    var address = Environment.GetEnvironmentVariable("KEYLESS_HOST") ?? "http://neuer-keyless:8080";
    o.Address = new Uri(address);
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();

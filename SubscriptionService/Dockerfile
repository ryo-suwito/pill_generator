FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 8080
EXPOSE 5000

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["SubscriptionService/PillGenerator.Subscription.csproj", "SubscriptionService/"]
COPY ["Common/PillGenerator.Common.csproj", "Common/"]
RUN dotnet restore "SubscriptionService/PillGenerator.Subscription.csproj"
COPY . .
WORKDIR "/src/SubscriptionService"
RUN dotnet build "PillGenerator.Subscription.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "PillGenerator.Subscription.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "PillGenerator.Subscription.dll"]

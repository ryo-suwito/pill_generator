FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["GatewayService/PillGenerator.Gateway.csproj", "GatewayService/"]
COPY ["Common/PillGenerator.Common.csproj", "Common/"]
RUN dotnet restore "GatewayService/PillGenerator.Gateway.csproj"
COPY . .
WORKDIR "/src/GatewayService"
RUN dotnet build "PillGenerator.Gateway.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "PillGenerator.Gateway.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "PillGenerator.Gateway.dll"]

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["IssuanceService/PillGenerator.Issuance.csproj", "IssuanceService/"]
COPY ["Common/PillGenerator.Common.csproj", "Common/"]
RUN dotnet restore "IssuanceService/PillGenerator.Issuance.csproj"
COPY . .
WORKDIR "/src/IssuanceService"
RUN dotnet build "PillGenerator.Issuance.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "PillGenerator.Issuance.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "PillGenerator.Issuance.dll"]

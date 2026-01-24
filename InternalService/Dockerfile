FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["InternalService/PillGenerator.Internal.csproj", "InternalService/"]
COPY ["Common/PillGenerator.Common.csproj", "Common/"]
RUN dotnet restore "InternalService/PillGenerator.Internal.csproj"
COPY . .
WORKDIR "/src/InternalService"
RUN dotnet build "PillGenerator.Internal.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "PillGenerator.Internal.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "PillGenerator.Internal.dll"]

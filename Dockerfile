FROM docker.io/library/node:22.22.2-bookworm-slim AS frontend
WORKDIR /web
COPY frontend/package*.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM mcr.microsoft.com/dotnet/sdk:10.0.300 AS build
WORKDIR /source
COPY global.json Directory.Build.props EchoCase.slnx ./
COPY src/ src/
RUN dotnet restore src/EchoCase.Api --locked-mode
RUN dotnet publish src/EchoCase.Api -c Release --no-restore -o /app

FROM mcr.microsoft.com/dotnet/aspnet:10.0.9 AS final
WORKDIR /app
COPY --from=build /app ./
COPY --from=frontend /web/dist ./wwwroot
ENV ASPNETCORE_HTTP_PORTS=8080
USER $APP_UID
EXPOSE 8080
ENTRYPOINT ["dotnet","EchoCase.Api.dll"]

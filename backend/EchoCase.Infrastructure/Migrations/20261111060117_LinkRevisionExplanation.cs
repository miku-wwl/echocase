using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace EchoCase.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class LinkRevisionExplanation : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "Rationale",
                table: "Links",
                type: "character varying(500)",
                maxLength: 500,
                nullable: true);

            migrationBuilder.AddColumn<DateTimeOffset>(
                name: "RevisedAt",
                table: "Links",
                type: "timestamp with time zone",
                nullable: true);

            migrationBuilder.AddCheckConstraint(
                name: "ck_link_revision",
                table: "Links",
                sql: "(\"Rationale\" IS NULL AND \"RevisedAt\" IS NULL) OR (\"Rationale\" IS NOT NULL AND \"RevisedAt\" IS NOT NULL AND char_length(\"Rationale\") BETWEEN 20 AND 500)");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropCheckConstraint(
                name: "ck_link_revision",
                table: "Links");

            migrationBuilder.DropColumn(
                name: "Rationale",
                table: "Links");

            migrationBuilder.DropColumn(
                name: "RevisedAt",
                table: "Links");
        }
    }
}

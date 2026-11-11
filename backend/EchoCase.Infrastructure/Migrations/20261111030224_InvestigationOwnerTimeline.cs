using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace EchoCase.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class InvestigationOwnerTimeline : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_Investigations_OwnerId",
                table: "Investigations");

            migrationBuilder.CreateIndex(
                name: "IX_Investigations_OwnerId_UpdatedAt",
                table: "Investigations",
                columns: new[] { "OwnerId", "UpdatedAt" },
                descending: new[] { false, true });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_Investigations_OwnerId_UpdatedAt",
                table: "Investigations");

            migrationBuilder.CreateIndex(
                name: "IX_Investigations_OwnerId",
                table: "Investigations",
                column: "OwnerId");
        }
    }
}
